import tempfile
import unittest
from pathlib import Path
from database.connection import connection
from database.schema import initialize_database
from repositories.slot_summary_repository import SlotSummaryRepository


class SlotSummaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / 'li.db'
        initialize_database(self.db)
        self.repo = SlotSummaryRepository(self.db)
        with connection(self.db) as conn:
            rows = [
                ('20260911','LI-01',1,'PASS',1,'T1','ABCDE'),
                ('20260912','LI-01',1,'FAIL',1,'T1','ABCDE'),
                ('20260913','LI-01',1,'PASS',1,'T1','ABCDE'),
                ('20260912','LI-01',1,'FAIL',2,'T1','ABCDE'),
                ('20260912','LI-01',1,'PASS',3,'T1','ABCDE'),
                ('20260912','LI-01',48,'FAIL',1,'T1','ABCDE'),
                ('20260912','LI-01',2,'FAIL',5,'T1','ABCDE'),
                ('20260910','LI-01',1,'FAIL',1,'T1','ABCDE'),
                ('20260914','LI-01',1,'FAIL',1,'T1','ABCDE'),
                ('20260912','LI-02',1,'FAIL',1,'T1','ABCDE'),
                ('20260912','LI-01',1,'FAIL',1,'T2','ABCDE'),
                ('20260912','LI-01',1,'FAIL',1,'T1','XXXXX'),
            ]
            for date, eqp, slot, result, count, tier, model in rows:
                conn.execute('''INSERT INTO prime_data
                    (DATE,TIME,EQP,PARTNO,LOTNO,SLOT,RESULT,TEST_COUNT,SERIAL,QTY,MODEL,TIER)
                    VALUES (?,'08:00:00',?,?,'LOT',?,?,?,'SERIAL',1,?,?)''',
                    (date,eqp,model+'PRODUCT',slot,result,count-1,model,tier))

    def tearDown(self):
        self.temp.cleanup()

    def test_filters_first_test_and_all_48_slots(self):
        result = self.repo.load('20260911','20260913',['T1'],['ABCDE'],'LI-01')
        self.assertEqual([r.slot for r in result.rows],list(range(1,49)))
        row = result.rows[0]
        self.assertEqual((row.in_qty,row.pass_qty,row.fail_qty),(3,2,1))
        self.assertAlmostEqual(row.yield_percent,200/3)
        self.assertAlmostEqual(row.fail_ppm,1_000_000/3)
        self.assertEqual(result.rows[47].fail_ppm,1_000_000)
        self.assertEqual(result.rows[47].yield_percent,0)
        self.assertIsNone(result.rows[1].yield_percent)
        self.assertIsNone(result.rows[1].fail_ppm)
        self.assertEqual(sum(r.in_qty for r in result.rows),4)

    def test_empty_filters_and_no_eqp(self):
        self.assertEqual(self.repo.load('20260911','20260913',['T1'],['ABCDE'],None).rows,[])
        for tiers, models in [([],['ABCDE']),(['T1'],[])]:
            self.assertTrue(all(r.in_qty == 0 for r in self.repo.load('20260911','20260913',tiers,models,'LI-01').rows))

    def test_existing_db_index_and_query_plan(self):
        with connection(self.db) as conn:
            before = [tuple(r) for r in conn.execute('SELECT * FROM prime_data')]
            conn.execute('DROP INDEX idx_prime_first_slot')
        initialize_database(self.db)
        initialize_database(self.db)
        with connection(self.db) as conn:
            self.assertEqual(before,[tuple(r) for r in conn.execute('SELECT * FROM prime_data')])
            plan = conn.execute('''EXPLAIN QUERY PLAN SELECT SLOT,SUM(QTY),
                SUM(CASE WHEN RESULT='PASS' THEN QTY ELSE 0 END) FROM prime_data
                WHERE EQP='LI-01' AND DATE BETWEEN '20260911' AND '20260913'
                AND TEST_COUNT=0 AND TIER IN ('T1') AND MODEL IN ('ABCDE') GROUP BY SLOT ORDER BY SLOT''').fetchall()
            self.assertTrue(any('idx_prime_first_slot' in r[3] for r in plan),str([tuple(r) for r in plan]))
