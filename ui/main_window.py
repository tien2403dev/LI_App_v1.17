from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtWidgets import QMainWindow
from ui.pages.prime_page import PrimePage


class MainWindow(QMainWindow):
    """Chỉ quản lý khung cửa sổ, không xử lý import hoặc SQL."""
    close_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LI Yield")
        self.setMinimumSize(1200, 900)
        self.prime_page = PrimePage()
        self.setCentralWidget(self.prime_page)
        self._can_close = False

    def finish_close(self):
        if self._can_close:
            return
        self._can_close = True
        # closeEvent hiện tại phải kết thúc trước khi gửi yêu cầu đóng mới.
        # Gọi close() trực tiếp tại đây bị Qt bỏ qua khi đang xử lý closeEvent.
        QTimer.singleShot(0, self.close)

    def closeEvent(self, event):
        if self._can_close:
            event.accept()
        else:
            event.ignore()
            self.close_requested.emit()
