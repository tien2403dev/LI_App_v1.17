# """Duyệt ngược lịch sử một EQP/Slot, lấy mọi TEST_COUNT và nối xuyên ngày."""
# import json
# from collections import deque
# from domain.prime import check_cancel
#
#
# HISTORY_FIELDS = ('id', 'DATE', 'TIME', 'MODEL', 'LOTNO', 'RESULT',
#                   'SCRAPCODE', 'TEST_COUNT', 'SERIAL', 'QTY')
#
#
# def history_test(row):
#     """Snapshot PRIME: ID để phân biệt các test trùng giây, giữ nguyên TEST_COUNT/QTY."""
#     return {key: row[key] for key in HISTORY_FIELDS}
#
#
# def event_time(row):
#     """Ghép thời điểm log; đây là ENDTIME trong PRIME, không phải giờ bắt đầu máy."""
#     return f"{row['DATE'][:4]}-{row['DATE'][4:6]}-{row['DATE'][6:]} {row['TIME']}"
#
#
# def build_slot_alarm(events, alarm_date, config, cancel=None):
#     """Tính một alarm từ cursor DATE/TIME/id giảm dần, không đọc ngày tương lai."""
#     queues, yields, evidence = {}, {15: None, 30: None}, {}
#     fail_run = None
#     runs = []
#     threshold = config['continuous_fail_count']
#     mixed_threshold = config.get('different_scrap_fail_count', 3)
#     mixed_queue = deque(maxlen=mixed_threshold)
#     mixed_runs = []
#     mixed_found = False
#     latest_results = []
#     skip_yield = {15: False, 30: False}
#
#     def finish_run():
#         """Ghi chuỗi FAIL đầy đủ nếu có test ngày đích và đủ ngưỡng."""
#         if fail_run and fail_run['today'] and fail_run['count'] >= threshold:
#             runs.append({k: sorted(v) if isinstance(v, set) else v
#                          for k, v in fail_run.items() if k not in ('today', 'key')})
#
#     for index, raw in enumerate(events):
#         if index % 1000 == 0:
#             check_cancel(cancel)
#         row = dict(raw)
#         # Cổng phục hồi của toàn slot: chỉ xét prefix mới nhất, không trượt về lịch sử.
#         if len(latest_results) < 10:
#             latest_results.append(row['RESULT'])
#             for size, recent in ((15, 6), (30, 10)):
#                 if len(latest_results) == recent:
#                     skip_yield[size] = all(value == 'PASS' for value in latest_results)
#
#         # Chuỗi cùng Model nhưng có >= 2 Scrap code trong đúng N test liên tục.
#         if (row['RESULT'] != 'FAIL' or not row['SCRAPCODE']
#                 or (mixed_queue and mixed_queue[-1]['MODEL'] != row['MODEL'])):
#             mixed_queue.clear()
#             mixed_found = False
#         if row['RESULT'] == 'FAIL' and row['SCRAPCODE']:
#             mixed_queue.append(row)
#             if (not mixed_found and len(mixed_queue) == mixed_threshold
#                     and mixed_queue[0]['DATE'] == alarm_date
#                     and len({test['SCRAPCODE'] for test in mixed_queue}) > 1):
#                 tests = list(mixed_queue)
#                 mixed_runs.append(dict(
#                     count=mixed_threshold, start=event_time(tests[-1]), end=event_time(tests[0]),
#                     models=[row['MODEL']], scraps=sorted({t['SCRAPCODE'] for t in tests}),
#                     lots=sorted({t['LOTNO'] for t in tests}),
#                     tests=[history_test(t) for t in tests]))
#                 mixed_found = True
#         # EQP/Slot của cursor đã được giới hạn; không bỏ qua MODEL khác ở quy tắc 1.
#         key = (row['MODEL'], row['SCRAPCODE']) if row['RESULT'] == 'FAIL' and row['SCRAPCODE'] else None
#         if fail_run and key != fail_run['key']:
#             finish_run()
#             fail_run = None
#         if key is not None:
#             if fail_run is None:
#                 fail_run = dict(key=key, count=0, start=event_time(row),
#                                 end=event_time(row), today=False,
#                                 models={row['MODEL']}, scraps={row['SCRAPCODE']}, lots=set(), tests=[])
#             if len(fail_run['tests']) < threshold:
#                 fail_run['tests'].append(history_test(row))
#             fail_run['count'] += 1
#             fail_run['start'] = event_time(row)
#             fail_run['today'] |= row['DATE'] == alarm_date
#             fail_run['lots'].add(row['LOTNO'])
#
#         model = row['MODEL']
#         # Chỉ giữ Model xuất hiện ngày đích; Model lịch sử khác không thể có endpoint hôm nay.
#         if row['DATE'] == alarm_date:
#             queues.setdefault(model, deque(maxlen=30))
#         if model in queues:
#             q = queues[model]
#             q.append(row)
#             for size in (15, 30):
#                 if skip_yield[size] or len(q) < size:
#                     continue
#                 window = list(q)[-size:]
#                 end = window[0]
#                 if end['DATE'] != alarm_date:
#                     continue
#                 order = (end['TIME'], end['id'])
#                 old = yields[size]
#                 if old is not None and order <= old['order']:
#                     continue
#                 passed = sum(e['RESULT'] == 'PASS' for e in window)
#                 if passed * 100 < config[f'target_{size}'] * size:
#                     yields[size] = dict(order=order, value=passed * 100 / size)
#                     evidence[str(size)] = dict(
#                         start=event_time(window[-1]), end=event_time(end),
#                         passed=passed, total=size, model=model,
#                         lots=sorted({e['LOTNO'] for e in window}),
#                         tests=[history_test(e) for e in window])
#         # Mọi cửa sổ kết thúc trong ngày đã đi qua, chuỗi FAIL nối qua ranh giới đã đóng.
#         if (row['DATE'] < alarm_date and not (fail_run and fail_run['today'])
#                 and not (mixed_queue and mixed_queue[0]['DATE'] == alarm_date)):
#             if all(len(q) == 30 and q[0]['DATE'] < alarm_date for q in queues.values()):
#                 break
#     finish_run()
#     check_cancel(cancel)
#     if not runs and not mixed_runs and not any(yields.values()):
#         return None
#     comments, models, lots, scraps = [], set(), set(), set()
#     if runs:
#         comments.append(f"FAIL liên tiếp ≥ {threshold} lần cùng Scrapcode & Model")
#         for run in runs:
#             models.update(run['models'])
#             lots.update(run['lots'])
#             scraps.update(run['scraps'])
#         evidence['1'] = runs
#     if mixed_runs:
#         comments.append(f"FAIL liên tục ≥ {mixed_threshold} lần khác Scrap code & cùng Model")
#         evidence['different_scrap'] = mixed_runs
#         for run in mixed_runs:
#             models.update(run['models'])
#             lots.update(run['lots'])
#             scraps.update(run['scraps'])
#     for size in (15, 30):
#         if yields[size] is not None:
#             comments.append(f"Yield {size} < {config[f'target_{size}']:.2f}%")
#             models.add(evidence[str(size)]['model'])
#             lots.update(evidence[str(size)]['lots'])
#     # Các run thu được theo thứ tự mới -> cũ. Ưu tiên một cặp thời gian 1, 2, 3.
#     chosen = (runs[0] if runs else mixed_runs[0] if mixed_runs
#               else evidence['15'] if yields[15] else evidence['30'])
#     return dict(alarm_date=alarm_date, fail_comment=' | '.join(comments),
#                 start_datetime=chosen['start'], end_datetime=chosen['end'],
#                 yield_15=yields[15]['value'] if yields[15] else None,
#                 yield_30=yields[30]['value'] if yields[30] else None,
#                 target_15=config['target_15'], target_30=config['target_30'],
#                 continuous_fail_count_used=threshold,
#                 different_scrap_fail_count_used=mixed_threshold,
#                 scrap_codes=','.join(sorted(scraps)), lotids=','.join(sorted(lots)),
#                 models=','.join(sorted(models)), evidence_json=json.dumps(evidence, ensure_ascii=False))

"""Duyệt ngược lịch sử EQP/Slot; chuỗi FAIL chỉ xét TEST_COUNT=0, Yield giữ nguyên."""
import json
from collections import deque
from domain.prime import check_cancel


HISTORY_FIELDS = ('id', 'DATE', 'TIME', 'MODEL', 'LOTNO', 'RESULT',
                  'SCRAPCODE', 'TEST_COUNT', 'SERIAL', 'QTY')


def history_test(row):
    """Snapshot PRIME: ID để phân biệt các test trùng giây, giữ nguyên TEST_COUNT/QTY."""
    return {key: row[key] for key in HISTORY_FIELDS}


def event_time(row):
    """Ghép thời điểm log; đây là ENDTIME trong PRIME, không phải giờ bắt đầu máy."""
    return f"{row['DATE'][:4]}-{row['DATE'][4:6]}-{row['DATE'][6:]} {row['TIME']}"


def build_slot_alarm(events, alarm_date, config, cancel=None, window_start=None):
    """Tính một alarm từ cursor DATE/TIME/id giảm dần, không đọc ngày tương lai."""
    window_start = window_start or alarm_date
    queues, yields, evidence = {}, {15: None, 30: None}, {}
    fail_run = None
    runs = []
    threshold = config['continuous_fail_count']
    mixed_threshold = config.get('different_scrap_fail_count', 3)
    mixed_queue = deque(maxlen=mixed_threshold)
    mixed_runs = []
    mixed_found = False
    latest_results = []
    skip_yield = {15: False, 30: False}

    def finish_run():
        """Ghi chuỗi FAIL đầy đủ nếu có test ngày đích và đủ ngưỡng."""
        if fail_run and fail_run['today'] and fail_run['count'] >= threshold:
            runs.append({k: sorted(v) if isinstance(v, set) else v
                         for k, v in fail_run.items() if k not in ('today', 'key')})

    for index, raw in enumerate(events):
        if index % 1000 == 0:
            check_cancel(cancel)
        row = dict(raw)
        # Cổng phục hồi của toàn slot: chỉ xét prefix mới nhất, không trượt về lịch sử.
        if len(latest_results) < 8:
            latest_results.append(row['RESULT'])
            for size, recent in ((15, 8), (30, 8)):
                if len(latest_results) == recent:
                    skip_yield[size] = all(value == 'PASS' for value in latest_results)

        # Bỏ qua retest chỉ cho hai quy tắc liên tiếp; Yield vẫn dùng mọi test.
        if row['TEST_COUNT'] == 0:
            # Chuỗi cùng Model nhưng có >= 2 Scrap code trong đúng N test liên tục.
            if (row['RESULT'] != 'FAIL' or not row['SCRAPCODE']
                    or (mixed_queue and mixed_queue[-1]['MODEL'] != row['MODEL'])):
                mixed_queue.clear()
                mixed_found = False
            if row['RESULT'] == 'FAIL' and row['SCRAPCODE']:
                mixed_queue.append(row)
                if (not mixed_found and len(mixed_queue) == mixed_threshold
                        and window_start <= mixed_queue[0]['DATE'] <= alarm_date
                        and len({test['SCRAPCODE'] for test in mixed_queue}) > 1):
                    tests = list(mixed_queue)
                    mixed_runs.append(dict(
                        count=mixed_threshold, start=event_time(tests[-1]), end=event_time(tests[0]),
                        models=[row['MODEL']], scraps=sorted({t['SCRAPCODE'] for t in tests}),
                        lots=sorted({t['LOTNO'] for t in tests}),
                        tests=[history_test(t) for t in tests]))
                    mixed_found = True
            # EQP/Slot của cursor đã được giới hạn; không bỏ qua MODEL khác ở quy tắc 1.
            key = (row['MODEL'], row['SCRAPCODE']) if row['RESULT'] == 'FAIL' and row['SCRAPCODE'] else None
            if fail_run and key != fail_run['key']:
                finish_run()
                fail_run = None
            if key is not None:
                if fail_run is None:
                    fail_run = dict(key=key, count=0, start=event_time(row),
                                    end=event_time(row), today=False,
                                    models={row['MODEL']}, scraps={row['SCRAPCODE']}, lots=set(), tests=[])
                if len(fail_run['tests']) < threshold:
                    fail_run['tests'].append(history_test(row))
                fail_run['count'] += 1
                fail_run['start'] = event_time(row)
                fail_run['today'] |= window_start <= row['DATE'] <= alarm_date
                fail_run['lots'].add(row['LOTNO'])

        model = row['MODEL']
        # Chỉ giữ Model xuất hiện ngày đích; Model lịch sử khác không thể có endpoint hôm nay.
        if window_start <= row['DATE'] <= alarm_date:
            queues.setdefault(model, deque(maxlen=30))
        if model in queues:
            q = queues[model]
            q.append(row)
            for size in (15, 30):
                if skip_yield[size] or len(q) < size:
                    continue
                window = list(q)[-size:]
                end = window[0]
                if not window_start <= end['DATE'] <= alarm_date:
                    continue
                order = (end['DATE'], end['TIME'], end['id'])
                old = yields[size]
                if old is not None and order <= old['order']:
                    continue
                passed = sum(e['RESULT'] == 'PASS' for e in window)
                if passed * 100 < config[f'target_{size}'] * size:
                    yields[size] = dict(order=order, value=passed * 100 / size)
                    evidence[str(size)] = dict(
                        start=event_time(window[-1]), end=event_time(end),
                        passed=passed, total=size, model=model,
                        lots=sorted({e['LOTNO'] for e in window}),
                        tests=[history_test(e) for e in window])
        # Mọi cửa sổ kết thúc trong ngày đã đi qua, chuỗi FAIL nối qua ranh giới đã đóng.
        if (row['DATE'] < window_start and not (fail_run and fail_run['today'])
                and not (mixed_queue and window_start <= mixed_queue[0]['DATE'] <= alarm_date)):
            if all(len(q) == 30 and q[0]['DATE'] < window_start for q in queues.values()):
                break
    finish_run()
    check_cancel(cancel)
    if not runs and not mixed_runs and not any(yields.values()):
        return None
    comments, models, lots, scraps = [], set(), set(), set()
    if runs:
        comments.append(f"FAIL liên tiếp ≥ {threshold} lần cùng Scrapcode & Model")
        for run in runs:
            models.update(run['models'])
            lots.update(run['lots'])
            scraps.update(run['scraps'])
        evidence['1'] = runs
    if mixed_runs:
        comments.append(f"FAIL liên tục ≥ {mixed_threshold} lần khác Scrap code & cùng Model")
        evidence['different_scrap'] = mixed_runs
        for run in mixed_runs:
            models.update(run['models'])
            lots.update(run['lots'])
            scraps.update(run['scraps'])
    for size in (15, 30):
        if yields[size] is not None:
            comments.append(f"Yield {size} < {config[f'target_{size}']:.2f}%")
            models.add(evidence[str(size)]['model'])
            lots.update(evidence[str(size)]['lots'])
    # Các run thu được theo thứ tự mới -> cũ. Ưu tiên một cặp thời gian 1, 2, 3.
    chosen = (runs[0] if runs else mixed_runs[0] if mixed_runs
              else evidence['15'] if yields[15] else evidence['30'])
    return dict(alarm_date=alarm_date, fail_comment=' | '.join(comments),
                start_datetime=chosen['start'], end_datetime=chosen['end'],
                yield_15=yields[15]['value'] if yields[15] else None,
                yield_30=yields[30]['value'] if yields[30] else None,
                target_15=config['target_15'], target_30=config['target_30'],
                continuous_fail_count_used=threshold,
                different_scrap_fail_count_used=mixed_threshold,
                scrap_codes=','.join(sorted(scraps)), lotids=','.join(sorted(lots)),
                models=','.join(sorted(models)), evidence_json=json.dumps(evidence, ensure_ascii=False))
