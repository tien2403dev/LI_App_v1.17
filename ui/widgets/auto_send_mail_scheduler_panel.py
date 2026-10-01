from __future__ import annotations

from pathlib import Path
from typing import Union

from PyQt5.QtCore import QTime
from PyQt5.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QTimeEdit,
    QVBoxLayout,
)

from repositories.auto_send_mail_scheduler_repository import (
    AutoSendMailSchedulerRepository,
)


class AutoSendMailSchedulerPanel(QGroupBox):
    """Khung cấu hình Auto Send Mail."""

    def __init__(
            self,
            database_path: Union[str, Path],
            parent=None,
    ):
        """Khởi tạo đối tượng và các thành phần liên quan."""
        super().__init__(parent)
        self.setTitle(
            "Auto Send Mail"
        )

        self.database_path = Path(
            database_path
        )

        self.repository = (
            AutoSendMailSchedulerRepository(
                self.database_path
            )
        )

        self.setObjectName(
            "autoSendMailPanel"
        )

        self.setMaximumHeight(
            260
        )

        self._build_ui()
        self._load_config()

    def _build_ui(self) -> None:
        """Tạo giao diện theo bố cục tab Send Mail của Aging."""
        self.setStyleSheet(
            """
            QGroupBox#autoSendMailPanel {
                background-color: #FFFFFF;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                border-radius: 7px;
                margin-top: 12px;
                font-size: 14px;
                font-weight: 600;
            }

            QGroupBox#autoSendMailPanel::title {
                subcontrol-origin: margin;
                left: 12px;
                padding-left: 5px;
                padding-right: 5px;
            }

            QLabel,
            QCheckBox {
                border: none;
                color: #0F172A;
                font-family: "Segoe UI";
                font-size: 13px;
            }

            QLabel#fieldLabel {
                font-weight: 600;
            }

            QTimeEdit {
                min-height: 30px;
                background-color: #FFFFFF;
                color: #0F172A;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding-left: 8px;
                padding-right: 8px;
            }

            QPushButton {
                min-height: 32px;
                padding-left: 14px;
                padding-right: 14px;
                background-color: #1976D2;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                font-weight: 500;
                font-size: 12px;
            }

            QPushButton:hover {
                background-color: #1565C0;
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

        self.enable_checkbox = QCheckBox(
            "Enable Auto Send Mail"
        )

        time_label = QLabel(
            "Send Time"
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
            self.enable_checkbox
        )

        layout.addWidget(
            time_label
        )

        layout.addWidget(
            self.time_edit
        )

        layout.addWidget(
            self.save_button
        )

        layout.addStretch(1)

    def _load_config(self) -> None:
        """Đọc cấu hình Auto Send Mail vào checkbox và giờ gửi."""
        try:
            config = (
                self.repository.get_config()
            )

            configured_time = (
                QTime.fromString(
                    config.send_time,
                    "HH:mm",
                )
            )

            if not configured_time.isValid():
                configured_time = QTime(
                    8,
                    0,
                )

            self.enable_checkbox.setChecked(
                config.enabled
            )

            self.time_edit.setTime(
                configured_time
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Không thể tải cấu hình",
                str(error),
            )

    def _save_config(self) -> None:
        """Lưu Enable và giờ gửi để tác vụ auto_send_mail_main sử dụng."""
        enabled = (
            self.enable_checkbox
            .isChecked()
        )

        send_time = (
            self.time_edit
            .time()
            .toString("HH:mm")
        )

        self.save_button.setEnabled(
            False
        )

        try:
            self.repository.save_config(
                enabled=enabled,
                send_time=send_time,
            )

            QMessageBox.information(
                self,
                "Lưu cấu hình thành công",
                (
                    "Đã lưu cấu hình "
                    "Auto Send Mail. Tác vụ auto_send_mail_main sẽ đọc cấu hình này khi chạy bằng Task Scheduler."
                ),
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Không thể lưu Auto Send Mail",
                str(error),
            )

        finally:
            self.save_button.setEnabled(
                True
            )