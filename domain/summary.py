from dataclasses import dataclass
from domain.daily_summary import CumDailyResult, PrimeDailyResult

@dataclass
class CumEqpSummaryRow:
    """Một dòng thống kê CUM theo EQPID."""

    eqpid: str
    in_qty: int
    out_qty: int
    fail_qty: int
    fail_ppm: float | None
    yield_percent: float | None

@dataclass
class CumEqpSummaryResult:
    """Kết quả bảng CUM theo EQPID, gồm cả dòng Total."""

    rows: list[CumEqpSummaryRow]
    total: CumEqpSummaryRow

    cum_daily: CumDailyResult | None = None
    prime_daily: PrimeDailyResult | None = None

