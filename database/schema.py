# # from database.connection import connection
# # from database.mail_schema import ensure_mail_schema
# # from database.alarm_schema import ensure_alarm_schema
# #
# # SCHEMA_VERSION = 2
# # APPLICATION_ID = 1279864914  # Distinguish LI database from Aging and unrelated files.
# #
# # # Used by both main database and local staging.
# # PRIME_FIELDS = """
# #     DATE TEXT NOT NULL CHECK(length(DATE)=8 AND DATE NOT GLOB '*[^0-9]*'),
# #     TIME TEXT NOT NULL CHECK(
# #         length(TIME)=8 AND TIME GLOB '[0-2][0-9]:[0-5][0-9]:[0-5][0-9]'
# #         AND CAST(substr(TIME,1,2) AS INTEGER) <= 23),
# #     EQP TEXT NOT NULL CHECK(length(trim(EQP))>0),
# #     PARTNO TEXT NOT NULL CHECK(length(trim(PARTNO))>=5),
# #     LOTNO TEXT NOT NULL CHECK(length(trim(LOTNO))>0),
# #     SLOT INTEGER NOT NULL CHECK(typeof(SLOT)='integer' AND SLOT BETWEEN 1 AND 48),
# #     RESULT TEXT NOT NULL CHECK(RESULT IN ('PASS','FAIL')),
# #     SCRAPCODE TEXT CHECK(SCRAPCODE IS NULL OR
# #         (length(trim(SCRAPCODE))>0 AND upper(SCRAPCODE) NOT IN ('0','NULL'))),
# #     TEST_COUNT INTEGER NOT NULL CHECK(typeof(TEST_COUNT)='integer' AND TEST_COUNT>=1),
# #     SERIAL TEXT NOT NULL CHECK(length(trim(SERIAL))>0 AND upper(SERIAL)<>'NULL'),
# #     QTY INTEGER NOT NULL DEFAULT 1 CHECK(typeof(QTY)='integer' AND QTY=1),
# #     MODEL TEXT NOT NULL CHECK(MODEL=substr(PARTNO,1,5))
# # """
# #
# # CREATE_CUM_DATA_TABLE = """
# # CREATE TABLE IF NOT EXISTS cum_data (
# #     id INTEGER PRIMARY KEY AUTOINCREMENT,
# #
# #     DATE TEXT NOT NULL
# #         CHECK (
# #             length(DATE) = 8
# #             AND DATE NOT GLOB '*[^0-9]*'
# #         ),
# #
# #     TIME TEXT NOT NULL
# #         CHECK (
# #             length(TIME) = 8
# #             AND TIME GLOB '[0-2][0-9]:[0-5][0-9]:[0-5][0-9]'
# #             AND CAST(substr(TIME, 1, 2) AS INTEGER) BETWEEN 0 AND 23
# #         ),
# #
# #     LOTID TEXT,
# #
# #     PRODUCT TEXT NOT NULL,
# #
# #     EQPID TEXT NOT NULL,
# #
# #     INQTY INTEGER NOT NULL
# #         CHECK (
# #             typeof(INQTY) = 'integer'
# #             AND INQTY >= 0
# #         ),
# #
# #     OUTQTY INTEGER NOT NULL
# #         CHECK (
# #             typeof(OUTQTY) = 'integer'
# #             AND OUTQTY >= 0
# #         ),
# #
# #     FAILQTY INTEGER NOT NULL
# #         CHECK (
# #             typeof(FAILQTY) = 'integer'
# #             AND FAILQTY >= 0
# #         ),
# #
# #     YIELD REAL NOT NULL
# #         CHECK (
# #             typeof(YIELD) IN ('integer', 'real')
# #         ),
# #
# #     SCRAP TEXT NOT NULL DEFAULT '',
# #
# #     MODEL TEXT NOT NULL
# #         CHECK (length(MODEL) = 5),
# #
# #     TIER TEXT NOT NULL
# # )
# # """
# #
# # CREATE_CUM_SCRAP_DETAIL_TABLE = """
# # CREATE TABLE IF NOT EXISTS cum_scrap_detail (
# #     id INTEGER PRIMARY KEY AUTOINCREMENT,
# #
# #     cum_data_id INTEGER NOT NULL,
# #
# #     scrap_code TEXT NOT NULL
# #         CHECK (
# #             length(scrap_code) = 4
# #             AND scrap_code NOT GLOB '*[^0-9]*'
# #         ),
# #
# #     qty INTEGER NOT NULL
# #         CHECK (
# #             typeof(qty) = 'integer'
# #             AND qty BETWEEN 1 AND 99
# #         ),
# #
# #     FOREIGN KEY (cum_data_id)
# #         REFERENCES cum_data(id)
# #         ON DELETE CASCADE,
# #
# #     UNIQUE (
# #         cum_data_id,
# #         scrap_code
# #     )
# # )
# # """
# #
# # CREATE_FRESH_SCHEMA = [
# #     "CREATE TABLE schema_version(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL, description TEXT NOT NULL)",
# #     f"CREATE TABLE prime_data(id INTEGER PRIMARY KEY AUTOINCREMENT, {PRIME_FIELDS})",
# #     """CREATE TABLE import_lock(
# #         lock_name TEXT PRIMARY KEY CHECK(lock_name='GLOBAL_IMPORT_LOCK'),
# #         batch_id TEXT NOT NULL, import_type TEXT NOT NULL,
# #         machine_name TEXT NOT NULL, windows_user TEXT NOT NULL,
# #         process_id INTEGER NOT NULL, source TEXT NOT NULL,
# #         acquired_at REAL NOT NULL, heartbeat_at REAL NOT NULL, expires_at REAL NOT NULL)""",
# #     """CREATE TABLE data_import_status(
# #         data_type TEXT NOT NULL, DATE TEXT NOT NULL,
# #         imported_at TEXT NOT NULL, batch_id TEXT NOT NULL, row_count INTEGER NOT NULL,
# #         PRIMARY KEY(data_type, DATE))""",
# #     "ALTER TABLE prime_data ADD COLUMN TIER TEXT",
# #     CREATE_CUM_DATA_TABLE,
# #     CREATE_CUM_SCRAP_DETAIL_TABLE,
# #     "CREATE INDEX idx_cum_date ON cum_data(DATE)",
# #     "CREATE INDEX idx_cum_lot_date_tier ON cum_data(LOTID, DATE, TIER)",
# #     "CREATE INDEX idx_cum_eqp_date ON cum_data(EQPID, DATE)",
# #     "CREATE INDEX idx_cum_scrap_code ON cum_scrap_detail(scrap_code, cum_data_id)",
# #     "CREATE INDEX IF NOT EXISTS idx_prime_daily_fail ON prime_data(EQP, DATE, TIER, MODEL, SCRAPCODE, QTY) WHERE RESULT = 'FAIL' AND COALESCE(SCRAPCODE, '') <> ''",
# #     "CREATE INDEX IF NOT EXISTS idx_prime_first_slot_daily ON prime_data(EQP, SLOT, DATE, TIER, MODEL, RESULT, QTY) WHERE TEST_COUNT = 1",
# #     "CREATE INDEX IF NOT EXISTS idx_prime_first_slot ON prime_data(EQP, DATE, TIER, MODEL, SLOT, RESULT, QTY) WHERE TEST_COUNT = 1",
# #     "CREATE INDEX idx_prime_date ON prime_data(DATE)",
# #     "CREATE INDEX idx_prime_eqp_date ON prime_data(EQP, DATE)",
# #     "CREATE INDEX idx_prime_slot_time ON prime_data(EQP, SLOT, DATE, TIME)",
# #     "CREATE INDEX idx_prime_slot ON prime_data(SLOT)",
# #     "CREATE INDEX idx_prime_model ON prime_data(MODEL)",
# #     "CREATE INDEX idx_prime_tier_model ON prime_data(TIER, MODEL)",
# #     "CREATE INDEX idx_prime_scrapcode ON prime_data(SCRAPCODE)",
# #     "CREATE INDEX idx_cum_model ON cum_data(MODEL)",
# #     "CREATE INDEX idx_cum_tier_date_model ON cum_data(TIER, DATE, MODEL)",
# #     "CREATE INDEX idx_cum_tier_model_date_eqp ON cum_data(TIER, MODEL, DATE, EQPID)",
# # ]
# #
# # PERFORMANCE_INDEXES = [
# #     "CREATE INDEX IF NOT EXISTS idx_prime_first_slot_daily ON prime_data(EQP, SLOT, DATE, TIER, MODEL, RESULT, QTY) WHERE TEST_COUNT = 1",
# #     "CREATE INDEX IF NOT EXISTS idx_prime_first_slot ON prime_data(EQP, DATE, TIER, MODEL, SLOT, RESULT, QTY) WHERE TEST_COUNT = 1",
# #     "CREATE INDEX IF NOT EXISTS idx_prime_daily_fail ON prime_data(EQP, DATE, TIER, MODEL, SCRAPCODE, QTY) WHERE RESULT = 'FAIL' AND COALESCE(SCRAPCODE, '') <> ''",
# #     "CREATE INDEX IF NOT EXISTS idx_cum_date ON cum_data(DATE)",
# #     "CREATE INDEX IF NOT EXISTS idx_cum_lot_date_tier ON cum_data(LOTID, DATE, TIER)",
# #     "CREATE INDEX IF NOT EXISTS idx_cum_eqp_date ON cum_data(EQPID, DATE)",
# #     "CREATE INDEX IF NOT EXISTS idx_cum_scrap_code ON cum_scrap_detail(scrap_code, cum_data_id)",
# #     "CREATE INDEX IF NOT EXISTS idx_prime_date ON prime_data(DATE)",
# #     "CREATE INDEX IF NOT EXISTS idx_prime_eqp_date ON prime_data(EQP, DATE)",
# #     "CREATE INDEX IF NOT EXISTS idx_prime_slot_time ON prime_data(EQP, SLOT, DATE, TIME)",
# #     "CREATE INDEX IF NOT EXISTS idx_prime_slot ON prime_data(SLOT)",
# #     "CREATE INDEX IF NOT EXISTS idx_prime_model ON prime_data(MODEL)",
# #     "CREATE INDEX IF NOT EXISTS idx_prime_tier_model ON prime_data(TIER, MODEL)",
# #     "CREATE INDEX IF NOT EXISTS idx_prime_scrapcode ON prime_data(SCRAPCODE)",
# #     "CREATE INDEX IF NOT EXISTS idx_cum_model ON cum_data(MODEL)",
# #     "CREATE INDEX IF NOT EXISTS idx_cum_tier_date_model ON cum_data(TIER, DATE, MODEL)",
# #     "CREATE INDEX IF NOT EXISTS idx_cum_tier_model_date_eqp ON cum_data(TIER, MODEL, DATE, EQPID)",
# # ]
# #
# #
# # def ensure_performance_indexes(conn):
# #     """Bổ sung index đọc/lọc cho cả database mới và database schema 2 đang dùng."""
# #     for statement in PERFORMANCE_INDEXES:
# #         conn.execute(statement)
# #
# #
# # def verify_database(conn):
# #     """Kiểm tra đúng database LI và phiên bản schema tương thích."""
# #     if conn.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID:
# #         raise ValueError("Đây không phải database LI. Không dùng database Aging.")
# #     row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
# #     if row[0] != SCHEMA_VERSION:
# #         raise ValueError("Version database không tương thích. Bản này cần database LI mới (schema 2); hãy sao lưu và di chuyển database cũ trước khi mở lại app.")
# #
# #
# # def initialize_database(database_path):
# #     """Tạo schema cho database mới hoặc kiểm tra database đã tồn tại."""
# #     with connection(database_path) as conn:
# #         tables = {row[0] for row in conn.execute(
# #             "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
# #         if tables:
# #             verify_database(conn)
# #             ensure_performance_indexes(conn)
# #             ensure_file_management_schema(conn)
# #             ensure_machine_slot_yield_schema(conn)
# #             ensure_mail_schema(conn)
# #             ensure_alarm_schema(conn)
# #             if conn.execute("PRAGMA journal_mode").fetchone()[0].lower() != "delete":
# #                 raise ValueError("Database LI phải dùng journal_mode=DELETE.")
# #             return
# #         if conn.execute("PRAGMA application_id").fetchone()[0] not in (0, APPLICATION_ID):
# #             raise ValueError("Database thuộc ứng dụng khác.")
# #         conn.execute("PRAGMA journal_mode = DELETE")
# #         conn.execute("BEGIN IMMEDIATE")
# #         try:
# #             # Another process may have initialized while this process was waiting.
# #             if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchone():
# #                 verify_database(conn)
# #             else:
# #                 for statement in CREATE_FRESH_SCHEMA:
# #                     conn.execute(statement)
# #                 conn.execute(f"PRAGMA application_id = {APPLICATION_ID}")
# #                 conn.execute(
# #                     "INSERT INTO schema_version VALUES(2, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
# #                     ("LI PRIME + CUM, scrap detail, TIER and global import lock",))
# #             ensure_file_management_schema(conn)
# #             ensure_machine_slot_yield_schema(conn)
# #             ensure_mail_schema(conn)
# #             ensure_alarm_schema(conn)
# #             conn.commit()
# #         except BaseException:
# #             conn.rollback()
# #             raise
# #
# #
# # CREATE_AUTO_IMPORT_SCHEDULER_TABLE = """
# # CREATE TABLE IF NOT EXISTS auto_import_scheduler (
# #     id INTEGER PRIMARY KEY
# #         CHECK (id = 1),
# #
# #     enable_auto_import INTEGER NOT NULL DEFAULT 0
# #         CHECK (enable_auto_import IN (0, 1)),
# #
# #     import_time TEXT NOT NULL DEFAULT '03:00'
# #         CHECK (
# #             length(import_time) = 5
# #             AND import_time GLOB '[0-2][0-9]:[0-5][0-9]'
# #             AND CAST(substr(import_time, 1, 2) AS INTEGER)
# #                 BETWEEN 0 AND 23
# #         ),
# #
# #     log_folder TEXT NOT NULL DEFAULT '',
# #
# #     last_import_date TEXT
# #         CHECK (
# #             last_import_date IS NULL
# #             OR (
# #                 length(last_import_date) = 8
# #                 AND last_import_date NOT GLOB '*[^0-9]*'
# #             )
# #         )
# # )
# # """
# #
# #
# # def ensure_file_management_schema(conn):
# #     """Bổ sung cấu hình File Management, giữ nguyên dữ liệu và schema LI 2."""
# #     conn.execute(CREATE_AUTO_IMPORT_SCHEDULER_TABLE)
# #     conn.execute("INSERT OR IGNORE INTO auto_import_scheduler(id) VALUES(1)")
# #
# #
# # CREATE_MACHINE_SLOT_YIELD_CONFIG_TABLE = """
# # CREATE TABLE IF NOT EXISTS machine_slot_yield_config (
# #     id INTEGER PRIMARY KEY CHECK (id = 1),
# #     log_folder TEXT NOT NULL DEFAULT '',
# #     target_15 REAL NOT NULL DEFAULT 70.0
# #         CHECK (typeof(target_15) IN ('integer', 'real')
# #                AND target_15 BETWEEN 0 AND 100),
# #     target_30 REAL NOT NULL DEFAULT 75.0
# #         CHECK (typeof(target_30) IN ('integer', 'real')
# #                AND target_30 BETWEEN 0 AND 100),
# #     continuous_fail_count INTEGER NOT NULL DEFAULT 3
# #         CHECK (typeof(continuous_fail_count) = 'integer'
# #                AND continuous_fail_count >= 1),
# #     updated_at TEXT
# # )
# # """
# #
# #
# # def ensure_machine_slot_yield_schema(conn):
# #     """Bổ sung cấu hình ngưỡng Machine Slot Yield cho DB mới/cũ."""
# #     conn.execute(CREATE_MACHINE_SLOT_YIELD_CONFIG_TABLE)
# #     conn.execute(
# #         "INSERT OR IGNORE INTO machine_slot_yield_config(id) VALUES(1)"
# #     )
# from database.connection import connection
# from database.mail_schema import ensure_mail_schema
# from database.alarm_schema import ensure_alarm_schema
#
# SCHEMA_VERSION = 2
# APPLICATION_ID = 1279864914  # Distinguish LI database from Aging and unrelated files.
#
# # Used by both main database and local staging.
# PRIME_FIELDS = """
#     DATE TEXT NOT NULL CHECK(length(DATE)=8 AND DATE NOT GLOB '*[^0-9]*'),
#     TIME TEXT NOT NULL CHECK(
#         length(TIME)=8 AND TIME GLOB '[0-2][0-9]:[0-5][0-9]:[0-5][0-9]'
#         AND CAST(substr(TIME,1,2) AS INTEGER) <= 23),
#     EQP TEXT NOT NULL CHECK(length(trim(EQP))>0),
#     PARTNO TEXT NOT NULL CHECK(length(trim(PARTNO))>=5),
#     LOTNO TEXT NOT NULL CHECK(length(trim(LOTNO))>0),
#     SLOT INTEGER NOT NULL CHECK(typeof(SLOT)='integer' AND SLOT BETWEEN 1 AND 48),
#     RESULT TEXT NOT NULL CHECK(RESULT IN ('PASS','FAIL')),
#     SCRAPCODE TEXT CHECK(SCRAPCODE IS NULL OR
#         (length(trim(SCRAPCODE))>0 AND upper(SCRAPCODE) NOT IN ('0','NULL'))),
#     TEST_COUNT INTEGER NOT NULL CHECK(typeof(TEST_COUNT)='integer' AND TEST_COUNT>=0),
#     SERIAL TEXT NOT NULL CHECK(length(trim(SERIAL))>0 AND upper(SERIAL)<>'NULL'),
#     QTY INTEGER NOT NULL DEFAULT 1 CHECK(typeof(QTY)='integer' AND QTY=1),
#     MODEL TEXT NOT NULL CHECK(MODEL=substr(PARTNO,1,5))
# """
#
# CREATE_CUM_DATA_TABLE = """
# CREATE TABLE IF NOT EXISTS cum_data (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#
#     DATE TEXT NOT NULL
#         CHECK (
#             length(DATE) = 8
#             AND DATE NOT GLOB '*[^0-9]*'
#         ),
#
#     TIME TEXT NOT NULL
#         CHECK (
#             length(TIME) = 8
#             AND TIME GLOB '[0-2][0-9]:[0-5][0-9]:[0-5][0-9]'
#             AND CAST(substr(TIME, 1, 2) AS INTEGER) BETWEEN 0 AND 23
#         ),
#
#     LOTID TEXT,
#
#     PRODUCT TEXT NOT NULL,
#
#     EQPID TEXT NOT NULL,
#
#     INQTY INTEGER NOT NULL
#         CHECK (
#             typeof(INQTY) = 'integer'
#             AND INQTY >= 0
#         ),
#
#     OUTQTY INTEGER NOT NULL
#         CHECK (
#             typeof(OUTQTY) = 'integer'
#             AND OUTQTY >= 0
#         ),
#
#     FAILQTY INTEGER NOT NULL
#         CHECK (
#             typeof(FAILQTY) = 'integer'
#             AND FAILQTY >= 0
#         ),
#
#     YIELD REAL NOT NULL
#         CHECK (
#             typeof(YIELD) IN ('integer', 'real')
#         ),
#
#     SCRAP TEXT NOT NULL DEFAULT '',
#
#     MODEL TEXT NOT NULL
#         CHECK (length(MODEL) = 5),
#
#     TIER TEXT NOT NULL
# )
# """
#
# CREATE_CUM_SCRAP_DETAIL_TABLE = """
# CREATE TABLE IF NOT EXISTS cum_scrap_detail (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#
#     cum_data_id INTEGER NOT NULL,
#
#     scrap_code TEXT NOT NULL
#         CHECK (
#             length(scrap_code) = 4
#             AND scrap_code NOT GLOB '*[^0-9]*'
#         ),
#
#     qty INTEGER NOT NULL
#         CHECK (
#             typeof(qty) = 'integer'
#             AND qty BETWEEN 1 AND 99
#         ),
#
#     FOREIGN KEY (cum_data_id)
#         REFERENCES cum_data(id)
#         ON DELETE CASCADE,
#
#     UNIQUE (
#         cum_data_id,
#         scrap_code
#     )
# )
# """
#
# CREATE_FRESH_SCHEMA = [
#     "CREATE TABLE schema_version(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL, description TEXT NOT NULL)",
#     f"CREATE TABLE prime_data(id INTEGER PRIMARY KEY AUTOINCREMENT, {PRIME_FIELDS})",
#     """CREATE TABLE import_lock(
#         lock_name TEXT PRIMARY KEY CHECK(lock_name='GLOBAL_IMPORT_LOCK'),
#         batch_id TEXT NOT NULL, import_type TEXT NOT NULL,
#         machine_name TEXT NOT NULL, windows_user TEXT NOT NULL,
#         process_id INTEGER NOT NULL, source TEXT NOT NULL,
#         acquired_at REAL NOT NULL, heartbeat_at REAL NOT NULL, expires_at REAL NOT NULL)""",
#     """CREATE TABLE data_import_status(
#         data_type TEXT NOT NULL, DATE TEXT NOT NULL,
#         imported_at TEXT NOT NULL, batch_id TEXT NOT NULL, row_count INTEGER NOT NULL,
#         PRIMARY KEY(data_type, DATE))""",
#     "ALTER TABLE prime_data ADD COLUMN TIER TEXT",
#     CREATE_CUM_DATA_TABLE,
#     CREATE_CUM_SCRAP_DETAIL_TABLE,
#     "CREATE INDEX idx_cum_date ON cum_data(DATE)",
#     "CREATE INDEX idx_cum_lot_date_tier ON cum_data(LOTID, DATE, TIER)",
#     "CREATE INDEX idx_cum_eqp_date ON cum_data(EQPID, DATE)",
#     "CREATE INDEX idx_cum_scrap_code ON cum_scrap_detail(scrap_code, cum_data_id)",
#     "CREATE INDEX IF NOT EXISTS idx_prime_daily_fail ON prime_data(EQP, DATE, TIER, MODEL, SCRAPCODE, QTY) WHERE RESULT = 'FAIL' AND COALESCE(SCRAPCODE, '') <> ''",
#     "CREATE INDEX IF NOT EXISTS idx_prime_first_slot_daily ON prime_data(EQP, SLOT, DATE, TIER, MODEL, RESULT, QTY) WHERE TEST_COUNT = 0",
#     "CREATE INDEX IF NOT EXISTS idx_prime_first_slot ON prime_data(EQP, DATE, TIER, MODEL, SLOT, RESULT, QTY) WHERE TEST_COUNT = 0",
#     "CREATE INDEX idx_prime_date ON prime_data(DATE)",
#     "CREATE INDEX idx_prime_eqp_date ON prime_data(EQP, DATE)",
#     "CREATE INDEX idx_prime_slot_time ON prime_data(EQP, SLOT, DATE, TIME)",
#     "CREATE INDEX idx_prime_slot ON prime_data(SLOT)",
#     "CREATE INDEX idx_prime_model ON prime_data(MODEL)",
#     "CREATE INDEX idx_prime_tier_model ON prime_data(TIER, MODEL)",
#     "CREATE INDEX idx_prime_scrapcode ON prime_data(SCRAPCODE)",
#     "CREATE INDEX idx_cum_model ON cum_data(MODEL)",
#     "CREATE INDEX idx_cum_tier_date_model ON cum_data(TIER, DATE, MODEL)",
#     "CREATE INDEX idx_cum_tier_model_date_eqp ON cum_data(TIER, MODEL, DATE, EQPID)",
# ]
#
# PERFORMANCE_INDEXES = [
#     "CREATE INDEX IF NOT EXISTS idx_prime_first_slot_daily ON prime_data(EQP, SLOT, DATE, TIER, MODEL, RESULT, QTY) WHERE TEST_COUNT = 0",
#     "CREATE INDEX IF NOT EXISTS idx_prime_first_slot ON prime_data(EQP, DATE, TIER, MODEL, SLOT, RESULT, QTY) WHERE TEST_COUNT = 0",
#     "CREATE INDEX IF NOT EXISTS idx_prime_daily_fail ON prime_data(EQP, DATE, TIER, MODEL, SCRAPCODE, QTY) WHERE RESULT = 'FAIL' AND COALESCE(SCRAPCODE, '') <> ''",
#     "CREATE INDEX IF NOT EXISTS idx_cum_date ON cum_data(DATE)",
#     "CREATE INDEX IF NOT EXISTS idx_cum_lot_date_tier ON cum_data(LOTID, DATE, TIER)",
#     "CREATE INDEX IF NOT EXISTS idx_cum_eqp_date ON cum_data(EQPID, DATE)",
#     "CREATE INDEX IF NOT EXISTS idx_cum_scrap_code ON cum_scrap_detail(scrap_code, cum_data_id)",
#     "CREATE INDEX IF NOT EXISTS idx_prime_date ON prime_data(DATE)",
#     "CREATE INDEX IF NOT EXISTS idx_prime_eqp_date ON prime_data(EQP, DATE)",
#     "CREATE INDEX IF NOT EXISTS idx_prime_slot_time ON prime_data(EQP, SLOT, DATE, TIME)",
#     "CREATE INDEX IF NOT EXISTS idx_prime_slot ON prime_data(SLOT)",
#     "CREATE INDEX IF NOT EXISTS idx_prime_model ON prime_data(MODEL)",
#     "CREATE INDEX IF NOT EXISTS idx_prime_tier_model ON prime_data(TIER, MODEL)",
#     "CREATE INDEX IF NOT EXISTS idx_prime_scrapcode ON prime_data(SCRAPCODE)",
#     "CREATE INDEX IF NOT EXISTS idx_cum_model ON cum_data(MODEL)",
#     "CREATE INDEX IF NOT EXISTS idx_cum_tier_date_model ON cum_data(TIER, DATE, MODEL)",
#     "CREATE INDEX IF NOT EXISTS idx_cum_tier_model_date_eqp ON cum_data(TIER, MODEL, DATE, EQPID)",
# ]
#
#
# def ensure_performance_indexes(conn):
#     """Bổ sung index đọc/lọc cho cả database mới và database schema 2 đang dùng."""
#     for statement in PERFORMANCE_INDEXES:
#         conn.execute(statement)
#
#
# def verify_database(conn):
#     """Kiểm tra đúng database LI và phiên bản schema tương thích."""
#     if conn.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID:
#         raise ValueError("Đây không phải database LI. Không dùng database Aging.")
#     row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
#     if row[0] != SCHEMA_VERSION:
#         raise ValueError("Version database không tương thích. Bản này cần database LI mới (schema 2); hãy sao lưu và di chuyển database cũ trước khi mở lại app.")
#
#
# def initialize_database(database_path):
#     """Tạo schema cho database mới hoặc kiểm tra database đã tồn tại."""
#     with connection(database_path, timeout=60) as conn:
#         tables = {row[0] for row in conn.execute(
#             "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
#         if tables:
#             verify_database(conn)
#             if _startup_schema_complete(conn):
#                 if conn.execute("PRAGMA journal_mode").fetchone()[0].lower() != "delete":
#                     raise ValueError("Database LI phải dùng journal_mode=DELETE.")
#                 return
#             ensure_performance_indexes(conn)
#             ensure_file_management_schema(conn)
#             ensure_machine_slot_yield_schema(conn)
#             ensure_mail_schema(conn)
#             ensure_alarm_schema(conn)
#             if conn.execute("PRAGMA journal_mode").fetchone()[0].lower() != "delete":
#                 raise ValueError("Database LI phải dùng journal_mode=DELETE.")
#             return
#         if conn.execute("PRAGMA application_id").fetchone()[0] not in (0, APPLICATION_ID):
#             raise ValueError("Database thuộc ứng dụng khác.")
#         conn.execute("PRAGMA journal_mode = DELETE")
#         conn.execute("BEGIN IMMEDIATE")
#         try:
#             # Another process may have initialized while this process was waiting.
#             if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchone():
#                 verify_database(conn)
#             else:
#                 for statement in CREATE_FRESH_SCHEMA:
#                     conn.execute(statement)
#                 conn.execute(f"PRAGMA application_id = {APPLICATION_ID}")
#                 conn.execute(
#                     "INSERT INTO schema_version VALUES(2, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
#                     ("LI PRIME + CUM, scrap detail, TIER and global import lock",))
#             ensure_file_management_schema(conn)
#             ensure_machine_slot_yield_schema(conn)
#             ensure_mail_schema(conn)
#             ensure_alarm_schema(conn)
#             conn.commit()
#         except BaseException:
#             conn.rollback()
#             raise
#
#
# CREATE_AUTO_IMPORT_SCHEDULER_TABLE = """
# CREATE TABLE IF NOT EXISTS auto_import_scheduler (
#     id INTEGER PRIMARY KEY
#         CHECK (id = 1),
#
#     enable_auto_import INTEGER NOT NULL DEFAULT 0
#         CHECK (enable_auto_import IN (0, 1)),
#
#     import_time TEXT NOT NULL DEFAULT '03:00'
#         CHECK (
#             length(import_time) = 5
#             AND import_time GLOB '[0-2][0-9]:[0-5][0-9]'
#             AND CAST(substr(import_time, 1, 2) AS INTEGER)
#                 BETWEEN 0 AND 23
#         ),
#
#     log_folder TEXT NOT NULL DEFAULT '',
#
#     last_import_date TEXT
#         CHECK (
#             last_import_date IS NULL
#             OR (
#                 length(last_import_date) = 8
#                 AND last_import_date NOT GLOB '*[^0-9]*'
#             )
#         )
# )
# """
#
#
# def ensure_file_management_schema(conn):
#     """Bổ sung cấu hình File Management, giữ nguyên dữ liệu và schema LI 2."""
#     conn.execute(CREATE_AUTO_IMPORT_SCHEDULER_TABLE)
#     conn.execute("INSERT OR IGNORE INTO auto_import_scheduler(id) VALUES(1)")
#
#
# CREATE_MACHINE_SLOT_YIELD_CONFIG_TABLE = """
# CREATE TABLE IF NOT EXISTS machine_slot_yield_config (
#     id INTEGER PRIMARY KEY CHECK (id = 1),
#     log_folder TEXT NOT NULL DEFAULT '',
#     target_15 REAL NOT NULL DEFAULT 70.0
#         CHECK (typeof(target_15) IN ('integer', 'real')
#                AND target_15 BETWEEN 0 AND 100),
#     target_30 REAL NOT NULL DEFAULT 75.0
#         CHECK (typeof(target_30) IN ('integer', 'real')
#                AND target_30 BETWEEN 0 AND 100),
#     continuous_fail_count INTEGER NOT NULL DEFAULT 3
#         CHECK (typeof(continuous_fail_count) = 'integer'
#                AND continuous_fail_count >= 1),
#     updated_at TEXT
# )
# """
#
#
# def ensure_machine_slot_yield_schema(conn):
#     """Bổ sung cấu hình ngưỡng Machine Slot Yield cho DB mới/cũ."""
#     conn.execute(CREATE_MACHINE_SLOT_YIELD_CONFIG_TABLE)
#     columns = {row[1] for row in conn.execute('PRAGMA table_info(machine_slot_yield_config)')}
#     if 'different_scrap_fail_count' not in columns:
#         conn.execute("""ALTER TABLE machine_slot_yield_config ADD COLUMN
#             different_scrap_fail_count INTEGER NOT NULL DEFAULT 3
#             CHECK(typeof(different_scrap_fail_count)='integer' AND different_scrap_fail_count>=2)""")
#     conn.execute(
#         "INSERT OR IGNORE INTO machine_slot_yield_config(id) VALUES(1)"
#     )
#
#
# def _startup_schema_complete(conn):
#     """Read metadata only on normal startup; migrate only missing objects."""
#     import re
#     from database.mail_schema import MAIL_SCHEMA_STATEMENTS
#     statements = (CREATE_FRESH_SCHEMA + PERFORMANCE_INDEXES +
#                   list(MAIL_SCHEMA_STATEMENTS) +
#                   [CREATE_AUTO_IMPORT_SCHEDULER_TABLE,
#                    CREATE_MACHINE_SLOT_YIELD_CONFIG_TABLE])
#     names = set()
#     for statement in statements:
#         match = re.search(r"CREATE\s+(?:UNIQUE\s+)?(?:TABLE|INDEX)\s+(?:IF NOT EXISTS\s+)?(\w+)",
#                           statement, re.IGNORECASE)
#         if match:
#             names.add(match.group(1))
#     names.update(("slot_fail_alarm", "idx_alarm_history_list"))
#     existing = {row[0] for row in conn.execute("SELECT name FROM sqlite_master")}
#     if not names <= existing:
#         return False
#     for table, column in (("machine_slot_yield_config", "different_scrap_fail_count"),
#                           ("slot_fail_alarm", "different_scrap_fail_count_used")):
#         if column not in {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}:
#             return False
#     for table in ("mail_template", "auto_send_mail_scheduler", "auto_import_scheduler",
#                   "machine_slot_yield_config"):
#         if conn.execute(f"SELECT 1 FROM {table} WHERE id=1").fetchone() is None:
#             return False
#     return True
# from database.connection import connection
# from database.mail_schema import ensure_mail_schema
# from database.alarm_schema import ensure_alarm_schema
#
# SCHEMA_VERSION = 2
# APPLICATION_ID = 1279864914  # Distinguish LI database from Aging and unrelated files.
#
# # Used by both main database and local staging.
# PRIME_FIELDS = """
#     DATE TEXT NOT NULL CHECK(length(DATE)=8 AND DATE NOT GLOB '*[^0-9]*'),
#     TIME TEXT NOT NULL CHECK(
#         length(TIME)=8 AND TIME GLOB '[0-2][0-9]:[0-5][0-9]:[0-5][0-9]'
#         AND CAST(substr(TIME,1,2) AS INTEGER) <= 23),
#     EQP TEXT NOT NULL CHECK(length(trim(EQP))>0),
#     PARTNO TEXT NOT NULL CHECK(length(trim(PARTNO))>=5),
#     LOTNO TEXT NOT NULL CHECK(length(trim(LOTNO))>0),
#     SLOT INTEGER NOT NULL CHECK(typeof(SLOT)='integer' AND SLOT BETWEEN 1 AND 48),
#     RESULT TEXT NOT NULL CHECK(RESULT IN ('PASS','FAIL')),
#     SCRAPCODE TEXT CHECK(SCRAPCODE IS NULL OR
#         (length(trim(SCRAPCODE))>0 AND upper(SCRAPCODE) NOT IN ('0','NULL'))),
#     TEST_COUNT INTEGER NOT NULL CHECK(typeof(TEST_COUNT)='integer' AND TEST_COUNT>=1),
#     SERIAL TEXT NOT NULL CHECK(length(trim(SERIAL))>0 AND upper(SERIAL)<>'NULL'),
#     QTY INTEGER NOT NULL DEFAULT 1 CHECK(typeof(QTY)='integer' AND QTY=1),
#     MODEL TEXT NOT NULL CHECK(MODEL=substr(PARTNO,1,5))
# """
#
# CREATE_CUM_DATA_TABLE = """
# CREATE TABLE IF NOT EXISTS cum_data (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#
#     DATE TEXT NOT NULL
#         CHECK (
#             length(DATE) = 8
#             AND DATE NOT GLOB '*[^0-9]*'
#         ),
#
#     TIME TEXT NOT NULL
#         CHECK (
#             length(TIME) = 8
#             AND TIME GLOB '[0-2][0-9]:[0-5][0-9]:[0-5][0-9]'
#             AND CAST(substr(TIME, 1, 2) AS INTEGER) BETWEEN 0 AND 23
#         ),
#
#     LOTID TEXT,
#
#     PRODUCT TEXT NOT NULL,
#
#     EQPID TEXT NOT NULL,
#
#     INQTY INTEGER NOT NULL
#         CHECK (
#             typeof(INQTY) = 'integer'
#             AND INQTY >= 0
#         ),
#
#     OUTQTY INTEGER NOT NULL
#         CHECK (
#             typeof(OUTQTY) = 'integer'
#             AND OUTQTY >= 0
#         ),
#
#     FAILQTY INTEGER NOT NULL
#         CHECK (
#             typeof(FAILQTY) = 'integer'
#             AND FAILQTY >= 0
#         ),
#
#     YIELD REAL NOT NULL
#         CHECK (
#             typeof(YIELD) IN ('integer', 'real')
#         ),
#
#     SCRAP TEXT NOT NULL DEFAULT '',
#
#     MODEL TEXT NOT NULL
#         CHECK (length(MODEL) = 5),
#
#     TIER TEXT NOT NULL
# )
# """
#
# CREATE_CUM_SCRAP_DETAIL_TABLE = """
# CREATE TABLE IF NOT EXISTS cum_scrap_detail (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#
#     cum_data_id INTEGER NOT NULL,
#
#     scrap_code TEXT NOT NULL
#         CHECK (
#             length(scrap_code) = 4
#             AND scrap_code NOT GLOB '*[^0-9]*'
#         ),
#
#     qty INTEGER NOT NULL
#         CHECK (
#             typeof(qty) = 'integer'
#             AND qty BETWEEN 1 AND 99
#         ),
#
#     FOREIGN KEY (cum_data_id)
#         REFERENCES cum_data(id)
#         ON DELETE CASCADE,
#
#     UNIQUE (
#         cum_data_id,
#         scrap_code
#     )
# )
# """
#
# CREATE_FRESH_SCHEMA = [
#     "CREATE TABLE schema_version(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL, description TEXT NOT NULL)",
#     f"CREATE TABLE prime_data(id INTEGER PRIMARY KEY AUTOINCREMENT, {PRIME_FIELDS})",
#     """CREATE TABLE import_lock(
#         lock_name TEXT PRIMARY KEY CHECK(lock_name='GLOBAL_IMPORT_LOCK'),
#         batch_id TEXT NOT NULL, import_type TEXT NOT NULL,
#         machine_name TEXT NOT NULL, windows_user TEXT NOT NULL,
#         process_id INTEGER NOT NULL, source TEXT NOT NULL,
#         acquired_at REAL NOT NULL, heartbeat_at REAL NOT NULL, expires_at REAL NOT NULL)""",
#     """CREATE TABLE data_import_status(
#         data_type TEXT NOT NULL, DATE TEXT NOT NULL,
#         imported_at TEXT NOT NULL, batch_id TEXT NOT NULL, row_count INTEGER NOT NULL,
#         PRIMARY KEY(data_type, DATE))""",
#     "ALTER TABLE prime_data ADD COLUMN TIER TEXT",
#     CREATE_CUM_DATA_TABLE,
#     CREATE_CUM_SCRAP_DETAIL_TABLE,
#     "CREATE INDEX idx_cum_date ON cum_data(DATE)",
#     "CREATE INDEX idx_cum_lot_date_tier ON cum_data(LOTID, DATE, TIER)",
#     "CREATE INDEX idx_cum_eqp_date ON cum_data(EQPID, DATE)",
#     "CREATE INDEX idx_cum_scrap_code ON cum_scrap_detail(scrap_code, cum_data_id)",
#     "CREATE INDEX IF NOT EXISTS idx_prime_daily_fail ON prime_data(EQP, DATE, TIER, MODEL, SCRAPCODE, QTY) WHERE RESULT = 'FAIL' AND COALESCE(SCRAPCODE, '') <> ''",
#     "CREATE INDEX IF NOT EXISTS idx_prime_first_slot_daily ON prime_data(EQP, SLOT, DATE, TIER, MODEL, RESULT, QTY) WHERE TEST_COUNT = 1",
#     "CREATE INDEX IF NOT EXISTS idx_prime_first_slot ON prime_data(EQP, DATE, TIER, MODEL, SLOT, RESULT, QTY) WHERE TEST_COUNT = 1",
#     "CREATE INDEX idx_prime_date ON prime_data(DATE)",
#     "CREATE INDEX idx_prime_eqp_date ON prime_data(EQP, DATE)",
#     "CREATE INDEX idx_prime_slot_time ON prime_data(EQP, SLOT, DATE, TIME)",
#     "CREATE INDEX idx_prime_slot ON prime_data(SLOT)",
#     "CREATE INDEX idx_prime_model ON prime_data(MODEL)",
#     "CREATE INDEX idx_prime_tier_model ON prime_data(TIER, MODEL)",
#     "CREATE INDEX idx_prime_scrapcode ON prime_data(SCRAPCODE)",
#     "CREATE INDEX idx_cum_model ON cum_data(MODEL)",
#     "CREATE INDEX idx_cum_tier_date_model ON cum_data(TIER, DATE, MODEL)",
#     "CREATE INDEX idx_cum_tier_model_date_eqp ON cum_data(TIER, MODEL, DATE, EQPID)",
# ]
#
# PERFORMANCE_INDEXES = [
#     "CREATE INDEX IF NOT EXISTS idx_prime_first_slot_daily ON prime_data(EQP, SLOT, DATE, TIER, MODEL, RESULT, QTY) WHERE TEST_COUNT = 1",
#     "CREATE INDEX IF NOT EXISTS idx_prime_first_slot ON prime_data(EQP, DATE, TIER, MODEL, SLOT, RESULT, QTY) WHERE TEST_COUNT = 1",
#     "CREATE INDEX IF NOT EXISTS idx_prime_daily_fail ON prime_data(EQP, DATE, TIER, MODEL, SCRAPCODE, QTY) WHERE RESULT = 'FAIL' AND COALESCE(SCRAPCODE, '') <> ''",
#     "CREATE INDEX IF NOT EXISTS idx_cum_date ON cum_data(DATE)",
#     "CREATE INDEX IF NOT EXISTS idx_cum_lot_date_tier ON cum_data(LOTID, DATE, TIER)",
#     "CREATE INDEX IF NOT EXISTS idx_cum_eqp_date ON cum_data(EQPID, DATE)",
#     "CREATE INDEX IF NOT EXISTS idx_cum_scrap_code ON cum_scrap_detail(scrap_code, cum_data_id)",
#     "CREATE INDEX IF NOT EXISTS idx_prime_date ON prime_data(DATE)",
#     "CREATE INDEX IF NOT EXISTS idx_prime_eqp_date ON prime_data(EQP, DATE)",
#     "CREATE INDEX IF NOT EXISTS idx_prime_slot_time ON prime_data(EQP, SLOT, DATE, TIME)",
#     "CREATE INDEX IF NOT EXISTS idx_prime_slot ON prime_data(SLOT)",
#     "CREATE INDEX IF NOT EXISTS idx_prime_model ON prime_data(MODEL)",
#     "CREATE INDEX IF NOT EXISTS idx_prime_tier_model ON prime_data(TIER, MODEL)",
#     "CREATE INDEX IF NOT EXISTS idx_prime_scrapcode ON prime_data(SCRAPCODE)",
#     "CREATE INDEX IF NOT EXISTS idx_cum_model ON cum_data(MODEL)",
#     "CREATE INDEX IF NOT EXISTS idx_cum_tier_date_model ON cum_data(TIER, DATE, MODEL)",
#     "CREATE INDEX IF NOT EXISTS idx_cum_tier_model_date_eqp ON cum_data(TIER, MODEL, DATE, EQPID)",
# ]
#
#
# def ensure_performance_indexes(conn):
#     """Bổ sung index đọc/lọc cho cả database mới và database schema 2 đang dùng."""
#     for statement in PERFORMANCE_INDEXES:
#         conn.execute(statement)
#
#
# def verify_database(conn):
#     """Kiểm tra đúng database LI và phiên bản schema tương thích."""
#     if conn.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID:
#         raise ValueError("Đây không phải database LI. Không dùng database Aging.")
#     row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
#     if row[0] != SCHEMA_VERSION:
#         raise ValueError("Version database không tương thích. Bản này cần database LI mới (schema 2); hãy sao lưu và di chuyển database cũ trước khi mở lại app.")
#
#
# def initialize_database(database_path):
#     """Tạo schema cho database mới hoặc kiểm tra database đã tồn tại."""
#     with connection(database_path) as conn:
#         tables = {row[0] for row in conn.execute(
#             "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
#         if tables:
#             verify_database(conn)
#             ensure_performance_indexes(conn)
#             ensure_file_management_schema(conn)
#             ensure_machine_slot_yield_schema(conn)
#             ensure_mail_schema(conn)
#             ensure_alarm_schema(conn)
#             if conn.execute("PRAGMA journal_mode").fetchone()[0].lower() != "delete":
#                 raise ValueError("Database LI phải dùng journal_mode=DELETE.")
#             return
#         if conn.execute("PRAGMA application_id").fetchone()[0] not in (0, APPLICATION_ID):
#             raise ValueError("Database thuộc ứng dụng khác.")
#         conn.execute("PRAGMA journal_mode = DELETE")
#         conn.execute("BEGIN IMMEDIATE")
#         try:
#             # Another process may have initialized while this process was waiting.
#             if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchone():
#                 verify_database(conn)
#             else:
#                 for statement in CREATE_FRESH_SCHEMA:
#                     conn.execute(statement)
#                 conn.execute(f"PRAGMA application_id = {APPLICATION_ID}")
#                 conn.execute(
#                     "INSERT INTO schema_version VALUES(2, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
#                     ("LI PRIME + CUM, scrap detail, TIER and global import lock",))
#             ensure_file_management_schema(conn)
#             ensure_machine_slot_yield_schema(conn)
#             ensure_mail_schema(conn)
#             ensure_alarm_schema(conn)
#             conn.commit()
#         except BaseException:
#             conn.rollback()
#             raise
#
#
# CREATE_AUTO_IMPORT_SCHEDULER_TABLE = """
# CREATE TABLE IF NOT EXISTS auto_import_scheduler (
#     id INTEGER PRIMARY KEY
#         CHECK (id = 1),
#
#     enable_auto_import INTEGER NOT NULL DEFAULT 0
#         CHECK (enable_auto_import IN (0, 1)),
#
#     import_time TEXT NOT NULL DEFAULT '03:00'
#         CHECK (
#             length(import_time) = 5
#             AND import_time GLOB '[0-2][0-9]:[0-5][0-9]'
#             AND CAST(substr(import_time, 1, 2) AS INTEGER)
#                 BETWEEN 0 AND 23
#         ),
#
#     log_folder TEXT NOT NULL DEFAULT '',
#
#     last_import_date TEXT
#         CHECK (
#             last_import_date IS NULL
#             OR (
#                 length(last_import_date) = 8
#                 AND last_import_date NOT GLOB '*[^0-9]*'
#             )
#         )
# )
# """
#
#
# def ensure_file_management_schema(conn):
#     """Bổ sung cấu hình File Management, giữ nguyên dữ liệu và schema LI 2."""
#     conn.execute(CREATE_AUTO_IMPORT_SCHEDULER_TABLE)
#     conn.execute("INSERT OR IGNORE INTO auto_import_scheduler(id) VALUES(1)")
#
#
# CREATE_MACHINE_SLOT_YIELD_CONFIG_TABLE = """
# CREATE TABLE IF NOT EXISTS machine_slot_yield_config (
#     id INTEGER PRIMARY KEY CHECK (id = 1),
#     log_folder TEXT NOT NULL DEFAULT '',
#     target_15 REAL NOT NULL DEFAULT 70.0
#         CHECK (typeof(target_15) IN ('integer', 'real')
#                AND target_15 BETWEEN 0 AND 100),
#     target_30 REAL NOT NULL DEFAULT 75.0
#         CHECK (typeof(target_30) IN ('integer', 'real')
#                AND target_30 BETWEEN 0 AND 100),
#     continuous_fail_count INTEGER NOT NULL DEFAULT 3
#         CHECK (typeof(continuous_fail_count) = 'integer'
#                AND continuous_fail_count >= 1),
#     updated_at TEXT
# )
# """
#
#
# def ensure_machine_slot_yield_schema(conn):
#     """Bổ sung cấu hình ngưỡng Machine Slot Yield cho DB mới/cũ."""
#     conn.execute(CREATE_MACHINE_SLOT_YIELD_CONFIG_TABLE)
#     conn.execute(
#         "INSERT OR IGNORE INTO machine_slot_yield_config(id) VALUES(1)"
#     )
from database.connection import connection
from database.mail_schema import ensure_mail_schema
from database.alarm_schema import ensure_alarm_schema

SCHEMA_VERSION = 2
APPLICATION_ID = 1279864914  # Distinguish LI database from Aging and unrelated files.

# Used by both main database and local staging.
PRIME_FIELDS = """
    DATE TEXT NOT NULL CHECK(length(DATE)=8 AND DATE NOT GLOB '*[^0-9]*'),
    TIME TEXT NOT NULL CHECK(
        length(TIME)=8 AND TIME GLOB '[0-2][0-9]:[0-5][0-9]:[0-5][0-9]'
        AND CAST(substr(TIME,1,2) AS INTEGER) <= 23),
    EQP TEXT NOT NULL CHECK(length(trim(EQP))>0),
    PARTNO TEXT NOT NULL CHECK(length(trim(PARTNO))>=5),
    LOTNO TEXT NOT NULL CHECK(length(trim(LOTNO))>0),
    SLOT INTEGER NOT NULL CHECK(typeof(SLOT)='integer' AND SLOT BETWEEN 1 AND 48),
    RESULT TEXT NOT NULL CHECK(RESULT IN ('PASS','FAIL')),
    SCRAPCODE TEXT CHECK(SCRAPCODE IS NULL OR
        (length(trim(SCRAPCODE))>0 AND upper(SCRAPCODE) NOT IN ('0','NULL'))),
    TEST_COUNT INTEGER NOT NULL CHECK(typeof(TEST_COUNT)='integer' AND TEST_COUNT>=0),
    SERIAL TEXT NOT NULL CHECK(length(trim(SERIAL))>0 AND upper(SERIAL)<>'NULL'),
    QTY INTEGER NOT NULL DEFAULT 1 CHECK(typeof(QTY)='integer' AND QTY=1),
    MODEL TEXT NOT NULL CHECK(MODEL=substr(PARTNO,1,5))
"""

CREATE_CUM_DATA_TABLE = """
CREATE TABLE IF NOT EXISTS cum_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    DATE TEXT NOT NULL
        CHECK (
            length(DATE) = 8
            AND DATE NOT GLOB '*[^0-9]*'
        ),

    TIME TEXT NOT NULL
        CHECK (
            length(TIME) = 8
            AND TIME GLOB '[0-2][0-9]:[0-5][0-9]:[0-5][0-9]'
            AND CAST(substr(TIME, 1, 2) AS INTEGER) BETWEEN 0 AND 23
        ),

    LOTID TEXT,

    PRODUCT TEXT NOT NULL,

    EQPID TEXT NOT NULL,

    INQTY INTEGER NOT NULL
        CHECK (
            typeof(INQTY) = 'integer'
            AND INQTY >= 0
        ),

    OUTQTY INTEGER NOT NULL
        CHECK (
            typeof(OUTQTY) = 'integer'
            AND OUTQTY >= 0
        ),

    FAILQTY INTEGER NOT NULL
        CHECK (
            typeof(FAILQTY) = 'integer'
            AND FAILQTY >= 0
        ),

    YIELD REAL NOT NULL
        CHECK (
            typeof(YIELD) IN ('integer', 'real')
        ),

    SCRAP TEXT NOT NULL DEFAULT '',

    MODEL TEXT NOT NULL
        CHECK (length(MODEL) = 5),

    TIER TEXT NOT NULL
)
"""

CREATE_CUM_SCRAP_DETAIL_TABLE = """
CREATE TABLE IF NOT EXISTS cum_scrap_detail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    cum_data_id INTEGER NOT NULL,

    scrap_code TEXT NOT NULL
        CHECK (
            length(scrap_code) = 4
            AND scrap_code NOT GLOB '*[^0-9]*'
        ),

    qty INTEGER NOT NULL
        CHECK (
            typeof(qty) = 'integer'
            AND qty BETWEEN 1 AND 99
        ),

    FOREIGN KEY (cum_data_id)
        REFERENCES cum_data(id)
        ON DELETE CASCADE,

    UNIQUE (
        cum_data_id,
        scrap_code
    )
)
"""

CREATE_FRESH_SCHEMA = [
    "CREATE TABLE schema_version(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL, description TEXT NOT NULL)",
    f"CREATE TABLE prime_data(id INTEGER PRIMARY KEY AUTOINCREMENT, {PRIME_FIELDS})",
    """CREATE TABLE import_lock(
        lock_name TEXT PRIMARY KEY CHECK(lock_name='GLOBAL_IMPORT_LOCK'),
        batch_id TEXT NOT NULL, import_type TEXT NOT NULL,
        machine_name TEXT NOT NULL, windows_user TEXT NOT NULL,
        process_id INTEGER NOT NULL, source TEXT NOT NULL,
        acquired_at REAL NOT NULL, heartbeat_at REAL NOT NULL, expires_at REAL NOT NULL)""",
    """CREATE TABLE data_import_status(
        data_type TEXT NOT NULL, DATE TEXT NOT NULL,
        imported_at TEXT NOT NULL, batch_id TEXT NOT NULL, row_count INTEGER NOT NULL,
        PRIMARY KEY(data_type, DATE))""",
    "ALTER TABLE prime_data ADD COLUMN TIER TEXT",
    CREATE_CUM_DATA_TABLE,
    CREATE_CUM_SCRAP_DETAIL_TABLE,
    "CREATE INDEX idx_cum_date ON cum_data(DATE)",
    "CREATE INDEX idx_cum_lot_date_tier ON cum_data(LOTID, DATE, TIER)",
    "CREATE INDEX idx_cum_eqp_date ON cum_data(EQPID, DATE)",
    "CREATE INDEX idx_cum_scrap_code ON cum_scrap_detail(scrap_code, cum_data_id)",
    "CREATE INDEX IF NOT EXISTS idx_prime_daily_fail ON prime_data(EQP, DATE, TIER, MODEL, SCRAPCODE, QTY) WHERE RESULT = 'FAIL' AND COALESCE(SCRAPCODE, '') <> ''",
    "CREATE INDEX IF NOT EXISTS idx_prime_first_slot_daily ON prime_data(EQP, SLOT, DATE, TIER, MODEL, RESULT, QTY) WHERE TEST_COUNT = 0",
    "CREATE INDEX IF NOT EXISTS idx_prime_first_slot ON prime_data(EQP, DATE, TIER, MODEL, SLOT, RESULT, QTY) WHERE TEST_COUNT = 0",
    "CREATE INDEX idx_prime_date ON prime_data(DATE)",
    "CREATE INDEX idx_prime_eqp_date ON prime_data(EQP, DATE)",
    "CREATE INDEX idx_prime_slot_time ON prime_data(EQP, SLOT, DATE, TIME)",
    "CREATE INDEX idx_prime_slot ON prime_data(SLOT)",
    "CREATE INDEX idx_prime_model ON prime_data(MODEL)",
    "CREATE INDEX idx_prime_tier_model ON prime_data(TIER, MODEL)",
    "CREATE INDEX idx_prime_scrapcode ON prime_data(SCRAPCODE)",
    "CREATE INDEX idx_cum_model ON cum_data(MODEL)",
    "CREATE INDEX idx_cum_tier_date_model ON cum_data(TIER, DATE, MODEL)",
    "CREATE INDEX idx_cum_tier_model_date_eqp ON cum_data(TIER, MODEL, DATE, EQPID)",
]

PERFORMANCE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_prime_first_slot_daily ON prime_data(EQP, SLOT, DATE, TIER, MODEL, RESULT, QTY) WHERE TEST_COUNT = 0",
    "CREATE INDEX IF NOT EXISTS idx_prime_first_slot ON prime_data(EQP, DATE, TIER, MODEL, SLOT, RESULT, QTY) WHERE TEST_COUNT = 0",
    "CREATE INDEX IF NOT EXISTS idx_prime_daily_fail ON prime_data(EQP, DATE, TIER, MODEL, SCRAPCODE, QTY) WHERE RESULT = 'FAIL' AND COALESCE(SCRAPCODE, '') <> ''",
    "CREATE INDEX IF NOT EXISTS idx_cum_date ON cum_data(DATE)",
    "CREATE INDEX IF NOT EXISTS idx_cum_lot_date_tier ON cum_data(LOTID, DATE, TIER)",
    "CREATE INDEX IF NOT EXISTS idx_cum_eqp_date ON cum_data(EQPID, DATE)",
    "CREATE INDEX IF NOT EXISTS idx_cum_scrap_code ON cum_scrap_detail(scrap_code, cum_data_id)",
    "CREATE INDEX IF NOT EXISTS idx_prime_date ON prime_data(DATE)",
    "CREATE INDEX IF NOT EXISTS idx_prime_eqp_date ON prime_data(EQP, DATE)",
    "CREATE INDEX IF NOT EXISTS idx_prime_slot_time ON prime_data(EQP, SLOT, DATE, TIME)",
    "CREATE INDEX IF NOT EXISTS idx_prime_slot ON prime_data(SLOT)",
    "CREATE INDEX IF NOT EXISTS idx_prime_model ON prime_data(MODEL)",
    "CREATE INDEX IF NOT EXISTS idx_prime_tier_model ON prime_data(TIER, MODEL)",
    "CREATE INDEX IF NOT EXISTS idx_prime_scrapcode ON prime_data(SCRAPCODE)",
    "CREATE INDEX IF NOT EXISTS idx_cum_model ON cum_data(MODEL)",
    "CREATE INDEX IF NOT EXISTS idx_cum_tier_date_model ON cum_data(TIER, DATE, MODEL)",
    "CREATE INDEX IF NOT EXISTS idx_cum_tier_model_date_eqp ON cum_data(TIER, MODEL, DATE, EQPID)",
]


# Versioned names keep these covering indexes distinct from the general-purpose
# indexes used by other tabs. The first two existing indexes also need repair
# on databases created when the first test was represented by TEST_COUNT = 1.
DAILY_COVERING_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_prime_daily_cover_v1 ON prime_data(EQP, TEST_COUNT, DATE, TIER, MODEL, RESULT, QTY)",
    "CREATE INDEX IF NOT EXISTS idx_prime_first_daily_fail_v1 ON prime_data(EQP, TEST_COUNT, DATE, TIER, MODEL, SCRAPCODE, QTY, RESULT) WHERE TEST_COUNT = 0 AND RESULT = 'FAIL' AND COALESCE(SCRAPCODE, '') <> ''",
    "CREATE INDEX IF NOT EXISTS idx_cum_daily_cover_v1 ON cum_data(EQPID, DATE, TIER, MODEL, INQTY, OUTQTY)",
    "CREATE INDEX IF NOT EXISTS idx_cum_scrap_daily_cover_v1 ON cum_scrap_detail(cum_data_id, scrap_code, qty)",
]
PERFORMANCE_INDEXES.extend(DAILY_COVERING_INDEXES)
DAILY_INDEX_DEFINITIONS = {
    statement.split()[5]: statement
    for statement in PERFORMANCE_INDEXES[:2] + DAILY_COVERING_INDEXES
}


def _canonical_index_sql(sql):
    """Compare our known index definitions, ignoring SQL formatting only."""
    import re
    text = re.sub(r"\bIF\s+NOT\s+EXISTS\b", "", sql or "", flags=re.I)
    # Preserve case/spacing inside SQL literals (e.g. 'FAIL').
    parts = re.split(r"('(?:[^']|'')*')", text)
    return ''.join(part if i % 2 else re.sub(r"\s+", "", part).lower()
                   for i, part in enumerate(parts)).rstrip(';')


def _daily_indexes_current(conn):
    existing = dict(conn.execute("SELECT name, sql FROM sqlite_master WHERE type='index'"))
    return all(_canonical_index_sql(existing.get(name)) == _canonical_index_sql(sql)
               for name, sql in DAILY_INDEX_DEFINITIONS.items())


def ensure_performance_indexes(conn):
    """Create missing indexes and atomically repair obsolete daily indexes."""
    own_transaction = not conn.in_transaction
    if own_transaction:
        # Acquire the write lock before inspecting definitions; concurrent app
        # startups then recheck metadata after the first migration has finished.
        conn.execute("BEGIN IMMEDIATE")
    else:
        conn.execute("SAVEPOINT daily_index_upgrade")
    try:
        existing = dict(conn.execute("SELECT name, sql FROM sqlite_master WHERE type='index'"))
        changed = []
        for name, statement in DAILY_INDEX_DEFINITIONS.items():
            if _canonical_index_sql(existing.get(name)) != _canonical_index_sql(statement):
                if name in existing:
                    conn.execute(f'DROP INDEX "{name}"')
                changed.append(name)
        for statement in PERFORMANCE_INDEXES:
            conn.execute(statement)
        # Statistics are collected only for newly built/repaired daily indexes,
        # never at every Search or normal startup.
        for name in changed:
            conn.execute(f'ANALYZE "{name}"')
        if own_transaction:
            conn.commit()
        else:
            conn.execute("RELEASE SAVEPOINT daily_index_upgrade")
    except BaseException:
        if own_transaction:
            conn.rollback()
        else:
            conn.execute("ROLLBACK TO SAVEPOINT daily_index_upgrade")
            conn.execute("RELEASE SAVEPOINT daily_index_upgrade")
        raise


def verify_database(conn):
    """Kiểm tra đúng database LI và phiên bản schema tương thích."""
    if conn.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID:
        raise ValueError("Đây không phải database LI. Không dùng database Aging.")
    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    if row[0] != SCHEMA_VERSION:
        raise ValueError("Version database không tương thích. Bản này cần database LI mới (schema 2); hãy sao lưu và di chuyển database cũ trước khi mở lại app.")


def initialize_database(database_path):
    """Tạo schema cho database mới hoặc kiểm tra database đã tồn tại."""
    with connection(database_path, timeout=60) as conn:
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        if tables:
            verify_database(conn)
            if _startup_schema_complete(conn):
                if conn.execute("PRAGMA journal_mode").fetchone()[0].lower() != "delete":
                    raise ValueError("Database LI phải dùng journal_mode=DELETE.")
                return
            ensure_performance_indexes(conn)
            ensure_file_management_schema(conn)
            ensure_machine_slot_yield_schema(conn)
            ensure_mail_schema(conn)
            ensure_alarm_schema(conn)
            if conn.execute("PRAGMA journal_mode").fetchone()[0].lower() != "delete":
                raise ValueError("Database LI phải dùng journal_mode=DELETE.")
            return
        if conn.execute("PRAGMA application_id").fetchone()[0] not in (0, APPLICATION_ID):
            raise ValueError("Database thuộc ứng dụng khác.")
        conn.execute("PRAGMA journal_mode = DELETE")
        conn.execute("BEGIN IMMEDIATE")
        try:
            # Another process may have initialized while this process was waiting.
            if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchone():
                verify_database(conn)
            else:
                for statement in CREATE_FRESH_SCHEMA:
                    conn.execute(statement)
                conn.execute(f"PRAGMA application_id = {APPLICATION_ID}")
                conn.execute(
                    "INSERT INTO schema_version VALUES(2, strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?)",
                    ("LI PRIME + CUM, scrap detail, TIER and global import lock",))
            ensure_performance_indexes(conn)
            ensure_file_management_schema(conn)
            ensure_machine_slot_yield_schema(conn)
            ensure_mail_schema(conn)
            ensure_alarm_schema(conn)
            conn.commit()
        except BaseException:
            conn.rollback()
            raise


CREATE_AUTO_IMPORT_SCHEDULER_TABLE = """
CREATE TABLE IF NOT EXISTS auto_import_scheduler (
    id INTEGER PRIMARY KEY
        CHECK (id = 1),

    enable_auto_import INTEGER NOT NULL DEFAULT 0
        CHECK (enable_auto_import IN (0, 1)),

    import_time TEXT NOT NULL DEFAULT '03:00'
        CHECK (
            length(import_time) = 5
            AND import_time GLOB '[0-2][0-9]:[0-5][0-9]'
            AND CAST(substr(import_time, 1, 2) AS INTEGER)
                BETWEEN 0 AND 23
        ),

    log_folder TEXT NOT NULL DEFAULT '',

    last_import_date TEXT
        CHECK (
            last_import_date IS NULL
            OR (
                length(last_import_date) = 8
                AND last_import_date NOT GLOB '*[^0-9]*'
            )
        )
)
"""


def ensure_file_management_schema(conn):
    """Bổ sung cấu hình File Management, giữ nguyên dữ liệu và schema LI 2."""
    conn.execute(CREATE_AUTO_IMPORT_SCHEDULER_TABLE)
    conn.execute("INSERT OR IGNORE INTO auto_import_scheduler(id) VALUES(1)")


CREATE_MACHINE_SLOT_YIELD_CONFIG_TABLE = """
CREATE TABLE IF NOT EXISTS machine_slot_yield_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    log_folder TEXT NOT NULL DEFAULT '',
    target_15 REAL NOT NULL DEFAULT 70.0
        CHECK (typeof(target_15) IN ('integer', 'real')
               AND target_15 BETWEEN 0 AND 100),
    target_30 REAL NOT NULL DEFAULT 75.0
        CHECK (typeof(target_30) IN ('integer', 'real')
               AND target_30 BETWEEN 0 AND 100),
    continuous_fail_count INTEGER NOT NULL DEFAULT 3
        CHECK (typeof(continuous_fail_count) = 'integer'
               AND continuous_fail_count >= 1),
    updated_at TEXT
)
"""


def ensure_machine_slot_yield_schema(conn):
    """Bổ sung cấu hình ngưỡng Machine Slot Yield cho DB mới/cũ."""
    conn.execute(CREATE_MACHINE_SLOT_YIELD_CONFIG_TABLE)
    columns = {row[1] for row in conn.execute('PRAGMA table_info(machine_slot_yield_config)')}
    if 'different_scrap_fail_count' not in columns:
        conn.execute("""ALTER TABLE machine_slot_yield_config ADD COLUMN
            different_scrap_fail_count INTEGER NOT NULL DEFAULT 3
            CHECK(typeof(different_scrap_fail_count)='integer' AND different_scrap_fail_count>=2)""")
    conn.execute(
        "INSERT OR IGNORE INTO machine_slot_yield_config(id) VALUES(1)"
    )


def _startup_schema_complete(conn):
    """Read metadata only on normal startup; migrate only missing objects."""
    import re
    from database.mail_schema import MAIL_SCHEMA_STATEMENTS
    statements = (CREATE_FRESH_SCHEMA + PERFORMANCE_INDEXES +
                  list(MAIL_SCHEMA_STATEMENTS) +
                  [CREATE_AUTO_IMPORT_SCHEDULER_TABLE,
                   CREATE_MACHINE_SLOT_YIELD_CONFIG_TABLE])
    names = set()
    for statement in statements:
        match = re.search(r"CREATE\s+(?:UNIQUE\s+)?(?:TABLE|INDEX)\s+(?:IF NOT EXISTS\s+)?(\w+)",
                          statement, re.IGNORECASE)
        if match:
            names.add(match.group(1))
    names.update(("slot_fail_alarm", "idx_alarm_history_list"))
    existing = {row[0] for row in conn.execute("SELECT name FROM sqlite_master")}
    if not names <= existing or not _daily_indexes_current(conn):
        return False
    for table, column in (("machine_slot_yield_config", "different_scrap_fail_count"),
                          ("slot_fail_alarm", "different_scrap_fail_count_used")):
        if column not in {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}:
            return False
    for table in ("mail_template", "auto_send_mail_scheduler", "auto_import_scheduler",
                  "machine_slot_yield_config"):
        if conn.execute(f"SELECT 1 FROM {table} WHERE id=1").fetchone() is None:
            return False
    return True
