import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from PyQt5.QtWidgets import QApplication
from controllers.prime_controller import PrimeController
from ui.main_window import MainWindow
from test_gui import wait_until
import test_daily_summary

APP = QApplication.instance() or QApplication([])


class DailyGuiTests(unittest.TestCase):
    def test_daily_charts_cache_and_reset(self):
        fixture = test_daily_summary.DailySummaryTests()
        fixture.setUp()
        window = MainWindow()
        controller = PrimeController(window, fixture.db)
        errors = []
        controller.dialogs.show_error = errors.append
        try:
            window.showMaximized()
            controller.initialize_database()
            wait_until(lambda: not controller.busy)
            criteria = SimpleNamespace(date_from='20260911',date_to='20260913',
                tiers=['T1'],models=['ABCDE'],eqp='LI-01',slot=None,scrap_codes=['3308'])
            controller.load_summary(criteria)
            wait_until(lambda: not controller.busy)
            daily = window.prime_page.summary_page.daily_summary
            self.assertEqual(errors, [])
            self.assertEqual(daily.daily_table.rowCount(),3)
            self.assertEqual(daily.daily_table.item(1,4).text(),'200000')
            self.assertEqual(daily.prime_daily_table.item(1,5).text(),'25.00%')
            self.assertIsNotNone(daily.daily_chart)
            self.assertIsNotNone(daily.prime_daily_chart)
            criteria.scrap_codes=['3313']
            with patch('controllers.prime_controller.SummaryWorker', side_effect=AssertionError('Unexpected SQL')):
                controller.load_summary(criteria)
            self.assertEqual(daily.prime_daily_table.columnCount(),8)
            criteria.eqp=None
            controller.load_summary(criteria)
            wait_until(lambda: not controller.busy)
            self.assertEqual(daily.daily_table.rowCount(),0)
            self.assertEqual(daily.prime_daily_table.rowCount(),0)
            self.assertIsNone(daily._cached_daily_result)
            self.assertEqual(errors, [])
        finally:
            window.close()
            wait_until(lambda: not controller.busy)
            fixture.tearDown()
