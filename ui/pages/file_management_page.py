from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Union

from PyQt5.QtCore import (
    QThread,
    Qt,
    pyqtSignal,
)
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.filter_value_dialog import (
    FilterValueDialog,
)
from workers.database_management_worker import (
    DatabaseListWorker,
    PrimeExportWorker,
)
from ui.widgets.auto_import_scheduler_panel import (
    AutoImportSchedulerPanel,
)
from ui.widgets.loading_dialog import (
    LoadingDialog,
)
class DataListPanel(QFrame):
    """Khối danh sách DATE dùng chung cho PRIME và CUM."""

    export_clicked = pyqtSignal()

    def __init__(
        self,
        title: str,
        checkable_rows: bool,
        allow_export: bool,
        parent=None,
    ):
        super().__init__(parent)

        self.checkable_rows = checkable_rows
        self.allow_export = allow_export

        self._records = []
        self._selected_months: set[str] = set()
        self._selected_dates: set[str] = set()
        self._updating_table_checks = False

        self.setObjectName(
            "dataListPanel"
        )

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        self.setStyleSheet(
            """
            QFrame#dataListPanel {
                background-color: #FFFFFF;
                border: 1px solid #D8DEE6;
                border-radius: 8px;
            }

            QLabel#panelTitle {
                color: #0F172A;
                font-family: "Segoe UI";
                font-size: 16px;
                font-weight: 500;
                border: none;
            }

            QPushButton {
                font-family: "Segoe UI";
                font-size: 12px;
                min-height: 30px;
                padding-left: 12px;
                padding-right: 12px;
                background-color: #FFFFFF;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                border-radius: 5px;
            }

            QPushButton:hover {
                background-color: #F1F5F9;
            }

            QPushButton#exportButton {
                background-color: #1976D2;
                color: #FFFFFF;
                border: none;
                font-weight: 500;
            }

            QPushButton#exportButton:hover {
                background-color: #1565C0;
            }

            QPushButton:disabled {
                background-color: #E2E8F0;
                color: #94A3B8;
            }

            QCheckBox {
                font-family: "Segoe UI";
                font-size: 12px;
                border: none;
                color: #1E293B;
            }

            QTableWidget {
                font-family: "Segoe UI";
                font-size: 12px;
                border: 1px solid #D8DEE6;
                gridline-color: #D8DEE6;
                alternate-background-color: #F8FAFC;
                background-color: #FFFFFF;
                selection-background-color: #DBEAFE;
                selection-color: #0F172A;
            }

            QHeaderView::section {
                font-family: "Segoe UI";
                font-size: 12px;
                background-color: #F1F5F9;
                color: #0F172A;
                border: none;
                border-right: 1px solid #D8DEE6;
                border-bottom: 1px solid #D8DEE6;
                padding: 6px;
                font-weight: 600;
            }
            """
        )

        self._build_ui(title)
    def _build_ui(
        self,
        title: str,
    ) -> None:
        """Tạo tiêu đề, bộ lọc và bảng."""

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            12,
            12,
            12,
            12,
        )

        layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setObjectName(
            "panelTitle"
        )

        layout.addWidget(title_label)

        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(8)

        self.select_all_checkbox = None

        if self.checkable_rows:
            self.select_all_checkbox = QCheckBox(
                "Select All"
            )

            self.select_all_checkbox.setTristate(
                True
            )

            self.select_all_checkbox.stateChanged.connect(
                self._set_all_visible_rows_checked
            )

            toolbar_layout.addWidget(
                self.select_all_checkbox
            )

        self.month_filter_button = QPushButton(
            "Filter Month ▼"
        )

        self.date_filter_button = QPushButton(
            "Filter Date ▼"
        )

        self.month_filter_button.clicked.connect(
            self._open_month_filter
        )

        self.date_filter_button.clicked.connect(
            self._open_date_filter
        )

        toolbar_layout.addWidget(
            self.month_filter_button
        )

        toolbar_layout.addWidget(
            self.date_filter_button
        )

        if self.allow_export:
            self.export_button = QPushButton(
                "Export Prime"
            )

            self.export_button.setObjectName(
                "exportButton"
            )

            self.export_button.clicked.connect(
                self.export_clicked.emit
            )
            self.export_button.setFixedWidth(120)

            toolbar_layout.addWidget(
                self.export_button
            )

        else:
            self.export_button = None

        toolbar_layout.addStretch(1)

        layout.addLayout(toolbar_layout)

        headers = (
            [
                "",
                "Month",
                "Date",
                "Load time",
            ]
            if self.checkable_rows
            else [
                "Month",
                "Date",
                "Load time",
            ]
        )

        self.table = QTableWidget(
            0,
            len(headers),
        )

        self.table.setHorizontalHeaderLabels(
            headers
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.table.setSortingEnabled(False)

        self.table.verticalHeader().setDefaultSectionSize(
            30
        )

        header = self.table.horizontalHeader()

        if self.checkable_rows:
            header.setSectionResizeMode(
                0,
                QHeaderView.ResizeToContents,
            )

            header.setSectionResizeMode(
                1,
                QHeaderView.ResizeToContents,
            )

            header.setSectionResizeMode(
                2,
                QHeaderView.ResizeToContents,
            )

            header.setSectionResizeMode(
                3,
                QHeaderView.Stretch,
            )

            self.table.itemChanged.connect(
                self._on_table_item_changed
            )

        else:
            header.setSectionResizeMode(
                0,
                QHeaderView.ResizeToContents,
            )

            header.setSectionResizeMode(
                1,
                QHeaderView.ResizeToContents,
            )

            header.setSectionResizeMode(
                2,
                QHeaderView.Stretch,
            )

        layout.addWidget(
            self.table,
            1,
        )

    def set_records(
        self,
        records,
    ) -> None:
        """Thay dữ liệu và mặc định chọn toàn bộ filter."""

        self._records = list(records)

        self._selected_months = {
            record.month
            for record in self._records
        }

        self._selected_dates = {
            record.data_date
            for record in self._records
        }

        self._apply_filters()

    def selected_checked_dates(
        self,
    ) -> list[str]:
        """Lấy những ngày đang hiển thị và được tích."""

        if not self.checkable_rows:
            return []

        selected_dates = []

        for row_index in range(
            self.table.rowCount()
        ):
            checkbox_item = self.table.item(
                row_index,
                0,
            )

            if (
                checkbox_item.checkState()
                != Qt.Checked
            ):
                continue

            selected_dates.append(
                self.table.item(
                    row_index,
                    2,
                ).text()
            )

        return selected_dates

    def set_export_enabled(
        self,
        is_enabled: bool,
    ) -> None:
        """Khóa nút Export khi worker đang chạy."""

        if self.export_button is not None:
            self.export_button.setEnabled(
                is_enabled
            )

    def _open_month_filter(self) -> None:
        """Mở Filter Month."""

        months = sorted(
            {
                record.month
                for record in self._records
            },
            reverse=True,
        )

        dialog = FilterValueDialog(
            title="Filter Month",
            values=months,
            selected_values=(
                self._selected_months
            ),
            parent=self,
        )

        if dialog.exec_() != dialog.Accepted:
            return

        self._selected_months = (
            dialog.selected_values()
        )

        # Khi Month thay đổi, mặc định chọn
        # toàn bộ Date thuộc các Month đó.
        self._selected_dates = {
            record.data_date
            for record in self._records
            if (
                record.month
                in self._selected_months
            )
        }

        self._apply_filters()

    def _open_date_filter(self) -> None:
        """Date chỉ hiển thị theo Month đang chọn."""

        available_dates = sorted(
            {
                record.data_date
                for record in self._records
                if (
                    record.month
                    in self._selected_months
                )
            },
            reverse=True,
        )

        selected_dates = (
            self._selected_dates
            & set(available_dates)
        )

        dialog = FilterValueDialog(
            title="Filter File Date",
            values=available_dates,
            selected_values=selected_dates,
            parent=self,
        )

        if dialog.exec_() != dialog.Accepted:
            return

        self._selected_dates = (
            dialog.selected_values()
        )

        self._apply_filters()

    def _apply_filters(self) -> None:
        """Render danh sách DATE nhỏ sau khi lọc."""

        visible_records = [
            record
            for record in self._records
            if (
                record.month
                in self._selected_months
                and record.data_date
                in self._selected_dates
            )
        ]

        self._updating_table_checks = True
        self.table.blockSignals(True)
        self.table.setUpdatesEnabled(False)

        try:
            self.table.setRowCount(
                len(visible_records)
            )

            for (
                row_index,
                record,
            ) in enumerate(visible_records):
                column_offset = 0

                if self.checkable_rows:
                    checkbox_item = (
                        QTableWidgetItem()
                    )

                    checkbox_item.setFlags(
                        Qt.ItemIsEnabled
                        | Qt.ItemIsUserCheckable
                    )

                    checkbox_item.setCheckState(
                        Qt.Unchecked
                    )

                    checkbox_item.setTextAlignment(
                        Qt.AlignCenter
                    )

                    self.table.setItem(
                        row_index,
                        0,
                        checkbox_item,
                    )

                    column_offset = 1

                values = (
                    record.month,
                    record.data_date,
                    record.load_time or "—",
                )

                for (
                    value_index,
                    value,
                ) in enumerate(values):
                    item = QTableWidgetItem(
                        value
                    )

                    item.setTextAlignment(
                        Qt.AlignCenter
                    )

                    self.table.setItem(
                        row_index,
                        column_offset
                        + value_index,
                        item,
                    )

        finally:
            self.table.setUpdatesEnabled(
                True
            )

            self.table.blockSignals(False)

            self._updating_table_checks = (
                False
            )

        self._update_table_select_all_state()

    def _set_all_visible_rows_checked(
        self,
        state: int,
    ) -> None:
        """Chọn tất cả dòng PRIME đang hiển thị."""

        if (
            not self.checkable_rows
            or self._updating_table_checks
        ):
            return

        target_state = (
            Qt.Checked
            if state != Qt.Unchecked
            else Qt.Unchecked
        )

        self._updating_table_checks = True
        self.table.blockSignals(True)

        try:
            for row_index in range(
                self.table.rowCount()
            ):
                self.table.item(
                    row_index,
                    0,
                ).setCheckState(
                    target_state
                )

        finally:
            self.table.blockSignals(False)

            self._updating_table_checks = (
                False
            )

        self._update_table_select_all_state()

    def _on_table_item_changed(
        self,
        item: QTableWidgetItem,
    ) -> None:
        """Đồng bộ Select All khi chọn từng dòng."""

        if (
            self._updating_table_checks
            or item.column() != 0
        ):
            return

        self._update_table_select_all_state()

    def _update_table_select_all_state(
        self,
    ) -> None:
        """Cập nhật checked/partial/unchecked."""

        if not self.checkable_rows:
            return

        row_count = self.table.rowCount()

        checked_count = sum(
            1
            for row_index in range(row_count)
            if (
                self.table.item(
                    row_index,
                    0,
                ).checkState()
                == Qt.Checked
            )
        )

        if checked_count == 0:
            state = Qt.Unchecked

        elif checked_count == row_count:
            state = Qt.Checked

        else:
            state = Qt.PartiallyChecked

        self._updating_table_checks = True

        self.select_all_checkbox.blockSignals(
            True
        )

        try:
            self.select_all_checkbox.setCheckState(
                state
            )

            self.select_all_checkbox.setEnabled(
                row_count > 0
            )

        finally:
            self.select_all_checkbox.blockSignals(
                False
            )

            self._updating_table_checks = (
                False
            )

class FileManagementPage(QWidget):
    """Quản lý danh sách ngày PRIME/CUM và export PRIME."""

    def __init__(
        self,
        database_path: Union[str, Path],
        parent=None,
    ):
        super().__init__(parent)

        self.database_path = Path(
            database_path
        )

        self.list_thread = None
        self.list_worker = None

        self.export_thread = None
        self.export_worker = None
        self.export_loading_dialog = None

        self._dirty_types = {
            "PRIME",
            "CUM",
        }

        self._loading_types: set[str] = set()

        self._reload_types_after_load: set[str] = (
            set()
        )

        self._export_result = None
        self._export_error = None

        self._closing = False
        self.list_loading_dialog = None
        self._build_ui()

    def _build_ui(self) -> None:
        """Đặt PRIME bên trái và CUM bên phải."""

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            12,
            12,
            12,
            12,
        )

        layout.setSpacing(8)

        self.refresh_button = QPushButton("REFRESH DATA LIST")
        self.refresh_button.setToolTip(
            "Tải lại danh sách PRIME/CUM khi dữ liệu được cập nhật bên ngoài app."
        )
        self.refresh_button.clicked.connect(lambda: self.load_if_needed(force=True))
        layout.addWidget(self.refresh_button, 0, Qt.AlignRight)

        panels_layout = QHBoxLayout()
        panels_layout.setSpacing(12)

        self.prime_panel = DataListPanel(
            title="Prime Data List",
            checkable_rows=True,
            allow_export=True,
            parent=self,
        )

        self.cum_panel = DataListPanel(
            title="Cum Data List",
            checkable_rows=False,
            allow_export=False,
            parent=self,
        )
        self.auto_import_panel = (
            AutoImportSchedulerPanel(
                database_path=self.database_path,
                parent=self,
            )
        )

        self.prime_panel.export_clicked.connect(
            self._choose_export_path
        )

        panels_layout.addWidget(
            self.prime_panel,
            1,
        )

        panels_layout.addWidget(
            self.cum_panel,
            1,
        )
        panels_layout.addWidget(
            self.auto_import_panel,
            0,
            Qt.AlignTop,
        )

        layout.addLayout(
            panels_layout,
            1,
        )

        self.status_label = QLabel()

        self.status_label.setStyleSheet(
            "color: #64748B; padding: 2px;"
        )

        self.status_label.hide()

        layout.addWidget(
            self.status_label
        )

    def load_if_needed(
        self,
        force: bool = False,
    ) -> None:
        """Lazy-load và không chạy trùng worker."""

        if self._closing:
            return
        if force:
            self._dirty_types.update(
                {"PRIME", "CUM"}
            )

        if not self._dirty_types:
            return

        # Giữ quyền sở hữu thread đến khi slot finished đã dọn xong.
        if self.list_thread is not None:
            if force:
                self._reload_types_after_load.update({"PRIME", "CUM"})
            return

        self._loading_types = set(
            self._dirty_types
        )

        self.status_label.hide()
        self.list_loading_dialog = LoadingDialog(parent=self, text="Loading ...")
        self.list_loading_dialog.show()

        self.list_thread = QThread(self)

        self.list_worker = DatabaseListWorker(
            database_path=self.database_path,
            data_types=self._loading_types,
        )

        self.list_worker.moveToThread(
            self.list_thread
        )

        self.list_thread.started.connect(
            self.list_worker.run
        )

        self.list_worker.succeeded.connect(
            self._on_lists_loaded
        )

        self.list_worker.failed.connect(
            self._on_lists_failed
        )

        self.list_worker.succeeded.connect(
            self.list_thread.quit
        )

        self.list_worker.failed.connect(
            self.list_thread.quit
        )

        self.list_thread.finished.connect(
            self.list_worker.deleteLater
        )

        self.list_thread.finished.connect(
            self._on_list_thread_finished
        )

        self.list_thread.start()

    def mark_data_changed(
        self,
        data_type: str,
    ) -> None:
        """Đánh dấu đúng bảng cần tải lại sau import."""

        normalized_type = (
            data_type.strip().upper()
        )

        if normalized_type not in {
            "PRIME",
            "CUM",
        }:
            return

        self._dirty_types.add(
            normalized_type
        )

        if self.list_thread is not None:
            self._reload_types_after_load.add(
                normalized_type
            )
            return

        if self.isVisible():
            self.load_if_needed()

    def is_busy(self) -> bool:
        """Kiểm tra worker danh sách hoặc export."""

        return self.list_thread is not None or self.export_thread is not None

    def _on_lists_loaded(
        self,
        result: dict,
    ) -> None:
        """Đổ dữ liệu vào bảng trên UI thread."""

        if "PRIME" in result:
            self.prime_panel.set_records(
                result["PRIME"]
            )

        if "CUM" in result:
            self.cum_panel.set_records(
                result["CUM"]
            )

        self._dirty_types.difference_update(
            self._loading_types
        )

        self._dirty_types.update(
            self._reload_types_after_load
        )

        self.status_label.hide()

    def _on_lists_failed(
        self,
        error_message: str,
    ) -> None:
        """Hiển thị lỗi query."""

        self.status_label.setText(
            "Không thể tải danh sách dữ liệu: "
            f"{error_message}"
        )

        self.status_label.setStyleSheet(
            "color: #C62828; padding: 2px;"
        )

        self.status_label.show()

    def _on_list_thread_finished(
        self,
    ) -> None:
        """Dọn worker và reload nếu import vừa hoàn thành."""

        if self.list_loading_dialog is not None:
            self.list_loading_dialog.close()
            self.list_loading_dialog.deleteLater()
            self.list_loading_dialog = None
        if self.list_thread is not None:
            self.list_thread.deleteLater()

        self.list_thread = None
        self.list_worker = None
        self._loading_types = set()

        should_reload = bool(
            self._reload_types_after_load
        )

        self._reload_types_after_load.clear()

        if (
            should_reload
            and self._dirty_types
        ):
            self.load_if_needed()

    def _choose_export_path(self) -> None:
        """Kiểm tra ngày rồi chọn nơi lưu Excel."""

        selected_dates = (
            self.prime_panel.selected_checked_dates()
        )

        if not selected_dates:
            QMessageBox.warning(
                self,
                "Chưa chọn dữ liệu",
                (
                    "Vui lòng tích ít nhất một ngày "
                    "PRIME để export."
                ),
            )
            return


        default_name = (
            "LI_PrimeData_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            ".xlsx"
        )

        output_path, _ = (
            QFileDialog.getSaveFileName(
                self,
                "Lưu dữ liệu PRIME",
                default_name,
                "Excel Files (*.xlsx)",
            )
        )

        if not output_path:
            return

        self._start_export(
            selected_dates=selected_dates,
            output_path=Path(output_path),
        )

    def _start_export(
        self,
        selected_dates: list[str],
        output_path: Path,
    ) -> None:
        """Chạy export streaming trong QThread."""

        if (
            self.export_thread is not None
            and self.export_thread.isRunning()
        ):
            return

        self._export_result = None
        self._export_error = None

        self.prime_panel.set_export_enabled(
            False
        )

        self.export_loading_dialog = LoadingDialog(
            parent=self,
            text="Loading...",
            title="Please Wait",
        )

        self.export_loading_dialog.show()

        self.export_thread = QThread(self)

        self.export_worker = PrimeExportWorker(
            database_path=self.database_path,
            business_dates=selected_dates,
            output_path=output_path,
        )

        self.export_worker.moveToThread(
            self.export_thread
        )

        self.export_thread.started.connect(
            self.export_worker.run
        )

        self.export_worker.succeeded.connect(
            self._on_export_succeeded
        )

        self.export_worker.failed.connect(
            self._on_export_failed
        )

        self.export_worker.succeeded.connect(
            self.export_thread.quit
        )

        self.export_worker.failed.connect(
            self.export_thread.quit
        )

        self.export_thread.finished.connect(
            self.export_worker.deleteLater
        )

        self.export_thread.finished.connect(
            self._on_export_thread_finished
        )

        self.export_thread.start()

    def _on_export_succeeded(
        self,
        result,
    ) -> None:
        """Lưu kết quả chờ thread dọn xong."""

        self._export_result = result

        self._close_export_loading_dialog()

    def _on_export_failed(
        self,
        error_message: str,
    ) -> None:
        """Lưu lỗi chờ thread dọn xong."""

        self._export_error = error_message

        self._close_export_loading_dialog()

    def _close_export_loading_dialog(
        self,
    ) -> None:
        """Đóng thông báo loading của export."""

        if self.export_loading_dialog is None:
            return

        self.export_loading_dialog.close()

        self.export_loading_dialog.deleteLater()

        self.export_loading_dialog = None

    def _on_export_thread_finished(
        self,
    ) -> None:
        """Dọn worker và hiển thị kết quả."""

        self._close_export_loading_dialog()

        if self.export_thread is not None:
            self.export_thread.deleteLater()

        self.export_thread = None
        self.export_worker = None

        self.prime_panel.set_export_enabled(
            True
        )

        if self._closing:
            return
        if self._export_error is not None:
            QMessageBox.critical(
                self,
                "Export PRIME thất bại",
                self._export_error,
            )

            self._export_error = None
            return

        if self._export_result is None:
            return

        result = self._export_result
        self._export_result = None

        QMessageBox.information(
            self,
            "Export PRIME thành công",
            "Export PRIME thành công.\n\n"
            f"Số dòng: "
            f"{result.exported_row_count:,}\n"
            f"Số sheet: {result.sheet_count}\n"
            f"File: {result.output_path}",
        )

    def prepare_close(self):
        """Ngừng tải lại và chờ worker hoàn tất trước khi đóng cửa sổ."""
        self._closing = True
        self._reload_types_after_load.clear()
