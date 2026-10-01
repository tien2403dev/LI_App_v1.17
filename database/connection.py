import re
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import quote
from database.diagnostics import caller, event

DEFAULT_TIMEOUT = 60.0


def _operation(sql):
    # No parameters, literal values, serial numbers, passwords or mail bodies.
    text = re.sub(r"'([^']|'')*'", "?", str(sql))
    words = text.strip().split()
    match = re.search(r'\b(?:FROM|INTO|UPDATE|TABLE)\s+([A-Za-z_][A-Za-z_0-9]*)', text, re.I)
    return (words[0].upper() if words else 'SQL') + (':' + match.group(1) if match else '')


class DiagnosticConnection(sqlite3.Connection):
    def _call(self, action, fn, *args, **kwargs):
        start = time.monotonic()
        event('DB_BEGIN', connection=self.diagnostic_id, operation=action,
              caller=caller(), in_transaction=self.in_transaction)
        try:
            value = fn(*args, **kwargs)
        except BaseException as error:
            event('DB_ERROR', connection=self.diagnostic_id, operation=action,
                  seconds=round(time.monotonic()-start, 3),
                  error_type=type(error).__name__, sqlite_code=getattr(error,'sqlite_errorcode',None),
                  sqlite_name=getattr(error,'sqlite_errorname',None),
                  in_transaction=self.in_transaction)
            raise
        event('DB_END', connection=self.diagnostic_id, operation=action,
              seconds=round(time.monotonic()-start,3), in_transaction=self.in_transaction)
        return value

    def execute(self, sql, parameters=()):
        return self._call(_operation(sql), super().execute, sql, parameters)

    def executemany(self, sql, parameters):
        return self._call('MANY:' + _operation(sql), super().executemany, sql, parameters)

    def commit(self):
        return self._call('COMMIT', super().commit)

    def rollback(self):
        return self._call('ROLLBACK', super().rollback)

    def close(self):
        if getattr(self, '_diagnostic_closed', False):
            return
        event('DB_CLOSE_BEGIN', connection=self.diagnostic_id,
              lifetime_seconds=round(time.monotonic()-self.opened_at,3),
              in_transaction=self.in_transaction)
        try:
            # Explicit rollback records aborted/read transactions in diagnostics.
            if self.in_transaction:
                self.rollback()
        finally:
            super().close()
            self._diagnostic_closed = True
            event('DB_CLOSED', connection=self.diagnostic_id)


def create_connection(database_path: str | Path, timeout: float = DEFAULT_TIMEOUT, *, readonly=False):
    """One connection per task; normal background writers wait like Aging."""
    from database.read_wait import read_timeout
    limit = read_timeout.get()
    if limit is not None:
        timeout = min(timeout, limit)
    path = Path(database_path)
    cid = uuid.uuid4().hex[:10]
    event('DB_OPEN_BEGIN', connection=cid, database=str(path), timeout=timeout, caller=caller())
    if not path.parent.is_dir():
        event('DB_OPEN_ERROR', connection=cid, reason='parent_unavailable')
        raise FileNotFoundError(f'Không truy cập được thư mục database: {path.parent}')
    try:
        target = 'file:' + quote(str(path.resolve()), safe='') + '?mode=ro' if readonly else str(path)
        conn = sqlite3.connect(target, timeout=timeout, isolation_level=None,
                               factory=DiagnosticConnection, uri=readonly)
    except BaseException as error:
        event('DB_OPEN_ERROR', connection=cid, error_type=type(error).__name__)
        raise
    conn.diagnostic_id = cid
    conn.opened_at = time.monotonic()
    conn.row_factory = sqlite3.Row
    try:
        conn.execute('PRAGMA foreign_keys = ON')
        conn.execute('PRAGMA synchronous = FULL')
        conn.execute(f'PRAGMA busy_timeout = {int(timeout * 1000)}')
        event('DB_OPENED', connection=cid)
        return conn
    except BaseException:
        conn.close()
        raise


@contextmanager
def connection(database_path: str | Path, timeout: float = DEFAULT_TIMEOUT):
    conn = create_connection(database_path, timeout)
    try:
        yield conn
    finally:
        conn.close()
