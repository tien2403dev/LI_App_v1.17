from __future__ import annotations

from pathlib import Path
from typing import Union

from PyQt5.QtCore import (
    QObject,
    pyqtSignal,
    pyqtSlot,
)


class DatabaseListWorker(QObject):
    """Tải danh sách ngày PRIME/CUM ngoài UI thread."""

    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(
        self,
        database_path: Union[str, Path],
        data_types: set[str] | None = None,
    ):
        super().__init__()

        self.database_path = Path(
            database_path
        )

        self.data_types = (
            set(data_types)
            if data_types is not None
            else {"PRIME", "CUM"}
        )

    @pyqtSlot()
    def run(self) -> None:
        try:
            # Lazy import repository khi worker chạy.
            from repositories.database_management_repository import (
                DatabaseManagementRepository,
            )

            repository = (
                DatabaseManagementRepository(
                    self.database_path
                )
            )

            result = {
                data_type: (
                    repository.get_date_records(
                        data_type
                    )
                )
                for data_type in sorted(
                    self.data_types
                )
            }

            self.succeeded.emit(result)

        except Exception as error:
            self.failed.emit(
                str(error).strip()
                or "Không thể tải danh sách dữ liệu."
            )


class PrimeExportWorker(QObject):
    """Export PRIME ngoài UI thread."""

    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(
        self,
        database_path: Union[str, Path],
        business_dates: list[str],
        output_path: Union[str, Path],
    ):
        super().__init__()

        self.database_path = Path(
            database_path
        )

        self.business_dates = list(
            business_dates
        )

        self.output_path = Path(
            output_path
        )

    @pyqtSlot()
    def run(self) -> None:
        try:
            # openpyxl chỉ được import sâu bên trong
            # service khi người dùng export.
            from services.prime_export_service import (
                PrimeExportService,
            )

            service = PrimeExportService(
                self.database_path
            )

            result = service.export_dates(
                business_dates=(
                    self.business_dates
                ),
                output_path=self.output_path,
            )

            self.succeeded.emit(result)

        except Exception as error:
            self.failed.emit(
                str(error).strip()
                or "Export PRIME thất bại."
            )