"""Dựng HTML mail LI từ alarm đã lưu; không tính lại hay thay đổi alarm."""
from html import escape
from datetime import datetime


def text(value):
    """Escape dữ liệu log trước khi đưa vào HTML."""
    return escape('' if value is None else str(value))


def percent(value):
    """Hiển thị phần trăm; không biến thiếu dữ liệu thành 0%."""
    return '—' if value is None else f'{float(value):.2f}%'


def date_label(value):
    """Chuyển ngày DB sang ngày/tháng/năm."""
    return datetime.strptime(value, '%Y%m%d').strftime('%d/%m/%Y')


def table(headers, rows):
    """Bảng viền mảnh và header xanh theo mẫu Aging, tương thích QTextBrowser."""
    parts = ['<table border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse;border-color:#CBD5E1;">', '<tr>']
    parts += [f'<th bgcolor="#0D6EFD" style="color:white;">{text(h)}</th>' for h in headers]
    parts.append('</tr>')
    for row in rows:
        parts.append('<tr>' + ''.join(f'<td align="center">{text(v)}</td>' for v in row) + '</tr>')
    parts.append('</table>')
    return ''.join(parts)


class MailContentBuilder:
    @staticmethod
    def build_alarm_body_html(target_dates, alarms):
        """Nhóm theo Alarm Date, EQP/Slot và quy tắc; luôn giữ Model."""
        parts = ['<div style="font-family:Segoe UI,Arial;font-size:10pt;color:#0F172A;">']
        for day in target_dates:
            daily = [a for a in alarms if a['alarm_date'] == day]
            if not daily:
                continue
            parts.append(f'<p><b>Alarm ngày: {date_label(day)}</b></p>')
            for alarm in daily:
                parts.append(f'<p><b>EQP: {text(alarm["eqp"])} &nbsp;&amp;&nbsp; Slot: {text(alarm["slot"])}</b></p>')
                evidence = alarm['evidence']
                if alarm['runs']:
                    for run in alarm['runs']:
                        mixed = run.get('different_scrap', False)
                        threshold = alarm['different_scrap_fail_count_used'] if mixed else alarm['continuous_fail_count_used']
                        kind = 'khác Scrap code &amp; cùng Model' if mixed else 'cùng Scrapcode &amp; Model'
                        parts.append('<p style="color:#FF3547;"><b>Alarm Type: FAIL liên tục ≥ '
                                     f'{text(threshold)} lần {kind}</b></p>')
                        rows = [[date_label(r['DATE']),
                                 f"{r['DATE'][:4]}-{r['DATE'][4:6]}-{r['DATE'][6:]} {r['TIME']}",
                                 r['MODEL'], r['LOTNO'], r['SCRAPCODE'], r['QTY']] for r in run['details']]
                        parts.append(table(['File Date', 'Date time', 'Model', 'Lot ID', 'Scrap code', 'Fail qty'], rows))
                        if not rows:
                            parts.append('<p>Không còn log chi tiết của chuỗi FAIL này trong database.</p>')
                sizes = [size for size in (15, 30) if str(size) in evidence]
                if sizes:
                    kind = ' và '.join(f'Fail hiệu suất thấp {size} lần liên tục' for size in sizes)
                    parts.append(f'<p style="color:#FF3547;"><b>Alarm Type: {kind}</b></p>')
                    # Mỗi cửa sổ có thể thuộc Model/thời điểm khác nhau: không gộp sai một hàng.
                    rows = []
                    for size in sizes:
                        window = evidence[str(size)]
                        rows.append([window['start'], window['end'], window['model'],
                                     percent(alarm['yield_15']) if size == 15 else '—', percent(alarm['target_15']),
                                     percent(alarm['yield_30']) if size == 30 else '—', percent(alarm['target_30'])])
                    parts.append(table(['Start time', 'End time', 'Model',
                                        'Yield 15', 'Target 15', 'Yield 30', 'Target 30'], rows))
                if not alarm['runs'] and not sizes:
                    parts.append(f'<p>Alarm Type: {text(alarm["fail_comment"])}</p>')
                    parts.append('<p>Không có bằng chứng chi tiết đã lưu cho alarm này.</p>')
        parts.append('</div>')
        return ''.join(parts)
