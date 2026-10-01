import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PyQt5.QtWidgets import QApplication

from controllers.prime_controller import PrimeController
from database.connection import connection
from database.schema import initialize_database
from repositories.machine_slot_yield_repository import (
    MachineSlotYieldRepository,
)
from ui.main_window import MainWindow


APP = QApplication.instance() or QApplication([])


def wait_until(predicate):
    """Xử lý sự kiện Qt đến khi worker hoàn tất hoặc hết thời gian."""
    deadline = time.monotonic() + 10
    while not predicate():
        APP.processEvents()
        if time.monotonic() > deadline:
            raise AssertionError("Thread không hoàn tất trong thời gian test")
        time.sleep(.005)
    APP.processEvents()


class MachineSlotYieldTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "database/li.db"
        self.db.parent.mkdir(parents=True)
        initialize_database(self.db)

    def tearDown(self):
        self.temp.cleanup()

    def test_default_save_and_reopen_preserve_config(self):
        """Cấu hình mặc định và giá trị chỉnh sửa phải bền vững."""
        repository = MachineSlotYieldRepository(self.db)
        default = repository.get_config()
        self.assertEqual(
            (default.target_15, default.target_30,
             default.continuous_fail_count),
            (70.0, 75.0, 3),
        )

        repository.save_config("//server/logs", 71.25, 76.5, 5, 8)
        initialize_database(self.db)
        saved = repository.get_config()
        self.assertEqual(saved.log_folder, "//server/logs")
        self.assertEqual(saved.target_15, 71.25)
        self.assertEqual(saved.target_30, 76.5)
        self.assertEqual(saved.continuous_fail_count, 5)
        self.assertEqual(saved.different_scrap_fail_count, 8)

        with connection(self.db) as conn:
            self.assertEqual(
                conn.execute(
                    "SELECT COUNT(*) FROM machine_slot_yield_config"
                ).fetchone()[0],
                1,
            )

    def test_tab_lazy_load_and_save_button(self):
        """Tab chỉ tạo khi mở và nút Save ghi đủ bốn trường."""
        window = MainWindow()
        controller = PrimeController(window, self.db)
        window.show()
        controller.initialize_database()
        wait_until(lambda: not controller.busy)

        self.assertIsNone(window.prime_page.machine_slot_yield_page)
        window.prime_page.tabs.setCurrentWidget(
            window.prime_page.machine_slot_yield_host
        )
        APP.processEvents()
        page = window.prime_page.machine_slot_yield_page
        self.assertIsNotNone(page)
        self.assertEqual(page.continuous_fail_spin.value(), 3)

        page.log_folder_edit.setText("D:/LI/log")
        page.target_15_spin.setValue(72.5)
        page.target_30_spin.setValue(77.5)
        page.continuous_fail_spin.setValue(4)
        page.different_scrap_fail_spin.setValue(6)
        with patch(
            "ui.pages.machine_slot_yield_page.QMessageBox.information"
        ) as information:
            page.save_button.click()
        information.assert_called_once()

        saved = MachineSlotYieldRepository(self.db).get_config()
        self.assertEqual(
            (saved.log_folder, saved.target_15, saved.target_30,
             saved.continuous_fail_count),
            ("D:/LI/log", 72.5, 77.5, 4),
        )
        self.assertEqual(saved.different_scrap_fail_count, 6)
        window.close()
        APP.processEvents()


if __name__ == "__main__":
    unittest.main()
