from threading import Event
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class PrimeImportWorker(QObject):
    """Move this QObject to a QThread; never call run() on the UI thread."""
    progress = pyqtSignal(str)
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, database_path, root_folder, business_dates, encoding="utf-8-sig"):
        super().__init__()
        self.database_path = database_path
        self.root_folder = root_folder
        self.business_dates = business_dates
        self.encoding = encoding
        self.cancel_event = Event()

    def request_cancel(self):
        # Call directly from UI: threading.Event is thread-safe.
        # A queued Qt slot would not run while run() is busy.
        self.cancel_event.set()

    @pyqtSlot()
    def run(self):
        try:
            from services.prime_import_service import PrimeImportService
            result = PrimeImportService(self.database_path, self.encoding).import_folder(
                self.root_folder, self.business_dates, self.progress.emit, self.cancel_event)
            self.succeeded.emit(result)
        except Exception as error:
            import logging
            logging.getLogger(__name__).exception("Import PRIME thất bại")
            self.failed.emit(str(error) or "Import PRIME thất bại")
        finally:
            self.finished.emit()

