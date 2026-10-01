"""Kiểm thử bằng chứng, tương thích alarm cũ, index và click UI."""
import json
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import tempfile
import unittest
from pathlib import Path
from database.connection import connection
from database.schema import initialize_database
from domain.prime import COLUMNS
from repositories.alarm_repository import AlarmRepository
from repositories.alarm_history_repository import AlarmHistoryRepository, LEGACY_SQL
from tests.test_alarm import event


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / 'test.db'
        initialize_database(self.db)
        self.repo = AlarmHistoryRepository(self.db)

    def seed(self, rows, threshold=3, target=75):
        with connection(self.db) as conn:
            conn.execute('UPDATE machine_slot_yield_config SET continuous_fail_count=?,target_15=?,target_30=? WHERE id=1',
                         (threshold, target, target))
            conn.execute('BEGIN')
            conn.executemany(f"INSERT INTO prime_data({','.join(COLUMNS)}) VALUES({','.join('?' for _ in COLUMNS)})",
                             [tuple(row[col] for col in COLUMNS) for row in rows])
            AlarmRepository.sync_import_dates(conn, ['20260915'], lambda _: None)
            conn.commit()
        return AlarmRepository(self.db).load('20260915', '20260915')[0]

    def legacy(self, alarm):
        evidence = json.loads(alarm['evidence_json'])
        for run in evidence.get('1', []):
            run.pop('tests', None)
        for key in ('15', '30'):
            for test in evidence.get(key, {}).get('tests', []):
                test.pop('id', None)
                test.pop('QTY', None)
        with connection(self.db) as conn:
            conn.execute('UPDATE slot_fail_alarm SET evidence_json=? WHERE id=?',
                         (json.dumps(evidence), alarm['id']))

    def test_exact_three_cross_day_and_original_test_count_zero(self):
        rows = [event(1, date='20260914'), event(2), event(3)]
        for row in rows:
            row['TEST_COUNT'] = 0
        alarm = self.seed(rows)
        group = self.repo.load(alarm)['groups'][0]
        self.assertEqual([row['TIME'] for row in group['tests']], ['00:00:03','00:00:02','00:00:01'])
        self.assertEqual([row['TEST_COUNT'] for row in group['tests']], [0,0,0])
        self.assertEqual([row['QTY'] for row in group['tests']], [1,1,1])
        self.assertFalse(group['error'])

    def test_long_run_bounded_snapshot_and_multiple_rules(self):
        alarm = self.seed([event(i) for i in range(1,36)])
        groups = self.repo.load(alarm)['groups']
        self.assertEqual([len(group['tests']) for group in groups], [3,15,30])
        self.assertEqual([row['TIME'] for row in groups[0]['tests']], ['00:00:35','00:00:34','00:00:33'])
        self.assertIn('35', groups[0]['note'])
        self.assertEqual(alarm['start_datetime'], '2026-09-15 00:00:01')

    def test_yield_pass_fail_model_and_no_future(self):
        rows = [event(i, 'PASS' if i % 3 == 0 else 'FAIL', date='20260914') for i in range(1,30)]
        rows += [event(30), event(31, 'PASS', model='BBBBB'), event(32, date='20260916')]
        alarm = self.seed(rows, threshold=999)
        groups = self.repo.load(alarm)['groups']
        self.assertEqual([len(group['tests']) for group in groups], [15,30])
        for group in groups:
            self.assertEqual({r['MODEL'] for r in group['tests']}, {'AAAAA'})
            self.assertEqual({r['RESULT'] for r in group['tests']}, {'PASS','FAIL'})
            self.assertNotIn('20260916', {r['DATE'] for r in group['tests']})

    def test_tied_timestamp_stable_by_id(self):
        rows = [event(i) for i in range(1,4)]
        for row in rows:
            row['TIME'] = '01:00:00'
        alarm = self.seed(rows)
        tests = self.repo.load(alarm)['groups'][0]['tests']
        self.assertEqual([r['SERIAL'] for r in tests], ['SN3','SN2','SN1'])

    def test_snapshot_survives_prime_changes(self):
        alarm = self.seed([event(i) for i in range(1,4)])
        before = self.repo.load(alarm)
        with connection(self.db) as conn:
            conn.execute('DELETE FROM prime_data')
        self.assertEqual(self.repo.load(alarm), before)

    def test_version_and_deleted_alarm(self):
        alarm = self.seed([event(i) for i in range(1,4)])
        with connection(self.db) as conn:
            conn.execute('UPDATE slot_fail_alarm SET row_version=row_version+1')
        with self.assertRaisesRegex(ValueError, 'thay đổi'):
            self.repo.load(alarm)
        with connection(self.db) as conn:
            conn.execute('DELETE FROM slot_fail_alarm')
        with self.assertRaisesRegex(ValueError, 'đã bị xóa'):
            self.repo.load(alarm)

    def test_legacy_all_rules_and_missing_prime(self):
        alarm = self.seed([event(i) for i in range(1,31)])
        self.legacy(alarm)
        groups = self.repo.load(alarm)['groups']
        self.assertEqual([len(g['tests']) for g in groups], [3,15,30])
        self.assertTrue(all(g['note'] for g in groups))
        with connection(self.db) as conn:
            conn.execute('DELETE FROM prime_data')
        self.assertTrue(all(g['error'] and not g['tests'] for g in self.repo.load(alarm)['groups']))

    def test_list_omits_evidence_only_when_requested(self):
        self.seed([event(i) for i in range(1,4)])
        repo = AlarmRepository(self.db)
        self.assertNotIn('evidence_json', repo.load('20260915','20260915', include_evidence=False)[0])
        self.assertIn('evidence_json', repo.load('20260915','20260915')[0])

    def test_index_plans_and_repeat_init(self):
        alarm = self.seed([event(i) for i in range(1,4)])
        initialize_database(self.db)
        with connection(self.db) as conn:
            plan = ' '.join(r[3] for r in conn.execute('EXPLAIN QUERY PLAN '+LEGACY_SQL,
                ('AI-H903',1,'20260914','00:00:00','20260915','23:59:59',3)))
            self.assertIn('idx_prime_slot_time', plan)
            self.assertNotIn('TEMP B-TREE', plan)
            plan = ' '.join(r[3] for r in conn.execute('EXPLAIN QUERY PLAN SELECT * FROM slot_fail_alarm WHERE id=?',(alarm['id'],)))
            self.assertIn('INTEGER PRIMARY KEY', plan)
            plan = ' '.join(r[3] for r in conn.execute('EXPLAIN QUERY PLAN SELECT * FROM slot_fail_alarm WHERE alarm_date BETWEEN ? AND ? ORDER BY alarm_date DESC,end_datetime DESC,eqp,slot',('20260901','20260930')))
            self.assertIn('idx_alarm_history_list', plan)
            self.assertNotIn('TEMP B-TREE', plan)


from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from tests import test_alarm_gui as gui
from tests.test_alarm_gui import APP, wait_until


class HistoryGuiTests(unittest.TestCase):
    setUp = gui.AlarmGuiTests.setUp
    tearDown = gui.AlarmGuiTests.tearDown
    open_alarm = gui.AlarmGuiTests.open_alarm

    def test_real_click_after_filter_and_edit_columns_excluded(self):
        page = self.open_alarm()
        page.apply_filter(3, {'2'}, ['1','2'])
        calls = []
        page.history_requested.connect(calls.append)
        for col in range(14,23):
            page.table.clicked.emit(page.proxy.index(0,col))
        self.assertEqual(calls, [])
        index = page.proxy.index(0,3)
        QTest.mouseClick(page.table.viewport(), Qt.LeftButton,
                         pos=page.table.visualRect(index).center())
        wait_until(lambda: not self.controller.busy)
        self.assertEqual(len(calls), 1)
        dialog = self.controller._history_dialog
        self.assertIn('SLOT: 2', dialog.windowTitle())
        self.assertNotIn('CHAMBER', dialog.windowTitle())
        self.assertEqual(dialog.model.rowCount(), 3)
        self.assertEqual(dialog.model.columnCount(), 8)
        dialog.close()
        self.assertEqual(self.errors, [])

    def test_rule_selection_and_read_only(self):
        from ui.dialogs.slot_fail_history_dialog import SlotFailHistoryDialog
        groups = [dict(label=f'Yield {size} < 75.00%',
                       tests=[event(i, 'PASS' if i % 2 else 'FAIL') for i in range(1,size+1)],
                       note='', error='') for size in (15,30)]
        dialog = SlotFailHistoryDialog(dict(eqp='AI-H903',slot=1,groups=groups),
                                       preferred_rule=30)
        self.assertEqual(dialog.model.rowCount(), 30)
        self.assertFalse(dialog.model.flags(dialog.model.index(0,0)) & Qt.ItemIsEditable)
        dialog.rule_combo.setCurrentIndex(0)
        self.assertEqual(dialog.model.rowCount(), 15)
        self.assertIn('Số dòng FAIL: 7', dialog.summary.text())
        dialog.close()

    def test_close_app_while_loading(self):
        page = self.open_alarm()
        page.table.clicked.emit(page.proxy.index(0,3))
        self.window.close()
        wait_until(lambda: not self.window.isVisible())
        self.assertFalse(self.controller.busy)
        self.assertEqual(self.errors, [])


if __name__ == '__main__':
    unittest.main()
