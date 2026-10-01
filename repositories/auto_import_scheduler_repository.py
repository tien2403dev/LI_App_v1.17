from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Union

from database.connection import create_connection


@dataclass(frozen=True)
class AutoImportSchedulerConfig:
    """Cấu hình Auto Import lưu trong database."""

    enabled: bool
    import_time: str
    log_folder: str
    last_import_date: str | None


class AutoImportSchedulerRepository:
    """Đọc và cập nhật cấu hình Auto Import."""

    CONFIG_ID = 1

    def __init__(
        self,
        database_path: Union[str, Path],
    ):
        self.database_path = Path(
            database_path
        )

    def get_config(
        self,
    ) -> AutoImportSchedulerConfig:
        """Đọc dòng cấu hình có id bằng 1."""

        connection = create_connection(
            self.database_path
        )

        try:
            row = connection.execute(
                """
                SELECT
                    enable_auto_import,
                    import_time,
                    log_folder,
                    last_import_date
                FROM auto_import_scheduler
                WHERE id = ?
                """,
                (self.CONFIG_ID,),
            ).fetchone()

            if row is None:
                raise RuntimeError(
                    "Không tìm thấy cấu hình "
                    "Auto Import trong database."
                )

            return AutoImportSchedulerConfig(
                enabled=bool(
                    row["enable_auto_import"]
                ),
                import_time=row["import_time"],
                log_folder=row["log_folder"],
                last_import_date=(
                    row["last_import_date"]
                ),
            )

        finally:
            connection.close()

    def save_config(
        self,
        enabled: bool,
        import_time: str,
        log_folder: str,
    ) -> None:
        """
        Lưu cấu hình.

        Không thay đổi last_import_date khi người dùng
        bấm Save Configuration.
        """

        self._validate_import_time(
            import_time
        )

        connection = create_connection(
            self.database_path
        )

        try:
            connection.execute(
                """
                UPDATE auto_import_scheduler
                SET
                    enable_auto_import = ?,
                    import_time = ?,
                    log_folder = ?
                WHERE id = ?
                """,
                (
                    int(enabled),
                    import_time,
                    log_folder.strip(),
                    self.CONFIG_ID,
                ),
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def mark_import_succeeded(
        self,
        target_date: str,
    ) -> None:
        """
        Lưu ngày log sau khi toàn bộ quá trình
        import PRIME thành công.
        """

        self._validate_business_date(
            target_date
        )

        connection = create_connection(
            self.database_path
        )

        try:
            connection.execute(
                """
                UPDATE auto_import_scheduler
                SET last_import_date = ?
                WHERE id = ?
                """,
                (
                    target_date,
                    self.CONFIG_ID,
                ),
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    @staticmethod
    def _validate_import_time(
        import_time: str,
    ) -> None:
        """Kiểm tra giờ theo định dạng HH:mm."""

        try:
            parsed_time = datetime.strptime(
                import_time,
                "%H:%M",
            )

            if (
                len(import_time) != 5
                or parsed_time.strftime(
                    "%H:%M"
                ) != import_time
            ):
                raise ValueError

        except ValueError as error:
            raise ValueError(
                "Import Time phải có định dạng HH:mm."
            ) from error

    @staticmethod
    def _validate_business_date(
        business_date: str,
    ) -> None:
        """Kiểm tra ngày theo định dạng yyyyMMdd."""

        try:
            parsed_date = datetime.strptime(
                business_date,
                "%Y%m%d",
            )

            if (
                len(business_date) != 8
                or parsed_date.strftime(
                    "%Y%m%d"
                ) != business_date
            ):
                raise ValueError

        except ValueError as error:
            raise ValueError(
                "Ngày import phải có định dạng yyyyMMdd."
            ) from error