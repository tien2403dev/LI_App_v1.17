from datetime import datetime, timedelta


def sync_prime_tiers(conn, prime_dates, cancel=None):
    """Tính TIER theo LOT và ngày CUM sớm nhất trong cửa sổ PRIME P đến P+4."""
    from domain.prime import check_cancel
    for day in sorted(set(prime_dates)):
        check_cancel(cancel)
        end = (datetime.strptime(day, "%Y%m%d") + timedelta(days=4)).strftime("%Y%m%d")
        conn.execute("""UPDATE prime_data AS prime SET TIER = (
            SELECT cum.TIER FROM cum_data AS cum
            WHERE cum.LOTID = prime.LOTNO AND cum.DATE BETWEEN ? AND ?
            ORDER BY cum.DATE LIMIT 1) WHERE prime.DATE = ?""", (day, end, day))


def sync_after_cum(conn, cum_dates, cancel=None):
    """Tính lại PRIME từ C-4 đến C khi dữ liệu CUM ngày C thay đổi."""
    dates = {(datetime.strptime(day, "%Y%m%d") - timedelta(days=offset)).strftime("%Y%m%d")
             for day in cum_dates for offset in range(5)}
    sync_prime_tiers(conn, dates, cancel)
