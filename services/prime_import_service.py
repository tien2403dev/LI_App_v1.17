import logging
from pathlib import Path
from tempfile import TemporaryDirectory

from database.schema import initialize_database
from database.diagnostics import event
from domain.prime import check_cancel
from repositories.import_lock_repository import ImportLockHeartbeat, ImportLockRepository
from repositories.prime_repository import PrimeRepository
from services.prime_log_reader import LiPrimeLogReader

logger = logging.getLogger(__name__)


class PrimeImportService:
    def __init__(self, database_path, encoding="utf-8-sig"):
        self.database_path = Path(database_path)
        self.reader = LiPrimeLogReader(encoding)

    def import_folder(self, root_folder, business_dates, progress=None, cancel=None):
        # A plain string represents one date, not an iterable of its characters.
        dates = (business_dates,) if isinstance(business_dates, str) else tuple(sorted(set(business_dates)))
        if not dates:
            raise ValueError("Cần chọn ít nhất một ngày")
        def notify(message):
            event("IMPORT_PROGRESS", batch=batch_id, import_type="PRIME", message=message)
            logger.info(message)
            if progress:
                try:
                    progress(message)
                except Exception:
                    logger.exception("Lỗi callback tiến độ")
        check_cancel(cancel)
        initialize_database(self.database_path)
        locks = ImportLockRepository(self.database_path)
        batch_id = locks.acquire(f"{root_folder} | {','.join(dates)}")
        heartbeat = ImportLockHeartbeat(locks, batch_id)
        try:
            heartbeat.start()
            # Windows TemporaryDirectory is local; main database remains on the configured share.
            with TemporaryDirectory(prefix="li_prime_", ignore_cleanup_errors=True) as temporary:
                stage = Path(temporary) / "staging.db"
                notify("Đang đọc và kiểm tra log")
                file_count = self.reader.stage_folder(root_folder, dates, stage, notify, cancel)
                if not heartbeat.stop():
                    raise TimeoutError("Heartbeat chưa dừng; hủy import trước khi thay dữ liệu. Xem log chẩn đoán.")
                check_cancel(cancel)
                notify("Đang thay thế các ngày có trong dữ liệu mới")
                result = PrimeRepository(self.database_path).replace_from_staging(
                    stage, batch_id, file_count, notify, cancel)
                notify(f"Import thành công: {result.inserted} dòng; thay {result.deleted} dòng cũ")
                return result
        finally:
            if heartbeat.thread.ident is not None:
                heartbeat.stop()
            try:
                locks.release(batch_id)
            except Exception:
                # Cleanup must not mask a committed result or the original import error.
                logger.exception("Chưa giải phóng được khóa import; khóa có thời hạn")

