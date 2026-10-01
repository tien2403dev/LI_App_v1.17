from datetime import datetime, timedelta

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QAbstractItemView, QFrame, QHeaderView, QHBoxLayout,
                             QLabel, QScrollArea, QSizePolicy, QTableWidget, QTableWidgetItem,
                             QVBoxLayout, QWidget)

from ui.charts.dashboard_bar_chart import DashboardBarChart


class DashboardPage(QWidget):
    """Dashboard chỉ đọc và tổng hợp snapshot đang dùng bởi tab Alarm."""

    CARD_DEFINITIONS = (
        ('total_alarm', 'Total Alarm', '#EAF2FF'),
        ('not_started', 'Chưa tiến hành', '#FDEBEC'),
        ('in_progress', 'Đang thực hiện', '#FFF4D6'),
        ('completed', 'Đã hoàn thành', '#E5F5EA'),
        ('action_effectiveness', 'Action Effectiveness', '#E5F5EA'),
        ('quick_pass', 'Quick Check PASS', '#E8F4FF'),
        ('cal_pass', 'CAL Check PASS', '#EEEAFE'),
        ('monitor_day1_pass', 'Monitor Day 1 PASS', '#E9F7F5'),
        ('monitor_day2_pass', 'Monitor Day 2 PASS', '#E9F7F5'),
        ('monitor_day3_pass', 'Monitor Day 3 PASS', '#E9F7F5'),
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []
        self._date_from = ''
        self._date_to = ''
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.title_label = QLabel('Dashboard')
        self.title_label.setStyleSheet(
            'font-size:18px; font-weight:700; color:#163A5F;'
        )
        layout.addWidget(self.title_label)

        cards = QHBoxLayout()
        cards.setSpacing(8)
        self.value_labels = {}
        for key, title, background in self.CARD_DEFINITIONS:
            card = QFrame()
            card.setObjectName(f'dashboardCard_{key}')
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            card.setMinimumWidth(105)
            card.setFixedHeight(64)
            card.setStyleSheet(f'''
                QFrame#{card.objectName()} {{
                    background-color: {background};
                    border: 1px solid #B8CDE0;
                    border-radius: 9px;
                }}
                QFrame#{card.objectName()} QLabel {{
                    border: none;
                    background: transparent;
                }}
            ''')
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(8, 5, 8, 5)
            card_layout.setSpacing(1)

            label = QLabel(title)
            label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            label.setWordWrap(True)
            label.setStyleSheet('color:#4D6B8A; font-size:11px; font-weight:600;')
            value = QLabel('0')
            value.setAlignment(Qt.AlignCenter)
            value.setStyleSheet('color:#102A43; font-size:19px; font-weight:700;')
            if key == 'action_effectiveness':
                value.setStyleSheet('color:#102A43; font-size:18px; font-weight:700;')
            card_layout.addWidget(label)
            card_layout.addWidget(value, 1)
            self.value_labels[key] = value
            cards.addWidget(card, 1)

        layout.addLayout(cards)
        self.daily_table = QTableWidget(0, 11, self)
        self.daily_table.setHorizontalHeaderLabels([
            'No', 'Date', 'Số lần\nphát sinh', 'Chưa\ntiến hành',
            'Đang\nthực hiện', 'Đã\nhoàn thành', 'Action\nEffectiveness',
            'Quick Check\nPASS', 'Monitor Day 1\nPASS',
            'Monitor Day 2\nPASS', 'Monitor Day 3\nPASS',
        ])
        self.daily_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.daily_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.daily_table.verticalHeader().setVisible(False)
        header = self.daily_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setMinimumSectionSize(30)
        for column, width in enumerate((38, 96, 76, 82, 82, 82, 108, 90, 98, 98, 98)):
            header.resizeSection(column, width)
        self.daily_table.verticalHeader().setDefaultSectionSize(29)
        self.daily_table.setMinimumWidth(0)
        self.daily_table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.daily_table.setStyleSheet(
            'QTableWidget { gridline-color:#B8CDE0; background:white; font-size:13px; }'
            'QHeaderView::section { background:#F3F6FA; color:#163A5F; '
            'padding:5px 3px; font-size:12px; font-weight:600; '
            'border:1px solid #D5DEE8; }'
        )
        self.alarm_chart = DashboardBarChart('Alarm phát sinh theo ngày', daily=True)
        self.status_chart = DashboardBarChart('Trạng thái action')
        self.effectiveness_chart = DashboardBarChart('Action Effectiveness theo ngày',
                                                      percent=True, daily=True)
        body = QHBoxLayout()
        body.setSpacing(8)
        body.addWidget(self.daily_table, 5)
        for chart, stretch in ((self.alarm_chart, 6), (self.status_chart, 3),
                               (self.effectiveness_chart, 6)):
            area = QScrollArea(self)
            area.setWidgetResizable(True)
            area.setMinimumWidth(0)
            area.setFrameShape(QFrame.NoFrame)
            area.setWidget(chart)
            body.addWidget(area, stretch)
        layout.addLayout(body, 1)
        self.load_rows([])

    @staticmethod
    def _date_text(value):
        """Đưa QDate hoặc chuỗi ngày về định dạng YYYYMMDD."""
        if value is None:
            return ''
        if hasattr(value, 'toString'):
            return value.toString('yyyyMMdd')
        digits = ''.join(character for character in str(value) if character.isdigit())
        return digits if len(digits) == 8 else str(value).strip()

    def set_date_range(self, date_from=None, date_to=None):
        """Chỉ hiện khoảng ngày trên tiêu đề sau khi có đủ From và To."""
        from_text = self._date_text(date_from)
        to_text = self._date_text(date_to)
        title = f'Dashboard | {from_text} - {to_text}' if from_text and to_text else 'Dashboard'
        self.title_label.setText(title)
        self._date_from, self._date_to = from_text, to_text
        self._refresh()

    @staticmethod
    def _is_pass(value):
        return str(value or '').strip().upper() == 'PASS'

    @classmethod
    def _summarize(cls, rows):
        """Một dòng Alarm được tính là một lần phát sinh."""
        status_counts = {
            'not_started': 0,
            'in_progress': 0,
            'completed': 0,
        }
        for row in rows:
            status = str(row.get('status') or '').strip()
            if status == 'Chưa tiến hành':
                status_counts['not_started'] += 1
            elif status in ('Đang tiến hành', 'Đang thực hiện'):
                status_counts['in_progress'] += 1
            elif status in ('Đã hoàn thành', 'Hoàn thành'):
                status_counts['completed'] += 1

        values = {
            'total_alarm': len(rows),
            **status_counts,
            'quick_pass': sum(cls._is_pass(row.get('quick_check_result')) for row in rows),
            'cal_pass': sum(cls._is_pass(row.get('cal_check_result')) for row in rows),
            'monitor_day1_pass': sum(cls._is_pass(row.get('monitor_day1')) for row in rows),
            'monitor_day2_pass': sum(cls._is_pass(row.get('monitor_day2')) for row in rows),
            'monitor_day3_pass': sum(cls._is_pass(row.get('monitor_day3')) for row in rows),
        }
        values['action_effectiveness'] = (
            100.0 * values['completed'] / values['total_alarm']
            if values['total_alarm'] else 0.0
        )
        return values

    def load_rows(self, rows):
        """Đồng bộ bảng ngày và các ô tổng từ snapshot của tab Alarm."""
        self._rows = list(rows or ())
        self._refresh()

    def _refresh(self):
        rows = self._rows
        dates = None
        if self._date_from and self._date_to:
            try:
                start = datetime.strptime(self._date_from, '%Y%m%d').date()
                end = datetime.strptime(self._date_to, '%Y%m%d').date()
            except ValueError:
                pass
            else:
                dates = [(start + timedelta(days=offset)).strftime('%Y%m%d')
                         for offset in range((end - start).days + 1)]
                rows = [row for row in rows
                        if self._date_from <= self._date_text(row.get('alarm_date'))
                        <= self._date_to]
        grouped = {}
        for row in rows:
            day = self._date_text(row.get('alarm_date'))
            grouped.setdefault(day, []).append(row)
        if dates is None:
            dates = sorted(grouped)
        totals = self._summarize(rows)
        daily_counts = [self._summarize(grouped.get(day, [])) for day in dates]
        for key, value in totals.items():
            text = f'{value:.2f}%' if key == 'action_effectiveness' else str(value)
            self.value_labels[key].setText(text)

        self.daily_table.setUpdatesEnabled(False)
        try:
            self.daily_table.setRowCount(len(dates))
            for index, day in enumerate(dates):
                counts = daily_counts[index]
                date_label = f'{day[6:8]}/{day[4:6]}/{day[:4]}' if len(day) == 8 else day
                values = [index + 1, date_label, counts['total_alarm'],
                          counts['not_started'], counts['in_progress'],
                          counts['completed'], f"{counts['action_effectiveness']:.2f}%",
                          counts['quick_pass'], counts['monitor_day1_pass'],
                          counts['monitor_day2_pass'], counts['monitor_day3_pass']]
                for column, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    if column in (5, 6):
                        item.setBackground(QColor('#D9EAD3'))
                    self.daily_table.setItem(index, column, item)
        finally:
            self.daily_table.setUpdatesEnabled(True)

        date_labels = list(dates)
        self.alarm_chart.update_chart(date_labels, [c['total_alarm'] for c in daily_counts])
        self.status_chart.update_chart(
            ['Đã\nhoàn thành', 'Đang\nthực hiện', 'Chưa\ntiến hành'],
            [totals['completed'], totals['in_progress'], totals['not_started']],
            colors=['#70AD47', '#FFC000', '#FF0000'])
        self.effectiveness_chart.update_chart(
            date_labels, [c['action_effectiveness'] for c in daily_counts])
