from __future__ import annotations

import argparse
import os
import os
import sys
import traceback

from datetime import (
    datetime,
    timedelta,
)
from pathlib import Path

from database.schema import (
    initialize_database,
)
from repositories.auto_send_mail_scheduler_repository import (
    AutoSendMailSchedulerRepository,
)


def get_application_root() -> Path:
    """Lấy folder project hoặc folder chứa EXE."""

    if getattr(
        sys,
        "frozen",
        False,
    ):
        return (
            Path(sys.executable)
            .resolve()
            .parent
        )

    return (
        Path(__file__)
        .resolve()
        .parent
    )


def get_default_database_path() -> Path:
    """Lấy database mặc định."""

    configured_path = os.environ.get(
        "LI_DB_PATH"
    )

    if configured_path:
        return Path(
            configured_path
        )

    from config.paths import DATABASE_PATH
    return DATABASE_PATH


def append_auto_send_log(
    level: str,
    message: str,
) -> None:
    """
    Ghi log Auto Send Mail.

    Format:
    YYYY-MM-DD HH:MM:SS | LEVEL | message
    """

    log_folder = (
        get_application_root()
        / "log"
    )

    log_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_path = (
        log_folder
        / "auto_send_mail_log.txt"
    )

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    with log_path.open(
        "a",
        encoding="utf-8",
    ) as log_file:
        log_file.write(
            f"{timestamp} | "
            f"{level} | "
            f"[PID={os.getpid()}] {message}\n"
        )


def append_separator() -> None:
    """Tạo dòng phân cách giữa các lần Task chạy."""

    append_auto_send_log(
        "START",
        "=" * 80,
    )


def format_log_value(
    value,
) -> str:
    """
    Chuyển các kiểu dữ liệu khác nhau
    thành chuỗi phù hợp để ghi log.
    """

    if value is None:
        return "N/A"

    if isinstance(
        value,
        (list, tuple, set),
    ):
        if not value:
            return "N/A"

        return ", ".join(
            str(item)
            for item in value
        )

    text = str(
        value
    ).strip()

    if not text:
        return "N/A"

    return text


def get_result_value(
    result,
    *attribute_names: str,
):
    """
    Thử lấy một field từ result.

    Dùng nhiều tên để không làm hỏng chương trình
    nếu MailSendJobResult hiện tại chưa có
    đầy đủ các field sender / receiver / cc.
    """

    for attribute_name in attribute_names:
        if hasattr(
            result,
            attribute_name,
        ):
            value = getattr(
                result,
                attribute_name,
            )

            if value is not None:
                return value

    return None


def parse_arguments() -> argparse.Namespace:
    """Đọc tùy chọn database dành cho Task Scheduler."""
    parser = argparse.ArgumentParser(
        description=(
            "Tự động gửi Slot Fail Alarm "
            "của ngày hiện tại và ba ngày liền trước."
        )
    )

    parser.add_argument(
        "--database",
        type=Path,
        default=get_default_database_path(),
    )

    return parser.parse_args()


def run_auto_send_mail(
    database_path: Path,
) -> int:

    """Kiểm tra Enable/giờ gửi và chạy job LI không mở giao diện."""
    append_separator()
    if not Path(database_path).is_file():
        raise FileNotFoundError(f"Không tìm thấy database LI: {database_path}")

    # ============================================================
    # INITIALIZE DATABASE
    # ============================================================

    initialize_database(
        database_path
    )

    scheduler_repository = (
        AutoSendMailSchedulerRepository(
            database_path
        )
    )

    config = (
        scheduler_repository.get_config()
    )

    enabled_text = (
        "ON"
        if config.enabled
        else "OFF"
    )

    append_auto_send_log(
        "CONFIG",
        (
            f"Enable: {enabled_text} | "
            f"Send Time: {config.send_time}"
        ),
    )

    # ============================================================
    # CHECK ENABLE
    # ============================================================

    # Chỉ file Task Scheduler kiểm tra Enable.
    # Nút Send Mail không gọi đoạn này.
    if not config.enabled:

        append_auto_send_log(
            "SKIP",
            (
                "Auto Send Mail đang OFF. "
                "Không thực hiện gửi mail."
            ),
        )

        append_auto_send_log(
            "END",
            "Kết thúc Task - không gửi mail.",
        )

        return 0

    # ============================================================
    # CHECK SEND TIME
    # ============================================================

    now = datetime.now()

    configured_time = datetime.strptime(
        config.send_time,
        "%H:%M",
    ).time()

    append_auto_send_log(
        "INFO",
        (
            "Thời gian hiện tại: "
            f"{now.strftime('%H:%M:%S')} | "
            "Thời gian cấu hình: "
            f"{configured_time.strftime('%H:%M')}"
        ),
    )

    # Chưa đến giờ thì thoát, không gửi.
    if now.time() < configured_time:

        append_auto_send_log(
            "SKIP",
            (
                "Chưa đến giờ gửi mail theo cấu hình. "
                f"Current: {now.strftime('%H:%M:%S')} | "
                f"Configured: "
                f"{configured_time.strftime('%H:%M')}"
            ),
        )

        append_auto_send_log(
            "END",
            "Kết thúc Task - chưa đến giờ gửi.",
        )

        return 0

    # ============================================================
    # TARGET DATES
    # ============================================================

    target_date = now.date().strftime(
        "%Y%m%d"
    )

    target_dates = [
        (
            now.date()
            - timedelta(days=day_offset)
        ).strftime("%Y%m%d")
        for day_offset in range(2)
    ]

    target_dates_text = ", ".join(
        target_dates
    )

    append_auto_send_log(
        "INFO",
        (
            "Đã đến giờ gửi mail. "
            "Các ngày Alarm cần kiểm tra: "
            f"{target_dates_text}"
        ),
    )

    # ============================================================
    # LAZY IMPORT MAIL SERVICE
    # ============================================================

    append_auto_send_log(
        "INFO",
        "Bắt đầu tải Mail Send Service.",
    )

    # Chỉ import cơ chế gửi khi đã đến giờ.
    from services.mail_send_job_service import (
        MailSendJobService,
        NoMailToSendError,
    )

    append_auto_send_log(
        "INFO",
        "Mail Send Service đã tải xong.",
    )

    # ============================================================
    # RUN SEND MAIL
    # ============================================================

    append_auto_send_log(
        "SEND",
        (
            "Bắt đầu kiểm tra Alarm "
            "và gửi chung một mail cho các ngày "
            f"{target_dates_text}."
        ),
    )

    try:
        result = MailSendJobService(
            database_path
        ).run(
            target_date=target_date,
            log_callback=append_auto_send_log,
        )

    except NoMailToSendError as error:

        error_detail = str(
            error
        ).strip()

        if not error_detail:
            error_detail = (
                "Không có Alarm cần gửi hoặc "
                "tất cả slot trong bốn ngày kiểm tra "
                "đã được gửi trước đó."
            )

        append_auto_send_log(
            "SKIP",
            (
                "Các ngày Alarm: "
                f"{target_dates_text} | "
                f"{error_detail}"
            ),
        )

        append_auto_send_log(
            "INFO",
            (
                "Không tạo mail mới. "
                "Có thể không có Alarm hoặc "
                "các slot Alarm đã tồn tại trong "
                "Mail History nên được bỏ qua."
            ),
        )

        append_auto_send_log(
            "END",
            "Kết thúc Task - không có mail cần gửi.",
        )

        return 0

    # ============================================================
    # READ RESULT INFORMATION
    # ============================================================

    sender = get_result_value(
        result,
        "sender_email",
        "sender",
        "sender_address",
    )

    receivers = get_result_value(
        result,
        "receiver_emails",
        "receivers",
        "receiver",
        "to_emails",
    )

    cc_list = get_result_value(
        result,
        "cc_emails",
        "cc_list",
        "cc",
    )

    sender_text = format_log_value(
        sender
    )

    receiver_text = format_log_value(
        receivers
    )

    cc_text = format_log_value(
        cc_list
    )

    # ============================================================
    # SUCCESS LOG
    # ============================================================

    append_auto_send_log(
        "SUCCESS",
        (
            "Gửi mail thành công | "
            "Các ngày Alarm: "
            f"{', '.join(result.target_dates)} | "
            f"Slot đã gửi: {result.sent_slot_count} | "
            f"Receiver count: {result.receiver_count} | "
            f"CC count: {result.cc_count}"
        ),
    )

    append_auto_send_log("END", "Kết thúc Task - gửi mail thành công.")
    return 0


def main() -> int:
    """Trả mã 0 khi thành công/bỏ qua, 1 khi lỗi; ghi log chi tiết."""
    arguments = parse_arguments()

    try:
        return run_auto_send_mail(
            database_path=arguments.database
        )

    except Exception as error:

        error_message = str(
            error
        ).strip()

        if not error_message:
            error_message = (
                "Auto Send Mail thất bại."
            )

        append_auto_send_log(
            "ERROR",
            (
                "Auto Send Mail thất bại | "
                f"{error_message}"
            ),
        )

        append_auto_send_log(
            "TRACEBACK",
            traceback.format_exc().rstrip(),
        )

        append_auto_send_log(
            "END",
            "Kết thúc Task với lỗi.",
        )

        return 1


if __name__ == "__main__":
    from database.diagnostics import run_entrypoint
    sys.exit(run_entrypoint("auto_send_mail_main", main))
