from dataclasses import dataclass
from threading import Event
from typing import Callable

COLUMNS = ("DATE", "TIME", "EQP", "PARTNO", "LOTNO", "SLOT", "RESULT",
           "SCRAPCODE", "TEST_COUNT", "SERIAL", "QTY", "MODEL")
Progress = Callable[[str], None]


class ImportErrorBase(Exception):
    """Lỗi nghiệp vụ có thể hiển thị cho người dùng."""


class ValidationError(ImportErrorBase):
    pass


class ImportBusyError(ImportErrorBase):
    pass


class LockLostError(ImportErrorBase):
    pass


class ImportCancelled(ImportErrorBase):
    pass


def check_cancel(cancel: Event | None) -> None:
    """Dừng import nếu có yêu cầu hủy trước khi commit."""
    if cancel is not None and cancel.is_set():
        raise ImportCancelled("Đã hủy import; dữ liệu chưa commit được giữ nguyên.")


@dataclass(frozen=True)
class PrimeRecord:
    DATE: str
    TIME: str
    EQP: str
    PARTNO: str
    LOTNO: str
    SLOT: int
    RESULT: str
    SCRAPCODE: str | None
    TEST_COUNT: int
    SERIAL: str
    QTY: int
    MODEL: str

    def values(self) -> tuple:
        """Chuyển bản ghi PRIME thành tuple theo thứ tự cột staging."""
        return tuple(getattr(self, name) for name in COLUMNS)


@dataclass(frozen=True)
class ImportResult:
    dates: tuple[str, ...]
    file_count: int
    inserted: int
    deleted: int
    passed: int
    failed: int

