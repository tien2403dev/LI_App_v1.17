"""Kiểm tra tab Alarm, worker lưu và đóng app bằng Qt offscreen."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWidgets import QApplication, QStyleOptionViewItem
from controllers.prime_controller import PrimeController
from ui.main_window import MainWindow
from repositories.alarm_repository import AlarmRepository
from database.schema import initialize_database
from database.connection import connection
from tests.test_alarm import event
from domain.prime import COLUMNS

APP=QApplication.instance() or QApplication([])


def wait_until(predicate):
    """Cho Qt xử lý signal tới khi thread kết thúc, có giới hạn thời gian."""
    deadline=time.monotonic()+10
    while not predicate():
        APP.processEvents()
        if time.monotonic()>deadline:
            raise AssertionError('Worker timeout')
        time.sleep(.005)
    APP.processEvents()


class AlarmGuiTests(unittest.TestCase):
    def setUp(self):
        """Dữ liệu mẫu và cửa sổ thật trên DB tạm."""
        self.temp=tempfile.TemporaryDirectory()
        self.db=Path(self.temp.name)/'li.db'
        initialize_database(self.db)
        with connection(self.db) as conn:
            rows=[event(i,slot=slot) for slot in (1,2) for i in range(1,4)]
            conn.executemany(f"INSERT INTO prime_data({','.join(COLUMNS)}) VALUES({','.join('?' for _ in COLUMNS)})",
                             [tuple(r[c] for c in COLUMNS) for r in rows])
            conn.execute('BEGIN IMMEDIATE')
            AlarmRepository.sync_import_dates(conn,['20260915'],lambda msg:None)
            conn.commit()
        self.window=MainWindow()
        self.controller=PrimeController(self.window,self.db)
        self.window.resize(1600,900)
        self.window.show()
        self.errors=[]
        self.controller.dialogs.show_error=self.errors.append
        self.controller.initialize_database()
        wait_until(lambda:not self.controller.busy)

    def tearDown(self):
        """Đợi worker rồi đóng cửa sổ trước khi xóa DB."""
        wait_until(lambda:not self.controller.busy)
        self.window.close()
        APP.processEvents()
        self.temp.cleanup()

    def open_alarm(self):
        """Chuyển vào tab tự tải ngày trên bộ lọc, không bấm Search."""
        panel=self.window.prime_page.filter_panel
        # Dùng API criteria có sẵn; kiểm tra routing khi đổi tab.
        criteria=panel.get_filter_criteria()
        from dataclasses import replace
        criteria=replace(criteria,date_from='20260915',date_to='20260915')
        self.patch=patch.object(panel,'get_filter_criteria',return_value=criteria)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.window.prime_page.tabs.setCurrentWidget(self.window.prime_page.alarm_host)
        wait_until(lambda:not self.controller.busy)
        return self.window.prime_page.alarm_page

    def test_tab_filters_save_status_text_and_refresh_external(self):
        """Lọc theo cột, lưu đúng ID sau lọc và refresh khi import ngoài app."""
        self.assertIsNone(self.window.prime_page.alarm_page)
        page=self.open_alarm()
        self.assertEqual(page.model.columnCount(),23)
        self.assertEqual(page.model.rowCount(),2)
        page.apply_filter(3,{'2'},['1','2'])
        self.assertEqual(page.proxy.rowCount(),1)
        page.proxy.setData(page.proxy.index(0,18),'Thay cáp',Qt.EditRole)
        wait_until(lambda:not self.controller.busy)
        row=next(r for r in AlarmRepository(self.db).load('20260915','20260915') if r['slot']==2)
        self.assertEqual(row['engineer_action'],'Thay cáp')
        page.proxy.setData(page.proxy.index(0,14),'Đã hoàn thành',Qt.EditRole)
        wait_until(lambda:not self.controller.busy)
        self.assertTrue(page.proxy.index(0,15).data())
        self.assertEqual(page.proxy.index(0,14).data(Qt.BackgroundRole).name(),'#d9ead3')
        self.assertEqual(page.proxy.index(0,7).data(),'')
        page.clear_filters()
        self.assertEqual(page.proxy.rowCount(),2)
        with connection(self.db) as conn:
            conn.execute("DELETE FROM slot_fail_alarm WHERE slot=1")
        self.controller.load_alarm(self.window.prime_page.filter_panel.get_filter_criteria())
        wait_until(lambda:not self.controller.busy)
        self.assertEqual(page.model.rowCount(),1)
        self.assertEqual(self.errors,[])

    def test_delegate_commit_and_close_with_worker(self):
        """Dropdown ghi qua model thật; đóng app đợi tác vụ lưu hoàn tất."""
        page=self.open_alarm()
        index=page.proxy.index(0,14)
        delegate=page.table.itemDelegateForColumn(14)
        editor=delegate.createEditor(page.table,QStyleOptionViewItem(),index)
        delegate.setEditorData(editor,index)
        editor.setCurrentText('Đang thực hiện')
        delegate.setModelData(editor,page.proxy,index)
        self.window.close()
        wait_until(lambda:not self.window.isVisible())
        rows=AlarmRepository(self.db).load('20260915','20260915')
        self.assertEqual(rows[0]['status'],'Đang thực hiện')
        self.assertEqual(self.errors,[])
        editor.deleteLater()


if __name__=='__main__':
    unittest.main()
