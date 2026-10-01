import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from PyQt5.QtWidgets import QApplication
from controllers.prime_controller import PrimeController
from ui.main_window import MainWindow
from test_gui import wait_until
import test_slot_summary

APP = QApplication.instance() or QApplication([])


class SlotGuiTests(unittest.TestCase):
    def test_active_tab_cache_clear_and_recovery(self):
        fixture = test_slot_summary.SlotSummaryTests()
        fixture.setUp()
        window = MainWindow()
        controller = PrimeController(window,fixture.db)
        errors = []
        controller.dialogs.show_error = errors.append
        try:
            window.showMaximized()
            controller.initialize_database()
            wait_until(lambda: not controller.busy)
            root = window.prime_page
            page = root.yield_slot_page
            self.assertIsNone(page.chart)
            root.tabs.setCurrentWidget(page)
            criteria = SimpleNamespace(date_from='20260911',date_to='20260913',tiers=['T1'],models=['ABCDE'],eqp='LI-01',slot=1,scrap_codes=['3308'])
            with patch('controllers.prime_controller.SummaryWorker',side_effect=AssertionError('Hidden Summary queried')):
                controller.load_summary(criteria)
                wait_until(lambda: not controller.busy)
            self.assertEqual(errors,[])
            self.assertIsNone(root.summary_page.chart)
            self.assertEqual(page.table.item(0,0).text(),'3')
            self.assertEqual(page.table.item(4,0).text(),'333333')
            self.assertEqual(page.table.item(3,1).text(),'')
            self.assertEqual(len(page.chart.axes.patches),48)
            self.assertEqual([p.get_height() for p in page.chart.axes.patches],[1]+[0]*46+[1])
            self.assertEqual(page.daily_summary.table.item(3, 4).text(), '66.67%')
            criteria.slot=48
            criteria.scrap_codes=[]
            controller.load_summary(criteria)
            wait_until(lambda: not controller.busy)
            self.assertEqual(page.daily_summary.table.item(3, 1).text(), '1')
            self.assertEqual(page.daily_summary.table.item(3, 4).text(), '0.00%')
            self.assertEqual(page.daily_summary.chart.size().width(), 1300)
            with patch('controllers.prime_controller.SlotSummaryWorker',side_effect=AssertionError('Cache missed')):
                controller.load_summary(criteria)
            criteria.eqp=None
            controller.load_summary(criteria)
            self.assertIsNone(page.table.item(0,0))
            criteria.eqp='LI-01'
            controller.load_summary(criteria)
            wait_until(lambda: not controller.busy)
            self.assertTrue(page.chart.axes.axison)
            root.tabs.setCurrentWidget(root.summary_page)
            with patch('controllers.prime_controller.SlotSummaryWorker',side_effect=AssertionError('Hidden slot queried')):
                controller.load_summary(criteria)
                wait_until(lambda: not controller.busy)
            self.assertIsNotNone(root.summary_page.chart)
            controller.refresh_filter_options()
            wait_until(lambda: not controller.busy)
            self.assertIsNone(controller._slot_key)
            self.assertIsNone(controller._summary_key)
            self.assertIsNone(page.table.item(0,0))
            self.assertEqual(errors,[])
            root.tabs.setCurrentWidget(page)
            with patch('repositories.slot_summary_repository.SlotSummaryRepository.load', side_effect=RuntimeError('slot query error')):
                controller.load_summary(criteria)
                wait_until(lambda: not controller.busy)
            self.assertEqual(errors,['slot query error'])
            self.assertIsNone(controller._slot_key)
            self.assertIsNone(controller.dialogs.progress)
            self.assertTrue(root.filter_panel.apply_filter_button.isEnabled())
            controller.load_summary(criteria)
            wait_until(lambda: not controller.busy)
            self.assertEqual(page.table.item(0,0).text(),'3')
        finally:
            window.close()
            wait_until(lambda: not controller.busy)
            fixture.tearDown()
