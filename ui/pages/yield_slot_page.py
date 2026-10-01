from ui.widgets.slot_daily_widget import SlotDailyWidget
from ui.widgets.model_summary_widget import ModelSummaryWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QAbstractButton, QAbstractItemView, QHeaderView, QLabel, QScrollArea,
                             QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,QSizePolicy)
from ui.clipboard_utils import enable_table_copy

def format_percent(value):
    text = f'{value:.2f}'
    if text.endswith('.00'):
        text = text[:-3]
    return f'{text}%'
class YieldSlotPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chart = None
        self._selected_scrap_codes = ()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        content = QWidget()
        content.setStyleSheet('background:white;')
        self.body = QVBoxLayout(content)
        self.title = QLabel('Prime Yield by Slot | Chọn EQP và bấm SEARCH.')
        self.title.setStyleSheet('font-size:14px; font-weight:bold;')
        self.body.addWidget(self.title)
        self.table = QTableWidget(5, 48)
        self.table.setHorizontalHeaderLabels([str(slot) for slot in range(1, 49)])
        self.table.setVerticalHeaderLabels(['In', 'PASS', 'Prime FAIL', 'Prime Yield', 'Fail PPM'])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        enable_table_copy(self.table)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        # self.table.horizontalHeader().setDefaultSectionSize(64)
        # self.table.verticalHeader().setDefaultSectionSize(28)
        # self.table.setFixedHeight(
        #     self.table.horizontalHeader().sizeHint().height()
        #     + sum(self.table.rowHeight(i) for i in range(5))
        #     + self.table.horizontalScrollBar().sizeHint().height()
        #     + self.table.frameWidth() * 2 + 6)
        # self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.table.setStyleSheet('''QTableWidget {gridline-color:#555; border:1px solid #555; font-size:12px;}
        #     QHeaderView::section {background:#C6E0B4; color:black; border:1px solid #777; padding:4px;}''')
        horizontal = self.table.horizontalHeader()
        vertical = self.table.verticalHeader()

        horizontal.setSectionResizeMode(QHeaderView.Fixed)
        horizontal.setDefaultSectionSize(80)
        horizontal.setDefaultAlignment(Qt.AlignCenter)

        vertical.setDefaultSectionSize(30)
        vertical.setDefaultAlignment(Qt.AlignCenter)

        for header in (horizontal, vertical):
            font = header.font()
            font.setBold(True)
            header.setFont(font)

        self.table.setWordWrap(False)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #555555;
                border: 1px solid #555555;
                font-size: 12px;
            }
            QHeaderView::section {
                background: #C6E0B4;
                color: black;
                border: 1px solid #777777;
                padding: 4px;
                font-weight: bold;
            }
            QScrollBar:horizontal {
                background: #E5E5E5;
                height: 10px;
                border: none;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #929292;
                min-width: 35px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #707070;
            }
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0px;
                border: none;
                background: transparent;
            }
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {
                background: #E5E5E5;
            }
        """)

        self.table.ensurePolished()
        self.table.setFixedHeight(
            horizontal.sizeHint().height()
            + sum(self.table.rowHeight(i) for i in range(self.table.rowCount()))
            + 10
            + self.table.frameWidth() * 2
            + 2
        )
        # Label inside Qt's corner button stays above In when scrolling horizontally.
        corner = self.table.findChild(QAbstractButton)
        self.slot_header = QLabel('Slot', corner)
        self.slot_header.setAlignment(Qt.AlignCenter)
        self.slot_header.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.slot_header.setStyleSheet(
            'background:#C6E0B4; color:black; border:1px solid #777;'
            'font-size:12px; font-weight:bold;'
        )
        corner_layout = QVBoxLayout(corner)
        corner_layout.setContentsMargins(0, 0, 0, 0)
        corner_layout.addWidget(self.slot_header)
        self._fit_columns()
        self.body.addWidget(self.table)
        # self.placeholder = QLabel('Biểu đồ sẽ được tạo khi bấm SEARCH.')
        # self.placeholder.setAlignment(Qt.AlignCenter)
        # self.body.addWidget(self.placeholder)
        self.placeholder = QLabel('Chọn một EQP rồi bấm SEARCH.')
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setWordWrap(True)
        self.placeholder.setFixedHeight(400)
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
        self.body.addWidget(self.placeholder)
        self.daily_summary = SlotDailyWidget(self)
        # self.body.addWidget(self.daily_summary, 0, Qt.AlignTop)
        self.body.addWidget(self.daily_summary)
        self.model_summary = ModelSummaryWidget(self)
        self.body.addWidget(self.model_summary)
        self.body.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def set_loading(self, date_from, date_to):
        self.title.setText(f'Prime Yield by Slot | {date_from} - {date_to}')

    def load_result(self, result, key):
        if result.cum_model is not None:
            self.model_summary.load_result(result.cum_model, key, self._selected_scrap_codes)
        else:
            self.model_summary.clear_result('Không có dữ liệu CUM theo Model.')
        if not result.eqp:
            self._clear_slot_result('Chọn một EQP rồi bấm SEARCH.')
            return
        self.title.setText(f'Prime Yield by Slot | {key[0]} - {key[1]} | EQP: {result.eqp}')
        self.table.setUpdatesEnabled(False)
        try:
            self.table.clearContents()
            for column, row in enumerate(result.rows):
                values = [f'{row.in_qty:,}', f'{row.pass_qty:,}', f'{row.fail_qty:,}',
                          '' if row.yield_percent is None else format_percent(row.yield_percent),
                          '' if row.fail_ppm is None else f'{row.fail_ppm:.0f}']
                for index, value in enumerate(values):
                    item = QTableWidgetItem(value)
                    item.setTextAlignment(Qt.AlignCenter)
                    if index == 3 and row.yield_percent is not None:
                        item.setBackground(QColor('#63BE7B' if row.yield_percent >= 99.8 else
                                                  '#FFEB84' if row.yield_percent >= 95 else '#F8696B'))
                    self.table.setItem(index, column, item)
            self._fit_columns()
        finally:
            self.table.setUpdatesEnabled(True)
        if self.chart is None:
            from ui.charts.slot_fail_chart import SlotFailChart

            self.chart = SlotFailChart(self)
            self.body.insertWidget(
                self.body.indexOf(self.daily_summary),
                self.chart,
            )

        self.chart.update_chart(result.rows, eqp=result.eqp)
        self.placeholder.hide()
        self.chart.show()

        self.daily_summary.load_result(result.daily, key)

    def clear_result(
            self,
            message='Dữ liệu đã cập nhật. Bấm SEARCH để tải lại.',
    ):
        self.model_summary.clear_result(message)
        self._clear_slot_result(message)

    def set_scrap_codes(self, codes, redraw=False):
        """Lưu lựa chọn và vẽ lại Cum Model từ cache khi chỉ đổi mã lỗi."""
        self._selected_scrap_codes = tuple(sorted(set(codes)))
        if redraw:
            self.model_summary.update_codes(self._selected_scrap_codes)

    def _clear_slot_result(self, message):
        """Xóa phần Slot riêng; Cum Model vẫn có thể hiển thị khi chưa chọn EQP."""
        self.daily_summary.clear_result(message)
        self.table.clearContents()
        self.title.setText('Prime Yield by Slot | ' + message)

        if self.chart is not None:
            self.chart.hide()

        self.placeholder.setText(message)
        self.placeholder.show()

    def _fit_columns(self):
        """Nới cột theo nội dung, chừa khoảng đệm để không che chữ."""
        self.table.ensurePolished()
        metrics = self.table.fontMetrics()
        header_metrics = self.table.horizontalHeader().fontMetrics()

        minimum = max(
            80,
            metrics.horizontalAdvance('1000000') + 24,
            metrics.horizontalAdvance('100.00%') + 24,
        )

        for column in range(self.table.columnCount()):
            width = minimum
            header = self.table.horizontalHeaderItem(column)
            if header is not None:
                width = max(
                    width,
                    header_metrics.horizontalAdvance(header.text()) + 24,
                )

            for row in range(self.table.rowCount()):
                item = self.table.item(row, column)
                if item is not None:
                    width = max(
                        width,
                        metrics.horizontalAdvance(item.text()) + 24,
                    )

            self.table.setColumnWidth(column, width)
