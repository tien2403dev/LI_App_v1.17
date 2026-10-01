from dataclasses import dataclass
from pathlib import Path
from typing import Union

from database.connection import connection


@dataclass(frozen=True)
class MachineSlotYieldConfig:
    """Cấu hình ngưỡng dùng để tạo alarm Machine Slot Yield."""

    log_folder: str
    target_15: float
    target_30: float
    continuous_fail_count: int
    different_scrap_fail_count: int = 3


class MachineSlotYieldRepository:
    """Đọc và lưu cấu hình Machine Slot Yield trong SQLite."""

    def __init__(self, database_path: Union[str, Path]):
        self.database_path = Path(database_path)

    def get_config(self) -> MachineSlotYieldConfig:
        """Đọc cấu hình; dùng Log Folder Auto Import nếu chưa lưu riêng."""
        with connection(self.database_path) as conn:
            row = conn.execute(
                """SELECT log_folder, target_15, target_30,
                          continuous_fail_count, different_scrap_fail_count
                   FROM machine_slot_yield_config
                   WHERE id = 1"""
            ).fetchone()
            if row is None:
                raise RuntimeError("Chưa khởi tạo cấu hình Machine Slot Yield.")

            log_folder = row["log_folder"]
            if not log_folder:
                scheduler = conn.execute(
                    "SELECT log_folder FROM auto_import_scheduler WHERE id = 1"
                ).fetchone()
                if scheduler is not None:
                    log_folder = scheduler["log_folder"]

            return MachineSlotYieldConfig(
                log_folder=log_folder or "",
                target_15=float(row["target_15"]),
                target_30=float(row["target_30"]),
                continuous_fail_count=int(row["continuous_fail_count"]),
                different_scrap_fail_count=int(row["different_scrap_fail_count"]),
            )

    def save_config(
        self,
        log_folder: str,
        target_15: float,
        target_30: float,
        continuous_fail_count: int,
        different_scrap_fail_count: int | None = None,
    ) -> MachineSlotYieldConfig:
        """Kiểm tra và lưu nguyên tử toàn bộ cấu hình singleton."""
        normalized_folder = str(log_folder).strip()
        target_15 = float(target_15)
        target_30 = float(target_30)
        continuous_fail_count = int(continuous_fail_count)

        if different_scrap_fail_count is not None:
            different_scrap_fail_count = int(different_scrap_fail_count)
            if different_scrap_fail_count < 2:
                raise ValueError("Số lần fail liên tục khác Scrap code phải >= 2.")

        if not 0 <= target_15 <= 100 or not 0 <= target_30 <= 100:
            raise ValueError("Target phải nằm trong khoảng 0 đến 100%.")
        if continuous_fail_count < 1:
            raise ValueError("Số lần fail liên tục phải lớn hơn hoặc bằng 1.")

        with connection(self.database_path) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                if different_scrap_fail_count is None:
                    different_scrap_fail_count = conn.execute(
                        'SELECT different_scrap_fail_count FROM machine_slot_yield_config WHERE id=1'
                    ).fetchone()[0]
                conn.execute(
                    """UPDATE machine_slot_yield_config
                       SET log_folder = ?, target_15 = ?, target_30 = ?,
                           continuous_fail_count = ?, different_scrap_fail_count = ?,
                           updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')
                       WHERE id = 1""",
                    (
                        normalized_folder,
                        target_15,
                        target_30,
                        continuous_fail_count,
                        different_scrap_fail_count,
                    ),
                )
                conn.commit()
            except BaseException:
                conn.rollback()
                raise

        return MachineSlotYieldConfig(
            normalized_folder,
            target_15,
            target_30,
            continuous_fail_count,
            different_scrap_fail_count,
        )
