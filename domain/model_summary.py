from dataclasses import dataclass, field


@dataclass
class CumModelRow:
    """Sản lượng và số lượng từng scrapcode của một Model."""
    model: str
    in_qty: int
    out_qty: int
    fail_qty: int
    yield_percent: float | None
    scrap_qty: dict[str, int] = field(default_factory=dict)


@dataclass
class CumModelResult:
    """Dữ liệu đầy đủ để bảng và biểu đồ dùng chung, không lọc scrapcode."""
    rows: list[CumModelRow]
    scrap_codes: list[str]
    scrap_totals: dict[str, int]
