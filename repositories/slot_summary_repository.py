# from datetime import datetime, timedelta
# from domain.slot_summary import SlotDailyResult, SlotDailyRow
# from database.connection import connection
# from domain.slot_summary import SlotSummaryResult, SlotSummaryRow
# from repositories.data_filter import build_data_filter
#
#
# class SlotSummaryRepository:
#     def __init__(self, database_path):
#         self.database_path = database_path
#
#     def load(self, date_from, date_to, tiers, models, eqp, slot=None):
#         """Tổng hợp 48 slot và chi tiết ngày cho slot được chọn trong worker."""
#         # A machine must be selected; never silently combine machines.
#         if not eqp:
#             return SlotSummaryResult(None, [])
#         filter_sql, params = build_data_filter('TIER', tiers, models)
#         with connection(self.database_path) as conn:
#             records = conn.execute(f"""
#                 SELECT SLOT, SUM(QTY) AS in_qty,
#                        SUM(CASE WHEN RESULT = 'PASS' THEN QTY ELSE 0 END) AS pass_qty
#                 FROM prime_data
#                 WHERE EQP = ? AND DATE BETWEEN ? AND ? AND TEST_COUNT = 1
#                   {filter_sql}
#                 GROUP BY SLOT ORDER BY SLOT
#             """, [eqp, date_from, date_to, *params]).fetchall()
#         quantities = {int(r['SLOT']): (int(r['in_qty']), int(r['pass_qty'])) for r in records}
#         rows = []
#         for slot_number in range(1, 49):
#             in_qty, pass_qty = quantities.get(slot_number, (0, 0))
#             fail_qty = in_qty - pass_qty
#             rows.append(SlotSummaryRow(
#                 slot_number, in_qty, pass_qty, fail_qty,
#                 pass_qty / in_qty * 100 if in_qty else None,
#                 fail_qty / in_qty * 1_000_000 if in_qty else None))
#         return SlotSummaryResult(eqp, rows, self.load_daily(
#             date_from, date_to, tiers, models, eqp, slot) if slot is not None else None)
#
#
#     def load_daily(self, date_from, date_to, tiers, models, eqp, slot):
#         """SQL chỉ đọc lần test đầu, lọc EQP/SLOT trước khoảng DATE và GROUP BY ngày."""
#         if not eqp or slot is None:
#             return None
#         filter_sql, params = build_data_filter('TIER', tiers, models)
#         with connection(self.database_path) as conn:
#             records = conn.execute(f"""
#                 SELECT DATE, SUM(QTY) AS in_qty,
#                        SUM(CASE WHEN RESULT = 'PASS' THEN QTY ELSE 0 END) AS pass_qty
#                 FROM prime_data
#                 WHERE EQP = ? AND SLOT = ? AND DATE BETWEEN ? AND ? AND TEST_COUNT = 1
#                   {filter_sql}
#                 GROUP BY DATE ORDER BY DATE
#             """, [eqp, slot, date_from, date_to, *params]).fetchall()
#         quantities = {r['DATE']: (int(r['in_qty']), int(r['pass_qty'])) for r in records}
#         rows = []
#         day = datetime.strptime(date_from, '%Y%m%d').date()
#         end = datetime.strptime(date_to, '%Y%m%d').date()
#         while day <= end:
#             date = day.strftime('%Y%m%d')
#             in_qty, pass_qty = quantities.get(date, (0, 0))
#             rows.append(self._daily_row(date, in_qty, pass_qty))
#             day += timedelta(days=1)
#         total = self._daily_row('Total', sum(r.in_qty for r in rows), sum(r.pass_qty for r in rows))
#         return SlotDailyResult(eqp, slot, rows, total)
#
#     @staticmethod
#     def _daily_row(date, in_qty, pass_qty):
#         """Tính yield bằng Output/Input; không lấy trung bình phần trăm các ngày."""
#         return SlotDailyRow(date, in_qty, pass_qty, in_qty - pass_qty,
#                             pass_qty / in_qty * 100 if in_qty else None)
from datetime import datetime, timedelta
from domain.slot_summary import SlotDailyResult, SlotDailyRow
from database.connection import connection
from domain.slot_summary import SlotSummaryResult, SlotSummaryRow
from repositories.data_filter import build_data_filter


class SlotSummaryRepository:
    def __init__(self, database_path):
        self.database_path = database_path

    def load(self, date_from, date_to, tiers, models, eqp, slot=None):
        """Tổng hợp 48 slot và chi tiết ngày cho slot được chọn trong worker."""
        # A machine must be selected; never silently combine machines.
        if not eqp:
            return SlotSummaryResult(None, [])
        filter_sql, params = build_data_filter('TIER', tiers, models)
        with connection(self.database_path) as conn:
            records = conn.execute(f"""
                SELECT SLOT, SUM(QTY) AS in_qty,
                       SUM(CASE WHEN RESULT = 'PASS' THEN QTY ELSE 0 END) AS pass_qty
                FROM prime_data
                WHERE EQP = ? AND DATE BETWEEN ? AND ? AND TEST_COUNT = 0
                  {filter_sql}
                GROUP BY SLOT ORDER BY SLOT
            """, [eqp, date_from, date_to, *params]).fetchall()
        quantities = {int(r['SLOT']): (int(r['in_qty']), int(r['pass_qty'])) for r in records}
        rows = []
        for slot_number in range(1, 49):
            in_qty, pass_qty = quantities.get(slot_number, (0, 0))
            fail_qty = in_qty - pass_qty
            rows.append(SlotSummaryRow(
                slot_number, in_qty, pass_qty, fail_qty,
                pass_qty / in_qty * 100 if in_qty else None,
                fail_qty / in_qty * 1_000_000 if in_qty else None))
        return SlotSummaryResult(eqp, rows, self.load_daily(
            date_from, date_to, tiers, models, eqp, slot) if slot is not None else None)


    def load_daily(self, date_from, date_to, tiers, models, eqp, slot):
        """SQL chỉ đọc lần test đầu, lọc EQP/SLOT trước khoảng DATE và GROUP BY ngày."""
        if not eqp or slot is None:
            return None
        filter_sql, params = build_data_filter('TIER', tiers, models)
        with connection(self.database_path) as conn:
            records = conn.execute(f"""
                SELECT DATE, SUM(QTY) AS in_qty,
                       SUM(CASE WHEN RESULT = 'PASS' THEN QTY ELSE 0 END) AS pass_qty
                FROM prime_data
                WHERE EQP = ? AND SLOT = ? AND DATE BETWEEN ? AND ? AND TEST_COUNT = 0
                  {filter_sql}
                GROUP BY DATE ORDER BY DATE
            """, [eqp, slot, date_from, date_to, *params]).fetchall()
        quantities = {r['DATE']: (int(r['in_qty']), int(r['pass_qty'])) for r in records}
        rows = []
        day = datetime.strptime(date_from, '%Y%m%d').date()
        end = datetime.strptime(date_to, '%Y%m%d').date()
        while day <= end:
            date = day.strftime('%Y%m%d')
            in_qty, pass_qty = quantities.get(date, (0, 0))
            rows.append(self._daily_row(date, in_qty, pass_qty))
            day += timedelta(days=1)
        total = self._daily_row('Total', sum(r.in_qty for r in rows), sum(r.pass_qty for r in rows))
        return SlotDailyResult(eqp, slot, rows, total)

    @staticmethod
    def _daily_row(date, in_qty, pass_qty):
        """Tính yield bằng Output/Input; không lấy trung bình phần trăm các ngày."""
        return SlotDailyRow(date, in_qty, pass_qty, in_qty - pass_qty,
                            pass_qty / in_qty * 100 if in_qty else None)
