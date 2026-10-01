import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from PyQt5.QtWidgets import QApplication
from database.schema import initialize_database
from database.connection import connection
from repositories.summary_repository import SummaryRepository
from controllers.prime_controller import PrimeController
from ui.main_window import MainWindow
from test_gui import wait_until

APP = QApplication.instance() or QApplication([])


class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / 'test.db'
        initialize_database(self.db)
        self.repo = SummaryRepository(self.db)
        with connection(self.db) as conn:
            for day, eqp, iq, oq, tier, model in [
                ('20260912','LI-01',100,90,'T1','ABCDE'),
                ('20260913','LI-01',900,891,'T1','ABCDE'),
                ('20260913','LI-02',50,40,'T1','ABCDE'),
                ('20260913','LI-03',0,0,'T1','ABCDE'),
                ('20260911','LI-01',100,0,'T1','ABCDE'),
                ('20260913','LI-04',100,0,'T2','ABCDE'),
                ('20260913','LI-05',100,0,'T1','XXXXX'),
            ]:
                conn.execute('''INSERT INTO cum_data
                    (DATE,TIME,PRODUCT,EQPID,INQTY,OUTQTY,FAILQTY,YIELD,MODEL,TIER)
                    VALUES (?,'08:00:00','PRODUCT',?,?,?,999,0,?,?)''',
                    (day,eqp,iq,oq,model,tier))

    def tearDown(self):
        self.temp.cleanup()

    def test_weighted_totals_and_filters(self):
        result = self.repo.load('20260912','20260913',['T1'],['ABCDE'])
        self.assertEqual([r.eqpid for r in result.rows], ['LI-01','LI-02','LI-03'])
        first = result.rows[0]
        self.assertEqual((first.in_qty,first.out_qty,first.fail_qty), (1000,981,19))
        self.assertAlmostEqual(first.fail_ppm,19000)
        self.assertAlmostEqual(first.yield_percent,98.1)
        self.assertEqual((result.total.in_qty,result.total.out_qty,result.total.fail_qty),(1050,1021,29))
        self.assertAlmostEqual(result.total.yield_percent,1021/1050*100)
        self.assertIsNone(result.rows[2].fail_ppm)
        self.assertIsNone(result.rows[2].yield_percent)
        for tiers,models in [([],['ABCDE']),(['T1'],[]),(['unknown'],['ABCDE'])]:
            empty = self.repo.load('20260912','20260913',tiers,models)
            self.assertEqual(empty.rows,[])
            self.assertIsNone(empty.total.yield_percent)

    def test_search_cache_error_and_refresh(self):
        window = MainWindow()
        controller = PrimeController(window,self.db)
        errors=[]
        controller.dialogs.show_error=errors.append
        controller.initialize_database()
        wait_until(lambda:not controller.busy)
        page=window.prime_page.summary_page
        self.assertIsNone(page.chart)
        c=SimpleNamespace(date_from='20260912',date_to='20260913',tiers=['T1'],models=['ABCDE'],eqp=None,slot=None,scrap_codes=[])
        controller.load_summary(c)
        wait_until(lambda:not controller.busy)
        self.assertEqual(page.summary_table.rowCount(),4)
        self.assertEqual(page.summary_table.item(0,4).text(),'19,000')
        self.assertEqual(len(page.chart.ppm_axis.patches),3)
        self.assertEqual(list(page.chart.yield_axis.lines[0].get_ydata()),[98.1,80,0])
        c.eqp='LI-01'
        controller.load_summary(c)
        wait_until(lambda:not controller.busy)
        c.slot=2;c.scrap_codes=['3212']
        with patch('controllers.prime_controller.SummaryWorker',side_effect=AssertionError('Cache missed')):
            controller.load_summary(c)
        controller.refresh_filter_options()
        wait_until(lambda:not controller.busy)
        self.assertIsNone(controller._summary_key)
        self.assertEqual(page.summary_table.rowCount(),0)
        with patch.object(SummaryRepository,'load',side_effect=RuntimeError('Test query failure')):
            controller.load_summary(c)
            wait_until(lambda:not controller.busy)
        self.assertEqual(errors,['Test query failure'])
        self.assertTrue(window.prime_page.filter_panel.apply_filter_button.isEnabled())
        controller.load_summary(c)
        wait_until(lambda:not controller.busy)
        self.assertEqual(page.summary_table.rowCount(),4)
        c.models=[]
        controller.load_summary(c)
        wait_until(lambda:not controller.busy)
        self.assertEqual(page.summary_table.rowCount(),1)
        self.assertEqual(len(page.chart.ppm_axis.patches),0)
        self.assertEqual(len(page.chart.figure.legends),0)
        controller._summary_key=None
        controller.load_summary(c)
        window.close()
        wait_until(lambda:not controller.busy)
        self.assertFalse(window.isVisible())
