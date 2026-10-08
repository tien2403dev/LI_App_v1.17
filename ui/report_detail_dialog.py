from __future__ import annotations

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, QThread, Qt
from PyQt5.QtGui import QGuiApplication, QKeySequence
from PyQt5.QtWidgets import (
    QAbstractItemView, QDialog, QHeaderView, QLabel, QMessageBox,
    QTableView, QVBoxLayout, QHBoxLayout, QPushButton,
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
        self._closing = False
        self.setAttribute(Qt.WA_DeleteOnClose, True)
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

        # Nút Close hiển thị trực tiếp trong dialog Report Detail.
        # Khi worker vẫn đang chạy, closeEvent sẽ chờ thread kết thúc an toàn.
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.close_button = QPushButton("Close", self)
        self.close_button.setMinimumWidth(90)
        self.close_button.clicked.connect(self._request_close)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

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
        # Worker/thread đã kết thúc bình thường. Chỉ xử lý nếu dialog vẫn còn tồn tại.
        thread = self.thread
        self.thread = None
        self.worker = None
        if thread is not None:
            thread.deleteLater()
        if self._close_pending:
            QDialog.done(self, QDialog.Rejected)

    def _request_close(self):
        """Đóng dialog ngay cả khi truy vấn DB vẫn đang chạy.

        Không để closeEvent chặn việc đóng cửa sổ. Khi đang chạy, dialog tách
        QThread ra khỏi dialog và hủy request; thread sẽ tự kết thúc ở nền.
        """
        if self._closing:
            return
        self._closing = True
        self._close_pending = True
        worker = self.worker
        thread = self.thread

        if worker is not None:
            cancel_read_task(worker)
            # Không cho worker gửi kết quả vào dialog sau khi dialog đã đóng.
            try:
                worker.succeeded.disconnect(self._loaded)
            except (TypeError, RuntimeError):
                pass
            try:
                worker.failed.disconnect(self._failed)
            except (TypeError, RuntimeError):
                pass

        if thread is not None and thread.isRunning():
            # QThread không còn là child của dialog, nên dialog có thể đóng
            # ngay mà không gặp lỗi "QThread: Destroyed while thread is running".
            thread.setParent(None)
            try:
                thread.finished.disconnect(self._finished)
            except (TypeError, RuntimeError):
                pass
            self.thread = None
            self.worker = None

        QDialog.done(self, QDialog.Rejected)

    def closeEvent(self, event):
        # X trên title bar cũng dùng cùng cơ chế với nút Close.
        if not self._closing:
            self._request_close()
        event.accept()

    def reject(self):
        self._request_close()
