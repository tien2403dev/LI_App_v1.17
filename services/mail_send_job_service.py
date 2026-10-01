from __future__ import annotations

from dataclasses import dataclass
from datetime import (
    date,
    datetime,
    timedelta,
)
from pathlib import Path
from typing import (
    Callable,
    Union,
)
from repositories.mail_configuration_repository import (
    MailConfigurationRepository,
)
from repositories.mail_send_repository import (
    MailSendRepository,
)
from repositories.mail_template_repository import (
    MailTemplateRepository,
)
from services.mail_content_builder import (
    MailContentBuilder,
)
from services.mail_service import MailService
from database.diagnostics import event


class NoMailToSendError(Exception):
    """Không có Alarm mới cần gửi."""


@dataclass(frozen=True)
class MailSendJobResult:
    """Kết quả của một lần gửi mail."""

    target_date: str
    target_dates: tuple[str, ...]
    sent_slot_count: int
    receiver_count: int
    cc_count: int


class MailSendJobService:
    """
    Gửi tự động LI qua Task Scheduler, dùng cơ chế chống trùng của Aging.
    """

    CHECK_DAY_COUNT = 2

    def __init__(
        self,
        database_path: Union[str, Path],
    ):
        """Giữ đường dẫn DB chung với ứng dụng LI."""
        self.database_path = Path(
            database_path
        )

    @staticmethod
    def _write_log(
            log_callback: Callable[[str, str], None] | None,
            level: str,
            message: str,
    ) -> None:
        """
        Ghi log nếu caller truyền log_callback.

        Nút Send Mail thủ công không truyền callback
        nên hoàn toàn không bị ảnh hưởng.
        """

        event("MAIL_STAGE", stage=level)
        if log_callback is None:
            return

        try:
            log_callback(
                level,
                message,
            )

        except Exception:
            # Lỗi ghi log không được phép
            # làm hỏng quá trình gửi mail.
            pass

    def run(
            self,
            target_date: str | None = None,
            log_callback: (
                    Callable[[str, str], None]
                    | None
            ) = None,
    ) -> MailSendJobResult:
        """
        Gửi các slot chưa gửi của target_date
        và ba ngày liền trước đó.

        Nếu không truyền target_date thì luôn lấy
        ngày hiện tại.
        """

        if target_date is None:
            target_date = date.today().strftime(
                "%Y%m%d"
            )

        self._validate_target_date(
            target_date
        )

        target_dates = self._build_target_dates(
            target_date
        )

        formatted_target_dates = ", ".join(
            self._format_date(value)
            for value in target_dates
        )

        self._write_log(
            log_callback,
            "INFO",
            (
                "Bắt đầu Mail Send Job | "
                "Các ngày Alarm: "
                f"{formatted_target_dates}"
            ),
        )

        mail_service = MailService()

        send_repository = MailSendRepository(
            self.database_path
        )

        lock_token = None

        try:
            # Chặn các task gửi đồng thời trên cùng database.
            lock_token = (
                send_repository
                .acquire_send_lock()
            )

            config_repository = (
                MailConfigurationRepository(
                    self.database_path
                )
            )

            sender = (
                config_repository
                .get_enabled_sender()
            )

            if sender is None:
                self._write_log(
                    log_callback,
                    "ERROR",
                    "Không có Sender nào được Enable.",
                )

                raise ValueError(
                    (
                        "Chưa có Sender nào "
                        "được Enable."
                    )
                )

            if not sender.password:
                self._write_log(
                    log_callback,
                    "ERROR",
                    (
                        "Sender chưa có mật khẩu | "
                        f"User ID: {sender.user_id}"
                    ),
                )

                raise ValueError(
                    (
                        "Sender đang Enable "
                        "chưa có mật khẩu."
                    )
                )

            recipients = (
                config_repository
                .get_recipients()
            )

            receivers = [
                (
                    recipient.user_id,
                    recipient.display_name,
                )
                for recipient in recipients
                if (
                    recipient.recipient_type
                    == "RECEIVER"
                )
            ]

            cc_receivers = [
                (
                    recipient.user_id,
                    recipient.display_name,
                )
                for recipient in recipients
                if (
                    recipient.recipient_type
                    == "CC"
                )
            ]
            receiver_log = ", ".join(
                self._format_person(
                    user_id,
                    display_name,
                )
                for (
                    user_id,
                    display_name,
                ) in receivers
            )

            cc_log = ", ".join(
                self._format_person(
                    user_id,
                    display_name,
                )
                for (
                    user_id,
                    display_name,
                ) in cc_receivers
            )

            self._write_log(
                log_callback,
                "INFO",
                (
                    "Receiver | "
                    f"{receiver_log or 'Không có'}"
                ),
            )

            self._write_log(
                log_callback,
                "INFO",
                (
                    "CC | "
                    f"{cc_log or 'Không có'}"
                ),
            )

            if not receivers:
                raise ValueError(
                    (
                        "Chưa có người nhận "
                        "loại Receiver."
                    )
                )

            template_repository = (
                MailTemplateRepository(
                    self.database_path
                )
            )

            template = (
                template_repository
                .get_template()
            )

            alarms = (
                template_repository
                .get_alarm_previews(
                    target_dates
                )
            )
            self._write_log(
                log_callback,
                "INFO",
                (
                    "Kiểm tra Slot Fail Alarm | "
                    f"Tìm thấy: {len(alarms)} Alarm record"
                ),
            )

            if not alarms:
                self._write_log(
                    log_callback,
                    "SKIP",
                    (
                        "Không có Slot Fail Alarm | "
                        "Các ngày: "
                        f"{formatted_target_dates}"
                    ),
                )

                raise NoMailToSendError(
                    (
                        "Không có Slot Fail Alarm "
                        "trong các ngày "
                        f"{formatted_target_dates}."
                    )
                )

            unsent_alarms = (
                send_repository
                .filter_unsent_alarms(
                    alarms=alarms,
                )
            )
            unsent_keys = {
                (
                    alarm["alarm_date"],
                    alarm["eqp"],
                    alarm["slot"],
                )
                for alarm in unsent_alarms
            }

            all_keys = {
                (
                    alarm["alarm_date"],
                    alarm["eqp"],
                    alarm["slot"],
                )
                for alarm in alarms
            }

            skipped_keys = (
                    all_keys
                    - unsent_keys
            )

            for alarm_date, eqp, slot in sorted(
                    skipped_keys
            ):
                self._write_log(
                    log_callback,
                    "SKIP SLOT",
                    (
                        "Ngày: "
                        f"{self._format_date(alarm_date)} | "
                        f"EQP: {eqp} | "
                        f"Slot: {slot} | "
                        "Đã gửi trước đó -> bỏ qua"
                    ),
                )

            if not unsent_alarms:
                raise NoMailToSendError(
                    (
                        "Tất cả Slot Fail Alarm "
                        "trong các ngày "
                        f"{formatted_target_dates} "
                        "đã được gửi trước đó."
                    )
                )

            from html import escape
            body = MailContentBuilder.build_alarm_body_html(
                target_dates=target_dates, alarms=unsent_alarms)
            html = ("<p>" + escape(template.heading).replace("\n", "<br>") + "</p>"
                    + body + "<p>" + escape(template.closing).replace("\n", "<br>") + "</p>")
            text = self._plain_text(html)

            self._write_log(
                log_callback,
                "LOGIN",
                (
                    "Bắt đầu đăng nhập hệ thống mail | "
                    f"Sender: {sender.user_id}"
                ),
            )

            login_success, login_detail = (
                mail_service.login(
                    user_id=sender.user_id,
                    password=sender.password,
                )
            )

            if not login_success:
                self._write_log(
                    log_callback,
                    "LOGIN FAILED",
                    (
                        f"Sender: {sender.user_id} | "
                        f"Reason: {login_detail}"
                    ),
                )

                raise RuntimeError(
                    str(login_detail)
                )

            self._write_log(
                log_callback,
                "LOGIN SUCCESS",
                (
                    "Đăng nhập thành công"
                    # f"User ID: {login_detail.user_id} | "
                    # f"Employee No: "
                    # f"{login_detail.employee_no} | "
                    # f"Name: "
                    # f"{login_detail.name_vn or login_detail.name_en}"
                ),
            )

            if mail_service.user_info is None:
                raise RuntimeError("Không có thông tin Sender sau khi đăng nhập.")
            send_repository.refresh_send_lock(lock_token)
            send_success, send_detail = (
                mail_service.send_mail(
                    receivers=receivers,
                    cc_receivers=cc_receivers,
                    subject=template.subject,
                    html=html,
                    text=text,
                )
            )

            if not send_success:
                self._write_log(
                    log_callback,
                    "SEND FAILED",
                    (
                        "Gửi mail thất bại | "
                        f"Sender: {sender.user_id} | "
                        f"Reason: {send_detail}"
                    ),
                )

                raise RuntimeError(
                    str(send_detail)
                )

            self._write_log(
                log_callback,
                "SEND SUCCESS",
                (
                    "Hệ thống mail xác nhận gửi thành công"
                    # f"Sender: {sender.user_id}"
                ),
            )

            if mail_service.user_info is None:
                raise RuntimeError(
                    (
                        "Không có thông tin Sender "
                        "sau khi đăng nhập."
                    )
                )

            sender_name = (
                mail_service.user_info.name_vn
                or mail_service.user_info.name_en
                or sender.display_name
            )

            sender_snapshot = (
                self._format_person(
                    mail_service.user_info.user_id,
                    sender_name,
                )
            )

            receiver_snapshot = ", ".join(
                self._format_person(
                    user_id,
                    display_name,
                )
                for (
                    user_id,
                    display_name,
                ) in receivers
            )

            cc_snapshot = ", ".join(
                self._format_person(
                    user_id,
                    display_name,
                )
                for (
                    user_id,
                    display_name,
                ) in cc_receivers
            )

            # Mail History và danh sách slot
            # được lưu cùng một transaction.
            try:
                send_repository.record_successful_mail(
                    target_date=target_date,
                    alarms=unsent_alarms,
                    sender=sender_snapshot,
                    receivers=receiver_snapshot,
                    cc=cc_snapshot,
                    subject=template.subject,
                    html_content=html,
                )
            except Exception:
                self._write_log(log_callback, "CRITICAL",
                    "Mail đã được hệ thống xác nhận gửi nhưng lưu lịch sử thất bại. "
                    "Cần đối chiếu mail đã gửi trước lần chạy tiếp theo để tránh gửi lại.")
                raise


            sent_slot_count = len(
                {
                    (
                        alarm["alarm_date"],
                        alarm["eqp"],
                        alarm["slot"],
                    )
                    for alarm in unsent_alarms
                }
            )

            return MailSendJobResult(
                target_date=target_date,
                target_dates=tuple(target_dates),
                sent_slot_count=sent_slot_count,
                receiver_count=len(receivers),
                cc_count=len(cc_receivers),
            )

        finally:
            mail_service.clear_session()

            if lock_token is not None:
                try:
                    send_repository.release_send_lock(
                        lock_token
                    )

                except Exception:
                    # Lock tự hết hạn sau 5 phút.
                    pass

    @staticmethod
    def _plain_text(html: str) -> str:
        """Tạo nội dung text cùng dữ liệu với HTML, không phụ thuộc Qt."""
        from html.parser import HTMLParser

        class TextParser(HTMLParser):
            """Giữ nội dung ô bảng và xuống dòng cho bản text."""
            def __init__(self):
                """Khởi tạo bộ đệm văn bản."""
                super().__init__(convert_charrefs=True)
                self.parts = []

            def handle_data(self, data):
                """Giữ nguyên ký tự tiếng Việt và dữ liệu đã giải escape."""
                self.parts.append(data)

            def handle_endtag(self, tag):
                """Ngăn các ô và các hàng dính vào nhau."""
                if tag in ('p', 'tr', 'div'):
                    self.parts.append("\n")
                elif tag in ('td', 'th'):
                    self.parts.append("\t")

            def handle_starttag(self, tag, attrs):
                """Giữ xuống dòng trong heading/closing."""
                if tag == 'br':
                    self.parts.append("\n")

        parser = TextParser()
        parser.feed(html)
        parser.close()
        return ''.join(parser.parts).strip()

    @staticmethod
    def _build_target_dates(
        target_date: str,
    ) -> list[str]:
        """Tạo target_date và ba ngày liền trước."""

        anchor_date = datetime.strptime(
            target_date,
            "%Y%m%d",
        ).date()

        return [
            (
                anchor_date
                - timedelta(days=day_offset)
            ).strftime("%Y%m%d")
            for day_offset in range(
                MailSendJobService.CHECK_DAY_COUNT
            )
        ]

    @staticmethod
    def _format_person(
        user_id: str,
        display_name: str,
    ) -> str:
        """Tạo snapshot người gửi/nhận cho lịch sử."""
        user_id = str(
            user_id or ""
        ).strip()

        display_name = str(
            display_name or ""
        ).strip()

        if display_name:
            return (
                f"{display_name}"
                f"({user_id})"
            )

        return user_id

    @staticmethod
    def _format_date(
        value: str,
    ) -> str:
        """Hiển thị ngày alarm trong log."""
        return (
            f"{value[6:8]}/"
            f"{value[4:6]}/"
            f"{value[0:4]}"
        )

    @staticmethod
    def _validate_target_date(
        value: str,
    ) -> None:
        """Kiểm tra ngày đầu vào đúng yyyyMMdd."""
        try:
            parsed = datetime.strptime(
                value,
                "%Y%m%d",
            )

            if (
                parsed.strftime("%Y%m%d")
                != value
            ):
                raise ValueError

        except ValueError as error:
            raise ValueError(
                (
                    "Ngày gửi mail phải có "
                    "dạng yyyyMMdd."
                )
            ) from error
