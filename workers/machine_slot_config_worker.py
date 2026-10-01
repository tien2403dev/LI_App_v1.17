"""Deferred config read when opening Machine Slot Yield during an import."""
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from workers.database_read_task import database_read_task
from repositories.machine_slot_yield_repository import MachineSlotYieldRepository


class MachineSlotConfigWorker(QObject):
    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)
    finished = pyqtSignal()
    database_waiting = pyqtSignal(bool)

    def __init__(self, database_path):
        super().__init__()
        self.database_path = database_path

    @pyqtSlot()
    @database_read_task
    def run(self):
        self.succeeded.emit(MachineSlotYieldRepository(self.database_path).get_config())
