# from PyQt5.QtCore import QObject, QThread, QTimer, Qt, pyqtSlot
# from config.paths import DATABASE_PATH, LOG_ENCODING
# from ui.dialogs.import_dialogs import ImportDialogs
# from workers.database_init_worker import DatabaseInitWorker
# from workers.prime_import_worker import PrimeImportWorker
# from workers.cum_import_worker import CumImportWorker
# from workers.filter_option_worker import FilterOptionWorker
# from workers.summary_worker import SummaryWorker
# from workers.slot_summary_worker import SlotSummaryWorker
#
#
# class PrimeController(QObject):
#     """Điều phối UI và worker; không đọc log hoặc truy vấn SQL."""
#     def __init__(self, window, database_path=DATABASE_PATH, encoding=LOG_ENCODING):
#         """Khởi tạo trạng thái và các thành phần cần cho đối tượng."""
#         super().__init__(window)
#         self.window = window
#         self.database_path = database_path
#         self.encoding = encoding
#         self.dialogs = ImportDialogs(window)
#         self._thread = None
#         self._worker = None
#         self._kind = None
#         self._outcome = None
#         self._ready = False
#         self._filter_thread = None
#         self._filter_worker = None
#         self._filter_outcome = None
#         self._filter_refresh_pending = False
#         self._filters_ready = False
#         self._pending_search = None
#         self._pending_action = None
#         self._preload_thread = None
#         self._preload_worker = None
#         self._closing = False
#         self._summary_key = None
#         self._slot_key = None
#         self._pending_slot_key = None
#         self._pending_summary_key = None
#         window.prime_page.import_requested.connect(self.choose_import)
#         window.prime_page.cum_import_requested.connect(self.choose_cum_import)
#         window.prime_page.filter_applied.connect(self.load_summary)
#         window.prime_page.alarm_edit_requested.connect(self.save_alarm_tracking)
#         window.prime_page.alarm_history_requested.connect(self.load_alarm_history)
#         window.close_requested.connect(self.request_close)
#         window.prime_page.file_management_requested.connect(self.open_file_management)
#         window.prime_page.send_mail_requested.connect(self.open_send_mail)
#         window.prime_page.report_requested.connect(self.open_report)
#         window.prime_page.machine_slot_yield_requested.connect(
#             self.open_machine_slot_yield
#         )
#
#     @property
#     def busy(self):
#         """Cho biết đang có worker khởi tạo hoặc import chạy."""
#         return self._thread is not None
#
#     def _start(self, worker, kind):
#         """Gắn worker vào QThread và khóa hai nút import đến khi tác vụ kết thúc."""
#         self._worker = worker
#         self._kind = kind
#         self._outcome = None
#         self._thread = QThread(self)
#         worker.moveToThread(self._thread)
#         self._thread.started.connect(worker.run)
#         worker.failed.connect(self._failed)
#         worker.finished.connect(self._thread.quit)
#         worker.finished.connect(worker.deleteLater)
#         self._thread.finished.connect(self._finished)
#         self._thread.finished.connect(self._thread.deleteLater)
#         self.window.prime_page.set_import_enabled(kind == "init")
#         if kind == "init":
#             self.window.prime_page.set_filters_ready(True)
#         if self.window.prime_page.alarm_page is not None:
#             self.window.prime_page.alarm_page.set_busy(True)
#         if kind in ("import", "cum") and self._filter_worker is not None:
#             self._filter_refresh_pending = True
#             self._filter_worker.request_cancel()
#         self._thread.start()
#
#     @pyqtSlot()
#     def initialize_database(self):
#         """Tạo schema cho database mới hoặc kiểm tra database đã tồn tại."""
#         if self.busy or self._closing:
#             return
#         self._ready = False
#         self.window.statusBar().showMessage("Đang kiểm tra database...")
#         worker = DatabaseInitWorker(self.database_path)
#         worker.succeeded.connect(self._initialized)
#         self._start(worker, "init")
#
#     @pyqtSlot()
#     def _initialized(self):
#         """Đánh dấu database đã sẵn sàng cho việc import."""
#         self._ready = True
#         self._outcome = ("success", None)
#
#     @pyqtSlot(str)
#     def _failed(self, message):
#         """Lưu thông báo lỗi để hiển thị sau khi worker kết thúc."""
#         self._outcome = ("error", message)
#
#     @pyqtSlot(object)
#     def _succeeded(self, result):
#         """Lưu kết quả import để hiển thị sau khi worker kết thúc."""
#         self._outcome = ("success", result)
#
#     @pyqtSlot(str)
#     def _progress(self, message):
#         """Cập nhật tiến độ khi cửa sổ chưa được yêu cầu đóng."""
#         if not self._closing:
#             self.dialogs.update_progress(message)
#
#     @pyqtSlot()
#     def _finished(self):
#         """Dọn worker, khôi phục nút và hiển thị kết quả hoặc đóng cửa sổ an toàn."""
#         kind, outcome = self._kind, self._outcome
#         self._worker = None
#         self._thread = None
#         self._kind = None
#         if self.window.prime_page.alarm_page is not None:
#             self.window.prime_page.alarm_page.set_busy(False)
#         if kind not in ("summary", "slot") or self._closing:
#             self.dialogs.end_progress()
#         if self._closing:
#             self._finish_close_when_idle()
#             return
#         # Chính nút Import PRIME cũng cho phép thử lại khi khởi tạo DB lỗi.
#         self.window.prime_page.set_import_enabled(True)
#         self.window.prime_page.tabs.tabBar().setEnabled(True)
#         self.window.prime_page.set_filters_ready(True)
#         if outcome is None or outcome[0] == "error":
#             message = outcome[1] if outcome else "Tác vụ kết thúc mà không có kết quả."
#             if kind == "init":
#                 message += "\nBấm Import PRIME để thử kết nối database lại."
#             if kind == "summary":
#                 self._summary_key = None
#                 self.window.prime_page.summary_page.clear_result("Không thể tải dữ liệu.")
#             if kind == "slot":
#                 self._slot_key = None
#                 self.window.prime_page.yield_slot_page.clear_result("Không thể tải dữ liệu.")
#             if kind == "alarm":
#                 self.window.prime_page.alarm_page.load_rows([])
#                 self.window.prime_page.alarm_page.status_label.setText("Không thể tải Alarm.")
#                 if self.window.prime_page.dashboard_page is not None:
#                     self.window.prime_page.dashboard_page.load_rows([])
#             if kind == "alarm_save":
#                 self.window.prime_page.alarm_page.status_label.setText("Chưa lưu thay đổi Alarm. " + message)
#             self.dialogs.end_progress()
#             self.dialogs.show_error(message)
#         elif kind == "summary":
#             try:
#                 self.window.prime_page.summary_page.load_result(outcome[1], self._pending_summary_key)
#                 self._summary_key = self._pending_summary_key
#             except Exception as error:
#                 self._summary_key = None
#                 self.window.prime_page.summary_page.clear_result("Không thể hiển thị biểu đồ.")
#                 self.dialogs.end_progress()
#                 self.dialogs.show_error(str(error))
#         elif kind == "slot":
#             try:
#                 self.window.prime_page.yield_slot_page.load_result(outcome[1], self._pending_slot_key)
#                 self._slot_key = self._pending_slot_key
#             except Exception as error:
#                 self._slot_key = None
#                 self.window.prime_page.yield_slot_page.clear_result("Không thể hiển thị biểu đồ.")
#                 self.dialogs.end_progress()
#                 self.dialogs.show_error(str(error))
#         elif kind == "alarm":
#             rows = outcome[1]
#             self.window.prime_page.alarm_page.load_rows(rows)
#             self.window.prime_page.ensure_dashboard_page().load_rows(
#                 self.window.prime_page.alarm_page.visible_rows()
#             )
#         elif kind == "alarm_history":
#             from ui.dialogs.slot_fail_history_dialog import SlotFailHistoryDialog
#             history = outcome[1]
#             dialog = SlotFailHistoryDialog(history, self.window,
#                                            preferred_rule=history.get('preferred_rule'))
#             dialog.setAttribute(Qt.WA_DeleteOnClose)
#             dialog.setModal(True)
#             self._history_dialog = dialog
#             dialog.show()
#         elif kind == "alarm_save":
#             latest, conflict = outcome[1]
#             page = self.window.prime_page.alarm_page
#             page.model.update_row(latest)
#             page.update_count()
#             if self.window.prime_page.dashboard_page is not None:
#                 self.window.prime_page.dashboard_page.load_rows(page.visible_rows())
#             if conflict:
#                 self.dialogs.show_error("Alarm vừa được người khác cập nhật. Đã tải dòng mới nhất; thay đổi của bạn chưa được lưu.")
#         elif kind == "cum":
#             self._mark_file_data_changed("CUM")
#             self.dialogs.show_cum_result(outcome[1])
#         elif kind == "import":
#             self._mark_file_data_changed("PRIME")
#             self.dialogs.show_result(outcome[1])
#         if kind in ("summary", "slot", "alarm", "alarm_save", "alarm_history"):
#             self.dialogs.end_progress()
#             self.window.prime_page.set_filters_ready(True)
#         if kind in ("init", "import", "cum") and self._ready and not self._closing:
#             self.refresh_filter_options()
#         if kind == "init" and self._ready:
#             self.window.statusBar().showMessage("Database sẵn sàng.", 3000)
#         if self._pending_action and self._ready:
#             action, self._pending_action = self._pending_action, None
#             QTimer.singleShot(0, action)
#         elif self._pending_search is not None and self._filters_ready:
#             QTimer.singleShot(0, self._resume_search)
#         elif self._ready:
#             # A tab selected while initialization was in progress must open now.
#             page = self.window.prime_page
#             if page.tabs.currentWidget() is page.file_management_host:
#                 self.open_file_management()
#             elif page.tabs.currentWidget() is page.send_mail_host:
#                 self.open_send_mail()
#             elif page.tabs.currentWidget() is page.machine_slot_yield_host:
#                 self.open_machine_slot_yield()
#             elif page.tabs.currentWidget() is page.report_host:
#                 self.open_report()
#
#     @pyqtSlot()
#     def choose_import(self):
#         """Chọn khoảng ngày và thư mục nguồn cho Import PRIME."""
#         if self._closing:
#             return
#         if not self._ready:
#             self._pending_action = self.choose_import
#             self.initialize_database()
#             return
#         if self.busy:
#             return
#         selection = self.dialogs.choose_source()
#         if selection is not None:
#             self.start_import(*selection)
#
#     def start_import(self, root, dates):
#         """Khởi động worker PRIME khi database sẵn sàng và không có tác vụ khác."""
#         if self.busy or self._closing or not self._ready:
#             return
#         worker = PrimeImportWorker(self.database_path, root, dates, self.encoding)
#         worker.progress.connect(self._progress)
#         worker.succeeded.connect(self._succeeded)
#         self.dialogs.begin_progress(self.cancel_import)
#         self._start(worker, "import")
#
#     @pyqtSlot()
#     def cancel_import(self):
#         """Gửi cờ hủy an toàn tới worker import đang chạy."""
#         if self._worker is not None and self._kind in ("import", "cum"):
#             self._worker.request_cancel()
#
#     @pyqtSlot()
#     def request_close(self):
#         """Hủy tác vụ đang chạy và đợi kết thúc trước khi đóng cửa sổ."""
#         self._closing = True
#         if self._filter_worker is not None:
#             self._filter_worker.request_cancel()
#         mail_page = self.window.prime_page.send_mail_page
#         if mail_page is not None:
#             mail_page.prepare_close()
#         page = self.window.prime_page.file_management_page
#         if page is not None:
#             page.prepare_close()
#         if self.busy:
#             self.cancel_import()
#             self.window.setEnabled(False)
#         else:
#             self._finish_close_when_idle()
#
#     @pyqtSlot()
#     def choose_cum_import(self):
#         """Chọn một file CUM rồi khởi động worker khi database đã sẵn sàng."""
#         if self._closing:
#             return
#         if not self._ready:
#             self._pending_action = self.choose_cum_import
#             self.initialize_database()
#             return
#         if self.busy:
#             return
#         source = self.dialogs.choose_cum_source()
#         if source:
#             self.start_cum_import(source)
#
#     def start_cum_import(self, excel_path):
#         """Chạy CUM dưới cùng bộ điều phối để không chồng tác vụ PRIME và CUM."""
#         if self.busy or self._closing or not self._ready:
#             return
#         worker = CumImportWorker(self.database_path, excel_path)
#         worker.progress.connect(self._progress)
#         worker.succeeded.connect(self._succeeded)
#         self.dialogs.begin_progress(self.cancel_import, "CUM")
#         self._start(worker, "cum")
#
#     @pyqtSlot()
#     def refresh_filter_options(self):
#         """Read options independently; never lock Import or the tab bar."""
#         if self._closing or not self._ready:
#             return
#         if self._filter_thread is not None or self.busy:
#             self._filter_refresh_pending = True
#             return
#         self._filter_refresh_pending = False
#         if self._filters_ready:
#             self.window.prime_page.yield_slot_page.clear_result()
#             self.window.prime_page.summary_page.clear_result()
#         self._filters_ready = False
#         self._summary_key = None
#         self._slot_key = None
#         self._filter_outcome = None
#         self.window.statusBar().showMessage("Đang tải bộ lọc ở nền; có thể chọn tab hoặc Import.")
#         worker = FilterOptionWorker(self.database_path)
#         thread = QThread(self)
#         self._filter_worker, self._filter_thread = worker, thread
#         worker.moveToThread(thread)
#         thread.started.connect(worker.run)
#         worker.succeeded.connect(self._filter_succeeded)
#         worker.failed.connect(self._filter_failed)
#         worker.finished.connect(thread.quit)
#         worker.finished.connect(worker.deleteLater)
#         thread.finished.connect(self._filter_finished)
#         thread.finished.connect(thread.deleteLater)
#         thread.start()
#
#     @pyqtSlot(object)
#     def _filter_succeeded(self, result):
#         self._filter_outcome = ("success", result)
#
#     @pyqtSlot(str)
#     def _filter_failed(self, message):
#         self._filter_outcome = ("error", message)
#
#     @pyqtSlot()
#     def _filter_finished(self):
#         self._filter_thread = self._filter_worker = None
#         if self._closing:
#             self._finish_close_when_idle()
#             return
#         if self._filter_refresh_pending:
#             self.refresh_filter_options()
#             return
#         outcome = self._filter_outcome
#         if outcome and outcome[0] == "success":
#             self.window.prime_page.load_filter_options(outcome[1])
#             self._filters_ready = True
#             self.window.statusBar().showMessage("Bộ lọc sẵn sàng.", 3000)
#             if not self.busy:
#                 self._resume_search()
#         elif outcome:
#             self.window.statusBar().showMessage("Không tải được bộ lọc. Bấm SEARCH để thử lại: " + outcome[1])
#         # A background result must not unlock an active foreground operation.
#         self.window.prime_page.set_filters_ready(not self.busy)
#
#     def _resume_search(self):
#         if self._pending_search is None or self.busy or self._closing:
#             return
#         self._pending_search = None
#         # Use controls after options arrive (including their default selection).
#         self.load_summary(self.window.prime_page.filter_panel.get_filter_criteria())
#
#     @pyqtSlot()
#     def start_chart_preload(self):
#         """Called after show; only import modules, never construct Qt widgets."""
#         if self._closing or self._preload_thread is not None:
#             return
#         from workers.chart_preload_worker import ChartPreloadWorker
#         worker = ChartPreloadWorker()
#         thread = QThread(self)
#         self._preload_worker, self._preload_thread = worker, thread
#         worker.moveToThread(thread)
#         thread.started.connect(worker.run)
#         worker.finished.connect(thread.quit)
#         worker.finished.connect(worker.deleteLater)
#         thread.finished.connect(self._preload_finished)
#         thread.finished.connect(thread.deleteLater)
#         thread.start()
#
#     @pyqtSlot()
#     def _preload_finished(self):
#         self._preload_thread = self._preload_worker = None
#         if self._closing:
#             self._finish_close_when_idle()
#
#     @pyqtSlot(object)
#     def load_summary(self, criteria):
#         """Chỉ query khi Date/Tier/Model/EQP đổi; chia sẻ vòng đời worker import."""
#         if self.window.prime_page.tabs.currentWidget() is self.window.prime_page.report_host:
#             self.open_report()
#             return
#         if self._closing:
#             return
#         if self.busy or not self._ready:
#             self._pending_search = criteria
#             return
#         if self.window.prime_page.tabs.currentWidget() is self.window.prime_page.file_management_host:
#             self.open_file_management()
#             return
#         if self.window.prime_page.tabs.currentWidget() is self.window.prime_page.send_mail_host:
#             self.open_send_mail()
#             return
#         if (
#             self.window.prime_page.tabs.currentWidget()
#             is self.window.prime_page.machine_slot_yield_host
#         ):
#             self.open_machine_slot_yield()
#             return
#         if not self._filters_ready:
#             self._pending_search = criteria
#             if self._filter_thread is None:
#                 self.refresh_filter_options()
#             self.window.statusBar().showMessage("Đang tải bộ lọc; sẽ thực hiện SEARCH khi sẵn sàng.")
#             return
#         if self.window.prime_page.tabs.currentWidget() is self.window.prime_page.alarm_host:
#             self.load_alarm(criteria)
#             return
#         if self.window.prime_page.tabs.currentWidget() is self.window.prime_page.dashboard_host:
#             self.load_alarm(criteria)
#             return
#         key = (criteria.date_from, criteria.date_to,
#                tuple(sorted({str(t) for t in criteria.tiers if t is not None})),
#                tuple(sorted(set(criteria.models))), criteria.eqp or None)
#         if self.window.prime_page.tabs.currentWidget() is self.window.prime_page.yield_slot_page:
#             self.load_slot_summary((*key, criteria.slot), criteria.scrap_codes)
#             return
#         page = self.window.prime_page.summary_page
#         page.set_scrap_codes(criteria.scrap_codes)
#         if key == self._summary_key:
#             try:
#                 page.set_scrap_codes(criteria.scrap_codes, redraw=True)
#             except Exception as error:
#                 self.dialogs.show_error(str(error))
#             return
#         self._pending_summary_key = key
#         self.window.prime_page.summary_page.set_loading(key[0], key[1])
#         self.dialogs.begin_loading("Loading ...")
#         worker = SummaryWorker(self.database_path, key)
#         worker.succeeded.connect(self._succeeded)
#         self._start(worker, "summary")
#
#     def load_slot_summary(self, key, scrap_codes=()):
#         """SEARCH chỉ tải tab Yield Slot đang mở; cache riêng với Summary."""
#         page = self.window.prime_page.yield_slot_page
#         page.set_scrap_codes(scrap_codes)
#         if key == self._slot_key:
#             try:
#                 page.set_scrap_codes(scrap_codes, redraw=True)
#             except Exception as error:
#                 self.dialogs.show_error(str(error))
#             return
#         self._pending_slot_key = key
#         page.set_loading(key[0], key[1])
#         self.dialogs.begin_loading("Loading ...")
#         cached_model = (page.model_summary.result
#                         if self._slot_key and self._slot_key[:3] == key[:3] else None)
#         worker = SlotSummaryWorker(self.database_path, key, cached_model=cached_model)
#         worker.succeeded.connect(self._succeeded)
#         self._start(worker, "slot")
#
#
#     @pyqtSlot()
#     def open_file_management(self):
#         """Tải File Management độc lập bộ lọc thống kê, chỉ sau khởi tạo DB."""
#         if self._ready and not self.busy and not self._closing:
#             self.window.prime_page.open_file_management(self.database_path)
#
#     def _mark_file_data_changed(self, data_type):
#         """Làm mới đúng danh sách sau import PRIME/CUM thành công."""
#         report = self.window.prime_page.report_page
#         if data_type == "PRIME" and report is not None:
#             report.mark_data_changed()
#         page = self.window.prime_page.file_management_page
#         if page is not None:
#             page.mark_data_changed(data_type)
#
#     def _finish_close_when_idle(self):
#         """Đợi cả worker File Management để đóng an toàn chỉ với một lần click."""
#         page = self.window.prime_page.file_management_page
#         mail_page = self.window.prime_page.send_mail_page
#         report = self.window.prime_page.report_page
#         if report is not None:
#             report.prepare_close()
#             if report.has_running_tasks():
#                 self.window.setEnabled(False)
#                 QTimer.singleShot(50, self._finish_close_when_idle)
#                 return
#         if self.busy or self._filter_thread is not None or self._preload_thread is not None or (page is not None and page.is_busy()) or (mail_page is not None and mail_page.is_busy()):
#             self.window.setEnabled(False)
#             QTimer.singleShot(50, self._finish_close_when_idle)
#             return
#         self.window.finish_close()
#
#     @pyqtSlot()
#     def open_report(self):
#         if self._ready and not self.busy and not self._closing:
#             self.window.prime_page.open_report(self.database_path)
#
#     @pyqtSlot()
#     def open_send_mail(self):
#         """Mở cấu hình mail độc lập From/To/EQP/Model/Tier/Scrap Code."""
#         if self._ready and not self.busy and not self._closing:
#             self.window.prime_page.open_send_mail(self.database_path)
#
#     @pyqtSlot()
#     def open_machine_slot_yield(self, refresh=True):
#         """Mở cấu hình Machine Slot Yield độc lập bộ lọc thống kê."""
#         if self._ready and not self.busy and not self._closing:
#             self.window.prime_page.open_machine_slot_yield(
#                 self.database_path
#             )
#
#     def load_alarm(self, criteria):
#         """Đọc Alarm mỗi lần Search/chuyển tab, kể cả import ngoài app vừa cập nhật DB."""
#         if self.busy or self._closing or not self._ready:
#             return
#         from workers.alarm_worker import AlarmWorker
#         page = self.window.prime_page.ensure_alarm_page()
#         page.set_date_range(criteria.date_from, criteria.date_to)
#         dashboard = self.window.prime_page.ensure_dashboard_page()
#         dashboard.set_date_range(criteria.date_from, criteria.date_to)
#         page.status_label.setText("Đang tải Alarm...")
#         worker = AlarmWorker(self.database_path, (criteria.date_from, criteria.date_to))
#         worker.succeeded.connect(self._succeeded)
#         self.dialogs.begin_loading("Loading Alarm ...")
#         self._start(worker, "alarm")
#
#     @pyqtSlot(object, str, str)
#     def save_alarm_tracking(self, expected, field, value):
#         """Lưu ô trên worker chung để chặn import chồng và đóng app an toàn."""
#         if self.busy or self._closing or not self._ready:
#             return
#         from workers.alarm_worker import AlarmWorker
#         worker = AlarmWorker(self.database_path, edit=(expected, field, value))
#         worker.succeeded.connect(self._succeeded)
#         self.dialogs.begin_loading("Saving Alarm ...")
#         self._start(worker, "alarm_save")
#
#     @pyqtSlot(object)
#     def load_alarm_history(self, expected):
#         """Dùng worker lifecycle hiện có: không treo UI, đóng app đợi thread an toàn."""
#         if self.busy or self._closing or not self._ready:
#             return
#         from workers.alarm_worker import AlarmWorker
#         worker = AlarmWorker(self.database_path, history=expected)
#         worker.succeeded.connect(self._succeeded)
#         self.dialogs.begin_loading("Loading Slot Fail History ...")
#         self._start(worker, "alarm_history")

from PyQt5.QtCore import QObject, QThread, QTimer, Qt, pyqtSlot
from ui.database_wait import wait_manager
from config.paths import DATABASE_PATH, LOG_ENCODING
from ui.dialogs.import_dialogs import ImportDialogs
from workers.database_init_worker import DatabaseInitWorker
from workers.prime_import_worker import PrimeImportWorker
from workers.cum_import_worker import CumImportWorker
from workers.filter_option_worker import FilterOptionWorker
from workers.summary_worker import SummaryWorker
from workers.slot_summary_worker import SlotSummaryWorker


class PrimeController(QObject):
    """Điều phối UI và worker; không đọc log hoặc truy vấn SQL."""
    def __init__(self, window, database_path=DATABASE_PATH, encoding=LOG_ENCODING):
        """Khởi tạo trạng thái và các thành phần cần cho đối tượng."""
        super().__init__(window)
        self.window = window
        self.database_path = database_path
        self.encoding = encoding
        self.dialogs = ImportDialogs(window)
        self.database_wait = wait_manager(window)
        self._thread = None
        self._worker = None
        self._kind = None
        self._outcome = None
        self._ready = False
        self._filter_thread = None
        self._filter_worker = None
        self._filter_outcome = None
        self._filter_refresh_pending = False
        self._filters_ready = False
        self._pending_search = None
        self._pending_search_force = False
        self._pending_action = None
        self._preload_thread = None
        self._preload_worker = None
        self._closing = False
        self._summary_key = None
        self._slot_key = None
        self._alarm_key = None
        self._pending_alarm_key = None
        self._pending_slot_key = None
        self._pending_summary_key = None
        window.prime_page.import_requested.connect(self.choose_import)
        window.prime_page.cum_import_requested.connect(self.choose_cum_import)
        window.prime_page.filter_applied.connect(
            lambda criteria: self.load_summary(criteria, force=True))
        window.prime_page.filter_activated.connect(self.load_summary)
        window.prime_page.alarm_edit_requested.connect(self.save_alarm_tracking)
        window.prime_page.alarm_history_requested.connect(self.load_alarm_history)
        window.close_requested.connect(self.request_close)
        window.prime_page.file_management_requested.connect(self.open_file_management)
        window.prime_page.send_mail_requested.connect(self.open_send_mail)
        window.prime_page.report_requested.connect(self.open_report)
        window.prime_page.machine_slot_yield_requested.connect(
            self.open_machine_slot_yield
        )

    @property
    def busy(self):
        """Cho biết đang có worker khởi tạo hoặc import chạy."""
        return self._thread is not None

    def _start(self, worker, kind):
        """Gắn worker vào QThread và khóa hai nút import đến khi tác vụ kết thúc."""
        if hasattr(worker, "database_waiting"):
            self.database_wait.bind(worker, self.dialogs.end_progress)
        self._worker = worker
        self._kind = kind
        self._outcome = None
        self._thread = QThread(self)
        worker.moveToThread(self._thread)
        self._thread.started.connect(worker.run)
        worker.failed.connect(self._failed)
        worker.finished.connect(self._thread.quit)
        worker.finished.connect(worker.deleteLater)
        self._thread.finished.connect(self._finished)
        self._thread.finished.connect(self._thread.deleteLater)
        self.window.prime_page.set_import_enabled(kind == "init")
        if kind == "init":
            self.window.prime_page.set_filters_ready(False)
        if self.window.prime_page.alarm_page is not None:
            self.window.prime_page.alarm_page.set_busy(True)
        if kind in ("import", "cum") and self._filter_worker is not None:
            self._filter_refresh_pending = True
            self._filter_worker.request_cancel()
        self._thread.start()

    @pyqtSlot()
    def initialize_database(self):
        """Tạo schema cho database mới hoặc kiểm tra database đã tồn tại."""
        if self.busy or self._closing:
            return
        self._ready = False
        self.window.statusBar().showMessage("Đang kiểm tra database...")
        worker = DatabaseInitWorker(self.database_path)
        worker.succeeded.connect(self._initialized)
        self._start(worker, "init")

    @pyqtSlot()
    def _initialized(self):
        """Đánh dấu database đã sẵn sàng cho việc import."""
        self._ready = True
        self._outcome = ("success", None)

    @pyqtSlot(str)
    def _failed(self, message):
        """Lưu thông báo lỗi để hiển thị sau khi worker kết thúc."""
        self._outcome = ("error", message)

    @pyqtSlot(object)
    def _succeeded(self, result):
        """Lưu kết quả import để hiển thị sau khi worker kết thúc."""
        self._outcome = ("success", result)

    @pyqtSlot(str)
    def _progress(self, message):
        """Cập nhật tiến độ khi cửa sổ chưa được yêu cầu đóng."""
        if not self._closing:
            self.dialogs.update_progress(message)

    @pyqtSlot()
    def _finished(self):
        """Dọn worker, khôi phục nút và hiển thị kết quả hoặc đóng cửa sổ an toàn."""
        kind, outcome = self._kind, self._outcome
        self._worker = None
        self._thread = None
        self._kind = None
        if self.window.prime_page.alarm_page is not None:
            self.window.prime_page.alarm_page.set_busy(False)
        if kind not in ("summary", "slot") or self._closing:
            self.dialogs.end_progress()
        if self._closing:
            self._finish_close_when_idle()
            return
        # Chính nút Import PRIME cũng cho phép thử lại khi khởi tạo DB lỗi.
        self.window.prime_page.set_import_enabled(True)
        self.window.prime_page.tabs.tabBar().setEnabled(True)
        self.window.prime_page.set_filters_ready(True)
        if outcome is None or outcome[0] == "error":
            message = outcome[1] if outcome else "Tác vụ kết thúc mà không có kết quả."
            if kind == "init":
                message += "\nBấm Import PRIME để thử kết nối database lại."
            if kind == "summary":
                self._summary_key = None
                self.window.prime_page.summary_page.clear_result("Không thể tải dữ liệu.")
            if kind == "slot":
                self._slot_key = None
                self.window.prime_page.yield_slot_page.clear_result("Không thể tải dữ liệu.")
            if kind == "alarm":
                self._alarm_key = None
                self.window.prime_page.alarm_page.load_rows([])
                self.window.prime_page.alarm_page.status_label.setText("Không thể tải Alarm.")
                if self.window.prime_page.dashboard_page is not None:
                    self.window.prime_page.dashboard_page.load_rows([])
            if kind == "alarm_save":
                self.window.prime_page.alarm_page.status_label.setText("Chưa lưu thay đổi Alarm. " + message)
            self.dialogs.end_progress()
            self.dialogs.show_error(message)
        elif kind == "summary":
            try:
                self.window.prime_page.summary_page.load_result(outcome[1], self._pending_summary_key)
                self._summary_key = self._pending_summary_key
            except Exception as error:
                self._summary_key = None
                self.window.prime_page.summary_page.clear_result("Không thể hiển thị biểu đồ.")
                self.dialogs.end_progress()
                self.dialogs.show_error(str(error))
        elif kind == "slot":
            try:
                self.window.prime_page.yield_slot_page.load_result(outcome[1], self._pending_slot_key)
                self._slot_key = self._pending_slot_key
            except Exception as error:
                self._slot_key = None
                self.window.prime_page.yield_slot_page.clear_result("Không thể hiển thị biểu đồ.")
                self.dialogs.end_progress()
                self.dialogs.show_error(str(error))
        elif kind == "alarm":
            self.window.prime_page.alarm_page.set_date_range(*self._pending_alarm_key)
            self.window.prime_page.ensure_dashboard_page().set_date_range(*self._pending_alarm_key)
            self._alarm_key = self._pending_alarm_key
            rows = outcome[1]
            self.window.prime_page.alarm_page.load_rows(rows)
            self.window.prime_page.ensure_dashboard_page().load_rows(
                self.window.prime_page.alarm_page.visible_rows()
            )
        elif kind == "alarm_history":
            from ui.dialogs.slot_fail_history_dialog import SlotFailHistoryDialog
            history = outcome[1]
            dialog = SlotFailHistoryDialog(history, self.window,
                                           preferred_rule=history.get('preferred_rule'))
            dialog.setAttribute(Qt.WA_DeleteOnClose)
            dialog.setModal(True)
            self._history_dialog = dialog
            dialog.show()
        elif kind == "alarm_save":
            latest, conflict = outcome[1]
            page = self.window.prime_page.alarm_page
            page.model.update_row(latest)
            page.update_count()
            if self.window.prime_page.dashboard_page is not None:
                self.window.prime_page.dashboard_page.load_rows(page.visible_rows())
            if conflict:
                self.dialogs.show_error("Alarm vừa được người khác cập nhật. Đã tải dòng mới nhất; thay đổi của bạn chưa được lưu.")
        elif kind == "cum":
            self._mark_file_data_changed("CUM")
            self.dialogs.show_cum_result(outcome[1])
        elif kind == "import":
            self._mark_file_data_changed("PRIME")
            self.dialogs.show_result(outcome[1])
        if kind in ("summary", "slot", "alarm", "alarm_save", "alarm_history"):
            self.dialogs.end_progress()
            self.window.prime_page.set_filters_ready(True)
        if kind in ("init", "import", "cum") and self._ready and not self._closing:
            self.refresh_filter_options()
        if kind == "init" and self._ready:
            self.window.statusBar().showMessage("Database sẵn sàng.", 3000)
        if self._pending_action and self._ready:
            action, self._pending_action = self._pending_action, None
            QTimer.singleShot(0, action)
        elif self._pending_search is not None and self._filters_ready:
            QTimer.singleShot(0, self._resume_search)
        elif self._ready:
            # A tab selected while initialization was in progress must open now.
            page = self.window.prime_page
            if page.tabs.currentWidget() is page.file_management_host:
                self.open_file_management()
            elif page.tabs.currentWidget() is page.send_mail_host:
                self.open_send_mail()
            elif page.tabs.currentWidget() is page.machine_slot_yield_host:
                self.open_machine_slot_yield()
            elif page.tabs.currentWidget() is page.report_host:
                self.open_report()

    @pyqtSlot()
    def choose_import(self):
        """Chọn khoảng ngày và thư mục nguồn cho Import PRIME."""
        if self._closing:
            return
        if not self._ready:
            self._pending_action = self.choose_import
            self.initialize_database()
            return
        if self.busy:
            return
        selection = self.dialogs.choose_source()
        if selection is not None:
            self.start_import(*selection)

    def start_import(self, root, dates):
        """Khởi động worker PRIME khi database sẵn sàng và không có tác vụ khác."""
        if self.busy or self._closing or not self._ready:
            return
        worker = PrimeImportWorker(self.database_path, root, dates, self.encoding)
        worker.progress.connect(self._progress)
        worker.succeeded.connect(self._succeeded)
        self.dialogs.begin_progress(self.cancel_import)
        self._start(worker, "import")

    @pyqtSlot()
    def cancel_import(self):
        """Gửi cờ hủy an toàn tới worker import đang chạy."""
        if self._worker is not None and self._kind in ("import", "cum"):
            self._worker.request_cancel()

    @pyqtSlot()
    def request_close(self):
        """Hủy tác vụ đang chạy và đợi kết thúc trước khi đóng cửa sổ."""
        self._closing = True
        self.database_wait.cancel_all()
        if self._filter_worker is not None:
            self._filter_worker.request_cancel()
        mail_page = self.window.prime_page.send_mail_page
        if mail_page is not None:
            mail_page.prepare_close()
        page = self.window.prime_page.file_management_page
        if page is not None:
            page.prepare_close()
        if self.busy:
            self.cancel_import()
            self.window.setEnabled(False)
        else:
            self._finish_close_when_idle()

    @pyqtSlot()
    def choose_cum_import(self):
        """Chọn một file CUM rồi khởi động worker khi database đã sẵn sàng."""
        if self._closing:
            return
        if not self._ready:
            self._pending_action = self.choose_cum_import
            self.initialize_database()
            return
        if self.busy:
            return
        source = self.dialogs.choose_cum_source()
        if source:
            self.start_cum_import(source)

    def start_cum_import(self, excel_path):
        """Chạy CUM dưới cùng bộ điều phối để không chồng tác vụ PRIME và CUM."""
        if self.busy or self._closing or not self._ready:
            return
        worker = CumImportWorker(self.database_path, excel_path)
        worker.progress.connect(self._progress)
        worker.succeeded.connect(self._succeeded)
        self.dialogs.begin_progress(self.cancel_import, "CUM")
        self._start(worker, "cum")

    @pyqtSlot()
    def refresh_filter_options(self):
        """Read options independently; never lock Import or the tab bar."""
        if self._closing or not self._ready:
            return
        if self._filter_thread is not None or self.busy:
            self._filter_refresh_pending = True
            return
        self._filter_refresh_pending = False
        self._filter_had_results = self._filters_ready
        self._filters_ready = False
        self._summary_key = None
        self._slot_key = None
        self._alarm_key = None
        self._pending_alarm_key = None
        self._filter_outcome = None
        self.window.statusBar().showMessage("Đang tải bộ lọc ở nền; có thể chọn tab hoặc Import.")
        worker = FilterOptionWorker(self.database_path)
        self.database_wait.bind(worker, self.dialogs.end_progress)
        thread = QThread(self)
        self._filter_worker, self._filter_thread = worker, thread
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.succeeded.connect(self._filter_succeeded)
        worker.failed.connect(self._filter_failed)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self._filter_finished)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    @pyqtSlot(object)
    def _filter_succeeded(self, result):
        self._filter_outcome = ("success", result)

    @pyqtSlot(str)
    def _filter_failed(self, message):
        self._filter_outcome = ("error", message)

    @pyqtSlot()
    def _filter_finished(self):
        self._filter_thread = self._filter_worker = None
        if self._closing:
            self._finish_close_when_idle()
            return
        if self._filter_refresh_pending:
            self.refresh_filter_options()
            return
        outcome = self._filter_outcome
        if outcome and outcome[0] == "success":
            if self._filter_had_results:
                self.window.prime_page.yield_slot_page.clear_result()
                self.window.prime_page.summary_page.clear_result()
            self.window.prime_page.load_filter_options(outcome[1])
            self._filters_ready = True
            self.window.statusBar().showMessage("Bộ lọc sẵn sàng.", 3000)
            if not self.busy:
                self._resume_search()
        elif outcome:
            self.window.statusBar().showMessage("Không tải được bộ lọc. Bấm SEARCH để thử lại: " + outcome[1])
        # A background result must not unlock an active foreground operation.
        self.window.prime_page.set_filters_ready(not self.busy)

    def _resume_search(self):
        if self._pending_search is None or self.busy or self._closing:
            return
        self._pending_search = None
        force = getattr(self, "_pending_search_force", False)
        self._pending_search_force = False
        # Use controls after options arrive (including their default selection).
        self.load_summary(self.window.prime_page.filter_panel.get_filter_criteria(), force=force)

    @pyqtSlot()
    def start_chart_preload(self):
        """Called after show; only import modules, never construct Qt widgets."""
        if self._closing or self._preload_thread is not None:
            return
        from workers.chart_preload_worker import ChartPreloadWorker
        worker = ChartPreloadWorker()
        thread = QThread(self)
        self._preload_worker, self._preload_thread = worker, thread
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self._preload_finished)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    @pyqtSlot()
    def _preload_finished(self):
        self._preload_thread = self._preload_worker = None
        if self._closing:
            self._finish_close_when_idle()

    @pyqtSlot(object)
    def load_summary(self, criteria, force=False):
        """Chỉ query khi Date/Tier/Model/EQP đổi; chia sẻ vòng đời worker import."""
        if self.window.prime_page.tabs.currentWidget() is self.window.prime_page.report_host:
            self.open_report()
            return
        if self._closing:
            return
        if self.busy or not self._ready:
            self._pending_search = criteria
            self._pending_search_force = force
            return
        if self.window.prime_page.tabs.currentWidget() is self.window.prime_page.file_management_host:
            self.open_file_management()
            return
        if self.window.prime_page.tabs.currentWidget() is self.window.prime_page.send_mail_host:
            self.open_send_mail()
            return
        if (
            self.window.prime_page.tabs.currentWidget()
            is self.window.prime_page.machine_slot_yield_host
        ):
            self.open_machine_slot_yield(refresh=False)
            self.window.prime_page.machine_slot_yield_page.summary.apply_date_range(
                criteria.date_from, criteria.date_to, force=force, show_loading=force)
            return
        if not self._filters_ready:
            self._pending_search = criteria
            self._pending_search_force = force
            if self._filter_thread is None:
                self.refresh_filter_options()
            self.window.statusBar().showMessage("Đang tải bộ lọc; sẽ thực hiện SEARCH khi sẵn sàng.")
            return
        if self.window.prime_page.tabs.currentWidget() is self.window.prime_page.alarm_host:
            self.load_alarm(criteria, force=force)
            return
        if self.window.prime_page.tabs.currentWidget() is self.window.prime_page.dashboard_host:
            self.load_alarm(criteria, force=force)
            return
        key = (criteria.date_from, criteria.date_to,
               tuple(sorted({str(t) for t in criteria.tiers if t is not None})),
               tuple(sorted(set(criteria.models))), criteria.eqp or None)
        if self.window.prime_page.tabs.currentWidget() is self.window.prime_page.yield_slot_page:
            self.load_slot_summary((*key, criteria.slot), criteria.scrap_codes)
            return
        page = self.window.prime_page.summary_page
        page.set_scrap_codes(criteria.scrap_codes)
        if key == self._summary_key:
            try:
                page.set_scrap_codes(criteria.scrap_codes, redraw=True)
            except Exception as error:
                self.dialogs.show_error(str(error))
            return
        self._pending_summary_key = key
        self.dialogs.begin_loading("Loading ...")
        worker = SummaryWorker(self.database_path, key)
        worker.succeeded.connect(self._succeeded)
        self._start(worker, "summary")

    def load_slot_summary(self, key, scrap_codes=()):
        """SEARCH chỉ tải tab Yield Slot đang mở; cache riêng với Summary."""
        page = self.window.prime_page.yield_slot_page
        page.set_scrap_codes(scrap_codes)
        if key == self._slot_key:
            try:
                page.set_scrap_codes(scrap_codes, redraw=True)
            except Exception as error:
                self.dialogs.show_error(str(error))
            return
        self._pending_slot_key = key
        self.dialogs.begin_loading("Loading ...")
        cached_model = (page.model_summary.result
                        if self._slot_key and self._slot_key[:3] == key[:3] else None)
        worker = SlotSummaryWorker(self.database_path, key, cached_model=cached_model)
        worker.succeeded.connect(self._succeeded)
        self._start(worker, "slot")


    @pyqtSlot()
    def open_file_management(self):
        """Tải File Management độc lập bộ lọc thống kê, chỉ sau khởi tạo DB."""
        if self._ready and not self.busy and not self._closing:
            self.window.prime_page.open_file_management(self.database_path)

    def _mark_file_data_changed(self, data_type):
        """Làm mới đúng danh sách sau import PRIME/CUM thành công."""
        machine = self.window.prime_page.machine_slot_yield_page
        if data_type == "PRIME":
            self._alarm_key = None
            if machine is not None:
                machine.summary.invalidate()
                if machine.isVisible():
                    machine.summary.refresh()
        report = self.window.prime_page.report_page
        if data_type == "PRIME" and report is not None:
            report.mark_data_changed()
        page = self.window.prime_page.file_management_page
        if page is not None:
            page.mark_data_changed(data_type)

    def _finish_close_when_idle(self):
        """Đợi cả worker File Management để đóng an toàn chỉ với một lần click."""
        machine = self.window.prime_page.machine_slot_yield_page
        if machine is not None:
            machine.summary.prepare_close()
            if machine.summary.has_running_tasks() or machine.config_thread is not None:
                self.window.setEnabled(False)
                QTimer.singleShot(50, self._finish_close_when_idle)
                return
        page = self.window.prime_page.file_management_page
        mail_page = self.window.prime_page.send_mail_page
        report = self.window.prime_page.report_page
        if report is not None:
            report.prepare_close()
            if report.has_running_tasks():
                self.window.setEnabled(False)
                QTimer.singleShot(50, self._finish_close_when_idle)
                return
        if self.busy or self._filter_thread is not None or self._preload_thread is not None or (page is not None and page.is_busy()) or (mail_page is not None and mail_page.is_busy()):
            self.window.setEnabled(False)
            QTimer.singleShot(50, self._finish_close_when_idle)
            return
        self.window.finish_close()

    @pyqtSlot()
    def open_report(self):
        if self._ready and not self.busy and not self._closing:
            self.window.prime_page.open_report(self.database_path)

    @pyqtSlot()
    def open_send_mail(self):
        """Mở cấu hình mail độc lập From/To/EQP/Model/Tier/Scrap Code."""
        if self._ready and not self.busy and not self._closing:
            self.window.prime_page.open_send_mail(self.database_path)

    @pyqtSlot()
    def open_machine_slot_yield(self, refresh=True):
        """Mở cấu hình Machine Slot Yield độc lập bộ lọc thống kê."""
        if self._ready and not self.busy and not self._closing:
            self.window.prime_page.open_machine_slot_yield(
                self.database_path
            )
            page = self.window.prime_page.machine_slot_yield_page
            if refresh:
                # Match the current controls, including changes made on another tab.
                criteria = self.window.prime_page.filter_panel.get_filter_criteria()
                if criteria is not None:
                    page.summary.apply_date_range(criteria.date_from, criteria.date_to)
                else:
                    page.summary.refresh()

    def load_alarm(self, criteria, force=False):
        """Share loaded date range between Alarm/Dashboard; Search can revalidate."""
        if self.busy or self._closing or not self._ready:
            return
        key = (criteria.date_from, criteria.date_to)
        if not force and key == self._alarm_key:
            return
        self._pending_alarm_key = key
        from workers.alarm_worker import AlarmWorker
        page = self.window.prime_page.ensure_alarm_page()
        dashboard = self.window.prime_page.ensure_dashboard_page()
        page.status_label.setText("Đang tải Alarm...")
        worker = AlarmWorker(self.database_path, (criteria.date_from, criteria.date_to))
        worker.succeeded.connect(self._succeeded)
        self.dialogs.begin_loading("Loading Alarm ...")
        self._start(worker, "alarm")

    @pyqtSlot(object, str, str)
    def save_alarm_tracking(self, expected, field, value):
        """Lưu ô trên worker chung để chặn import chồng và đóng app an toàn."""
        if self.busy or self._closing or not self._ready:
            return
        from workers.alarm_worker import AlarmWorker
        worker = AlarmWorker(self.database_path, edit=(expected, field, value))
        worker.succeeded.connect(self._succeeded)
        self.dialogs.begin_loading("Saving Alarm ...")
        self._start(worker, "alarm_save")

    @pyqtSlot(object)
    def load_alarm_history(self, expected):
        """Dùng worker lifecycle hiện có: không treo UI, đóng app đợi thread an toàn."""
        if self.busy or self._closing or not self._ready:
            return
        from workers.alarm_worker import AlarmWorker
        worker = AlarmWorker(self.database_path, history=expected)
        worker.succeeded.connect(self._succeeded)
        self.dialogs.begin_loading("Loading Slot Fail History ...")
        self._start(worker, "alarm_history")
