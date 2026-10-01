import getpass
import logging
import os
import socket
import sqlite3
import time
import uuid
from threading import Event, Thread

from database.connection import connection
from database.diagnostics import event
from database.schema import verify_database
from domain.prime import ImportBusyError, LockLostError

LOCK_NAME = "GLOBAL_IMPORT_LOCK"
LEASE_SECONDS = 900
logger = logging.getLogger(__name__)


class ImportLockRepository:
    def __init__(self, database_path):
        """Khởi tạo trạng thái và các thành phần cần cho đối tượng."""
        self.database_path = database_path

    def acquire(self, source, import_type="PRIME"):
        """Chiếm khóa import chung, từ chối khi phiên khác còn giữ khóa."""
        batch_id = uuid.uuid4().hex
        event("IMPORT_LOCK_ACQUIRE", batch=batch_id, source=str(source), import_type=import_type)
        try:
            with connection(self.database_path, timeout=60) as conn:
                verify_database(conn)
                conn.execute("BEGIN IMMEDIATE")
                now = time.time()
                row = conn.execute("SELECT * FROM import_lock WHERE lock_name=?", (LOCK_NAME,)).fetchone()
                if row and row["expires_at"] > now:
                    event('IMPORT_LOCK_BUSY_OWNER', requested_batch=batch_id,
                          owner_batch=row['batch_id'], owner_pid=row['process_id'],
                          owner_host=row['machine_name'], expires_at=row['expires_at'])
                    raise ImportBusyError(
                        f"Đang có người import: {row['windows_user']} trên máy {row['machine_name']}. "
                        "Vui lòng đợi hoàn tất rồi bấm Import lại.")
                conn.execute("DELETE FROM import_lock WHERE lock_name=?", (LOCK_NAME,))
                conn.execute(
                    "INSERT INTO import_lock VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (LOCK_NAME, batch_id, import_type, socket.gethostname(), getpass.getuser(),
                     os.getpid(), str(source), now, now, now + LEASE_SECONDS))
                conn.commit()
            event("IMPORT_LOCK_ACQUIRED", batch=batch_id)
            return batch_id
        except sqlite3.OperationalError as error:
            if "locked" in str(error).lower() or "busy" in str(error).lower():
                raise ImportBusyError("Database đang bận đọc/ghi sau khi chờ tối đa 60 giây cho thao tác khóa. Vui lòng thử lại; xem log chẩn đoán trên máy chạy app.") from error
            raise

    @staticmethod
    def assert_owner(conn, batch_id):
        """Kiểm tra phiên hiện tại còn sở hữu khóa và khóa chưa hết hạn."""
        row = conn.execute(
            "SELECT batch_id, expires_at FROM import_lock WHERE lock_name=?", (LOCK_NAME,)
        ).fetchone()
        if not row or row["batch_id"] != batch_id or row["expires_at"] <= time.time():
            raise LockLostError("Phiên import đã mất/hết hạn khóa; dữ liệu chưa được thay thế. Hãy import lại.")

    @staticmethod
    def renew_in_transaction(conn, batch_id):
        """Gia hạn khóa của phiên đang ghi ngay trong transaction hiện tại."""
        now = time.time()
        cursor = conn.execute(
            "UPDATE import_lock SET heartbeat_at=?, expires_at=? WHERE lock_name=? AND batch_id=?",
            (now, now + LEASE_SECONDS, LOCK_NAME, batch_id))
        if cursor.rowcount != 1:
            raise LockLostError("Phiên import không còn sở hữu khóa.")

    def refresh(self, batch_id):
        """Mở kết nối riêng để kiểm tra và gia hạn khóa import."""
        with connection(self.database_path, timeout=60) as conn:
            conn.execute("BEGIN IMMEDIATE")
            self.assert_owner(conn, batch_id)
            self.renew_in_transaction(conn, batch_id)
            conn.commit()

    def release(self, batch_id):
        """Giải phóng đúng khóa do phiên hiện tại sở hữu."""
        event("IMPORT_LOCK_RELEASE_BEGIN", batch=batch_id)
        with connection(self.database_path, timeout=60) as conn:
            conn.execute("DELETE FROM import_lock WHERE lock_name=? AND batch_id=?", (LOCK_NAME, batch_id))

        event("IMPORT_LOCK_RELEASED", batch=batch_id)


class ImportLockHeartbeat:
    def __init__(self, repository, batch_id):
        """Khởi tạo trạng thái và các thành phần cần cho đối tượng."""
        self.repository = repository
        self.batch_id = batch_id
        self.stopped = Event()
        self.thread = Thread(target=self._run, name="ImportLockHeartbeat", daemon=True)

    def start(self):
        """Khởi động luồng gia hạn khóa nền."""
        self.thread.start()

    def stop(self):
        """Yêu cầu dừng và đợi luồng gia hạn khóa kết thúc."""
        self.stopped.set()
        self.thread.join(timeout=5)
        stopped = not self.thread.is_alive()
        event("HEARTBEAT_STOP", batch=self.batch_id, stopped=stopped)
        return stopped

    def _run(self):
        """Định kỳ gia hạn khóa và ghi log nếu cập nhật thất bại."""
        while not self.stopped.wait(60):
            try:
                self.repository.refresh(self.batch_id)
            except LockLostError:
                event("HEARTBEAT_LOCK_LOST", batch=self.batch_id)
                return
            except Exception:
                event("HEARTBEAT_ERROR", batch=self.batch_id)
                # Final ownership check is mandatory even if a heartbeat failed.
                logger.exception("Không cập nhật được heartbeat của phiên %s", self.batch_id)
