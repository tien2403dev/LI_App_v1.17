from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QKeySequence
from PyQt5.QtWidgets import (
    QAbstractItemView, QAction, QApplication, QHeaderView, QHBoxLayout,
    QLabel, QPushButton, QTableView, QVBoxLayout, QWidget, QSizePolicy,
)


class ModelSummaryTableModel(QAbstractTableModel):
    """Đọc dữ liệu trực tiếp từ kết quả tổng hợp, không tạo item từng ô."""

    def __init__(self, parent=None):
        """Khởi tạo bảng rỗng và các cột sản lượng cố định."""
        super().__init__(parent)
        self.result = None
        self.headers = ['Model', 'In', 'Out', 'Fail', 'Yield']

    def set_result(self, result):
        """Thay toàn bộ dữ liệu bằng một lần reset model."""
        self.beginResetModel()
        self.result = result
        self.headers = ['Model', 'In', 'Out', 'Fail', 'Yield'] + (
            result.scrap_codes if result else [])
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        """Trả số Model và một dòng Total khi có dữ liệu."""
        return 0 if parent.isValid() or not self.result or not self.result.rows else len(self.result.rows) + 1

    def columnCount(self, parent=QModelIndex()):
        """Trả số cột gồm tất cả scrapcode trong kết quả đã lọc."""
        return 0 if parent.isValid() else len(self.headers)

    def text_at(self, row, column):
        """Định dạng chung cho giao diện và clipboard; ô không có scrap để trống."""
        if row == len(self.result.rows):
            if column < 5:
                return 'Total' if column == 0 else ''
            return str(self.result.scrap_totals.get(self.headers[column], 0))
        item = self.result.rows[row]
        values = [item.model, str(item.in_qty), str(item.out_qty), str(item.fail_qty),
                  f'{item.yield_percent:.2f}%' if item.yield_percent is not None else '—']
        if column < 5:
            return values[column]
        qty = item.scrap_qty.get(self.headers[column], 0)
        return str(qty) if qty else ''

    def data(self, index, role=Qt.DisplayRole):
        """Cung cấp chữ, căn giữa và nền xanh cho dòng Total."""
        if not index.isValid() or not self.result:
            return None
        if role == Qt.DisplayRole:
            return self.text_at(index.row(), index.column())
        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignCenter)
        if index.row() == len(self.result.rows):
            if role == Qt.BackgroundRole:
                return QColor('#A9D08E')
            if role == Qt.FontRole:
                font = QFont()
                font.setBold(True)
                return font
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """Hiển thị tiêu đề Model, sản lượng và mã scrap."""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]
        return None


class ModelSummaryWidget(QWidget):
    """Bảng Cum theo Model và biểu đồ cột chồng scrap/đường Yield bên dưới."""

    def __init__(self, parent=None):
        """Dựng UI nhẹ; chưa import Matplotlib khi mở ứng dụng."""
        super().__init__(parent)
        self.result = None
        self.codes = ()
        self.chart = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        heading = QHBoxLayout()
        self.title = QLabel('Cum Yield by Model')
        self.title.setStyleSheet('font-size:14px; font-weight:bold;')
        heading.addWidget(self.title)
        self.copy_button = QPushButton('Copy All')
        self.copy_button.clicked.connect(self.copy_all)
        heading.addWidget(self.copy_button)
        heading.addStretch()
        layout.addLayout(heading)
        self.table = QTableView()
        self.table_model = ModelSummaryTableModel(self)
        self.table.setModel(self.table_model)
        self.table.verticalHeader().hide()
        self.table.verticalHeader().setDefaultSectionSize(26)
        self.table.horizontalHeader().setFixedHeight(28)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setDefaultSectionSize(48)
        self.table.setMinimumWidth(0)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setStyleSheet("""
            QTableView {
                background: white;
                color: black;
                gridline-color: #333333;
                border: 1px solid #333333;
                font-size: 13px;
            }

            QHeaderView::section {
                background: #A9D08E;
                color: black;
                border: 1px solid #333333;
                font-weight: bold;
                padding: 3px;
            }

            QScrollBar:horizontal {
                background: #EEEEEE;
                height: 10px;
                margin: 0px;
                border: none;
            }

            QScrollBar::handle:horizontal {
                background: #999999;
                min-width: 30px;
                border-radius: 4px;
                margin: 1px 0px;
            }

            QScrollBar:vertical {
                background: #EEEEEE;
                width: 10px;
                margin: 0px;
                border: none;
            }

            QScrollBar::handle:vertical {
                background: #999999;
                min-height: 30px;
                border-radius: 4px;
                margin: 0px 1px;
            }

            QScrollBar::handle:horizontal:hover,
            QScrollBar::handle:vertical:hover {
                background: #777777;
            }

            QScrollBar::handle:horizontal:pressed,
            QScrollBar::handle:vertical:pressed {
                background: #666666;
            }

            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0px;
                background: none;
                border: none;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
                background: none;
                border: none;
            }

            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }

            QTableView QAbstractScrollArea::corner {
                background: #EEEEEE;
                border: none;
            }
        """)
        self.table.setFixedHeight(84)
        copy_action = QAction('Copy All', self.table)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.setShortcutContext(Qt.WidgetShortcut)
        copy_action.triggered.connect(self.copy_all)
        self.table.addAction(copy_action)
        self.table.setContextMenuPolicy(Qt.ActionsContextMenu)
        layout.addWidget(self.table)
        self.chart_layout = QVBoxLayout()
        self.placeholder = QLabel('Biểu đồ sẽ được tạo khi bấm SEARCH.')
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.chart_layout.addWidget(self.placeholder)
        layout.addLayout(self.chart_layout)
        self.copy_button.setEnabled(False)

    def load_result(self, result, key, codes):
        """Nạp bảng đầy đủ rồi vẽ các scrapcode đang chọn từ cùng kết quả."""
        self.result = result
        self.title.setText(f'Cum Yield by Model | {key[0]} - {key[1]}')
        self.table.clearSpans()
        self.table_model.set_result(result)
        count = self.table_model.rowCount()
        if count:
            self.table.setSpan(count - 1, 0, 1, 5)
        content_height = 28 + count * 26 + self.table.frameWidth() * 2
        self._fit_columns()
        # Dự phòng thanh cuộn ngang; bảng tự giãn theo toàn bộ chiều ngang tab.
        content_height += self.table.horizontalScrollBar().sizeHint().height()
        self.table.setFixedHeight(min(440, max(58, content_height)))
        self.copy_button.setEnabled(bool(count))
        self.update_codes(codes)

    def update_codes(self, codes):
        """Đổi scrap chỉ vẽ lại biểu đồ từ cache, không reset bảng hoặc query DB."""
        self.codes = tuple(sorted(set(codes)))
        if self.result is None:
            return
        if self.chart is None:
            from ui.charts.cum_model_chart import CumModelChart
            self.placeholder.hide()
            self.chart = CumModelChart(self)
            self.chart_layout.addWidget(self.chart, 0, Qt.AlignLeft)
        self.chart.update_chart(self.result, self.codes)

    def copy_all(self):
        """Copy cả header, tất cả Model/scrap và Total dạng TSV để dán Excel."""
        model = self.table_model
        if not model.rowCount():
            return
        lines = ['\t'.join(model.headers)]
        lines.extend('\t'.join(model.text_at(row, col) for col in range(model.columnCount()))
                     for row in range(model.rowCount()))
        QApplication.clipboard().setText('\n'.join(lines))

    def clear_result(self, message):
        """Xóa cache và biểu đồ khi import lại hoặc tải dữ liệu lỗi."""
        self.result = None
        self.table.clearSpans()
        self.table_model.set_result(None)
        self.table.setFixedHeight(84)
        self.copy_button.setEnabled(False)
        self.title.setText('Cum Yield by Model')
        self.placeholder.setText(message)
        if self.chart is not None:
            self.chart.show_empty_state(message)

    def _fit_columns(self):
        """Co từng cột vừa header/số lượng, kể cả Total; không kéo giãn mã lỗi."""
        self.table.ensurePolished()
        normal = self.table.fontMetrics()
        bold_font = QFont(self.table.font())
        bold_font.setBold(True)
        bold = QFontMetrics(bold_font)
        model = self.table_model
        for column, title in enumerate(model.headers):
            width = bold.horizontalAdvance(title)
            for row in range(model.rowCount()):
                metrics = bold if row == model.rowCount() - 1 else normal
                width = max(width, metrics.horizontalAdvance(model.text_at(row, column)))
            self.table.setColumnWidth(column, width + 14)
