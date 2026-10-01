import os, sys, tempfile, time, unittest
os.environ['QT_QPA_PLATFORM']='offscreen'
from pathlib import Path
from unittest.mock import patch
from database.schema import initialize_database
from database.connection import connection
from repositories.database_management_repository import DatabaseManagementRepository
from repositories.auto_import_scheduler_repository import AutoImportSchedulerRepository
from services.prime_export_service import PrimeExportService
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
APP=QApplication.instance() or QApplication([])
def wait(pred):
 deadline=time.monotonic()+15
 while not pred():
  APP.processEvents(); time.sleep(.005)
  if time.monotonic()>deadline: raise AssertionError('timeout')
 APP.processEvents()
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.db=Path(self.tmp.name)/'li.db'; initialize_database(self.db)
  with connection(self.db) as c:
   for day,tc in [('20260915',1),('20260915',2),('20260831',1)]:
    c.execute("INSERT INTO prime_data(DATE,TIME,EQP,PARTNO,LOTNO,SLOT,RESULT,TEST_COUNT,SERIAL,MODEL) VALUES(?, '08:00:00','AI-H903','ABCDE-123','LOT1',1,'PASS',?,'SN','ABCDE')",(day,tc))
   c.execute("INSERT INTO data_import_status VALUES('PRIME','20260915','2026-09-15T01:02:03+00:00','batch',2)")
 def tearDown(self): self.tmp.cleanup()
 def test_existing_database_and_list(self):
  with connection(self.db) as c: c.execute('DROP TABLE auto_import_scheduler')
  initialize_database(self.db); initialize_database(self.db)
  r=DatabaseManagementRepository(self.db).get_date_records('PRIME')
  self.assertEqual([x.data_date for x in r],['20260915','20260831']);self.assertIsNone(r[1].load_time)
  self.assertEqual(DatabaseManagementRepository(self.db).get_date_records('CUM'),[])
  self.assertEqual(AutoImportSchedulerRepository(self.db).get_config().enabled,False)
 def test_export_split_all_test_counts(self):
  import services.prime_export_service as m
  from openpyxl import load_workbook
  with patch.object(m,'MAX_DATA_ROWS_PER_SHEET',1):
   result=PrimeExportService(self.db).export_dates(['20260915'],Path(self.tmp.name)/'export.xlsx')
  self.assertEqual((result.exported_row_count,result.sheet_count),(2,2))
  w=load_workbook(result.output_path,read_only=True)
  rows=[list(s.values) for s in w];col=rows[0][0].index('TEST_COUNT')
  self.assertEqual([r[1][col] for r in rows],[1,2]);w.close()
 def test_scheduler_gates_and_success(self):
  import auto_import_main as m
  from datetime import datetime,timedelta
  repo=AutoImportSchedulerRepository(self.db)
  target=(datetime.now().date()-timedelta(days=1)).strftime('%Y%m%d')
  with patch.object(m,'append_auto_import_log'),patch('services.prime_import_service.PrimeImportService') as svc:
   m.run_auto_import(self.db);svc.assert_not_called()
   repo.save_config(True,'00:00','logs')
   svc.return_value.import_folder.side_effect=ValueError('invalid log')
   with self.assertRaises(ValueError):m.run_auto_import(self.db)
   self.assertIsNone(repo.get_config().last_import_date)
   svc.return_value.import_folder.side_effect=None
   svc.return_value.import_folder.return_value=type('R',(),dict(inserted=2,deleted=0))()
   m.run_auto_import(self.db)
   self.assertEqual(repo.get_config().last_import_date,target)
   svc.reset_mock();m.run_auto_import(self.db);svc.assert_not_called()
 def test_scheduler_skips_only_when_selected_date_has_no_txt_file(self):
  """Thiếu file ngày cần lấy là SKIPPED; các lỗi validation khác vẫn được ném ra."""
  import auto_import_main as m
  from domain.prime import ValidationError
  repo=AutoImportSchedulerRepository(self.db)
  repo.save_config(True,'00:00','logs')
  with patch.object(m,'append_auto_import_log') as write_log, patch(
          'services.prime_import_service.PrimeImportService') as svc:
   svc.return_value.import_folder.side_effect=ValidationError(
       'Không tìm thấy file .txt trong các folder ngày được chọn')
   self.assertEqual(m.run_auto_import(self.db),0)
   self.assertIsNone(repo.get_config().last_import_date)
   self.assertEqual(write_log.call_args_list[-1].args[0],'SKIPPED')
   self.assertIn('sẽ kiểm tra lại',write_log.call_args_list[-1].args[1])
   svc.return_value.import_folder.side_effect=ValidationError(
       'File log sai cấu trúc')
   with self.assertRaisesRegex(ValidationError,'sai cấu trúc'):
    m.run_auto_import(self.db)
   self.assertIsNone(repo.get_config().last_import_date)
 def test_gui_refresh_export_and_close(self):
  from ui.main_window import MainWindow
  from controllers.prime_controller import PrimeController
  w=MainWindow();ctl=PrimeController(w,self.db);errors=[];ctl.dialogs.show_error=errors.append
  w.resize(1892,780);w.show();ctl.initialize_database();wait(lambda:not ctl.busy)
  w.prime_page.tabs.setCurrentWidget(w.prime_page.file_management_host)
  p=w.prime_page.file_management_page;self.assertIsNotNone(p);wait(lambda:not p.is_busy())
  self.assertEqual(errors,[]);self.assertTrue(w.prime_page.filter_panel.isVisible())
  self.assertEqual(p.prime_panel.table.rowCount(),2)
  p.prime_panel.select_all_checkbox.setCheckState(Qt.Checked)
  self.assertEqual(p.prime_panel.selected_checked_dates(),['20260915','20260831'])
  p.prime_panel._selected_months={'202609'};p.prime_panel._apply_filters()
  self.assertEqual(p.prime_panel.table.rowCount(),1)
  with patch.object(QMessageBox,'information'):
   p._start_export(['20260915'],Path(self.tmp.name)/'gui.xlsx');wait(lambda:not p.is_busy())
  p.load_if_needed(force=True);wait(lambda:not p.is_busy())
  p.load_if_needed(force=True);w.close();wait(lambda:not w.isVisible());self.assertFalse(p.is_busy())
if __name__=='__main__':unittest.main(verbosity=2)
