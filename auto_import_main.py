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
from repositories.auto_import_scheduler_repository import (
    AutoImportSchedulerRepository,
)


def get_application_root() -> Path:
    """
    Lấy folder project hoặc folder
    chứa EXE sau khi build.
    """

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
    """
    Lấy database mặc định khi không
    truyền tham số.
    """

    configured_path = os.environ.get(
        "LI_DB_PATH"
    )

    if configured_path:
        return Path(
            configured_path
        )

    from config.paths import DATABASE_PATH
    return DATABASE_PATH


def append_auto_import_log(
    level: str,
    message: str,
) -> None:
    """
    Ghi nối tiếp vào duy nhất một file
    auto_import_log.txt.
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
        / "auto_import_log.txt"
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


def parse_arguments() -> argparse.Namespace:
    """
    Đọc đường dẫn database do
    Task Scheduler truyền vào.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Tự động import PRIME log "
            "của ngày hôm trước."
        )
    )

    parser.add_argument(
        "--database",
        type=Path,
        default=get_default_database_path(),
    )

    return parser.parse_args()


def run_auto_import(
    database_path: Path,
) -> int:
    """
    Kiểm tra cấu hình rồi gọi đúng
    PrimeImportService hiện tại.
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
            "Auto Import đang tắt.",
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
                "Chưa đến giờ Auto Import "
                f"{config.import_time}."
            ),
        )
        return 0

    target_date = (
        now.date()
        - timedelta(days=1)
    ).strftime(
        "%Y%m%d"
    )

    if (
        config.last_import_date
        == target_date
    ):
        append_auto_import_log(
            "SKIPPED",
            (
                f"Ngày {target_date} đã được "
                "Auto Import thành công."
            ),
        )
        return 0

    if not config.log_folder.strip():
        raise ValueError(
            "Chưa cấu hình Log Folder "
            "cho Auto Import."
        )

    log_folder = Path(
        config.log_folder
    )

    append_auto_import_log(
        "INFO",
        (
            "Bắt đầu Auto Import PRIME | "
            f"Ngày: {target_date} | "
            f"Folder: {log_folder}"
        ),
    )

    # Lazy import:
    # Chỉ tải service khi thật sự cần import.
    #
    # Đây chính là service nút Import PRIME
    # hiện tại đang sử dụng.
    from services.prime_import_service import (
        PrimeImportService,
    )
    from domain.prime import (
        ValidationError,
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
        # Không có file của ngày cần lấy là trạng thái bình thường:
        # Task Scheduler có thể chạy trước khi log được tạo/copy xong.
        # Không đánh dấu hoàn thành để lần chạy sau vẫn kiểm tra lại.
        if str(error).strip() != (
            "Không tìm thấy file .txt trong các folder "
            "ngày được chọn"
        ):
            raise

        append_auto_import_log(
            "SKIPPED",
            (
                f"Không có file PRIME của ngày {target_date}; "
                "bỏ qua và sẽ kiểm tra lại ở lần chạy sau."
            ),
        )

        return 0

    # Chỉ cập nhật sau khi PrimeImportService
    # đã hoàn tất và transaction đã commit.
    scheduler_repository.mark_import_succeeded(
        target_date=target_date
    )

    append_auto_import_log(
        "SUCCESS",
        (
            f"Ngày: {target_date} | "
            f"Inserted: "
            f"{result.inserted} | "
            f"Deleted: "
            f"{result.deleted} | "
            "TIER đã được xử lý "
            "theo PrimeImportService hiện tại."
        ),
    )

    return 0


def main() -> int:
    """
    Entry point dành riêng cho
    LIAutoImport.exe.
    """

    arguments = parse_arguments()

    try:
        return run_auto_import(
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
                "Auto Import thất bại "
                "do lỗi không xác định."
            )

        append_auto_import_log(
            "ERROR",
            error_message,
        )

        append_auto_import_log(
            "TRACEBACK",
            traceback.format_exc().rstrip(),
        )

        return 1


if __name__ == "__main__":
    from database.diagnostics import run_entrypoint
    sys.exit(run_entrypoint("auto_import_main", main))
