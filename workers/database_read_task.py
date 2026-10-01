"""Retry only GUI reads on SQLite contention, retaining the same request/thread."""
from functools import wraps
from threading import Event
from PyQt5.QtCore import QThread
from database.read_wait import GUI_READ_TIMEOUT, is_database_busy, read_timeout

RETRY_SECONDS = 5.0


def prepare_read_task(worker):
    event = getattr(worker, '_database_cancel', None)
    if event is None:
        event = getattr(worker, 'cancel_event', None)
        if event is None:
            event = getattr(worker, 'cancel', None)
        if not isinstance(event, Event):
            event = Event()
        worker._database_cancel = event
    return event


def database_read_task(run):
    @wraps(run)
    def execute(worker, *args, **kwargs):
        cancel = prepare_read_task(worker)
        # Alarm edits are deliberately never retried and retain their own timeout.
        enabled = getattr(worker, 'edit', None) is None
        token = read_timeout.set(GUI_READ_TIMEOUT if enabled else None)
        waiting = False
        try:
            while not cancel.is_set():
                try:
                    return run(worker, *args, **kwargs)
                except Exception as error:
                    if not enabled or not is_database_busy(error):
                        raise
                    if not waiting:
                        waiting = True
                        worker.database_waiting.emit(True)
                    # No connection/transaction survives the failed attempt.
                    if cancel.wait(RETRY_SECONDS):
                        return
        except Exception as error:
            if not cancel.is_set():
                if hasattr(worker, 'failed'):
                    worker.failed.emit(str(error))
                else:
                    worker.error = str(error)
        finally:
            read_timeout.reset(token)
            if waiting:
                worker.database_waiting.emit(False)
            # QThread itself emits finished after run returns.
            if not isinstance(worker, QThread):
                worker.finished.emit()
    return execute
