from dataclasses import dataclass

@dataclass
class CumDailyRow:
    """Một dòng thống kê CUM của EQP theo ngày."""

    date: str
    in_qty: int
    out_qty: int
    fail_qty: int
    fail_ppm: float | None
    yield_percent: float | None
    scrap_ppm_by_code: dict[str, float]


@dataclass
class CumDailyResult:
    """Kết quả thống kê từng ngày của một EQP."""

    eqpid: str | None
    scrap_codes: list[str]
    rows: list[CumDailyRow]


@dataclass
class PrimeDailyRow:
    """Một dòng thống kê PRIME của EQP theo ngày."""

    date: str
    in_qty: int
    out_qty: int
    fail_qty: int
    fail_ppm: float | None
    yield_percent: float | None
    scrap_ppm_by_code: dict[str, float]


@dataclass
class PrimeDailyResult:
    """Kết quả thống kê PRIME từng ngày của một EQP."""

    eqpid: str | None
    scrap_codes: list[str]
    rows: list[PrimeDailyRow]


