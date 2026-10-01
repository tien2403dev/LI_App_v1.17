import tempfile
import unittest
from pathlib import Path
from database.connection import connection
from database.schema import initialize_database
from repositories.daily_summary_repository import DailySummaryRepository


class DailySummaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / 'test.db'
        initialize_database(self.db)
        self.repo = DailySummaryRepository(self.db)
        with connection(self.db) as conn:
            for eqp, tier, model in [('LI-01','T1','ABCDE'), ('LI-02','T1','ABCDE'), ('LI-01','T2','ABCDE'), ('LI-01','T1','XXXXX')]:
                row_id = conn.execute('''INSERT INTO cum_data
                    (DATE,TIME,PRODUCT,EQPID,INQTY,OUTQTY,FAILQTY,YIELD,MODEL,TIER)
                    VALUES ('20260912','08:00:00','PRODUCT',?,10,8,999,0,?,?)''', (eqp,model,tier)).lastrowid
                conn.execute('INSERT INTO cum_scrap_detail(cum_data_id,scrap_code,qty) VALUES (?,\'3308\',2)', (row_id,))
                for result, code in [('PASS',None), ('FAIL','3308'), ('FAIL','3313'), ('FAIL',None)]:
                    conn.execute('''INSERT INTO prime_data
                        (DATE,TIME,EQP,PARTNO,LOTNO,SLOT,RESULT,SCRAPCODE,TEST_COUNT,SERIAL,QTY,MODEL,TIER)
                        VALUES ('20260912','08:00:00',?,?,'LOT',1,?,?,0,'SERIAL',1,?,?)''',
                        (eqp,model+'PRODUCT',result,code,model,tier))

    def tearDown(self):
        self.temp.cleanup()

    def test_daily_metrics_and_empty_dates(self):
        args = ('20260911','20260913','LI-01',['T1'])
        cum = self.repo.get_cum_daily_summary(*args, selected_models=['ABCDE'])
        prime = self.repo.get_prime_daily_summary(*args, selected_models=['ABCDE'])
        self.assertEqual([r.date for r in cum.rows], ['20260911','20260912','20260913'])
        c = cum.rows[1]
        self.assertEqual((c.in_qty,c.out_qty,c.fail_qty,c.fail_ppm,c.yield_percent),(10,8,2,200000,80))
        self.assertEqual(c.scrap_ppm_by_code, {'3308':200000})
        p = prime.rows[1]
        self.assertEqual((p.in_qty,p.out_qty,p.fail_qty,p.fail_ppm,p.yield_percent),(4,1,3,750000,25))
        self.assertEqual(p.scrap_ppm_by_code, {'3308':250000,'3313':250000})
        for result in [cum,prime]:
            self.assertIsNone(result.rows[0].yield_percent)
            self.assertEqual(result.rows[0].scrap_ppm_by_code,{})
            self.assertIsNone(result.rows[2].fail_ppm)

    def test_no_eqp_and_no_model(self):
        for method in [self.repo.get_cum_daily_summary,self.repo.get_prime_daily_summary]:
            self.assertEqual(method('20260911','20260913',None,['T1'],selected_models=['ABCDE']).rows, [])
            empty = method('20260911','20260913','LI-01',['T1'],selected_models=[])
            self.assertTrue(all(r.in_qty == 0 for r in empty.rows))

    def test_existing_database_gets_index_without_data_change(self):
        with connection(self.db) as conn:
            before = conn.execute('SELECT COUNT(*) FROM prime_data').fetchone()[0]
            conn.execute('DROP INDEX idx_prime_daily_fail')
        initialize_database(self.db)
        initialize_database(self.db)
        with connection(self.db) as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM prime_data').fetchone()[0], before)
            names = {row[1] for row in conn.execute('PRAGMA index_list(prime_data)')}
            self.assertIn('idx_prime_daily_fail', names)
            plan = conn.execute('''EXPLAIN QUERY PLAN SELECT DATE,SCRAPCODE,SUM(QTY) FROM prime_data
                WHERE DATE BETWEEN '20260911' AND '20260913' AND EQP='LI-01'
                AND RESULT='FAIL' AND COALESCE(SCRAPCODE,'')<>'' AND TIER IN ('T1') AND MODEL IN ('ABCDE')
                GROUP BY DATE,SCRAPCODE''').fetchall()
            self.assertTrue(any('idx_prime_daily_fail' in row[3] for row in plan), str([tuple(r) for r in plan]))

if __name__ == '__main__':
    unittest.main()
