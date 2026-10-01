from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


from workers.database_read_task import database_read_task
from database.read_wait import is_database_busy

class DatabaseInitWorker(QObject):
    succeeded = pyqtSignal()
    failed = pyqtSignal(str)
    finished = pyqtSignal()
    database_waiting = pyqtSignal(bool)

    def __init__(self, database_path):
        super().__init__()
        self.database_path = Path(database_path)

    @pyqtSlot()
    @database_read_task
    def run(self):
        try:
            from database.schema import initialize_database
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            initialize_database(self.database_path)
            self.succeeded.emit()
        except Exception as error:
            if is_database_busy(error):
                raise
            self.failed.emit(str(error) or "Không thể khởi tạo database.")
