import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import tempfile
import unittest
from pathlib import Path
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import QApplication
from database.schema import initialize_database
from database.connection import connection
from repositories.filter_option_repository import FilterOptionRepository, FilterOptionResult
from ui.pages.prime_page import PrimePage

APP = QApplication.instance() or QApplication([])


class FilterTests(unittest.TestCase):
    def test_database_sources_and_no_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "li.db"
            initialize_database(db)
            with connection(db) as conn:
                for slot, tier, scrap in [(2, "T1", "3212"), (12, None, "3308"), (2, "T1", "invalid")]:
                    conn.execute("""INSERT INTO prime_data
                        (DATE,TIME,EQP,PARTNO,LOTNO,SLOT,RESULT,SCRAPCODE,TEST_COUNT,SERIAL,MODEL,TIER)
                        VALUES ('20260913','08:00:00','LI-01','ABCDE123','LOT',?,'FAIL',?,1,'SN','ABCDE',?)""",
                        (slot, scrap, tier))
                conn.execute("""INSERT INTO cum_data
                    (DATE,TIME,PRODUCT,EQPID,INQTY,OUTQTY,FAILQTY,YIELD,MODEL,TIER)
                    VALUES ('20260913','08:00:00','XXXXX123','CUM-EQP',1,0,1,0,'XXXXX','T2')""")
                conn.execute("INSERT INTO cum_scrap_detail(cum_data_id,scrap_code,qty) VALUES(1,'9999',1)")
                before = conn.execute("SELECT * FROM prime_data").fetchall()
            repo = FilterOptionRepository(db)
            options = repo.load_options()
            self.assertEqual(options.eqps, ['LI-01'])
            self.assertEqual(options.slots, [2, 12])
            self.assertEqual(options.models, ['ABCDE', 'XXXXX'])
            self.assertEqual(options.tiers, ['T1', 'T2'])
            self.assertEqual(options.scrap_codes, ['3212','3308','9999'])
            with connection(db) as conn:
                self.assertEqual(before, conn.execute("SELECT * FROM prime_data").fetchall())
                conn.execute('DELETE FROM prime_data')
            self.assertEqual(repo.load_options().eqps, [])
            # CUM vẫn được chọn và thống kê khi PRIME rỗng.
            cum_options = repo.load_options()
            self.assertEqual(cum_options.models, ['XXXXX'])
            page = PrimePage()
            page.load_filter_options(cum_options)
            selected_models = page.filter_panel._get_selected_models()
            self.assertEqual(selected_models, ['XXXXX'])
            from repositories.summary_repository import SummaryRepository
            result = SummaryRepository(db).load(
                '20260908', '20260913', cum_options.tiers, selected_models)
            self.assertEqual(len(result.rows), 1)
            self.assertEqual(result.rows[0].eqpid, 'CUM-EQP')
            self.assertEqual(result.total.in_qty, 1)
            self.assertEqual(result.total.fail_qty, 1)
            page.deleteLater()

    def test_performance_indexes_created(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "li.db"
            initialize_database(db)
            with connection(db) as conn:
                index_names = {
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='index'"
                    )
                }
            self.assertIn("idx_prime_slot", index_names)
            self.assertIn("idx_prime_model", index_names)
            self.assertIn("idx_prime_tier_model", index_names)
            self.assertIn("idx_prime_scrapcode", index_names)
            self.assertIn("idx_cum_model", index_names)
            self.assertIn("idx_cum_tier_model_date_eqp", index_names)

    def test_ui_criteria_and_select_all(self):
        page = PrimePage()
        panel = page.filter_panel
        page.load_filter_options(FilterOptionResult(['LI-01'], [2,12], ['9999','3212'], ['T1','T2'], ['ABCDE']))
        self.assertEqual(panel.scrap_code_list.item(1).text(), '3212')
        self.assertEqual(panel._get_selected_scrap_codes(), [])
        self.assertEqual(panel._get_selected_tiers(), ['T1','T2'])
        panel.from_date_edit.setDate(QDate(2026,9,15))
        panel.to_date_edit.setDate(QDate(2026,9,13))
        self.assertLessEqual(panel.from_date_edit.date(), panel.to_date_edit.date())
        panel.eqp_combo.setCurrentIndex(1)
        panel.slot_combo.setCurrentIndex(2)
        panel.scrap_code_list.item(0).setCheckState(Qt.Checked)
        panel.tier_list.item(1).setCheckState(Qt.Unchecked)
        events=[]
        page.filter_applied.connect(events.append)
        panel.apply_filter_button.click()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].slot, 12)
        self.assertEqual(events[0].eqp, 'LI-01')
        self.assertEqual(events[0].tiers, ['T2'])
        self.assertEqual(events[0].models, ['ABCDE'])
        self.assertEqual(events[0].scrap_codes, ['3212','9999'])
        self.assertIs(page.current_criteria, events[0])
        panel.model_list.item(0).setCheckState(Qt.Unchecked)
        self.assertEqual(panel._get_selected_models(), [])
        page.set_import_enabled(False)
        self.assertFalse(panel.apply_filter_button.isEnabled())
        page.deleteLater()


if __name__ == '__main__':
    unittest.main()
