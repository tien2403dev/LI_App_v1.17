from __future__ import annotations

from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)


class MailSenderDialog(QDialog):
    """Dialog thêm mới tài khoản gửi mail."""

    def __init__(
        self,
        parent=None,
    ):
        """Khởi tạo đối tượng và các thành phần liên quan."""
        super().__init__(parent)

        self.setWindowTitle(
            "Add Sender"
        )

        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.user_id_edit = QLineEdit()
        self.name_edit = QLineEdit()
        self.password_edit = QLineEdit()

        # Che mật khẩu khi nhập.
        self.password_edit.setEchoMode(
            QLineEdit.Password
        )

        self.enabled_checkbox = QCheckBox(
            "Use this account as sender"
        )

        form_layout.addRow(
            "User ID:",
            self.user_id_edit,
        )

        form_layout.addRow(
            "Name:",
            self.name_edit,
        )

        form_layout.addRow(
            "Password:",
            self.password_edit,
        )

        form_layout.addRow(
            "Enable:",
            self.enabled_checkbox,
        )

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save
            | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(
            self._validate_and_accept
        )

        buttons.rejected.connect(
            self.reject
        )

        layout.addWidget(buttons)

    def values(
        self,
    ) -> tuple[str, str, str, bool]:
        """Trả về các giá trị người dùng nhập."""
        return (
            self.user_id_edit.text().strip(),
            self.name_edit.text().strip(),
            self.password_edit.text(),
            self.enabled_checkbox.isChecked(),
        )

    def _validate_and_accept(self) -> None:
        """Kiểm tra thông tin trước khi chấp nhận."""
        (
            user_id,
            name,
            password,
            _,
        ) = self.values()

        if not user_id:
            QMessageBox.warning(
                self,
                "Thiếu User ID",
                "Vui lòng nhập User ID.",
            )
            return

        if not name:
            QMessageBox.warning(
                self,
                "Thiếu Name",
                "Vui lòng nhập tên người gửi.",
            )
            return

        if not password:
            QMessageBox.warning(
                self,
                "Thiếu Password",
                "Vui lòng nhập mật khẩu.",
            )
            return

        self.accept()


class MailRecipientDialog(QDialog):
    """Dialog thêm mới Receiver hoặc CC."""

    TYPE_OPTIONS = (
        ("Receiver", "RECEIVER"),
        ("CC", "CC"),
        ("None", "NONE"),
    )

    def __init__(
        self,
        parent=None,
    ):
        """Khởi tạo đối tượng và các thành phần liên quan."""
        super().__init__(parent)

        self.setWindowTitle(
            "Add Receiver"
        )

        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.user_id_edit = QLineEdit()
        self.name_edit = QLineEdit()
        self.type_combo = QComboBox()

        for label, value in self.TYPE_OPTIONS:
            self.type_combo.addItem(
                label,
                value,
            )

        form_layout.addRow(
            "User ID:",
            self.user_id_edit,
        )

        form_layout.addRow(
            "Name:",
            self.name_edit,
        )

        form_layout.addRow(
            "Recipient Type:",
            self.type_combo,
        )

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save
            | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(
            self._validate_and_accept
        )

        buttons.rejected.connect(
            self.reject
        )

        layout.addWidget(buttons)

    def values(
        self,
    ) -> tuple[str, str, str]:
        """Trả về các giá trị người dùng nhập."""
        return (
            self.user_id_edit.text().strip(),
            self.name_edit.text().strip(),
            str(self.type_combo.currentData()),
        )

    def _validate_and_accept(self) -> None:
        """Kiểm tra thông tin trước khi chấp nhận."""
        user_id, name, _ = self.values()

        if not user_id:
            QMessageBox.warning(
                self,
                "Thiếu User ID",
                "Vui lòng nhập User ID.",
            )
            return

        if not name:
            QMessageBox.warning(
                self,
                "Thiếu Name",
                "Vui lòng nhập tên người nhận.",
            )
            return

        self.accept()