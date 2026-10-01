from __future__ import annotations

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, QThread, Qt
from PyQt5.QtGui import QGuiApplication, QKeySequence
from PyQt5.QtWidgets import (
    QAbstractItemView, QDialog, QHeaderView, QLabel, QMessageBox,
    QTableView, QVBoxLayout,
)

from workers.report_worker import ReportWorker
from ui.database_wait import wait_manager, cancel_read_task


class CopyTableView(QTableView):
    """QTableView hỗ trợ Ctrl+C với cả vùng chọn."""

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            indexes = sorted(self.selectedIndexes(), key=lambda item: (item.row(), item.column()))
            if indexes:
                selected_rows = sorted({item.row() for item in indexes})
                selected_columns = sorted({item.column() for item in indexes})
                lines = []
                for row in selected_rows:
                    lines.append("\t".join(
                        ("" if self.model().index(row, column).data() is None
                         else str(self.model().index(row, column).data()))
                        for column in selected_columns
                    ))
                QGuiApplication.clipboard().setText("\n".join(lines))
                return
        super().keyPressEvent(event)


class ReportDetailModel(QAbstractTableModel):
    HEADERS = [
        "DATE", "TIME", "PARTNO", "LOTNO", "SERIAL", "RESULT",
        "SCRAPCODE", "QTY", "EQP", "TEST_COUNT", "Slot", "MODEL", "TIER",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = []

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignCenter)
        if role != Qt.DisplayRole:
            return None
        row = self.rows[index.row()]
        return (
            row.date, row.time, row.partno, row.lotno, row.serial,
            row.result, row.scrap_code, row.qty, row.eqp, row.test_count,
            row.slot, row.model, row.tier,
        )[index.column()]

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return None

    def set_rows(self, rows):
        self.beginResetModel()
        self.rows = list(rows)
        self.endResetModel()


class ReportDetailDialog(QDialog):
    def __init__(self, database_path, date_from, date_to, row, parent=None):
        super().__init__(parent)
        self.thread = None
        self.worker = None
        self._close_pending = False
        self.setWindowTitle(f"Report Detail | {row.date} | {row.eqp} | Slot {row.slot}")
        self.resize(1250, 600)

        layout = QVBoxLayout(self)
        self.status_label = QLabel("Đang tải dữ liệu...")
        layout.addWidget(self.status_label)
        self.model = ReportDetailModel(self)
        self.table = CopyTableView(self)
        self.table.setModel(self.model)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.table, 1)

        self.thread = QThread(self)
        self.worker = ReportWorker(
            database_path, "details", date_from=date_from, date_to=date_to,
            date=row.date, eqp=row.eqp, slot=row.slot,
        )
        wait_manager(self).bind(self.worker)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.succeeded.connect(self._loaded)
        self.worker.failed.connect(self._failed)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self._finished)
        self.thread.start()

    def _loaded(self, rows):
        if self._close_pending:
            return
        self.model.set_rows(rows)
        self.status_label.setText(f"{len(rows):,} lần test — Ctrl+C để sao chép")

    def _failed(self, message):
        if self._close_pending:
            return
        self.status_label.setText("Không thể tải dữ liệu.")
        QMessageBox.critical(self, "Report", message)

    def _finished(self):
        self.thread.deleteLater()
        self.thread = None
        self.worker = None
        if self._close_pending:
            self.close()

    def closeEvent(self, event):
        self._close_pending = True
        cancel_read_task(self.worker)
        if self.thread is not None and self.thread.isRunning():
            event.ignore()
            return
        super().closeEvent(event)

    def reject(self):
        self.close()
