import sqlite3
import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from threading import Event
from repositories.machine_slot_summary_repository import load_machine_slot_summary


class SummaryTests(unittest.TestCase):
    def test_counts_cutoff_history_and_alarm(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'test.db'
            with sqlite3.connect(path) as c:
                c.execute('CREATE TABLE prime_data(id INTEGER PRIMARY KEY,EQP TEXT,SLOT INTEGER,DATE TEXT,TIME TEXT,RESULT TEXT,TEST_COUNT INTEGER,QTY INTEGER)')
                c.execute('CREATE INDEX idx_prime_slot_time ON prime_data(EQP,SLOT,DATE,TIME)')
                c.execute('CREATE TABLE slot_fail_alarm(eqp TEXT,slot INTEGER,alarm_date TEXT)')
                rows = [('A',1,'20260922','12:00:00','FAIL',2,99),
                        ('A',1,'20260922','13:00:00','PASS',0,1),
                        ('A',1,'20260824','00:00:00','PASS',0,50),
                        ('A',1,'20260823','23:59:59','FAIL',1,1),
                        ('B',1,'20260101','00:00:00','PASS',0,1)]
                rows += [('C',2,'20260921',f'01:00:{i:02d}','PASS',i,1) for i in range(12)]
                c.executemany('INSERT INTO prime_data(EQP,SLOT,DATE,TIME,RESULT,TEST_COUNT,QTY) VALUES(?,?,?,?,?,?,?)', rows)
                c.executemany('INSERT INTO slot_fail_alarm VALUES(?,?,?)', [('A',1,'20260920'),('A',1,'20260921'),('B',1,'20260919')])
            result = load_machine_slot_summary(path,'20260920','20260922', Event(),datetime(2026,9,22,12,30))
            a,b,c = result['rows']
            self.assertEqual((a['total'],a['passed'],a['failed']), (2,1,1))
            self.assertEqual([r['RESULT'] for r in a['recent']], ['FAIL','PASS','FAIL'])
            self.assertEqual(a['recent'][0]['TEST_COUNT'], 2)
            self.assertTrue(a['alarm'])
            self.assertFalse(b['alarm'])
            self.assertEqual(b['total'],0)
            self.assertEqual(len(b['recent']),1)
            self.assertEqual(len(c['recent']),10)
            self.assertEqual(c['recent'][0]['TIME'],'01:00:11')
            self.assertEqual(c['recent'][-1]['TIME'],'01:00:02')
            cancel = Event(); cancel.set()
            with self.assertRaises((InterruptedError,sqlite3.OperationalError)):
                load_machine_slot_summary(path,None,None,cancel)

if __name__ == '__main__':
    unittest.main()
