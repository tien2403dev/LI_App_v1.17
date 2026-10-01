"""Short lock waits scoped to GUI read workers; import connections are unchanged."""
from contextvars import ContextVar
import sqlite3

GUI_READ_TIMEOUT = 1.0
read_timeout = ContextVar('li_gui_read_timeout', default=None)


def is_database_busy(error):
    if not isinstance(error, sqlite3.OperationalError):
        return False
    code = getattr(error, 'sqlite_errorcode', None)
    if code is not None:
        return (code & 255) in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED)
    return str(error).lower().strip() in (
        'database is locked', 'database table is locked', 'database schema is locked',
        'database is busy',
    )
