from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QLabel,
    QScrollArea,
    QTabBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from ui.widgets.filter_panel import FilterPanel
from ui.pages.summary_page import SummaryPage
from ui.pages.yield_slot_page import YieldSlotPage


class EqualWidthTabBar(QTabBar):
    """Giữ tất cả tab cùng chiều rộng cố định 180 px."""

    def tabSizeHint(self, index: int) -> QSize:
        size = super().tabSizeHint(index)
        size.setWidth(170)
        return size


class PrimePage(QWidget):
    import_requested = pyqtSignal()
    cum_import_requested = pyqtSignal()
    filter_applied = pyqtSignal(object)
    filter_activated = pyqtSignal(object)
    file_management_requested = pyqtSignal()
    send_mail_requested = pyqtSignal()
    report_requested = pyqtSignal()
    machine_slot_yield_requested = pyqtSignal()
    alarm_history_requested = pyqtSignal(object)
    alarm_edit_requested = pyqtSignal(object, str, str)

    def __init__(self):
        """Khởi tạo đối tượng và các thành phần liên quan."""
        super().__init__()
        self.current_criteria = None
        self.filter_panel = FilterPanel()
        self.import_button = self.filter_panel.import_prime_button
        self.cum_import_button = self.filter_panel.import_cum_button
        self.filter_panel.import_prime_clicked.connect(self.import_requested)
        self.filter_panel.import_cum_clicked.connect(self.cum_import_requested)
        self.filter_panel.filter_applied.connect(self._apply_filter)
        self.filter_status = QLabel()
        self.filter_status.setWordWrap(True)
        self.filter_status.setStyleSheet("color:#475569; font-size:12px;")
        content = QWidget()
        content.setObjectName("liAppBackground")
        content.setAttribute(Qt.WA_StyledBackground, True)

        # Chỉ đổi nền ngoài, không áp dụng cho bảng hoặc biểu đồ.
        # content.setStyleSheet("""
        #     QWidget#liAppBackground {
        #         background-color: #D8E3F0;
        #     }
        # """)
        content.setStyleSheet("""
            QWidget#liAppBackground {
                background-color: #E3EFFF;
            }
        """)

        body = QVBoxLayout(content)
        self.body_layout = body
        # body.setContentsMargins(24, 24, 24, 24)
        body.addWidget(self.filter_panel)
        body.addWidget(self.filter_status)
        self.tabs = QTabWidget()
        self.tabs.setTabBar(EqualWidthTabBar(self.tabs))
        self.summary_page = SummaryPage()
        self.tabs.addTab(self.summary_page, "📊 Summary")
        self.yield_slot_page = YieldSlotPage()
        self.tabs.addTab(self.yield_slot_page, "📈 Yield Slot")
        self.machine_slot_yield_page = None
        self.machine_slot_yield_host = QWidget()
        self.machine_slot_yield_layout = QVBoxLayout(
            self.machine_slot_yield_host
        )
        self.machine_slot_yield_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs.addTab(
            self.machine_slot_yield_host,
            "🧪 Machine Slot Yield",
        )
        self.alarm_page = None
        self.alarm_host = QWidget()
        self.alarm_layout = QVBoxLayout(self.alarm_host)
        self.alarm_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs.addTab(self.alarm_host, "🚨 Alarm")
        self.dashboard_page = None
        self.dashboard_host = QWidget()
        self.dashboard_layout = QVBoxLayout(self.dashboard_host)
        self.dashboard_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs.addTab(self.dashboard_host, "🧭 Dashboard")
        self.file_management_page = None
        self.file_management_host = QWidget()
        self.file_management_layout = QVBoxLayout(self.file_management_host)
        self.file_management_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs.addTab(self.file_management_host, "🗃 File Management")
        self.send_mail_page = None
        self.send_mail_host = QWidget()
        self.send_mail_layout = QVBoxLayout(self.send_mail_host)
        self.send_mail_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs.addTab(self.send_mail_host, "📤 Send Mail")
        self.report_page = None
        self.report_host = QWidget()
        self.report_layout = QVBoxLayout(self.report_host)
        self.report_layout.setContentsMargins(0, 0, 0, 0)
        self.tabs.addTab(self.report_host, "📋 Report")
        self.tabs.tabBar().setExpanding(False)
        self.tabs.tabBar().setUsesScrollButtons(True)
        self.tabs.tabBar().setDrawBase(False)
        self.tabs.setStyleSheet("""
            QTabBar { border:none; }
            QTabBar::tab { background:#E8EEF5; color:#1E4F7A; padding:9px 10px;
                border-left:1px solid #D4DFEB;
                border-right:1px solid #D4DFEB;
                border-bottom:1px solid #D4DFEB;
                border-top:none; border-top-left-radius:5px;
                border-top-right-radius:5px; margin-right:2px;
                font-size:14px; font-weight:700; }
            QTabBar::tab:selected { background:white; color:#0078D7;
                border-bottom:2px solid #1684E8; }
            QTabWidget::pane { border:none; background:white; }
        """)
        body.addWidget(self.tabs, 1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setWidget(content)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        self.set_import_enabled(False)
        self.set_filters_ready(False)
        self.tabs.currentChanged.connect(self._on_tab_changed)

    def set_import_enabled(self, enabled):
        """Thực hiện set import enabled cho chức năng tương ứng."""
        self.filter_panel.set_import_buttons_enabled(enabled)
        if not enabled:
            self.filter_panel.apply_filter_button.setEnabled(False)

    def set_filters_ready(self, ready):
        """Thực hiện set filters ready cho chức năng tương ứng."""
        self.filter_panel.apply_filter_button.setEnabled(ready)

    def load_filter_options(self, result):
        """Thực hiện load filter options cho chức năng tương ứng."""
        self.filter_panel.load_options(result)
        self.current_criteria = None
        self.filter_status.clear()
        self.set_filters_ready(True)

    def _apply_filter(self, criteria, manual=True):
        """Thực hiện apply filter cho chức năng tương ứng."""
        self.current_criteria = criteria
        self.filter_status.setText(
            f"Đã chọn điều kiện: {criteria.date_from} → {criteria.date_to} | "
            f"EQP: {criteria.eqp if criteria.eqp is not None else 'NULL'} | "
            f"SLOT: {criteria.slot if criteria.slot is not None else 'NULL'} | "
            f"Tier: {len(criteria.tiers)} | Model: {len(criteria.models)} | "
            f"Scrap Code: {len(criteria.scrap_codes)}")
        (self.filter_applied if manual else self.filter_activated).emit(criteria)

    def _on_tab_changed(self, index):
        """Apply current controls only to the newly visible tab, after initialization."""
        if self.tabs.currentWidget() is self.report_host:
            self.report_requested.emit()
            return
        if self.tabs.currentWidget() is self.send_mail_host:
            self.send_mail_requested.emit()
            return
        if self.tabs.currentWidget() is self.machine_slot_yield_host:
            self.machine_slot_yield_requested.emit()
            return
        is_files = self.tabs.currentWidget() is self.file_management_host
        # Giữ bộ lọc và lề chung cho mọi tab, kể cả File Management.
        if is_files:
            self.file_management_requested.emit()
            return
        if index < 0 or not self.filter_panel.apply_filter_button.isEnabled():
            return
        self._apply_filter(self.filter_panel.get_filter_criteria(), manual=False)


    def open_report(self, database_path):
        if self.report_page is None:
            from ui.pages.report_page import ReportPage
            self.report_page = ReportPage(database_path, self)
            self.report_layout.addWidget(self.report_page)
        self.report_page.load_if_needed()

    def open_file_management(self, database_path):
        """Tạo tab sau khi database sẵn sàng; chỉ đọc danh sách khi có thay đổi."""
        if self.file_management_page is None:
            from ui.pages.file_management_page import FileManagementPage
            self.file_management_page = FileManagementPage(database_path, self)
            self.file_management_layout.addWidget(self.file_management_page)
        self.file_management_page.load_if_needed()

    def open_send_mail(self, database_path):
        """Chỉ tạo giao diện Send Mail sau khi database sẵn sàng."""
        if self.send_mail_page is None:
            from ui.pages.send_mail_page import SendMailTab
            self.send_mail_page = SendMailTab(database_path, self)
            self.send_mail_layout.addWidget(self.send_mail_page)
        self.send_mail_page.load_if_needed()

    def open_machine_slot_yield(self, database_path):
        """Tạo và tải tab cấu hình sau khi database đã sẵn sàng."""
        if self.machine_slot_yield_page is None:
            from ui.pages.machine_slot_yield_page import MachineSlotYieldPage
            self.machine_slot_yield_page = MachineSlotYieldPage(
                database_path,
                self,
            )
            self.machine_slot_yield_layout.addWidget(
                self.machine_slot_yield_page
            )
        self.machine_slot_yield_page.load_if_needed()

    def ensure_alarm_page(self):
        """Chỉ dựng tab Alarm khi người dùng mở; chưa thực hiện truy vấn."""
        if self.alarm_page is None:
            from ui.pages.alarm_page import AlarmPage
            self.alarm_page = AlarmPage(self)
            self.alarm_layout.addWidget(self.alarm_page)
            self.alarm_page.edit_requested.connect(self.alarm_edit_requested)
            self.alarm_page.history_requested.connect(self.alarm_history_requested)
        return self.alarm_page

    def ensure_dashboard_page(self):
        """Dựng Dashboard khi cần; dữ liệu luôn do controller chuyển từ Alarm sang."""
        if self.dashboard_page is None:
            from ui.pages.dashboard_page import DashboardPage
            self.dashboard_page = DashboardPage(self)
            self.dashboard_layout.addWidget(self.dashboard_page)
            if self.alarm_page is not None:
                self.alarm_page.dashboard_rows_changed.connect(
                    self.dashboard_page.load_rows
                )
        return self.dashboard_page
