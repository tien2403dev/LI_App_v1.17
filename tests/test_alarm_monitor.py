import tempfile
import unittest
from pathlib import Path
from database.connection import connection
from database.schema import initialize_database
from repositories.alarm_repository import AlarmRepository

class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=Path(self.tmp.name)/'test.db'
        initialize_database(self.db)
        self.repo=AlarmRepository(self.db)
        with connection(self.db) as c:
            c.execute("""INSERT INTO slot_fail_alarm
                (alarm_date,eqp,slot,fail_comment,start_datetime,end_datetime,
                target_15,target_30,continuous_fail_count_used,status,date_complete,
                created_at,updated_at,comment)
                VALUES ('20260120','AI-H903',1,'x','','',90,90,3,
                'Đã hoàn thành','2026-01-21 23:59:59','','','keep')""")
    def tearDown(self):
        self.tmp.cleanup()
    def add(self,day,result='PASS',slot=1,eqp='AI-H903',count=0,model='AAAAA'):
        with connection(self.db) as c:
            c.execute("""INSERT INTO prime_data
                (DATE,TIME,EQP,SLOT,PARTNO,LOTNO,RESULT,TEST_COUNT,SERIAL,QTY,MODEL)
                VALUES (?,'12:00:00',?,?,?,'LOT',?,?,'SN',1,?)""",
                (day,eqp,slot,model+'-PART',result,count,model))
    def row(self):
        return self.repo.load('20260120','20260120')[0]
    def values(self):
        r=self.row()
        return tuple(r[f'monitor_day{i}'] for i in (1,2,3))
    def test_gaps_isolation_all_tests_and_three_day_limit(self):
        self.add('20260121','FAIL')
        self.add('20260122')
        self.add('20260122','FAIL',slot=2)
        self.add('20260122','FAIL',eqp='AI-H904')
        self.add('20260125')
        self.add('20260125','FAIL',count=2,model='BBBBB')
        self.add('20260129')
        self.add('20260130','FAIL')
        self.repo.refresh_monitors()
        self.assertEqual(self.values(),('PASS','FAIL','PASS'))
        r=self.row()
        self.assertEqual(r['comment'],'keep')
        self.assertEqual(self.repo.refresh_monitors(),0)
        self.assertEqual(self.row()['row_version'],r['row_version'])
    def test_progress_and_reimport(self):
        self.repo.refresh_monitors()
        self.assertEqual(self.values(),('','',''))
        self.add('20260122')
        self.repo.refresh_monitors()
        self.assertEqual(self.values(),('PASS','',''))
        self.add('20260122','FAIL')
        self.add('20260125')
        self.repo.refresh_monitors()
        self.assertEqual(self.values(),('FAIL','PASS',''))
        with connection(self.db) as c:
            c.execute("DELETE FROM prime_data WHERE DATE='20260122'")
        self.repo.refresh_monitors()
        self.assertEqual(self.values(),('PASS','',''))
    def test_status_reset_and_stale_edit(self):
        old=self.row()
        self.add('20260122')
        self.repo.refresh_monitors()
        latest,conflict=self.repo.update_tracking(old,'comment','stale')
        self.assertTrue(conflict)
        latest,conflict=self.repo.update_tracking(latest,'status','Đang thực hiện')
        self.assertFalse(conflict)
        self.assertEqual(self.values(),('','',''))
        self.assertEqual(latest['date_complete'],'')
        self.assertEqual(self.repo.refresh_monitors(),0)
    def test_invalid_completion_future_and_busy(self):
        self.add('20990122')
        self.repo.refresh_monitors()
        self.assertEqual(self.values(),('','',''))
        with connection(self.db) as c:
            c.execute("UPDATE slot_fail_alarm SET date_complete='bad',monitor_day1='PASS'")
        self.repo.refresh_monitors()
        self.assertEqual(self.values(),('','',''))
        with connection(self.db) as c:
            c.execute('BEGIN IMMEDIATE')
            with self.assertRaisesRegex(ValueError,'Search'):
                self.repo.refresh_monitors()
            c.rollback()

if __name__=='__main__':
    unittest.main()
