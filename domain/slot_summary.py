from dataclasses import dataclass
from domain.model_summary import CumModelResult


@dataclass(frozen=True)
class SlotSummaryRow:
    slot: int
    in_qty: int
    pass_qty: int
    fail_qty: int
    yield_percent: float | None
    fail_ppm: float | None


@dataclass(frozen=True)
class SlotSummaryResult:
    eqp: str | None
    rows: list[SlotSummaryRow]
    daily: "SlotDailyResult | None" = None
    cum_model: CumModelResult | None = None


@dataclass(frozen=True)
class SlotDailyRow:
    """Số lượng và yield của một ngày, hoặc toàn khoảng ngày."""
    date: str
    in_qty: int
    pass_qty: int
    fail_qty: int
    yield_percent: float | None


@dataclass(frozen=True)
class SlotDailyResult:
    """Dữ liệu đã tổng hợp, dùng chung cho bảng và biểu đồ."""
    eqp: str
    slot: int
    rows: list[SlotDailyRow]
    total: SlotDailyRow
