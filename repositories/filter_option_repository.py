"""Các lựa chọn hiện có trong database LI; không thay đổi dữ liệu gốc."""
from dataclasses import dataclass
from database.connection import connection


@dataclass
class FilterOptionResult:
    eqps: list[str]
    slots: list[int]
    scrap_codes: list[str]
    tiers: list[str]
    models: list[str]


class FilterOptionRepository:
    def __init__(self, database_path):
        self.database_path = database_path

    def load_options(self, cancel_event=None):
        # Index seeks visit each distinct value, rather than every test row.
        # All columns below are the leading columns of existing LI indexes.
        with connection(self.database_path, timeout=5) as conn:
            if cancel_event is not None:
                conn.set_progress_handler(lambda: int(cancel_event.is_set()), 1000)
            conn.execute("BEGIN")

            def values(table, column):
                # Identifiers are internal constants, never user input.
                sql = f"""WITH RECURSIVE options(value) AS (
                    SELECT MIN({column}) FROM {table}
                    UNION ALL
                    SELECT (SELECT MIN({column}) FROM {table} WHERE {column}>options.value)
                    FROM options WHERE value IS NOT NULL
                ) SELECT value FROM options WHERE value IS NOT NULL"""
                return [row[0] for row in conn.execute(sql)]

            def combined(column):
                return sorted(set(values("prime_data", column)) |
                              set(values("cum_data", column)))

            prime_codes = values("prime_data", "SCRAPCODE")
            return FilterOptionResult(
                eqps=values("prime_data", "EQP"),
                slots=values("prime_data", "SLOT"),
                models=combined("MODEL"),
                tiers=combined("TIER"),
                scrap_codes=sorted({code for code in prime_codes
                    if len(code) == 4 and all("0" <= ch <= "9" for ch in code)} |
                    set(values("cum_scrap_detail", "scrap_code"))),
            )
