from dataclasses import dataclass

CUM_COLUMNS = ("DATE", "TIME", "LOTID", "PRODUCT", "EQPID", "INQTY", "OUTQTY",
               "FAILQTY", "YIELD", "SCRAP", "MODEL", "TIER")


@dataclass(frozen=True)
class CumImportResult:
    file_name: str
    inserted: int
    deleted: int
    scrap_details: int
    dates: tuple[str, ...]
