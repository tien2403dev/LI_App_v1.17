# from __future__ import annotations
#
# import sqlite3
# from contextlib import closing
# from dataclasses import dataclass
# from datetime import datetime, timedelta
# from pathlib import Path
# from typing import Union
#
#
# @dataclass(frozen=True)
# class ReportSummaryRow:
#     date: str
#     eqp: str
#     slot: int
#     in_qty: int | None
#     out_qty: int | None
#     fail_qty: int | None
#     scrap_codes: str
#     yield_percent: float | None
#     models: str
#
#
# @dataclass(frozen=True)
# class ReportDetailRow:
#     date: str
#     time: str
#     partno: str
#     lotno: str
#     serial: str
#     result: str
#     scrap_code: str
#     qty: int
#     eqp: str
#     test_count: int
#     slot: int
#     model: str
#     tier: str
#
#
# class ReportRepository:
#     """Truy vấn dữ liệu PRIME dành riêng cho tab Report."""
#
#     def __init__(self, database_path: Union[str, Path]):
#         self.database_path = Path(database_path)
#
#     def _connect(self):
#         connection = sqlite3.connect(self.database_path.resolve().as_uri() + "?mode=ro", uri=True, timeout=5)
#         connection.row_factory = sqlite3.Row
#         return closing(connection)
#
#     @staticmethod
#     def _db_datetime(value: str) -> str:
#         # UI: yyyy-MM-dd HH:mm:ss; DB: yyyyMMdd + HH:mm:ss.
#         return value[:10].replace("-", "") + value[10:]
#
#     def get_filter_options(self) -> tuple[list[str], list[int]]:
#         with self._connect() as connection:
#             eqps = [
#                 row[0]
#                 for row in connection.execute(
#                     "SELECT DISTINCT EQP FROM prime_data ORDER BY EQP"
#                 )
#             ]
#             slots = [
#                 int(row[0])
#                 for row in connection.execute(
#                     "SELECT DISTINCT Slot FROM prime_data ORDER BY Slot"
#                 )
#             ]
#         return eqps, slots
#
#     @staticmethod
#     def _where_clause(
#         date_from: str,
#         date_to: str,
#         eqps: list[str],
#         slots: list[int],
#     ) -> tuple[str, list[object]]:
#         from_date, from_time = date_from.split(" ", 1)
#         to_date, to_time = date_to.split(" ", 1)
#         if from_date == to_date:
#             clauses = ["DATE = ? AND TIME BETWEEN ? AND ?"]
#             parameters: list[object] = [from_date, from_time, to_time]
#         else:
#             clauses = [
#                 "DATE BETWEEN ? AND ?",
#                 "(DATE > ? OR TIME >= ?)",
#                 "(DATE < ? OR TIME <= ?)",
#             ]
#             parameters = [
#                 from_date, to_date, from_date, from_time, to_date, to_time,
#             ]
#
# #         if eqps:
#             clauses.append("EQP IN ({})".format(",".join("?" for _ in eqps)))
#             parameters.extend(eqps)
#         if slots:
#             clauses.append("Slot IN ({})".format(",".join("?" for _ in slots)))
#             parameters.extend(slots)
#
#         return " AND ".join(clauses), parameters
#
#     def get_summary(
#         self,
#         date_from: str,
#         date_to: str,
#         eqps: list[str],
#         slots: list[int],
#     ) -> list[ReportSummaryRow]:
#         selected_eqps = list(eqps)
#         selected_slots = list(slots)
#         if not selected_eqps or not selected_slots:
#             return []
#
#         where_sql, parameters = self._where_clause(
#             self._db_datetime(date_from),
#             self._db_datetime(date_to),
#             selected_eqps,
#             selected_slots,
#         )
#         sql = f"""
#             WITH filtered AS MATERIALIZED (
#                 SELECT DATE, EQP, Slot, RESULT, SCRAPCODE, MODEL
#                 FROM prime_data
#                 WHERE {where_sql}
#             ),
#             totals AS (
#                 SELECT DATE, EQP, Slot,
#                        COUNT(*) AS in_qty,
#                        SUM(RESULT = 'PASS') AS out_qty,
#                        SUM(RESULT = 'FAIL') AS fail_qty
#                 FROM filtered
#                 GROUP BY DATE, EQP, Slot
#             ),
#             scrap_counts AS (
#                 SELECT DATE, EQP, Slot, SCRAPCODE, COUNT(*) AS qty
#                 FROM filtered
#                 WHERE RESULT = 'FAIL'
#                   AND COALESCE(SCRAPCODE, '') <> ''
#                 GROUP BY DATE, EQP, Slot, SCRAPCODE
#             ),
#             scraps AS (
#                 SELECT DATE, EQP, Slot,
#                        GROUP_CONCAT(SCRAPCODE || '*' || qty, char(10)) AS values_text
#                 FROM scrap_counts
#                 GROUP BY DATE, EQP, Slot
#             ),
#             model_values AS (
#                 SELECT DISTINCT DATE, EQP, Slot, MODEL
#                 FROM filtered
#                 WHERE COALESCE(MODEL, '') <> ''
#             ),
#             models AS (
#                 SELECT DATE, EQP, Slot,
#                        GROUP_CONCAT(MODEL, char(10)) AS values_text
#                 FROM model_values
#                 GROUP BY DATE, EQP, Slot
#             )
#             SELECT t.DATE, t.EQP, t.Slot, t.in_qty, t.out_qty, t.fail_qty,
#                    COALESCE(s.values_text, '') AS scrap_codes,
#                    CASE WHEN t.in_qty = 0 THEN NULL
#                         ELSE 100.0 * t.out_qty / t.in_qty END AS yield_percent,
#                    COALESCE(m.values_text, '') AS models
#             FROM totals AS t
#             LEFT JOIN scraps AS s USING (DATE, EQP, Slot)
#             LEFT JOIN models AS m USING (DATE, EQP, Slot)
#             ORDER BY t.DATE, t.EQP, t.Slot
#         """
#         with self._connect() as connection:
#             rows = connection.execute(sql, parameters).fetchall()
#
#         data_rows = [
#             ReportSummaryRow(
#                 date=row["DATE"], eqp=row["EQP"], slot=int(row["Slot"]),
#                 in_qty=int(row["in_qty"]), out_qty=int(row["out_qty"]),
#                 fail_qty=int(row["fail_qty"]), scrap_codes=row["scrap_codes"],
#                 yield_percent=row["yield_percent"], models=row["models"],
#             )
#             for row in rows
#         ]
#
#         # Luôn tạo đủ ma trận ngày x EQP x Slot được chọn. Dòng không có
#         # dữ liệu chỉ hiển thị DATE, EQP, SLOT để có thể copy thẳng sang Excel.
#         rows_by_key = {
#             (row.date, row.eqp, row.slot): row
#             for row in data_rows
#         }
#         first_date = datetime.strptime(date_from[:10], "%Y-%m-%d").date()
#         last_date = datetime.strptime(date_to[:10], "%Y-%m-%d").date()
#         result: list[ReportSummaryRow] = []
#         current_date = first_date
#         while current_date <= last_date:
#             date_text = current_date.strftime("%Y%m%d")
#             for eqp in selected_eqps:
#                 for slot in selected_slots:
#                     result.append(
#                         rows_by_key.get(
#                             (date_text, eqp, slot),
#                             ReportSummaryRow(
#                                 date=date_text,
#                                 eqp=eqp,
#                                 slot=slot,
#                                 in_qty=None,
#                                 out_qty=None,
#                                 fail_qty=None,
#                                 scrap_codes="",
#                                 yield_percent=None,
#                                 models="",
#                             ),
#                         )
#                     )
#             current_date += timedelta(days=1)
#         return result
#
#     def get_details(
#         self,
#         date_from: str,
#         date_to: str,
#         date: str,
#         eqp: str,
#         slot: int,
#     ) -> list[ReportDetailRow]:
#         sql = """
#             SELECT DATE, TIME, PARTNO, COALESCE(LOTNO, '') AS LOTNO,
#                    COALESCE(SERIAL, '') AS SERIAL, RESULT,
#                    COALESCE(SCRAPCODE, '') AS SCRAPCODE, QTY, EQP,
#                    TEST_COUNT, Slot, MODEL, COALESCE(TIER, '') AS TIER
#             FROM prime_data
#             WHERE DATE = ? AND EQP = ? AND Slot = ?
# #               AND DATE BETWEEN ? AND ?
#               AND (DATE > ? OR TIME >= ?)
#               AND (DATE < ? OR TIME <= ?)
#             ORDER BY DATE, TIME, id
#         """
#         date_from = self._db_datetime(date_from)
#         date_to = self._db_datetime(date_to)
#         from_date, from_time = date_from.split(" ", 1)
#         to_date, to_time = date_to.split(" ", 1)
#         parameters = (
#             date, eqp, slot, from_date, to_date,
#             from_date, from_time, to_date, to_time,
#         )
#         with self._connect() as connection:
#             rows = connection.execute(sql, parameters).fetchall()
#         return [ReportDetailRow(*tuple(row)) for row in rows]

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Union
from urllib.parse import quote


@dataclass(frozen=True)
class ReportSummaryRow:
    date: str
    eqp: str
    slot: int
    in_qty: int | None
    out_qty: int | None
    fail_qty: int | None
    scrap_codes: str
    yield_percent: float | None
    models: str


@dataclass(frozen=True)
class ReportDetailRow:
    date: str
    time: str
    partno: str
    lotno: str
    serial: str
    result: str
    scrap_code: str
    qty: int
    eqp: str
    test_count: int
    slot: int
    model: str
    tier: str


class ReportRepository:
    """Truy vấn dữ liệu PRIME dành riêng cho tab Report."""

    def __init__(self, database_path: Union[str, Path]):
        self.database_path = Path(database_path)

    @staticmethod
    def _readonly_uri(path):
        """Mã hóa đường dẫn thành URI chỉ đọc, không có authority kể cả UNC."""
        # Encode cả dấu phân cách: SQLite phân tích URI trước, rồi giải mã
        # filename cho hệ điều hành. Giữ nguyên đường dẫn UNC/ổ đĩa Windows.
        return "file:" + quote(str(path), safe="") + "?mode=ro"

    def _connect(self):
        """Mở database hiện có ở chế độ chỉ đọc cho bộ lọc/bảng/chi tiết Report."""
        uri = self._readonly_uri(self.database_path.resolve())
        from database.connection import create_connection
        connection = create_connection(self.database_path, timeout=5, readonly=True)
        return closing(connection)

    @staticmethod
    def _db_datetime(value: str) -> str:
        # UI: yyyy-MM-dd HH:mm:ss; DB: yyyyMMdd + HH:mm:ss.
        return value[:10].replace("-", "") + value[10:]

    def get_filter_options(self) -> tuple[list[str], list[int]]:
        with self._connect() as connection:
            def values(column):
                # Internal column names only. Seek the next distinct value via
                # the existing index, as in FilterOptionRepository.load_options.
                sql = f"""WITH RECURSIVE options(value) AS (
                    SELECT MIN({column}) FROM prime_data
                    UNION ALL
                    SELECT (SELECT MIN({column}) FROM prime_data
                            WHERE {column}>options.value)
                    FROM options WHERE value IS NOT NULL
                ) SELECT value FROM options WHERE value IS NOT NULL"""
                return [row[0] for row in connection.execute(sql)]

            eqps = values("EQP")
            slots = [int(value) for value in values("Slot")]
        return eqps, slots

    @staticmethod
    def _where_clause(
        date_from: str,
        date_to: str,
        eqps: list[str],
        slots: list[int],
    ) -> tuple[str, list[object]]:
        from_date, from_time = date_from.split(" ", 1)
        to_date, to_time = date_to.split(" ", 1)
        if from_date == to_date:
            clauses = ["DATE = ? AND TIME BETWEEN ? AND ?"]
            parameters: list[object] = [from_date, from_time, to_time]
        else:
            clauses = [
                "DATE BETWEEN ? AND ?",
                "(DATE > ? OR TIME >= ?)",
                "(DATE < ? OR TIME <= ?)",
            ]
            parameters = [
                from_date, to_date, from_date, from_time, to_date, to_time,
            ]

        if eqps:
            clauses.append("EQP IN ({})".format(",".join("?" for _ in eqps)))
            parameters.extend(eqps)
        if slots:
            clauses.append("Slot IN ({})".format(",".join("?" for _ in slots)))
            parameters.extend(slots)

        return " AND ".join(clauses), parameters

    def get_summary(
        self,
        date_from: str,
        date_to: str,
        eqps: list[str],
        slots: list[int],
    ) -> list[ReportSummaryRow]:
        selected_eqps = list(eqps)
        selected_slots = list(slots)
        if not selected_eqps or not selected_slots:
            return []

        where_sql, parameters = self._where_clause(
            self._db_datetime(date_from),
            self._db_datetime(date_to),
            selected_eqps,
            selected_slots,
        )
        sql = f"""
            WITH filtered AS MATERIALIZED (
                SELECT DATE, EQP, Slot, RESULT, SCRAPCODE, MODEL
                FROM prime_data
                WHERE {where_sql}
            ),
            totals AS (
                SELECT DATE, EQP, Slot,
                       COUNT(*) AS in_qty,
                       SUM(RESULT = 'PASS') AS out_qty,
                       SUM(RESULT = 'FAIL') AS fail_qty
                FROM filtered
                GROUP BY DATE, EQP, Slot
            ),
            scrap_counts AS (
                SELECT DATE, EQP, Slot, SCRAPCODE, COUNT(*) AS qty
                FROM filtered
                WHERE RESULT = 'FAIL'
                  AND COALESCE(SCRAPCODE, '') <> ''
                GROUP BY DATE, EQP, Slot, SCRAPCODE
            ),
            scraps AS (
                SELECT DATE, EQP, Slot,
                       GROUP_CONCAT(SCRAPCODE || '*' || qty, char(10)) AS values_text
                FROM scrap_counts
                GROUP BY DATE, EQP, Slot
            ),
            model_values AS (
                SELECT DISTINCT DATE, EQP, Slot, MODEL
                FROM filtered
                WHERE COALESCE(MODEL, '') <> ''
            ),
            models AS (
                SELECT DATE, EQP, Slot,
                       GROUP_CONCAT(MODEL, char(10)) AS values_text
                FROM model_values
                GROUP BY DATE, EQP, Slot
            )
            SELECT t.DATE, t.EQP, t.Slot, t.in_qty, t.out_qty, t.fail_qty,
                   COALESCE(s.values_text, '') AS scrap_codes,
                   CASE WHEN t.in_qty = 0 THEN NULL
                        ELSE 100.0 * t.out_qty / t.in_qty END AS yield_percent,
                   COALESCE(m.values_text, '') AS models
            FROM totals AS t
            LEFT JOIN scraps AS s USING (DATE, EQP, Slot)
            LEFT JOIN models AS m USING (DATE, EQP, Slot)
            ORDER BY t.DATE, t.EQP, t.Slot
        """
        with self._connect() as connection:
            rows = connection.execute(sql, parameters).fetchall()

        data_rows = [
            ReportSummaryRow(
                date=row["DATE"], eqp=row["EQP"], slot=int(row["Slot"]),
                in_qty=int(row["in_qty"]), out_qty=int(row["out_qty"]),
                fail_qty=int(row["fail_qty"]), scrap_codes=row["scrap_codes"],
                yield_percent=row["yield_percent"], models=row["models"],
            )
            for row in rows
        ]

        # Luôn tạo đủ ma trận ngày x EQP x Slot được chọn. Dòng không có
        # dữ liệu chỉ hiển thị DATE, EQP, SLOT để có thể copy thẳng sang Excel.
        rows_by_key = {
            (row.date, row.eqp, row.slot): row
            for row in data_rows
        }
        first_date = datetime.strptime(date_from[:10], "%Y-%m-%d").date()
        last_date = datetime.strptime(date_to[:10], "%Y-%m-%d").date()
        result: list[ReportSummaryRow] = []
        current_date = first_date
        while current_date <= last_date:
            date_text = current_date.strftime("%Y%m%d")
            for eqp in selected_eqps:
                for slot in selected_slots:
                    result.append(
                        rows_by_key.get(
                            (date_text, eqp, slot),
                            ReportSummaryRow(
                                date=date_text,
                                eqp=eqp,
                                slot=slot,
                                in_qty=None,
                                out_qty=None,
                                fail_qty=None,
                                scrap_codes="",
                                yield_percent=None,
                                models="",
                            ),
                        )
                    )
            current_date += timedelta(days=1)
        return result

    def get_details(
        self,
        date_from: str,
        date_to: str,
        date: str,
        eqp: str,
        slot: int,
    ) -> list[ReportDetailRow]:
        sql = """
            SELECT DATE, TIME, PARTNO, COALESCE(LOTNO, '') AS LOTNO,
                   COALESCE(SERIAL, '') AS SERIAL, RESULT,
                   COALESCE(SCRAPCODE, '') AS SCRAPCODE, QTY, EQP,
                   TEST_COUNT, Slot, MODEL, COALESCE(TIER, '') AS TIER
            FROM prime_data
            WHERE DATE = ? AND EQP = ? AND Slot = ?
              AND DATE BETWEEN ? AND ?
              AND (DATE > ? OR TIME >= ?)
              AND (DATE < ? OR TIME <= ?)
            ORDER BY DATE, TIME, id
        """
        date_from = self._db_datetime(date_from)
        date_to = self._db_datetime(date_to)
        from_date, from_time = date_from.split(" ", 1)
        to_date, to_time = date_to.split(" ", 1)
        parameters = (
            date, eqp, slot, from_date, to_date,
            from_date, from_time, to_date, to_time,
        )
        with self._connect() as connection:
            rows = connection.execute(sql, parameters).fetchall()
        return [ReportDetailRow(*tuple(row)) for row in rows]
