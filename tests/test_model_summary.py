import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import QApplication
from database.connection import connection
from database.schema import initialize_database
from repositories.model_summary_repository import ModelSummaryRepository
from controllers.prime_controller import PrimeController
from ui.main_window import MainWindow
from test_gui import wait_until

APP = QApplication.instance() or QApplication([])


class ModelSummaryTests(unittest.TestCase):
    """Kiểm tra tổng hợp, bộ lọc và cache qua luồng SEARCH thực tế."""

    def setUp(self):
        """Tạo nhiều scrap trên một bản ghi, nhiều ngày/máy/tier và Model rỗng sản lượng."""
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / 'model.db'
        initialize_database(self.db)
        self.repo = ModelSummaryRepository(self.db)
        with connection(self.db) as conn:
            for day, eqp, tier, model, iq, oq, scraps in [
                ('20260912','LI-01','T1','ABCDE',100,90,{'4502':3,'4528':7}),
                ('20260913','LI-01','T1','ABCDE',900,891,{'4502':9}),
                ('20260913','LI-02','T1','ABCDE',50,40,{'4528':10}),
                ('20260913','LI-01','T1','FGHIJ',0,0,{}),
                ('20260913','LI-01','T1','KLMNO',50,48,{'9999':2}),
                ('20260911','LI-01','T1','ABCDE',100,1,{'4502':99}),
                ('20260913','LI-01','T2','ABCDE',100,1,{'4502':99}),
            ]:
                row_id = conn.execute('''INSERT INTO cum_data
                    (DATE,TIME,PRODUCT,EQPID,INQTY,OUTQTY,FAILQTY,YIELD,MODEL,TIER)
                    VALUES (?,'08:00:00','PRODUCT',?,?,?,999,0,?,?)''',
                    (day,eqp,iq,oq,model,tier)).lastrowid
                for code, qty in scraps.items():
                    conn.execute('INSERT INTO cum_scrap_detail(cum_data_id,scrap_code,qty) VALUES (?,?,?)',
                                 (row_id, code, qty))

    def tearDown(self):
        """Xóa database thử nghiệm."""
        self.temp.cleanup()

    def test_quantities_filters_and_dynamic_codes(self):
        """Không nhân sản lượng qua JOIN; Yield có trọng số; không giới hạn danh sách scrap."""
        r = self.repo.load('20260912','20260913',['T1'])
        self.assertEqual([row.model for row in r.rows], ['ABCDE','FGHIJ','KLMNO'])
        first = r.rows[0]
        self.assertEqual((first.in_qty,first.out_qty,first.fail_qty), (1050,1021,29))
        self.assertAlmostEqual(first.yield_percent,1021/1050*100)
        self.assertIsNone(r.rows[1].yield_percent)
        self.assertEqual(r.scrap_codes,['4502','4528','9999'])
        self.assertEqual(r.scrap_totals,{'4502':12,'4528':17,'9999':2})
        self.assertEqual(self.repo.load('20260912','20260913',[]).rows,[])
        other_tier = self.repo.load('20260912','20260913',['T2'])
        self.assertEqual(other_tier.rows[0].in_qty,100)
        self.assertEqual(other_tier.scrap_totals,{'4502':99})

    def test_query_plan_uses_existing_indexes(self):
        """Xác nhận query thực tế dùng index lọc và index JOIN sẵn có."""
        with connection(self.db) as conn:
            before = conn.execute('SELECT COUNT(*) FROM cum_data').fetchone()[0]
            conn.execute('DROP INDEX idx_cum_tier_date_model')
        initialize_database(self.db)
        initialize_database(self.db)
        with connection(self.db) as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM cum_data').fetchone()[0], before)
            statements = []
            conn.set_trace_callback(statements.append)
            self.repo.load('20260912','20260913',['T1'],conn=conn)
            conn.set_trace_callback(None)
            selects = [s for s in statements if s.lstrip().startswith('SELECT')]
            self.assertEqual(len(selects),2)
            plans = [' '.join(r[3] for r in conn.execute('EXPLAIN QUERY PLAN '+s)) for s in selects]
            self.assertIn('idx_cum_tier_date_model', plans[0])
            self.assertIn('SEARCH data USING', plans[1])
            self.assertIn('sqlite_autoindex_cum_scrap_detail', plans[1])

    def test_search_copy_chart_cache_and_invalidation(self):
        """Đi qua controller/worker; đổi scrap không SQL và Copy All vẫn chứa mọi cột."""
        window = MainWindow()
        controller = PrimeController(window,self.db)
        errors = []
        controller.dialogs.show_error = errors.append
        try:
            controller.initialize_database()
            wait_until(lambda:not controller.busy)
            widget = window.prime_page.yield_slot_page.model_summary
            window.prime_page.tabs.blockSignals(True)
            window.prime_page.tabs.setCurrentWidget(window.prime_page.yield_slot_page)
            window.prime_page.tabs.blockSignals(False)
            self.assertIsNone(widget.chart)
            c = SimpleNamespace(date_from='20260912',date_to='20260913',tiers=['T1'],
                models=['ABCDE','FGHIJ','KLMNO'],eqp=None,slot=None,scrap_codes=['4502','4528'])
            controller.load_summary(c)
            wait_until(lambda:not controller.busy)
            self.assertEqual(errors,[])
            self.assertEqual(widget.table_model.rowCount(),4)
            self.assertEqual(widget.table_model.columnCount(),8)
            self.assertEqual(len(widget.chart.fail_axis.patches),2)
            self.assertEqual(widget.table.columnSpan(3,0),5)
            self.assertAlmostEqual(widget.chart.yield_axis.lines[0].get_ydata()[0],1021/1050*100)
            widget.copy_all()
            copied = APP.clipboard().text()
            self.assertEqual(copied.splitlines()[0],'Model\tIn\tOut\tFail\tYield\t4502\t4528\t9999')
            self.assertEqual(copied.splitlines()[-1],'Total\t\t\t\t\t12\t17\t2')
            original = widget.result
            c.scrap_codes = ['9999']
            with patch('controllers.prime_controller.SlotSummaryWorker',side_effect=AssertionError('Unexpected SQL')):
                controller.load_summary(c)
            self.assertIs(widget.result,original)
            self.assertEqual(len(widget.chart.fail_axis.patches),1)
            self.assertEqual([b.get_height() for b in widget.chart.fail_axis.patches],[2])
            widget.copy_all()
            self.assertEqual(APP.clipboard().text(),copied)
            c.scrap_codes=[]
            controller.load_summary(c)
            self.assertEqual(len(widget.chart.fail_axis.patches),0)
            self.assertEqual(len(widget.chart.yield_axis.lines),0)
            controller.refresh_filter_options()
            wait_until(lambda:not controller.busy)
            self.assertEqual(widget.table_model.rowCount(),0)
            self.assertIsNone(widget.result)
            self.assertFalse(widget.copy_button.isEnabled())
        finally:
            window.close()
            wait_until(lambda:not controller.busy)

    def test_tab_switch_applies_current_controls_to_model_summary(self):
        """Quay lại Summary dùng ngày vừa sửa trên bộ lọc, không cần bấm SEARCH."""
        window = MainWindow()
        controller = PrimeController(window, self.db)
        errors = []
        controller.dialogs.show_error = errors.append
        try:
            controller.initialize_database()
            wait_until(lambda: not controller.busy)
            root = window.prime_page
            panel = root.filter_panel
            panel.from_date_edit.setDate(QDate(2026, 9, 12))
            panel.to_date_edit.setDate(QDate(2026, 9, 13))
            for listing, selected in [(panel.tier_list, 'T1'), (panel.model_list, 'ABCDE')]:
                listing.item(0).setCheckState(Qt.Unchecked)
                for index in range(1, listing.count()):
                    item = listing.item(index)
                    item.setCheckState(Qt.Checked if item.data(Qt.UserRole) == selected else Qt.Unchecked)
            root.tabs.setCurrentWidget(root.summary_page)
            wait_until(lambda: not controller.busy)
            root.tabs.setCurrentWidget(root.yield_slot_page)
            wait_until(lambda: not controller.busy)
            self.assertEqual(root.yield_slot_page.model_summary.result.rows[0].in_qty, 1050)
            root.tabs.setCurrentWidget(root.summary_page)
            wait_until(lambda: not controller.busy)
            panel.to_date_edit.setDate(QDate(2026, 9, 12))
            root.tabs.setCurrentWidget(root.yield_slot_page)
            wait_until(lambda: not controller.busy)
            self.assertEqual(root.yield_slot_page.model_summary.result.rows[0].in_qty, 100)
            self.assertEqual(errors, [])
        finally:
            window.close()
            wait_until(lambda: not controller.busy)


    def test_legend_style_and_slot_only_cache(self):
        """Legend chỉ chứa mã có số lượng; đổi SLOT không query lại CUM."""
        window = MainWindow()
        controller = PrimeController(window, self.db)
        errors = []
        controller.dialogs.show_error = errors.append
        try:
            controller.initialize_database()
            wait_until(lambda: not controller.busy)
            root = window.prime_page
            root.tabs.blockSignals(True)
            root.tabs.setCurrentWidget(root.yield_slot_page)
            root.tabs.blockSignals(False)
            self.assertFalse(hasattr(root.summary_page, 'model_summary'))
            c = SimpleNamespace(date_from='20260912', date_to='20260913', tiers=['T1'],
                models=['ABCDE'], eqp='LI-01', slot=None, scrap_codes=['4502', '4528', '9999'])
            controller.load_summary(c)
            wait_until(lambda: not controller.busy)
            widget = root.yield_slot_page.model_summary
            self.assertEqual([t.get_text() for t in widget.chart.figure.legends[0].texts],
                             ['4502','4528','9999','Yield'])
            self.assertEqual(widget.chart.width(),1550)
            self.assertEqual(widget.chart.height(),550)
            self.assertEqual(widget.chart.fail_axis.title.get_fontweight(),'normal')
            self.assertEqual(widget.chart.figure.legends[0]._ncols,4)
            self.assertLess(widget.table.columnWidth(5),82)
            self.assertGreater(widget.table.maximumWidth(),1300)
            cached = widget.result
            # EQP/Model/SLOT thay đổi vẫn dùng đúng đối tượng CUM đã tải.
            for eqp, models, slot in [('LI-02',['FGHIJ'],1),(None,[],None),('LI-01',['UNKNOWN'],2)]:
                c.eqp, c.models, c.slot = eqp, models, slot
                with patch.object(ModelSummaryRepository,'load',side_effect=AssertionError('CUM cache missed')):
                    controller.load_summary(c)
                    wait_until(lambda: not controller.busy)
                self.assertIs(widget.result,cached)
                self.assertEqual([row.model for row in widget.result.rows],['ABCDE','FGHIJ','KLMNO'])
            # Ép tải mới với Model rỗng để kiểm tra repository/worker cũng độc lập.
            controller._slot_key = None
            c.models = []
            controller.load_summary(c)
            wait_until(lambda: not controller.busy)
            self.assertEqual(widget.result.scrap_totals,{'4502':12,'4528':17,'9999':2})
            c.tiers = ['T2']
            controller.load_summary(c)
            wait_until(lambda: not controller.busy)
            self.assertEqual(widget.result.scrap_totals,{'4502':99})
            c.date_to = '20260912'
            controller.load_summary(c)
            wait_until(lambda: not controller.busy)
            self.assertEqual(widget.result.rows,[])
            c.scrap_codes=['0001']
            controller.load_summary(c)
            self.assertEqual(len(widget.chart.figure.legends),0)
            self.assertEqual(len(widget.chart.fail_axis.patches),0)
            self.assertEqual(errors,[])
        finally:
            window.close()
            wait_until(lambda: not controller.busy)


if __name__ == '__main__':
    unittest.main()
