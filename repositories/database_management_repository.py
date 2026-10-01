from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Union

from database.connection import create_connection


@dataclass(frozen=True)
class DataDateRecord:
    month: str
    data_date: str
    load_time: str | None


class DatabaseManagementRepository:
    """Đọc danh sách DATE đã có mà không tải dữ liệu chi tiết."""

    TABLE_BY_TYPE = {
        "PRIME": "prime_data",
        "CUM": "cum_data",
    }

    def __init__(
        self,
        database_path: Union[str, Path],
    ):
        self.database_path = Path(database_path)

    def get_date_records(
        self,
        data_type: str,
    ) -> list[DataDateRecord]:
        """
        Tìm từng DATE khác nhau bằng index seek, không quét mọi dòng test.

        LEFT JOIN giúp dữ liệu cũ vẫn xuất hiện dù chưa có metadata
        load time; các lần import mới sẽ có load time chính xác.
        """

        normalized_type = data_type.strip().upper()

        table_name = self.TABLE_BY_TYPE.get(
            normalized_type
        )

        if table_name is None:
            raise ValueError(
                "Loại dữ liệu không hợp lệ."
            )

        connection = create_connection(
            self.database_path
        )

        try:
            connection.execute(
                "PRAGMA query_only = ON"
            )

            rows = connection.execute(
                f"""
                WITH RECURSIVE dates(DATE) AS (
                    SELECT MIN(DATE) FROM {table_name} WHERE DATE > ''
                    UNION ALL
                    SELECT (SELECT MIN(DATE) FROM {table_name}
                            WHERE DATE > dates.DATE)
                    FROM dates WHERE DATE IS NOT NULL
                )
                SELECT
                    substr(source.DATE, 1, 6) AS month,
                    source.DATE AS data_date,
                    status.imported_at AS load_time
                FROM dates AS source
                LEFT JOIN data_import_status AS status
                  ON status.data_type = ?
                 AND status.DATE = source.DATE
                WHERE source.DATE IS NOT NULL
                ORDER BY source.DATE DESC
                """,
                (normalized_type,),
            ).fetchall()

            return [
                DataDateRecord(
                    month=row["month"],
                    data_date=row["data_date"],
                    load_time=self._display_time(row["load_time"]),
                )
                for row in rows
            ]

        finally:
            connection.close()

    @staticmethod
    def _display_time(value):
        """Đổi imported_at UTC sang giờ máy, định dạng giống Aging."""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone().strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            return str(value)
