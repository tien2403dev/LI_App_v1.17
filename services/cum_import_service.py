import logging
from pathlib import Path

from database.schema import initialize_database
from database.diagnostics import event
from domain.prime import check_cancel
from repositories.cum_repository import CumRepository
from repositories.import_lock_repository import ImportLockHeartbeat, ImportLockRepository
from services.cum_excel_reader import CumExcelReader

logger = logging.getLogger(__name__)


class CumImportService:
    def __init__(self, database_path):
        """Lưu cấu hình database cho tác vụ nhập CUM."""
        self.database_path = Path(database_path)

    def import_file(self, excel_path, progress=None, cancel=None):
        """Giữ khóa chung, validate Excel vào staging rồi thay dữ liệu và dọn tài nguyên."""
        excel_path = Path(excel_path)
        def notify(message):
            """Ghi log và thông báo tiến độ mà không làm gián đoạn transaction."""
            event("IMPORT_PROGRESS", batch=batch_id, import_type="CUM", message=message)
            logger.info(message)
            if progress:
                try:
                    progress(message)
                except Exception:
                    logger.exception("Lỗi callback tiến độ")
        check_cancel(cancel)
        initialize_database(self.database_path)
        locks = ImportLockRepository(self.database_path)
        batch_id = locks.acquire(str(excel_path), import_type="CUM")
        heartbeat = ImportLockHeartbeat(locks, batch_id)
        reader = CumExcelReader(notify, cancel)
        staged = None
        try:
            heartbeat.start()
            notify("Đang đọc và kiểm tra Excel CUM")
            staged = reader.stage_file(excel_path)
            if not heartbeat.stop():
                raise TimeoutError("Heartbeat chưa dừng; hủy import trước khi thay dữ liệu. Xem log chẩn đoán.")
            check_cancel(cancel)
            return CumRepository(self.database_path).replace_from_staging(
                staged.staging_database_path, batch_id, excel_path.name, notify, cancel)
        finally:
            if staged is not None:
                reader.delete_staging_database(staged.staging_database_path)
            if heartbeat.thread.ident is not None:
                heartbeat.stop()
            try:
                locks.release(batch_id)
            except Exception:
                logger.exception("Chưa giải phóng được khóa import; khóa có thời hạn")
