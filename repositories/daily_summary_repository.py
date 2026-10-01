# from database.connection import connection as open_connection
# from datetime import datetime, timedelta
# from domain.daily_summary import CumDailyRow, CumDailyResult, PrimeDailyRow, PrimeDailyResult
# from repositories.data_filter import build_data_filter
#
# class DailySummaryRepository:
#
#     def __init__(self, database_path):
#         self.database_path = database_path
#
#     def get_cum_daily_summary(self, date_from: str, date_to: str, eqpid: str | None, tiers: list[str | None], connection=None, selected_models: list[str] | None=None) -> CumDailyResult:
#         """
#         Tổng hợp hiệu suất từng ngày của một EQP.
#
#         In/Out lấy từ cum_data.
#         Fail = In - Out.
#         Mã lỗi lấy từ cum_scrap_detail.
#         """
#         if not eqpid:
#             return CumDailyResult(eqpid=None, scrap_codes=[], rows=[])
#         if connection is None:
#             with open_connection(self.database_path) as conn:
#                 conn.execute('BEGIN')
#                 return self.get_cum_daily_summary(date_from, date_to, eqpid, tiers, connection=conn, selected_models=selected_models)
#         tier_sql, tier_params = build_data_filter(column_name='TIER', tiers=tiers, selected_models=selected_models)
#         quantity_cursor = connection.execute(f'\n                SELECT\n                    DATE,\n                    SUM(INQTY) AS in_qty,\n                    SUM(OUTQTY) AS out_qty\n                FROM cum_data\n                WHERE DATE BETWEEN ? AND ?\n                  AND EQPID = ?\n                  {tier_sql}\n                GROUP BY DATE\n                ORDER BY DATE\n                ', [date_from, date_to, eqpid, *tier_params])
#         quantity_by_date = {row['DATE']: (int(row['in_qty'] or 0), int(row['out_qty'] or 0)) for row in quantity_cursor.fetchall()}
#         detail_tier_sql, detail_tier_params = build_data_filter(column_name='data.TIER', tiers=tiers, selected_models=selected_models)
#         scrap_cursor = connection.execute(f'\n                SELECT\n                    data.DATE,\n                    detail.scrap_code,\n                    SUM(detail.qty) AS scrap_qty\n                FROM cum_data AS data\n                INNER JOIN cum_scrap_detail AS detail\n                    ON detail.cum_data_id = data.id\n                WHERE data.DATE BETWEEN ? AND ?\n                  AND data.EQPID = ?\n                  {detail_tier_sql}\n                GROUP BY\n                    data.DATE,\n                    detail.scrap_code\n                ORDER BY\n                    detail.scrap_code,\n                    data.DATE\n                ', [date_from, date_to, eqpid, *detail_tier_params])
#         scrap_qty_by_date: dict[str, dict[str, int]] = {}
#         scrap_codes = set()
#         for row in scrap_cursor.fetchall():
#             date = row['DATE']
#             scrap_code = row['scrap_code']
#             scrap_qty = int(row['scrap_qty'] or 0)
#             scrap_codes.add(scrap_code)
#             scrap_qty_by_date.setdefault(date, {})[scrap_code] = scrap_qty
#         rows = []
#         for date in self._iter_dates(date_from=date_from, date_to=date_to):
#             in_qty, out_qty = quantity_by_date.get(date, (0, 0))
#             fail_qty = in_qty - out_qty
#             if in_qty > 0:
#                 fail_ppm = fail_qty / in_qty * 1000000
#                 yield_percent = out_qty / in_qty * 100
#             else:
#                 fail_ppm = None
#                 yield_percent = None
#             scrap_ppm_by_code = {}
#             for scrap_code, scrap_qty in scrap_qty_by_date.get(date, {}).items():
#                 if in_qty > 0:
#                     scrap_ppm_by_code[scrap_code] = scrap_qty / in_qty * 1000000
#             rows.append(CumDailyRow(date=date, in_qty=in_qty, out_qty=out_qty, fail_qty=fail_qty, fail_ppm=fail_ppm, yield_percent=yield_percent, scrap_ppm_by_code=scrap_ppm_by_code))
#         return CumDailyResult(eqpid=eqpid, scrap_codes=sorted(scrap_codes), rows=rows)
#
#     def get_prime_daily_summary(self, date_from: str, date_to: str, eqpid: str | None, tiers: list[str | None], connection=None, selected_models: list[str] | None=None) -> PrimeDailyResult:
#         """
#         Tổng hợp In, Pass, Fail và Scrap PPM
#         từ bảng prime_data theo từng ngày, chỉ lấy TEST_COUNT = 1.
#         """
#         if not eqpid:
#             return PrimeDailyResult(eqpid=None, scrap_codes=[], rows=[])
#         if connection is None:
#             with open_connection(self.database_path) as conn:
#                 conn.execute('BEGIN')
#                 return self.get_prime_daily_summary(date_from, date_to, eqpid, tiers, connection=conn, selected_models=selected_models)
#         tier_sql, tier_params = build_data_filter(column_name='TIER', tiers=tiers, selected_models=selected_models)
#         quantity_cursor = connection.execute(f"\n                SELECT\n                    DATE,\n                    SUM(QTY) AS in_qty,\n                    SUM(\n                        CASE\n                            WHEN RESULT = 'PASS'\n                            THEN QTY\n                            ELSE 0\n                        END\n                    ) AS pass_qty\n                FROM prime_data\n                WHERE DATE BETWEEN ? AND ?\n                  AND EQP = ?\n                  AND TEST_COUNT = 1\n                  {tier_sql}\n                GROUP BY DATE\n                ORDER BY DATE\n                ", [date_from, date_to, eqpid, *tier_params])
#         quantity_by_date = {row['DATE']: (int(row['in_qty'] or 0), int(row['pass_qty'] or 0)) for row in quantity_cursor.fetchall()}
#         scrap_tier_sql, scrap_tier_params = build_data_filter(column_name='TIER', tiers=tiers, selected_models=selected_models)
#         scrap_cursor = connection.execute(f"\n                SELECT\n                    DATE,\n                    SCRAPCODE AS scrap_code,\n                    SUM(QTY) AS scrap_qty\n                FROM prime_data\n                WHERE DATE BETWEEN ? AND ?\n                  AND EQP = ?\n                  AND TEST_COUNT = 1\n                  AND RESULT = 'FAIL'\n                  AND COALESCE(SCRAPCODE, '') <> ''\n                  {scrap_tier_sql}\n                GROUP BY\n                    DATE,\n                    SCRAPCODE\n                ORDER BY\n                    SCRAPCODE,\n                    DATE\n                ", [date_from, date_to, eqpid, *scrap_tier_params])
#         scrap_qty_by_date: dict[str, dict[str, int]] = {}
#         scrap_codes = set()
#         for row in scrap_cursor.fetchall():
#             date = row['DATE']
#             scrap_code = row['scrap_code']
#             scrap_qty = int(row['scrap_qty'] or 0)
#             scrap_codes.add(scrap_code)
#             scrap_qty_by_date.setdefault(date, {})[scrap_code] = scrap_qty
#         rows = []
#         for date in self._iter_dates(date_from=date_from, date_to=date_to):
#             in_qty, pass_qty = quantity_by_date.get(date, (0, 0))
#             fail_qty = in_qty - pass_qty
#             if in_qty > 0:
#                 fail_ppm = fail_qty / in_qty * 1000000
#                 yield_percent = pass_qty / in_qty * 100
#             else:
#                 fail_ppm = None
#                 yield_percent = None
#             scrap_ppm_by_code = {scrap_code: scrap_qty / in_qty * 1000000 for scrap_code, scrap_qty in scrap_qty_by_date.get(date, {}).items() if in_qty > 0}
#             rows.append(PrimeDailyRow(date=date, in_qty=in_qty, out_qty=pass_qty, fail_qty=fail_qty, fail_ppm=fail_ppm, yield_percent=yield_percent, scrap_ppm_by_code=scrap_ppm_by_code))
#         return PrimeDailyResult(eqpid=eqpid, scrap_codes=sorted(scrap_codes), rows=rows)
#
#     @staticmethod
#     def _iter_dates(date_from: str, date_to: str) -> list[str]:
#         """Tạo đầy đủ danh sách ngày trong khoảng đã chọn."""
#         start_date = datetime.strptime(date_from, '%Y%m%d').date()
#         end_date = datetime.strptime(date_to, '%Y%m%d').date()
#         dates = []
#         current_date = start_date
#         while current_date <= end_date:
#             dates.append(current_date.strftime('%Y%m%d'))
#             current_date += timedelta(days=1)
#         return dates
from database.connection import connection as open_connection
from datetime import datetime, timedelta
from domain.daily_summary import CumDailyRow, CumDailyResult, PrimeDailyRow, PrimeDailyResult
from repositories.data_filter import build_data_filter

class DailySummaryRepository:

    def __init__(self, database_path):
        self.database_path = database_path

    def get_cum_daily_summary(self, date_from: str, date_to: str, eqpid: str | None, tiers: list[str | None], connection=None, selected_models: list[str] | None=None) -> CumDailyResult:
        """
        Tổng hợp hiệu suất từng ngày của một EQP.

        In/Out lấy từ cum_data.
        Fail = In - Out.
        Mã lỗi lấy từ cum_scrap_detail.
        """
        if not eqpid:
            return CumDailyResult(eqpid=None, scrap_codes=[], rows=[])
        if connection is None:
            with open_connection(self.database_path) as conn:
                conn.execute('BEGIN')
                return self.get_cum_daily_summary(date_from, date_to, eqpid, tiers, connection=conn, selected_models=selected_models)
        tier_sql, tier_params = build_data_filter(column_name='TIER', tiers=tiers, selected_models=selected_models)
        quantity_cursor = connection.execute(f'\n                SELECT\n                    DATE,\n                    SUM(INQTY) AS in_qty,\n                    SUM(OUTQTY) AS out_qty\n                FROM cum_data\n                WHERE DATE BETWEEN ? AND ?\n                  AND EQPID = ?\n                  {tier_sql}\n                GROUP BY DATE\n                ORDER BY DATE\n                ', [date_from, date_to, eqpid, *tier_params])
        quantity_by_date = {row['DATE']: (int(row['in_qty'] or 0), int(row['out_qty'] or 0)) for row in quantity_cursor.fetchall()}
        detail_tier_sql, detail_tier_params = build_data_filter(column_name='data.TIER', tiers=tiers, selected_models=selected_models)
        scrap_cursor = connection.execute(f'\n                SELECT\n                    data.DATE,\n                    detail.scrap_code,\n                    SUM(detail.qty) AS scrap_qty\n                FROM cum_data AS data\n                INNER JOIN cum_scrap_detail AS detail\n                    ON detail.cum_data_id = data.id\n                WHERE data.DATE BETWEEN ? AND ?\n                  AND data.EQPID = ?\n                  {detail_tier_sql}\n                GROUP BY\n                    data.DATE,\n                    detail.scrap_code\n                ORDER BY\n                    detail.scrap_code,\n                    data.DATE\n                ', [date_from, date_to, eqpid, *detail_tier_params])
        scrap_qty_by_date: dict[str, dict[str, int]] = {}
        scrap_codes = set()
        for row in scrap_cursor.fetchall():
            date = row['DATE']
            scrap_code = row['scrap_code']
            scrap_qty = int(row['scrap_qty'] or 0)
            scrap_codes.add(scrap_code)
            scrap_qty_by_date.setdefault(date, {})[scrap_code] = scrap_qty
        rows = []
        for date in self._iter_dates(date_from=date_from, date_to=date_to):
            in_qty, out_qty = quantity_by_date.get(date, (0, 0))
            fail_qty = in_qty - out_qty
            if in_qty > 0:
                fail_ppm = fail_qty / in_qty * 1000000
                yield_percent = out_qty / in_qty * 100
            else:
                fail_ppm = None
                yield_percent = None
            scrap_ppm_by_code = {}
            for scrap_code, scrap_qty in scrap_qty_by_date.get(date, {}).items():
                if in_qty > 0:
                    scrap_ppm_by_code[scrap_code] = scrap_qty / in_qty * 1000000
            rows.append(CumDailyRow(date=date, in_qty=in_qty, out_qty=out_qty, fail_qty=fail_qty, fail_ppm=fail_ppm, yield_percent=yield_percent, scrap_ppm_by_code=scrap_ppm_by_code))
        return CumDailyResult(eqpid=eqpid, scrap_codes=sorted(scrap_codes), rows=rows)

    def get_prime_daily_summary(self, date_from: str, date_to: str, eqpid: str | None, tiers: list[str | None], connection=None, selected_models: list[str] | None=None) -> PrimeDailyResult:
        """
        Tổng hợp In, Pass, Fail và Scrap PPM
        từ bảng prime_data theo từng ngày, chỉ lấy TEST_COUNT = 0.
        """
        if not eqpid:
            return PrimeDailyResult(eqpid=None, scrap_codes=[], rows=[])
        if connection is None:
            with open_connection(self.database_path) as conn:
                conn.execute('BEGIN')
                return self.get_prime_daily_summary(date_from, date_to, eqpid, tiers, connection=conn, selected_models=selected_models)
        tier_sql, tier_params = build_data_filter(column_name='TIER', tiers=tiers, selected_models=selected_models)
        quantity_cursor = connection.execute(f"\n                SELECT\n                    DATE,\n                    SUM(QTY) AS in_qty,\n                    SUM(\n                        CASE\n                            WHEN RESULT = 'PASS'\n                            THEN QTY\n                            ELSE 0\n                        END\n                    ) AS pass_qty\n                FROM prime_data\n                WHERE DATE BETWEEN ? AND ?\n                  AND EQP = ?\n                  AND TEST_COUNT = 0\n                  {tier_sql}\n                GROUP BY DATE\n                ORDER BY DATE\n                ", [date_from, date_to, eqpid, *tier_params])
        quantity_by_date = {row['DATE']: (int(row['in_qty'] or 0), int(row['pass_qty'] or 0)) for row in quantity_cursor.fetchall()}
        scrap_tier_sql, scrap_tier_params = build_data_filter(column_name='TIER', tiers=tiers, selected_models=selected_models)
        scrap_cursor = connection.execute(f"\n                SELECT\n                    DATE,\n                    SCRAPCODE AS scrap_code,\n                    SUM(QTY) AS scrap_qty\n                FROM prime_data\n                WHERE DATE BETWEEN ? AND ?\n                  AND EQP = ?\n                  AND TEST_COUNT = 0\n                  AND RESULT = 'FAIL'\n                  AND COALESCE(SCRAPCODE, '') <> ''\n                  {scrap_tier_sql}\n                GROUP BY\n                    DATE,\n                    SCRAPCODE\n                ORDER BY\n                    SCRAPCODE,\n                    DATE\n                ", [date_from, date_to, eqpid, *scrap_tier_params])
        scrap_qty_by_date: dict[str, dict[str, int]] = {}
        scrap_codes = set()
        for row in scrap_cursor.fetchall():
            date = row['DATE']
            scrap_code = row['scrap_code']
            scrap_qty = int(row['scrap_qty'] or 0)
            scrap_codes.add(scrap_code)
            scrap_qty_by_date.setdefault(date, {})[scrap_code] = scrap_qty
        rows = []
        for date in self._iter_dates(date_from=date_from, date_to=date_to):
            in_qty, pass_qty = quantity_by_date.get(date, (0, 0))
            fail_qty = in_qty - pass_qty
            if in_qty > 0:
                fail_ppm = fail_qty / in_qty * 1000000
                yield_percent = pass_qty / in_qty * 100
            else:
                fail_ppm = None
                yield_percent = None
            scrap_ppm_by_code = {scrap_code: scrap_qty / in_qty * 1000000 for scrap_code, scrap_qty in scrap_qty_by_date.get(date, {}).items() if in_qty > 0}
            rows.append(PrimeDailyRow(date=date, in_qty=in_qty, out_qty=pass_qty, fail_qty=fail_qty, fail_ppm=fail_ppm, yield_percent=yield_percent, scrap_ppm_by_code=scrap_ppm_by_code))
        return PrimeDailyResult(eqpid=eqpid, scrap_codes=sorted(scrap_codes), rows=rows)

    @staticmethod
    def _iter_dates(date_from: str, date_to: str) -> list[str]:
        """Tạo đầy đủ danh sách ngày trong khoảng đã chọn."""
        start_date = datetime.strptime(date_from, '%Y%m%d').date()
        end_date = datetime.strptime(date_to, '%Y%m%d').date()
        dates = []
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date.strftime('%Y%m%d'))
            current_date += timedelta(days=1)
        return dates
