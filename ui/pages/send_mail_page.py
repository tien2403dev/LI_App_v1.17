from __future__ import annotations

from pathlib import Path
from typing import Union
from PyQt5.QtCore import (
    QThread,
    QTimer,
    Qt,
)
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from repositories.mail_configuration_repository import (
    MailConfigurationRepository,
)
from ui.mail_party_dialogs import (
    MailRecipientDialog,
    MailSenderDialog,
)

from repositories.mail_send_repository import (
    MailSendRepository,
)
from ui.mail_history_dialog import (
    MailHistoryDialog,
)
from ui.widgets.auto_send_mail_scheduler_panel import (
    AutoSendMailSchedulerPanel,
)
class SendMailTab(QWidget):
    """Quản lý Sender và Receiver/CC."""

    def __init__(
        self,
        database_path: Union[str, Path],
        parent=None,
    ):
        """Khởi tạo đối tượng và các thành phần liên quan."""
        super().__init__(parent)

        self.database_path = Path(
            database_path
        )

        self.repository = (
            MailConfigurationRepository(
                self.database_path
            )
        )
        self.mail_send_repository = (
            MailSendRepository(
                self.database_path
            )
        )

        self._closing = False
        self._mail_histories = []
        self._loaded = False
        self._senders = []
        self._recipients = []
        self.template_dialog = None
        self.login_thread = None
        self.login_worker = None

        self.setObjectName("sendMailPage")
        self._build_ui()

    def _build_ui(self) -> None:
        """Tạo giao diện theo bố cục tab Send Mail của Aging."""
        self.setStyleSheet(
            """
            QWidget#sendMailPage { background-color: #FFFFFF; }

            QGroupBox {
                background-color: #FFFFFF;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                border-radius: 7px;
                margin-top: 12px;
                font-size: 14px;
                font-weight: 600;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding-left: 5px;
                padding-right: 5px;
            }

            QTableWidget {
                background-color: #FFFFFF;
                alternate-background-color: #F8FAFC;
                border: 1px solid #CBD5E1;
                gridline-color: #CBD5E1;
                font-size: 12px;
            }

            QHeaderView::section {
                background-color: #E2E8F0;
                color: #1E293B;
                min-height: 30px;
                border: none;
                border-right: 1px solid #CBD5E1;
                border-bottom: 1px solid #94A3B8;
                font-weight: 600;
                font-size: 12px;
            }

            QPushButton {
                min-height: 30px;
                min-width: 80px;
                padding-left: 12px;
                padding-right: 12px;
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

            QPushButton#deleteButton {
                background-color: #DC2626;
            }

            QPushButton#deleteButton:hover {
                background-color: #B91C1C;
            }

            QPushButton:disabled { background-color: #94A3B8; color: #F1F5F9; }

            QComboBox {
                min-height: 26px;
                font-size: 12px;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding-left: 6px;
                background-color: #FFFFFF;
            }
            """
        )

        root_layout = QVBoxLayout(self)

        root_layout.setContentsMargins(
            12,
            12,
            12,
            12,
        )

        root_layout.setSpacing(12)
        tables_layout = QHBoxLayout()
        tables_layout.setSpacing(12)

        sender_group = QGroupBox(
            "Sender"
        )
        sender_group.setMaximumHeight(
            260
        )

        sender_layout = QVBoxLayout(
            sender_group
        )

        self.sender_table = QTableWidget(
            0,
            5,
        )

        self.sender_table.setHorizontalHeaderLabels(
            [
                "ID",
                "User ID",
                "Name",
                "Password",
                "Enable",
            ]
        )

        self._configure_table(
            self.sender_table
        )
        self.sender_table.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.sender_table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.sender_table.setColumnWidth(
            0,
            55,
        )

        self.sender_table.setColumnWidth(
            1,
            110,
        )

        self.sender_table.horizontalHeader(
        ).setSectionResizeMode(
            2,
            QHeaderView.Stretch,
        )

        self.sender_table.setColumnWidth(
            3,
            100,
        )

        self.sender_table.setColumnWidth(
            4,
            75,
        )

        sender_button_layout = QHBoxLayout()

        self.add_sender_button = QPushButton(
            "Add"
        )

        self.delete_sender_button = QPushButton(
            "Delete"
        )

        self.delete_sender_button.setObjectName(
            "deleteButton"
        )

        self.add_sender_button.clicked.connect(
            self._add_sender
        )

        self.delete_sender_button.clicked.connect(
            self._delete_sender
        )

        sender_button_layout.addWidget(
            self.add_sender_button
        )

        sender_button_layout.addWidget(
            self.delete_sender_button
        )

        sender_button_layout.addStretch(1)

        sender_layout.addWidget(
            self.sender_table
        )

        sender_layout.addLayout(
            sender_button_layout
        )

        recipient_group = QGroupBox(
            "Receiver / CC"
        )
        recipient_group.setMaximumHeight(
            260
        )

        recipient_layout = QVBoxLayout(
            recipient_group
        )

        self.recipient_table = QTableWidget(
            0,
            4,
        )

        self.recipient_table.setHorizontalHeaderLabels(
            [
                "ID",
                "User ID",
                "Name",
                "Recipient Type",
            ]
        )

        self._configure_table(
            self.recipient_table
        )
        self.recipient_table.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.recipient_table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.recipient_table.setColumnWidth(
            0,
            55,
        )

        self.recipient_table.setColumnWidth(
            1,
            105,
        )

        self.recipient_table.horizontalHeader(
        ).setSectionResizeMode(
            2,
            QHeaderView.Stretch,
        )

        self.recipient_table.setColumnWidth(
            3,
            130,
        )

        recipient_button_layout = QHBoxLayout()

        self.add_recipient_button = QPushButton(
            "Add"
        )

        self.delete_recipient_button = QPushButton(
            "Delete"
        )

        self.delete_recipient_button.setObjectName(
            "deleteButton"
        )

        self.add_recipient_button.clicked.connect(
            self._add_recipient
        )

        self.delete_recipient_button.clicked.connect(
            self._delete_recipient
        )

        recipient_button_layout.addWidget(
            self.add_recipient_button
        )

        recipient_button_layout.addWidget(
            self.delete_recipient_button
        )

        recipient_button_layout.addStretch(1)

        recipient_layout.addWidget(
            self.recipient_table
        )

        recipient_layout.addLayout(
            recipient_button_layout
        )

        tables_layout.addWidget(
            sender_group,
            2,
        )

        tables_layout.addWidget(
            recipient_group,
            2,
        )

        self.auto_send_mail_panel = (
            AutoSendMailSchedulerPanel(
                database_path=self.database_path,
                parent=self,
            )
        )

        tables_layout.addWidget(
            self.auto_send_mail_panel,
            2,
        )

        root_layout.addLayout(
            tables_layout
        )

        mail_action_layout = QHBoxLayout()
        mail_action_layout.setSpacing(8)

        self.test_login_button = QPushButton(
            "Test Login"
        )

        self.test_login_button.setFixedWidth(
            110
        )

        self.test_login_button.clicked.connect(
            self._start_test_login
        )

        mail_action_layout.addWidget(
            self.test_login_button
        )

        self.customize_email_button = QPushButton(
            "Customize Email"
        )

        self.customize_email_button.setFixedWidth(
            145
        )

        self.customize_email_button.clicked.connect(self._customize_email)

        mail_action_layout.addWidget(
            self.customize_email_button
        )
        mail_action_layout.addStretch(1)

        root_layout.addLayout(
            mail_action_layout
        )
        history_group = QGroupBox(
            "MAIL HISTORY"
        )

        history_layout = QVBoxLayout(
            history_group
        )

        self.mail_history_table = QTableWidget(
            0,
            8,
        )

        self.mail_history_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Alarm Date",
                "Send Time",
                "Sender",
                "Receiver",
                "CC",
                "Result",
                "Detail",
            ]
        )

        self._configure_table(
            self.mail_history_table
        )

        self.mail_history_table.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.mail_history_table.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.mail_history_table.setColumnWidth(
            0,
            55,
        )

        self.mail_history_table.setColumnWidth(
            1,
            95,
        )

        self.mail_history_table.setColumnWidth(
            2,
            145,
        )

        self.mail_history_table.setColumnWidth(
            3,
            160,
        )

        self.mail_history_table.setColumnWidth(
            4,
            180,
        )

        self.mail_history_table.setColumnWidth(
            5,
            180,
        )

        self.mail_history_table.setColumnWidth(
            6,
            80,
        )

        self.mail_history_table.horizontalHeader(
        ).setSectionResizeMode(
            7,
            QHeaderView.Stretch,
        )

        self.mail_history_table.cellClicked.connect(
            self._open_mail_history_detail
        )

        history_layout.addWidget(
            self.mail_history_table
        )

        root_layout.addWidget(
            history_group,
            1,
        )

    def _customize_email(self):
        """Mở preview mới mỗi lần để đọc alarm và target đã lưu mới nhất."""
        if self._closing or self.template_dialog is not None:
            return
        from ui.mail_template_dialog import MailTemplateDialog
        dialog = MailTemplateDialog(self.database_path, self)
        self.template_dialog = dialog
        try:
            dialog.exec_()
        finally:
            self.template_dialog = None
            dialog.deleteLater()

    @staticmethod
    def _configure_table(
        table: QTableWidget,
    ) -> None:
        """Định dạng bảng chọn một dòng, không sửa trực tiếp, nền xen kẽ."""
        table.setAlternatingRowColors(True)

        table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        table.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        table.verticalHeader().setVisible(
            False
        )

        table.verticalHeader(
        ).setDefaultSectionSize(
            30
        )

    def load_if_needed(self) -> None:
        """Đọc lại cấu hình và lịch sử khi quay lại tab, độc lập bộ lọc."""
        if not self._closing:
            self.reload_data()
            self.auto_send_mail_panel._load_config()

    def reload_data(self) -> None:
        """Đọc và hiển thị lại Sender, người nhận và lịch sử mail."""
        try:
            self._senders = (
                self.repository.get_senders()
            )

            self._recipients = (
                self.repository.get_recipients()
            )
            self._mail_histories = (
                self.mail_send_repository
                .get_mail_history()
            )

            self._fill_sender_table()
            self._fill_recipient_table()
            self._fill_mail_history_table()

            self._loaded = True

        except Exception as error:
            QMessageBox.critical(
                self,
                "Không thể tải cấu hình mail",
                str(error),
            )

    def _fill_sender_table(self) -> None:
        """Hiển thị Sender với mật khẩu che và checkbox Enable."""
        self.sender_table.setRowCount(
            len(self._senders)
        )

        for row_index, sender in enumerate(
            self._senders
        ):
            self._set_item(
                self.sender_table,
                row_index,
                0,
                sender.id,
            )

            self._set_item(
                self.sender_table,
                row_index,
                1,
                sender.user_id,
            )

            self._set_item(
                self.sender_table,
                row_index,
                2,
                sender.display_name,
            )
            self._set_item(
                self.sender_table,
                row_index,
                3,
                (
                    "••••••••"
                    if sender.password
                    else "Chưa có"
                ),
            )

            checkbox = QCheckBox()
            checkbox.setChecked(
                sender.enabled
            )

            checkbox.stateChanged.connect(
                lambda state, sender_id=sender.id:
                self._sender_enabled_changed(
                    sender_id,
                    state,
                )
            )

            wrapper = QWidget()
            wrapper_layout = QHBoxLayout(
                wrapper
            )

            wrapper_layout.setContentsMargins(
                0,
                0,
                0,
                0,
            )

            wrapper_layout.setAlignment(
                Qt.AlignCenter
            )

            wrapper_layout.addWidget(
                checkbox
            )

            self.sender_table.setCellWidget(
                row_index,
                4,
                wrapper,
            )

    def _fill_recipient_table(self) -> None:
        """Hiển thị người nhận với combobox Receiver/CC/None."""
        self.recipient_table.setRowCount(
            len(self._recipients)
        )

        for row_index, recipient in enumerate(
            self._recipients
        ):
            self._set_item(
                self.recipient_table,
                row_index,
                0,
                recipient.id,
            )

            self._set_item(
                self.recipient_table,
                row_index,
                1,
                recipient.user_id,
            )

            self._set_item(
                self.recipient_table,
                row_index,
                2,
                recipient.display_name,
            )

            type_combo = QComboBox()

            type_combo.addItem(
                "Receiver",
                "RECEIVER",
            )

            type_combo.addItem(
                "CC",
                "CC",
            )

            type_combo.addItem(
                "None",
                "NONE",
            )

            selected_index = (
                type_combo.findData(
                    recipient.recipient_type
                )
            )

            if selected_index >= 0:
                type_combo.setCurrentIndex(
                    selected_index
                )

            type_combo.currentIndexChanged.connect(
                lambda _index,
                recipient_id=recipient.id,
                combo=type_combo:
                self._recipient_type_changed(
                    recipient_id,
                    combo.currentData(),
                )
            )

            self.recipient_table.setCellWidget(
                row_index,
                3,
                type_combo,
            )

    def _fill_mail_history_table(self) -> None:
        """Hiển thị các email gửi thành công mới nhất."""

        self.mail_history_table.setRowCount(
            len(self._mail_histories)
        )

        for row_index, history in enumerate(
                self._mail_histories
        ):
            values = [
                history.id,
                history.alarm_date,
                history.sent_at,
                history.sender,
                history.receivers,
                history.cc,
                history.result,
                "Click to view",
            ]

            for column_index, value in enumerate(
                    values
            ):
                item = QTableWidgetItem(
                    str(value or "")
                )

                item.setTextAlignment(
                    int(Qt.AlignCenter)
                )

                # Di chuột vào ô để xem toàn bộ
                # Receiver hoặc CC bị rút gọn.
                item.setToolTip(
                    str(value or "")
                )

                self.mail_history_table.setItem(
                    row_index,
                    column_index,
                    item,
                )

    def _open_mail_history_detail(
            self,
            row_index: int,
            _column_index: int,
    ) -> None:
        """Mở nội dung HTML đã gửi."""

        if not (
                0 <= row_index < len(
            self._mail_histories
        )
        ):
            return

        history_id = (
            self._mail_histories[
                row_index
            ].id
        )

        try:
            detail = (
                self.mail_send_repository
                .get_mail_history_detail(
                    history_id
                )
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Không thể mở Mail History",
                str(error),
            )
            return

        dialog = MailHistoryDialog(
            detail=detail,
            parent=self,
        )

        dialog.exec_()
        dialog.deleteLater()

    @staticmethod
    def _set_item(
        table,
        row: int,
        column: int,
        value,
    ) -> None:
        """Gán nội dung ô bảng và căn giữa."""
        item = QTableWidgetItem(
            str(value)
        )

        item.setTextAlignment(
            int(Qt.AlignCenter)
        )

        table.setItem(
            row,
            column,
            item,
        )

    def _selected_sender(self):
        """Lấy Sender tương ứng dòng đang chọn."""
        row_index = (
            self.sender_table.currentRow()
        )

        if not (
            0 <= row_index < len(
                self._senders
            )
        ):
            return None

        return self._senders[row_index]

    def _selected_recipient(self):
        """Lấy người nhận tương ứng dòng đang chọn."""
        row_index = (
            self.recipient_table.currentRow()
        )

        if not (
            0 <= row_index < len(
                self._recipients
            )
        ):
            return None

        return self._recipients[row_index]

    def _add_sender(self) -> None:
        """Kiểm tra và thêm Sender; tắt Sender cũ nếu bật tài khoản mới."""
        dialog = MailSenderDialog(
            parent=self
        )

        if dialog.exec_() != QDialog.Accepted:
            return

        try:
            self.repository.add_sender(
                *dialog.values()
            )

            self.reload_data()

        except Exception as error:
            self._show_save_error(error)

    def _delete_sender(self) -> None:
        """Xóa Sender theo ID."""
        sender = self._selected_sender()

        if sender is None:
            QMessageBox.warning(
                self,
                "Chưa chọn Sender",
                "Vui lòng chọn một Sender.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Xóa Sender",
            (
                "Bạn có chắc muốn xóa Sender:\n"
                f"{sender.display_name} "
                f"({sender.user_id})?"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        try:
            self.repository.delete_sender(
                sender.id
            )

            self.reload_data()

        except Exception as error:
            self._show_save_error(error)

    def _sender_enabled_changed(
            self,
            sender_id: int,
            state: int,
    ) -> None:
        """Lưu trạng thái Enable của Sender."""

        enabled = (
                state == Qt.Checked
        )

        try:
            self.repository.set_sender_enabled(
                sender_id=sender_id,
                enabled=enabled,
            )

            QTimer.singleShot(0, self.reload_data)

        except Exception as error:
            self._show_save_error(error)

            # Tải lại để checkbox trở về
            # đúng trạng thái trong database.
            QTimer.singleShot(0, self.reload_data)

    def _add_recipient(self) -> None:
        """Kiểm tra và thêm người nhận, từ chối User ID trùng."""
        dialog = MailRecipientDialog(
            parent=self
        )

        if dialog.exec_() != QDialog.Accepted:
            return

        try:
            self.repository.add_recipient(
                *dialog.values()
            )

            self.reload_data()

        except Exception as error:
            self._show_save_error(error)

    def _delete_recipient(self) -> None:
        """Xóa người nhận theo ID."""
        recipient = (
            self._selected_recipient()
        )

        if recipient is None:
            QMessageBox.warning(
                self,
                "Chưa chọn người nhận",
                "Vui lòng chọn một người nhận.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Xóa người nhận",
            (
                "Bạn có chắc muốn xóa:\n"
                f"{recipient.display_name} "
                f"({recipient.user_id})?"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        try:
            self.repository.delete_recipient(
                recipient.id
            )

            self.reload_data()

        except Exception as error:
            self._show_save_error(error)

    def _recipient_type_changed(
        self,
        recipient_id: int,
        recipient_type: str,
    ) -> None:
        """Lưu loại người nhận rồi đồng bộ lại thứ tự danh sách và bảng."""
        try:
            self.repository.update_recipient_type(
                recipient_id=recipient_id,
                recipient_type=recipient_type,
            )

            QTimer.singleShot(0, self.reload_data)

        except Exception as error:
            self._show_save_error(error)
            QTimer.singleShot(0, self.reload_data)


    def _start_test_login(self) -> None:
        """Bắt đầu kiểm tra Sender đang Enable."""

        if self._closing or self.is_busy():
            return

        # Chỉ tải worker khi người dùng bấm Test Login.
        from workers.mail_login_worker import (
            MailLoginWorker,
        )

        self.test_login_button.setEnabled(
            False
        )

        self.test_login_button.setText(
            "Đang đăng nhập..."
        )

        self.login_thread = QThread(self)

        self.login_worker = MailLoginWorker(
            database_path=self.database_path
        )

        self.login_worker.moveToThread(
            self.login_thread
        )

        self.login_thread.started.connect(
            self.login_worker.run
        )

        self.login_worker.succeeded.connect(
            self._on_test_login_succeeded
        )

        self.login_worker.failed.connect(
            self._on_test_login_failed
        )

        self.login_worker.finished.connect(self.login_worker.deleteLater)
        self.login_worker.finished.connect(self.login_thread.quit)

        self.login_thread.finished.connect(
            self._on_test_login_finished
        )

        self.login_thread.finished.connect(
            self.login_thread.deleteLater
        )

        self.login_thread.start()






    def _on_test_login_succeeded(
            self,
            result,
    ) -> None:
        """Thông báo Test Login thành công."""

        if self._closing:
            return

        login_info = result.login_info

        login_name = (
                login_info.name_vn
                or login_info.name_en
                or result.configured_name
        )

        organization = (
                login_info.organization_vn
                or login_info.organization_en
        )

        message_lines = [
            "Đăng nhập hệ thống mail thành công.",
            "",
            f"User ID: {login_info.user_id}",
            f"Employee No: {login_info.employee_no}",
            f"Name: {login_name}",
        ]

        if organization:
            message_lines.append(
                f"Organization: {organization}"
            )

        QMessageBox.information(
            self,
            "Test Login thành công",
            "\n".join(message_lines),
        )

    def _on_test_login_failed(
            self,
            error_message: str,
    ) -> None:
        """Thông báo Test Login thất bại."""

        if self._closing:
            return

        QMessageBox.warning(
            self,
            "Test Login thất bại",
            error_message,
        )

    def _on_test_login_finished(
            self,
    ) -> None:
        """Dọn QThread sau khi Test Login kết thúc."""

        self.login_worker = None
        self.login_thread = None

        self.test_login_button.setEnabled(
            True
        )

        self.test_login_button.setText(
            "Test Login"
        )

    def prepare_close(self) -> None:
        """Ngăn thao tác mới; controller đợi Test Login kết thúc trước khi đóng."""
        self._closing = True
        if self.template_dialog is not None:
            self.template_dialog.reject()
        self.setEnabled(False)

    def is_busy(self) -> bool:
        """Giữ tham chiếu thread tới khi callback dọn dẹp đã chạy."""
        return (self.login_thread is not None or
                (self.template_dialog is not None and self.template_dialog.is_busy()))

    def _show_save_error(
        self,
        error: Exception,
    ) -> None:
        """Thông báo lỗi lưu cấu hình mail."""
        QMessageBox.critical(
            self,
            "Không thể lưu cấu hình mail",
            str(error),
        )
