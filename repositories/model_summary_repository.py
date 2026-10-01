from database.connection import connection
from domain.model_summary import CumModelRow, CumModelResult


class ModelSummaryRepository:
    """Tổng hợp CUM theo Model bằng hai truy vấn, không truy vấn từng dòng."""

    def __init__(self, database_path):
        """Lưu đường dẫn; kết nối chỉ được mở trong worker."""
        self.database_path = database_path

    def load(self, date_from, date_to, tiers, conn=None):
        """Chỉ lọc From/To/Tier; tổng hợp mọi Model trên tất cả EQP."""
        if conn is None:
            with connection(self.database_path) as db:
                db.execute("BEGIN")
                return self.load(date_from, date_to, tiers, conn=db)
        selected_tiers = sorted({str(tier) for tier in tiers if tier is not None})
        if not selected_tiers:
            return CumModelResult([], [], {})
        placeholders = ', '.join('?' for _ in selected_tiers)
        where = f"data.DATE BETWEEN ? AND ? AND data.TIER IN ({placeholders})"
        params = [date_from, date_to, *selected_tiers]
        # Tổng sản lượng trước JOIN: mỗi bản ghi CUM chỉ cộng đúng một lần.
        quantities = conn.execute(f"""
            SELECT data.MODEL, SUM(data.INQTY) AS in_qty,
                   SUM(data.OUTQTY) AS out_qty
            FROM cum_data AS data WHERE {where}
            GROUP BY data.MODEL ORDER BY data.MODEL
        """, params).fetchall()
        # Index UNIQUE(cum_data_id, scrap_code) hỗ trợ JOIN từ CUM đã lọc.
        details = conn.execute(f"""
            SELECT data.MODEL, detail.scrap_code, SUM(detail.qty) AS qty
            FROM cum_data AS data
            JOIN cum_scrap_detail AS detail ON detail.cum_data_id = data.id
            WHERE {where}
            GROUP BY data.MODEL, detail.scrap_code
        """, params)
        by_model, totals = {}, {}
        for detail in details:
            code, qty = detail['scrap_code'], int(detail['qty'] or 0)
            by_model.setdefault(detail['MODEL'], {})[code] = qty
            totals[code] = totals.get(code, 0) + qty
        rows = []
        for item in quantities:
            incoming, outgoing = int(item['in_qty'] or 0), int(item['out_qty'] or 0)
            rows.append(CumModelRow(
                item['MODEL'], incoming, outgoing, incoming - outgoing,
                outgoing / incoming * 100 if incoming else None,
                by_model.get(item['MODEL'], {})))
        return CumModelResult(rows, sorted(totals), totals)
