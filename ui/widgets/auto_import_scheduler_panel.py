from __future__ import annotations

from pathlib import Path
from typing import Union

from PyQt5.QtCore import QTime
from PyQt5.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTimeEdit,
    QVBoxLayout,
)

from repositories.auto_import_scheduler_repository import (
    AutoImportSchedulerRepository,
)


class AutoImportSchedulerPanel(QFrame):
    """
    Khung cấu hình tự động import
    PRIME hằng ngày.
    """

    def __init__(
        self,
        database_path: Union[str, Path],
        parent=None,
    ):
        super().__init__(parent)

        self.database_path = Path(
            database_path
        )

        self.repository = (
            AutoImportSchedulerRepository(
                database_path=(
                    self.database_path
                )
            )
        )

        self.setObjectName(
            "autoImportSchedulerPanel"
        )

        self.setFixedWidth(440)

        self._build_ui()
        self._load_config()

    def _build_ui(self) -> None:
        """Tạo giao diện Auto Import Log."""

        self.setStyleSheet(
            """
            QFrame#autoImportSchedulerPanel {
                background-color: #FFFFFF;
                border: 1px solid #D8DEE6;
                border-radius: 8px;
            }

            QLabel,
            QCheckBox {
                border: none;
                color: #0F172A;
                font-family: "Segoe UI";
                font-size: 13px;
            }

            QLabel#autoImportTitle {
                font-size: 16px;
                font-weight: 500;
            }

            QLabel#fieldLabel {
                font-weight: 500;
            }

            QLineEdit,
            QTimeEdit {
                font-family: "Segoe UI";
                font-size: 12px;
                min-height: 30px;
                background-color: #FFFFFF;
                color: #0F172A;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding-left: 8px;
                padding-right: 8px;
            }

            QPushButton {
                font-family: "Segoe UI";
                font-size: 12px;
                min-height: 32px;
                padding-left: 14px;
                padding-right: 14px;
                background-color: #1976D2;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                font-weight: 500;
            }

            QPushButton:hover {
                background-color: #1565C0;
            }

            QPushButton:pressed {
                background-color: #0D47A1;
            }
            """
        )

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            14,
            14,
            14,
            14,
        )

        layout.setSpacing(10)

        title_label = QLabel(
            "Auto Import Prime Log"
        )

        title_label.setObjectName(
            "autoImportTitle"
        )

        self.enable_checkbox = QCheckBox(
            "Enable Auto Import Prime Log"
        )

        time_label = QLabel(
            "Import Time"
        )

        time_label.setObjectName(
            "fieldLabel"
        )

        self.time_edit = QTimeEdit()

        self.time_edit.setDisplayFormat(
            "HH:mm"
        )

        self.time_edit.setFixedWidth(
            120
        )

        folder_label = QLabel(
            "Log Folder "
            "(Folder chứa log của tất cả thiết bị)"
        )

        folder_label.setObjectName(
            "fieldLabel"
        )

        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(8)

        self.folder_edit = QLineEdit()

        self.folder_edit.setPlaceholderText(
            "Chọn folder gốc chứa log PRIME"
        )

        self.select_folder_button = QPushButton(
            "Select Folder"
        )

        self.select_folder_button.setFixedWidth(
            112
        )

        self.select_folder_button.clicked.connect(
            self._select_folder
        )

        folder_layout.addWidget(
            self.folder_edit,
            1,
        )

        folder_layout.addWidget(
            self.select_folder_button
        )

        self.save_button = QPushButton(
            "Save"
        )

        self.save_button.setFixedWidth(
            120
        )

        self.save_button.clicked.connect(
            self._save_config
        )

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            self.enable_checkbox
        )

        layout.addWidget(
            time_label
        )

        layout.addWidget(
            self.time_edit
        )

        layout.addWidget(
            folder_label
        )

        layout.addLayout(
            folder_layout
        )

        layout.addWidget(
            self.save_button
        )

        layout.addStretch(1)

    def _load_config(self) -> None:
        """
        Đọc cấu hình đã lưu trong
        database lên giao diện.
        """

        try:
            config = (
                self.repository.get_config()
            )

            configured_time = (
                QTime.fromString(
                    config.import_time,
                    "HH:mm",
                )
            )

            if not configured_time.isValid():
                configured_time = QTime(
                    3,
                    0,
                )

            self.enable_checkbox.setChecked(
                config.enabled
            )

            self.time_edit.setTime(
                configured_time
            )

            self.folder_edit.setText(
                config.log_folder
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Không thể tải cấu hình",
                str(error),
            )

    def _select_folder(self) -> None:
        """
        Chọn folder gốc chứa toàn bộ
        log PRIME.
        """

        current_folder = (
            self.folder_edit
            .text()
            .strip()
        )

        selected_folder = (
            QFileDialog.getExistingDirectory(
                self,
                "Chọn folder chứa log PRIME",
                current_folder,
            )
        )

        if selected_folder:
            self.folder_edit.setText(
                selected_folder
            )

    def _save_config(self) -> None:
        """
        Chỉ lưu cấu hình Auto Import
        vào database.
        """

        enabled = (
            self.enable_checkbox
            .isChecked()
        )

        import_time = (
            self.time_edit
            .time()
            .toString("HH:mm")
        )

        log_folder = (
            self.folder_edit
            .text()
            .strip()
        )

        if enabled and not log_folder:
            QMessageBox.warning(
                self,
                "Thiếu Log Folder",
                (
                    "Vui lòng chọn folder "
                    "chứa log PRIME."
                ),
            )
            return

        self.save_button.setEnabled(
            False
        )

        try:
            self.repository.save_config(
                enabled=enabled,
                import_time=import_time,
                log_folder=log_folder,
            )

            QMessageBox.information(
                self,
                "Lưu cấu hình thành công",
                "Đã lưu cấu hình Auto Import.",
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Không thể lưu Auto Import",
                (
                    "Không thể ghi cấu hình "
                    "vào database.\n\n"
                    f"Chi tiết: {error}"
                ),
            )

        finally:
            self.save_button.setEnabled(
                True
            )