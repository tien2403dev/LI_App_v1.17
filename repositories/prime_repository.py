import sqlite3
from contextlib import closing
from datetime import datetime, timezone

from database.connection import connection
from database.schema import verify_database
from domain.prime import COLUMNS, ImportResult, ValidationError, check_cancel
from repositories.import_lock_repository import ImportLockRepository

BATCH_SIZE = 5000


class PrimeRepository:
    def __init__(self, database_path):
        """Khởi tạo trạng thái và các thành phần cần cho đối tượng."""
        self.database_path = database_path

    def replace_from_staging(self, stage_path, batch_id, file_count, progress, cancel=None):
        """Thay dữ liệu các ngày trong staging và đồng bộ TIER trong transaction."""
        with closing(sqlite3.connect(str(stage_path))) as stage:
            counts = stage.execute(
                "SELECT DATE, COUNT(*) FROM staging_prime_data GROUP BY DATE ORDER BY DATE").fetchall()
            if not counts:
                raise ValidationError("Staging rỗng; không xóa dữ liệu")
            dates = tuple(row[0] for row in counts)
            passed = stage.execute(
                "SELECT COUNT(*) FROM staging_prime_data WHERE RESULT='PASS'").fetchone()[0]
            with connection(self.database_path) as conn:
                verify_database(conn)
                conn.execute("BEGIN IMMEDIATE")
                try:
                    ImportLockRepository.assert_owner(conn, batch_id)
                    check_cancel(cancel)
                    conn.execute("CREATE TEMP TABLE replace_dates(DATE TEXT PRIMARY KEY)")
                    conn.executemany("INSERT INTO replace_dates VALUES(?)", [(d,) for d in dates])
                    # Chụp cả slot cũ để tính lại khi re-import làm slot biến mất.
                    # Today không kích hoạt tính Monitor và không được dùng làm ngày Monitor.
                    monitor_cutoff = datetime.now().strftime('%Y%m%d')
                    affected = {}
                    has_past_dates = any(day < monitor_cutoff for day in dates)
                    def collect_monitor_slots():
                        if not has_past_dates:
                            return
                        for row in conn.execute("""SELECT DISTINCT EQP,SLOT,DATE
                                FROM prime_data WHERE DATE IN (SELECT DATE FROM replace_dates)
                                AND DATE<?""", (monitor_cutoff,)):
                            affected.setdefault((row['EQP'], row['SLOT']), set()).add(row['DATE'])
                    collect_monitor_slots()
                    deleted = conn.execute(
                        "SELECT COUNT(*) FROM prime_data WHERE DATE IN (SELECT DATE FROM replace_dates)"
                    ).fetchone()[0]
                    conn.execute("DELETE FROM prime_data WHERE DATE IN (SELECT DATE FROM replace_dates)")
                    cursor = stage.execute(f"SELECT {','.join(COLUMNS)} FROM staging_prime_data ORDER BY rowid")
                    sql = f"INSERT INTO prime_data({','.join(COLUMNS)}) VALUES({','.join('?' for _ in COLUMNS)})"
                    inserted = 0
                    while rows := cursor.fetchmany(BATCH_SIZE):
                        check_cancel(cancel)
                        conn.executemany(sql, rows)
                        inserted += len(rows)
                        progress(f"Đang ghi database: {inserted} dòng (chưa commit)")
                    from repositories.tier_repository import sync_prime_tiers
                    progress("Đang đồng bộ TIER (chưa commit)")
                    sync_prime_tiers(conn, dates, cancel)
                    from repositories.alarm_repository import AlarmRepository
                    progress("Đang tính Alarm (chưa commit)")
                    AlarmRepository.sync_import_dates(conn, dates, progress, cancel)
                    collect_monitor_slots()
                    if affected:
                        AlarmRepository.sync_import_monitors(
                            conn, affected, monitor_cutoff, progress, cancel)
                    now = datetime.now(timezone.utc).isoformat()
                    conn.executemany(
                        """INSERT INTO data_import_status VALUES('PRIME',?,?,?,?)
                        ON CONFLICT(data_type, DATE) DO UPDATE SET
                        imported_at=excluded.imported_at, batch_id=excluded.batch_id,
                        row_count=excluded.row_count""",
                        [(date, now, batch_id, count) for date, count in counts])
                    check_cancel(cancel)
                    # SQLite write transaction blocks takeover even if a long write exceeds lease.
                    ImportLockRepository.renew_in_transaction(conn, batch_id)
                    progress("Đang commit PRIME")
                    conn.commit()
                except BaseException:
                    conn.rollback()
                    raise
        return ImportResult(dates, file_count, inserted, deleted, passed, inserted - passed)

