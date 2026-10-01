"""Warm chart modules after the window is visible, like Aging."""
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


def preload_charts():
    import importlib
    for name in ("cum_eqp_chart", "cum_daily_chart", "cum_model_chart",
                 "slot_daily_chart", "slot_fail_chart"):
        importlib.import_module("ui.charts." + name)


class ChartPreloadWorker(QObject):
    finished = pyqtSignal()

    @pyqtSlot()
    def run(self):
        try:
            preload_charts()
        except Exception:
            # A real SEARCH retries and surfaces the error; preload is optional.
            import logging
            logging.getLogger(__name__).exception("Không thể nạp trước thư viện biểu đồ")
        finally:
            self.finished.emit()
