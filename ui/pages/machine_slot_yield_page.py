# from pathlib import Path
# from typing import Union
#
# from PyQt5.QtWidgets import (
#     QDoubleSpinBox,
#     QGridLayout,
#     QLabel,
#     QMessageBox,
#     QPushButton,
#     QSpinBox,
#     QStyle,
#     QVBoxLayout,
#     QWidget,
# )
#
# from repositories.machine_slot_yield_repository import (
#     MachineSlotYieldRepository,
# )
#
#
# class MachineSlotYieldPage(QWidget):
#     """Màn hình cấu hình ngưỡng Machine Slot Yield cho chức năng Alarm."""
#
#     def __init__(self, database_path: Union[str, Path], parent=None):
#         super().__init__(parent)
#         self.repository = MachineSlotYieldRepository(database_path)
#         self._loaded = False
#         self._build_ui()
#
#     def _build_ui(self) -> None:
#         """Tạo bố cục một hàng cho bốn ngưỡng và nút lưu."""
#         self.setObjectName("machineSlotYieldPage")
#         self.setStyleSheet(
#             """
#             QWidget#machineSlotYieldPage { background: #FFFFFF; }
#             QLabel { color:#111827; font-family:"Segoe UI"; font-size:12px; }
#             QLabel#titleLabel { font-size:16px; font-weight:600; }
#             QLabel#fieldLabel { font-weight:600; }
#             QDoubleSpinBox, QSpinBox {
#                 min-height:28px; background:#FFFFFF; color:#111827;
#                 border:1px solid #B8C2CC; border-radius:3px;
#                 font-family:"Segoe UI"; font-size:12px;
#             }
#             QPushButton {
#                 min-height:30px; padding:0 12px; background:#F8FAFC;
#                 color:#1F2937; border:1px solid #B8C2CC; border-radius:3px;
#                 font-family:"Segoe UI"; font-size:12px; font-weight:500;
#             }
#             QPushButton:hover { background:#EAF3FC; border-color:#7AA7D3; }
#             QPushButton:pressed { background:#DCEBFA; }
#             """
#         )
#
#         layout = QVBoxLayout(self)
#         layout.setContentsMargins(10, 10, 10, 10)
#         layout.setSpacing(10)
#
#         title = QLabel("Machine Slot Yield")
#         title.setObjectName("titleLabel")
#         layout.addWidget(title)
#
#         config_grid = QGridLayout()
#         config_grid.setHorizontalSpacing(8)
#         config_grid.setVerticalSpacing(0)
#
#         self.target_15_spin = self._target_spin_box()
#         self.target_30_spin = self._target_spin_box()
#         self.continuous_fail_spin = QSpinBox()
#         self.continuous_fail_spin.setRange(1, 9999)
#         self.continuous_fail_spin.setFixedWidth(95)
#         self.continuous_fail_spin.setToolTip(
#             "Số bản ghi FAIL liên tục cùng máy/slot, Model và Scrap code."
#         )
#         self.different_scrap_fail_spin = QSpinBox()
#         self.different_scrap_fail_spin.setRange(2, 9999)
#         self.different_scrap_fail_spin.setFixedWidth(95)
#         self.different_scrap_fail_spin.setToolTip(
#             "FAIL liên tục cùng máy/slot và Model, có ít nhất 2 Scrap code khác nhau."
#         )
#         self.save_button = QPushButton("Save Target")
#         self.save_button.setIcon(
#             self.style().standardIcon(QStyle.SP_DialogSaveButton)
#         )
#         self.save_button.clicked.connect(self._save_config)
#
#         labels = (
#             QLabel("Target 15:"),
#             QLabel("Target 30:"),
#             QLabel("Số lần fail liên tục cùng scrapcode:"),
#             QLabel("Số lần fail liên tục khác Scrap code:"),
#         )
#         for label in labels:
#             label.setObjectName("fieldLabel")
#
#         config_grid.addWidget(labels[0], 0, 0)
#         config_grid.addWidget(self.target_15_spin, 0, 1)
#         config_grid.addWidget(labels[1], 0, 2)
#         config_grid.addWidget(self.target_30_spin, 0, 3)
#         config_grid.addWidget(labels[2], 0, 4)
#         config_grid.addWidget(self.continuous_fail_spin, 0, 5)
#         config_grid.addWidget(labels[3], 0, 6)
#         config_grid.addWidget(self.different_scrap_fail_spin, 0, 7)
#         config_grid.addWidget(self.save_button, 0, 8)
#         config_grid.setColumnStretch(9, 1)
#         layout.addLayout(config_grid)
#         layout.addStretch(1)
#
#     @staticmethod
#     def _target_spin_box() -> QDoubleSpinBox:
#         """Tạo ô Target phần trăm đồng nhất cho Target 15 và Target 30."""
#         spin = QDoubleSpinBox()
#         spin.setRange(0, 100)
#         spin.setDecimals(2)
#         spin.setSingleStep(0.1)
#         spin.setSuffix(" %")
#         spin.setFixedWidth(100)
#         return spin
#
#     def load_if_needed(self, force: bool = False) -> None:
#         """Đọc cấu hình lần đầu hoặc tải lại theo yêu cầu."""
#         if self._loaded and not force:
#             return
#         try:
#             config = self.repository.get_config()
#             # Log Folder được cấu hình tại File Management; tab này chỉ giữ
#             # lại giá trị hiện có khi lưu bốn ngưỡng.
#             self._log_folder = config.log_folder
#             self.target_15_spin.setValue(config.target_15)
#             self.target_30_spin.setValue(config.target_30)
#             self.continuous_fail_spin.setValue(config.continuous_fail_count)
#             self.different_scrap_fail_spin.setValue(config.different_scrap_fail_count)
#             self._loaded = True
#         except Exception as error:
#             QMessageBox.critical(self, "Machine Slot Yield", str(error))
#
#     def _save_config(self) -> None:
#         """Lưu các trường cấu hình và thông báo kết quả cho người dùng."""
#         try:
#             self.repository.save_config(
#                 getattr(self, "_log_folder", ""),
#                 self.target_15_spin.value(),
#                 self.target_30_spin.value(),
#                 self.continuous_fail_spin.value(),
#                 self.different_scrap_fail_spin.value(),
#             )
#             self._loaded = True
#             QMessageBox.information(
#                 self,
#                 "Machine Slot Yield",
#                 "Đã lưu cấu hình Machine Slot Yield.",
#             )
#         except Exception as error:
#             QMessageBox.critical(self, "Không thể lưu cấu hình", str(error))


from pathlib import Path
from typing import Union

from PyQt5.QtWidgets import (
    QDoubleSpinBox,
    QGridLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from repositories.machine_slot_yield_repository import (
    MachineSlotYieldRepository,
)


from PyQt5.QtCore import QThread
from database.read_wait import is_database_busy, read_timeout
from ui.database_wait import wait_manager
from workers.machine_slot_config_worker import MachineSlotConfigWorker

class MachineSlotYieldPage(QWidget):
    """Màn hình cấu hình ngưỡng Machine Slot Yield cho chức năng Alarm."""

    def __init__(self, database_path: Union[str, Path], parent=None):
        super().__init__(parent)
        self.repository = MachineSlotYieldRepository(database_path)
        self._loaded = False
        self.config_thread = None
        self.config_worker = None
        self._build_ui()

    def _build_ui(self) -> None:
        """Tạo bố cục một hàng cho bốn ngưỡng và nút lưu."""
        self.setObjectName("machineSlotYieldPage")
        self.setStyleSheet(
            """
            QWidget#machineSlotYieldPage { background: #FFFFFF; }
            QLabel { color:#111827; font-family:"Segoe UI"; font-size:12px; }
            QLabel#titleLabel { font-size:16px; font-weight:600; }
            QLabel#fieldLabel { font-weight:600; }
            QDoubleSpinBox, QSpinBox {
                min-height:28px; background:#FFFFFF; color:#111827;
                border:1px solid #B8C2CC; border-radius:3px;
                font-family:"Segoe UI"; font-size:12px;
            }
            QPushButton {
                min-height:30px; padding:0 12px; background:#F8FAFC;
                color:#1F2937; border:1px solid #B8C2CC; border-radius:3px;
                font-family:"Segoe UI"; font-size:12px; font-weight:500;
            }
            QPushButton:hover { background:#EAF3FC; border-color:#7AA7D3; }
            QPushButton:pressed { background:#DCEBFA; }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title = QLabel("Machine Slot Yield")
        title.setObjectName("titleLabel")
        # layout.addWidget(title)

        config_grid = QGridLayout()
        config_grid.setHorizontalSpacing(8)
        config_grid.setVerticalSpacing(0)

        self.target_15_spin = self._target_spin_box()
        self.target_30_spin = self._target_spin_box()
        self.continuous_fail_spin = QSpinBox()
        self.continuous_fail_spin.setRange(1, 9999)
        self.continuous_fail_spin.setFixedWidth(95)
        self.continuous_fail_spin.setToolTip(
            "Số bản ghi FAIL liên tục cùng máy/slot, Model và Scrap code."
        )
        self.different_scrap_fail_spin = QSpinBox()
        self.different_scrap_fail_spin.setRange(2, 9999)
        self.different_scrap_fail_spin.setFixedWidth(95)
        self.different_scrap_fail_spin.setToolTip(
            "FAIL liên tục cùng máy/slot và Model, có ít nhất 2 Scrap code khác nhau."
        )
        self.save_button = QPushButton("Save Target")
        self.save_button.setIcon(
            self.style().standardIcon(QStyle.SP_DialogSaveButton)
        )
        self.save_button.clicked.connect(self._save_config)

        labels = (
            QLabel("Target 15:"),
            QLabel("Target 30:"),
            QLabel("Số lần fail liên tục cùng scrapcode:"),
            QLabel("Số lần fail liên tục khác Scrap code:"),
        )
        for label in labels:
            label.setObjectName("fieldLabel")

        config_grid.addWidget(labels[0], 0, 0)
        config_grid.addWidget(self.target_15_spin, 0, 1)
        config_grid.addWidget(labels[1], 0, 2)
        config_grid.addWidget(self.target_30_spin, 0, 3)
        config_grid.addWidget(labels[2], 0, 4)
        config_grid.addWidget(self.continuous_fail_spin, 0, 5)
        config_grid.addWidget(labels[3], 0, 6)
        config_grid.addWidget(self.different_scrap_fail_spin, 0, 7)
        config_grid.addWidget(self.save_button, 0, 8)
        config_grid.setColumnStretch(9, 1)
        layout.addLayout(config_grid)
        from ui.widgets.machine_slot_summary import MachineSlotSummary
        self.summary = MachineSlotSummary(self.repository.database_path, self)
        layout.addWidget(self.summary, 1)

    @staticmethod
    def _target_spin_box() -> QDoubleSpinBox:
        """Tạo ô Target phần trăm đồng nhất cho Target 15 và Target 30."""
        spin = QDoubleSpinBox()
        spin.setRange(0, 100)
        spin.setDecimals(2)
        spin.setSingleStep(0.1)
        spin.setSuffix(" %")
        spin.setFixedWidth(100)
        return spin

    def load_if_needed(self, force: bool = False) -> None:
        """Đọc cấu hình lần đầu hoặc tải lại theo yêu cầu."""
        if (self._loaded and not force) or self.config_thread is not None:
            return
        token = read_timeout.set(0.1)
        try:
            self._apply_config(self.repository.get_config())
        except Exception as error:
            if is_database_busy(error):
                self.config_thread = QThread(self)
                self.config_worker = MachineSlotConfigWorker(self.repository.database_path)
                for control in self._config_controls():
                    control.setEnabled(False)
                wait_manager(self).bind(self.config_worker)
                self.config_worker.moveToThread(self.config_thread)
                self.config_thread.started.connect(self.config_worker.run)
                self.config_worker.succeeded.connect(self._apply_config)
                self.config_worker.failed.connect(self._config_failed)
                self.config_worker.finished.connect(self.config_thread.quit)
                self.config_worker.finished.connect(self.config_worker.deleteLater)
                self.config_thread.finished.connect(self._config_finished)
                self.config_thread.finished.connect(self.config_thread.deleteLater)
                self.config_thread.start()
            else:
                QMessageBox.critical(self, "Machine Slot Yield", str(error))
        finally:
            read_timeout.reset(token)

    def _config_controls(self):
        return (self.target_15_spin, self.target_30_spin, self.continuous_fail_spin,
                self.different_scrap_fail_spin, self.save_button)

    def _apply_config(self, config):
        self._log_folder = config.log_folder
        self.target_15_spin.setValue(config.target_15)
        self.target_30_spin.setValue(config.target_30)
        self.continuous_fail_spin.setValue(config.continuous_fail_count)
        self.different_scrap_fail_spin.setValue(config.different_scrap_fail_count)
        self._loaded = True

    def _config_failed(self, message):
        if not self.summary.closing:
            QMessageBox.critical(self, "Machine Slot Yield", message)

    def _config_finished(self):
        self.config_thread = self.config_worker = None
        for control in self._config_controls():
            control.setEnabled(self._loaded)

    def _save_config(self) -> None:
        """Lưu các trường cấu hình và thông báo kết quả cho người dùng."""
        try:
            self.repository.save_config(
                getattr(self, "_log_folder", ""),
                self.target_15_spin.value(),
                self.target_30_spin.value(),
                self.continuous_fail_spin.value(),
                self.different_scrap_fail_spin.value(),
            )
            self._loaded = True
            QMessageBox.information(
                self,
                "Machine Slot Yield",
                "Đã lưu cấu hình Machine Slot Yield.",
            )
        except Exception as error:
            QMessageBox.critical(self, "Không thể lưu cấu hình", str(error))
