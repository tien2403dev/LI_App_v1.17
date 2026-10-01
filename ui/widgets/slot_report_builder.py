"""SLOT report UX: fixed selector, automatic preview and ordered report builder."""
from PyQt5.QtCore import QDateTime, QMimeData, QThread, QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QGuiApplication, QKeySequence
from PyQt5.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDateTimeEdit, QDialog,
    QDialogButtonBox, QFileDialog, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QListView, QListWidget, QMessageBox, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QSplitter, QTableWidget, QTableWidgetItem, QTabWidget,
    QVBoxLayout, QWidget,
)
from services.slot_report_service import (
    HEADERS, WIDTHS, report_rows, display_value,
    merged_spans, yield_color, clipboard_text, clipboard_html,
)
from ui.report_detail_dialog import ReportDetailDialog
from workers.slot_report_worker import SlotReportWorker
from ui.database_wait import wait_manager, cancel_read_task


class SlotCell(QCheckBox):
    """Make the full bordered cell clickable, including whitespace."""

    def hitButton(self, position):
        """Toggle exactly once anywhere inside the cell."""
        return self.rect().contains(position)


class SlotPicker(QDialog):
    """Searchable fixed 1..48 choices with selection order preserved."""

    def __init__(self, selected, parent=None):
        """Build a scrollable checkbox grid; accept changes only on Apply."""
        super().__init__(parent)
        self.setWindowTitle('Chọn SLOT • 1–48')
        self.order = list(selected)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Chọn theo thứ tự muốn đưa vào báo cáo.'))
        self.search = QLineEdit()
        self.search.setPlaceholderText('Tìm số SLOT…')
        layout.addWidget(self.search)
        bar = QHBoxLayout()
        all_button, none_button = QPushButton('Chọn tất cả'), QPushButton('Bỏ chọn tất cả')
        bar.addWidget(all_button)
        bar.addWidget(none_button)
        self.count = QLabel()
        bar.addWidget(self.count)
        layout.addLayout(bar)
        area = QScrollArea()
        area.setWidgetResizable(True)
        body = QWidget()
        grid = QGridLayout(body)
        grid.setSpacing(0)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setAlignment(Qt.AlignTop)
        for col in range(4):
            label = QLabel(f'SLOT {col * 12 + 1}–{(col + 1) * 12}')
            label.setAlignment(Qt.AlignCenter)
            label.setFixedHeight(38)
            label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            label.setStyleSheet('background:#B7DEE8;border:1px solid #9AADB9;padding:8px;font-weight:bold;')
            grid.addWidget(label, 0, col)
            grid.setColumnStretch(col, 1)
        self.boxes = {}
        for slot in range(1, 49):
            box = SlotCell(f'SLOT {slot}')
            box.setMinimumHeight(34)
            box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            box.setStyleSheet('QCheckBox {border:1px solid #BAC6CE;padding:6px;spacing:8px;}'
                             'QCheckBox:hover {background:#E8F3FA;}'
                             'QCheckBox:checked {background:#D8EDF9;}')
            box.setToolTip(f'Slot {slot}')
            box.setChecked(slot in selected)
            box.toggled.connect(lambda checked, t=slot: self._toggle(t, checked))
            self.boxes[slot] = box
            grid.addWidget(box, (slot - 1) % 12 + 1, (slot - 1) // 12)
        area.setWidget(body)
        # Header + exactly 12 slot rows; no expanding blank area below SLOT 48.
        area.setFixedHeight(body.sizeHint().height() + 2)
        layout.addWidget(area)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText('Áp dụng')
        buttons.button(QDialogButtonBox.Cancel).setText('Hủy')
        for button in buttons.buttons():
            button.setMinimumSize(120, 42)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.search.textChanged.connect(self._filter)
        all_button.clicked.connect(lambda: self._set_all(True))
        none_button.clicked.connect(lambda: self._set_all(False))
        self.count.setText(f'Đã chọn: {len(self.order)}')
        self.resize(900, self.sizeHint().height())

    def _toggle(self, slot, checked):
        """Record manual selection order, including reselection."""
        if checked and slot not in self.order:
            self.order.append(slot)
        elif not checked and slot in self.order:
            self.order.remove(slot)
        self.count.setText(f'Đã chọn: {len(self.order)}')

    def _set_all(self, checked):
        """Apply bulk selection to all fixed SLOT choices."""
        for box in self.boxes.values():
            box.setChecked(checked)

    def _filter(self, text):
        """Search by SLOT number without discarding selected values."""
        for slot, box in self.boxes.items():
            box.setEnabled(text.strip() in str(slot))


class ReportPreview(QTableWidget):
    copy_requested = pyqtSignal()

    def __init__(self, parent=None):
        """Create read-only preview with merged cells matching Excel."""
        super().__init__(0, len(HEADERS), parent)
        self.setHorizontalHeaderLabels(HEADERS)
        self.verticalHeader().hide()
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.setWordWrap(True)
        self.setStyleSheet('QHeaderView::section {background:#B7DEE8;font-weight:bold;padding:6px;} '
                           'QTableWidget {background:white;gridline-color:#93A4AF;}')
        for col, width in enumerate(WIDTHS):
            self.setColumnWidth(col, max(width * 6, self.fontMetrics().horizontalAdvance(HEADERS[col]) + 28))
        self.setColumnWidth(0, self.fontMetrics().horizontalAdvance('30/09/2026') + 24)
        self.setColumnWidth(7, self.fontMetrics().horizontalAdvance('100.00%') + 20)

    def set_groups(self, groups):
        """Render identical values, colors and spans for each output channel."""
        self.setUpdatesEnabled(False)
        try:
            self.clearSpans()
            rows = report_rows(groups)
            self.setRowCount(len(rows))
            for r, values in enumerate(rows):
                for c, value in enumerate(values):
                    item = QTableWidgetItem(display_value(value, c))
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setToolTip(display_value(value, c))
                    color = yield_color(value) if c == 7 else None
                    if c == 6:
                        item.setForeground(QColor('red'))
                    if color:
                        item.setBackground(QColor('#' + color))
                    self.setItem(r, c, item)
                self.setRowHeight(r, max(34, 12 + self.fontMetrics().lineSpacing() * max(
                    len(str(values[c] or '').splitlines()) for c in (6, 8))))
            for row, count, col in merged_spans(groups):
                self.setSpan(row, col, count, 1)
        finally:
            self.setUpdatesEnabled(True)

    def keyPressEvent(self, event):
        """Ctrl+C copies the complete current preview with formatting."""
        if event.matches(QKeySequence.Copy):
            self.copy_requested.emit()
            return
        super().keyPressEvent(event)


class SlotReportBuilder(QWidget):
    """Own report draft; filters only change preview until Add is clicked."""

    def __init__(self, database_path, parent=None):
        """Create widgets and load machine options in the background."""
        super().__init__(parent)
        self.database_path = database_path
        self._closing = False
        self._options_dirty = False
        font = self.font()
        font.setPointSize(10)
        self.setFont(font)
        self.slots = []
        self.preview_groups = []
        self.groups = []
        self.thread = self.worker = None
        self.dialogs = []
        self.pending_preview = False
        self.preview_signature = None
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(300)
        self.timer.timeout.connect(self._load_preview)
        self._build_ui()
        self._start('options', {})

    def _build_ui(self):
        """Use a compact filter bar and two clearly separated workflow steps."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        title = QLabel('TẠO BÁO CÁO THEO SLOT')
        title.setStyleSheet('font-size:12px;font-weight:bold;color:#174A67;')
        layout.addWidget(title)
        self.filters = QWidget()
        grid = QGridLayout(self.filters)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(16)
        now = QDateTime.currentDateTime()
        self.first = QDateTimeEdit(now.addDays(-1))
        self.last = QDateTimeEdit(now)
        for editor in (self.first, self.last):
            editor.setCalendarPopup(True)
            editor.setDisplayFormat('yyyy-MM-dd HH:mm:ss')
            editor.setMinimumWidth(205)
            editor.dateTimeChanged.connect(self._selection_changed)
        self.eqp = QComboBox()
        self.eqp.setMinimumWidth(160)
        self.eqp.setView(QListView())
        self.eqp.setMaxVisibleItems(15)
        self.eqp.view().setStyleSheet('QListView::item {min-height:24px;padding:2px 8px;}')
        self.eqp.view().setSpacing(0)
        self.eqp.currentIndexChanged.connect(self._selection_changed)
        self.slot_button = QPushButton('Chọn SLOT (1–48)…')
        self.slot_button.clicked.connect(self._pick_slots)
        self.slot_button.setFixedWidth(230)
        for col, (label, widget) in enumerate([
            ('From', self.first), ('To', self.last), ('EQP', self.eqp),
            ('SLOT', self.slot_button),
        ]):
            grid.addWidget(QLabel(label), 0, col)
            grid.addWidget(widget, 1, col)
            widget.setMinimumHeight(40)
        grid.setColumnStretch(4, 1)
        layout.addWidget(self.filters)
        self.slot_hint = QLabel('Chọn EQP và SLOT để tự tính. Lấy tất cả Test Count.')
        self.slot_hint.setWordWrap(True)
        layout.addWidget(self.slot_hint)
        self.pages = QTabWidget()
        self.pages.setStyleSheet(
            'QTabBar::tab { min-width: 155px; padding: 7px 12px; }'
        )
        preview_page = QWidget()
        preview_layout = QVBoxLayout(preview_page)
        preview_bar = QHBoxLayout()
        self.add_button = QPushButton('＋ Thêm vào báo cáo')
        self.add_button.setStyleSheet('background:#176B91;color:white;font-weight:bold;padding:9px;')
        self.add_button.clicked.connect(self._add)
        preview_bar.addWidget(self.add_button)
        self.reload_button = QPushButton('Tải lại xem trước')
        self.reload_button.clicked.connect(self._selection_changed)
        preview_bar.addWidget(self.reload_button)
        self.preview_copy_button = QPushButton('Copy có định dạng')
        self.preview_copy_button.clicked.connect(
            lambda: self._copy_groups(self.preview_groups, True)
        )
        preview_bar.addWidget(self.preview_copy_button)
        preview_bar.addStretch()
        preview_layout.addLayout(preview_bar)
        self.preview = ReportPreview()
        self.preview.copy_requested.connect(lambda: self._copy_groups(self.preview_groups, True))
        self.preview.cellDoubleClicked.connect(lambda row, col: self._details(self.preview_groups, row))
        preview_layout.addWidget(self.preview)
        self.pages.addTab(preview_page, '1. Xem trước')
        report_page = QWidget()
        report_layout = QVBoxLayout(report_page)
        toolbar = QHBoxLayout()
        self.report_buttons = []
        for label, handler in [
            ('Làm mới số liệu', self._refresh),
            ('Copy có định dạng', lambda: self._copy_groups(self.groups, True)),
            ('Copy dữ liệu', lambda: self._copy_groups(self.groups, False)),
            ('Xuất Excel', self._export),
        ]:
            button = QPushButton(label)
            button.setMinimumHeight(34)
            button.clicked.connect(handler)
            toolbar.addWidget(button)
            self.report_buttons.append(button)
        toolbar.addStretch()
        report_layout.addLayout(toolbar)
        splitter = QSplitter(Qt.Horizontal)
        order_panel = QWidget()
        order_layout = QVBoxLayout(order_panel)
        order_layout.setContentsMargins(0, 0, 0, 0)
        order_layout.addWidget(QLabel('Thứ tự nhóm Slot trong báo cáo'))
        self.order_list = QListWidget()
        self.order_list.currentRowChanged.connect(self._scroll_to_group)
        order_layout.addWidget(self.order_list)
        self.edit_buttons = []
        for labels in [[('↑ Lên', lambda: self._move(-1)), ('↓ Xuống', lambda: self._move(1))],
                       [('Xóa mục', self._remove), ('Xóa hết', self._clear)]]:
            bar = QHBoxLayout()
            for label, handler in labels:
                button = QPushButton(label)
                button.clicked.connect(handler)
                bar.addWidget(button)
                self.edit_buttons.append(button)
            order_layout.addLayout(bar)
        splitter.addWidget(order_panel)
        self.report = ReportPreview()
        self.report.copy_requested.connect(lambda: self._copy_groups(self.groups, True))
        self.report.cellDoubleClicked.connect(lambda row, col: self._details(self.groups, row))
        splitter.addWidget(self.report)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([270, 1100])
        report_layout.addWidget(splitter)
        self.pages.addTab(report_page, '2. Báo cáo (0)')
        layout.addWidget(self.pages, 1)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(5)
        self.progress.setTextVisible(False)
        self.progress.hide()
        layout.addWidget(self.progress)
        self.status = QLabel('Đang tải danh sách máy…')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self._update_buttons()

    def _signature(self):
        """Identify data selection; chamber is intentionally absent."""
        return (self.first.dateTime().toString('yyyy-MM-dd HH:mm:ss'),
                self.last.dateTime().toString('yyyy-MM-dd HH:mm:ss'), self.eqp.currentText(), tuple(self.slots))

    def _pick_slots(self):
        """Show fixed choices without requiring PRIME records to exist."""
        dialog = SlotPicker(self.slots, self)
        if dialog.exec_() == QDialog.Accepted:
            self.slots = dialog.order
            self.slot_button.setText(f'{len(self.slots)} SLOT đã chọn • Thay đổi…')
            labels = [str(t) for t in self.slots]
            self.slot_hint.setText('Thứ tự SLOT: ' + ('   |   '.join(labels[:8]) or 'Chưa chọn')
                                   + (f'   … (+{len(labels)-8} SLOT)' if len(labels) > 8 else ''))
            self.slot_hint.setToolTip('\n'.join(labels))
            self._selection_changed()

    def _selection_changed(self, *_args):
        """Invalidate stale preview immediately and debounce database work."""
        if self._closing:
            return
        self.preview_signature = None
        self.preview_groups = []
        self.preview.set_groups([])
        self.pending_preview = True
        self.pages.setCurrentIndex(0)
        self.timer.start()
        self._update_buttons()

    def _load_preview(self):
        """Fetch the exact selected date/time interval for the selected SLOTs."""
        if self._closing:
            return
        if self.thread is not None:
            self.pending_preview = True
            return
        self.pending_preview = False
        first, last, eqp, slots = self._signature()
        if not eqp or not slots:
            self.status.setText('Chọn EQP và ít nhất một SLOT. SLOT có cố định từ 1 đến 48.')
            return
        if first > last:
            self.status.setText('Thời gian bắt đầu phải nhỏ hơn hoặc bằng thời gian kết thúc.')
            return
        self.request_signature = self._signature()
        self._start('preview', dict(first=first, last=last, eqp=eqp,
                                   slots=list(slots)))

    def _start(self, action, arguments):
        """Start one worker at a time; keep report mutations locked until finish."""
        if self.thread is not None or self._closing:
            return
        self.action = action
        self.thread = QThread(self)
        self.worker = SlotReportWorker(self.database_path, action, arguments)
        wait_manager(self).bind(self.worker)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.succeeded.connect(self._loaded)
        self.worker.failed.connect(self._failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self._finished)
        self.progress.show()
        self.status.setText({'options': 'Đang tải danh sách máy…', 'preview': 'Đang tính kết quả…',
                             'refresh': 'Đang làm mới báo cáo…', 'export': 'Đang xuất Excel…'}[action])
        self._update_buttons()
        self.thread.start()

    def _loaded(self, result):
        """Apply completed results only to the matching preview or report draft."""
        if self._closing:
            return
        if self.action == 'options':
            self.eqp.blockSignals(True)
            selected = self.eqp.currentText()
            self.eqp.clear()
            self.eqp.addItem('')
            self.eqp.addItems(result)
            self.eqp.setCurrentText(selected)
            self.eqp.blockSignals(False)
            self.status.setText('Chọn EQP và SLOT để tạo báo cáo.' if result else 'Database chưa có EQP.')
        elif self.action == 'preview':
            if self.pending_preview or self.request_signature != self._signature():
                return
            self.preview_signature = self.request_signature
            self.preview_groups = list(result)
            self.preview.set_groups(self.preview_groups)
            missing = sum(row.in_qty is None for g in result for row in g.rows)
            self.status.setText(f'Xem trước: {sum(len(g.rows) for g in result)} dòng • {missing} slot/ngày không có dữ liệu. '
                                'Bấm “Thêm vào báo cáo” để giữ kết quả. Nhấp đúp slot để xem log.')
        elif self.action == 'refresh':
            self.groups = result
            self._render_report()
            self.status.setText('Đã làm mới số liệu; giữ nguyên khoảng thời gian và thứ tự SLOT.')
        elif self.action == 'export':
            self.status.setText('Đã xuất Excel: ' + str(result))
            QMessageBox.information(self, 'Xuất Excel thành công',
                                    'Đã xuất báo cáo thành công.\n\nĐường dẫn:\n' + str(result))

    def _failed(self, message):
        """Keep report draft intact and offer retry after a database/export error."""
        if self._closing:
            return
        self.status.setText('Không thể xử lý: ' + message)
        QMessageBox.warning(self, 'Báo cáo SLOT', message)

    def _finished(self):
        """Release worker references and process the latest queued selection."""
        self.thread.deleteLater()
        self.thread = self.worker = None
        self.progress.hide()
        self._update_buttons()
        if self._closing:
            return
        if self._options_dirty:
            self.load_if_needed()
        elif self.pending_preview:
            self.timer.start(0)

    def _update_buttons(self):
        """Prevent adding stale previews or changing a report during refresh/export."""
        idle = self.thread is None and not self._closing
        preview_ready = (idle and not self.pending_preview and bool(self.preview_groups)
                         and self.preview_signature == self._signature())
        self.add_button.setEnabled(preview_ready)
        self.preview_copy_button.setEnabled(preview_ready)
        self.reload_button.setEnabled(idle)
        for button in self.report_buttons + self.edit_buttons:
            button.setEnabled(idle and bool(self.groups))

    def _add(self):
        """Append new group keys; re-adding updates quantities at the same position."""
        if not self.add_button.isEnabled():
            return
        positions = {g.key: i for i, g in enumerate(self.groups)}
        for group in self.preview_groups:
            if group.key in positions:
                self.groups[positions[group.key]] = group
            else:
                positions[group.key] = len(self.groups)
                self.groups.append(group)
        self._render_report()
        self.pages.setCurrentIndex(1)
        self.status.setText(f'Báo cáo có {len(self.groups)} nhóm / {sum(len(g.rows) for g in self.groups)} dòng. '
                            'Có thể chọn nhóm khác rồi thêm tiếp; thêm trùng sẽ cập nhật số liệu.')

    def _render_report(self, selected=-1):
        """Synchronize ordered group list, final preview and action states."""
        self.order_list.clear()
        for g in self.groups:
            self.order_list.addItem(f'{g.date[6:8]}/{g.date[4:6]}/{g.date[:4]} • {g.eqp}\n'
                                    f'Slot: {", ".join(map(str, g.slots))}')
            self.order_list.item(self.order_list.count() - 1).setToolTip(
                f'Khoảng tính: {g.date_from} → {g.date_to}')
        self.report.set_groups(self.groups)
        self.order_list.setCurrentRow(selected)
        self.pages.setTabText(1, f'2. Báo cáo ({len(self.groups)} nhóm)')
        self._update_buttons()

    def _scroll_to_group(self, index):
        """Scroll report to the SLOT selected in the order list."""
        if 0 <= index < len(self.groups):
            offset = sum(len(g.rows) for g in self.groups[:index])
            self.report.setCurrentCell(offset, 2)
            item = self.report.item(offset, 2)
            if item:
                self.report.scrollToItem(item)

    def _move(self, offset):
        """Move the selected slot group together."""
        index = self.order_list.currentRow()
        dest = index + offset
        if self.thread is None and 0 <= index < len(self.groups) and 0 <= dest < len(self.groups):
            self.groups[index], self.groups[dest] = self.groups[dest], self.groups[index]
            self._render_report(dest)

    def _remove(self):
        """Remove selected SLOT group without touching database records."""
        index = self.order_list.currentRow()
        if self.thread is None and 0 <= index < len(self.groups):
            self.groups.pop(index)
            self._render_report(min(index, len(self.groups)-1))

    def _clear(self):
        """Confirm only clearing the current composed report."""
        if self.thread is None and QMessageBox.question(
                self, 'Xóa báo cáo', 'Xóa tất cả mục trong báo cáo đang soạn?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            self.groups = []
            self._render_report()

    def _refresh(self):
        """Refresh exactly the groups already added to the report."""
        if self.groups and self.thread is None:
            self._start('refresh', {'groups': list(self.groups)})

    def _copy_groups(self, groups, formatted):
        """Copy the whole displayed report with a plain-text fallback."""
        if not groups:
            return
        mime = QMimeData()
        mime.setText(clipboard_text(groups))
        if formatted:
            mime.setHtml(clipboard_html(groups))
        QGuiApplication.clipboard().setMimeData(mime)
        self.status.setText('Đã copy nội dung đang hiển thị, không kèm tiêu đề. Dán vào Excel/email bằng Ctrl+V. '
                            'Xuất Excel để giữ bố cục đầy đủ nhất.')

    def _export(self):
        """Choose output path and perform workbook writing in a background job."""
        if not self.groups or self.thread is not None:
            return
        path, _ = QFileDialog.getSaveFileName(self, 'Xuất báo cáo SLOT',
                                             'LI_Slot_Report.xlsx', 'Excel (*.xlsx)')
        if path:
            if not path.lower().endswith('.xlsx'):
                path += '.xlsx'
            self._start('export', {'path': path, 'groups': list(self.groups)})

    def _details(self, groups, index):
        """Open source log for exactly the date/EQP/slot behind a report row."""
        if index < 0:
            return
        for group in groups:
            if index < len(group.rows):
                row = group.rows[index]
                break
            index -= len(group.rows)
        else:
            return
        day = f'{row.date[:4]}-{row.date[4:6]}-{row.date[6:]}'
        dialog = ReportDetailDialog(self.database_path, group.date_from or day + ' 00:00:00',
                                    group.date_to or day + ' 23:59:59', row, self)
        self.dialogs.append(dialog)
        dialog.finished.connect(lambda _result, d=dialog: self.dialogs.remove(d))
        dialog.show()

    def is_busy(self):
        """Prevent closing the host while report/detail workers are alive."""
        return self.thread is not None or any(d.thread is not None for d in self.dialogs)

    def mark_data_changed(self):
        self._options_dirty = True
        self._selection_changed()
        self.load_if_needed()

    def load_if_needed(self):
        if self._options_dirty and self.thread is None and not self._closing:
            self._options_dirty = False
            self._start('options', {})

    def prepare_close(self):
        cancel_read_task(self.worker)
        self._closing = True
        self.pending_preview = False
        self.timer.stop()
