"""Regression: changing tabs must not reload filters or unchanged file lists."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from PyQt5.QtWidgets import QApplication
from controllers.prime_controller import PrimeController
from database.schema import initialize_database
from repositories.database_management_repository import DatabaseManagementRepository
from repositories.filter_option_repository import FilterOptionRepository
from ui.main_window import MainWindow

APP = QApplication.instance() or QApplication([])


def wait(predicate):
    deadline = time.monotonic() + 10
    while not predicate():
        APP.processEvents()
        if time.monotonic() > deadline:
            raise AssertionError('Worker timeout')
        time.sleep(.002)
    APP.processEvents()


class FileTabCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / 'test.db'
        initialize_database(self.db)
        self.window = MainWindow()
        self.controller = PrimeController(self.window, self.db)
        self.window.show()
        self.controller.initialize_database()
        wait(lambda: self.controller._filters_ready and not self.controller.busy)
        self.page = self.window.prime_page
        self.page.tabs.setCurrentWidget(self.page.file_management_host)
        self.files = self.page.file_management_page
        wait(lambda: not self.files.is_busy())

    def tearDown(self):
        self.window.close()
        wait(lambda: self.window._can_close)
        self.temp.cleanup()

    def test_reopen_and_search_do_not_query_or_reset_filters(self):
        panel = self.page.filter_panel
        panel.eqp_combo.addItem('CUSTOM', 'CUSTOM')
        panel.eqp_combo.setCurrentIndex(1)
        before = panel.get_filter_criteria()
        self.files.prime_panel._selected_months = {'202609'}
        with patch.object(DatabaseManagementRepository, 'get_date_records') as lists, \
                patch.object(FilterOptionRepository, 'load_options') as filters:
            for _ in range(3):
                self.page.tabs.setCurrentWidget(self.page.machine_slot_yield_host)
                self.page.tabs.setCurrentWidget(self.page.file_management_host)
                panel.apply_filter_button.click()
                APP.processEvents()
            lists.assert_not_called()
            filters.assert_not_called()
        self.assertEqual(before, panel.get_filter_criteria())
        self.assertEqual(self.files.prime_panel._selected_months, {'202609'})
        self.assertIsNone(self.files.list_loading_dialog)

    def test_import_invalidates_only_affected_list(self):
        with patch.object(DatabaseManagementRepository, 'get_date_records', return_value=[]) as lists:
            self.controller._mark_file_data_changed('PRIME')
            wait(lambda: not self.files.is_busy())
            lists.assert_called_once_with('PRIME')

    def test_hidden_import_loads_on_next_visit(self):
        self.page.tabs.setCurrentWidget(self.page.machine_slot_yield_host)
        with patch.object(DatabaseManagementRepository, 'get_date_records', return_value=[]) as lists:
            self.controller._mark_file_data_changed('CUM')
            lists.assert_not_called()
            self.page.tabs.setCurrentWidget(self.page.file_management_host)
            wait(lambda: not self.files.is_busy())
            lists.assert_called_once_with('CUM')

    def test_manual_refresh_reads_both_lists_only(self):
        with patch.object(DatabaseManagementRepository, 'get_date_records', return_value=[]) as lists, \
                patch.object(FilterOptionRepository, 'load_options') as filters:
            self.files.refresh_button.click()
            wait(lambda: not self.files.is_busy())
            self.assertEqual([c.args[0] for c in lists.call_args_list], ['CUM', 'PRIME'])
            filters.assert_not_called()

    def test_failed_list_can_retry_on_revisit(self):
        with patch.object(DatabaseManagementRepository, 'get_date_records', side_effect=RuntimeError('locked')):
            self.files.load_if_needed(force=True)
            wait(lambda: not self.files.is_busy())
        self.assertTrue(self.files._dirty_types)
        self.page.tabs.setCurrentWidget(self.page.machine_slot_yield_host)
        self.page.tabs.setCurrentWidget(self.page.file_management_host)
        wait(lambda: not self.files.is_busy())
        self.assertFalse(self.files._dirty_types)

    def test_change_during_load_is_not_lost(self):
        from threading import Event
        gate = Event()
        calls = []
        def slow(repo, data_type):
            calls.append(data_type)
            if len(calls) == 1:
                gate.wait(3)
            return []
        try:
            with patch.object(DatabaseManagementRepository, 'get_date_records', slow):
                self.files.mark_data_changed('PRIME')
                wait(lambda: bool(calls))
                self.files.mark_data_changed('PRIME')
                gate.set()
                wait(lambda: not self.files.is_busy())
            self.assertEqual(calls, ['PRIME', 'PRIME'])
        finally:
            gate.set()


if __name__ == '__main__':
    unittest.main()
