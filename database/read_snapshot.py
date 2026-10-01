"""Copy selected rows locally, then release shared DB before report formatting."""
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from database.connection import connection
from database.diagnostics import event


def copy_query(source, target, table, sql, params=(), cancel=None):
    cursor = source.execute(sql, params)
    try:
        columns = [column[0] for column in cursor.description]
        names = ','.join('"' + name.replace('"', '""') + '"' for name in columns)
        target.execute(f'CREATE TABLE "{table}" ({names})')
        count = 0
        while True:
            if cancel is not None and cancel.is_set():
                raise InterruptedError('Đã hủy đọc snapshot.')
            rows = cursor.fetchmany(5000)
            if not rows:
                break
            target.executemany(f'INSERT INTO "{table}" VALUES ({",".join("?" for _ in columns)})', rows)
            count += len(rows)
        event('READ_SNAPSHOT_TABLE', table=table, rows=count)
    finally:
        cursor.close()


@contextmanager
def machine_export_snapshot(path, dates, cancel):
    with TemporaryDirectory(prefix='li_export_') as temporary:
        local = sqlite3.connect(str(Path(temporary) / 'snapshot.db'))
        local.row_factory = sqlite3.Row
        try:
            with connection(path) as source:
                source.execute('PRAGMA query_only=ON')
                source.set_progress_handler(lambda: int(cancel.is_set()), 1000)
                source.execute('BEGIN')
                copy_query(source, local, 'machine_slot_yield_config',
                           'SELECT * FROM machine_slot_yield_config', cancel=cancel)
                copy_query(source, local, 'slot_fail_alarm',
                           'SELECT eqp,slot,alarm_date FROM slot_fail_alarm WHERE alarm_date BETWEEN ? AND ?', dates, cancel)
                copy_query(source, local, 'prime_data',
                           'SELECT * FROM prime_data WHERE DATE BETWEEN ? AND ?', dates, cancel)
            event('READ_SNAPSHOT_MAIN_CLOSED', kind='machine_export')
            local.execute('CREATE INDEX snapshot_slot ON prime_data(EQP,SLOT,DATE,TIME,id)')
            local.commit()
            yield local
        finally:
            local.close()
