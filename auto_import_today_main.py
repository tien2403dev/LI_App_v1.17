from __future__ import annotations

import argparse
import sys
import traceback

from datetime import datetime
from pathlib import Path

from auto_import_main import (
    append_auto_import_log,
    get_default_database_path,
)
from database.schema import (
    initialize_database,
)
from repositories.auto_import_scheduler_repository import (
    AutoImportSchedulerRepository,
)


def parse_arguments() -> argparse.Namespace:
    """Đọc đường dẫn database do Task Scheduler truyền vào."""

    parser = argparse.ArgumentParser(
        description=(
            "Tự động import và thay thế PRIME log "
            "của ngày hiện tại."
        )
    )

    parser.add_argument(
        "--database",
        type=Path,
        default=get_default_database_path(),
    )

    return parser.parse_args()


def run_auto_import_today(
    database_path: Path,
) -> int:
    """
    Import lại toàn bộ log ngày hiện tại mỗi lần được gọi.

    PrimeImportService staging dữ liệu trước, sau đó xóa và ghi lại
    đúng ngày có trong staging trong một transaction. File này không
    dùng last_import_date nên Task Scheduler có thể chạy lặp trong ngày.
    """

    initialize_database(
        database_path
    )

    scheduler_repository = (
        AutoImportSchedulerRepository(
            database_path=database_path
        )
    )

    config = (
        scheduler_repository.get_config()
    )

    if not config.enabled:
        append_auto_import_log(
            "SKIPPED",
            "Auto Import Today đang tắt.",
        )
        return 0

    now = datetime.now()

    configured_time = datetime.strptime(
        config.import_time,
        "%H:%M",
    ).time()

    if now.time() < configured_time:
        append_auto_import_log(
            "SKIPPED",
            (
                "Auto Import Today chưa đến giờ "
                f"{config.import_time}."
            ),
        )
        return 0

    target_date = now.strftime(
        "%Y%m%d"
    )

    if not config.log_folder.strip():
        raise ValueError(
            "Chưa cấu hình Log Folder "
            "cho Auto Import Today."
        )

    log_folder = Path(
        config.log_folder
    )

    append_auto_import_log(
        "INFO",
        (
            "Bắt đầu Auto Import PRIME TODAY | "
            f"Ngày: {target_date} | "
            f"Folder: {log_folder}"
        ),
    )

    # Lazy import: chỉ tải parser/service khi Task Scheduler thực sự chạy import.
    from domain.prime import (
        ValidationError,
    )
    from services.prime_import_service import (
        PrimeImportService,
    )

    service = PrimeImportService(
        database_path=database_path
    )

    try:
        result = service.import_folder(
            root_folder=log_folder,
            business_dates=(target_date,),
        )

    except ValidationError as error:
        # Log hôm nay có thể chưa được tạo/copy tại thời điểm task chạy.
        # Không có staging hợp lệ nên dữ liệu hiện tại không bị xóa.
        if str(error).strip() != (
            "Không tìm thấy file .txt trong các folder "
            "ngày được chọn"
        ):
            raise

        append_auto_import_log(
            "SKIPPED",
            (
                f"Chưa có file PRIME của ngày {target_date}; "
                "bỏ qua và sẽ kiểm tra lại ở lần chạy sau."
            ),
        )

        return 0

    # Không gọi mark_import_succeeded: tiến trình Today phải được phép
    # thay thế dữ liệu hiện tại ở mọi lần Task Scheduler kích hoạt.
    append_auto_import_log(
        "SUCCESS",
        (
            "Auto Import PRIME TODAY hoàn tất | "
            f"Ngày: {target_date} | "
            f"Inserted: {result.inserted} | "
            f"Deleted: {result.deleted} | "
            "TIER đã được đồng bộ."
        ),
    )

    return 0


def main() -> int:
    """Entry point dành riêng cho LI Auto Import Today."""

    arguments = parse_arguments()

    try:
        return run_auto_import_today(
            database_path=(
                arguments.database
            )
        )

    except Exception as error:
        error_message = str(
            error
        ).strip()

        if not error_message:
            error_message = (
                "Auto Import Today thất bại "
                "do lỗi không xác định."
            )

        append_auto_import_log(
            "ERROR",
            (
                "Auto Import PRIME TODAY | "
                f"{error_message}"
            ),
        )

        append_auto_import_log(
            "TRACEBACK",
            traceback.format_exc().rstrip(),
        )

        return 1


if __name__ == "__main__":
    from database.diagnostics import run_entrypoint
    sys.exit(run_entrypoint("auto_import_today_main", main))
