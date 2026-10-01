from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QKeySequence
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from ui.clipboard_utils import enable_table_copy, copy_selected_table_cells


class CopyableTableWidget(QTableWidget):
    """Cho phép chọn nhiều ô và copy sang Excel bằng Ctrl+C."""

    def __init__(self, parent=None):
        super().__init__(0, 5, parent)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            self.copy_selection()
            event.accept()
            return

        if event.matches(QKeySequence.SelectAll):
            self.selectAll()
            event.accept()
            return

        super().keyPressEvent(event)

    def copy_selection(self):
        copy_selected_table_cells(self)


def format_percent(value):
    """Để trống khi thiếu dữ liệu; bỏ .00 khi phần trăm tròn."""
    if value is None:
        return ''

    text = f'{value:.2f}'
    if text.endswith('.00'):
        text = text[:-3]
    return f'{text}%'


class SlotDailyWidget(QWidget):
    """Bảng ngày bên trái, biểu đồ giãn hết chiều rộng còn lại."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart = None
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 24, 0, 0)

        self.title = QLabel(
            'Daily Prime Yield by Slot | Chọn EQP và SLOT.'
        )
        self.title.setStyleSheet(
            'font-size:14px; font-weight:bold;'
        )
        layout.addWidget(self.title)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(28)

        self.table = CopyableTableWidget(self)
        enable_table_copy(self.table)
        self.table.setHorizontalHeaderLabels(
            ['Day', 'Input', 'Output', 'Prime Fail', 'Prime Yield']
        )
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.horizontalHeader().setFixedHeight(28)
        self.table.horizontalHeader().setDefaultAlignment(
            Qt.AlignCenter
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        self.table.setWordWrap(False)
        self.table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        self.table.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #222222;
                border: 1px solid #222222;
                font-size: 13px;
                selection-background-color: #3399FF;
                selection-color: white;
            }
            QHeaderView::section {
                background: #C6E0B4;
                color: black;
                font-weight: bold;
                border: 1px solid #222222;
                padding: 4px;
            }
        """)
        row.addWidget(self.table, 0, Qt.AlignTop)

        self.chart_layout = QVBoxLayout()
        self.chart_layout.setContentsMargins(0, 0, 0, 0)
        self.chart_layout.setSpacing(0)

        # self.placeholder = QLabel(
        #     'Chọn EQP và SLOT rồi bấm SEARCH.'
        # )
        # self.placeholder.setAlignment(Qt.AlignCenter)
        # self.placeholder.setFixedHeight(536)
        # self.placeholder.setMinimumWidth(0)
        # self.placeholder.setSizePolicy(
        #     QSizePolicy.Expanding,
        #     QSizePolicy.Fixed,
        # )
        # self.chart_layout.addWidget(self.placeholder)
        self.placeholder = QLabel(
            'Chọn EQP và SLOT rồi bấm SEARCH.'
        )
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setWordWrap(True)
        self.placeholder.setFixedHeight(300)
        self.placeholder.setMinimumWidth(0)
        self.placeholder.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )
        self.placeholder.setStyleSheet("""
            QLabel {
                background: white;
                border: 1px solid #BFBFBF;
                color: #404040;
                font-size: 13px;
            }
        """)
        self.chart_layout.addWidget(
            self.placeholder,
            0,
            Qt.AlignTop,
        )

        # Biểu đồ nhận toàn bộ chiều ngang còn lại.
        # Không thêm khoảng stretch ở bên phải biểu đồ.
        row.addLayout(self.chart_layout, 1)
        layout.addLayout(row)

        self._fit_table()

    def load_result(self, result, key):
        """Đổ kết quả vào bảng và biểu đồ."""
        if result is None:
            self.clear_result('Chọn một SLOT rồi bấm SEARCH.')
            return

        self.title.setText(
            f'Daily Prime Yield by Slot | {key[0]} - {key[1]} | '
            f'EQP: {result.eqp} | Slot: {result.slot}'
        )

        self.table.setUpdatesEnabled(False)
        try:
            self.table.clearSelection()
            rows = [*result.rows, result.total]
            self.table.setRowCount(len(rows))

            for index, data in enumerate(rows):
                total = data.date == 'Total'

                # Ngày nguồn đã có định dạng YYYYMMDD.
                day = 'Total' if total else str(data.date)

                values = [
                    day,
                    f'{data.in_qty:,}',
                    f'{data.pass_qty:,}',
                    f'{data.fail_qty:,}',
                    format_percent(data.yield_percent),
                ]

                for column, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setToolTip(str(data.date))

                    if total:
                        item.setBackground(QColor('#C6E0B4'))
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)

                    elif column == 4 and data.yield_percent is not None:
                        color = (
                            '#63BE7B'
                            if data.yield_percent >= 99.8
                            else '#FFEB84'
                            if data.yield_percent >= 95
                            else '#F8696B'
                        )
                        item.setBackground(QColor(color))

                    self.table.setItem(index, column, item)

            self._fit_table()
        finally:
            self.table.setUpdatesEnabled(True)

        if self.chart is None:
            from ui.charts.slot_daily_chart import SlotDailyChart

            self.chart = SlotDailyChart(self)
            self.chart.setMinimumWidth(0)
            self.chart.setMaximumWidth(16777215)
            self.chart.setFixedHeight(536)
            self.chart.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed,
            )
            self.chart_layout.addWidget(
                self.chart,
                0,
                Qt.AlignTop,
            )

        self.chart.update_chart(result)
        self.placeholder.hide()
        self.chart.show()

    def clear_result(self, message):
        """Trở lại khung chờ khi chưa có lựa chọn hợp lệ."""
        self.title.setText(
            'Daily Prime Yield by Slot | ' + message
        )
        self.table.clearSelection()
        self.table.setRowCount(0)
        self._fit_table()

        if self.chart is not None:
            self.chart.hide()

        self.placeholder.setText(message)
        self.placeholder.show()

    def _fit_table(self):
        """Bảng trống cao 300px; có dữ liệu thì cao theo số hàng."""
        self.table.ensurePolished()
        self.table.resizeColumnsToContents()

        # Giữ cột Day đủ rộng cho YYYYMMDD ngay khi chưa có dữ liệu.
        day_width = (
                self.table.fontMetrics().horizontalAdvance('20260930')
                + 24
        )
        self.table.setColumnWidth(
            0,
            max(self.table.columnWidth(0), day_width),
        )

        width = (
                sum(
                    self.table.columnWidth(column)
                    for column in range(self.table.columnCount())
                )
                + self.table.frameWidth() * 2
                + 2
        )

        if self.table.rowCount() == 0:
            height = 300
        else:
            height = (
                    self.table.horizontalHeader().height()
                    + sum(
                self.table.rowHeight(row)
                for row in range(self.table.rowCount())
            )
                    + self.table.frameWidth() * 2
                    + 2
            )

        self.table.setFixedWidth(width)
        self.table.setFixedHeight(height)

    def _fit_table(self):
        """Vừa nội dung; cuộn dọc bằng thanh cuộn chung của trang."""
        self.table.ensurePolished()
        self.table.resizeColumnsToContents()

        width = (
            sum(
                self.table.columnWidth(column)
                for column in range(self.table.columnCount())
            )
            + self.table.frameWidth() * 2
            + 2
        )
        height = (
            self.table.horizontalHeader().height()
            + sum(
                self.table.rowHeight(row)
                for row in range(self.table.rowCount())
            )
            + self.table.frameWidth() * 2
            + 2
        )

        self.table.setFixedWidth(width)
        self.table.setFixedHeight(height)
