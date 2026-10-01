"""Cửa sổ lịch sử chỉ đọc, tám cột PRIME và lựa chọn bằng chứng theo quy tắc."""
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                            QTableView, QHeaderView, QAbstractItemView, QDialogButtonBox)

COLUMNS = (('No', None), ('Date', 'DATE'), ('Time', 'TIME'), ('Model', 'MODEL'), ('Lot ID', 'LOTNO'),
           ('Result', 'RESULT'), ('Scrapcode', 'SCRAPCODE'),
           ('Test count', 'TEST_COUNT'), ('Fail qty (QTY)', 'QTY'))


class HistoryTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = []

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(COLUMNS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return COLUMNS[section][0]
        return super().headerData(section, orientation, role)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = self.rows[index.row()]
        if role in (Qt.DisplayRole, Qt.ToolTipRole):
            if index.column() == 0:
                return str(index.row() + 1)
            value = row[COLUMNS[index.column()][1]]
            return '' if value is None else str(value)
        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignCenter)
        if role == Qt.ForegroundRole and index.column() == 5:
            return QColor('#B42318' if row['RESULT'] == 'FAIL' else '#067647')
        return None

    def set_rows(self, rows):
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()


class SlotFailHistoryDialog(QDialog):
    def __init__(self, history, parent=None, preferred_rule=None):
        super().__init__(parent)
        self.setWindowTitle(f"Slot Fail History: EQP: {history['eqp']}  SLOT: {history['slot']}")
        self.resize(1050, 580)
        self.groups = history['groups']
        layout = QVBoxLayout(self)
        self.fail_comment = QLabel()
        self.fail_comment.setTextFormat(Qt.PlainText)
        self.fail_comment.setText('Fail comment: ' + str(history.get('fail_comment') or ''))
        self.fail_comment.setWordWrap(True)
        self.fail_comment.setVisible(bool(history.get('fail_comment')))
        layout.addWidget(self.fail_comment)
        bar = QHBoxLayout()
        bar.addWidget(QLabel('Quy tắc / chuỗi:'))
        self.rule_combo = QComboBox()
        self.rule_combo.addItems([group['label'] for group in self.groups])
        bar.addWidget(self.rule_combo, 1)
        layout.addLayout(bar)
        self.summary = QLabel()
        layout.addWidget(self.summary)
        self.note = QLabel()
        self.note.setWordWrap(True)
        layout.addWidget(self.note)
        self.table = QTableView()
        self.model = HistoryTableModel(self)
        self.table.setModel(self.model)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setWordWrap(False)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 45)
        self.table.setStyleSheet('QHeaderView::section {background:#DCEAF7; padding:8px; border:1px solid #B8CDE0;}')
        layout.addWidget(self.table, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.rule_combo.currentIndexChanged.connect(self.show_group)
        selected = next((i for i, group in enumerate(self.groups)
                         if preferred_rule and group['label'].startswith(f'Yield {preferred_rule} ')), 0)
        self.rule_combo.setCurrentIndex(selected)
        self.show_group(selected)

    def show_group(self, index):
        group = self.groups[index]
        tests = group['tests']
        self.model.set_rows(tests)
        failures = [row for row in tests if row['RESULT'] == 'FAIL']
        self.summary.setText(f'Tổng số test: {len(tests)}  |  Số dòng FAIL: {len(failures)}'
                             f"  |  Tổng FAIL QTY: {sum(row['QTY'] for row in failures)}")
        note = group['error'] or group['note']
        self.note.setText(note)
        self.note.setVisible(bool(note))
        self.note.setStyleSheet('color:#B42318;' if group['error'] else 'color:#475467;')
