# import ctypes
# import logging
# import sys
# from pathlib import Path
#
# from PyQt5.QtCore import QTimer
# from PyQt5.QtGui import QIcon
# from PyQt5.QtWidgets import QApplication
#
# from controllers.prime_controller import PrimeController
# from ui.main_window import MainWindow
#
#
# def configure_logging():
#     """Gửi tiến độ INFO ra stdout, giữ cảnh báo và lỗi ở stderr."""
#     progress_handler = logging.StreamHandler(sys.stdout)
#     progress_handler.setLevel(logging.INFO)
#     progress_handler.addFilter(lambda record: record.levelno < logging.WARNING)
#
#     error_handler = logging.StreamHandler(sys.stderr)
#     error_handler.setLevel(logging.WARNING)
#
#     logging.basicConfig(
#         level=logging.INFO,
#         format="%(asctime)s %(levelname)s %(message)s",
#         handlers=[progress_handler, error_handler],
#     )
#
#
# def resource_path(filename: str) -> Path:
#     """Lấy đúng đường dẫn tài nguyên khi chạy Python hoặc file EXE."""
#     if hasattr(sys, "_MEIPASS"):
#         return Path(sys._MEIPASS) / filename
#
#     return Path(__file__).resolve().parent / filename
#
#
# def main():
#     """Mở giao diện tối đa và khởi tạo database sau khi hiện cửa sổ."""
#
#     # Giúp Windows hiển thị đúng icon riêng của ứng dụng trên taskbar.
#     if sys.platform == "win32":
#         app_id = "LI.Yield.PerformanceMonitor.1.0"
#         ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
#
#     app = QApplication(sys.argv)
#     app.setApplicationName("LI Yield")
#     app.setOrganizationName("LI_Yield")
#
#     icon_path = resource_path("icon.ico")
#     app_icon = QIcon(str(icon_path))
#     app.setWindowIcon(app_icon)
#
#     window = MainWindow()
#     window.setWindowIcon(app_icon)
#
#     controller = PrimeController(window)
#
#     # Giữ controller tồn tại trong suốt thời gian chạy.
#     window.controller = controller
#
#     window.showMaximized()
#     QTimer.singleShot(0, controller.initialize_database)
#
#     return app.exec_()
#
#
# if __name__ == "__main__":
#     sys.exit(main())


"""Chạy giao diện: python main.py."""
import ctypes
import logging
import sys
from pathlib import Path

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from controllers.prime_controller import PrimeController
from ui.main_window import MainWindow


def configure_logging():
    """Gửi tiến độ INFO ra stdout, giữ cảnh báo và lỗi ở stderr."""
    progress_handler = logging.StreamHandler(sys.stdout)
    progress_handler.setLevel(logging.INFO)
    progress_handler.addFilter(lambda record: record.levelno < logging.WARNING)

    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setLevel(logging.WARNING)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[progress_handler, error_handler],
    )


def resource_path(filename: str) -> Path:
    """Lấy đúng đường dẫn tài nguyên khi chạy Python hoặc file EXE."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / filename

    return Path(__file__).resolve().parent / filename


def main():
    """Mở giao diện tối đa và khởi tạo database sau khi hiện cửa sổ."""

    # Giúp Windows hiển thị đúng icon riêng của ứng dụng trên taskbar.
    if sys.platform == "win32":
        app_id = "LI.Yield.PerformanceMonitor.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

    app = QApplication(sys.argv)
    app.setApplicationName("LI Yield")
    app.setOrganizationName("LI_Yield")

    icon_path = resource_path("icon.ico")
    app_icon = QIcon(str(icon_path))
    app.setWindowIcon(app_icon)

    window = MainWindow()
    window.setWindowIcon(app_icon)

    controller = PrimeController(window)

    # Giữ controller tồn tại trong suốt thời gian chạy.
    window.controller = controller

    window.showMaximized()
    QTimer.singleShot(0, controller.initialize_database)
    QTimer.singleShot(500, controller.start_chart_preload)

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
