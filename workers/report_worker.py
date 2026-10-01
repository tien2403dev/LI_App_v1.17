from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


from workers.database_read_task import database_read_task
from database.read_wait import is_database_busy

class ReportWorker(QObject):
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)
    finished = pyqtSignal()
    database_waiting = pyqtSignal(bool)

    def __init__(self, database_path: Path, action: str, **arguments):
        super().__init__()
        self.database_path = Path(database_path)
        self.action = action
        self.arguments = arguments

    @pyqtSlot()
    @database_read_task
    def run(self) -> None:
        try:
            from repositories.report_repository import ReportRepository

            repository = ReportRepository(self.database_path)
            if self.action == "options":
                result = repository.get_filter_options()
            elif self.action == "summary":
                result = repository.get_summary(**self.arguments)
            elif self.action == "details":
                result = repository.get_details(**self.arguments)
            else:
                raise ValueError("Tác vụ Report không hợp lệ.")
            self.succeeded.emit(result)
        except Exception as error:
            if is_database_busy(error):
                raise
            self.failed.emit(str(error).strip() or "Không thể tải dữ liệu Report.")
