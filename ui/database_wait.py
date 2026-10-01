"""One dismissible database-busy notice per window; all UI changes stay on GUI thread."""
from PyQt5.QtCore import QObject, Qt, pyqtSlot
from PyQt5.QtWidgets import (QMessageBox, QAbstractButton, QAbstractSpinBox,
                             QComboBox, QLineEdit, QTabBar, QHeaderView)
from workers.database_read_task import prepare_read_task

MESSAGE = 'Database đang cập nhật, vui lòng thử lại sau 2 phút'


class ReadBinding(QObject):
    def __init__(self, manager, worker, stop_loading):
        super().__init__(manager)
        self.manager = manager
        self.cancel = prepare_read_task(worker)
        self.stop_loading = stop_loading
        worker.database_waiting.connect(self.changed)
        worker.finished.connect(self.finished)

    @pyqtSlot(bool)
    def changed(self, waiting):
        self.manager.changed(self, waiting)

    @pyqtSlot()
    def finished(self):
        self.manager.changed(self, False)
        self.manager.bindings.discard(self)
        self.deleteLater()


class DatabaseWaitManager(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.bindings = set()
        self.waiting = set()
        self.dialog = None
        self.controls = []
        self.closing = False

    def bind(self, worker, stop_loading=None):
        binding = ReadBinding(self, worker, stop_loading)
        self.bindings.add(binding)
        return binding

    def changed(self, binding, waiting):
        if waiting and not self.closing:
            if binding in self.waiting:
                return
            if binding.stop_loading:
                binding.stop_loading()
            first = not self.waiting
            self.waiting.add(binding)
            if first:
                root = getattr(self.window, 'prime_page', self.window)
                # Tables remain visible; filter/search/edit buttons cannot change
                # the request captured by the running worker.
                types = (QAbstractButton, QAbstractSpinBox, QComboBox,
                         QLineEdit, QTabBar, QHeaderView)
                self.controls = [(w, not w.testAttribute(Qt.WA_ForceDisabled))
                                 for w in root.findChildren(QObject)
                                 if isinstance(w, types)]
                panel = getattr(root, "filter_panel", None)
                if panel is not None:
                    self.controls.append((panel, not panel.testAttribute(Qt.WA_ForceDisabled)))
                for widget, _ in self.controls:
                    widget.setEnabled(False)
                dialog = QMessageBox(QMessageBox.Information, 'Database đang cập nhật',
                                     MESSAGE, QMessageBox.Close, self.window)
                dialog.button(QMessageBox.Close).setText('Đóng')
                dialog.setModal(False)
                dialog.setWindowModality(Qt.NonModal)
                self.dialog = dialog
                dialog.show()
            if hasattr(self.window, 'statusBar'):
                self.window.statusBar().showMessage(MESSAGE + ' — đang tự động chờ kết nối.')
        else:
            self.waiting.discard(binding)
            if not self.waiting:
                self._restore()

    def _restore(self):
        if self.dialog is not None:
            self.dialog.close()
            self.dialog.deleteLater()
            self.dialog = None
        for widget, enabled in self.controls:
            try:
                widget.setEnabled(enabled)
            except RuntimeError:  # A child dialog/widget may have been destroyed.
                pass
        if self.controls and hasattr(self.window, 'statusBar') and not self.closing:
            self.window.statusBar().showMessage('Database sẵn sàng. Đang cập nhật kết quả...', 3000)
        self.controls = []

    def cancel_all(self):
        self.closing = True
        for binding in self.bindings:
            binding.cancel.set()
        self.waiting.clear()
        self._restore()


def wait_manager(widget):
    root = widget
    while root.parentWidget() is not None:
        root = root.parentWidget()
    manager = getattr(root, '_database_wait_manager', None)
    if manager is None:
        manager = DatabaseWaitManager(root)
        root._database_wait_manager = manager
    return manager


def cancel_read_task(worker):
    if worker is not None:
        prepare_read_task(worker).set()
