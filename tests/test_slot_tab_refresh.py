import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
from unittest.mock import patch
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import QApplication, QLabel
from controllers.prime_controller import PrimeController
from ui.main_window import MainWindow
from test_gui import wait_until
import test_slot_summary

APP = QApplication.instance() or QApplication([])


class SlotTabRefreshTests(unittest.TestCase):
    def test_tab_switch_reads_unsubmitted_filters_and_uses_cache(self):
        fixture = test_slot_summary.SlotSummaryTests()
        fixture.setUp()
        window = MainWindow()
        controller = PrimeController(window, fixture.db)
        errors = []
        controller.dialogs.show_error = errors.append
        try:
            window.showMaximized()
            controller.initialize_database()
            wait_until(lambda: not controller.busy)
            root = window.prime_page
            panel = root.filter_panel
            self.assertIsNone(root.summary_page.chart)
            self.assertIsNone(root.yield_slot_page.chart)
            panel.from_date_edit.setDate(QDate(2026,9,11))
            panel.to_date_edit.setDate(QDate(2026,9,13))
            panel.eqp_combo.setCurrentIndex(panel.eqp_combo.findData('LI-01'))
            for listing, selected in [(panel.tier_list, 'T1'), (panel.model_list, 'ABCDE')]:
                listing.item(0).setCheckState(Qt.Unchecked)
                for index in range(1,listing.count()):
                    listing.item(index).setCheckState(Qt.Checked if listing.item(index).data(Qt.UserRole)==selected else Qt.Unchecked)
            with patch('controllers.prime_controller.SummaryWorker',side_effect=AssertionError('Hidden Summary queried')):
                root.tabs.setCurrentWidget(root.yield_slot_page)
                wait_until(lambda: not controller.busy)
            slot = root.yield_slot_page
            self.assertEqual(slot.table.item(0,0).text(),'3')
            self.assertEqual(slot.slot_header.text(),'Slot')
            self.assertTrue(slot.slot_header.isVisible())
            self.assertFalse(any(label.text().startswith('Áp dụng') for label in slot.findChildren(QLabel)))
            self.assertGreaterEqual(slot.table.columnWidth(47), slot.table.fontMetrics().horizontalAdvance('1000000')+6)
            self.assertLess(slot.table.columnWidth(47),64)
            self.assertEqual(slot.chart.axes.get_ylim(),(0,1))
            self.assertTrue(all(line.get_visible() for line in slot.chart.axes.get_xgridlines()))
            self.assertTrue(all(line.get_visible() for line in slot.chart.axes.get_ygridlines()))
            for axis in (slot.chart.axes.xaxis,slot.chart.axes.yaxis):
                self.assertTrue(all(t.tick1line.get_markersize()==0 for t in axis.get_major_ticks()))
            with patch('controllers.prime_controller.SlotSummaryWorker',side_effect=AssertionError('Hidden Slot queried')):
                root.tabs.setCurrentWidget(root.summary_page)
                wait_until(lambda: not controller.busy)
            panel.to_date_edit.setDate(QDate(2026,9,12))
            root.tabs.setCurrentWidget(slot)
            wait_until(lambda: not controller.busy)
            self.assertEqual(slot.table.item(0,0).text(),'2')
            self.assertEqual(slot.table.item(3,0).text(),'50.00%')
            self.assertEqual(root.current_criteria.date_to,'20260912')
            root.tabs.setCurrentWidget(root.summary_page)
            wait_until(lambda: not controller.busy)
            self.assertEqual(controller._summary_key[1],'20260912')
            with patch('controllers.prime_controller.SlotSummaryWorker',side_effect=AssertionError('Cache missed')):
                root.tabs.setCurrentWidget(slot)
            root.tabs.setCurrentWidget(root.summary_page)
            wait_until(lambda: not controller.busy)
            panel.eqp_combo.setCurrentIndex(0)
            root.tabs.setCurrentWidget(slot)
            self.assertIsNone(slot.table.item(0,0))
            self.assertEqual(errors,[])
        finally:
            window.close()
            wait_until(lambda: not controller.busy)
            fixture.tearDown()
