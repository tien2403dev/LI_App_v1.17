"""Regression tests cho nguồn log Interface/TCP; chỉ sử dụng database tạm."""
import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from threading import Event
from unittest.mock import patch

from domain.prime import ImportCancelled, ValidationError
from services.prime_log_reader import LiPrimeLogReader
from services.prime_import_service import PrimeImportService


def log(serial='SN1', result='PASS', time='[12:34:56]', **changes):
    fields = dict(FUNCTION='SLOT_END', EQPID='AI-H902', LOTID='LOT1',
                  PARTNO='ABCDE-PART', SLOT='1', TESTRESULT=result,
                  SCRAP_CODE='0', TEST_COUNT='2', SERIAL=serial, P_SERIAL='IGNORED')
    fields.update(changes)
    return time + ' ' + ' '.join(f'{k}={v}' for k, v in fields.items()) + '\n'


class TcpImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'Interface'
        self.root.mkdir()
        self.db = self.base / 'li.db'
        self.reader = LiPrimeLogReader()

    def write(self, relative, content=None, encoding='utf-8'):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(log() if content is None else content, encoding=encoding)
        return path

    def rows(self):
        with sqlite3.connect(self.db) as conn:
            return conn.execute('SELECT DATE,TIME,EQP,MODEL,SERIAL,QTY,RESULT FROM prime_data ORDER BY DATE,SERIAL').fetchall()

    def test_recursive_dates_suffix_and_missing_machine(self):
        a = self.write('AI-H902/TCP/2026-09/20260916_TCP.txt')
        b = self.write('AI-H903/extra/deeper/TCP/20260916_tcp')
        c = self.write('AI-H904/20260917_run_TCP.TXT')
        for name in ('AI-H902/20260915_TCP.txt', 'AI-H902/20260916_UDP.txt',
                     'AI-H902/20260916_TCP_backup.txt', 'AI-H902/20260230_TCP.txt'):
            self.write(name)
        (self.root / 'AI-H905').mkdir()
        self.assertEqual(self.reader.discover(self.root, ('20260916',)), sorted([a, b]))
        self.assertEqual(self.reader.discover(self.root, ('20260916','20260917')), sorted([a,b,c]))

    def test_all_twelve_columns_date_time_qty_model(self):
        path = self.write('AI-H902/20260916_TCP.txt', log(time='[2020-01-01 12:34:56.789]', QTY='99', MODEL='WRONG'))
        self.assertEqual(list(self.reader.read_file(path))[0].values(),
                         ('20260916','12:34:56','AI-H902','ABCDE-PART','LOT1',1,'PASS',None,2,'SN1',1,'ABCDE'))

    def test_aliases_and_fail_scrap(self):
        text = '[01:02:03] function=slot_end EQP_ID=M LOT_ID=L PART_NO=ABCDE-X SLOT_NO=48 TEST_RESULT=fail SCRAP=4541 COUNT=3 SERIAL_NO=S P_SERIAL_NO=P\n'
        row = list(self.reader.parse_text(text, '20260916'))[0]
        self.assertEqual((row.EQP,row.LOTNO,row.SLOT,row.RESULT,row.SCRAPCODE,row.TEST_COUNT,row.SERIAL), ('M','L',48,'FAIL','4541',3,'S'))

    def test_ignore_non_end_and_null_serial(self):
        text = log(FUNCTION='SLOT_START') + log(FUNCTION='SLOT_END_ACK') + log(serial='NULL') + log()
        self.assertEqual(len(list(self.reader.parse_text(text,'20260916'))),1)

    def test_tcp_count_is_preserved(self):
        for raw in ("0", "1", "2", "9223372036854775807"):
            row = list(self.reader.parse_text(log(TEST_COUNT=raw), '20260916'))[0]
            self.assertEqual(row.TEST_COUNT, int(raw))

    def test_lot_subtrees_are_not_visited(self):
        import os
        keep = self.write('A/TCP/20260916_TCP.txt')
        keep2 = self.write('A/LOT_EXTRA/20260916_TCP.txt')
        self.write('A/LOT/deeper/20260916_TCP.txt')
        self.write('B/deep/lot/20260916_TCP.txt')
        real_scandir = os.scandir
        visited = []
        def scandir(path):
            visited.append(Path(path))
            self.assertNotEqual(Path(path).name.upper(), 'LOT')
            return real_scandir(path)
        with patch('os.scandir', side_effect=scandir):
            self.assertEqual(self.reader.discover(self.root, ('20260916',)), sorted([keep, keep2]))

    def test_encodings(self):
        for encoding in ('utf-8-sig','utf-16','cp949'):
            path = self.write(f'{encoding}/20260916_TCP.txt', '# 한글\n'+log(), encoding)
            self.assertEqual(len(list(self.reader.read_file(path))),1)

    def test_invalid_required_values_have_file_and_line(self):
        for change in ({'SLOT':'49'},{'TEST_COUNT':'-1'},{'TESTRESULT':'UNKNOWN'},{'PARTNO':'ABC'},{'EQPID':'NULL'}):
            path=self.write('20260916_TCP.txt', '\n'+log(**change))
            with self.assertRaisesRegex(ValidationError, '20260916_TCP.txt: Dòng 2:'):
                list(self.reader.read_file(path))

    def test_replace_selected_date_keep_other_dates_and_failure_rollback(self):
        p=self.write('A/deep/20260916_TCP.txt')
        self.write('B/20260917_TCP.txt', log(serial='NEXT'))
        service=PrimeImportService(self.db)
        result=service.import_folder(self.root,('20260916','20260917'))
        self.assertEqual((result.file_count,result.inserted), (2,2))
        p.write_text(log(serial='NEW', result='FAIL', SCRAP_CODE='4541'))
        service.import_folder(self.root,'20260916')
        self.assertEqual([r[4] for r in self.rows()],['NEW','NEXT'])
        before=self.rows()
        p.write_text(log(serial='GOOD')+log(SLOT='99'))
        with self.assertRaises(ValidationError):
            service.import_folder(self.root,'20260916')
        self.assertEqual(self.rows(),before)
        p.write_text('FUNCTION=SLOT_START\n')
        with self.assertRaises(ValidationError):
            service.import_folder(self.root,'20260916')
        self.assertEqual(self.rows(),before)

    def test_no_date_preserves_existing_data(self):
        self.write('20260916_TCP.txt')
        service=PrimeImportService(self.db)
        service.import_folder(self.root,'20260916')
        before=self.rows()
        with self.assertRaises(ValidationError):
            service.import_folder(self.root,'20260918')
        self.assertEqual(self.rows(),before)

    def test_changed_source_keeps_read_snapshot(self):
        p=self.write('20260916_TCP.txt')
        def progress(_):
            p.write_text(log() + log(serial='NEW'))
        self.reader.stage_folder(self.root,('20260916',),self.base/'stage.db',progress)
        with sqlite3.connect(self.base/'stage.db') as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM staging_prime_data').fetchone()[0], 1)

    def test_cancel(self):
        self.write('20260916_TCP.txt')
        cancel=Event(); cancel.set()
        with self.assertRaises(ImportCancelled):
            self.reader.stage_folder(self.root,('20260916',),self.base/'stage.db',lambda _:None,cancel)

    def test_auto_today_reimport_and_skip(self):
        import auto_import_today_main as today
        from database.schema import initialize_database
        from repositories.auto_import_scheduler_repository import AutoImportSchedulerRepository
        initialize_database(self.db)
        AutoImportSchedulerRepository(self.db).save_config(True,'00:00',str(self.root))
        day=datetime.now().strftime('%Y%m%d')
        p=self.write(f'A/TCP/deep/{day}_TCP.txt')
        with patch.object(today,'append_auto_import_log') as output:
            self.assertEqual(today.run_auto_import_today(self.db),0)
            p.write_text(log(serial='NEW'))
            self.assertEqual(today.run_auto_import_today(self.db),0)
            self.assertEqual(self.rows()[0][4],'NEW')
            before=self.rows()
            p.unlink()
            self.assertEqual(today.run_auto_import_today(self.db),0)
            self.assertEqual(self.rows(),before)
            self.assertEqual(output.call_args.args[0],'SKIPPED')

    def test_access_error_not_silently_skipped(self):
        def denied(*args, **kwargs):
            kwargs['onerror'](PermissionError('folder denied'))
            return iter(())
        with patch('services.prime_log_reader.os.walk',side_effect=denied):
            with self.assertRaisesRegex(ValidationError,'folder denied'):
                self.reader.discover(self.root,('20260916',))


if __name__ == '__main__':
    unittest.main()
