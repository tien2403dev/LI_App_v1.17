import sqlite3
from contextlib import closing
from datetime import datetime, timezone

from database.connection import connection
from database.schema import verify_database
from domain.cum import CUM_COLUMNS, CumImportResult
from domain.prime import check_cancel, ValidationError
from repositories.import_lock_repository import ImportLockRepository
from repositories.tier_repository import sync_after_cum

BATCH_SIZE = 5000


class CumRepository:
    def __init__(self, database_path):
        """Lưu đường dẫn database để mỗi tác vụ tự mở kết nối."""
        self.database_path = database_path

    def replace_from_staging(self, stage_path, batch_id, file_name, progress, cancel=None):
        """Thay CUM theo DATE, ghi scrap con và đồng bộ TIER trong một transaction."""
        with closing(sqlite3.connect(str(stage_path))) as stage:
            counts = stage.execute(
                "SELECT DATE, COUNT(*) FROM staging_cum_data GROUP BY DATE ORDER BY DATE").fetchall()
            if not counts:
                raise ValidationError("Staging CUM rỗng; không xóa dữ liệu")
            dates = tuple(day for day, _ in counts)
            with connection(self.database_path) as conn:
                verify_database(conn)
                conn.execute("BEGIN IMMEDIATE")
                try:
                    ImportLockRepository.assert_owner(conn, batch_id)
                    check_cancel(cancel)
                    conn.execute("CREATE TEMP TABLE replace_cum_dates(DATE TEXT PRIMARY KEY)")
                    conn.executemany("INSERT INTO replace_cum_dates VALUES(?)", [(d,) for d in dates])
                    deleted = conn.execute("SELECT COUNT(*) FROM cum_data WHERE DATE IN "
                                           "(SELECT DATE FROM replace_cum_dates)").fetchone()[0]
                    conn.execute("DELETE FROM cum_data WHERE DATE IN (SELECT DATE FROM replace_cum_dates)")
                    columns = ','.join(CUM_COLUMNS)
                    cursor = stage.execute(f"SELECT stage_id,{columns} FROM staging_cum_data ORDER BY stage_id")
                    insert_sql = f"INSERT INTO cum_data(id,{columns}) VALUES({','.join('?' for _ in range(13))})"
                    seq = conn.execute("SELECT seq FROM sqlite_sequence WHERE name='cum_data'").fetchone()
                    next_id = max(seq[0] if seq else 0,
                                  conn.execute("SELECT COALESCE(MAX(id),0) FROM cum_data").fetchone()[0]) + 1
                    inserted = details = 0
                    while rows := cursor.fetchmany(BATCH_SIZE):
                        check_cancel(cancel)
                        # Cấp ID tường minh trong transaction để ánh xạ parent/detail chính xác.
                        mapping = {row[0]: next_id + i for i, row in enumerate(rows)}
                        conn.executemany(insert_sql, [(mapping[row[0]], *row[1:]) for row in rows])
                        next_id += len(rows)
                        child_cursor = stage.execute(
                            "SELECT stage_id,scrap_code,qty FROM staging_cum_scrap_detail "
                            "WHERE stage_id BETWEEN ? AND ? ORDER BY stage_id,scrap_code",
                            (rows[0][0], rows[-1][0]))
                        while children := child_cursor.fetchmany(BATCH_SIZE):
                            check_cancel(cancel)
                            conn.executemany(
                                "INSERT INTO cum_scrap_detail(cum_data_id,scrap_code,qty) VALUES(?,?,?)",
                                [(mapping[sid], code, qty) for sid, code, qty in children])
                            details += len(children)
                        inserted += len(rows)
                        progress(f"Đang ghi CUM: {inserted:,} dòng (chưa commit)")
                    progress("Đang đồng bộ TIER cho PRIME")
                    sync_after_cum(conn, dates, cancel)
                    now = datetime.now(timezone.utc).isoformat()
                    conn.executemany("""INSERT INTO data_import_status VALUES('CUM',?,?,?,?)
                        ON CONFLICT(data_type,DATE) DO UPDATE SET imported_at=excluded.imported_at,
                        batch_id=excluded.batch_id,row_count=excluded.row_count""",
                        [(day, now, batch_id, count) for day, count in counts])
                    check_cancel(cancel)
                    ImportLockRepository.renew_in_transaction(conn, batch_id)
                    conn.commit()
                except BaseException:
                    conn.rollback()
                    raise
        return CumImportResult(file_name, inserted, deleted, details, dates)
