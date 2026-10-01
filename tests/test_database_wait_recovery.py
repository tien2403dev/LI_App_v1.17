"""Real SQLite contention + Qt event-loop regression tests for GUI recovery."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from PyQt5.QtCore import QDate, QThread
from PyQt5.QtWidgets import QApplication
from controllers.prime_controller import PrimeController
from database.schema import initialize_database
from database.connection import create_connection
from ui.main_window import MainWindow
from ui.database_wait import MESSAGE
from workers.report_worker import ReportWorker

APP = QApplication.instance() or QApplication([])


def wait(predicate, seconds=8):
    deadline = time.monotonic() + seconds
    while not predicate():
        APP.processEvents()
        if time.monotonic() > deadline:
            raise AssertionError('Timed out waiting for Qt worker')
        time.sleep(.003)
    APP.processEvents()


class DatabaseWaitRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name)/'li.db'
        initialize_database(self.db)
        with sqlite3.connect(self.db) as c:
            c.execute("INSERT INTO prime_data(DATE,TIME,EQP,PARTNO,LOTNO,SLOT,RESULT,SCRAPCODE,TEST_COUNT,SERIAL,QTY,MODEL) VALUES('20261001','08:00:00','LI-01','ABCDE123','LOT1',1,'PASS',NULL,0,'SN1',1,'ABCDE')")
        self.window = MainWindow()
        self.controller = PrimeController(self.window, self.db)
        self.window.show()
        self.errors = []
        self.controller.dialogs.show_error = self.errors.append
        self.writer = None
        self.interval = patch('workers.database_read_task.RETRY_SECONDS', .08)
        self.interval.start()

    def tearDown(self):
        self.unlock()
        self.window.close()
        wait(lambda: self.window._can_close)
        self.interval.stop()
        self.temp.cleanup()

    def lock(self, mode='EXCLUSIVE'):
        self.writer = sqlite3.connect(self.db)
        self.writer.execute('BEGIN '+mode)

    def unlock(self):
        if self.writer:
            self.writer.rollback()
            self.writer.close()
            self.writer = None

    def ready(self):
        self.controller.initialize_database()
        wait(lambda: self.controller._filters_ready and not self.controller.busy)

    def waiting(self):
        wait(lambda: bool(self.controller.database_wait.waiting))
        self.assertEqual(self.controller.database_wait.dialog.text(), MESSAGE)
        self.assertFalse(self.window.prime_page.filter_panel.apply_filter_button.isEnabled())

    def recovered(self):
        wait(lambda: not self.controller.database_wait.waiting and not self.controller.busy
             and self.controller._filter_thread is None)
        self.assertIsNone(self.controller.database_wait.dialog)
        self.assertTrue(self.window.prime_page.filter_panel.apply_filter_button.isEnabled())
        self.assertEqual(self.errors, [])

    def test_startup_dialog_open_recovers_filters(self):
        self.lock()
        self.controller.initialize_database()
        self.waiting()
        self.assertTrue(self.window.isVisible())
        self.unlock()
        wait(lambda: self.controller._filters_ready)
        self.recovered()
        self.assertGreaterEqual(self.window.prime_page.filter_panel.eqp_combo.findData('LI-01'), 0)

    def test_startup_dismiss_does_not_cancel_or_reopen_notice(self):
        self.lock()
        self.controller.initialize_database()
        self.waiting()
        dialog = self.controller.database_wait.dialog
        dialog.close()
        deadline = time.monotonic()+1.2
        while time.monotonic()<deadline:
            APP.processEvents(); time.sleep(.003)
        self.assertIs(dialog, self.controller.database_wait.dialog)
        self.assertFalse(dialog.isVisible())
        self.unlock()
        wait(lambda: self.controller._filters_ready)
        self.recovered()

    def test_filter_read_itself_recovers(self):
        self.ready()
        self.lock()
        self.controller.refresh_filter_options()
        self.waiting()
        self.unlock()
        wait(lambda: self.controller._filters_ready)
        self.recovered()

    def test_summary_search_retains_request_and_recovers(self):
        self.ready()
        panel = self.window.prime_page.filter_panel
        panel.from_date_edit.setDate(QDate(2026,10,1))
        panel.to_date_edit.setDate(QDate(2026,10,1))
        old_title = self.window.prime_page.summary_page.summary_title_label.text()
        self.lock()
        panel.apply_filter_button.click()
        self.waiting()
        self.assertEqual(self.window.prime_page.summary_page.summary_title_label.text(), old_title)
        self.assertIsNone(self.controller.dialogs.progress)
        self.unlock()
        self.recovered()
        self.assertEqual(self.controller._summary_key[:2], ('20261001','20261001'))

    def test_alarm_search_dismiss_keeps_rows_then_refreshes(self):
        self.ready()
        root = self.window.prime_page
        root.tabs.setCurrentWidget(root.alarm_host)
        wait(lambda: not self.controller.busy)
        page = root.ensure_alarm_page()
        # Observe that no intermediate empty result is delivered on lock.
        calls=[]
        original=page.load_rows
        with patch.object(page,'load_rows',side_effect=lambda rows:(calls.append(rows),original(rows))):
            self.lock()
            root.filter_panel.apply_filter_button.click()
            self.waiting()
            self.assertEqual(calls, [])
            self.controller.database_wait.dialog.close()
            self.unlock()
            self.recovered()
            self.assertEqual(len(calls),1)

    def test_yield_slot_search_recovers(self):
        self.ready()
        self.lock()
        self.window.prime_page.tabs.setCurrentWidget(self.window.prime_page.yield_slot_page)
        self.waiting()
        self.unlock()
        self.recovered()
        self.assertIsNotNone(self.controller._slot_key)

    def test_first_machine_tab_config_and_search_both_recover(self):
        self.ready()
        self.lock()
        root=self.window.prime_page
        root.tabs.setCurrentWidget(root.machine_slot_yield_host)
        self.waiting()
        machine=root.machine_slot_yield_page
        self.unlock()
        wait(lambda: machine._loaded and machine.config_thread is None and machine.summary.thread is None)
        self.recovered()
        self.assertIsNotNone(machine.summary.payload)

    def test_report_worker_retries_same_query(self):
        self.ready()
        results=[]; errors=[]
        thread=QThread()
        worker=ReportWorker(self.db,'summary',date_from='2026-10-01 00:00:00',
                            date_to='2026-10-01 23:59:59',eqps=['LI-01'],slots=[1])
        self.controller.database_wait.bind(worker)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.succeeded.connect(results.append)
        worker.failed.connect(errors.append)
        worker.finished.connect(thread.quit)
        self.lock(); thread.start()
        try:
            self.waiting()
            self.unlock()
            wait(lambda: not thread.isRunning())
            self.assertEqual(errors,[])
            self.assertEqual(len(results),1)
            self.assertEqual(len(results[0]),1)
        finally:
            self.unlock()
            thread.quit(); thread.wait(3000)
        self.recovered()

    def test_staging_import_lease_does_not_block_reads(self):
        from repositories.import_lock_repository import ImportLockRepository
        lease=ImportLockRepository(self.db)
        batch=lease.acquire('test staging')
        try:
            self.ready()
            self.assertFalse(self.controller.database_wait.waiting)
            self.assertIsNone(self.controller.database_wait.dialog)
        finally:
            lease.release(batch)

    def test_reserved_write_lock_still_allows_reads(self):
        self.lock('IMMEDIATE')
        self.ready()
        self.assertFalse(self.controller.database_wait.waiting)

    def test_close_while_locked_stops_retry(self):
        self.lock(); self.controller.initialize_database(); self.waiting()
        start=time.monotonic()
        self.window.close()
        wait(lambda:self.window._can_close,3)
        self.assertLess(time.monotonic()-start,2)
        self.assertEqual(self.errors,[])

    def test_non_lock_error_is_not_retried(self):
        with patch('database.schema.initialize_database',side_effect=ValueError('Bad schema')) as read:
            self.controller.initialize_database()
            wait(lambda:not self.controller.busy)
            self.assertEqual(read.call_count,1)
            self.assertIn('Bad schema',self.errors[0])
            self.assertFalse(self.controller.database_wait.waiting)

    def test_alarm_write_is_never_retried(self):
        from workers.alarm_worker import AlarmWorker
        errors=[]; waiting=[]
        worker=AlarmWorker(self.db, edit=({}, 'status', 'Đang tiến hành'))
        worker.failed.connect(errors.append)
        worker.database_waiting.connect(waiting.append)
        with patch('repositories.alarm_repository.AlarmRepository.update_tracking',
                   side_effect=sqlite3.OperationalError('database is locked')) as save:
            worker.run()
            self.assertEqual(save.call_count,1)
        self.assertEqual(waiting,[])
        self.assertEqual(errors,['database is locked'])

    def test_open_report_during_lock_and_close_cancels_workers(self):
        self.ready()
        self.lock()
        root=self.window.prime_page
        root.tabs.setCurrentWidget(root.report_host)
        self.waiting()
        self.window.close()
        wait(lambda: self.window._can_close,3)
        self.assertEqual(self.errors,[])

    def test_import_default_timeout_unchanged(self):
        self.ready()
        c=create_connection(self.db)
        try:
            self.assertEqual(c.execute('PRAGMA busy_timeout').fetchone()[0],60000)
        finally: c.close()

if __name__=='__main__':
    unittest.main()
