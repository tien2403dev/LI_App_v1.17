"""Local, per-process diagnostics. Never log SQL parameters or mail credentials."""
import atexit
import faulthandler
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time
import uuid

_RUN = uuid.uuid4().hex[:12]
_guard = threading.Lock()
_log = None
_path = None


def log_path():
    global _log, _path
    with _guard:
        if _log is None:
            logger = logging.getLogger('li.database.diagnostics')
            logger.setLevel(logging.INFO)
            logger.propagate = False
            # LOCALAPPDATA is independent of a shared EXE/database folder.
            base = Path(os.environ.get('LOCALAPPDATA') or tempfile.gettempdir()) / 'LI_App' / 'logs'
            try:
                base.mkdir(parents=True, exist_ok=True)
                path = base / f'li_diagnostic_{os.getpid()}_{_RUN}.jsonl'
                handler = RotatingFileHandler(path, maxBytes=5*1024*1024,
                                               backupCount=3, encoding='utf-8')
                handler.setFormatter(logging.Formatter('%(message)s'))
                logger.addHandler(handler)
                _path = path
            except OSError:
                logger.addHandler(logging.NullHandler())
            _log = logger
    return _path


def event(name, **fields):
    """Best effort: logging failures must not change database outcomes."""
    try:
        log_path()
        payload = dict(time=time.strftime('%Y-%m-%d %H:%M:%S'),
                       event=name, pid=os.getpid(), ppid=os.getppid(),
                       host=socket.gethostname(), run=_RUN,
                       thread=threading.current_thread().name, **fields)
        _log.info(json.dumps(payload, ensure_ascii=False, default=str))
    except Exception:
        pass


def caller():
    frame = sys._getframe(1)
    while frame:
        filename = Path(frame.f_code.co_filename)
        if filename.name not in ('connection.py', 'diagnostics.py', 'contextlib.py'):
            return f'{filename.parent.name}/{filename.name}:{frame.f_lineno}:{frame.f_code.co_name}'
        frame = frame.f_back
    return 'unknown'


def run_entrypoint(task, main):
    """Periodic stacks distinguish a slow job from a blocked I/O/shutdown."""
    path = log_path()
    stack_file = None
    if path:
        try:
            stack_file = path.with_suffix('.stacks.log').open('a', encoding='utf-8')
            faulthandler.dump_traceback_later(120, repeat=True, file=stack_file)
        except (OSError, RuntimeError):
            if stack_file:
                stack_file.close()
            stack_file = None
    atexit.register(event, 'PROCESS_PYTHON_SHUTDOWN', task=task)
    event('PROCESS_START', task=task, executable=sys.executable, frozen=bool(getattr(sys,'frozen',False)))
    try:
        result = main()
        event('PROCESS_EXIT_REQUEST', task=task, exit_code=result,
              threads=[dict(name=t.name, daemon=t.daemon) for t in threading.enumerate()])
        return result
    except BaseException as error:
        event('PROCESS_EXCEPTION', task=task, error_type=type(error).__name__)
        raise
    finally:
        # Remain armed during Python shutdown; a stuck non-daemon thread will
        # produce stacks. Keep the descriptor alive until normal process exit.
        if stack_file:
            _stack_handles.append(stack_file)


_stack_handles = []
