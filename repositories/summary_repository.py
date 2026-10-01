from contextlib import nullcontext
from database.connection import connection
from domain.summary import CumEqpSummaryRow, CumEqpSummaryResult
from repositories.data_filter import build_data_filter


class SummaryRepository:
    """Tổng hợp CUM như Aging; không dùng EQP, SLOT hoặc Scrap Code."""

    def __init__(self, database_path):
        self.database_path = database_path

    def load(self, date_from, date_to, tiers, models, *, conn=None):
        filter_sql, params = build_data_filter("TIER", tiers, models)
        with (connection(self.database_path) if conn is None else nullcontext(conn)) as conn:
            records = conn.execute(f"""
                SELECT EQPID, SUM(INQTY) AS in_qty, SUM(OUTQTY) AS out_qty
                FROM cum_data
                WHERE DATE BETWEEN ? AND ? {filter_sql}
                GROUP BY EQPID ORDER BY EQPID
            """, [date_from, date_to, *params]).fetchall()
        rows = [self._build_summary_row(row["EQPID"], row["in_qty"], row["out_qty"])
                for row in records]
        total = self._build_summary_row("Total", sum(r.in_qty for r in rows),
                                        sum(r.out_qty for r in rows))
        return CumEqpSummaryResult(rows, total)

    @staticmethod
    def _build_summary_row(
        eqpid: str,
        in_qty: int,
        out_qty: int,
    ) -> CumEqpSummaryRow:
        """Tính Fail Qty, Fail PPM và Yield từ tổng In/Out."""

        fail_qty = in_qty - out_qty

        if in_qty <= 0:
            fail_ppm = None
            yield_percent = None
        else:
            fail_ppm = (
                fail_qty / in_qty
            ) * 1_000_000

            yield_percent = (
                out_qty / in_qty
            ) * 100

        return CumEqpSummaryRow(
            eqpid=eqpid,
            in_qty=in_qty,
            out_qty=out_qty,
            fail_qty=fail_qty,
            fail_ppm=fail_ppm,
            yield_percent=yield_percent,
        )

