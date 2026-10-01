from threading import Event
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class CumImportWorker(QObject):
    """Move this QObject to a QThread; never call run() on the UI thread."""
    progress = pyqtSignal(str)
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, database_path, excel_path):
        """Khởi tạo trạng thái và các thành phần cần cho đối tượng."""
        super().__init__()
        self.database_path = database_path
        self.excel_path = excel_path
        self.cancel_event = Event()

    def request_cancel(self):
        # Call directly from UI: threading.Event is thread-safe.
        # A queued Qt slot would not run while run() is busy.
        """Đặt cờ hủy thread-safe để service dừng tại điểm kiểm tra tiếp theo."""
        self.cancel_event.set()

    @pyqtSlot()
    def run(self):
        """Nạp service CUM trong worker, chạy import và phát kết quả hoặc lỗi."""
        try:
            from services.cum_import_service import CumImportService
            result = CumImportService(self.database_path).import_file(
                self.excel_path, self.progress.emit, self.cancel_event)
            self.succeeded.emit(result)
        except Exception as error:
            import logging
            logging.getLogger(__name__).exception("Import CUM thất bại")
            self.failed.emit(f"{self.excel_path}\n{error}" or "Import CUM thất bại")
        finally:
            self.finished.emit()

