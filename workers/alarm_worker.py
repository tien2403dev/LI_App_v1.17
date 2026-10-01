"""Đọc/lưu Alarm trong QThread do PrimeController quản lý."""
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from repositories.alarm_repository import AlarmRepository


from workers.database_read_task import database_read_task
from database.read_wait import is_database_busy

class AlarmWorker(QObject):
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)
    finished = pyqtSignal()
    database_waiting = pyqtSignal(bool)

    def __init__(self, database_path, date_range=None, edit=None, history=None):
        """Chọn đọc theo ngày hoặc lưu ô; không chia sẻ SQLite connection giữa thread."""
        super().__init__()
        self.database_path = database_path
        self.date_range = date_range
        self.edit = edit
        self.history = history

    @pyqtSlot()
    @database_read_task
    def run(self):
        """Phát kết quả/lỗi, luôn kết thúc để controller dọn thread an toàn."""
        try:
            repository = AlarmRepository(self.database_path)
            if self.history is not None:
                from repositories.alarm_history_repository import AlarmHistoryRepository
                result = AlarmHistoryRepository(self.database_path).load(self.history)
                result['preferred_rule'] = self.history.get('preferred_rule')
            elif self.edit is not None:
                result = repository.update_tracking(*self.edit)
            else:
                result = repository.load(*self.date_range, include_evidence=False)
            self.succeeded.emit(result)
        except Exception as error:
            if is_database_busy(error):
                raise
            self.failed.emit(str(error) or 'Không thể xử lý Alarm.')
