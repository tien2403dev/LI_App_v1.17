"""Regression coverage: reader contention, snapshots, cleanup and SQL privacy."""
import json
import sqlite3
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from database.connection import create_connection
from database.diagnostics import log_path
from database.schema import initialize_database
from database.read_snapshot import machine_export_snapshot
from domain.prime import ValidationError
from repositories.import_lock_repository import ImportLockRepository, ImportLockHeartbeat
from repositories.mail_template_repository import MailTemplateRepository
from services.prime_import_service import PrimeImportService
from services.prime_log_reader import LiPrimeLogReader
from tests.test_tcp_import import log


class LockSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = self.root/'li.db'
        initialize_database(self.db)
        self.file = self.root/'20260924_TCP.txt'

    def test_reader_contention_waits_and_then_succeeds(self):
        ready = threading.Event()
        def read():
            conn = sqlite3.connect(self.db)
            conn.execute('BEGIN')
            conn.execute('SELECT COUNT(*) FROM prime_data').fetchone()
            ready.set()
            time.sleep(0.7)
            conn.close()
        worker = threading.Thread(target=read)
        worker.start()
        self.assertTrue(ready.wait(3))
        locks = ImportLockRepository(self.db)
        start = time.monotonic()
        batch = locks.acquire('reader test')
        self.assertGreater(time.monotonic()-start, 0.25)
        worker.join()
        locks.release(batch)

    def test_partial_tail_waits_for_next_import_utf8_and_utf16(self):
        for encoding in ('utf-8', 'utf-16'):
            self.file.write_bytes((log(serial='FIRST')+log(serial='SECOND')[:-1]).encode(encoding))
            reader = LiPrimeLogReader()
            self.assertEqual([r.SERIAL for r in reader.read_file(self.file)], ['FIRST'])
            self.file.write_bytes((log(serial='FIRST')+log(serial='SECOND')).encode(encoding))
            self.assertEqual([r.SERIAL for r in reader.read_file(self.file)], ['FIRST','SECOND'])

    def test_later_changes_do_not_replace_snapshot_and_next_import_catches_up(self):
        self.file.write_text(log(serial='FIRST'))
        def progress(message):
            if message.startswith('Đã đọc'):
                self.file.write_text(log(serial='SECOND'))
        service = PrimeImportService(self.db)
        service.import_folder(self.root, ('20260924',), progress)
        with sqlite3.connect(self.db) as c:
            self.assertEqual(c.execute('SELECT SERIAL FROM prime_data').fetchone()[0], 'FIRST')
        service.import_folder(self.root, ('20260924',))
        with sqlite3.connect(self.db) as c:
            self.assertEqual(c.execute('SELECT SERIAL FROM prime_data').fetchone()[0], 'SECOND')
            self.assertEqual(c.execute('SELECT COUNT(*) FROM import_lock').fetchone()[0], 0)

    def test_malformed_complete_line_preserves_data_and_releases_lock(self):
        self.file.write_text(log())
        service = PrimeImportService(self.db)
        service.import_folder(self.root, ('20260924',))
        self.file.write_text(log(SLOT='99'))
        with self.assertRaises(ValidationError):
            service.import_folder(self.root, ('20260924',))
        with sqlite3.connect(self.db, timeout=0) as c:
            c.execute('BEGIN IMMEDIATE')
            self.assertEqual(c.execute('SELECT COUNT(*) FROM prime_data').fetchone()[0], 1)
            self.assertEqual(c.execute('SELECT COUNT(*) FROM import_lock').fetchone()[0], 0)
            c.rollback()

    def test_export_local_snapshot_does_not_hold_main_reader(self):
        self.file.write_text(log())
        PrimeImportService(self.db).import_folder(self.root, ('20260924',))
        with machine_export_snapshot(self.db, ('20260924','20260924'), threading.Event()) as snapshot:
            with sqlite3.connect(self.db, timeout=0) as c:
                c.execute('BEGIN IMMEDIATE')
                c.execute("UPDATE prime_data SET SERIAL='NEW'")
                c.commit()
            self.assertEqual(snapshot.execute('SELECT SERIAL FROM prime_data').fetchone()[0], 'SN1')

    def test_mail_details_preserved_for_same_and_mixed_codes(self):
        self.file.write_text(''.join(log(serial=f'S{i}', result='FAIL', time=f'[12:00:0{i}]',
                                      SCRAP_CODE=code, TEST_COUNT='0')
                                      for i,code in enumerate(['A','A','A','B','C','D'])))
        PrimeImportService(self.db).import_folder(self.root, ('20260924',))
        alarms = MailTemplateRepository(self.db).get_alarm_previews(['20260924'])
        self.assertEqual(len(alarms), 1)
        same = [r for r in alarms[0]['runs'] if not r.get('different_scrap')]
        self.assertTrue(same)
        self.assertEqual(len(same[0]['details']), 3)
        self.assertEqual({r['SCRAPCODE'] for r in same[0]['details']}, {'A'})
        self.assertTrue(any(r.get('different_scrap') for r in alarms[0]['runs']))

    def test_diagnostics_redact_parameters_and_record_commit_failure(self):
        read = sqlite3.connect(self.db)
        read.execute('BEGIN')
        read.execute('SELECT COUNT(*) FROM prime_data').fetchone()
        writer = create_connection(self.db, timeout=0.02)
        try:
            writer.execute('BEGIN IMMEDIATE')
            writer.execute('UPDATE auto_import_scheduler SET log_folder=?', ('SECRET_MARKER_2026',))
            with self.assertRaises(sqlite3.OperationalError):
                writer.commit()
        finally:
            writer.close()
            read.close()
        text = log_path().read_text()
        self.assertNotIn('SECRET_MARKER_2026', text)
        events = [json.loads(line) for line in text.splitlines()]
        self.assertTrue(any(e['event']=='DB_ERROR' and e['operation']=='COMMIT' for e in events))

    def test_heartbeat_stop_bounded_and_stop_failure_prevents_replace(self):
        hb = ImportLockHeartbeat(None, 'test')
        with patch.object(hb.thread, 'join') as join, patch.object(hb.thread, 'is_alive', return_value=True):
            self.assertFalse(hb.stop())
            join.assert_called_once_with(timeout=5)
        self.file.write_text(log())
        with patch.object(ImportLockHeartbeat, 'stop', return_value=False), \
             patch.object(ImportLockHeartbeat, 'start'), \
             patch('services.prime_import_service.PrimeRepository.replace_from_staging') as replace:
            with self.assertRaises(TimeoutError):
                PrimeImportService(self.db).import_folder(self.root, ('20260924',))
            replace.assert_not_called()

    def test_active_import_owner_is_not_stolen(self):
        from domain.prime import ImportBusyError
        locks = ImportLockRepository(self.db)
        batch = locks.acquire('first')
        try:
            with self.assertRaises(ImportBusyError):
                locks.acquire('second')
            with sqlite3.connect(self.db) as c:
                self.assertEqual(c.execute('SELECT batch_id FROM import_lock').fetchone()[0], batch)
        finally:
            locks.release(batch)

    def test_report_connection_remains_readonly(self):
        from repositories.report_repository import ReportRepository
        with ReportRepository(self.db)._connect() as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM prime_data').fetchone()[0], 0)
            with self.assertRaises(sqlite3.OperationalError):
                c.execute('DELETE FROM prime_data')
