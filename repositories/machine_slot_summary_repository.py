"""Machine/slot data for the explicitly applied inclusive date range."""
from datetime import datetime, timedelta
from database.connection import connection
from repositories.report_repository import ReportDetailRow


def _load_day(conn, day, cancel):
    """Cache only aggregates and ten newest tests per slot, never all test rows."""
    if cancel.is_set():
        raise InterruptedError('Cancelled')
    stats = [dict(r) for r in conn.execute('''
        SELECT EQP AS eqp,SLOT AS slot,DATE AS date,COUNT(*) AS total,
               SUM(RESULT='PASS') AS passed,SUM(RESULT='FAIL') AS failed
        FROM prime_data WHERE DATE=? GROUP BY EQP,SLOT''', (day,))]
    recent = {}
    for row in conn.execute('''
        SELECT EQP,SLOT,DATE,TIME,RESULT,TEST_COUNT,id FROM (
            SELECT EQP,SLOT,DATE,TIME,RESULT,TEST_COUNT,id,
                ROW_NUMBER() OVER (PARTITION BY EQP,SLOT ORDER BY TIME DESC,id DESC) AS rn
            FROM prime_data WHERE DATE=?) WHERE rn<=10
        ORDER BY EQP,SLOT,TIME DESC,id DESC''', (day,)):
        if cancel.is_set():
            raise InterruptedError('Cancelled')
        item = dict(row)
        key = (item.pop('EQP'), item.pop('SLOT'))
        recent.setdefault(key, []).append(item)
    return dict(stats=stats, recent=recent)



def _recent_alarm_slots(conn, candidates, now, cancel, previous=None):
    """Recheck saved alarm slots using only today and the two previous dates."""
    from services.alarm_builder import build_slot_alarm
    first = (now.date() - timedelta(days=2)).strftime('%Y%m%d')
    last = now.strftime('%Y%m%d')
    config = dict(conn.execute('SELECT * FROM machine_slot_yield_config WHERE id=1').fetchone())
    signatures = []
    reliable = True
    for offset in range(3):
        day = (now.date() - timedelta(days=offset)).strftime('%Y%m%d')
        revision = conn.execute("""SELECT imported_at,batch_id,row_count FROM data_import_status
            WHERE data_type='PRIME' AND DATE=?""", (day,)).fetchone()
        if revision is None:
            exists = conn.execute('SELECT 1 FROM prime_data WHERE DATE=? LIMIT 1', (day,)).fetchone()
            reliable &= exists is None
            signatures.append((day, None))
        else:
            signatures.append((day, tuple(revision)))
    key = (first, last, tuple(sorted(candidates)), tuple(signatures),
           tuple(config[name] for name in ('target_15', 'target_30',
                 'continuous_fail_count', 'different_scrap_fail_count')))
    if reliable and previous and previous['key'] == key:
        return previous
    qualified = set()
    for eqp, slot in sorted(candidates):
        if cancel.is_set():
            raise InterruptedError('Cancelled')
        cursor = conn.execute("""SELECT id,DATE,TIME,MODEL,LOTNO,RESULT,SCRAPCODE,
                TEST_COUNT,SERIAL,QTY FROM prime_data
            WHERE EQP=? AND SLOT=? AND DATE BETWEEN ? AND ?
            ORDER BY DATE DESC,TIME DESC,id DESC""", (eqp, slot, first, last))
        try:
            if build_slot_alarm(cursor, last, config, cancel, window_start=first) is not None:
                qualified.add((eqp, slot))
        finally:
            cursor.close()
    return dict(key=key, qualified=qualified, date_range=(first, last))


def load_machine_slot_summary(database_path, date_from, date_to, cancel, now=None, cache=None):
    """Revalidate import revisions and reuse unchanged day snapshots in this session.

    PRIME imports replace whole dates and update data_import_status atomically.
    Re-read a changed date, including historical reimports, instead of appending
    rows by timestamp (which would miss corrections and duplicate replaced rows).
    Legacy days without metadata are deliberately never trusted across reads.
    The caller owns the cache; errors/cancellation leave its old snapshot intact.
    """
    first = datetime.strptime(date_from, '%Y%m%d').date()
    last = datetime.strptime(date_to, '%Y%m%d').date()
    if first > last:
        raise ValueError('From phải nhỏ hơn hoặc bằng To.')
    now = now or datetime.now()
    days = []
    day = first
    while day <= last:
        if cancel.is_set():
            raise InterruptedError('Cancelled')
        days.append(day.strftime('%Y%m%d'))
        day += timedelta(days=1)
    # Replacing the DB file must not reuse snapshots of a different database.
    from pathlib import Path
    path = Path(database_path).resolve()
    stat = path.stat()
    identity = (str(path), stat.st_dev, stat.st_ino)
    old_days = (cache or {}).get('days', {}) if (cache or {}).get('identity') == identity else {}
    next_days = dict(old_days)
    refreshed = []
    with connection(database_path, timeout=2) as conn:
        conn.execute('PRAGMA query_only=ON')
        conn.set_progress_handler(lambda: int(cancel.is_set()), 1000)
        conn.execute('BEGIN')
        revisions = {r['DATE']: (r['imported_at'], r['batch_id'], r['row_count'])
                     for r in conn.execute('''SELECT DATE,imported_at,batch_id,row_count
                         FROM data_import_status WHERE data_type='PRIME'
                         AND DATE BETWEEN ? AND ?''', (date_from, date_to))}
        for day in days:
            if cancel.is_set():
                raise InterruptedError('Cancelled')
            revision = revisions.get(day)
            if revision is None:
                # Also detects new data in previously empty dates without metadata.
                exists = conn.execute('SELECT 1 FROM prime_data WHERE DATE=? LIMIT 1', (day,)).fetchone()
                if exists is None:
                    revision = ('empty',)
            previous = old_days.get(day)
            if previous is not None and revision is not None and previous['revision'] == revision:
                continue
            data = _load_day(conn, day, cancel)
            next_days[day] = dict(revision=revision, **data)
            refreshed.append(day)
        # Alarm tracking/evidence may change independently from PRIME imports.
        alarms, daily_comments = {}, {}
        for alarm in conn.execute('''SELECT eqp,slot,alarm_date,fail_comment
                FROM slot_fail_alarm WHERE alarm_date BETWEEN ? AND ?
                ORDER BY alarm_date DESC, fail_comment''', (date_from, date_to)):
            key = (alarm['eqp'], alarm['slot'])
            comment = alarm['fail_comment'] or ''
            for mapping, item in ((alarms, key),
                                  (daily_comments, (alarm['alarm_date'], *key))):
                comments = mapping.setdefault(item, [])
                if comment and comment not in comments:
                    comments.append(comment)
        previous = (cache or {}).get('recent_alarm') if (cache or {}).get('identity') == identity else None
        recent_alarm = _recent_alarm_slots(conn, alarms, now, cancel, previous)
    totals, recent_by_slot, daily = {}, {}, []
    for day in reversed(days):
        if cancel.is_set():
            raise InterruptedError('Cancelled')
        data = next_days[day]
        for raw in data['stats']:
            r = dict(raw)  # Never attach comments to immutable cached aggregates.
            key = (r['eqp'], r['slot'])
            if not r['eqp'] or r['slot'] not in range(1, 49) or not r['total']:
                continue
            total = totals.setdefault(key, dict(total=0, passed=0, failed=0))
            for field in total:
                total[field] += r[field]
            r['fail_comment'] = ' | '.join(daily_comments.get((day, *key), []))
            daily.append(r)
            recent = recent_by_slot.setdefault(key, [])
            recent.extend(data['recent'].get(key, [])[:max(0, 10-len(recent))])
    rows = [dict(eqp=eqp, slot=slot, **totals[(eqp, slot)],
                 recent=[{k: v for k, v in r.items() if k != 'id'}
                         for r in recent_by_slot[(eqp, slot)]],
                 alarm=(eqp, slot) in alarms,
                 recent_alarm=(eqp, slot) in recent_alarm['qualified'],
                 fail_comment=' | '.join(alarms.get((eqp, slot), [])))
            for eqp, slot in sorted(totals)]
    # Preserve original date-descending, machine/slot-ascending Daily order.
    daily.sort(key=lambda r: (-int(r['date']), r['eqp'], r['slot']))
    return dict(rows=rows, daily=daily, start=date_from, end=date_to, now=now,
                alarm_range=(date_from, date_to), refreshed_days=tuple(refreshed),
                recent_alarm_range=recent_alarm['date_range'],
                _cache=dict(identity=identity, days=next_days, recent_alarm=recent_alarm))


def load_slot_history(path, date_from, date_to, eqp, slot, cancel):
    with connection(path, timeout=2) as conn:
        conn.execute('PRAGMA query_only=ON')
        conn.set_progress_handler(lambda: int(cancel.is_set()), 1000)
        return [ReportDetailRow(*tuple(r)) for r in conn.execute('''
            SELECT DATE,TIME,PARTNO,COALESCE(LOTNO,''),COALESCE(SERIAL,''),RESULT,
                   COALESCE(SCRAPCODE,''),QTY,EQP,TEST_COUNT,SLOT,MODEL,COALESCE(TIER,'')
            FROM prime_data WHERE EQP=? AND SLOT=? AND DATE BETWEEN ? AND ?
            ORDER BY DATE DESC,TIME DESC,id DESC''', (eqp,slot,date_from,date_to))]
