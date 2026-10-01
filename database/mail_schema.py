"""Bảng cấu hình Send Mail và lịch sử, tương thích Aging; hỗ trợ gửi tự động."""

MAIL_SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS mail_slot_send_history (
        alarm_date TEXT NOT NULL CHECK(length(alarm_date)=8 AND alarm_date NOT GLOB '*[^0-9]*'),
        eqp TEXT NOT NULL,
        slot INTEGER NOT NULL CHECK(typeof(slot)='integer' AND slot BETWEEN 1 AND 48),
        sent_at TEXT NOT NULL,
        PRIMARY KEY(alarm_date,eqp,slot)
    ) WITHOUT ROWID""",
    """CREATE TABLE IF NOT EXISTS mail_send_lock (
        id INTEGER PRIMARY KEY CHECK(id=1),
        lock_token TEXT NOT NULL, expires_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS mail_template (
        id INTEGER PRIMARY KEY CHECK(id=1),
        subject TEXT NOT NULL, heading TEXT NOT NULL, closing TEXT NOT NULL
    )""",
    """INSERT OR IGNORE INTO mail_template(id,subject,heading,closing)
        VALUES(1,'KTSP SSD gửi bộ phận KTTB Kiểm tra Slot Fail tại công đoạn LI',
        'KTSP SSD nhờ KTTB kiểm tra các slot sau','')""",
    """CREATE TABLE IF NOT EXISTS mail_sender (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id TEXT NOT NULL
        COLLATE NOCASE,

    display_name TEXT NOT NULL,

    password TEXT NOT NULL,

    enabled INTEGER NOT NULL DEFAULT 0
        CHECK (enabled IN (0, 1)),

    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    UNIQUE (user_id)
)""",
    """CREATE TABLE IF NOT EXISTS mail_recipient (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id TEXT NOT NULL
        COLLATE NOCASE,

    display_name TEXT NOT NULL,

    recipient_type TEXT NOT NULL DEFAULT 'NONE'
        CHECK (
            recipient_type IN (
                'RECEIVER',
                'CC',
                'NONE'
            )
        ),

    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    UNIQUE (user_id)
)""",
    """CREATE TABLE IF NOT EXISTS mail_send_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    alarm_date TEXT NOT NULL
        CHECK (
            length(alarm_date) = 8
            AND alarm_date NOT GLOB '*[^0-9]*'
        ),

    sent_at TEXT NOT NULL,

    sender TEXT NOT NULL,

    receivers TEXT NOT NULL,

    cc TEXT NOT NULL DEFAULT '',

    result TEXT NOT NULL DEFAULT 'Success'
        CHECK (result = 'Success'),

    subject TEXT NOT NULL,

    html_content TEXT NOT NULL
)""",
    """CREATE TABLE IF NOT EXISTS auto_send_mail_scheduler (
    id INTEGER PRIMARY KEY
        CHECK (id = 1),

    enable_auto_send INTEGER NOT NULL DEFAULT 0
        CHECK (enable_auto_send IN (0, 1)),

    send_time TEXT NOT NULL DEFAULT '08:00'
        CHECK (
            length(send_time) = 5
            AND send_time GLOB '[0-2][0-9]:[0-5][0-9]'
            AND CAST(
                substr(send_time, 1, 2)
                AS INTEGER
            ) BETWEEN 0 AND 23
        )
)""",
    """CREATE UNIQUE INDEX IF NOT EXISTS ux_mail_sender_single_enabled ON mail_sender(enabled) WHERE enabled=1""",
    """CREATE INDEX IF NOT EXISTS idx_mail_recipient_type ON mail_recipient(recipient_type, display_name)""",
    """INSERT OR IGNORE INTO auto_send_mail_scheduler(id, enable_auto_send, send_time) VALUES(1,0,'07:00')""",
)


def ensure_mail_schema(conn):
    """Bổ sung bảng atomically; có thể chạy lại, không thay dữ liệu đã lưu."""
    conn.execute("SAVEPOINT li_mail_schema")
    try:
        for statement in MAIL_SCHEMA_STATEMENTS:
            conn.execute(statement)
        conn.execute("RELEASE SAVEPOINT li_mail_schema")
    except BaseException:
        conn.execute("ROLLBACK TO SAVEPOINT li_mail_schema")
        conn.execute("RELEASE SAVEPOINT li_mail_schema")
        raise
