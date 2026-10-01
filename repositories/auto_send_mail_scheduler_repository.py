from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Union

from database.connection import create_connection


@dataclass(frozen=True)
class AutoSendMailSchedulerConfig:
    """Cấu hình Auto Send Mail."""

    enabled: bool
    send_time: str


class AutoSendMailSchedulerRepository:
    """Đọc và lưu cấu hình Auto Send Mail."""

    CONFIG_ID = 1

    def __init__(
        self,
        database_path: Union[str, Path],
    ):
        """Khởi tạo đối tượng và các thành phần liên quan."""
        self.database_path = Path(
            database_path
        )

    def get_config(
        self,
    ) -> AutoSendMailSchedulerConfig:
        """Đọc cấu hình id bằng 1."""

        connection = create_connection(
            self.database_path
        )

        try:
            row = connection.execute(
                """
                SELECT
                    enable_auto_send,
                    send_time
                FROM auto_send_mail_scheduler
                WHERE id = ?
                """,
                (self.CONFIG_ID,),
            ).fetchone()

            if row is None:
                raise RuntimeError(
                    (
                        "Không tìm thấy cấu hình "
                        "Auto Send Mail."
                    )
                )

            return AutoSendMailSchedulerConfig(
                enabled=bool(
                    row["enable_auto_send"]
                ),
                send_time=str(
                    row["send_time"]
                ),
            )

        finally:
            connection.close()

    def save_config(
        self,
        enabled: bool,
        send_time: str,
    ) -> None:
        """Chỉ lưu database, không tạo Task Scheduler."""

        self._validate_send_time(
            send_time
        )

        connection = create_connection(
            self.database_path
        )

        try:
            connection.execute(
                """
                UPDATE auto_send_mail_scheduler
                SET
                    enable_auto_send = ?,
                    send_time = ?
                WHERE id = ?
                """,
                (
                    int(enabled),
                    send_time,
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
    def _validate_send_time(
        send_time: str,
    ) -> None:
        """Kiểm tra định dạng HH:mm."""

        try:
            parsed_time = datetime.strptime(
                send_time,
                "%H:%M",
            )

            if (
                len(send_time) != 5
                or parsed_time.strftime(
                    "%H:%M"
                ) != send_time
            ):
                raise ValueError

        except ValueError as error:
            raise ValueError(
                (
                    "Send Time phải có "
                    "định dạng HH:mm."
                )
            ) from error