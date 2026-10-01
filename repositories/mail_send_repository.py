from __future__ import annotations

import uuid

from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, Union
from dataclasses import dataclass
from database.connection import create_connection
@dataclass(frozen=True)
class MailHistorySummary:
    id: int
    alarm_date: str
    sent_at: str
    sender: str
    receivers: str
    cc: str
    result: str


@dataclass(frozen=True)
class MailHistoryDetail:
    id: int
    alarm_date: str
    sent_at: str
    sender: str
    receivers: str
    cc: str
    result: str
    subject: str
    html_content: str

class MailSendRepository:
    """Kiểm tra và lưu các slot đã gửi mail."""

    def __init__(
        self,
        database_path: Union[str, Path],
    ):
        """Giữ đường dẫn database LI dùng chung."""
        self.database_path = Path(
            database_path
        )

    def acquire_send_lock(self) -> str:
        """Chặn hai máy gửi mail cùng lúc."""

        now = datetime.now()
        lock_token = str(uuid.uuid4())

        expires_at = (
            now + timedelta(minutes=5)
        )

        connection = create_connection(
            self.database_path
        )

        try:
            connection.execute(
                "BEGIN IMMEDIATE"
            )

            row = connection.execute(
                """
                SELECT expires_at
                FROM mail_send_lock
                WHERE id = 1
                """
            ).fetchone()

            if row is not None:
                try:
                    current_expiry = (
                        datetime.strptime(
                            str(row["expires_at"]),
                            "%Y-%m-%d %H:%M:%S",
                        )
                    )

                except ValueError:
                    current_expiry = (
                        now + timedelta(minutes=5)
                    )

                if current_expiry > now:
                    connection.rollback()

                    raise RuntimeError(
                        (
                            "Một máy khác đang thực hiện "
                            "gửi mail. Vui lòng thử lại sau."
                        )
                    )

                connection.execute(
                    """
                    DELETE FROM mail_send_lock
                    WHERE id = 1
                    """
                )

            connection.execute(
                """
                INSERT INTO mail_send_lock (
                    id,
                    lock_token,
                    expires_at
                )
                VALUES (1, ?, ?)
                """,
                (
                    lock_token,
                    expires_at.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                ),
            )

            connection.commit()

            return lock_token

        except Exception:
            if connection.in_transaction:
                connection.rollback()

            raise

        finally:
            connection.close()

    def refresh_send_lock(self, lock_token: str) -> None:
        """Gia hạn khóa trước khi gửi; dừng nếu tiến trình khác đã lấy khóa."""
        conn = create_connection(self.database_path)
        try:
            expiry = (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
            cursor = conn.execute(
                "UPDATE mail_send_lock SET expires_at=? WHERE id=1 AND lock_token=?",
                (expiry, lock_token))
            if cursor.rowcount != 1:
                raise RuntimeError("Đã mất khóa gửi mail; dừng để tránh gửi trùng.")
        finally:
            conn.close()

    def release_send_lock(
        self,
        lock_token: str,
    ) -> None:
        """Chỉ tiến trình giữ đúng token mới được mở khóa."""

        connection = create_connection(
            self.database_path
        )

        try:
            connection.execute(
                """
                DELETE FROM mail_send_lock
                WHERE
                    id = 1
                    AND lock_token = ?
                """,
                (lock_token,),
            )

            connection.commit()

        finally:
            connection.close()

    def filter_unsent_alarms(
        self,
        alarms: Iterable[dict],
    ) -> list[dict]:
        """Loại các slot đã gửi theo đúng ngày của Alarm."""

        alarm_list = list(alarms)

        if not alarm_list:
            return []

        alarm_dates = sorted(
            {
                alarm["alarm_date"]
                for alarm in alarm_list
            }
        )

        date_placeholders = ", ".join(
            "?" for _ in alarm_dates
        )

        connection = create_connection(
            self.database_path
        )

        try:
            sent_rows = connection.execute(
                f"""
                SELECT
                    alarm_date,
                    eqp,
                    slot
                FROM mail_slot_send_history
                WHERE alarm_date IN (
                    {date_placeholders}
                )
                """,
                tuple(alarm_dates),
            ).fetchall()

        finally:
            connection.close()

        sent_keys = {
            (
                str(row["alarm_date"]),
                str(row["eqp"]),
                int(row["slot"]),
            )
            for row in sent_rows
        }

        return [
            alarm
            for alarm in alarm_list
            if (
                alarm["alarm_date"],
                alarm["eqp"],
                alarm["slot"],
            ) not in sent_keys
        ]

    def record_successful_mail(
            self,
            target_date: str,
            alarms: Iterable[dict],
            sender: str,
            receivers: str,
            cc: str,
            subject: str,
            html_content: str,
    ) -> int:
        """
        Lưu một email thành công và các slot đã gửi
        trong cùng một transaction.
        """

        alarm_list = list(alarms)

        if not alarm_list:
            raise ValueError(
                "Không có Alarm để lưu lịch sử mail."
            )

        sent_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        slot_rows = [
            (
                alarm_date,
                eqp,
                slot,
                sent_at,
            )
            for alarm_date, eqp, slot in sorted(
                {
                    (
                        alarm["alarm_date"],
                        alarm["eqp"],
                        alarm["slot"],
                    )
                    for alarm in alarm_list
                }
            )
        ]

        connection = create_connection(
            self.database_path
        )

        try:
            connection.execute(
                "BEGIN IMMEDIATE"
            )

            cursor = connection.execute(
                """
                INSERT INTO mail_send_history (
                    alarm_date,
                    sent_at,
                    sender,
                    receivers,
                    cc,
                    result,
                    subject,
                    html_content
                )
                VALUES (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    'Success',
                    ?,
                    ?
                )
                """,
                (
                    target_date,
                    sent_at,
                    sender,
                    receivers,
                    cc,
                    subject,
                    html_content,
                ),
            )

            connection.executemany(
                """
                INSERT INTO
                    mail_slot_send_history (
                        alarm_date,
                        eqp,
                        slot,
                        sent_at
                    )
                VALUES (?, ?, ?, ?)
                """,
                slot_rows,
            )

            connection.commit()

            return int(cursor.lastrowid)

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def get_mail_history(
            self,
            limit: int = 500,
    ) -> list[MailHistorySummary]:
        """Lấy danh sách email thành công mới nhất."""

        limit = max(
            1,
            int(limit),
        )

        connection = create_connection(
            self.database_path
        )

        try:
            rows = connection.execute(
                """
                SELECT
                    id,
                    alarm_date,
                    sent_at,
                    sender,
                    receivers,
                    cc,
                    result
                FROM mail_send_history
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

            return [
                MailHistorySummary(
                    id=int(row["id"]),
                    alarm_date=str(
                        row["alarm_date"]
                    ),
                    sent_at=str(
                        row["sent_at"]
                    ),
                    sender=str(
                        row["sender"]
                    ),
                    receivers=str(
                        row["receivers"]
                    ),
                    cc=str(
                        row["cc"] or ""
                    ),
                    result=str(
                        row["result"]
                    ),
                )
                for row in rows
            ]

        finally:
            connection.close()

    def get_mail_history_detail(
            self,
            history_id: int,
    ) -> MailHistoryDetail:
        """Lấy snapshot đầy đủ của email đã gửi."""

        connection = create_connection(
            self.database_path
        )

        try:
            row = connection.execute(
                """
                SELECT
                    id,
                    alarm_date,
                    sent_at,
                    sender,
                    receivers,
                    cc,
                    result,
                    subject,
                    html_content
                FROM mail_send_history
                WHERE id = ?
                """,
                (history_id,),
            ).fetchone()

            if row is None:
                raise ValueError(
                    (
                        "Không tìm thấy "
                        "Mail History đã chọn."
                    )
                )

            return MailHistoryDetail(
                id=int(row["id"]),
                alarm_date=str(
                    row["alarm_date"]
                ),
                sent_at=str(
                    row["sent_at"]
                ),
                sender=str(
                    row["sender"]
                ),
                receivers=str(
                    row["receivers"]
                ),
                cc=str(
                    row["cc"] or ""
                ),
                result=str(
                    row["result"]
                ),
                subject=str(
                    row["subject"]
                ),
                html_content=str(
                    row["html_content"]
                ),
            )

        finally:
            connection.close()
