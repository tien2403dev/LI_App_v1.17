from datetime import timedelta
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QDateEdit, QDialog, QDialogButtonBox, QFormLayout, QLabel, QVBoxLayout


class DateRangeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chọn khoảng ngày import")
        self.setMinimumWidth(370)
        yesterday = QDate.currentDate().addDays(-1)
        self.date_from = QDateEdit(yesterday)
        self.date_to = QDateEdit(yesterday)
        for field in (self.date_from, self.date_to):
            field.setCalendarPopup(True)
            field.setDisplayFormat("dd/MM/yyyy")
            field.setDateRange(QDate(2000, 1, 1), QDate(2099, 12, 31))
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.addRow("Từ ngày:", self.date_from)
        form.addRow("Đến ngày:", self.date_to)
        layout.addLayout(form)
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color:#b42318")
        layout.addWidget(self.error_label)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Tiếp tục")
        buttons.button(QDialogButtonBox.Cancel).setText("Hủy")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        if self.date_to.date() < self.date_from.date():
            self.error_label.setText("Đến ngày phải bằng hoặc sau Từ ngày.")
            return
        super().accept()

    def business_dates(self):
        start = self.date_from.date().toPyDate()
        end = self.date_to.date().toPyDate()
        return tuple((start + timedelta(days=i)).strftime("%Y%m%d")
                     for i in range((end - start).days + 1))
