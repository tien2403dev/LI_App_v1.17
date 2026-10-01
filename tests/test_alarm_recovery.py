"""Kiểm thử quy tắc mixed Scrap code, cổng 6/10 và migration DB cũ."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from tests import test_alarm as helpers
from database.connection import connection
from database.schema import initialize_database
from repositories.machine_slot_yield_repository import MachineSlotYieldRepository
from repositories.alarm_history_repository import AlarmHistoryRepository
from repositories.mail_template_repository import MailTemplateRepository
from services.alarm_builder import build_slot_alarm
from services.mail_content_builder import MailContentBuilder

event = helpers.event

def build(rows, same=999, mixed=999, t15=70, t30=75):
    return build_slot_alarm(sorted(rows, key=lambda r:(r['DATE'],r['TIME'],r['id']), reverse=True),
        '20260915', dict(continuous_fail_count=same, different_scrap_fail_count=mixed,
                        target_15=t15, target_30=t30))

class RecoveryRulesTests(unittest.TestCase):
    def test_exact_recovery_boundaries(self):
        for passes in (5, 6, 9, 10):
            with self.subTest(passes=passes):
                alarm = build([event(i, 'PASS' if i > 30-passes else 'FAIL') for i in range(1,31)])
                if passes == 10:
                    self.assertIsNone(alarm)
                else:
                    self.assertEqual(alarm['yield_15'] is None, passes >= 6)
                    self.assertIsNotNone(alarm['yield_30'])

    def test_one_recent_fail_enables_both_rules(self):
        rows = [event(i, 'PASS' if 21<=i<=29 else 'FAIL') for i in range(1,31)]
        alarm = build(rows)
        self.assertIsNotNone(alarm['yield_15'])
        self.assertIsNotNone(alarm['yield_30'])

    def test_gate_uses_slot_across_models_and_days(self):
        # Latest 10 records cross midnight and are not grouped by Model.
        rows = [event(i,date='20260914') for i in range(1,31)]
        rows += [event(i,'PASS', model='BBBBB',date='20260914') for i in range(31,40)]
        rows += [event(40,'PASS')]
        self.assertIsNone(build(rows))

    def test_historical_healthy_prefix_does_not_suppress_recent_failure(self):
        rows = [event(i, 'PASS' if i<=10 else 'FAIL') for i in range(1,31)]
        self.assertIsNotNone(build(rows)['yield_30'])

    def test_recovery_keeps_same_scrap_alarm(self):
        rows = [event(i,'PASS' if i>30 else 'FAIL') for i in range(1,41)]
        alarm = build(rows,same=3)
        self.assertIn('1',json.loads(alarm['evidence_json']))
        self.assertIsNone(alarm['yield_15'])
        self.assertIsNone(alarm['yield_30'])

    def test_mixed_accepts_repeated_codes_and_preserves_test_count(self):
        rows = [event(i, scrap='A' if i<3 else 'B') for i in range(1,4)]
        rows[0]['TEST_COUNT']=0
        alarm=build(rows,mixed=3)
        run=json.loads(alarm['evidence_json'])['different_scrap'][0]
        self.assertEqual([r['id'] for r in run['tests']],[3,2,1])
        self.assertEqual(run['tests'][-1]['TEST_COUNT'],0)
        self.assertEqual(alarm['different_scrap_fail_count_used'],3)

    def test_mixed_breaks_at_pass_model_or_missing_scrap(self):
        for middle in (event(2,'PASS'), event(2,model='BBBBB'), event(2,scrap=None)):
            self.assertIsNone(build([event(1,scrap='A'),middle,event(3,scrap='B')],mixed=3))
        self.assertIsNone(build([event(i) for i in range(1,4)],mixed=3))
        self.assertIsNone(build([event(1,scrap='A'),event(2,scrap='B')],mixed=3))

    def test_mixed_cross_day_and_latest_qualifying_window(self):
        rows=[event(i,scrap='A' if i<=4 else 'B',date='20260914' if i<=4 else '20260915') for i in range(1,9)]
        alarm=build(rows,mixed=3)
        run=json.loads(alarm['evidence_json'])['different_scrap'][0]
        self.assertEqual([r['id'] for r in run['tests']],[6,5,4])
        self.assertEqual(run['end'],'2026-09-15 00:00:06')

    def test_old_only_mixed_run_ignored(self):
        rows=[event(i,scrap=str(i),date='20260914') for i in range(1,5)]+[event(5,'PASS')]
        self.assertIsNone(build(rows,mixed=3))

    def test_mixed_and_same_can_coexist(self):
        rows=[event(i,scrap='A' if i<=3 else 'B') for i in range(1,7)]
        evidence=json.loads(build(rows,same=3,mixed=4)['evidence_json'])
        self.assertIn('1',evidence)
        self.assertIn('different_scrap',evidence)

class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.case=helpers.AlarmImportTests()
        self.case.setUp()
        self.db=self.case.db
    def tearDown(self):
        self.case.tearDown()

    def test_migration_existing_db_and_round_trip(self):
        self.case.import_rows([event(i) for i in range(1,4)])
        before=self.case.alarms()[0]
        with connection(self.db) as conn:
            conn.execute('ALTER TABLE machine_slot_yield_config DROP COLUMN different_scrap_fail_count')
            conn.execute('ALTER TABLE slot_fail_alarm DROP COLUMN different_scrap_fail_count_used')
        initialize_database(self.db)
        repository=MachineSlotYieldRepository(self.db)
        self.assertEqual(repository.get_config().different_scrap_fail_count,3)
        repository.save_config('logs',50.1,70,1000,7)
        initialize_database(self.db)
        self.assertEqual(repository.get_config().different_scrap_fail_count,7)
        repository.save_config('logs',50.1,70,1000)
        self.assertEqual(repository.get_config().different_scrap_fail_count,7)
        after=self.case.alarms()[0]
        for key in before:
            if key!='different_scrap_fail_count_used': self.assertEqual(before[key],after[key])
        with self.assertRaises(ValueError): repository.save_config('',70,75,3,0)
        with connection(self.db) as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute('UPDATE machine_slot_yield_config SET different_scrap_fail_count=0')

    def test_import_history_mail_and_tracking(self):
        self.case.config.save_config('',0,0,999,3)
        rows=[event(i,scrap='A' if i<3 else 'B') for i in range(1,4)]
        self.case.import_rows(rows)
        alarm=self.case.alarms()[0]
        history=AlarmHistoryRepository(self.db).load(alarm)
        self.assertEqual(len(history['groups']),1)
        self.assertEqual(history['groups'][0]['error'],'')
        self.assertEqual(len(history['groups'][0]['tests']),3)
        self.assertIn('khác Scrap code',history['groups'][0]['label'])
        alarm,_=self.case.repository.update_tracking(alarm,'comment','Giữ lại')
        self.case.import_rows(rows)
        updated=self.case.alarms()[0]
        self.assertEqual(updated['comment'],'Giữ lại')
        self.assertEqual(updated['id'],alarm['id'])
        # Mail uses the saved snapshot and identifies the new rule.
        repository=MailTemplateRepository(self.db)
        alarms=repository.get_alarm_previews(['20260915'])
        html=MailContentBuilder.build_alarm_body_html(['20260915'],alarms)
        self.assertIn('khác Scrap code',html)
        self.case.config.save_config('',0,0,999,4)
        self.case.import_rows(rows)
        self.assertEqual(self.case.alarms(),[])

    def test_reimport_recovery_removes_yield_alarm(self):
        self.case.config.save_config('',70,75,999,999)
        self.case.import_rows([event(i) for i in range(1,31)])
        self.assertEqual(len(self.case.alarms()),1)
        self.case.import_rows([event(i,'PASS' if i>20 else 'FAIL') for i in range(1,31)])
        self.assertEqual(self.case.alarms(),[])

if __name__=='__main__': unittest.main()
