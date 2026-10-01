import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QApplication, QPushButton, QLabel, QDialog
from controllers.prime_controller import PrimeController
from database.connection import connection
from ui.main_window import MainWindow
from ui.dialogs.date_range_dialog import DateRangeDialog

APP = QApplication.instance() or QApplication([])


def wait_until(predicate):
    """Xử lý sự kiện Qt và chờ điều kiện kiểm thử trong giới hạn thời gian."""
    deadline = time.monotonic() + 10
    while not predicate():
        APP.processEvents()
        if time.monotonic() > deadline:
            raise AssertionError("Thread không hoàn tất trong thời gian test")
        time.sleep(.005)
    APP.processEvents()


class GuiTests(unittest.TestCase):
    def setUp(self):
        """Tạo database và cửa sổ độc lập cho mỗi kiểm thử giao diện."""
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.db = self.base / "database/li.db"
        self.window = MainWindow()
        self.controller = PrimeController(self.window, self.db)
        self.errors = []
        self.results = []
        self.controller.dialogs.show_error = self.errors.append
        self.controller.dialogs.show_result = self.results.append
        self.window.showMaximized()
        self.controller.initialize_database()
        wait_until(lambda: not self.controller.busy)

    def tearDown(self):
        """Đóng cửa sổ an toàn và xóa dữ liệu tạm sau kiểm thử."""
        self.window.close()
        wait_until(lambda: not self.controller.busy)
        APP.processEvents()
        self.temp.cleanup()

    def test_startup_import_buttons_and_maximized(self):
        """Kiểm tra startup import buttons and maximized."""
        self.assertTrue(self.db.exists())
        self.assertTrue(self.window.isMaximized())
        page = self.window.centralWidget()
        self.assertEqual(len(page.findChildren(QPushButton)), 3)
        self.assertIsNotNone(page.filter_panel)
        self.assertEqual(page.import_button.text(), "IMPORT PRIME")
        self.assertTrue(page.import_button.isEnabled())
        self.assertEqual(page.cum_import_button.text(), "IMPORT CUM")
        self.assertTrue(page.cum_import_button.isEnabled())
        self.assertEqual(self.errors, [])

    def test_date_validation(self):
        """Kiểm tra date validation."""
        dialog = DateRangeDialog()
        dialog.date_from.setDate(QDate(2026, 9, 12))
        dialog.date_to.setDate(QDate(2026, 9, 11))
        dialog.accept()
        self.assertNotEqual(dialog.result(), QDialog.Accepted)
        dialog.date_to.setDate(QDate(2026, 9, 13))
        self.assertEqual(dialog.business_dates(), ("20260912", "20260913"))

    def test_button_import_reimport(self):
        """Kiểm tra button import reimport."""
        folder = self.base / "logs/AT-H903/260910"
        folder.mkdir(parents=True)
        text = (
            "<ENDTIME>20260910152504</ENDTIME><TESTER>AI-H903</TESTER>"
            "<PARTID>MZWLO3T8HCLS-01AGG-JZ7</PARTID><LOTID>LOT1</LOTID>"
            "<PORT>37:38:39:40:</PORT><HBIN>1:0:0:0:</HBIN>"
            "<SCRAP_CODE>0:0:0:0:</SCRAP_CODE>"
            "<SERIAL_NO>SERIAL1:NULL:NULL:NULL:</SERIAL_NO>"
            "<TESTCNT>3:NULL:NULL:NULL:</TESTCNT>")
        (folder / "log.txt").write_text(text, encoding="utf-8")
        order = []
        def choose_dates(dialog):
            """Giả lập người dùng chọn khoảng ngày trong kiểm thử."""
            order.append("dates")
            dialog.date_from.setDate(QDate(2026, 9, 10))
            dialog.date_to.setDate(QDate(2026, 9, 10))
            return QDialog.Accepted
        def choose_folder(*args):
            """Giả lập người dùng chọn thư mục log trong kiểm thử."""
            order.append("folder")
            return str(self.base / "logs")
        with patch.object(DateRangeDialog, "exec_", choose_dates), patch(
                "ui.dialogs.import_dialogs.QFileDialog.getExistingDirectory", choose_folder):
            self.window.prime_page.import_button.click()
        wait_until(lambda: not self.controller.busy)
        self.assertEqual(order, ["dates", "folder"])
        self.assertEqual((self.results[0].inserted, self.results[0].passed), (1, 1))
        self.controller.start_import(self.base / "logs", ("20260910",))
        wait_until(lambda: not self.controller.busy)
        self.assertEqual((self.results[-1].deleted, self.results[-1].inserted), (1, 1))
        with connection(self.db) as conn:
            row = conn.execute("SELECT SLOT,QTY,TEST_COUNT,SCRAPCODE FROM prime_data").fetchone()
            self.assertEqual(tuple(row), (37, 1, 3, None))
        self.assertIsNone(self.controller.dialogs.progress)
        self.assertEqual(self.errors, [])

    def test_close_idle_once(self):
        """Một yêu cầu close khi rảnh phải đóng cửa sổ, không cần gọi lần hai."""
        self.assertFalse(self.controller.busy)
        self.assertTrue(self.window.isVisible())
        self.window.close()
        APP.processEvents()
        self.assertFalse(self.window.isVisible())

    def test_safe_close(self):
        """Kiểm tra safe close."""
        self.controller.initialize_database()
        self.window.close()
        wait_until(lambda: not self.controller.busy)
        self.assertFalse(self.window.isVisible())

    def test_cancel_selection_does_not_import(self):
        """Kiểm tra cancel selection does not import."""
        with patch.object(DateRangeDialog, "exec_", return_value=QDialog.Rejected):
            self.window.prime_page.import_button.click()
        self.assertFalse(self.controller.busy)
        self.assertEqual(self.results, [])


if __name__ == "__main__":
    unittest.main()
