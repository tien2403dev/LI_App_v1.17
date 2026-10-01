from __future__ import annotations

from pathlib import Path
from typing import Union

from PyQt5.QtCore import (
    QThread,
    QTimer,
)
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
)

from repositories.mail_template_repository import (
    MailTemplateRepository,
)
from workers.mail_template_preview_worker import (
    MailTemplatePreviewWorker,
)


class MailTemplateDialog(QDialog):
    """Chỉnh sửa và lưu Mail Template."""

    def __init__(
        self,
        database_path: Union[str, Path],
        parent=None,
    ):
        """Tạo cửa sổ theo Aging; tải dữ liệu sau khi hiển thị."""
        super().__init__(parent)

        self.database_path = Path(
            database_path
        )

        self.repository = MailTemplateRepository(
            self.database_path
        )

        self.preview_thread = None
        self.preview_worker = None
        self.target_date = None
        self._close_pending = False

        self.setWindowTitle(
            "Customize Email Template"
        )

        self.resize(
            1100,
            730,
        )

        self.setMinimumSize(
            700,
            620,
        )

        self._build_ui()
        for field in (self.subject_edit, self.heading_edit, self.closing_edit):
            field.setReadOnly(True)

        # Chờ dialog hiển thị rồi mới tải dữ liệu.
        QTimer.singleShot(
            0,
            self._start_preview_load,
        )

    def _build_ui(self) -> None:
        """Bố trí Subject, Heading, Body Preview, Closing và nút lưu."""
        self.setStyleSheet(
            """
            QDialog {
                background-color: #F8FAFC;
            }

            QLabel {
                color: #0F3B8F;
                font-family: "Segoe UI";
                font-size: 13px;
                font-weight: 600;
            }

            QLineEdit,
            QTextEdit,
            QTextBrowser {
                background-color: #FFFFFF;
                color: #0F172A;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                font-family: "Segoe UI";
                font-size: 13px;
            }

            QLineEdit {
                min-height: 32px;
                padding-left: 8px;
                padding-right: 8px;
            }

            QTextEdit {
                padding: 6px;
            }

            QTextBrowser {
                padding: 4px;
            }

            QPushButton {
                min-height: 36px;
                min-width: 140px;
                padding-left: 16px;
                padding-right: 16px;
                border-radius: 6px;
                font-family: "Segoe UI";
                font-size: 13px;
                font-weight: 500;
            }

            QPushButton#saveButton {
                background-color: #0D6EFD;
                color: #FFFFFF;
                border: none;
            }

            QPushButton#saveButton:hover {
                background-color: #0B5ED7;
            }

            QPushButton#closeButton {
                background-color: #FFFFFF;
                color: #0D47A1;
                border: 1px solid #0D6EFD;
            }

            QPushButton:disabled {
                background-color: #CBD5E1;
                color: #64748B;
            }
            """
        )

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            24,
            20,
            24,
            20,
        )

        layout.setSpacing(10)

        subject_label = QLabel(
            "Subject  *"
        )

        self.subject_edit = QLineEdit()

        heading_label = QLabel(
            "Heading"
        )

        self.heading_edit = QTextEdit()
        self.heading_edit.setFixedHeight(
            62
        )

        body_label = QLabel(
            "Body Preview  (auto-generated)"
        )

        self.body_preview = QTextBrowser()
        self.body_preview.setOpenExternalLinks(
            False
        )

        self.body_preview.setHtml(
            """
            <div style="
                color:#64748B;
                font-style:italic;
            ">
                Đang tải nội dung email...
            </div>
            """
        )

        closing_label = QLabel(
            "Closing"
        )

        self.closing_edit = QTextEdit()
        self.closing_edit.setFixedHeight(
            62
        )

        button_layout = QHBoxLayout()
        button_layout.addStretch(1)

        self.close_button = QPushButton(
            "Close"
        )

        self.close_button.setObjectName(
            "closeButton"
        )

        self.save_button = QPushButton(
            "Save"
        )

        self.save_button.setObjectName(
            "saveButton"
        )

        self.save_button.setEnabled(
            False
        )

        self.close_button.clicked.connect(
            self._request_close
        )

        self.save_button.clicked.connect(
            self._save_template
        )

        button_layout.addWidget(
            self.close_button
        )

        button_layout.addWidget(
            self.save_button
        )

        layout.addWidget(subject_label)
        layout.addWidget(self.subject_edit)

        layout.addWidget(heading_label)
        layout.addWidget(self.heading_edit)

        layout.addWidget(body_label)

        layout.addWidget(
            self.body_preview,
            1,
        )

        layout.addWidget(closing_label)
        layout.addWidget(self.closing_edit)

        layout.addSpacing(4)
        layout.addLayout(button_layout)

    def _start_preview_load(self) -> None:
        """Tải template và Alarm hôm nay/hôm qua trong worker."""

        if self.is_busy() or self._close_pending:
            return

        self.save_button.setEnabled(
            False
        )

        self.preview_thread = QThread(self)

        self.preview_worker = (
            MailTemplatePreviewWorker(
                database_path=self.database_path
            )
        )

        self.preview_worker.moveToThread(
            self.preview_thread
        )

        self.preview_thread.started.connect(
            self.preview_worker.run
        )

        self.preview_worker.succeeded.connect(
            self._on_preview_loaded
        )

        self.preview_worker.failed.connect(
            self._on_preview_failed
        )

        self.preview_worker.succeeded.connect(
            self.preview_thread.quit
        )

        self.preview_worker.failed.connect(
            self.preview_thread.quit
        )

        self.preview_thread.finished.connect(
            self.preview_worker.deleteLater
        )

        self.preview_thread.finished.connect(
            self._on_preview_finished
        )

        self.preview_thread.finished.connect(
            self.preview_thread.deleteLater
        )

        self.preview_thread.start()

    def _on_preview_loaded(
        self,
        result,
    ) -> None:
        """Hiển thị template và Body Preview."""

        self.target_date = result.target_date
        for field in (self.subject_edit, self.heading_edit, self.closing_edit):
            field.setReadOnly(False)

        self.subject_edit.setText(
            result.template.subject
        )

        self.heading_edit.setPlainText(
            result.template.heading
        )

        self.closing_edit.setPlainText(
            result.template.closing
        )

        self.body_preview.setHtml(
            result.body_html
        )

        self.save_button.setEnabled(
            True
        )

    def _on_preview_failed(
        self,
        error_message: str,
    ) -> None:
        """Hiển thị lỗi tải Email Preview."""

        self.body_preview.setHtml(
            """
            <div style="
                color:#DC2626;
                font-weight:600;
            ">
                Không thể tải nội dung email.
            </div>
            """
        )

        QMessageBox.critical(
            self,
            "Không thể tải Email Preview",
            error_message,
        )

    def _on_preview_finished(self) -> None:
        """Dọn QThread tải preview."""

        self.preview_worker = None
        self.preview_thread = None
        if self._close_pending:
            self.reject()

    def _save_template(self) -> None:
        """Lưu Subject, Heading và Closing."""

        subject = (
            self.subject_edit
            .text()
            .strip()
        )

        if not subject:
            QMessageBox.warning(
                self,
                "Thiếu Subject",
                "Subject không được để trống.",
            )

            self.subject_edit.setFocus()
            return

        self.save_button.setEnabled(
            False
        )

        try:
            self.repository.save_template(
                subject=subject,
                heading=(
                    self.heading_edit
                    .toPlainText()
                ),
                closing=(
                    self.closing_edit
                    .toPlainText()
                ),
            )

            QMessageBox.information(
                self,
                "Lưu Mail Template thành công",
                (
                    "Đã lưu Mail Template "
                    "vào database."
                ),
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Không thể lưu Mail Template",
                str(error),
            )

        finally:
            self.save_button.setEnabled(
                True
            )

    def _request_close(self) -> None:
        """Ghi nhận đóng; đợi worker kết thúc an toàn nếu đang tải."""
        self.reject()

    def is_busy(self) -> bool:
        """Giữ dialog tới khi callback dọn thread hoàn tất."""
        return self.preview_thread is not None

    def reject(self) -> None:
        """Áp dụng cùng cơ chế đóng cho Close và phím Escape."""
        self._close_pending = True
        if self.is_busy():
            self.setEnabled(False)
            return
        super().reject()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Đóng bằng dấu X cũng phải bảo vệ worker đang chạy."""
        self.reject()
        if self.is_busy():
            event.ignore()
        else:
            event.accept()
