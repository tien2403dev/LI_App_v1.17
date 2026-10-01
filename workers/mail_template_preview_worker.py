from __future__ import annotations

from dataclasses import dataclass
from datetime import (
    date,
    timedelta,
)
from pathlib import Path
from typing import Union

from PyQt5.QtCore import (
    QObject,
    pyqtSignal,
    pyqtSlot,
)

from repositories.mail_template_repository import (
    MailTemplate,
    MailTemplateRepository,
)
from services.mail_content_builder import (
    MailContentBuilder,
)


@dataclass(frozen=True)
class MailTemplatePreviewResult:
    """Dữ liệu trả về dialog Customize Email."""

    target_date: str
    template: MailTemplate
    alarm_count: int
    body_html: str


class MailTemplatePreviewWorker(QObject):
    """Tải template và Alarm ngoài UI thread."""

    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(
        self,
        database_path: Union[str, Path],
    ):
        """Giữ đường dẫn DB; mở kết nối trong worker."""
        super().__init__()

        self.database_path = Path(
            database_path
        )

    @pyqtSlot()
    def run(self) -> None:
        """Tải mẫu và alarm theo ngày máy tính, dựng HTML ngoài UI thread."""
        try:
            # Ngày chính là hôm nay. Preview hiển thị
            # ngày này và ngày hôm trước.
            anchor_date = date.today()

            target_dates = [
                (
                    anchor_date
                    - timedelta(days=day_offset)
                ).strftime("%Y%m%d")
                for day_offset in range(2)
            ]

            target_date = target_dates[0]

            repository = MailTemplateRepository(
                self.database_path
            )

            template = (
                repository.get_template()
            )

            alarms = (
                repository.get_alarm_previews(
                    target_dates
                )
            )

            body_html = (
                MailContentBuilder
                .build_alarm_body_html(
                    target_dates=target_dates,
                    alarms=alarms,
                )
            )

            self.succeeded.emit(
                MailTemplatePreviewResult(
                    target_date=target_date,
                    template=template,
                    alarm_count=len(alarms),
                    body_html=body_html,
                )
            )

        except Exception as error:
            self.failed.emit(
                str(error).strip()
                or "Không thể tạo Email Preview."
            )

