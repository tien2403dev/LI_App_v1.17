from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from services.mail_service import MailLoginInfo

from PyQt5.QtCore import (
    QObject,
    pyqtSignal,
    pyqtSlot,
)

from repositories.mail_configuration_repository import (
    MailConfigurationRepository,
)


@dataclass(frozen=True)
class MailLoginResult:
    """Kết quả Test Login trả về giao diện."""

    configured_user_id: str
    configured_name: str
    login_info: MailLoginInfo


class MailLoginWorker(QObject):
    """Chạy Test Login ngoài UI thread."""

    succeeded = pyqtSignal(object)
    failed = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(
        self,
        database_path: Union[str, Path],
    ):
        """Khởi tạo đối tượng và các thành phần liên quan."""
        super().__init__()

        self.database_path = Path(
            database_path
        )

    @pyqtSlot()
    def run(self) -> None:
        """Kiểm tra đăng nhập Sender đang Enable và luôn báo kết thúc worker."""
        service = None

        try:
            from services.mail_service import MailService
            service = MailService()
            repository = (
                MailConfigurationRepository(
                    self.database_path
                )
            )

            sender = (
                repository.get_enabled_sender()
            )

            if sender is None:
                raise ValueError(
                    (
                        "Chưa có Sender nào được Enable.\n\n"
                        "Vui lòng tích Enable cho một Sender "
                        "trước khi Test Login."
                    )
                )

            if not sender.password:
                raise ValueError(
                    (
                        "Sender đang Enable chưa có mật khẩu.\n\n"
                        "Vui lòng xóa Sender cũ và Add lại."
                    )
                )

            success, detail = service.login(
                user_id=sender.user_id,
                password=sender.password,
            )

            if not success:
                self.failed.emit(
                    str(detail)
                )
                return

            result = MailLoginResult(
                configured_user_id=(
                    sender.user_id
                ),
                configured_name=(
                    sender.display_name
                ),
                login_info=detail,
            )

            self.succeeded.emit(result)

        except Exception as error:
            self.failed.emit(
                str(error).strip()
                or "Không thể đăng nhập hệ thống mail."
            )

        finally:
            # Test Login chỉ kiểm tra tài khoản.
            # Khi gửi mail thật sẽ login bằng một
            # MailService mới trong worker gửi mail.
            if service is not None:
                service.clear_session()
            self.finished.emit()
            