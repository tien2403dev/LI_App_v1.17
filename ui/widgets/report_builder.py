from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QGuiApplication, QKeySequence
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSplitter,
    QTreeWidget, QTreeWidgetItem, QAbstractItemView, QTableWidget,
    QTableWidgetItem, QFileDialog, QMessageBox,
)
from services.report_export import HEADERS, cells, spans, yield_color, clipboard_text, export_excel


class SourceTree(QTreeWidget):
    """Chọn nguồn theo ngày/EQP/SLOT, giữ thứ tự tick SLOT."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows_by_key = {}
        self.checked_keys = []
        self.setHeaderLabel("1. Nguồn báo cáo")
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.itemChanged.connect(self._check_changed)

    def set_rows(self, rows):
        """Thay nguồn truy vấn và bỏ lựa chọn nguồn cũ."""
        self.blockSignals(True)
        try:
            self.clear()
            self.rows_by_key = {}
            self.checked_keys = []
            dates, eqps = {}, {}
            for row in rows:
                key = (row.date, row.eqp, row.slot)
                if row.date not in dates:
                    dates[row.date] = self._node(self.invisibleRootItem(), cells(row)[0])
                group = (row.date, row.eqp)
                if group not in eqps:
                    eqps[group] = self._node(dates[row.date], row.eqp)
                leaf = self._node(eqps[group], f"SLOT {row.slot}" + (" (không dữ liệu)" if row.in_qty is None else ""))
                leaf.setData(0, Qt.UserRole, key)
                self.rows_by_key[key] = row
            self.expandToDepth(1)
        finally:
            self.blockSignals(False)

    @staticmethod
    def _node(parent, label):
        """Tạo nút có checkbox và hỗ trợ kéo."""
        item = QTreeWidgetItem(parent, [label])
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsDragEnabled)
        item.setCheckState(0, Qt.Unchecked)
        return item

    def _leaves(self, item):
        """Duyệt SLOT con theo thứ tự hiển thị."""
        if item.childCount():
            for i in range(item.childCount()):
                yield from self._leaves(item.child(i))
        elif item.data(0, Qt.UserRole) is not None:
            yield item

    def _check_changed(self, item, column):
        """Tick nhóm chọn mọi SLOT con và cập nhật trạng thái nhóm cha."""
        self.blockSignals(True)
        try:
            checked = item.checkState(0) != Qt.Unchecked
            for leaf in self._leaves(item):
                leaf.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)
                key = leaf.data(0, Qt.UserRole)
                if checked and key not in self.checked_keys:
                    self.checked_keys.append(key)
                elif not checked and key in self.checked_keys:
                    self.checked_keys.remove(key)
            def update(node):
                if not node.childCount():
                    return node.checkState(0)
                states = [update(node.child(i)) for i in range(node.childCount())]
                state = states[0] if all(s == states[0] for s in states) else Qt.PartiallyChecked
                node.setCheckState(0, state)
                return state
            for i in range(self.topLevelItemCount()):
                update(self.topLevelItem(i))
        finally:
            self.blockSignals(False)

    def chosen_rows(self):
        """Lấy các SLOT theo thứ tự tick."""
        return [self.rows_by_key[key] for key in self.checked_keys]

    def dragged_rows(self):
        """Kéo một nút để thêm riêng nút đó và toàn bộ SLOT con."""
        item = self.currentItem()
        return [] if item is None else [self.rows_by_key[n.data(0, Qt.UserRole)] for n in self._leaves(item)]


class OrderTree(QTreeWidget):
    reordered = pyqtSignal()
    rows_dropped = pyqtSignal(object)

    def _is_source(self, event):
        """Chỉ nhận nguồn của chính bộ soạn này."""
        return isinstance(event.source(), SourceTree) and event.source().window() is self.window()

    def dragEnterEvent(self, event):
        """Nhận thao tác thêm từ nguồn hoặc kéo nội bộ."""
        if self._is_source(event):
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        """Cho phép thả nguồn mới lên cây báo cáo."""
        if self._is_source(event):
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        """Thêm nhóm từ nguồn hoặc đổi thứ tự các mục cùng cấp."""
        if self._is_source(event):
            self.rows_dropped.emit(event.source().dragged_rows())
            event.setDropAction(Qt.CopyAction)
            event.accept()
            return
        if event.source() is not self:
            event.ignore()
            return
        source = self.currentItem()
        target = self.itemAt(event.pos())
        # Reorder siblings only: dates, EQPs within a date, SLOTs within an EQP.
        if source is None or target is None or source is target:
            event.ignore()
            return
        if source.parent() is not target.parent():
            event.ignore()
            return
        if self.dropIndicatorPosition() not in (self.AboveItem, self.BelowItem):
            event.ignore()
            return
        event.setDropAction(Qt.MoveAction)
        super().dropEvent(event)
        self.reordered.emit()


class PreviewTable(QTableWidget):
    copy_requested = pyqtSignal()

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            self.copy_requested.emit()
            return
        super().keyPressEvent(event)


class ReportBuilder(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.entries = {}
        self.rows = []
        layout = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        for title, handler in (
            ("↑ Lên", lambda: self.move(-1)), ("↓ Xuống", lambda: self.move(1)),
            ("Xóa mục chọn", self.remove_selected), ("Xóa hết", self.clear),
            ("Copy báo cáo", self.copy), ("Xuất Excel", self.export),
        ):
            button = QPushButton(title)
            button.clicked.connect(handler)
            toolbar.addWidget(button)
        layout.addLayout(toolbar)
        self.status = QLabel("Chọn From/To, EQP và SLOT; tick nguồn bên trái rồi bấm Thêm mục đã tick.")
        layout.addWidget(self.status)
        splitter = QSplitter(Qt.Horizontal)
        source_panel = QWidget()
        source_layout = QVBoxLayout(source_panel)
        source_layout.setContentsMargins(0, 0, 0, 0)
        self.source = SourceTree(self)
        source_layout.addWidget(self.source)
        self.add_checked_button = QPushButton("Thêm mục đã tick →")
        self.add_checked_button.clicked.connect(self.add_checked)
        source_layout.addWidget(self.add_checked_button)
        hint = QLabel("Tick SLOT theo thứ tự muốn hiển thị.\nHoặc kéo ngày/máy/SLOT sang cây bên cạnh.")
        hint.setWordWrap(True)
        source_layout.addWidget(hint)
        splitter.addWidget(source_panel)
        self.tree = OrderTree()
        self.tree.setHeaderLabel("2. Thứ tự báo cáo")
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree.setDragDropMode(QAbstractItemView.DragDrop)
        self.tree.setDefaultDropAction(Qt.MoveAction)
        self.tree.setStyleSheet("QTreeWidget::item { height: 30px; }")
        self.tree.reordered.connect(self.render)
        self.tree.rows_dropped.connect(self.add_rows)
        self.table = PreviewTable()
        self.table.setColumnCount(len(HEADERS))
        self.table.setHorizontalHeaderLabels(HEADERS)
        self.table.horizontalHeader().setStyleSheet("QHeaderView::section {background:#B7DEE8; font-weight:bold;}")
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setStyleSheet("QTableWidget { background: white; gridline-color: black; }")
        self.table.verticalHeader().hide()
        self.table.copy_requested.connect(self.copy)
        for col, width in enumerate((110, 115, 65, 70, 80, 80, 180, 95)):
            self.table.setColumnWidth(col, width)
        splitter.addWidget(self.tree)
        splitter.addWidget(self.table)
        splitter.setStretchFactor(2, 1)
        splitter.setSizes([240, 240, 900])
        layout.addWidget(splitter, 1)

    def set_available_rows(self, rows):
        """Đổi nguồn chọn, giữ nguyên báo cáo đã soạn."""
        self.source.set_rows(rows)
        self.add_checked_button.setEnabled(bool(rows))

    def add_checked(self):
        """Thêm mục đã tick theo thứ tự chọn; cập nhật dòng trùng."""
        rows = self.source.chosen_rows()
        if not rows:
            self.status.setText("Hãy tick ngày, EQP hoặc SLOT ở cây nguồn bên trái.")
            return
        self.add_rows(rows)

    @staticmethod
    def child(parent, label, data):
        item = QTreeWidgetItem([label])
        item.setData(0, Qt.UserRole, data)
        parent.addChild(item)
        return item

    def add_rows(self, rows):
        root = self.tree.invisibleRootItem()
        dates = {root.child(i).data(0, Qt.UserRole): root.child(i) for i in range(root.childCount())}
        for row in rows:
            key = (row.date, row.eqp, row.slot)
            # Re-adding updates quantities without duplicating the slot.
            if key not in self.entries:
                date = dates.get(row.date)
                if date is None:
                    date = self.child(root, cells(row)[0], row.date)
                    dates[row.date] = date
                eqps = {date.child(i).data(0, Qt.UserRole): date.child(i) for i in range(date.childCount())}
                eqp = eqps.get(row.eqp)
                if eqp is None:
                    eqp = self.child(date, row.eqp, row.eqp)
                self.child(eqp, f"SLOT {row.slot}", key)
            self.entries[key] = row
        self.tree.expandAll()
        self.render()

    def render(self):
        self.rows = []
        root = self.tree.invisibleRootItem()
        for d in range(root.childCount()):
            date = root.child(d)
            for e in range(date.childCount()):
                eqp = date.child(e)
                for s in range(eqp.childCount()):
                    self.rows.append(self.entries[eqp.child(s).data(0, Qt.UserRole)])
        self.table.clearSpans()
        self.table.setRowCount(len(self.rows))
        for r, row in enumerate(self.rows):
            for c, value in enumerate(cells(row)):
                text = f"{value:.2%}" if c == 7 and isinstance(value, (int, float)) else str(value)
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                if c == 6:
                    item.setForeground(QColor("red"))
                if c == 7 and row.in_qty is not None:
                    color = yield_color(row.yield_percent)
                    if color:
                        item.setBackground(QColor("#"+color))
                self.table.setItem(r, c, item)
            self.table.setRowHeight(r, max(28, 22 * len(cells(row)[6].split("\n"))))
        for start, count, col in spans(self.rows):
            self.table.setSpan(start, col, count, 1)
        self.status.setText(f"{len(self.rows)} dòng • Kéo cùng cấp để đổi thứ tự • Copy lấy toàn bộ báo cáo")

    def move(self, direction):
        item = self.tree.currentItem()
        if item is None:
            return
        parent = item.parent() or self.tree.invisibleRootItem()
        index = parent.indexOfChild(item)
        dest = index + direction
        if 0 <= dest < parent.childCount():
            parent.takeChild(index)
            parent.insertChild(dest, item)
            self.tree.setCurrentItem(item)
            item.setExpanded(True)
            self.render()

    def remove_selected(self):
        item = self.tree.currentItem()
        if item is None:
            return
        def forget(node):
            if node.childCount():
                for i in range(node.childCount()):
                    forget(node.child(i))
            else:
                self.entries.pop(node.data(0, Qt.UserRole), None)
        forget(item)
        parent = item.parent() or self.tree.invisibleRootItem()
        parent.takeChild(parent.indexOfChild(item))
        while parent is not self.tree.invisibleRootItem() and parent.childCount() == 0:
            grand = parent.parent() or self.tree.invisibleRootItem()
            grand.takeChild(grand.indexOfChild(parent))
            parent = grand
        self.render()

    def clear(self):
        self.entries.clear()
        self.tree.clear()
        self.render()

    def copy(self):
        if self.rows:
            QGuiApplication.clipboard().setText(clipboard_text(self.rows))
            self.status.setText("Đã copy toàn bộ báo cáo, kèm tiêu đề; Excel giữ số 0. Xuất Excel để giữ ô gộp/màu.")

    def export(self):
        if not self.rows:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Xuất báo cáo", "Report.xlsx", "Excel (*.xlsx)")
        if not path:
            return
        if not path.lower().endswith(".xlsx"):
            path += ".xlsx"
        try:
            export_excel(path, self.rows)
        except Exception as error:
            QMessageBox.critical(self, "Xuất Excel", str(error))
            return
        self.status.setText("Đã xuất Excel: " + path)
