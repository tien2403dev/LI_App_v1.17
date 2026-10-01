"""Kiểm thử nghiệp vụ Alarm và transaction import thật trên SQLite tạm."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from threading import Event
from unittest.mock import patch
from database.connection import connection
from database.schema import initialize_database, PRIME_FIELDS
from domain.prime import COLUMNS, ImportCancelled
from repositories.alarm_repository import AlarmRepository
from repositories.import_lock_repository import ImportLockRepository
from repositories.machine_slot_yield_repository import MachineSlotYieldRepository
from repositories.prime_repository import PrimeRepository
from services.alarm_builder import build_slot_alarm


def event(number, result='FAIL', model='AAAAA', scrap='4590', date='20260915', slot=1):
    """Một test hợp lệ; TEST_COUNT=2 để bảo đảm không chỉ lấy test đầu."""
    return dict(id=number, DATE=date, TIME=f'{number//3600:02d}:{number//60%60:02d}:{number%60:02d}',
                EQP='AI-H903', PARTNO=model+'-PART', LOTNO='LOT'+model, SLOT=slot,
                RESULT=result, SCRAPCODE=scrap if result=='FAIL' else None,
                TEST_COUNT=2, SERIAL=f'SN{number}', QTY=1, MODEL=model)


def build(rows, threshold=3, t15=70, t30=75, date='20260915'):
    """Duyệt giống truy vấn repository; caller cung cấp lịch sử không có tương lai."""
    return build_slot_alarm(sorted(rows, key=lambda r:(r['DATE'],r['TIME'],r['id']), reverse=True), date,
                            dict(continuous_fail_count=threshold, different_scrap_fail_count=999, target_15=t15, target_30=t30))


class AlarmRulesTests(unittest.TestCase):
    def test_cross_day_same_model_and_skip_other_models(self):
        """Gom 15 A xuyên ngày dù B xen giữa; B không làm tăng mẫu số."""
        rows = [event(i, 'PASS' if i <= 10 else 'FAIL', date='20260914') for i in range(1,15)]
        rows += [event(15, 'FAIL'), event(16, 'PASS', 'BBBBB')]
        alarm = build(rows, threshold=999)
        self.assertAlmostEqual(alarm['yield_15'], 100*10/15)
        self.assertIsNone(alarm['yield_30'])
        self.assertEqual(alarm['models'], 'AAAAA')
        self.assertEqual(alarm['scrap_codes'], '')
        self.assertEqual(alarm['start_datetime'], '2026-09-14 00:00:01')
        self.assertEqual(alarm['end_datetime'], '2026-09-15 00:00:15')

    def test_latest_ten_pass_suppresses_old_violation(self):
        """Mười test mới nhất PASS bỏ qua alarm hiệu suất cũ."""
        rows = [event(i, 'FAIL' if i<=20 else 'PASS') for i in range(1,31)]
        alarm = build(rows, threshold=999)
        self.assertIsNone(alarm)  # 10 test mới nhất PASS: bỏ cả Yield 15/30.

    def test_no_slide_back_after_recovery(self):
        """Không tìm ngược alarm hiệu suất khi slot đã phục hồi."""
        rows = [event(i, 'FAIL' if i<=10 else 'PASS') for i in range(1,31)]
        alarm = build(rows, threshold=999)
        self.assertIsNone(alarm)  # Đã phục hồi: không tìm lại cửa sổ lỗi cũ.

    def test_models_compete_by_endpoint_not_completion_order(self):
        """A ít gặp vẫn được chọn nếu endpoint mới hơn cửa sổ B đã tìm ra trước."""
        rows = [event(i) for i in range(1,15)]
        rows += [event(i, model='BBBBB') for i in range(20,35)]
        rows += [event(40)]
        alarm = build(rows, threshold=999)
        self.assertEqual(alarm['models'], 'AAAAA')
        self.assertEqual(alarm['end_datetime'], '2026-09-15 00:00:40')

    def test_rule1_cross_day_full_run_priority_and_scraps(self):
        """Cả ba quy tắc chỉ một alarm, thời gian ưu tiên chuỗi 1 gần nhất."""
        rows = [event(i, date='20260914', scrap='4580') for i in range(1,4)]
        rows += [event(i, scrap='4580') for i in range(4,7)]
        rows += [event(7, 'PASS')]
        rows += [event(i) for i in range(8,35)]
        alarm = build(rows)
        self.assertEqual(alarm['fail_comment'].count(' | '), 2)
        self.assertEqual(alarm['scrap_codes'], '4580,4590')
        self.assertEqual(alarm['start_datetime'], '2026-09-15 00:00:08')
        self.assertEqual(alarm['end_datetime'], '2026-09-15 00:00:34')
        self.assertEqual(json.loads(alarm['evidence_json'])['1'][1]['start'], '2026-09-14 00:00:01')

    def test_rule1_pass_model_scrap_break_run(self):
        """Không nối FAIL qua PASS, đổi model hoặc đổi mã lỗi."""
        for middle in [event(2,'PASS'), event(2,model='BBBBB'), event(2,scrap='4580')]:
            self.assertIsNone(build([event(1), middle, event(3)]))

    def test_insufficient_equal_threshold_and_historical_only(self):
        """Không dùng thiếu mẫu, bằng target hoặc vi phạm chỉ ở ngày cũ."""
        self.assertIsNone(build([event(i) for i in range(1,15)], threshold=999))
        self.assertIsNone(build([event(i,'PASS' if i<=9 else 'FAIL') for i in range(1,16)],
                                threshold=999, t15=60))
        rows = [event(i,date='20260914') for i in range(1,40)] + [event(50,'PASS',model='BBBBB')]
        self.assertIsNone(build(rows, threshold=999))


class AlarmImportTests(unittest.TestCase):
    def setUp(self):
        """Tạo database LI độc lập và các repository thật."""
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.db = self.base/'li.db'
        initialize_database(self.db)
        self.repository = AlarmRepository(self.db)
        self.config = MachineSlotYieldRepository(self.db)

    def tearDown(self):
        """Đóng và xóa thư mục test."""
        self.temp.cleanup()

    def import_rows(self, rows):
        """Chạy replace_from_staging có khóa import như luồng production."""
        stage = self.base/'stage.db'
        stage.unlink(missing_ok=True)
        with sqlite3.connect(stage) as conn:
            conn.execute(f'CREATE TABLE staging_prime_data({PRIME_FIELDS})')
            conn.executemany(f"INSERT INTO staging_prime_data({','.join(COLUMNS)}) VALUES({','.join('?' for _ in COLUMNS)})",
                             [tuple(r[c] for c in COLUMNS) for r in rows])
        locks = ImportLockRepository(self.db)
        token = locks.acquire('test')
        try:
            return PrimeRepository(self.db).replace_from_staging(stage,token,1,lambda msg:None)
        finally:
            locks.release(token)

    def alarms(self):
        """Lấy cả hai ngày để kiểm tra cô lập Alarm Date."""
        return self.repository.load('20260914','20260916')

    def test_reimport_updates_machine_fields_preserves_tracking_then_deletes(self):
        """Cập nhật trường máy nhưng bảo toàn tất cả trường xử lý; xóa khi hết vi phạm."""
        self.import_rows([event(i) for i in range(1,4)])
        row = self.alarms()[0]
        row, _ = self.repository.update_tracking(row,'engineer_action','Đã kiểm tra cáp')
        row, _ = self.repository.update_tracking(row,'status','Đã hoàn thành')
        for name in ('quick_check_result','cal_check_result','comment'):
            row, _ = self.repository.update_tracking(row,name,'PASS' if name in ('quick_check_result','cal_check_result') else 'Nội dung '+name)
        self.import_rows([event(i,scrap='4580') for i in range(1,5)])
        changed = self.alarms()[0]
        from domain.alarm import TRACKING_FIELDS
        for field in (*TRACKING_FIELDS, 'date_complete', 'id', 'created_at',
                      'alarm_date', 'eqp', 'slot'):
            self.assertEqual(changed[field], row[field], field)
        self.assertEqual(changed['scrap_codes'], '4580')
        self.assertEqual(changed['end_datetime'], '2026-09-15 00:00:04')
        self.assertEqual(changed['row_version'], row['row_version'] + 1)
        latest, conflict = self.repository.update_tracking(row, 'comment', 'stale edit')
        self.assertTrue(conflict)
        self.assertEqual(latest, changed)
        self.config.save_config('',0,0,99)
        self.import_rows([event(i) for i in range(1,4)])
        self.assertEqual(self.alarms(),[])
        self.config.save_config('',70,75,3)
        self.import_rows([event(i) for i in range(1,4)])
        new = self.alarms()[0]
        self.assertNotEqual(new['id'],row['id'])
        self.assertEqual(new['status'],'Chưa tiến hành')
        self.assertEqual(new['engineer_action'],'')
        with self.assertRaisesRegex(ValueError,'đã bị xóa'):
            self.repository.update_tracking(row,'comment','stale')

    def test_new_targets_refresh_all_machine_fields_and_clear_obsolete_yield(self):
        """Đổi target làm đổi cửa sổ, comment và thời gian nhưng giữ kết quả xử lý."""
        rows = [event(i, 'FAIL' if i <= 9 or i == 30 else 'PASS') for i in range(1,31)]
        self.config.save_config('', 90.5, 90, 999)
        self.import_rows(rows)
        old = self.alarms()[0]
        old, _ = self.repository.update_tracking(old, 'status', 'Đã hoàn thành')
        old, _ = self.repository.update_tracking(old, 'engineer_action', 'Giữ nguyên')
        self.config.save_config('', 0, 70, 999)
        self.import_rows(rows)
        new = self.alarms()[0]
        self.assertEqual((new['target_15'], new['target_30']), (0, 70))
        self.assertIsNone(new['yield_15'])
        self.assertAlmostEqual(new['yield_30'], 100*20/30)
        self.assertEqual(new['fail_comment'], 'Yield 30 < 70.00%')
        self.assertEqual(new['start_datetime'], '2026-09-15 00:00:01')
        self.assertEqual(new['end_datetime'], '2026-09-15 00:00:30')
        for field in ('id','status','date_complete','engineer_action'):
            self.assertEqual(new[field], old[field])
        changed_rows = [event(i, 'FAIL' if i <= 9 or i == 30 else 'PASS', model='BBBBB')
                        for i in range(1,31)]
        self.import_rows(changed_rows)
        changed = self.alarms()[0]
        self.assertEqual(changed['models'], 'BBBBB')
        self.assertEqual(changed['lotids'], 'LOTBBBBB')
        self.assertEqual(changed['status'], old['status'])
        self.assertEqual(changed['engineer_action'], old['engineer_action'])

    def test_new_slot_removed_slot_and_other_alarm_date(self):
        """Slot biến mất bị xóa; cùng slot ngày khác vẫn có dòng độc lập."""
        self.import_rows([event(i,date='20260914') for i in range(1,4)]+[event(i) for i in range(4,7)])
        self.assertEqual(len(self.alarms()),2)
        before = [r for r in self.alarms() if r['alarm_date']=='20260914'][0]
        self.import_rows([event(i,slot=2) for i in range(1,4)])
        self.assertEqual({(r['alarm_date'],r['slot']) for r in self.alarms()}, {('20260914',1),('20260915',2)})
        self.assertIn(before,self.alarms())

    def test_yield_history_retest_and_no_future(self):
        """Tất cả TEST_COUNT; ngày 15 lấy 14 nhưng không được lấy 16."""
        rows = [event(i,date='20260914') for i in range(1,15)]+[event(15)]
        rows += [event(i,date='20260916') for i in range(16,40)]
        self.config.save_config('',70,75,999)
        self.import_rows(rows)
        day15 = next(r for r in self.alarms() if r['alarm_date']=='20260915')
        self.assertEqual(day15['yield_15'],0)
        self.assertIsNone(day15['yield_30'])
        self.assertEqual(day15['end_datetime'],'2026-09-15 00:00:15')

    def test_failure_rolls_back_prime_alarm_and_metadata(self):
        """Lỗi sau khi alarm đã được đồng bộ phải rollback toàn bộ dữ liệu."""
        self.import_rows([event(i) for i in range(1,4)])
        def snapshot():
            with connection(self.db) as conn:
                return {t:[tuple(r) for r in conn.execute(f'SELECT * FROM {t}')]
                        for t in ('prime_data','slot_fail_alarm','data_import_status')}
        before=snapshot()
        with patch.object(ImportLockRepository,'renew_in_transaction',side_effect=RuntimeError('injected')):
            with self.assertRaisesRegex(RuntimeError,'injected'):
                self.import_rows([event(i,'PASS') for i in range(1,4)])
        self.assertEqual(snapshot(),before)

    def test_conflict_busy_and_completion(self):
        """Ngăn ghi đè người khác; completion chỉ đổi khi chuyển trạng thái."""
        self.import_rows([event(i) for i in range(1,4)])
        old=self.alarms()[0]
        new, conflict=self.repository.update_tracking(old,'comment','Người 1')
        self.assertFalse(conflict)
        latest, conflict=self.repository.update_tracking(old,'comment','Người 2')
        self.assertTrue(conflict)
        self.assertEqual(latest['comment'],'Người 1')
        with connection(self.db) as conn:
            conn.execute('BEGIN IMMEDIATE')
            with self.assertRaisesRegex(ValueError,'đang được cập nhật'):
                self.repository.update_tracking(new,'status','Đang thực hiện')
            conn.rollback()
        complete,_=self.repository.update_tracking(new,'status','Đã hoàn thành')
        self.assertTrue(complete['date_complete'])
        same,_=self.repository.update_tracking(complete,'status','Đã hoàn thành')
        self.assertEqual(same,complete)
        reopened,_=self.repository.update_tracking(same,'status','Đang thực hiện')
        self.assertEqual(reopened['date_complete'],'')

    def test_auto_today_generates_and_removes_alarm_from_real_logs(self):
        """Auto Today đi qua reader/service thật, tạo rồi xóa alarm khi log thành PASS."""
        from datetime import datetime
        from auto_import_today_main import run_auto_import_today
        from repositories.auto_import_scheduler_repository import AutoImportSchedulerRepository
        day = datetime.now().strftime('%Y%m%d')
        root = self.base / 'logs'
        folder = root / 'AI-H903' / datetime.now().strftime('%y%m%d')
        folder.mkdir(parents=True)
        AutoImportSchedulerRepository(self.db).save_config(True, '00:00', str(root))
        for result in (8, 1):
            from tests.test_tcp_import import log
            (folder / f'{day}_TCP.txt').write_text(''.join(
                log(serial=f'SN{n}', result='FAIL' if result == 8 else 'PASS',
                    time=f'[12:00:0{n}]', EQPID='AI-H903', SCRAP_CODE='4590', TEST_COUNT='0')
                for n in range(3)), encoding='utf-8')
            with patch('auto_import_today_main.append_auto_import_log'):
                self.assertEqual(run_auto_import_today(self.db), 0)
            self.assertEqual(len(self.repository.load(day, day)), 1 if result == 8 else 0)

    def test_schema_repeat_and_cancel(self):
        """Khởi tạo lặp không mất dữ liệu; engine tôn trọng yêu cầu hủy."""
        self.import_rows([event(i) for i in range(1,4)])
        before=self.alarms()
        initialize_database(self.db)
        self.assertEqual(self.alarms(),before)
        cancel=Event();cancel.set()
        with self.assertRaises(ImportCancelled):
            build_slot_alarm([event(1)],'20260915',dict(continuous_fail_count=3,target_15=70,target_30=75),cancel)


if __name__=='__main__':
    unittest.main()
