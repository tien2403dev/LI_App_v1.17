import unittest
from database.connection import connection
from database.schema import initialize_database
import test_slot_summary


class SlotDailyTests(unittest.TestCase):
    def setUp(self):
        """Tạo dữ liệu có nhiều máy/slot/model/tier và nhiều test count."""
        self.fixture = test_slot_summary.SlotSummaryTests()
        self.fixture.setUp()
        self.repo, self.db = self.fixture.repo, self.fixture.db

    def tearDown(self):
        """Dọn database tạm."""
        self.fixture.tearDown()

    def test_weighted_total_and_missing_days(self):
        """Tổng yield phải có trọng số, bỏ retest và giữ ngày trống."""
        with connection(self.db) as conn:
            conn.execute("""INSERT INTO prime_data (DATE,TIME,EQP,PARTNO,LOTNO,SLOT,
                RESULT,TEST_COUNT,SERIAL,QTY,MODEL,TIER)
                SELECT DATE,TIME,EQP,PARTNO,LOTNO,SLOT,RESULT,TEST_COUNT,SERIAL,QTY,MODEL,TIER
                FROM prime_data WHERE DATE='20260911' AND EQP='LI-01'""")
        result = self.repo.load_daily('20260911','20260913',['T1'],['ABCDE'],'LI-01',1)
        self.assertEqual((result.total.in_qty, result.total.pass_qty, result.total.fail_qty), (4,3,1))
        self.assertEqual(result.total.yield_percent,75)
        self.assertNotAlmostEqual(result.total.yield_percent, sum(r.yield_percent for r in result.rows)/3)
        result = self.repo.load_daily('20260911','20260913',['T1'],['ABCDE'],'LI-01',48)
        self.assertEqual([r.in_qty for r in result.rows],[0,1,0])
        self.assertIsNone(result.rows[0].yield_percent)
        self.assertEqual(result.total.yield_percent,0)
        result = self.repo.load_daily('20260911','20260913',[],['ABCDE'],'LI-01',1)
        self.assertIsNone(result.total.yield_percent)
        self.assertIsNone(self.repo.load_daily('20260911','20260913',['T1'],['ABCDE'],'LI-01',None))

    def test_existing_database_and_plan(self):
        """Index bổ sung an toàn và được dùng cho EQP/SLOT/DATE."""
        with connection(self.db) as conn:
            before = [tuple(r) for r in conn.execute('SELECT * FROM prime_data')]
            conn.execute('DROP INDEX idx_prime_first_slot_daily')
        initialize_database(self.db)
        initialize_database(self.db)
        with connection(self.db) as conn:
            self.assertEqual(before,[tuple(r) for r in conn.execute('SELECT * FROM prime_data')])
            plan = conn.execute("""EXPLAIN QUERY PLAN SELECT DATE,SUM(QTY),
                SUM(CASE WHEN RESULT='PASS' THEN QTY ELSE 0 END) FROM prime_data
                WHERE EQP=? AND SLOT=? AND DATE BETWEEN ? AND ? AND TEST_COUNT=0
                AND TIER IN (?) AND MODEL IN (?) GROUP BY DATE ORDER BY DATE""",
                ['LI-01',1,'20260911','20260913','T1','ABCDE']).fetchall()
            detail = ' '.join(r[3] for r in plan)
            self.assertIn('idx_prime_first_slot_daily', detail)
            self.assertNotIn('TEMP B-TREE', detail)
