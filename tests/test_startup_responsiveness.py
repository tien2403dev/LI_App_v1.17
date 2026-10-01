import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from threading import Event
from unittest.mock import patch
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
from controllers.prime_controller import PrimeController
from database.schema import initialize_database, _startup_schema_complete
from repositories.filter_option_repository import FilterOptionRepository, FilterOptionResult
from ui.main_window import MainWindow

APP = QApplication.instance() or QApplication([])


def wait(predicate):
    end = time.monotonic() + 8
    while not predicate():
        APP.processEvents()
        if time.monotonic() > end:
            raise AssertionError('Worker timeout')
        time.sleep(.002)
    APP.processEvents()


class StartupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / 'test.db'
        initialize_database(self.db)
        self.window = MainWindow()
        self.controller = PrimeController(self.window, self.db)
        self.errors = []
        self.controller.dialogs.show_error = self.errors.append
        self.window.show()

    def tearDown(self):
        self.window.close()
        wait(lambda: self.window._can_close)
        self.temp.cleanup()

    def test_no_heavy_library_before_window(self):
        code = '''import sys
from PyQt5.QtWidgets import QApplication
from controllers.prime_controller import PrimeController
from ui.main_window import MainWindow
app=QApplication([])
w=MainWindow(); c=PrimeController(w)
assert not any(x in sys.modules for x in ('matplotlib','numpy','pandas','openpyxl'))
'''
        subprocess.run([sys.executable, '-c', code], check=True, env=os.environ.copy())

    def test_slow_filters_leave_buttons_and_event_loop_available(self):
        gate = Event()
        def slow(*args):
            gate.wait(3)
            return FilterOptionResult(['EQP1'], [1], [], ['1'], ['MODEL'])
        try:
            with patch.object(FilterOptionRepository, 'load_options', slow):
                self.controller.initialize_database()
                wait(lambda: self.controller._filter_thread is not None)
                panel = self.window.prime_page.filter_panel
                self.assertTrue(panel.import_prime_button.isEnabled())
                self.assertTrue(panel.import_cum_button.isEnabled())
                self.assertTrue(panel.apply_filter_button.isEnabled())
                self.assertTrue(self.window.prime_page.tabs.tabBar().isEnabled())
                ticks = []
                QTimer.singleShot(20, lambda: ticks.append(True))
                wait(lambda: bool(ticks))
                with patch.object(self.controller.dialogs, 'choose_source', return_value=None) as choose:
                    panel.import_prime_button.click()
                    choose.assert_called_once()
                gate.set()
                wait(lambda: self.controller._filter_thread is None)
        finally:
            gate.set()
        self.assertEqual(self.errors, [])

    def test_search_during_filter_load_is_replayed(self):
        gate = Event()
        def slow(*args):
            gate.wait(3)
            return FilterOptionResult([], [], [], [], [])
        try:
            with patch.object(FilterOptionRepository, 'load_options', slow):
                self.controller.initialize_database()
                wait(lambda: self.controller._filter_thread is not None)
                self.window.prime_page.filter_panel.apply_filter_button.click()
                self.assertIsNotNone(self.controller._pending_search)
                with patch.object(self.controller, 'load_summary') as load:
                    gate.set()
                    wait(lambda: self.controller._filter_thread is None)
                    load.assert_called_once()
        finally:
            gate.set()

    def test_filter_error_allows_retry(self):
        with patch.object(FilterOptionRepository, 'load_options', side_effect=RuntimeError('locked')):
            self.controller.initialize_database()
            wait(lambda: self.controller._ready and not self.controller.busy and self.controller._filter_thread is None)
            self.assertFalse(self.controller._filters_ready)
            self.assertTrue(self.window.prime_page.filter_panel.apply_filter_button.isEnabled())
        self.controller.refresh_filter_options()
        wait(lambda: self.controller._filter_thread is None)
        self.assertTrue(self.controller._filters_ready)

    def test_current_schema_needs_no_write_lock(self):
        conn = sqlite3.connect(self.db)
        self.assertTrue(_startup_schema_complete(conn))
        conn.execute('BEGIN IMMEDIATE')
        try:
            # A reserved lock permits reads, but blocks the old INSERT OR IGNORE startup.
            started = time.monotonic()
            initialize_database(self.db)
            self.assertLess(time.monotonic()-started, 1)
        finally:
            conn.rollback()
            conn.close()

    def test_missing_schema_objects_still_repaired(self):
        with sqlite3.connect(self.db) as conn:
            conn.execute('DROP INDEX idx_prime_slot')
            conn.execute('DELETE FROM auto_import_scheduler')
        initialize_database(self.db)
        with sqlite3.connect(self.db) as conn:
            self.assertTrue(_startup_schema_complete(conn))

    def test_close_waits_for_preload_thread(self):
        gate = Event()
        try:
            with patch('workers.chart_preload_worker.preload_charts', lambda: gate.wait(3)):
                self.controller.start_chart_preload()
                self.window.close()
                self.assertFalse(self.window._can_close)
                gate.set()
                wait(lambda: self.window._can_close)
        finally:
            gate.set()

    def test_init_keeps_import_request_until_ready(self):
        self.controller.initialize_database()
        with patch.object(self.controller.dialogs, 'choose_source', return_value=None) as choose:
            self.window.prime_page.import_button.click()
            wait(lambda: choose.call_count == 1)
            wait(lambda: not self.controller.busy and self.controller._filter_thread is None)
        self.assertEqual(self.errors, [])

    def test_real_search_after_background_filters(self):
        self.controller.initialize_database()
        wait(lambda: self.controller._filters_ready)
        self.window.prime_page.filter_panel.apply_filter_button.click()
        wait(lambda: not self.controller.busy)
        self.assertIsNotNone(self.controller._summary_key)
        self.assertEqual(self.errors, [])

    def test_close_cancels_slow_filter_safely(self):
        started = Event()
        def slow(repo, cancel_event):
            started.set()
            cancel_event.wait(3)
            return FilterOptionResult([], [], [], [], [])
        with patch.object(FilterOptionRepository, 'load_options', slow):
            self.controller.initialize_database()
            wait(started.is_set)
            self.window.close()
            wait(lambda: self.window._can_close)
        self.assertEqual(self.errors, [])

    def test_preload_creates_no_charts(self):
        self.controller.start_chart_preload()
        wait(lambda: self.controller._preload_thread is None)
        self.assertIsNone(self.window.prime_page.yield_slot_page.chart)
        self.assertIn('ui.charts.cum_eqp_chart', sys.modules)


if __name__ == '__main__':
    unittest.main()
