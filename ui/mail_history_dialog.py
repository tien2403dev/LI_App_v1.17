from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from repositories.mail_send_repository import (
    MailHistoryDetail,
)


class MailHistoryDialog(QDialog):
    """Hiển thị snapshot email đã gửi thành công."""

    def __init__(
        self,
        detail: MailHistoryDetail,
        parent=None,
    ):
        """Khởi tạo đối tượng và các thành phần liên quan."""
        super().__init__(parent)

        self.detail = detail

        self.setWindowTitle(
            "Mail History"
        )

        self.resize(
            1180,
            720,
        )

        self.setMinimumSize(
            850,
            560,
        )

        self._build_ui()

    def _build_ui(self) -> None:
        """Tạo giao diện theo bố cục tab Send Mail của Aging."""
        self.setStyleSheet(
            """
            QDialog {
                background-color: #F8FAFC;
            }

            QLabel#sectionTitle {
                color: #111827;
                font-size: 15px;
                font-weight: 700;
            }

            QLabel#fieldName {
                color: #111827;
                font-size: 13px;
                font-weight: 700;
            }

            QLabel#fieldValue {
                color: #111827;
                font-size: 13px;
            }

            QTextBrowser {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                font-size: 13px;
            }

            QPushButton {
                min-width: 95px;
                min-height: 32px;
                background-color: #FFFFFF;
                color: #0D47A1;
                border: 1px solid #0D6EFD;
                border-radius: 5px;
            }

            QPushButton:hover {
                background-color: #EFF6FF;
            }
            """
        )

        root_layout = QVBoxLayout(self)

        root_layout.setContentsMargins(
            16,
            16,
            16,
            12,
        )

        root_layout.setSpacing(12)

        information_title = QLabel(
            "Mail Information"
        )

        information_title.setObjectName(
            "sectionTitle"
        )

        root_layout.addWidget(
            information_title
        )

        information_layout = QGridLayout()

        information_layout.setContentsMargins(
            8,
            4,
            8,
            4,
        )

        information_layout.setHorizontalSpacing(
            14
        )

        information_layout.setVerticalSpacing(
            8
        )

        information_layout.setColumnStretch(
            1,
            1,
        )

        fields = [
            (
                "Alarm Date",
                self.detail.alarm_date,
            ),
            (
                "Send Time",
                self.detail.sent_at,
            ),
            (
                "Sender",
                self.detail.sender,
            ),
            (
                "Receiver",
                self.detail.receivers,
            ),
            (
                "CC",
                self.detail.cc,
            ),
            (
                "Result",
                self.detail.result,
            ),
        ]

        for row_index, (
            name,
            value,
        ) in enumerate(fields):
            name_label = QLabel(
                name
            )

            name_label.setObjectName(
                "fieldName"
            )

            name_label.setAlignment(
                Qt.AlignRight
                | Qt.AlignTop
            )

            name_label.setMinimumWidth(
                72
            )

            value_label = QLabel(
                value or "-"
            )

            value_label.setObjectName(
                "fieldValue"
            )

            value_label.setWordWrap(
                True
            )

            value_label.setTextInteractionFlags(
                Qt.TextSelectableByMouse
            )

            information_layout.addWidget(
                name_label,
                row_index,
                0,
            )

            information_layout.addWidget(
                value_label,
                row_index,
                1,
            )

        root_layout.addLayout(
            information_layout
        )

        separator = QFrame()

        separator.setFrameShape(
            QFrame.HLine
        )

        separator.setFrameShadow(
            QFrame.Sunken
        )

        root_layout.addWidget(
            separator
        )

        content_title = QLabel(
            "Email Content"
        )

        content_title.setObjectName(
            "sectionTitle"
        )

        root_layout.addWidget(
            content_title
        )

        self.content_browser = QTextBrowser()

        self.content_browser.setOpenExternalLinks(
            False
        )

        self.content_browser.setHtml(
            self.detail.html_content
        )

        root_layout.addWidget(
            self.content_browser,
            1,
        )

        button_layout = QHBoxLayout()
        button_layout.addStretch(1)

        close_button = QPushButton(
            "Close"
        )

        close_button.clicked.connect(
            self.accept
        )

        button_layout.addWidget(
            close_button
        )

        root_layout.addLayout(
            button_layout
        )