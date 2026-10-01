"""Bổ sung bảng Alarm tương thích database LI schema 2."""


def ensure_alarm_schema(conn):
    """Tạo bảng/index nếu thiếu; không thay đổi dữ liệu đã có."""
    conn.execute("""CREATE TABLE IF NOT EXISTS slot_fail_alarm (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alarm_date TEXT NOT NULL,
        eqp TEXT NOT NULL,
        slot INTEGER NOT NULL CHECK(slot BETWEEN 1 AND 48),
        fail_comment TEXT NOT NULL,
        start_datetime TEXT NOT NULL,
        end_datetime TEXT NOT NULL,
        yield_15 REAL,
        target_15 REAL NOT NULL,
        yield_30 REAL,
        target_30 REAL NOT NULL,
        continuous_fail_count_used INTEGER NOT NULL,
        scrap_codes TEXT NOT NULL DEFAULT '',
        lotids TEXT NOT NULL DEFAULT '',
        models TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'Chưa tiến hành'
            CHECK(status IN ('Chưa tiến hành','Đang thực hiện','Đã hoàn thành')),
        date_complete TEXT NOT NULL DEFAULT '',
        quick_check_result TEXT NOT NULL DEFAULT '',
        cal_check_result TEXT NOT NULL DEFAULT '',
        engineer_action TEXT NOT NULL DEFAULT '',
        monitor_day1 TEXT NOT NULL DEFAULT '',
        monitor_day2 TEXT NOT NULL DEFAULT '',
        monitor_day3 TEXT NOT NULL DEFAULT '',
        comment TEXT NOT NULL DEFAULT '',
        evidence_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        row_version INTEGER NOT NULL DEFAULT 1,
        UNIQUE(alarm_date, eqp, slot)
    )""")
    columns = {row[1] for row in conn.execute('PRAGMA table_info(slot_fail_alarm)')}
    if 'different_scrap_fail_count_used' not in columns:
        conn.execute('ALTER TABLE slot_fail_alarm ADD COLUMN different_scrap_fail_count_used INTEGER')
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_alarm_history_list
        ON slot_fail_alarm(alarm_date DESC, end_datetime DESC, eqp, slot)""")
