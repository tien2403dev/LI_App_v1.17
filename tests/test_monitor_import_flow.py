import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
from tests import test_alarm as helpers
from database.connection import connection
from repositories.alarm_repository import AlarmRepository
from workers.alarm_worker import AlarmWorker


class MonitorImportTests(unittest.TestCase):
    setUp = helpers.AlarmImportTests.setUp
    tearDown = helpers.AlarmImportTests.tearDown
    import_rows = helpers.AlarmImportTests.import_rows

    def seed(self):
        self.today = datetime.now().strftime('%Y%m%d')
        self.days = [(datetime.now()-timedelta(days=i)).strftime('%Y%m%d') for i in (5,4,3,2,1)]
        with connection(self.db) as c:
            c.execute("""INSERT INTO slot_fail_alarm
                (alarm_date,eqp,slot,fail_comment,start_datetime,end_datetime,
                 target_15,target_30,continuous_fail_count_used,status,date_complete,
                 created_at,updated_at,comment)
                VALUES (?,'AI-H903',1,'x','','',90,90,3,'Đã hoàn thành',?,'','','keep')""",
                (self.days[0], datetime.strptime(self.days[0],'%Y%m%d').isoformat()))
        self.alarm_id = self.row()['id']

    def row(self):
        return self.repository.load(self.days[0], self.days[0])[0]

    def values(self):
        r=self.row()
        return tuple(r[f'monitor_day{i}'] for i in (1,2,3))

    def test_past_import_reimport_noop_and_all_counts(self):
        self.seed()
        self.import_rows([helpers.event(1,'PASS',date=self.days[1])])
        self.assertEqual(self.values(),('PASS','',''))
        version=self.row()['row_version']
        self.import_rows([helpers.event(1,'PASS',date=self.days[1])])
        self.assertEqual(self.row()['row_version'],version)
        self.import_rows([helpers.event(1,'PASS',date=self.days[1]),helpers.event(2,'FAIL',date=self.days[1])])
        self.assertEqual(self.values(),('FAIL','',''))
        self.assertEqual(self.row()['comment'],'keep')
        self.import_rows([helpers.event(1,'PASS',date=self.days[1])])
        self.assertEqual(self.values(),('PASS','',''))

    def test_removed_slot_reorders_days(self):
        self.seed()
        self.import_rows([helpers.event(i,'PASS',date=day) for i,day in enumerate(self.days[1:],1)])
        self.assertEqual(self.values(),('PASS','PASS','PASS'))
        self.import_rows([helpers.event(1,'FAIL',date=self.days[1],slot=2)])
        self.assertEqual(self.values(),('PASS','PASS','PASS'))
        self.import_rows([helpers.event(1,'FAIL',date=self.days[4])])
        self.assertEqual(self.values(),('PASS','PASS','FAIL'))

    def test_today_neither_updates_nor_enters_past_calculation(self):
        self.seed()
        before=self.row()
        self.import_rows([helpers.event(1,'FAIL',date=self.today)])
        self.assertEqual(self.row(),before)
        self.import_rows([helpers.event(1,'PASS',date=self.days[-1])])
        self.assertEqual(self.values(),('PASS','',''))
        before=self.row()
        self.import_rows([helpers.event(1,'PASS',date=self.today)])
        self.assertEqual(self.row(),before)

    def test_search_only_reads_under_writer_lock(self):
        self.seed()
        before=self.row()
        with connection(self.db) as c:
            c.execute('BEGIN IMMEDIATE')
            worker=AlarmWorker(self.db,(self.days[0],self.today))
            results, errors=[],[]
            worker.succeeded.connect(results.append)
            worker.failed.connect(errors.append)
            with patch.object(AlarmRepository,'sync_import_monitors',side_effect=AssertionError('read only')):
                worker.run()
            self.assertEqual(errors,[])
            self.assertEqual(results[0][0]['id'],before['id'])
            c.rollback()
        self.assertEqual(self.row(),before)

    def test_monitor_error_rolls_back_prime_and_monitor(self):
        self.seed()
        self.import_rows([helpers.event(1,'PASS',date=self.days[1])])
        before=self.row()
        sync=AlarmRepository.sync_import_monitors
        def fail(*args,**kwargs):
            sync(*args,**kwargs)
            raise RuntimeError('fail before commit')
        with patch.object(AlarmRepository,'sync_import_monitors',side_effect=fail):
            with self.assertRaisesRegex(RuntimeError,'fail before commit'):
                self.import_rows([helpers.event(1,'FAIL',date=self.days[1])])
        self.assertEqual(self.row(),before)
        with connection(self.db) as c:
            self.assertEqual(c.execute('SELECT RESULT FROM prime_data').fetchone()[0],'PASS')

    def test_unrelated_slots_unchanged(self):
        self.seed()
        before=self.row()
        self.import_rows([helpers.event(1,'PASS',date=self.days[1],slot=2)])
        self.assertEqual(self.row(),before)

    def test_scheduler_yesterday_manual_reimport_and_today(self):
        import auto_import_main as yesterday
        import auto_import_today_main as today
        from repositories.auto_import_scheduler_repository import AutoImportSchedulerRepository
        from services.prime_import_service import PrimeImportService
        from tests.test_tcp_import import log
        self.seed()
        root=self.base/'logs'
        root.mkdir()
        past=root/f'{self.days[-1]}_TCP.txt'
        past.write_text(log(EQPID='AI-H903'),encoding='utf-8')
        current=root/f'{self.today}_TCP.txt'
        current.write_text(log(EQPID='AI-H903',result='FAIL'),encoding='utf-8')
        scheduler=AutoImportSchedulerRepository(self.db)
        scheduler.save_config(enabled=True,import_time='00:00',log_folder=str(root))
        with patch.object(yesterday,'append_auto_import_log'),patch.object(today,'append_auto_import_log'):
            self.assertEqual(yesterday.run_auto_import(self.db),0)
            self.assertEqual(self.values(),('PASS','',''))
            self.assertEqual(scheduler.get_config().last_import_date,self.days[-1])
            snapshot=self.row()
            self.assertEqual(today.run_auto_import_today(self.db),0)
            self.assertEqual(self.row(),snapshot)
            current.write_text(log(EQPID='AI-H903',serial='REPLACED'),encoding='utf-8')
            self.assertEqual(today.run_auto_import_today(self.db),0)
            self.assertEqual(self.row(),snapshot)
            past.write_text(log(EQPID='AI-H903',result='FAIL'),encoding='utf-8')
            PrimeImportService(self.db).import_folder(root,(self.days[-1],))
            self.assertEqual(self.values(),('FAIL','',''))
            with connection(self.db) as conn:
                self.assertEqual(conn.execute('SELECT SERIAL FROM prime_data WHERE DATE=?',(self.today,)).fetchone()[0],'REPLACED')
