from __future__ import annotations
from dataclasses import dataclass
from PyQt5.QtCore import QDate, QSize, Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QComboBox, QDateEdit, QFrame, QGridLayout, QHBoxLayout, QLabel, QListView, QListWidget, QListWidgetItem, QPushButton, QStyledItemDelegate, QVBoxLayout, QWidget
from services.scrap_code_config import PRIORITY_SCRAP_CODES as SHARED_PRIORITY_SCRAP_CODES

class ComboBoxItemDelegate(QStyledItemDelegate):
    """Tăng chiều cao mỗi dòng trong dropdown thêm 16px."""

    def sizeHint(self, option, index) -> QSize:
        size = super().sizeHint(option, index)
        size.setHeight(size.height() + 16)
        return size

@dataclass
class FilterCriteria:
    """
    Lưu điều kiện filter chung để các tab sử dụng.
    """
    date_from: str
    date_to: str
    selected_date: str | None
    eqp: str | None
    slot: int | None
    scrap_codes: list[str]
    tiers: list[str | None]
    models: list[str]

class FilterPanel(QWidget):
    """
    Hiển thị và xử lý toàn bộ bộ lọc chung của ứng dụng.
    """
    import_prime_clicked = pyqtSignal()
    import_cum_clicked = pyqtSignal()
    filter_applied = pyqtSignal(object)
    PRIORITY_SCRAP_CODES = SHARED_PRIORITY_SCRAP_CODES

    def __init__(self, parent=None):
        """Khởi tạo bộ lọc với To là hôm nay và From lùi 14 ngày."""
        super().__init__(parent)
        self._updating_scrap_selection = False
        self._updating_tier_selection = False
        self._updating_model_selection = False
        self._build_ui()

    def _build_ui(self) -> None:
        """Tạo khu vực bộ lọc nằm trong QFrame."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        filter_frame = QFrame(self)
        filter_frame.setObjectName('filterFrame')
        filter_frame.setFixedWidth(1116 + 16 + 16)
        frame_layout = QVBoxLayout(filter_frame)
        frame_layout.setContentsMargins(16, 2, 16, 8)
        frame_layout.setSpacing(16)
        today = QDate.currentDate()
        self.from_date_edit = QDateEdit()
        self.from_date_edit.setCalendarPopup(True)
        self.from_date_edit.setDisplayFormat('yyyy-MM-dd')
        self.from_date_edit.setDate(today.addDays(-14))
        self.to_date_edit = QDateEdit()
        self.to_date_edit.setCalendarPopup(True)
        self.to_date_edit.setDisplayFormat('yyyy-MM-dd')
        self.to_date_edit.setDate(today)
        self.eqp_combo = QComboBox()
        self.slot_combo = QComboBox()
        self.scrap_code_list = QListWidget()
        self.model_list = QListWidget()
        self.model_list.setFixedSize(180, 102)
        self.tier_list = QListWidget()
        for widget in (self.from_date_edit, self.to_date_edit, self.eqp_combo, self.slot_combo):
            widget.setFixedSize(180, 32)
        for combo_box in (self.eqp_combo, self.slot_combo):
            dropdown_view = QListView(combo_box)
            dropdown_view.setItemDelegate(ComboBoxItemDelegate(dropdown_view))
            combo_box.setView(dropdown_view)
        self.scrap_code_list.setFixedSize(180, 102)
        self.tier_list.setFixedSize(180, 102)

        def create_vertical_filter(label_text: str, widget: QWidget) -> QVBoxLayout:
            """Tạo filter có label nằm phía trên ô chọn."""
            group_layout = QVBoxLayout()
            group_layout.setContentsMargins(0, 0, 0, 0)
            group_layout.setSpacing(0)
            label = QLabel(label_text)
            group_layout.addWidget(label)
            group_layout.addWidget(widget)
            return group_layout
        compact_filter_widget = QWidget(filter_frame)
        compact_filter_widget.setFixedWidth(1116)
        compact_filter_layout = QVBoxLayout(compact_filter_widget)
        compact_filter_layout.setContentsMargins(0, 0, 0, 0)
        compact_filter_layout.setSpacing(8)
        filters_row_layout = QHBoxLayout()
        filters_row_layout.setContentsMargins(0, 0, 0, 0)
        filters_row_layout.setSpacing(0)
        left_filter_layout = QGridLayout()
        left_filter_layout.setContentsMargins(0, 14, 0, 0)
        left_filter_layout.setHorizontalSpacing(48)
        left_filter_layout.setVerticalSpacing(16)
        left_filter_layout.addLayout(create_vertical_filter('From', self.from_date_edit), 0, 0)
        left_filter_layout.addLayout(create_vertical_filter('To', self.to_date_edit), 0, 1)
        left_filter_layout.addLayout(create_vertical_filter('EQP', self.eqp_combo), 1, 0)
        left_filter_layout.addLayout(create_vertical_filter('SLOT', self.slot_combo), 1, 1)
        tier_filter_layout = QVBoxLayout()
        tier_filter_layout.setContentsMargins(0, 14, 0, 0)
        tier_filter_layout.setSpacing(2)
        tier_filter_layout.setAlignment(Qt.AlignTop)
        tier_filter_layout.addWidget(QLabel('Tier'))
        tier_filter_layout.addWidget(self.tier_list)
        model_filter_layout = QVBoxLayout()
        model_filter_layout.setContentsMargins(0, 14, 0, 0)
        model_filter_layout.setSpacing(0)
        model_filter_layout.setAlignment(Qt.AlignTop)
        model_filter_layout.addWidget(QLabel('Model'))
        model_filter_layout.addWidget(self.model_list)
        scrap_filter_layout = QVBoxLayout()
        scrap_filter_layout.setContentsMargins(0, 0, 0, 0)
        scrap_filter_layout.setSpacing(0)
        scrap_filter_layout.setAlignment(Qt.AlignTop)
        scrap_filter_layout.addWidget(QLabel('Scrap Code'))
        scrap_filter_layout.addWidget(self.scrap_code_list)
        chart_filter_frame = QFrame()
        chart_filter_frame.setObjectName('chartFilterFrame')
        chart_filter_frame.setFixedSize(196, 140)
        chart_filter_layout = QHBoxLayout(chart_filter_frame)
        chart_filter_layout.setContentsMargins(8, 14, 8, 2)
        chart_filter_layout.setSpacing(0)
        chart_filter_layout.addLayout(scrap_filter_layout)
        chart_filter_hint = QLabel('Chọn để vẽ biểu đồ', chart_filter_frame)
        chart_filter_hint.setObjectName('chartFilterHint')
        chart_filter_hint.setAlignment(Qt.AlignCenter)
        chart_filter_hint.setGeometry(8, 0, 180, 14)
        chart_filter_hint.raise_()
        filters_row_layout.addLayout(left_filter_layout, 0)
        filters_row_layout.addSpacing(48)
        filters_row_layout.addLayout(tier_filter_layout, 0)
        filters_row_layout.addSpacing(48)
        filters_row_layout.addLayout(model_filter_layout, 0)
        filters_row_layout.addSpacing(44)
        filters_row_layout.addWidget(chart_filter_frame, 0, Qt.AlignTop)
        compact_filter_layout.addLayout(filters_row_layout)
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(2, 6, 0, 6)
        button_layout.setSpacing(0)
        self.import_prime_button = QPushButton('IMPORT PRIME')
        self.import_cum_button = QPushButton('IMPORT CUM')
        self.apply_filter_button = QPushButton('SEARCH')
        self.import_prime_button.setFixedSize(120, 30)
        self.import_cum_button.setFixedSize(120, 30)
        self.apply_filter_button.setFixedSize(120, 30)
        button_layout.addWidget(self.import_prime_button, 0, Qt.AlignLeft)
        button_layout.addSpacing(12)
        button_layout.addWidget(self.import_cum_button, 0, Qt.AlignLeft)
        button_layout.addStretch()
        button_layout.addWidget(self.apply_filter_button)
        compact_filter_layout.addLayout(button_layout)
        frame_layout.addWidget(compact_filter_widget, alignment=Qt.AlignLeft)
        main_layout.addWidget(filter_frame, alignment=Qt.AlignLeft | Qt.AlignTop)
        main_layout.addStretch()
        self.setStyleSheet("""
            QFrame#filterFrame {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
            }

            QFrame#filterFrame QLabel {
                color: #1E293B;
                background-color: transparent;
                border: none;
                font-size: 13px;
                font-weight: 700;
            }

            QFrame#filterFrame QDateEdit,
            QFrame#filterFrame QComboBox {
                color: #0F172A;
                background-color: white;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding-left: 8px;
                font-size: 13px;
            }

            QFrame#filterFrame QDateEdit:hover,
            QFrame#filterFrame QComboBox:hover {
                border-color: #94A3B8;
            }

            QFrame#filterFrame QDateEdit:focus,
            QFrame#filterFrame QComboBox:focus {
                border-color: #1976D2;
            }

            QFrame#filterFrame QComboBox QAbstractItemView {
                min-width: 176px;
                max-width: 176px;
                color: #0F172A;
                background-color: white;
                border: 1px solid #CBD5E1;
                font-size: 13px;
                outline: none;
                selection-color: white;
                selection-background-color: #1976D2;
            }

            QFrame#filterFrame QListWidget {
                color: #0F172A;
                background-color: white;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                font-size: 13px;
            }

            QFrame#chartFilterFrame {
                background-color: #EEF4FF;
                border: 1px solid #94A3B8;
                border-radius: 4px;
            }

            QFrame#chartFilterFrame QLabel {
                background-color: transparent;
                border: none;
            }

            QFrame#chartFilterFrame QLabel#chartFilterHint {
                color: #475569;
                border: none;
                font-size: 11px;
                font-weight: 500;
                padding: 0 0px;
            }
            QFrame#filterFrame QPushButton {
                color: white;
                background-color: #1976D2;
                border: 1px solid #1565C0;
                border-radius: 4px;
                font-size: 13px;
                font-weight: 500;
            }

            QFrame#filterFrame QPushButton:hover { 
                background-color: #42A5F5; 
                border-color: #1976D2; 
            }

            QFrame#filterFrame QPushButton:pressed {
                background-color: #0D47A1;
            }

            QFrame#filterFrame QPushButton:disabled {
                color: #E2E8F0;
                background-color: #90CAF9;
                border-color: #90CAF9;
            }
            """)
        self.from_date_edit.dateChanged.connect(self._on_date_range_changed)
        self.to_date_edit.dateChanged.connect(self._on_date_range_changed)
        self.scrap_code_list.itemChanged.connect(self._on_scrap_code_item_changed)
        self.tier_list.itemChanged.connect(self._on_tier_item_changed)
        self.model_list.itemChanged.connect(self._on_model_item_changed)
        self.import_prime_button.clicked.connect(self.import_prime_clicked)
        self.import_cum_button.clicked.connect(self.import_cum_clicked)
        self.apply_filter_button.clicked.connect(self._emit_filter_criteria)

    def _on_date_range_changed(self) -> None:
        """Đảm bảo ngày From không lớn hơn ngày To."""
        from_date = self.from_date_edit.date()
        to_date = self.to_date_edit.date()
        if from_date > to_date:
            if self.sender() is self.from_date_edit:
                self.to_date_edit.setDate(from_date)
            else:
                self.from_date_edit.setDate(to_date)

    def load_options(self, result) -> None:
        """Nạp EQP, SLOT, Scrap code và Tier từ worker."""
        self._load_eqp_options(result.eqps)
        self._load_slot_options(result.slots)
        self._load_scrap_code_options(result.scrap_codes)
        self._load_tier_options(result.tiers)
        self._load_model_options(result.models)

    def _load_eqp_options(self, eqps: list[str]) -> None:
        """Nạp danh sách EQP và đặt mặc định ở trạng thái chưa chọn."""
        self.eqp_combo.blockSignals(True)
        try:
            self.eqp_combo.clear()
            self.eqp_combo.addItem('Chọn EQP', None)
            for eqp in eqps:
                self.eqp_combo.addItem(eqp, eqp)
        finally:
            self.eqp_combo.blockSignals(False)

    def _load_slot_options(self, slots: list[int]) -> None:
        """Nạp danh sách SLOT và đặt mặc định ở trạng thái chưa chọn."""
        self.slot_combo.blockSignals(True)
        try:
            self.slot_combo.clear()
            self.slot_combo.addItem('Chọn SLOT', None)
            for slot in slots:
                self.slot_combo.addItem(f'SLOT {slot}', slot)
        finally:
            self.slot_combo.blockSignals(False)

    def _load_scrap_code_options(self, scrap_codes: list[str]) -> None:
        """
        Nạp Scrap Code dạng checkbox.

        Các mã thường gặp được đưa lên đầu và tô đỏ.
        Những mã còn lại giữ nguyên thứ tự tăng dần
        được trả về từ repository.
        """
        self._updating_scrap_selection = True
        try:
            self.scrap_code_list.clear()
            select_all_item = QListWidgetItem('Select All')
            select_all_item.setFlags(select_all_item.flags() | Qt.ItemIsUserCheckable)
            select_all_item.setCheckState(Qt.Unchecked)
            self.scrap_code_list.addItem(select_all_item)
            priority_order = {scrap_code: index for index, scrap_code in enumerate(self.PRIORITY_SCRAP_CODES)}
            ordered_scrap_codes = sorted(scrap_codes, key=lambda scrap_code: (0, priority_order[scrap_code]) if scrap_code in priority_order else (1, 0))
            for scrap_code in ordered_scrap_codes:
                item = QListWidgetItem(scrap_code)
                item.setData(Qt.UserRole, scrap_code)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                if scrap_code in priority_order:
                    item.setForeground(QColor('#DC2626'))
                self.scrap_code_list.addItem(item)
        finally:
            self._updating_scrap_selection = False

    def _load_model_options(self, models: list[str]) -> None:
        """Nạp Model dạng checkbox kèm Select All."""
        self._updating_model_selection = True
        try:
            self.model_list.clear()
            select_all_item = QListWidgetItem('Select All')
            select_all_item.setFlags(select_all_item.flags() | Qt.ItemIsUserCheckable)
            select_all_item.setCheckState(Qt.Checked)
            self.model_list.addItem(select_all_item)
            for model in models:
                item = QListWidgetItem(model)
                item.setData(Qt.UserRole, model)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)
                self.model_list.addItem(item)
        finally:
            self._updating_model_selection = False

    def _on_model_item_changed(self, changed_item: QListWidgetItem) -> None:
        """Đồng bộ Select All và từng Model."""
        if self._updating_model_selection:
            return
        self._updating_model_selection = True
        try:
            changed_row = self.model_list.row(changed_item)
            if changed_row == 0:
                new_state = Qt.Checked if changed_item.checkState() == Qt.Checked else Qt.Unchecked
                for index in range(1, self.model_list.count()):
                    self.model_list.item(index).setCheckState(new_state)
                return
            total_count = self.model_list.count() - 1
            checked_count = sum((1 for index in range(1, self.model_list.count()) if self.model_list.item(index).checkState() == Qt.Checked))
            self.model_list.item(0).setCheckState(Qt.Checked if total_count > 0 and checked_count == total_count else Qt.Unchecked)
        finally:
            self._updating_model_selection = False

    def _get_selected_models(self) -> list[str]:
        """Lấy danh sách Model đang được tick."""
        return [self.model_list.item(index).data(Qt.UserRole) for index in range(1, self.model_list.count()) if self.model_list.item(index).checkState() == Qt.Checked]

    def _on_scrap_code_item_changed(self, changed_item: QListWidgetItem) -> None:
        """Đồng bộ trạng thái giữa Select All và từng Scrap code."""
        if self._updating_scrap_selection:
            return
        self._updating_scrap_selection = True
        try:
            changed_row = self.scrap_code_list.row(changed_item)
            if changed_row == 0:
                is_checked = changed_item.checkState() == Qt.Checked
                for index in range(1, self.scrap_code_list.count()):
                    self.scrap_code_list.item(index).setCheckState(Qt.Checked if is_checked else Qt.Unchecked)
                return
            total_count = self.scrap_code_list.count() - 1
            checked_count = sum((1 for index in range(1, self.scrap_code_list.count()) if self.scrap_code_list.item(index).checkState() == Qt.Checked))
            select_all_item = self.scrap_code_list.item(0)
            select_all_item.setCheckState(Qt.Checked if total_count > 0 and checked_count == total_count else Qt.Unchecked)
        finally:
            self._updating_scrap_selection = False

    def _load_tier_options(self, tiers: list[str]) -> None:
        """Nạp Tier khác NULL và mặc định chọn tất cả."""
        self._updating_tier_selection = True
        try:
            self.tier_list.clear()
            select_all_item = QListWidgetItem('Select All')
            select_all_item.setFlags(select_all_item.flags() | Qt.ItemIsUserCheckable)
            select_all_item.setCheckState(Qt.Checked)
            self.tier_list.addItem(select_all_item)
            for tier in tiers:
                item = QListWidgetItem(str(tier))
                item.setData(Qt.UserRole, tier)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)
                self.tier_list.addItem(item)
        finally:
            self._updating_tier_selection = False

    def _on_tier_item_changed(self, changed_item: QListWidgetItem) -> None:
        """Đồng bộ trạng thái Select All và từng Tier."""
        if self._updating_tier_selection:
            return
        self._updating_tier_selection = True
        try:
            changed_row = self.tier_list.row(changed_item)
            if changed_row == 0:
                new_state = Qt.Checked if changed_item.checkState() == Qt.Checked else Qt.Unchecked
                for index in range(1, self.tier_list.count()):
                    self.tier_list.item(index).setCheckState(new_state)
                return
            total_count = self.tier_list.count() - 1
            checked_count = sum((1 for index in range(1, self.tier_list.count()) if self.tier_list.item(index).checkState() == Qt.Checked))
            self.tier_list.item(0).setCheckState(Qt.Checked if total_count > 0 and checked_count == total_count else Qt.Unchecked)
        finally:
            self._updating_tier_selection = False

    def _emit_filter_criteria(self) -> None:
        """Tạo FilterCriteria hiện tại và gửi ra MainWindow."""
        self.filter_applied.emit(self.get_filter_criteria())

    def get_filter_criteria(self) -> FilterCriteria:
        """Read the current controls, including changes not yet submitted with SEARCH."""
        return FilterCriteria(date_from=self.from_date_edit.date().toString('yyyyMMdd'), date_to=self.to_date_edit.date().toString('yyyyMMdd'), selected_date=None, eqp=self.eqp_combo.currentData(), slot=self.slot_combo.currentData(), scrap_codes=self._get_selected_scrap_codes(), tiers=self._get_selected_tiers(), models=self._get_selected_models())

    def _get_selected_scrap_codes(self) -> list[str]:
        """Lấy danh sách Scrap code đang được người dùng tick."""
        selected_codes = []
        for index in range(1, self.scrap_code_list.count()):
            item = self.scrap_code_list.item(index)
            if item.checkState() == Qt.Checked:
                selected_codes.append(item.data(Qt.UserRole))
        return selected_codes

    def _get_selected_tiers(self) -> list[str]:
        """Lấy các Tier khác NULL đang được tick."""
        selected_tiers: list[str] = []
        for index in range(1, self.tier_list.count()):
            item = self.tier_list.item(index)
            if item.checkState() == Qt.Checked:
                tier = item.data(Qt.UserRole)
                if tier is not None:
                    selected_tiers.append(str(tier))
        return selected_tiers

    def set_import_buttons_enabled(self, is_enabled: bool) -> None:
        """Bật hoặc tắt đồng thời hai nút Import."""
        self.import_prime_button.setEnabled(is_enabled)
        self.import_cum_button.setEnabled(is_enabled)
