from __future__ import annotations

from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLayout,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QScrollArea,
)


from ui.widgets.daily_summary_widget import DailySummaryWidget
from ui.clipboard_utils import enable_table_copy


class SummaryPage(QWidget):
    """Khối Cum Yield LI Summary: bảng trái, biểu đồ phải như Aging."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_scrap_codes = ()
        self._build_ui()

    def _build_ui(
        self,
    ) -> None:
        """Tạo bảng CUM bên trái và biểu đồ bên phải."""

        outer_layout = QVBoxLayout(self)

        outer_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.scroll_area = QScrollArea(self)

        self.scroll_area.setWidgetResizable(
            True
        )

        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.scroll_area.setFrameShape(
            QScrollArea.NoFrame
        )

        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("summaryContent")
        self.scroll_content.setStyleSheet("QWidget#summaryContent { background: white; }")

        main_layout = QVBoxLayout(
            self.scroll_content
        )

        main_layout.setContentsMargins(
            10,
            10,
            10,
            10,
        )

        main_layout.setSpacing(0)

        self.scroll_area.setWidget(
            self.scroll_content
        )

        outer_layout.addWidget(
            self.scroll_area
        )

        content_layout = QHBoxLayout()

        content_layout.setSpacing(28)
        content_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        today = QDate.currentDate().toString(
            "yyyyMMdd"
        )

        self.summary_title_label = QLabel(
            "Cum Yield LI Summary: "
            # f"{today} - {today}"
        )

        self.summary_title_label.setFixedHeight(24)

        self.summary_title_label.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Fixed,
        )

        self.summary_title_label.setStyleSheet(
            """
            font-size: 14px;
            font-weight: bold;
            color: #222222;
            """
        )

        #CUM SUMMARY TABLE
        self.summary_table = QTableWidget()
        self.summary_table.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.summary_table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.summary_table.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Fixed,
        )

        self.summary_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        self.summary_table.horizontalHeader().setStretchLastSection(
            False
        )

        self.summary_table.horizontalHeader().setDefaultSectionSize(
            82
        )

        self.summary_table.verticalHeader().setDefaultSectionSize(
            28
        )

        self.summary_table.horizontalHeader().setFixedHeight(
            28
        )

        self.summary_table.setStyleSheet(
            """
            QTableWidget {
                gridline-color: #222222;
                border: 1px solid #222222;
                font-size: 13px;
            }

            QHeaderView::section {
                background-color: #E2F0D9;
                color: #000000;
                font-size: 13px;
                font-weight: bold;
                border: 1px solid #222222;
                padding: 4px;
            }
            """
        )
        self.summary_table.setColumnCount(6)

        self.summary_table.setHorizontalHeaderLabels(
            [
                "EQPID",
                "In Qty",
                "Out Qty",
                "Fail Qty",
                "Fail PPM",
                "Yield",
            ]
        )

        self.summary_table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        enable_table_copy(self.summary_table)

        self.summary_table.setAlternatingRowColors(True)

        self.summary_table.verticalHeader().setVisible(
            False
        )

        self.summary_table.horizontalHeader().setStretchLastSection(
            True
        )

        self.summary_table.setMinimumWidth(520)
        self.summary_table.setMinimumHeight(330)

        #CUM SUMMARY CHART
        self.chart = None

        self.chart_container = QWidget()

        self.chart_layout = QVBoxLayout(
            self.chart_container
        )

        self.chart_layout.setContentsMargins(
            0,
            30,
            0,
            0,
        )

        self.chart_placeholder_label = QLabel(
            "Biểu đồ sẽ được tạo khi bấm SEARCH."
        )

        self.chart_placeholder_label.setAlignment(
            Qt.AlignCenter
        )

        self.chart_placeholder_label.setStyleSheet(
            "color: #777777;"
        )

        self.chart_layout.addWidget(
            self.chart_placeholder_label
        )

        left_layout = QVBoxLayout()
        left_layout.setSpacing(0)
        left_layout.addWidget(self.summary_title_label)
        left_layout.addWidget(self.summary_table)
        left_layout.addStretch()
        content_layout.addLayout(left_layout)
        content_layout.addWidget(self.chart_container, 0, Qt.AlignTop)
        content_layout.addStretch()
        main_layout.addLayout(content_layout)
        main_layout.addSpacing(24)
        self.daily_summary = DailySummaryWidget(self)
        main_layout.addWidget(self.daily_summary, 0, Qt.AlignTop)
        main_layout.addStretch()


    def set_loading(self, date_from, date_to):
        self.summary_title_label.setText(
            f"Cum Yield LI Summary: {date_from} - {date_to}")

    def load_result(self, result, key):
        self._ensure_chart()
        self._load_summary_table(result.rows, result.total)
        if result.cum_daily is not None and result.prime_daily is not None:
            self.daily_summary.load_result(result.cum_daily, result.prime_daily, self._selected_scrap_codes)
        self.chart.update_chart(result.rows)
        self.summary_title_label.setText(f"Cum Yield LI Summary: {key[0]} - {key[1]}")

    def clear_result(self, message="Dữ liệu đã cập nhật. Bấm SEARCH để tải lại."):
        self.daily_summary.clear_result(message)
        self.summary_table.setRowCount(0)
        self.summary_title_label.setText("Cum Yield LI Summary:")
        if self.chart is not None:
            self.chart.show_empty_state(message)
        elif self.chart_placeholder_label is not None:
            self.chart_placeholder_label.setText(message)

    def _load_summary_table(
        self,
        rows,
        total,
    ) -> None:
        """Đổ các dòng EQPID và dòng Total vào QTableWidget."""
        self.summary_table.setUpdatesEnabled(
            False
        )
        all_rows = [
            *rows,
            total,
        ]

        self.summary_table.setRowCount(
            len(all_rows)
        )

        for row_index, row in enumerate(all_rows):
            is_total_row = row.eqpid == "Total"

            values = [
                row.eqpid,
                f"{row.in_qty:,}",
                f"{row.out_qty:,}",
                f"{row.fail_qty:,}",
                self._format_ppm(row.fail_ppm),
                self._format_yield(
                    row.yield_percent
                ),
            ]

            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)

                if column_index == 0:
                    item.setTextAlignment(
                        Qt.AlignLeft
                        | Qt.AlignVCenter
                    )
                else:
                    item.setTextAlignment(
                        Qt.AlignRight
                        | Qt.AlignVCenter
                    )

                if is_total_row:
                    item.setBackground(
                        Qt.lightGray
                    )

                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

                self.summary_table.setItem(
                    row_index,
                    column_index,
                    item,
                )

        self._fit_table_to_content()
        self.summary_table.setUpdatesEnabled(
            True
        )

    @staticmethod
    def _format_ppm(
        value: float | None,
    ) -> str:
        """Định dạng Fail PPM để hiển thị trên bảng."""

        if value is None:
            return "—"

        return f"{value:,.0f}"

    @staticmethod
    def _format_yield(
        value: float | None,
    ) -> str:
        """Định dạng Yield phần trăm để hiển thị trên bảng."""

        if value is None:
            return "—"

        return f"{value:.2f}%"

    def _ensure_chart(
            self,
    ) -> None:
        """
        Chỉ import Matplotlib và tạo biểu đồ
        khi người dùng Apply Filter lần đầu.
        """

        if self.chart is not None:
            return

        from ui.charts.cum_eqp_chart import (
            CumEqpChart,
        )

        self.chart_layout.removeWidget(
            self.chart_placeholder_label
        )

        self.chart_placeholder_label.hide()
        self.chart_placeholder_label.deleteLater()
        self.chart_placeholder_label = None

        self.chart = CumEqpChart(self)

        self.chart_layout.addWidget(
            self.chart,
            0,
            Qt.AlignTop,
        )

    def _fit_table_to_content(
            self,
    ) -> None:
        """
        Co bảng đúng bằng số dòng và độ rộng cột.
        Không xuất hiện thanh cuộn.
        """

        self.summary_table.resizeColumnsToContents()

        table_width = (
                self.summary_table.frameWidth() * 2
        )

        for column_index in range(
                self.summary_table.columnCount()
        ):
            table_width += self.summary_table.columnWidth(
                column_index
            )

        table_height = (
                self.summary_table.frameWidth() * 2
                + self.summary_table.horizontalHeader().height()
        )

        for row_index in range(
                self.summary_table.rowCount()
        ):
            table_height += self.summary_table.rowHeight(
                row_index
            )

        self.summary_table.setFixedWidth(
            table_width + 2
        )

        self.summary_table.setFixedHeight(
            table_height + 2
        )

    def set_scrap_codes(self, codes, redraw=False):
        self._selected_scrap_codes = tuple(codes)
        if redraw:
            self.daily_summary.update_codes(codes)
