"""Background jobs for SLOT report; each job owns its database connection."""
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


from workers.database_read_task import database_read_task
from database.read_wait import is_database_busy

class SlotReportWorker(QObject):
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)
    finished = pyqtSignal()
    database_waiting = pyqtSignal(bool)

    def __init__(self, database_path, action, arguments):
        """Capture immutable request data before entering the worker thread."""
        super().__init__()
        self.database_path = database_path
        self.action = action
        self.arguments = arguments

    @pyqtSlot()
    @database_read_task
    def run(self):
        """Run options/query/refresh/export without blocking the GUI."""
        try:
            from services.slot_report_service import (
                SlotRepository, load_groups, refresh_groups, export_excel,
            )
            if self.action == 'options':
                result = SlotRepository(self.database_path).get_eqps()
            elif self.action == 'preview':
                result = load_groups(self.database_path, **self.arguments)
            elif self.action == 'refresh':
                result = refresh_groups(self.database_path, self.arguments['groups'])
            elif self.action == 'export':
                export_excel(**self.arguments)
                result = self.arguments['path']
            else:
                raise ValueError('Tác vụ báo cáo không hợp lệ.')
            self.succeeded.emit(result)
        except Exception as error:
            if is_database_busy(error):
                raise
            self.failed.emit(str(error) or 'Không thể xử lý báo cáo.')
