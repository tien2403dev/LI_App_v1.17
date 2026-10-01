"""Asynchronous summary; one running read and one coalesced refresh."""
from threading import Event
from datetime import datetime
from PyQt5.QtCore import Qt, QThread, QTimer, QAbstractTableModel, QPoint, pyqtSignal
from PyQt5.QtGui import QColor, QPen, QPolygon
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                             QPushButton, QFileDialog, QMessageBox, QCheckBox, QTableView, QHeaderView, QSplitter, QListView, QDialog, QDialogButtonBox, QApplication)
from repositories.machine_slot_summary_repository import load_machine_slot_summary, load_slot_history
from ui.report_detail_dialog import CopyTableView, ReportDetailModel
from ui.pages.alarm_page import AlarmFilterProxy, AlarmFilterHeader
from ui.filter_value_dialog import FilterValueDialog
from ui.widgets.loading_dialog import LoadingDialog


from workers.database_read_task import database_read_task
from database.read_wait import is_database_busy
from ui.database_wait import wait_manager


class SummaryThread(QThread):
    database_waiting = pyqtSignal(bool)
    def __init__(self, path, dates, parent, cache=None):
        super().__init__(parent)
        self.path, self.dates = path, dates
        self.cache = cache
        self.cancel = Event()
        self.result = None
        self.error = None

    @database_read_task
    def run(self):
        try:
            self.result = load_machine_slot_summary(self.path, *self.dates, self.cancel, cache=self.cache)
        except Exception as exc:
            if is_database_busy(exc):
                raise
            self.error = str(exc)


class ExportThread(QThread):
    def __init__(self, path, output, dates, rows, daily, parent):
        super().__init__(parent)
        self.path, self.output, self.dates = path, output, dates
        self.rows, self.daily = rows, daily
        self.cancel, self.error = Event(), None

    def run(self):
        try:
            from services.machine_slot_export import export_machine_slots
            export_machine_slots(self.path, self.output, self.dates,
                                 self.rows, self.daily, self.cancel)
        except Exception as exc:
            self.error = str(exc)


class HistoryThread(QThread):
    def __init__(self, path, dates, eqp, slot, parent):
        super().__init__(parent)
        self.args = (path, *dates, eqp, slot)
        self.cancel = Event()
        self.result, self.error = [], None

    def run(self):
        try:
            self.result = load_slot_history(*self.args, self.cancel)
        except Exception as exc:
            self.error = str(exc)


class HistoryModel(ReportDetailModel):
    HEADERS = ['No'] + ReportDetailModel.HEADERS

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if index.column() == 0:
            if role in (Qt.DisplayRole, Qt.ToolTipRole):
                return index.row() + 1
            if role == Qt.TextAlignmentRole:
                return int(Qt.AlignCenter)
            return None
        if index.column() == 6 and role == Qt.ForegroundRole:
            result = str(self.rows[index.row()].result).strip().upper()
            return {'PASS': QColor('#16845B'), 'FAIL': QColor('#DC2626')}.get(result)
        return super().data(self.index(index.row(), index.column() - 1), role)


class SlotHistoryDialog(QDialog):
    def __init__(self, path, dates, eqp, slot, parent, fail_comment=''):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle(f"Test History | {dates[0]} - {dates[1]} | {eqp} | Slot {slot}")
        self.resize(980, 600)
        self.closing = False
        layout = QVBoxLayout(self)
        self.fail_comment = QLabel()
        self.fail_comment.setTextFormat(Qt.PlainText)
        self.fail_comment.setText('Fail comment: ' + fail_comment)
        self.fail_comment.setWordWrap(True)
        self.fail_comment.setVisible(bool(fail_comment))
        layout.addWidget(self.fail_comment)
        self.status = QLabel('Đang tải lịch sử...')
        layout.addWidget(self.status)
        self.model = HistoryModel(self)
        self.table = CopyTableView(self)
        self.table.setModel(self.model)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.table)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Close, parent=self)
        self.buttons.rejected.connect(self.close)
        layout.addWidget(self.buttons)
        self.thread = HistoryThread(path, dates, eqp, slot, self)
        self.thread.finished.connect(self._finished)
        self.thread.start()

    def _finished(self):
        worker = self.thread
        self.thread = None
        if not self.closing:
            self.model.set_rows(worker.result)
            self.table.resizeColumnsToContents()
            # Add the vertical scrollbar and frame; cap to available desktop.
            width = (sum(self.table.columnWidth(i) for i in range(self.model.columnCount()))
                     + self.table.verticalScrollBar().sizeHint().width() + 38)
            screen = QApplication.screenAt(self.pos()) or QApplication.primaryScreen()
            maximum = int(screen.availableGeometry().width() * 0.9) if screen else 1200
            self.resize(min(maximum, max(500, width)), self.height())
            self.status.setText(('Không thể tải: ' + worker.error) if worker.error else
                                f'{len(worker.result):,} lần test — Ctrl+C để sao chép')
        worker.deleteLater()
        if self.closing:
            self.close()

    def closeEvent(self, event):
        if self.thread is not None:
            self.closing = True
            self.thread.cancel.set()
            event.ignore()
        else:
            super().closeEvent(event)


class SummaryModel(QAbstractTableModel):
    headers = ['No', 'Machine', 'Slot', 'Total\nTest', 'PASS', 'FAIL', 'YIELD', 'Fail comment'] + [f'Lần {i}' for i in range(1, 11)]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = []
        self.alarm_highlight = False

    def rowCount(self, parent=None):
        return len(self.rows)

    def columnCount(self, parent=None):
        return len(self.headers)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.headers[section]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        r, c = self.rows[index.row()], index.column()
        recent = r['recent'][c-8] if c >= 8 and c-8 < len(r['recent']) else None
        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignCenter)
        if role == Qt.BackgroundRole and r['alarm']:
            return QColor('#FCA5A5')
        if role == Qt.ForegroundRole and recent:
            return QColor('#DC2626' if recent['RESULT'] == 'FAIL' else '#16845B')
        if c == 7 and role in (Qt.DisplayRole, Qt.ToolTipRole):
            return r.get('fail_comment', '')
        if role == Qt.ToolTipRole and recent:
            return f"{recent['DATE']} {recent['TIME']} | Test Count: {recent['TEST_COUNT']}"
        if role == Qt.DisplayRole:
            if c < 7:
                return [index.row()+1, r['eqp'], r['slot'], r['total'], r['passed'], r['failed'],
                        f"{100*r['passed']/r['total']:.2f}%" if r['total'] else ''][c]
            if recent:
                d = recent['DATE']
                return f"{recent['RESULT']}\n{d[:4]}-{d[4:6]}-{d[6:8]}"
            return ''

    def replace(self, rows):
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()


class DailyModel(SummaryModel):
    headers = ['No', 'Date', 'Machine', 'Slot', 'Total\nTest', 'Pass', 'Fail', 'Yield']

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        r = self.rows[index.row()]
        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignCenter)
        if role == Qt.DisplayRole:
            return [index.row()+1, r['date'], r['eqp'], r['slot'], r['total'],
                    r['passed'], r['failed'],
                    f"{100*r['passed']/r['total']:.2f}%" if r['total'] else ''][index.column()]


class FittedTable(QTableView):
    """Share available width proportionally, including after window resizing."""
    def __init__(self, weights, parent=None):
        super().__init__(parent)
        self.weights = weights
        self.horizontalHeader().setMinimumSectionSize(16)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.horizontalHeader().setFixedHeight(44)
        self.verticalHeader().hide()
        self.verticalHeader().setDefaultSectionSize(52)
        self.setAlternatingRowColors(True)
        self.setMinimumWidth(0)
        self.setStyleSheet(
            'QHeaderView::section {background:#214666;color:white;font-size:13px;'
            'font-weight:bold;padding:1px;} '
            'QTableView {font-family:Segoe UI;font-size:13px;gridline-color:#D1D5DB;}')

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Keep dates/yields readable after increasing the font. Small windows
        # may scroll horizontally instead of cutting off the displayed value.
        samples = (['999', 'Machine', 'Slot', 'Total', 'PASS', 'FAIL', '100.00%', 'Fail comment']
                   + ['2026-09-22']*10 if len(self.weights) == 18 else
                   ['No', '20260922', 'AI-H908', 'Slot', 'Total', 'Pass', 'Fail', '100.00%'])
        minimums = [self.fontMetrics().horizontalAdvance(text)+10 for text in samples]
        width = max(self.viewport().width(), sum(minimums))
        total = sum(self.weights)
        extra = max(0, width-sum(minimums))
        edge = 0
        for column, weight in enumerate(self.weights):
            next_edge = sum(minimums[:column+1]) + round(extra * sum(self.weights[:column+1]) / total)
            self.setColumnWidth(column, max(16, next_edge-edge))
            edge = next_edge


class DailyFilterHeader(AlarmFilterHeader):
    """Dark header matching Summary, including white filter indicators."""

    def paintSection(self, painter, rect, column):
        if not rect.isValid():
            return
        filtered = self.model().is_column_filtered(column)
        painter.save()
        painter.fillRect(rect, QColor('#315779' if filtered else '#214666'))
        painter.setPen(QPen(QColor('#64809A'), 1))
        painter.drawLine(rect.topRight(), rect.bottomRight())
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        font = painter.font()
        font.setBold(True)
        font.setPixelSize(13)
        painter.setFont(font)
        painter.setPen(QColor('#FFFFFF'))
        label = str(self.model().headerData(column, Qt.Horizontal, Qt.DisplayRole) or '')
        painter.drawText(rect.adjusted(3, 1, -16, -1),
                         int(Qt.AlignCenter | Qt.TextWordWrap), label)
        x, y = rect.right() - 9, rect.center().y()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor('#FFFFFF'))
        if filtered:
            painter.drawPolygon(QPolygon([
                QPoint(x-5,y-5), QPoint(x+5,y-5), QPoint(x+2,y),
                QPoint(x+2,y+5), QPoint(x-2,y+3), QPoint(x-2,y)]))
            painter.fillRect(rect.left(), rect.bottom()-2, rect.width(), 3,
                             QColor('#FFFFFF'))
        else:
            painter.drawPolygon(QPolygon([
                QPoint(x-5,y-2), QPoint(x+5,y-2), QPoint(x,y+4)]))
        painter.restore()


class MachineSlotSummary(QWidget):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = path
        self.applied_dates = None
        self.dialogs = []
        self.thread = None
        self.pending = False
        self.closing = False
        self.payload = None
        self.cache = {}
        self.dirty = False
        self.search_loading_dialog = None
        self.export_thread = None
        self.export_loading_dialog = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        filters = QHBoxLayout()
        self.machine, self.slot = QComboBox(), QComboBox()
        for title, combo in [('Machine:', self.machine), ('Slot:', self.slot)]:
            filters.addWidget(QLabel(title))
            combo.addItem('All', None)
            combo.setMinimumWidth(140)
            combo.setView(QListView())
            combo.view().setStyleSheet('QListView::item { min-height:28px; padding:3px 8px; }')
            combo.setMaxVisibleItems(12)
            filters.addWidget(combo)
        self.alarm = QCheckBox('🔴 Chỉ hiện Alarm')
        self.alarm.setToolTip('Chỉ hiện slot đã có Alarm và còn Fail theo rule trong hôm nay + 2 ngày trước.')
        filters.addWidget(self.alarm)
        self.export_button = QPushButton("Export Excel")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_excel)
        filters.addWidget(self.export_button)
        filters.addStretch()
        filters.addWidget(QLabel('Tự cập nhật: 10 phút'))
        layout.addLayout(filters)
        self.status = QLabel('Chọn From–To trên bộ lọc chung rồi bấm Search.')
        layout.addWidget(self.status)
        self.status.setWordWrap(True)
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(6)
        left, right = QWidget(), QWidget()
        for panel, title in ((left, 'Machine / Slot Summary'), (right, 'Daily Machine / Slot')):
            panel.setMinimumWidth(0)
            box = QVBoxLayout(panel)
            box.setContentsMargins(0, 0, 0, 0)
            box.setSpacing(6)
            box.addWidget(QLabel(title))
            self.splitter.addWidget(panel)
        self.table = FittedTable([30,80,30,48,38,38,52,70] + [68]*10)
        self.model = SummaryModel(self)
        self.table.setModel(self.model)
        left.layout().addWidget(self.table, 1)
        self.daily_table = FittedTable([24,68,65,28,38,30,30,54])
        self.daily_model = DailyModel(self)
        self.daily_proxy = AlarmFilterProxy(self)
        self.daily_proxy.setSourceModel(self.daily_model)
        self.daily_table.setModel(self.daily_proxy)
        daily_header = DailyFilterHeader(Qt.Horizontal, self.daily_table)
        self.daily_table.setHorizontalHeader(daily_header)
        daily_header.setMinimumSectionSize(16)
        daily_header.setSectionResizeMode(QHeaderView.Fixed)
        daily_header.setFixedHeight(44)
        daily_header.setSectionsClickable(True)
        daily_header.sectionClicked.connect(self.open_daily_filter)
        right.layout().addWidget(self.daily_table, 1)
        self.splitter.setStretchFactor(0, 73)
        self.splitter.setStretchFactor(1, 27)
        self.splitter.setSizes([1387, 513])
        layout.addWidget(self.splitter, 1)
        self.machine.currentIndexChanged.connect(self._machine_changed)
        self.slot.currentIndexChanged.connect(self.apply_filters)
        self.alarm.toggled.connect(self._alarm_toggled)
        self.table.clicked.connect(lambda index: self.open_history(self.model, index))
        self.daily_table.clicked.connect(lambda index: self.open_history(self.daily_model, self.daily_proxy.mapToSource(index)))
        self.timer = QTimer(self)
        self.timer.setInterval(600000)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

    def apply_date_range(self, first, last, force=False, show_loading=False):
        try:
            if datetime.strptime(first, '%Y%m%d') > datetime.strptime(last, '%Y%m%d'):
                raise ValueError('From phải nhỏ hơn hoặc bằng To.')
        except (ValueError, TypeError) as exc:
            self.status.setText(str(exc))
            return
        dates = (first, last)
        if (not force and not self.dirty and dates == self.applied_dates
                and (not self.alarm.isChecked() or self.payload is None
                     or self.payload.get('recent_alarm_range', ('', ''))[1]
                     == datetime.now().strftime('%Y%m%d'))):
            if self.thread is not None or (self.payload is not None and
                    (self.payload['start'], self.payload['end']) == dates):
                return
        self.applied_dates = dates
        self.refresh(show_loading=show_loading)

    def invalidate(self):
        """Import changed data; metadata will select the affected days on refresh."""
        self.dirty = True

    def open_history(self, model, index):
        if not index.isValid() or self.payload is None or self.closing:
            return
        row = model.rows[index.row()]
        dates = ((row['date'], row['date']) if model is self.daily_model
                 else (self.payload['start'], self.payload['end']))
        dialog = SlotHistoryDialog(self.path, dates, row['eqp'], row['slot'], self,
                                   fail_comment=row.get('fail_comment', ''))
        self.dialogs.append(dialog)
        dialog.destroyed.connect(lambda: self.dialogs.remove(dialog) if dialog in self.dialogs else None)
        dialog.show()

    def open_daily_filter(self, column):
        if self.closing:
            return
        values = sorted({str(self.daily_model.index(row, column).data())
                         for row in range(self.daily_model.rowCount())})
        selected = self.daily_proxy.filters.get(column, set(values))
        dialog = FilterValueDialog(self.daily_model.headers[column].replace('\n', ' '),
                                   values, selected, apply_immediately=True,
                                   compact=True, parent=self)
        dialog.selection_changed.connect(
            lambda selection: self.daily_proxy.set_filter(column, selection, values))
        # Local adjustment: the shared Alarm/Report filter dialog keeps its size.
        widest = max([dialog.fontMetrics().horizontalAdvance(value)
                      for value in values] + [110])
        dialog.resize(min(250, max(190, widest + 65)), dialog.height())
        header = self.daily_table.horizontalHeader()
        point = header.mapToGlobal(QPoint(header.sectionViewportPosition(column), header.height()))
        screen = QApplication.screenAt(point) or QApplication.primaryScreen()
        if screen:
            rect = screen.availableGeometry()
            point.setX(max(rect.left(), min(point.x(), rect.right()-dialog.width())))
            point.setY(max(rect.top(), min(point.y(), rect.bottom()-dialog.height())))
        dialog.move(point)
        dialog.exec_()
        dialog.deleteLater()

    def _tick(self):
        if self.isVisible():
            self.refresh()

    def refresh(self, show_loading=False):
        if self.closing or self.applied_dates is None:
            return
        if show_loading and self.search_loading_dialog is None:
            self.search_loading_dialog = LoadingDialog(
                parent=self, text="Loading ...", title="Please Wait")
            self.search_loading_dialog.show()
        if self.thread is not None:
            self.pending = True
            return
        self.status.setText('Đang cập nhật dữ liệu...')
        self.export_button.setEnabled(False)
        self.thread = SummaryThread(self.path, self.applied_dates, self, cache=self.cache)
        wait_manager(self).bind(self.thread, self._close_search_loading)
        self.thread.finished.connect(self._finished)
        self.thread.start()

    def _finished(self):
        worker = self.thread
        self.thread = None
        payload, error = worker.result, worker.error
        worker.deleteLater()
        if self.closing:
            self._close_search_loading()
            return
        if error is None:
            self.cache = payload.pop('_cache')
        if self.pending:
            self.pending = False
            self.refresh()
            return
        self._close_search_loading()
        self.export_button.setEnabled(self.payload is not None and self.export_thread is None)
        if error:
            self.dirty = True
            self.status.setText('Chưa cập nhật được; dữ liệu hiển thị có thể cũ. ' + error)
            return
        self.payload = payload
        self.dirty = False
        self.export_button.setEnabled(self.export_thread is None)
        self.daily_model.replace(payload['daily'])
        self._fill(self.machine, sorted({r['eqp'] for r in payload['daily']}))
        self._machine_changed()

    @staticmethod
    def _fill(combo, values):
        selected = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem('All', None)
        for value in values:
            combo.addItem(str(value), value)
        combo.setCurrentIndex(max(0, combo.findData(selected)))
        combo.blockSignals(False)

    def _machine_changed(self):
        if self.payload:
            eqp = self.machine.currentData()
            self._fill(self.slot, sorted({r['slot'] for r in self.payload['rows'] if eqp is None or r['eqp'] == eqp}))
        self.apply_filters()

    def _alarm_toggled(self, checked):
        if checked and self.applied_dates is not None:
            # Validate current day/import/config instead of trusting an old result.
            self.model.replace([])
            self.refresh(show_loading=True)
        else:
            self.apply_filters()

    def apply_filters(self):
        if not self.payload:
            return
        eqp, slot = self.machine.currentData(), self.slot.currentData()
        rows = [r for r in self.payload['rows'] if (eqp is None or r['eqp'] == eqp)
                and (slot is None or r['slot'] == slot) and (not self.alarm.isChecked() or (r['alarm'] and r.get('recent_alarm', False)))]
        self.model.alarm_highlight = True
        self.model.replace(rows)
        p = self.payload
        alarm_scope = 'Alarm: trong khoảng ngày đã chọn'
        if self.alarm.isChecked():
            first, last = p['recent_alarm_range']
            # alarm_scope = f'Alarm còn Fail theo dữ liệu trong khoảng ngày: {first} → {last}'
            alarm_scope = f'Alarm còn Fail theo dữ liệu 3 ngày gần nhất'
        self.status.setText(f"Khoảng ngày: {p['start']} → {p['end']} | {alarm_scope} | "
                            f"Hiển thị: {len(rows)} slot | Cập nhật: {p['now']:%Y-%m-%d %H:%M:%S}")

    def export_excel(self):
        if self.payload is None or self.export_thread is not None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, 'Export Excel',
            f"Machine_Slot_{self.payload['start']}_{self.payload['end']}.xlsx",
            'Excel (*.xlsx)')
        if not path:
            return
        if not path.lower().endswith('.xlsx'):
            path += '.xlsx'
        # Capture applied dates and visible filters before starting background work.
        daily = [self.daily_model.rows[self.daily_proxy.mapToSource(
            self.daily_proxy.index(i, 0)).row()] for i in range(self.daily_proxy.rowCount())]
        self.export_thread = ExportThread(self.path, path,
            (self.payload['start'], self.payload['end']), list(self.model.rows), daily, self)
        self.export_button.setEnabled(False)
        self.export_loading_dialog = LoadingDialog(
            parent=self, text="Đang xuất Excel...", title="Please Wait")
        self.export_thread.finished.connect(self._export_finished)
        self.export_loading_dialog.show()
        self.export_thread.start()

    def _close_search_loading(self):
        dialog, self.search_loading_dialog = self.search_loading_dialog, None
        if dialog is not None:
            dialog.close()
            dialog.deleteLater()

    def _close_export_loading(self):
        dialog = self.export_loading_dialog
        self.export_loading_dialog = None
        if dialog is not None:
            dialog.close()
            dialog.deleteLater()

    def _export_finished(self):
        self._close_export_loading()
        worker = self.export_thread
        self.export_thread = None
        self.export_button.setEnabled(self.payload is not None and not self.closing)
        if not self.closing:
            if worker.error:
                QMessageBox.warning(self, 'Export Excel', worker.error)
            else:
                QMessageBox.information(self, 'Export Excel', 'Đã xuất file: ' + worker.output)
        worker.deleteLater()

    def prepare_close(self):
        self._close_search_loading()
        self._close_export_loading()
        self.closing = True
        self.pending = False
        self.timer.stop()
        for dialog in list(self.dialogs):
            dialog.close()
        if self.export_thread:
            self.export_thread.cancel.set()
        if self.thread:
            self.thread.cancel.set()

    def has_running_tasks(self):
        return self.thread is not None or self.export_thread is not None or any(d.thread is not None for d in self.dialogs)
