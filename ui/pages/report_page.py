from __future__ import annotations

from PyQt5.QtCore import (
    QAbstractTableModel, QDateTime, QTime, QModelIndex, QThread, QTimer, Qt,
    QSize,
    pyqtSignal,
)
from PyQt5.QtGui import QGuiApplication, QKeySequence
from PyQt5.QtWidgets import (
    QAbstractItemView, QCheckBox, QDateTimeEdit, QDialog, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QTableView, QVBoxLayout, QWidget, QTabBar,
    QTabWidget,
)

from ui.report_detail_dialog import ReportDetailDialog
from workers.report_worker import ReportWorker
from ui.database_wait import wait_manager, cancel_read_task


class ReportTabBar(QTabBar):
    """Use the same 170 px tab width as the main Summary tab bar."""

    def tabSizeHint(self, index):
        size = super().tabSizeHint(index)
        size.setWidth(170)
        return size


class FullRowCheckList(QListWidget):
    """Bấm ở bất kỳ vị trí nào trên hàng để đổi trạng thái checkbox."""

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if item is None:
            super().mousePressEvent(event)
            return
        self.setFocus()
        self.setCurrentItem(item)
        item.setCheckState(
            Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked
        )
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space and self.currentItem() is not None:
            item = self.currentItem()
            item.setCheckState(
                Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked
            )
            return
        super().keyPressEvent(event)


class ReportFilterDialog(QDialog):
    """Dialog chọn EQP hoặc SLOT; SLOT chia bốn cột, mỗi cột 12."""

    ITEM_HEIGHT = 34

    def __init__(self, title, values, selected_order, two_columns=False, parent=None):
        super().__init__(parent)
        self.values = list(values)
        self.selection_order = list(selected_order)
        self._updating = False
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(860 if two_columns else 420, 640)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        title_label = QLabel("Filter by value:")
        title_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        layout.addWidget(title_label)

        self.search_edit = QLineEdit(self)
        self.search_edit.setPlaceholderText("Search")
        self.search_edit.setFixedHeight(38)
        self.search_edit.setStyleSheet("font-size: 13px; padding: 4px 8px;")
        layout.addWidget(self.search_edit)

        self.select_all = QCheckBox("Select All", self)
        self.select_all.setTristate(True)
        self.select_all.setFixedHeight(32)
        self.select_all.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.select_all)

        lists_layout = QHBoxLayout()
        lists_layout.setSpacing(12)
        self.list_widgets = [FullRowCheckList(self)]
        if two_columns:
            self.list_widgets.extend(FullRowCheckList(self) for _ in range(3))

        for list_widget in self.list_widgets:
            list_widget.setAlternatingRowColors(True)
            list_widget.setStyleSheet("font-size: 13px;")
            lists_layout.addWidget(list_widget, 1)

        selected_set = set(selected_order)
        for value in self.values:
            list_index = 0
            if two_columns:
                try:
                    list_index = min(3, max(0, (int(value) - 1) // 12))
                except ValueError:
                    list_index = 0
            item = QListWidgetItem(value)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if value in selected_set else Qt.Unchecked)
            item.setData(Qt.UserRole, value)
            self.list_widgets[list_index].addItem(item)
            self.list_widgets[list_index].setUniformItemSizes(True)
            self.list_widgets[list_index].setStyleSheet(
                "QListWidget { font-size: 13px; }"
                f"QListWidget::item {{ height: {self.ITEM_HEIGHT}px; }}"
            )

        layout.addLayout(lists_layout, 1)

        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK", self)
        cancel_button = QPushButton("Cancel", self)
        for button in (ok_button, cancel_button):
            button.setFixedHeight(38)
        ok_button.setStyleSheet(
            "QPushButton { background:#1976D2; color:white; border:none; "
            "border-radius:5px; font-size:13px; font-weight:600; }"
        )
        button_layout.addWidget(ok_button, 1)
        button_layout.addWidget(cancel_button, 1)
        layout.addLayout(button_layout)

        for list_widget in self.list_widgets:
            list_widget.itemChanged.connect(self._item_changed)
        self.search_edit.textChanged.connect(self._filter_items)
        self.select_all.stateChanged.connect(self._set_all)
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        self._update_select_all()
        self.search_edit.setFocus()

    def _item_changed(self, item):
        if self._updating:
            return
        value = item.data(Qt.UserRole)
        if item.checkState() == Qt.Checked:
            if value not in self.selection_order:
                self.selection_order.append(value)
        elif value in self.selection_order:
            self.selection_order.remove(value)
        self._update_select_all()

    def _set_all(self, state):
        if self._updating:
            return
        checked = state != Qt.Unchecked
        self._updating = True
        try:
            for list_widget in self.list_widgets:
                for index in range(list_widget.count()):
                    list_widget.item(index).setCheckState(
                        Qt.Checked if checked else Qt.Unchecked
                    )
            self.selection_order = list(self.values) if checked else []
        finally:
            self._updating = False
        self._update_select_all()

    def _update_select_all(self):
        checked_count = sum(
            item.checkState() == Qt.Checked
            for list_widget in self.list_widgets
            for item in (list_widget.item(i) for i in range(list_widget.count()))
        )
        self._updating = True
        try:
            if checked_count == 0:
                self.select_all.setCheckState(Qt.Unchecked)
            elif checked_count == len(self.values):
                self.select_all.setCheckState(Qt.Checked)
            else:
                self.select_all.setCheckState(Qt.PartiallyChecked)
        finally:
            self._updating = False

    def _filter_items(self, text):
        query = text.strip().lower()
        for list_widget in self.list_widgets:
            for index in range(list_widget.count()):
                item = list_widget.item(index)
                item.setHidden(query not in item.text().lower())

    def selected_values_ordered(self):
        checked = {
            item.data(Qt.UserRole)
            for list_widget in self.list_widgets
            for item in (list_widget.item(i) for i in range(list_widget.count()))
            if item.checkState() == Qt.Checked
        }
        ordered = [value for value in self.selection_order if value in checked]
        ordered.extend(value for value in self.values if value in checked and value not in ordered)
        return ordered


class MultiSelectButton(QPushButton):
    selection_changed = pyqtSignal()

    def __init__(self, title, parent=None):
        super().__init__("Select...", parent)
        self.title = title
        self.values = []
        self.selected = []
        self.clicked.connect(self._open_dialog)

    def set_values(self, values):
        self.values = [str(value) for value in values]
        self.selected = [
            value for value in self.selected
            if value in self.values
        ]
        self._update_text()

    def _open_dialog(self):
        dialog = ReportFilterDialog(
            self.title,
            self.values,
            self.selected,
            two_columns=self.title == "Select SLOT",
            parent=self,
        )
        if dialog.exec_() == dialog.Accepted:
            new_selection = dialog.selected_values_ordered()
            changed = new_selection != self.selected
            self.selected = new_selection
            self._update_text()
            if changed:
                self.selection_changed.emit()

    def _update_text(self):
        if not self.selected:
            self.setText("Select...")
        elif len(self.selected) == len(self.values):
            self.setText("All")
        elif len(self.selected) == 1:
            self.setText(next(iter(self.selected)))
        else:
            self.setText(f"{len(self.selected)} selected")

    def selected_values(self):
        return list(self.selected)


class ReportSummaryModel(QAbstractTableModel):
    HEADERS = ["DATE", "EQP", "SLOT", "IN", "OUT", "FAIL", "SCRAP CODE", "YIELD", "MODEL"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = []

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.HEADERS)

    @staticmethod
    def _slash_separated(value):
        if value is None:
            return ""
        normalized = str(value).replace("\r\n", "\n").replace("\r", "\n")
        return " / ".join(
            part.strip() for part in normalized.split("\n") if part.strip()
        )

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignCenter)
        if role != Qt.DisplayRole:
            return None
        row = self.rows[index.row()]
        if row.in_qty is None:
            values = (row.date, row.eqp, row.slot, "", "", "", "", "", "")
            return values[index.column()]
        return (
            row.date, row.eqp, row.slot, row.in_qty, row.out_qty,
            row.fail_qty, self._slash_separated(row.scrap_codes),
            "—" if row.yield_percent is None else f"{row.yield_percent:.2f}%",
            self._slash_separated(row.models),
        )[index.column()]

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return None

    def set_rows(self, rows):
        self.beginResetModel()
        self.rows = list(rows)
        self.endResetModel()


class ReportTableView(QTableView):
    @staticmethod
    def _cell_text(value):
        text = "" if value is None else str(value)
        return text.replace("\r\n", "\n").replace("\r", "\n")

    @classmethod
    def _plain_clipboard_cell(cls, value):
        """Fallback TSV: bọc ô nhiều dòng bằng dấu nháy kép."""
        text = cls._cell_text(value)
        if any(character in text for character in ('\t', '\n', '"')):
            return '"' + text.replace('"', '""') + '"'
        return text

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            indexes = sorted(self.selectedIndexes(), key=lambda item: (item.row(), item.column()))
            if indexes:
                rows = sorted({item.row() for item in indexes})
                columns = sorted({item.column() for item in indexes})
                values = [
                    [
                        self.model().index(row, column).data()
                        for column in columns
                    ]
                    for row in rows
                ]
                plain_text = "\n".join(
                    "\t".join(
                        self._plain_clipboard_cell(value)
                        for value in row_values
                    )
                    for row_values in values
                )
                # Plain TSV avoids Windows CF_HTML metadata in Excel paste.
                QGuiApplication.clipboard().setText(plain_text)
                return
        super().keyPressEvent(event)


class SlotLookupPage(QWidget):
    def __init__(self, database_path, parent=None):
        super().__init__(parent)
        self.database_path = database_path
        self.thread = None
        self.worker = None
        self._dialogs = []
        self._last_range = None
        self._pending_search = False
        self._closing = False
        self._options_dirty = False
        self._request_range = None
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)
        self._search_timer.timeout.connect(self.search)
        self._build_ui()
        self._start_worker("options")

    def _build_ui(self):
        layout = QVBoxLayout(self)
        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)

        now = QDateTime.currentDateTime()
        self.from_edit = QDateTimeEdit(QDateTime(now.date(), QTime(0, 0)), self)
        self.to_edit = QDateTimeEdit(QDateTime(now.date(), QTime(23, 59, 59)), self)
        for editor in (self.from_edit, self.to_edit):
            editor.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
            editor.setCalendarPopup(True)
            editor.setFixedSize(220, 42)
            editor.setStyleSheet(
                "QDateTimeEdit { font-size: 14px; padding: 4px 8px; }"
            )
            editor.dateTimeChanged.connect(self._schedule_search)

        self.eqp_button = MultiSelectButton("Select EQP", self)
        self.slot_button = MultiSelectButton("Select SLOT", self)
        for button in (self.eqp_button, self.slot_button):
            button.setFixedSize(180, 42)
            button.setStyleSheet(
                "QPushButton { font-size: 14px; padding: 4px 10px; }"
            )
            button.selection_changed.connect(self._schedule_search)

        for label, widget in (
            ("From", self.from_edit), ("To", self.to_edit),
            ("EQP", self.eqp_button), ("SLOT", self.slot_button),
        ):
            title = QLabel(label)
            title.setStyleSheet("font-size: 13px; font-weight: 600;")
            filter_row.addWidget(title)
            filter_row.addWidget(widget)
        filter_row.addStretch(1)
        layout.addLayout(filter_row)

        actions = QHBoxLayout()
        full_day = QPushButton("Trọn ngày 00:00–23:59:59")
        full_day.clicked.connect(self._full_days)
        actions.addWidget(full_day)
        refresh = QPushButton("Tải lại dữ liệu")
        refresh.clicked.connect(self._schedule_search)
        actions.addWidget(refresh)
        actions.addStretch()
        layout.addLayout(actions)

        self.status_label = QLabel("Đang tải lựa chọn bộ lọc...")
        layout.addWidget(self.status_label)
        self.model = ReportSummaryModel(self)
        self.table = ReportTableView(self)
        self.table.setModel(self.model)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        widths = (95, 110, 70, 70, 70, 70, 150, 90, 150)
        for column, width in enumerate(widths):
            self.table.setColumnWidth(column, width)
        self.table.doubleClicked.connect(self._open_details)
        layout.addWidget(self.table, 1)
        self._invalidate_source()

    def _full_days(self):
        """Giữ ngày đang chọn, đặt lại giờ đầu/cuối ngày cho truy vấn."""
        self.from_edit.setTime(QTime(0, 0))
        self.to_edit.setTime(QTime(23, 59, 59))

    def _invalidate_source(self):
        """Khóa nguồn cũ khi bộ lọc thay đổi; giữ báo cáo đã soạn."""
        self._last_range = None

    def _start_worker(self, action, **arguments):
        if self.is_busy() or self._closing:
            return
        self.thread = QThread(self)
        self.worker = ReportWorker(self.database_path, action, **arguments)
        wait_manager(self).bind(self.worker)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        if action == "options":
            self.worker.succeeded.connect(self._options_loaded)
        else:
            self.worker.succeeded.connect(self._summary_loaded)
        self.worker.failed.connect(self._failed)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self._finished)
        self.thread.start()

    def _schedule_search(self, *_args):
        """Gộp các thay đổi liên tiếp rồi tự động chạy lại truy vấn."""
        if self._closing:
            return
        self._invalidate_source()
        self._pending_search = True
        self._search_timer.start()

    def search(self):
        if self._closing:
            return
        if self.is_busy():
            self._pending_search = True
            return
        self._invalidate_source()
        selected_eqps = self.eqp_button.selected_values()
        selected_slots = self.slot_button.selected_values()
        if not selected_eqps or not selected_slots:
            self._pending_search = False
            self.model.set_rows([])
            self._last_range = None
            self.status_label.setText(
                "Vui lòng chọn ít nhất một EQP và một SLOT."
            )
            return
        date_from = self.from_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        date_to = self.to_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        if date_from > date_to:
            self._pending_search = False
            QMessageBox.warning(self, "Report", "From phải nhỏ hơn hoặc bằng To.")
            return
        self._pending_search = False
        self._request_range = (date_from, date_to)
        self._last_range = None
        self.status_label.setText("Đang tải dữ liệu Report...")
        self._start_worker(
            "summary", date_from=date_from, date_to=date_to,
            eqps=selected_eqps,
            slots=[int(value) for value in selected_slots],
        )

    def _options_loaded(self, result):
        eqps, slots = result
        self.eqp_button.set_values(eqps)
        self.slot_button.set_values(range(1, 49))
        self.status_label.setText(
            "Vui lòng chọn ít nhất một EQP và một SLOT."
        )

    def _summary_loaded(self, rows):
        if self._closing or self._pending_search:
            return
        self._last_range = self._request_range
        self.model.set_rows(rows)
        self.status_label.setText(f"{len(rows):,} dòng — nhấp đúp để xem chi tiết, Ctrl+C để sao chép")

    def _failed(self, message):
        if self._closing:
            return
        self.status_label.setText("Không thể tải dữ liệu Report.")
        QMessageBox.critical(self, "Report", message)

    def _finished(self):
        self.thread.deleteLater()
        self.thread = None
        self.worker = None
        if self._closing:
            return
        if self._options_dirty and self.isVisible():
            self.load_if_needed()
            return
        if self._pending_search:
            self._search_timer.start(0)

    def _open_details(self, index):
        if self._closing or self.is_busy() or self._pending_search or not index.isValid() or self._last_range is None:
            return
        row = self.model.rows[index.row()]
        dialog = ReportDetailDialog(
            self.database_path, self._last_range[0], self._last_range[1], row, self,
        )
        self._dialogs.append(dialog)
        dialog.finished.connect(lambda _result, item=dialog: self._dialogs.remove(item))
        dialog.show()

    def is_busy(self):
        return self.thread is not None

    def mark_data_changed(self):
        self._invalidate_source()
        self._options_dirty = True
        self._pending_search = True
        if self.isVisible():
            self.load_if_needed()

    def load_if_needed(self):
        if self._options_dirty and not self.is_busy() and not self._closing:
            self._options_dirty = False
            self._start_worker("options")

    def prepare_close(self):
        cancel_read_task(self.worker)
        self._closing = True
        self._pending_search = False
        self._search_timer.stop()

    def has_running_tasks(self):
        return self.is_busy() or any(dialog.thread is not None for dialog in self._dialogs)


class ReportPage(QWidget):
    """Aging-style report workflow and independent LI slot lookup."""
    def __init__(self, database_path, parent=None):
        super().__init__(parent)
        from ui.widgets.slot_report_builder import SlotReportBuilder
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.pages = QTabWidget(self)
        self.pages.setTabBar(ReportTabBar(self.pages))
        self.pages.tabBar().setExpanding(False)
        self.pages.setStyleSheet(
            'QTabBar { border:none; }'
            'QTabBar::tab { background:#E8EEF5; color:#1E4F7A; padding:9px 10px; '
            'border-left:1px solid #D4DFEB; border-right:1px solid #D4DFEB; '
            'border-bottom:1px solid #D4DFEB; border-top:none; '
            'border-top-left-radius:5px; border-top-right-radius:5px; '
            'margin-right:2px; font-size:14px; font-weight:700; }'
            'QTabBar::tab:selected { background:white; color:#0078D7; '
            'border-bottom:2px solid #1684E8; }'
            'QTabWidget::pane { border:none; background:white; }'
        )
        self.builder = SlotReportBuilder(database_path, self)
        self.lookup = SlotLookupPage(database_path, self)
        self.pages.addTab(self.builder, 'Báo cáo Slot')
        self.pages.addTab(self.lookup, 'Tra cứu SLOT')
        layout.addWidget(self.pages)
        self.pages.currentChanged.connect(lambda _index: self.load_if_needed())

    def load_if_needed(self):
        self.builder.load_if_needed()
        self.lookup.load_if_needed()

    def mark_data_changed(self):
        self.builder.mark_data_changed()
        self.lookup.mark_data_changed()

    def prepare_close(self):
        self.builder.prepare_close()
        self.lookup.prepare_close()

    def has_running_tasks(self):
        return self.builder.is_busy() or self.lookup.has_running_tasks()

    def is_busy(self):
        return self.has_running_tasks()
