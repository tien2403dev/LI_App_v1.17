# """Đọc bằng chứng của đúng alarm; không chạy lại engine bằng cấu hình hiện tại."""
# import json
# from database.connection import connection
#
# FIELDS = ('DATE', 'TIME', 'MODEL', 'LOTNO', 'RESULT', 'SCRAPCODE', 'TEST_COUNT', 'QTY')
# IDENTITY = ('DATE', 'TIME', 'MODEL', 'LOTNO', 'RESULT', 'SCRAPCODE', 'TEST_COUNT', 'SERIAL')
# LEGACY_SQL = '''SELECT id,DATE,TIME,MODEL,LOTNO,RESULT,SCRAPCODE,TEST_COUNT,SERIAL,QTY
#     FROM prime_data WHERE EQP=? AND SLOT=?
#       AND (DATE,TIME)>=(?,?) AND (DATE,TIME)<=(?,?)
#     ORDER BY DATE DESC,TIME DESC,id DESC LIMIT ?'''
#
#
# def boundary(value):
#     date, time = value.split(' ')
#     return date.replace('-', ''), time
#
#
# class AlarmHistoryRepository:
#     def __init__(self, database_path):
#         self.database_path = database_path
#
#     def load(self, expected):
#         # Một read transaction giữ alarm và PRIME nhất quán khi app khác import.
#         with connection(self.database_path, timeout=5) as conn:
#             conn.execute('BEGIN')
#             raw = conn.execute('SELECT * FROM slot_fail_alarm WHERE id=?',
#                                (expected['id'],)).fetchone()
#             if raw is None:
#                 raise ValueError('Alarm đã bị xóa. Bấm Search để tải lại danh sách.')
#             alarm = dict(raw)
#             if alarm['row_version'] != expected['row_version']:
#                 raise ValueError('Alarm đã thay đổi. Bấm Search rồi mở lại lịch sử.')
#             try:
#                 evidence = json.loads(alarm['evidence_json'])
#                 if not isinstance(evidence, dict):
#                     raise ValueError()
#             except (ValueError, TypeError) as error:
#                 raise ValueError('Bằng chứng alarm không hợp lệ. Cần import lại ngày alarm.') from error
#             groups = []
#             for number, run in enumerate(evidence.get('1', []), 1):
#                 size = alarm['continuous_fail_count_used']
#                 label = f'FAIL liên tục cùng Scrap code {size} lần — chuỗi {number}'
#                 groups.append(self._group(conn, alarm, run, size, label, continuous=True))
#             for number, run in enumerate(evidence.get('different_scrap', []), 1):
#                 size = alarm['different_scrap_fail_count_used']
#                 label = f'FAIL liên tục khác Scrap code {size} lần — chuỗi {number}'
#                 groups.append(self._group(conn, alarm, run, size, label, mixed=True))
#             for size in (15, 30):
#                 if str(size) in evidence:
#                     target = alarm[f'target_{size}']
#                     label = f'Yield {size} < {target:.2f}%'
#                     groups.append(self._group(conn, alarm, evidence[str(size)], size, label))
#             if not groups:
#                 raise ValueError('Alarm chưa có bằng chứng lịch sử. Cần import lại ngày alarm.')
#             return dict(eqp=alarm['eqp'], slot=alarm['slot'], groups=groups)
#
#     def _group(self, conn, alarm, evidence, size, label, continuous=False, mixed=False):
#         note = ''
#         try:
#             tests = evidence.get('tests')
#             if tests is None and continuous:
#                 # Alarm cũ chưa lưu test: chỉ đọc phạm vi đã lưu, không tìm chuỗi mới.
#                 tests = [dict(row) for row in conn.execute(LEGACY_SQL,
#                     (alarm['eqp'], alarm['slot'], *boundary(evidence['start']),
#                      *boundary(evidence['end']), size))]
#                 if (len(tests) != size or any(
#                         row['RESULT'] != 'FAIL' or row['MODEL'] not in evidence['models']
#                         or row['SCRAPCODE'] not in evidence['scraps'] for row in tests)
#                         or (tests[0]['DATE'], tests[0]['TIME']) != boundary(evidence['end'])):
#                     raise ValueError('PRIME không còn đủ chuỗi khớp bằng chứng cũ.')
#                 note = ('Alarm cũ: dựng từ PRIME hiện tại trong khoảng đã lưu. '
#                         'Import lại ngày alarm để lưu bằng chứng cố định từng test.')
#             elif tests is not None:
#                 tests = [dict(test) for test in tests]
#                 if any('QTY' not in row for row in tests):
#                     tests = self._legacy_quantities(conn, alarm, tests)
#                     note = 'Alarm cũ: chuỗi đã lưu; QTY đối chiếu từ PRIME hiện tại.'
#             if not tests or len(tests) != size:
#                 raise ValueError(f'Không đủ đúng {size} test trong bằng chứng.')
#             for row in tests:
#                 for field in FIELDS:
#                     row[field]  # Không tự điền số lượng hoặc TEST_COUNT khi thiếu dữ liệu.
#             if continuous and (any(row['RESULT'] != 'FAIL' for row in tests)
#                     or len({(row['MODEL'], row['SCRAPCODE']) for row in tests}) != 1):
#                 raise ValueError('Bằng chứng FAIL liên tiếp không hợp lệ.')
#             if mixed and (any(row['RESULT'] != 'FAIL' or not row['SCRAPCODE'] for row in tests)
#                     or len({row['MODEL'] for row in tests}) != 1
#                     or len({row['SCRAPCODE'] for row in tests}) < 2):
#                 raise ValueError('Bằng chứng FAIL khác Scrap code không hợp lệ.')
#             tests.sort(key=lambda row: (row['DATE'], row['TIME'], row.get('id', 0)), reverse=True)
#             if continuous and evidence.get('count', size) > size:
#                 note += (f" Chuỗi gốc có {evidence['count']} lần FAIL; hiển thị {size} lần "
#                          'liên tiếp kết thúc tại End time của chuỗi đã báo alarm.')
#             return dict(label=label, tests=tests, note=note.strip(), error='')
#         except (ValueError, KeyError, TypeError) as error:
#             return dict(label=label, tests=[], note='',
#                         error=f'{error} Cần import lại ngày alarm; không thay bằng chuỗi khác.')
#
#     @staticmethod
#     def _legacy_quantities(conn, alarm, tests):
#         """Một batch lookup tối đa 30 mốc thời gian bằng idx_prime_slot_time."""
#         if not 1 <= len(tests) <= 30:
#             raise ValueError('Số test của bằng chứng cũ không hợp lệ.')
#         values = ','.join('(?,?,?)' for _ in tests)
#         args = [value for i, test in enumerate(tests)
#                 for value in (i, test['DATE'], test['TIME'])]
#         rows = conn.execute(f'''WITH wanted(n,d,t) AS (VALUES {values})
#             SELECT wanted.n, p.* FROM wanted JOIN prime_data p
#               ON p.EQP=? AND p.SLOT=? AND p.DATE=wanted.d AND p.TIME=wanted.t''',
#             (*args, alarm['eqp'], alarm['slot'])).fetchall()
#         candidates = {}
#         for raw in rows:
#             row = dict(raw)
#             n = row.pop('n')
#             if all(row[key] == tests[n][key] for key in IDENTITY):
#                 candidates.setdefault(n, []).append(row)
#         result = []
#         for n in range(len(tests)):
#             matches = candidates.get(n, [])
#             if len(matches) != 1:
#                 raise ValueError('PRIME đã đổi hoặc có test trùng không thể xác định QTY.')
#             result.append(matches[0])
#         return result

"""Đọc bằng chứng của đúng alarm; không chạy lại engine bằng cấu hình hiện tại."""
import json
from database.connection import connection

FIELDS = ('DATE', 'TIME', 'MODEL', 'LOTNO', 'RESULT', 'SCRAPCODE', 'TEST_COUNT', 'QTY')
IDENTITY = ('DATE', 'TIME', 'MODEL', 'LOTNO', 'RESULT', 'SCRAPCODE', 'TEST_COUNT', 'SERIAL')
LEGACY_SQL = '''SELECT id,DATE,TIME,MODEL,LOTNO,RESULT,SCRAPCODE,TEST_COUNT,SERIAL,QTY
    FROM prime_data WHERE EQP=? AND SLOT=? AND TEST_COUNT=0
      AND (DATE,TIME)>=(?,?) AND (DATE,TIME)<=(?,?)
    ORDER BY DATE DESC,TIME DESC,id DESC LIMIT ?'''


def boundary(value):
    date, time = value.split(' ')
    return date.replace('-', ''), time


class AlarmHistoryRepository:
    def __init__(self, database_path):
        self.database_path = database_path

    def load(self, expected):
        # Một read transaction giữ alarm và PRIME nhất quán khi app khác import.
        with connection(self.database_path, timeout=5) as conn:
            conn.execute('BEGIN')
            raw = conn.execute('SELECT * FROM slot_fail_alarm WHERE id=?',
                               (expected['id'],)).fetchone()
            if raw is None:
                raise ValueError('Alarm đã bị xóa. Bấm Search để tải lại danh sách.')
            alarm = dict(raw)
            if alarm['row_version'] != expected['row_version']:
                raise ValueError('Alarm đã thay đổi. Bấm Search rồi mở lại lịch sử.')
            try:
                evidence = json.loads(alarm['evidence_json'])
                if not isinstance(evidence, dict):
                    raise ValueError()
            except (ValueError, TypeError) as error:
                raise ValueError('Bằng chứng alarm không hợp lệ. Cần import lại ngày alarm.') from error
            groups = []
            for number, run in enumerate(evidence.get('1', []), 1):
                size = alarm['continuous_fail_count_used']
                label = f'FAIL liên tục cùng Scrap code {size} lần — chuỗi {number}'
                groups.append(self._group(conn, alarm, run, size, label, continuous=True))
            for number, run in enumerate(evidence.get('different_scrap', []), 1):
                size = alarm['different_scrap_fail_count_used']
                label = f'FAIL liên tục khác Scrap code {size} lần — chuỗi {number}'
                groups.append(self._group(conn, alarm, run, size, label, mixed=True))
            for size in (15, 30):
                if str(size) in evidence:
                    target = alarm[f'target_{size}']
                    label = f'Yield {size} < {target:.2f}%'
                    groups.append(self._group(conn, alarm, evidence[str(size)], size, label))
            if not groups:
                raise ValueError('Alarm chưa có bằng chứng lịch sử. Cần import lại ngày alarm.')
            return dict(eqp=alarm['eqp'], slot=alarm['slot'], groups=groups,
                        fail_comment=alarm.get('fail_comment') or '')

    def _group(self, conn, alarm, evidence, size, label, continuous=False, mixed=False):
        note = ''
        try:
            tests = evidence.get('tests')
            if tests is None and continuous:
                # Alarm cũ chưa lưu test: chỉ đọc phạm vi đã lưu, không tìm chuỗi mới.
                tests = [dict(row) for row in conn.execute(LEGACY_SQL,
                    (alarm['eqp'], alarm['slot'], *boundary(evidence['start']),
                     *boundary(evidence['end']), size))]
                if (len(tests) != size or any(
                        row['RESULT'] != 'FAIL' or row['MODEL'] not in evidence['models']
                        or row['SCRAPCODE'] not in evidence['scraps'] for row in tests)
                        or (tests[0]['DATE'], tests[0]['TIME']) != boundary(evidence['end'])):
                    raise ValueError('PRIME không còn đủ chuỗi khớp bằng chứng cũ.')
                note = ('Alarm cũ: dựng từ PRIME hiện tại trong khoảng đã lưu. '
                        'Import lại ngày alarm để lưu bằng chứng cố định từng test.')
            elif tests is not None:
                tests = [dict(test) for test in tests]
                if any('QTY' not in row for row in tests):
                    tests = self._legacy_quantities(conn, alarm, tests)
                    note = 'Alarm cũ: chuỗi đã lưu; QTY đối chiếu từ PRIME hiện tại.'
            if not tests or len(tests) != size:
                raise ValueError(f'Không đủ đúng {size} test trong bằng chứng.')
            for row in tests:
                for field in FIELDS:
                    row[field]  # Không tự điền số lượng hoặc TEST_COUNT khi thiếu dữ liệu.
            if (continuous or mixed) and any(row['TEST_COUNT'] != 0 for row in tests):
                raise ValueError('Bằng chứng FAIL liên tiếp có TEST_COUNT khác 0, '
                                 'không hợp lệ theo quy tắc mới.')
            if continuous and (any(row['RESULT'] != 'FAIL' for row in tests)
                    or len({(row['MODEL'], row['SCRAPCODE']) for row in tests}) != 1):
                raise ValueError('Bằng chứng FAIL liên tiếp không hợp lệ.')
            if mixed and (any(row['RESULT'] != 'FAIL' or not row['SCRAPCODE'] for row in tests)
                    or len({row['MODEL'] for row in tests}) != 1
                    or len({row['SCRAPCODE'] for row in tests}) < 2):
                raise ValueError('Bằng chứng FAIL khác Scrap code không hợp lệ.')
            tests.sort(key=lambda row: (row['DATE'], row['TIME'], row.get('id', 0)), reverse=True)
            if continuous and evidence.get('count', size) > size:
                note += (f" Chuỗi gốc có {evidence['count']} lần FAIL; hiển thị {size} lần "
                         'liên tiếp kết thúc tại End time của chuỗi đã báo alarm.')
            return dict(label=label, tests=tests, note=note.strip(), error='')
        except (ValueError, KeyError, TypeError) as error:
            return dict(label=label, tests=[], note='',
                        error=f'{error} Cần import lại ngày alarm; không thay bằng chuỗi khác.')

    @staticmethod
    def _legacy_quantities(conn, alarm, tests):
        """Một batch lookup tối đa 30 mốc thời gian bằng idx_prime_slot_time."""
        if not 1 <= len(tests) <= 30:
            raise ValueError('Số test của bằng chứng cũ không hợp lệ.')
        values = ','.join('(?,?,?)' for _ in tests)
        args = [value for i, test in enumerate(tests)
                for value in (i, test['DATE'], test['TIME'])]
        rows = conn.execute(f'''WITH wanted(n,d,t) AS (VALUES {values})
            SELECT wanted.n, p.* FROM wanted JOIN prime_data p
              ON p.EQP=? AND p.SLOT=? AND p.DATE=wanted.d AND p.TIME=wanted.t''',
            (*args, alarm['eqp'], alarm['slot'])).fetchall()
        candidates = {}
        for raw in rows:
            row = dict(raw)
            n = row.pop('n')
            if all(row[key] == tests[n][key] for key in IDENTITY):
                candidates.setdefault(n, []).append(row)
        result = []
        for n in range(len(tests)):
            matches = candidates.get(n, [])
            if len(matches) != 1:
                raise ValueError('PRIME đã đổi hoặc có test trùng không thể xác định QTY.')
            result.append(matches[0])
        return result
