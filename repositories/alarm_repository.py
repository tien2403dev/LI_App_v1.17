# """Lưu Alarm nguyên tử với PRIME; cập nhật kết quả máy và bảo toàn các trường xử lý khi import lại."""
# import sqlite3
# from datetime import datetime
# from database.connection import connection
# from domain.alarm import STATUSES, TRACKING_FIELDS
# from domain.prime import check_cancel
# from services.alarm_builder import build_slot_alarm
#
#
# class AlarmRepository:
#     def __init__(self, database_path):
#         """Giữ đường dẫn; mỗi tác vụ mở connection của chính thread đó."""
#         self.database_path = database_path
#
#     @staticmethod
#     def sync_import_dates(conn, dates, progress, cancel=None):
#         """Tính lại ngày nhập trên connection PRIME, không commit riêng; chỉ cập nhật trường máy của alarm còn vi phạm."""
#         config = dict(conn.execute('SELECT * FROM machine_slot_yield_config WHERE id=1').fetchone())
#         created = removed = updated = 0
#         for date in sorted(set(dates)):
#             # Bao gồm alarm cũ mà slot đã biến mất khỏi PRIME mới.
#             slots = conn.execute('''SELECT EQP, SLOT FROM prime_data WHERE DATE=?
#                 UNION SELECT eqp, slot FROM slot_fail_alarm WHERE alarm_date=?
#                 ORDER BY 1,2''', (date, date)).fetchall()
#             for number, slot in enumerate(slots, 1):
#                 check_cancel(cancel)
#                 eqp, slot_no = slot
#                 old = conn.execute('SELECT id FROM slot_fail_alarm WHERE alarm_date=? AND eqp=? AND slot=?',
#                                    (date, eqp, slot_no)).fetchone()
#                 has_today = conn.execute('SELECT 1 FROM prime_data WHERE DATE=? AND EQP=? AND SLOT=? LIMIT 1',
#                                          (date, eqp, slot_no)).fetchone()
#                 alarm = None
#                 if has_today:
#                     cursor = conn.execute('''SELECT id,DATE,TIME,MODEL,LOTNO,RESULT,SCRAPCODE,
#                         TEST_COUNT,SERIAL FROM prime_data
#                         WHERE EQP=? AND SLOT=? AND DATE<=?
#                         ORDER BY DATE DESC,TIME DESC,id DESC''', (eqp, slot_no, date))
#                     try:
#                         alarm = build_slot_alarm(cursor, date, config, cancel)
#                     finally:
#                         cursor.close()
#                 if old and alarm:
#                     # Chỉ cập nhật nhóm máy tính đến Model và bằng chứng kỹ thuật.
#                     # Không ghi Status, Date complete hoặc bất kỳ trường xử lý nào.
#                     fields = (
#                         'fail_comment', 'start_datetime', 'end_datetime',
#                         'yield_15', 'target_15', 'yield_30', 'target_30',
#                         'continuous_fail_count_used', 'different_scrap_fail_count_used', 'scrap_codes', 'lotids',
#                         'models', 'evidence_json',
#                     )
#                     assignments = ','.join(f'{field}=?' for field in fields)
#                     now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#                     conn.execute(
#                         f'UPDATE slot_fail_alarm SET {assignments}, updated_at=?, '
#                         'row_version=row_version+1 WHERE id=?',
#                         (*[alarm[field] for field in fields], now, old['id']),
#                     )
#                     updated += 1
#                 elif old:
#                     conn.execute('DELETE FROM slot_fail_alarm WHERE id=?', (old['id'],))
#                     removed += 1
#                 elif alarm:
#                     now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#                     alarm.update(eqp=eqp, slot=slot_no, created_at=now, updated_at=now)
#                     fields = ','.join(alarm)
#                     conn.execute(f"INSERT INTO slot_fail_alarm({fields}) VALUES({','.join('?' for _ in alarm)})",
#                                  tuple(alarm.values()))
#                     created += 1
#                 if number == 1 or number % 20 == 0 or number == len(slots):
#                     progress(f'Đang tính Alarm {date}: {number}/{len(slots)} slot (chưa commit)')
#         progress(f'Alarm: tạo {created}, cập nhật {updated}, xóa {removed} (chưa commit)')
#
#     def load(self, date_from, date_to):
#         """Lọc ngày Alarm độc lập Tier/EQP/Model của bộ lọc thống kê."""
#         with connection(self.database_path) as conn:
#             return [dict(row) for row in conn.execute('''SELECT * FROM slot_fail_alarm
#                 WHERE alarm_date BETWEEN ? AND ? ORDER BY alarm_date DESC,end_datetime DESC,eqp,slot''',
#                 (date_from, date_to))]
#
#     def update_tracking(self, expected, field, value):
#         """Lưu một ô sau kiểm tra version; không tự retry hay ghi đè người khác."""
#         if field not in TRACKING_FIELDS:
#             raise ValueError('Cột Alarm không được phép chỉnh sửa.')
#         value = str(value)
#         if field == 'status' and value not in STATUSES:
#             raise ValueError('Status không hợp lệ.')
#         try:
#             with connection(self.database_path, timeout=0) as conn:
#                 conn.execute('BEGIN IMMEDIATE')
#                 try:
#                     row = conn.execute('SELECT * FROM slot_fail_alarm WHERE id=?', (expected['id'],)).fetchone()
#                     if row is None:
#                         raise ValueError('Alarm đã bị xóa khi import lại. Hãy bấm Search để tải lại.')
#                     latest = dict(row)
#                     if latest['row_version'] != expected['row_version']:
#                         conn.rollback()
#                         return latest, True
#                     if latest[field] != value:
#                         latest[field] = value
#                         if field == 'status':
#                             latest['date_complete'] = (datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#                                                        if value == STATUSES[2] else '')
#                         latest['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#                         conn.execute(f'''UPDATE slot_fail_alarm SET {field}=?,date_complete=?,
#                             updated_at=?,row_version=row_version+1 WHERE id=? AND row_version=?''',
#                             (value, latest['date_complete'], latest['updated_at'],
#                              expected['id'], expected['row_version']))
#                         latest['row_version'] += 1
#                     conn.commit()
#                     return latest, False
#                 except BaseException:
#                     conn.rollback()
#                     raise
#         except sqlite3.OperationalError as error:
#             if (getattr(error, 'sqlite_errorcode', 0) & 255) in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED) or 'locked' in str(error).lower():
#                 raise ValueError('Database đang được cập nhật bởi tác vụ/người dùng khác. Chưa lưu thay đổi; vui lòng thử lại.') from error
#             raise
"""Lưu Alarm nguyên tử với PRIME; cập nhật kết quả máy và bảo toàn các trường xử lý khi import lại."""
import sqlite3
from datetime import datetime
from database.connection import connection
from domain.alarm import CHECK_RESULTS, COLUMNS, STATUSES, TRACKING_FIELDS
from domain.prime import check_cancel
from services.alarm_builder import build_slot_alarm


class AlarmRepository:
    def __init__(self, database_path):
        """Giữ đường dẫn; mỗi tác vụ mở connection của chính thread đó."""
        self.database_path = database_path

    @staticmethod
    def sync_import_dates(conn, dates, progress, cancel=None):
        """Tính lại ngày nhập trên connection PRIME, không commit riêng; chỉ cập nhật trường máy của alarm còn vi phạm."""
        config = dict(conn.execute('SELECT * FROM machine_slot_yield_config WHERE id=1').fetchone())
        created = removed = updated = 0
        for date in sorted(set(dates)):
            # Bao gồm alarm cũ mà slot đã biến mất khỏi PRIME mới.
            slots = conn.execute('''SELECT EQP, SLOT FROM prime_data WHERE DATE=?
                UNION SELECT eqp, slot FROM slot_fail_alarm WHERE alarm_date=?
                ORDER BY 1,2''', (date, date)).fetchall()
            for number, slot in enumerate(slots, 1):
                check_cancel(cancel)
                eqp, slot_no = slot
                old = conn.execute('SELECT id FROM slot_fail_alarm WHERE alarm_date=? AND eqp=? AND slot=?',
                                   (date, eqp, slot_no)).fetchone()
                has_today = conn.execute('SELECT 1 FROM prime_data WHERE DATE=? AND EQP=? AND SLOT=? LIMIT 1',
                                         (date, eqp, slot_no)).fetchone()
                alarm = None
                if has_today:
                    cursor = conn.execute('''SELECT id,DATE,TIME,MODEL,LOTNO,RESULT,SCRAPCODE,
                        TEST_COUNT,SERIAL,QTY FROM prime_data
                        WHERE EQP=? AND SLOT=? AND DATE<=?
                        ORDER BY DATE DESC,TIME DESC,id DESC''', (eqp, slot_no, date))
                    try:
                        alarm = build_slot_alarm(cursor, date, config, cancel)
                    finally:
                        cursor.close()
                if old and alarm:
                    # Chỉ cập nhật nhóm máy tính đến Model và bằng chứng kỹ thuật.
                    # Không ghi Status, Date complete hoặc bất kỳ trường xử lý nào.
                    fields = (
                        'fail_comment', 'start_datetime', 'end_datetime',
                        'yield_15', 'target_15', 'yield_30', 'target_30',
                        'continuous_fail_count_used', 'different_scrap_fail_count_used', 'scrap_codes', 'lotids',
                        'models', 'evidence_json',
                    )
                    assignments = ','.join(f'{field}=?' for field in fields)
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    conn.execute(
                        f'UPDATE slot_fail_alarm SET {assignments}, updated_at=?, '
                        'row_version=row_version+1 WHERE id=?',
                        (*[alarm[field] for field in fields], now, old['id']),
                    )
                    updated += 1
                elif old:
                    conn.execute('DELETE FROM slot_fail_alarm WHERE id=?', (old['id'],))
                    removed += 1
                elif alarm:
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    alarm.update(eqp=eqp, slot=slot_no, created_at=now, updated_at=now)
                    fields = ','.join(alarm)
                    conn.execute(f"INSERT INTO slot_fail_alarm({fields}) VALUES({','.join('?' for _ in alarm)})",
                                 tuple(alarm.values()))
                    created += 1
                if number == 1 or number % 20 == 0 or number == len(slots):
                    progress(f'Đang tính Alarm {date}: {number}/{len(slots)} slot (chưa commit)')
        progress(f'Alarm: tạo {created}, cập nhật {updated}, xóa {removed} (chưa commit)')

    @staticmethod
    def sync_import_monitors(conn, affected, cutoff, progress, cancel=None):
        """Tính Monitor cho slot/ngày quá khứ vừa thay thế, dùng transaction import."""
        if not affected:
            return 0
        rows = conn.execute(
            "SELECT id,eqp,slot,date_complete,monitor_day1,monitor_day2,"
            "monitor_day3 FROM slot_fail_alarm WHERE status=?",
            (STATUSES[2],)).fetchall()
        cache = {}
        updated = 0
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for row in rows:
            check_cancel(cancel)
            dates = affected.get((row['eqp'], row['slot']))
            if not dates:
                continue
            try:
                completed = datetime.fromisoformat(
                    str(row['date_complete']).strip()).strftime('%Y%m%d')
            except (ValueError, TypeError):
                continue
            if not any(completed < day < cutoff for day in dates):
                continue
            key = (row['eqp'], row['slot'], completed)
            if key not in cache:
                days = conn.execute("""
                    SELECT DATE,
                        CASE WHEN MIN(CASE WHEN RESULT='PASS' THEN 1 ELSE 0 END)=1
                            THEN 'PASS' ELSE 'FAIL' END AS result
                    FROM prime_data
                    WHERE EQP=? AND SLOT=? AND DATE>? AND DATE<?
                    GROUP BY DATE ORDER BY DATE LIMIT 3
                """, (*key, cutoff)).fetchall()
                results = [day['result'] for day in days]
                cache[key] = tuple(results + [''] * (3-len(results)))
            values = cache[key]
            previous = tuple(row[f'monitor_day{i}'] for i in (1, 2, 3))
            if values != previous:
                conn.execute("""
                    UPDATE slot_fail_alarm SET monitor_day1=?,monitor_day2=?,
                        monitor_day3=?,updated_at=?,row_version=row_version+1 WHERE id=?
                """, (*values, now, row['id']))
                updated += 1
        progress(f'Monitor: cập nhật {updated} Alarm theo ngày import (chưa commit)')
        return updated

    def load(self, date_from, date_to, include_evidence=True):
        """Lọc ngày Alarm độc lập Tier/EQP/Model của bộ lọc thống kê."""
        columns = '*' if include_evidence else ','.join(
            ['id', 'row_version'] + [field for _, field in COLUMNS if field])
        with connection(self.database_path) as conn:
            return [dict(row) for row in conn.execute(f'''SELECT {columns} FROM slot_fail_alarm
                WHERE alarm_date BETWEEN ? AND ? ORDER BY alarm_date DESC,end_datetime DESC,eqp,slot''',
                (date_from, date_to))]

    def update_tracking(self, expected, field, value):
        """Lưu một ô sau kiểm tra version; không tự retry hay ghi đè người khác."""
        if field not in TRACKING_FIELDS:
            raise ValueError('Cột Alarm không được phép chỉnh sửa.')
        value = str(value)
        if field == 'status' and value not in STATUSES:
            raise ValueError('Status không hợp lệ.')
        if field in ('quick_check_result', 'cal_check_result') and value not in CHECK_RESULTS:
            raise ValueError('Kết quả kiểm tra chỉ được chọn PASS hoặc FAIL.')
        try:
            with connection(self.database_path, timeout=0) as conn:
                conn.execute('BEGIN IMMEDIATE')
                try:
                    row = conn.execute('SELECT * FROM slot_fail_alarm WHERE id=?', (expected['id'],)).fetchone()
                    if row is None:
                        raise ValueError('Alarm đã bị xóa khi import lại. Hãy bấm Search để tải lại.')
                    latest = dict(row)
                    if latest['row_version'] != expected['row_version']:
                        conn.rollback()
                        return latest, True
                    if latest[field] != value:
                        latest[field] = value
                        if field == 'status':
                            latest['date_complete'] = (datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                                       if value == STATUSES[2] else '')
                            # Mỗi lần đổi Status bắt đầu/kết thúc một đợt xử lý mới.
                            for monitor in ('monitor_day1', 'monitor_day2', 'monitor_day3'):
                                latest[monitor] = ''
                        latest['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        conn.execute(f'''UPDATE slot_fail_alarm SET {field}=?,date_complete=?,
                            monitor_day1=?,monitor_day2=?,monitor_day3=?,
                            updated_at=?,row_version=row_version+1 WHERE id=? AND row_version=?''',
                            (value, latest['date_complete'],
                             latest['monitor_day1'], latest['monitor_day2'], latest['monitor_day3'],
                             latest['updated_at'], expected['id'], expected['row_version']))
                        latest['row_version'] += 1
                    conn.commit()
                    return latest, False
                except BaseException:
                    conn.rollback()
                    raise
        except sqlite3.OperationalError as error:
            if (getattr(error, 'sqlite_errorcode', 0) & 255) in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED) or 'locked' in str(error).lower():
                raise ValueError('Database đang được cập nhật bởi tác vụ/người dùng khác. Chưa lưu thay đổi; vui lòng thử lại.') from error
            raise
