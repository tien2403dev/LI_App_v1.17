from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


from workers.database_read_task import database_read_task
from database.read_wait import is_database_busy

class SlotSummaryWorker(QObject):
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)
    finished = pyqtSignal()
    database_waiting = pyqtSignal(bool)

    def __init__(self, database_path, key, cached_model=None):
        super().__init__()
        self.database_path = database_path
        self.key = key
        self.cached_model = cached_model

    @pyqtSlot()
    @database_read_task
    def run(self):
        try:
            from repositories.slot_summary_repository import SlotSummaryRepository
            result = SlotSummaryRepository(self.database_path).load(*self.key)
            # CUM chỉ phụ thuộc From/To/Tier; bỏ EQP, Model và SLOT khỏi cache.
            from dataclasses import replace
            from repositories.model_summary_repository import ModelSummaryRepository
            model = self.cached_model
            if model is None:
                model = ModelSummaryRepository(self.database_path).load(*self.key[:3])
            result = replace(result, cum_model=model)
            # Load heavy modules after SEARCH, outside the UI thread.
            from workers.chart_preload_worker import preload_charts
            preload_charts()
            self.succeeded.emit(result)
        except Exception as error:
            if is_database_busy(error):
                raise
            self.failed.emit(str(error) or 'Không thể tải Yield Slot.')
