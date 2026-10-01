from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView, QLabel, QLayout, QSizePolicy, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from ui.clipboard_utils import enable_table_copy


class DailySummaryWidget(QWidget):
    EMPTY_DAILY_WIDTH = 520
    EMPTY_DAILY_HEIGHT = 60
    DAILY_CHART_PLACEHOLDER_TEXT = "Chọn EQP và Scrap Code rồi bấm SEARCH để vẽ biểu đồ Daily."

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scroll_content = self
        self._cached_daily_result = None
        self._cached_prime_daily_result = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        for prefix, title in [("daily", "Cum"), ("prime_daily", "Prime")]:
            label = QLabel(f"{title} Yield LI Daily | Vui lòng chọn EQP")
            label.setFixedHeight(24)
            label.setStyleSheet("font-size:14px; font-weight:bold; color:#222222;")
            table = self._create_empty_daily_table()
            container = QWidget()
            chart_layout = QVBoxLayout(container)
            chart_layout.setContentsMargins(0, 0, 0, 0)
            chart_layout.setSizeConstraint(QLayout.SetFixedSize)
            placeholder = QLabel(self.DAILY_CHART_PLACEHOLDER_TEXT)
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setFixedSize(self.EMPTY_DAILY_WIDTH, self.EMPTY_DAILY_HEIGHT)
            placeholder.setStyleSheet("color:#777777; border:1px solid #D9D9D9; background:white;")
            chart_layout.addWidget(placeholder)
            for suffix, value in [("title_label", label), ("table", table), ("chart", None), ("chart_layout", chart_layout), ("chart_placeholder_label", placeholder)]:
                setattr(self, f"{prefix}_{suffix}", value)
            layout.addWidget(label)
            layout.addWidget(table, 0, Qt.AlignLeft)
            layout.addWidget(container, 0, Qt.AlignLeft)

    def load_result(self, cum, prime, codes):
        self._cached_daily_result = cum
        self._cached_prime_daily_result = prime
        self._load_daily_table(cum)
        self._load_prime_daily_table(prime)
        self._load_daily_chart(cum, codes)
        self._load_prime_daily_chart(prime, codes)

    def update_codes(self, codes):
        if self._cached_daily_result is not None:
            self._load_daily_chart(self._cached_daily_result, codes)
        if self._cached_prime_daily_result is not None:
            self._load_prime_daily_chart(self._cached_prime_daily_result, codes)

    def clear_result(self, message):
        from domain.daily_summary import CumDailyResult, PrimeDailyResult
        self._load_daily_table(CumDailyResult(None, [], []))
        self._load_prime_daily_table(PrimeDailyResult(None, [], []))
        self._show_daily_chart_message(message)
        self._show_prime_daily_chart_message(message)

    def _ensure_daily_chart(
            self,
    ) -> bool:
        """
        Chỉ import Matplotlib và tạo chart Daily
        sau khi người dùng bấm Apply Filter.
        """

        if self.daily_chart is not None:
            return False

        from ui.charts.cum_daily_chart import (
            CumDailyStackedChart,
        )

        self.daily_chart_layout.removeWidget(
            self.daily_chart_placeholder_label
        )

        self.daily_chart_placeholder_label.hide()
        self.daily_chart_placeholder_label.deleteLater()
        self.daily_chart_placeholder_label = None

        self.daily_chart = CumDailyStackedChart(
            self
        )

        self.daily_chart_layout.addWidget(
            self.daily_chart,
            0,
            Qt.AlignLeft,
        )
        return True


    def _load_daily_chart(
            self,
            daily_result,
            selected_scrap_codes: list[str],
    ) -> None:
        """
        Vẽ chart bằng các Scrap Code đang được tick.

        Bảng Daily vẫn giữ toàn bộ mã lỗi.
        """
        if not daily_result.eqpid:
            self._show_daily_chart_message(
                self.DAILY_CHART_PLACEHOLDER_TEXT
            )
            return

        if not selected_scrap_codes:
            self._show_daily_chart_message(
                self.DAILY_CHART_PLACEHOLDER_TEXT
            )
            return

        available_codes = set(
            daily_result.scrap_codes
        )

        has_available_code = any(
            code in available_codes
            for code in selected_scrap_codes
        )

        if not has_available_code:
            self._show_daily_chart_message(
                "Các Scrap Code được chọn "
                "không phát sinh dữ liệu."
            )
            return

        chart_was_created = (
            self._ensure_daily_chart()
        )

        self.daily_chart.update_chart(
            daily_result=daily_result,
            selected_scrap_codes=(
                selected_scrap_codes
            ),
        )

        # Chart có kích thước cố định.
        # Chỉ adjust layout khi tạo lần đầu.
        if chart_was_created:
            self.scroll_content.adjustSize()


    def _show_daily_chart_message(
            self,
            message: str,
    ) -> None:
        """Hiển thị trạng thái của chart Daily."""

        if self.daily_chart is not None:
            self.daily_chart.show_empty_state(
                message
            )

            return

        self.daily_chart_placeholder_label.setText(
            message
        )


    def _load_daily_table(
            self,
            result,
    ) -> None:
        """Hiển thị hiệu suất từng ngày của EQP được chọn."""

        # if not result.eqpid:
        #     self.daily_title_label.setText(
        #         "Cum Yield LI Daily | "
        #         "Chọn EQP"
        #     )
        #     self.daily_table.setUpdatesEnabled(
        #         False
        #     )
        #     self.daily_table.clear()
        #     self.daily_table.setRowCount(0)
        #     self.daily_table.setColumnCount(0)
        #     self.daily_table.setFixedSize(
        #         520,
        #         80,
        #     )
        #
        #     self.scroll_content.adjustSize()
        #     return
        if not result.eqpid:
            self._cached_daily_result = None

            self.daily_title_label.setText(
                "Cum Yield LI Daily | "
                "Chọn EQP"
            )

            self.daily_table.setUpdatesEnabled(False)

            try:
                self.daily_table.clear()
                self.daily_table.setRowCount(0)
                self.daily_table.setColumnCount(0)

                self.daily_table.setFixedSize(
                    self.EMPTY_DAILY_WIDTH,
                    self.EMPTY_DAILY_HEIGHT,
                )
            finally:
                # Bắt buộc phải bật lại để Qt xóa
                # dữ liệu cũ đang hiển thị trên màn hình.
                self.daily_table.setUpdatesEnabled(True)

            self.daily_table.viewport().update()
            self.scroll_content.adjustSize()
            return

        self.daily_title_label.setText(
            "Cum Yield LI Daily | "
            f"EQP: {result.eqpid}"
        )

        fixed_headers = [
            "Date",
            "In Qty",
            "Pass",
            "Fail Qty",
            "Fail PPM",
            "Yield",
        ]

        headers = [
            *fixed_headers,
            *result.scrap_codes,
        ]

        self.daily_table.clear()

        self.daily_table.setColumnCount(
            len(headers)
        )

        self.daily_table.setHorizontalHeaderLabels(
            headers
        )

        self.daily_table.setRowCount(
            len(result.rows)
        )

        for row_index, row in enumerate(
                result.rows
        ):
            fixed_values = [
                row.date,
                f"{row.in_qty:,}",
                f"{row.out_qty:,}",
                f"{row.fail_qty:,}",
                self._format_daily_ppm(
                    row.fail_ppm
                ),
                self._format_daily_yield(
                    row.yield_percent
                ),
            ]

            for column_index, value in enumerate(
                    fixed_values
            ):
                self._set_daily_item(
                    row_index=row_index,
                    column_index=column_index,
                    value=value,
                )

            for code_offset, scrap_code in enumerate(
                    result.scrap_codes
            ):
                scrap_ppm = row.scrap_ppm_by_code.get(
                    scrap_code
                )

                value = (
                    ""
                    if scrap_ppm is None
                    else self._format_daily_ppm(
                        scrap_ppm
                    )
                )

                self._set_daily_item(
                    row_index=row_index,
                    column_index=(
                            len(fixed_headers)
                            + code_offset
                    ),
                    value=value,
                )

        self._fit_daily_table_to_content()
        self.daily_table.setUpdatesEnabled(
            True
        )


    def _set_daily_item(
            self,
            row_index: int,
            column_index: int,
            value: str,
            table: QTableWidget | None = None,
    ) -> None:
        """Tạo ô và căn giữa toàn bộ dữ liệu bảng Daily."""

        target_table = (
            table
            if table is not None
            else self.daily_table
        )

        item = QTableWidgetItem(value)

        item.setTextAlignment(
            Qt.AlignCenter
        )

        target_table.setItem(
            row_index,
            column_index,
            item,
        )


    def _fit_daily_table_to_content(
            self,
            table: QTableWidget | None = None,
    ) -> None:
        """
        Co bảng vừa đủ toàn bộ cột và dòng.

        Nếu không truyền table thì mặc định
        sử dụng bảng Cum Daily.
        """

        target_table = (
            table
            if table is not None
            else self.daily_table
        )

        target_table.resizeColumnsToContents()

        for row_index in range(
                target_table.rowCount()
        ):
            target_table.setRowHeight(
                row_index,
                24,
            )

        table_width = (
                target_table.frameWidth() * 2
        )

        for column_index in range(
                target_table.columnCount()
        ):
            table_width += (
                target_table.columnWidth(
                    column_index
                )
            )

        table_height = (
                target_table.frameWidth() * 2
                + target_table.horizontalHeader().height()
        )

        for row_index in range(
                target_table.rowCount()
        ):
            table_height += (
                target_table.rowHeight(
                    row_index
                )
            )

        target_table.setFixedSize(
            table_width + 2,
            table_height + 2,
        )

        self.scroll_content.adjustSize()


    @staticmethod
    def _format_daily_ppm(
            value: float | None,
    ) -> str:
        """
        Làm tròn PPM và không sử dụng
        dấu phẩy phân cách hàng nghìn.
        """

        if value is None:
            return ""

        return f"{value:.0f}"


    @staticmethod
    def _format_daily_yield(
            value: float | None,
    ) -> str:
        """Định dạng Yield; không có dữ liệu thì để trống."""

        if value is None:
            return ""

        return f"{value:.2f}%"


    def _create_empty_daily_table(
            self,
    ) -> QTableWidget:
        """Tạo bảng Daily rỗng có giao diện giống CUM Daily."""

        table = QTableWidget()

        table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        enable_table_copy(table)

        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)

        table.setVerticalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        table.setSizePolicy(
            QSizePolicy.Fixed,
            QSizePolicy.Fixed,
        )

        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )

        table.horizontalHeader().setFixedHeight(24)
        table.verticalHeader().setDefaultSectionSize(24)

        table.setStyleSheet(
            """
            QTableWidget {
                gridline-color: #D9D9D9;
                border: 1px solid #BFBFBF;
                background-color: white;
                alternate-background-color: #F8FAFC;
                font-size: 12px;
            }

            QHeaderView::section {
                background-color: #E2F0D9;
                color: #000000;
                font-size: 12px;
                font-weight: bold;
                border: 1px solid #BFBFBF;
                padding: 4px 8px;
            }
            """
        )

        table.setRowCount(0)
        table.setColumnCount(0)

        table.setFixedSize(
            self.EMPTY_DAILY_WIDTH,
            self.EMPTY_DAILY_HEIGHT,
        )

        return table


    def _load_prime_daily_table(
            self,
            result,
    ) -> None:
        """Hiển thị hiệu suất PRIME từng ngày của EQP."""

        if not result.eqpid:
            self._cached_prime_daily_result = None

            self.prime_daily_title_label.setText(
                "Prime Yield LI Daily | "
                "Chọn EQP"
            )

            self.prime_daily_table.setUpdatesEnabled(
                False
            )

            try:
                self.prime_daily_table.clear()
                self.prime_daily_table.setRowCount(0)
                self.prime_daily_table.setColumnCount(0)

                self.prime_daily_table.setFixedSize(
                    self.EMPTY_DAILY_WIDTH,
                    self.EMPTY_DAILY_HEIGHT,
                )
            finally:
                self.prime_daily_table.setUpdatesEnabled(
                    True
                )

            self.prime_daily_table.viewport().update()
            self.scroll_content.adjustSize()
            return

        self.prime_daily_title_label.setText(
            "Prime Yield LI Daily | "
            f"EQP: {result.eqpid}"
        )

        fixed_headers = [
            "Date",
            "In Qty",
            "Pass",
            "Fail Qty",
            "Fail PPM",
            "Yield",
        ]

        headers = [
            *fixed_headers,
            *result.scrap_codes,
        ]

        self.prime_daily_table.setUpdatesEnabled(
            False
        )

        try:
            self.prime_daily_table.clear()

            self.prime_daily_table.setColumnCount(
                len(headers)
            )

            self.prime_daily_table.setHorizontalHeaderLabels(
                headers
            )

            self.prime_daily_table.setRowCount(
                len(result.rows)
            )

            for row_index, row in enumerate(
                    result.rows
            ):
                fixed_values = [
                    row.date,
                    f"{row.in_qty:,}",
                    f"{row.out_qty:,}",
                    f"{row.fail_qty:,}",
                    self._format_daily_ppm(
                        row.fail_ppm
                    ),
                    self._format_daily_yield(
                        row.yield_percent
                    ),
                ]

                for column_index, value in enumerate(
                        fixed_values
                ):
                    self._set_daily_item(
                        row_index=row_index,
                        column_index=column_index,
                        value=value,
                        table=self.prime_daily_table,
                    )

                for code_offset, scrap_code in enumerate(
                        result.scrap_codes
                ):
                    scrap_ppm = (
                        row.scrap_ppm_by_code.get(
                            scrap_code
                        )
                    )

                    value = (
                        ""
                        if scrap_ppm is None
                        else self._format_daily_ppm(
                            scrap_ppm
                        )
                    )

                    self._set_daily_item(
                        row_index=row_index,
                        column_index=(
                                len(fixed_headers)
                                + code_offset
                        ),
                        value=value,
                        table=self.prime_daily_table,
                    )

            self._fit_daily_table_to_content(
                table=self.prime_daily_table
            )

        finally:
            self.prime_daily_table.setUpdatesEnabled(
                True
            )


    def _ensure_prime_daily_chart(
            self,
    ) -> bool:
        """Tạo chart Prime Daily khi cần hiển thị."""

        if self.prime_daily_chart is not None:
            return False

        from ui.charts.cum_daily_chart import (
            CumDailyStackedChart,
        )

        self.prime_daily_chart_layout.removeWidget(
            self.prime_daily_chart_placeholder_label
        )

        self.prime_daily_chart_placeholder_label.hide()
        self.prime_daily_chart_placeholder_label.deleteLater()
        self.prime_daily_chart_placeholder_label = None

        self.prime_daily_chart = CumDailyStackedChart(
            self,
            chart_title="Prime Yield LI Daily",
            empty_data_message=(
                "Không có dữ liệu PRIME Daily."
            ),
        )

        self.prime_daily_chart_layout.addWidget(
            self.prime_daily_chart,
            0,
            Qt.AlignLeft,
        )

        return True


    def _load_prime_daily_chart(
            self,
            daily_result,
            selected_scrap_codes: list[str],
    ) -> None:
        """Vẽ chart Prime theo Scrap Code được chọn."""

        if not daily_result.eqpid:
            self._show_prime_daily_chart_message(
                self.DAILY_CHART_PLACEHOLDER_TEXT
            )
            return

        if not selected_scrap_codes:
            self._show_prime_daily_chart_message(
                self.DAILY_CHART_PLACEHOLDER_TEXT
            )
            return

        available_codes = set(
            daily_result.scrap_codes
        )

        has_available_code = any(
            code in available_codes
            for code in selected_scrap_codes
        )

        if not has_available_code:
            self._show_prime_daily_chart_message(
                "Các Scrap Code được chọn "
                "không phát sinh dữ liệu."
            )
            return

        chart_was_created = (
            self._ensure_prime_daily_chart()
        )

        self.prime_daily_chart.update_chart(
            daily_result=daily_result,
            selected_scrap_codes=(
                selected_scrap_codes
            ),
        )

        if chart_was_created:
            self.scroll_content.adjustSize()


    def _show_prime_daily_chart_message(
            self,
            message: str,
    ) -> None:
        """Hiển thị trạng thái chart Prime Daily."""

        if self.prime_daily_chart is not None:
            self.prime_daily_chart.show_empty_state(
                message
            )
            return

        self.prime_daily_chart_placeholder_label.setText(
            message
        )

