from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QDialog, QFileDialog, QMessageBox
from ui.dialogs.date_range_dialog import DateRangeDialog
from ui.widgets.loading_dialog import LoadingDialog


class ImportDialogs:
    """Hộp thoại tác vụ; không thêm nội dung vào trang chính."""
    def __init__(self, parent):
        """Khởi tạo trạng thái và các thành phần cần cho đối tượng."""
        self.parent = parent
        self.preferences = QSettings("LI_App", "PrimeImport")
        self.progress = None

    def choose_source(self):
        """Chọn khoảng ngày rồi chọn thư mục log PRIME."""
        dialog = DateRangeDialog(self.parent)
        if dialog.exec_() != QDialog.Accepted:
            return None
        folder = QFileDialog.getExistingDirectory(
            self.parent, "Chọn folder log chứa tất cả máy",
            str(self.preferences.value("last_log_root", "")))
        if not folder:
            return None
        self.preferences.setValue("last_log_root", folder)
        return folder, dialog.business_dates()

    def begin_progress(self, on_cancel, import_type="PRIME"):
        """Mở hộp thoại loading giống Aging cho PRIME/CUM."""
        self.begin_loading("Loading ...")

    def begin_loading(self, text="Loading ..."):
        """Mở hộp thoại loading dùng chung cho SEARCH và IMPORT."""
        if self.progress is not None:
            return
        self.progress = LoadingDialog(self.parent, text=text, title="Please Wait")
        self.progress.show()

    def update_progress(self, message):
        """Hiển thị thông báo tiến độ nếu người dùng chưa hủy."""
        if self.progress is not None:
            self.progress.set_text(message)

    def end_progress(self):
        """Đóng và giải phóng hộp thoại tiến độ."""
        if self.progress is not None:
            self.progress.close()
            self.progress.deleteLater()
            self.progress = None

    def show_error(self, message):
        """Hiển thị lỗi tác vụ cho người dùng."""
        QMessageBox.warning(self.parent, "Không hoàn tất tác vụ", message)

    def show_result(self, result):
        """Hiển thị số dòng, PASS/FAIL và ngày đã nhập của PRIME."""
        QMessageBox.information(
            self.parent, "Import thành công",
            f"File đã đọc: {result.file_count}\nDòng mới: {result.inserted:,}\n"
            f"Dòng cũ đã thay: {result.deleted:,}\n"
            f"PASS: {result.passed:,} | FAIL: {result.failed:,}\n"
            f"Ngày đã thay: {', '.join(result.dates)}")

    def choose_cum_source(self):
        """Chọn file Excel CUM giống Aging và nhớ đường dẫn lần trước."""
        path, _ = QFileDialog.getOpenFileName(
            self.parent, "Chọn file CUM", str(self.preferences.value("last_cum_file", "")),
            "Excel Files (*.xlsx)")
        if path:
            self.preferences.setValue("last_cum_file", path)
        return path or None

    def show_cum_result(self, result):
        """Hiển thị số dòng CUM, scrap detail và các ngày đã thay thế."""
        QMessageBox.information(self.parent, "Import CUM thành công",
            f"File: {result.file_name}\nDòng mới: {result.inserted:,}\n"
            f"Dòng cũ đã thay: {result.deleted:,}\nChi tiết scrap: {result.scrap_details:,}\n"
            f"Ngày đã thay: {', '.join(result.dates)}\nĐã đồng bộ TIER cho PRIME.")
