from __future__ import annotations

import sqlite3

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Union

from database.connection import create_connection


RECIPIENT_TYPES = (
    "RECEIVER",
    "CC",
    "NONE",
)


@dataclass(frozen=True)
class MailSender:
    id: int
    user_id: str
    display_name: str
    password: str
    enabled: bool


@dataclass(frozen=True)
class MailRecipient:
    id: int
    user_id: str
    display_name: str
    recipient_type: str


class MailConfigurationRepository:
    """Quản lý sender và receiver của chức năng gửi mail."""

    def __init__(
        self,
        database_path: Union[str, Path],
    ):
        """Khởi tạo đối tượng và các thành phần liên quan."""
        self.database_path = Path(
            database_path
        )

    def get_senders(self) -> list[MailSender]:
        """Đọc danh sách Sender, ưu tiên tài khoản được Enable."""
        connection = create_connection(
            self.database_path
        )

        try:
            rows = connection.execute(
                """
                SELECT
                    id,
                    user_id,
                    display_name,
                    password,
                    enabled
                FROM mail_sender
                ORDER BY
                    enabled DESC,
                    display_name COLLATE NOCASE,
                    id
                """
            ).fetchall()

            return [
                MailSender(
                    id=int(row["id"]),
                    user_id=str(row["user_id"]),
                    display_name=str(
                        row["display_name"]
                    ),
                    password=str(
                        row["password"] or ""
                    ),
                    enabled=bool(row["enabled"]),
                )
                for row in rows
            ]

        finally:
            connection.close()

    def get_enabled_sender(
            self,
    ) -> MailSender | None:
        """Lấy tài khoản Sender đang được Enable."""

        connection = create_connection(
            self.database_path
        )

        try:
            row = connection.execute(
                """
                SELECT
                    id,
                    user_id,
                    display_name,
                    password,
                    enabled
                FROM mail_sender
                WHERE enabled = 1
                LIMIT 1
                """
            ).fetchone()

            if row is None:
                return None

            return MailSender(
                id=int(row["id"]),
                user_id=str(row["user_id"]),
                display_name=str(
                    row["display_name"]
                ),
                password=str(
                    row["password"] or ""
                ),
                enabled=bool(row["enabled"]),
            )

        finally:
            connection.close()
    def add_sender(
            self,
            user_id: str,
            display_name: str,
            password: str,
            enabled: bool,
    ) -> int:
        """Kiểm tra và thêm Sender; tắt Sender cũ nếu bật tài khoản mới."""
        user_id, display_name = (
            self._validate_person(
                user_id=user_id,
                display_name=display_name,
            )
        )

        if not password:
            raise ValueError(
                "Password không được để trống."
            )

        connection = create_connection(
            self.database_path
        )

        try:
            connection.execute(
                "BEGIN IMMEDIATE"
            )

            now = self._now()

            if enabled:
                connection.execute(
                    """
                    UPDATE mail_sender
                    SET
                        enabled = 0,
                        updated_at = ?
                    WHERE enabled = 1
                    """,
                    (now,),
                )

            cursor = connection.execute(
                """
                INSERT INTO mail_sender (
                    user_id,
                    display_name,
                    password,
                    enabled,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    display_name,
                    password,
                    int(enabled),
                    now,
                    now,
                ),
            )

            connection.commit()

            return int(cursor.lastrowid)

        except sqlite3.IntegrityError as error:
            connection.rollback()
            self._raise_integrity_error(error)

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def set_sender_enabled(
        self,
        sender_id: int,
        enabled: bool,
    ) -> None:
        """Đổi Enable trong một transaction, bảo đảm tối đa một Sender hoạt động."""
        connection = create_connection(
            self.database_path
        )

        try:
            connection.execute(
                "BEGIN IMMEDIATE"
            )

            now = self._now()

            if enabled:
                connection.execute(
                    """
                    UPDATE mail_sender
                    SET
                        enabled = 0,
                        updated_at = ?
                    WHERE enabled = 1
                    """,
                    (now,),
                )

            cursor = connection.execute(
                """
                UPDATE mail_sender
                SET
                    enabled = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    int(enabled),
                    now,
                    sender_id,
                ),
            )

            if cursor.rowcount != 1:
                raise ValueError(
                    "Sender không còn tồn tại."
                )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def delete_sender(
        self,
        sender_id: int,
    ) -> None:
        """Xóa Sender theo ID."""
        self._delete_by_id(
            table_name="mail_sender",
            record_id=sender_id,
        )

    def get_recipients(
            self,
    ) -> list[MailRecipient]:
        """Đọc người nhận theo loại Receiver/CC/None và tên."""
        connection = create_connection(
            self.database_path
        )

        try:
            rows = connection.execute(
                """
                SELECT
                    id,
                    user_id,
                    display_name,
                    recipient_type
                FROM mail_recipient
                ORDER BY
                    CASE recipient_type
                        WHEN 'RECEIVER' THEN 1
                        WHEN 'CC' THEN 2
                        ELSE 3
                    END,
                    display_name COLLATE NOCASE,
                    id
                """
            ).fetchall()

            return [
                MailRecipient(
                    id=int(row["id"]),
                    user_id=str(row["user_id"]),
                    display_name=str(
                        row["display_name"]
                    ),
                    recipient_type=str(
                        row["recipient_type"]
                    ),
                )
                for row in rows
            ]

        finally:
            connection.close()

    def add_recipient(
            self,
            user_id: str,
            display_name: str,
            recipient_type: str,
    ) -> int:
        """Kiểm tra và thêm người nhận, từ chối User ID trùng."""
        user_id, display_name = (
            self._validate_person(
                user_id=user_id,
                display_name=display_name,
            )
        )

        recipient_type = (
            self._validate_recipient_type(
                recipient_type
            )
        )

        connection = create_connection(
            self.database_path
        )

        try:
            connection.execute(
                "BEGIN IMMEDIATE"
            )

            now = self._now()

            cursor = connection.execute(
                """
                INSERT INTO mail_recipient (
                    user_id,
                    display_name,
                    recipient_type,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    display_name,
                    recipient_type,
                    now,
                    now,
                ),
            )

            connection.commit()

            return int(cursor.lastrowid)

        except sqlite3.IntegrityError as error:
            connection.rollback()
            self._raise_integrity_error(error)

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def update_recipient_type(
        self,
        recipient_id: int,
        recipient_type: str,
    ) -> None:
        """Lưu loại Receiver, CC hoặc None cho đúng ID người nhận."""
        recipient_type = (
            self._validate_recipient_type(
                recipient_type
            )
        )

        connection = create_connection(
            self.database_path
        )

        try:
            cursor = connection.execute(
                """
                UPDATE mail_recipient
                SET
                    recipient_type = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    recipient_type,
                    self._now(),
                    recipient_id,
                ),
            )

            if cursor.rowcount != 1:
                raise ValueError(
                    "Người nhận không còn tồn tại."
                )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def delete_recipient(
        self,
        recipient_id: int,
    ) -> None:
        """Xóa người nhận theo ID."""
        self._delete_by_id(
            table_name="mail_recipient",
            record_id=recipient_id,
        )

    def _delete_by_id(
        self,
        table_name: str,
        record_id: int,
    ) -> None:
        """Xóa đúng bản ghi trong bảng cấu hình được cho phép."""
        allowed_tables = {
            "mail_sender",
            "mail_recipient",
        }

        if table_name not in allowed_tables:
            raise ValueError(
                "Tên bảng không hợp lệ."
            )

        connection = create_connection(
            self.database_path
        )

        try:
            cursor = connection.execute(
                f"""
                DELETE FROM {table_name}
                WHERE id = ?
                """,
                (record_id,),
            )

            if cursor.rowcount != 1:
                raise ValueError(
                    "Dữ liệu không còn tồn tại."
                )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    @staticmethod
    def _validate_person(
        user_id: str,
        display_name: str,
    ) -> tuple[str, str]:
        """Loại bỏ khoảng trắng và kiểm tra User ID, Name bắt buộc."""
        user_id = user_id.strip()
        display_name = display_name.strip()

        if not user_id:
            raise ValueError(
                "User ID không được để trống."
            )

        if not display_name:
            raise ValueError(
                "Name không được để trống."
            )

        return user_id, display_name

    @staticmethod
    def _validate_recipient_type(
        recipient_type: str,
    ) -> str:
        """Chuẩn hóa và kiểm tra loại Receiver/CC/None."""
        recipient_type = (
            recipient_type.strip().upper()
        )

        if recipient_type not in RECIPIENT_TYPES:
            raise ValueError(
                "Recipient Type không hợp lệ."
            )

        return recipient_type

    @staticmethod
    def _raise_integrity_error(
        error: sqlite3.IntegrityError,
    ) -> None:
        """Chuyển lỗi ràng buộc SQLite thành thông báo dễ hiểu."""
        error_text = str(error).lower()

        if "user_id" in error_text:
            raise ValueError(
                "User ID này đã tồn tại."
            ) from error

        raise ValueError(
            f"Dữ liệu không hợp lệ: {error}"
        ) from error

    @staticmethod
    def _now() -> str:
        """Lấy thời điểm hiện tại để ghi nhận thay đổi."""
        return datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )