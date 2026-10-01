# """Launcher cập nhật LI Yield từ thư mục dùng chung rồi chạy bản local."""
# from __future__ import annotations
#
# import ctypes
# import os
# import shutil
# import subprocess
# import sys
# import traceback
#
# from ctypes import wintypes
# from datetime import datetime
# from pathlib import Path
#
#
# APP_NAME = "LI Yield"
# LOCAL_FOLDER_NAME = "LI_Yield"
# CORE_EXE_NAME = "LI_Yield.exe"
# MUTEX_NAME = "Local\\LIYieldLauncher"
#
#
# def show_error(message: str) -> None:
#     """Hiển thị lỗi khi Launcher được build không kèm console."""
#     ctypes.windll.user32.MessageBoxW(
#         None, message, f"{APP_NAME} Launcher", 0x10
#     )
#
#
# def show_information(message: str) -> None:
#     """Hiển thị thông báo trạng thái cho người dùng."""
#     ctypes.windll.user32.MessageBoxW(
#         None, message, f"{APP_NAME} Launcher", 0x40
#     )
#
#
# def acquire_single_instance():
#     """Không cho hai Launcher cập nhật đồng thời trên cùng một máy."""
#     kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
#     kernel32.CreateMutexW.argtypes = [
#         ctypes.c_void_p,
#         wintypes.BOOL,
#         wintypes.LPCWSTR,
#     ]
#     kernel32.CreateMutexW.restype = wintypes.HANDLE
#     kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
#     kernel32.CloseHandle.restype = wintypes.BOOL
#
#     mutex_handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
#     if not mutex_handle:
#         raise ctypes.WinError(ctypes.get_last_error())
#
#     # ERROR_ALREADY_EXISTS
#     if ctypes.get_last_error() == 183:
#         kernel32.CloseHandle(mutex_handle)
#         return None
#
#     return kernel32, mutex_handle
#
#
# class UpdateService:
#     """Kiểm tra phiên bản, cập nhật package local và mở LI Yield."""
#
#     def __init__(self) -> None:
#         self.server_root = self.get_server_root()
#         self.server_package = self.server_root / "package"
#         self.server_version = self.server_package / "version.txt"
#         self.server_exe = self.server_package / CORE_EXE_NAME
#         self.server_internal = self.server_package / "_internal"
#         self.server_db = self.server_root / "database" / "li_app.db"
#
#         self.local_root = (
#             Path(os.environ["LOCALAPPDATA"]) / LOCAL_FOLDER_NAME
#         )
#         self.local_app_root = self.local_root / "App"
#         self.local_staging = self.local_root / "App.new"
#         self.local_backup = self.local_root / "App.backup"
#         self.local_version = self.local_app_root / "version.txt"
#         self.local_exe = self.local_app_root / CORE_EXE_NAME
#         self.local_internal = self.local_app_root / "_internal"
#         self.log_file = self.local_root / "logs" / "launcher.log"
#
#     @staticmethod
#     def get_server_root() -> Path:
#         """Lấy folder chứa Launcher trên server hoặc folder source khi test."""
#         if getattr(sys, "frozen", False):
#             return Path(sys.executable).resolve().parent
#         return Path(__file__).resolve().parent
#
#     def write_log(self, message: str) -> None:
#         """Ghi log Launcher riêng trên máy người dùng."""
#         try:
#             self.log_file.parent.mkdir(parents=True, exist_ok=True)
#             timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             with self.log_file.open("a", encoding="utf-8") as log_file:
#                 log_file.write(f"[{timestamp}] {message}\n")
#         except Exception:
#             pass
#
#     @staticmethod
#     def read_optional_text(path: Path) -> str:
#         """Đọc version local, trả về rỗng nếu máy chưa có app."""
#         try:
#             if path.is_file():
#                 return path.read_text(encoding="utf-8").strip()
#         except OSError:
#             return ""
#         return ""
#
#     @staticmethod
#     def read_required_text(path: Path) -> str:
#         """Đọc file text bắt buộc và không che giấu lỗi từ server."""
#         value = path.read_text(encoding="utf-8-sig").strip()
#         if not value:
#             raise ValueError(f"File phiên bản đang rỗng:\n{path}")
#         return value
#
#     def validate_server(self) -> None:
#         """Kiểm tra package và database dùng chung trước khi cập nhật."""
#         if not self.server_package.is_dir():
#             raise FileNotFoundError(
#                 f"Không tìm thấy package:\n{self.server_package}"
#             )
#         if not self.server_version.is_file():
#             raise FileNotFoundError(
#                 f"Không tìm thấy version.txt:\n{self.server_version}"
#             )
#         if not self.server_exe.is_file():
#             raise FileNotFoundError(
#                 f"Không tìm thấy {CORE_EXE_NAME}:\n{self.server_exe}"
#             )
#         if not self.server_internal.is_dir():
#             raise FileNotFoundError(
#                 f"Không tìm thấy folder _internal:\n{self.server_internal}"
#             )
#         self.read_required_text(self.server_version)
#
#         # LI không dùng allow_create_database.flag. Database dùng chung phải
#         # có sẵn để tránh SQLite tạo nhầm database rỗng khi sai đường dẫn.
#         if not self.server_db.is_file():
#             raise FileNotFoundError(
#                 "Không tìm thấy database LI dùng chung:\n"
#                 f"{self.server_db}\n\n"
#                 "Hãy kiểm tra kết nối mạng hoặc đặt li_app.db đúng thư mục "
#                 "database cạnh Launcher."
#             )
#
#     def get_versions(self) -> tuple[str, str]:
#         """Lấy version server và version đang có trên máy."""
#         return (
#             self.read_required_text(self.server_version),
#             self.read_optional_text(self.local_version),
#         )
#
#     def need_update(self) -> bool:
#         """Xác định có cần copy lại package xuống máy hay không."""
#         server_version, local_version = self.get_versions()
#         return any(
#             (
#                 server_version != local_version,
#                 not self.local_exe.is_file(),
#                 not self.local_internal.is_dir(),
#             )
#         )
#
#     @staticmethod
#     def is_core_running() -> bool:
#         """Kiểm tra LI Yield đang mở trên máy hay không."""
#         result = subprocess.run(
#             ["tasklist", "/FI", f"IMAGENAME eq {CORE_EXE_NAME}"],
#             capture_output=True,
#             text=True,
#             shell=False,
#             creationflags=subprocess.CREATE_NO_WINDOW,
#             check=False,
#         )
#         return CORE_EXE_NAME.lower() in result.stdout.lower()
#
#     @staticmethod
#     def remove_folder(path: Path) -> None:
#         """Xóa folder cập nhật tạm nếu tồn tại."""
#         if path.is_dir():
#             shutil.rmtree(path)
#
#     def copy_to_staging(self) -> None:
#         """Copy package server vào App.new, chưa thay bản đang dùng."""
#         self.local_root.mkdir(parents=True, exist_ok=True)
#         self.remove_folder(self.local_staging)
#         command = [
#             "robocopy",
#             str(self.server_package),
#             str(self.local_staging),
#             "/MIR",
#             "/R:2",
#             "/W:1",
#             "/NFL",
#             "/NDL",
#             "/NJH",
#             "/NJS",
#             "/NP",
#         ]
#         self.write_log("Run robocopy: " + subprocess.list2cmdline(command))
#         result = subprocess.run(
#             command,
#             capture_output=True,
#             text=True,
#             shell=False,
#             creationflags=subprocess.CREATE_NO_WINDOW,
#             check=False,
#         )
#         self.write_log(f"Robocopy return code: {result.returncode}")
#         if result.stdout:
#             self.write_log(result.stdout)
#         if result.stderr:
#             self.write_log(result.stderr)
#         # Robocopy dùng mã 0–7 cho các trạng thái thành công.
#         if result.returncode >= 8:
#             raise RuntimeError(
#                 "Copy chương trình thất bại.\n"
#                 f"Robocopy code: {result.returncode}"
#             )
#
#     def validate_staging(self, expected_version: str) -> None:
#         """Xác nhận App.new đầy đủ trước khi thay bản local hiện tại."""
#         staging_exe = self.local_staging / CORE_EXE_NAME
#         staging_internal = self.local_staging / "_internal"
#         staging_version = self.local_staging / "version.txt"
#         if not staging_exe.is_file():
#             raise FileNotFoundError(
#                 f"Package copy về thiếu {CORE_EXE_NAME}."
#             )
#         if not staging_internal.is_dir():
#             raise FileNotFoundError("Package copy về thiếu folder _internal.")
#         if self.read_required_text(staging_version) != expected_version:
#             raise RuntimeError(
#                 "Version package copy về không khớp version trên server."
#             )
#
#     def activate_staging(self) -> None:
#         """Đưa App.new thành App và khôi phục bản cũ nếu đổi folder lỗi."""
#         self.remove_folder(self.local_backup)
#         old_app_moved = False
#         try:
#             if self.local_app_root.is_dir():
#                 self.local_app_root.rename(self.local_backup)
#                 old_app_moved = True
#             self.local_staging.rename(self.local_app_root)
#         except Exception:
#             if (
#                 old_app_moved
#                 and not self.local_app_root.exists()
#                 and self.local_backup.is_dir()
#             ):
#                 self.local_backup.rename(self.local_app_root)
#             raise
#
#         try:
#             self.remove_folder(self.local_backup)
#         except Exception as error:
#             self.write_log(f"Không thể xóa App.backup: {error}")
#
#     def copy_package(self) -> None:
#         """Copy và kích hoạt phiên bản mới theo cơ chế staging an toàn."""
#         if self.is_core_running():
#             raise RuntimeError(
#                 "LI Yield đang mở.\n\n"
#                 "Vui lòng đóng chương trình rồi mở lại để cập nhật."
#             )
#         expected_version = self.read_required_text(self.server_version)
#         self.copy_to_staging()
#         self.validate_staging(expected_version)
#         self.activate_staging()
#         self.write_log(
#             f"Cập nhật thành công lên version {expected_version}."
#         )
#
#     def start_core_app(self) -> None:
#         """Truyền DB server và mở LI Yield từ package trên máy local."""
#         if not self.local_exe.is_file():
#             raise FileNotFoundError(
#                 f"Không tìm thấy chương trình local:\n{self.local_exe}"
#             )
#         environment = os.environ.copy()
#         environment["LI_DB_PATH"] = str(self.server_db)
#         environment["LI_SERVER_ROOT"] = str(self.server_root)
#         subprocess.Popen(
#             [str(self.local_exe)],
#             env=environment,
#             cwd=str(self.local_app_root),
#         )
#
#     def run(self) -> None:
#         """Thực hiện toàn bộ luồng kiểm tra, cập nhật và mở ứng dụng."""
#         self.validate_server()
#         server_version, local_version = self.get_versions()
#         self.write_log(
#             "Launcher start | "
#             f"Server: {server_version} | Local: {local_version or 'NONE'}"
#         )
#         if self.need_update():
#             self.copy_package()
#         elif self.is_core_running():
#             show_information("LI Yield đang được mở.")
#             return
#         self.start_core_app()
#         self.write_log("Đã mở LI Yield.")
#
#     def log_exception(self) -> None:
#         """Ghi traceback đầy đủ vào log Launcher."""
#         self.write_log(traceback.format_exc().rstrip())
#
#
# def main() -> int:
#     """Entry point của LI Yield Launcher."""
#     if os.name != "nt":
#         return 1
#     mutex = acquire_single_instance()
#     if mutex is None:
#         return 0
#     kernel32, mutex_handle = mutex
#     service = UpdateService()
#     try:
#         service.run()
#         return 0
#     except Exception as error:
#         service.log_exception()
#         show_error(str(error).strip() or "Launcher gặp lỗi không xác định.")
#         return 1
#     finally:
#         kernel32.CloseHandle(mutex_handle)
#
#
# if __name__ == "__main__":
#     sys.exit(main())

"""Launcher cập nhật LI Yield từ thư mục dùng chung rồi chạy bản local."""
from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import sys
import traceback

from ctypes import wintypes
from datetime import datetime
from pathlib import Path


APP_NAME = "LI Yield"
LOCAL_FOLDER_NAME = "LI_Yield"
CORE_EXE_NAME = "LI_Yield.exe"
MUTEX_NAME = "Local\\LIYieldLauncher"


def show_error(message: str) -> None:
    """Hiển thị lỗi khi Launcher được build không kèm console."""
    ctypes.windll.user32.MessageBoxW(
        None, message, f"{APP_NAME} Launcher", 0x10
    )


def show_information(message: str) -> None:
    """Hiển thị thông báo trạng thái cho người dùng."""
    ctypes.windll.user32.MessageBoxW(
        None, message, f"{APP_NAME} Launcher", 0x40
    )


def acquire_single_instance():
    """Không cho hai Launcher cập nhật đồng thời trên cùng một máy."""
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.argtypes = [
        ctypes.c_void_p,
        wintypes.BOOL,
        wintypes.LPCWSTR,
    ]
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL

    mutex_handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if not mutex_handle:
        raise ctypes.WinError(ctypes.get_last_error())

    # ERROR_ALREADY_EXISTS
    if ctypes.get_last_error() == 183:
        kernel32.CloseHandle(mutex_handle)
        return None

    return kernel32, mutex_handle


class UpdateService:
    """Kiểm tra phiên bản, cập nhật package local và mở LI Yield."""

    def __init__(self) -> None:
        self.server_root = self.get_server_root()
        self.server_package = self.server_root / "package"
        self.server_version = self.server_package / "version.txt"
        self.server_exe = self.server_package / CORE_EXE_NAME
        self.server_internal = self.server_package / "_internal"
        self.server_db = self.server_root / "database" / "li_app.db"

        self.local_root = (
            Path(os.environ["LOCALAPPDATA"]) / LOCAL_FOLDER_NAME
        )
        self.local_app_root = self.local_root / "App"
        self.local_staging = self.local_root / "App.new"
        self.local_backup = self.local_root / "App.backup"
        self.local_version = self.local_app_root / "version.txt"
        self.local_exe = self.local_app_root / CORE_EXE_NAME
        self.local_internal = self.local_app_root / "_internal"
        self.log_file = self.local_root / "logs" / "launcher.log"

    @staticmethod
    def get_server_root() -> Path:
        """Lấy folder chứa Launcher trên server hoặc folder source khi test."""
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parent

    def write_log(self, message: str) -> None:
        """Ghi log Launcher riêng trên máy người dùng."""
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self.log_file.open("a", encoding="utf-8") as log_file:
                log_file.write(f"[{timestamp}] {message}\n")
        except Exception:
            pass

    @staticmethod
    def read_optional_text(path: Path) -> str:
        """Đọc version local, trả về rỗng nếu máy chưa có app."""
        try:
            if path.is_file():
                return path.read_text(encoding="utf-8").strip()
        except OSError:
            return ""
        return ""

    @staticmethod
    def read_required_text(path: Path) -> str:
        """Đọc file text bắt buộc và không che giấu lỗi từ server."""
        value = path.read_text(encoding="utf-8-sig").strip()
        if not value:
            raise ValueError(f"File phiên bản đang rỗng:\n{path}")
        return value

    def validate_server(self) -> None:
        """Kiểm tra package và chuẩn bị vị trí database dùng chung."""
        if not self.server_package.is_dir():
            raise FileNotFoundError(
                f"Không tìm thấy package:\n{self.server_package}"
            )
        if not self.server_version.is_file():
            raise FileNotFoundError(
                f"Không tìm thấy version.txt:\n{self.server_version}"
            )
        if not self.server_exe.is_file():
            raise FileNotFoundError(
                f"Không tìm thấy {CORE_EXE_NAME}:\n{self.server_exe}"
            )
        if not self.server_internal.is_dir():
            raise FileNotFoundError(
                f"Không tìm thấy folder _internal:\n{self.server_internal}"
            )
        self.read_required_text(self.server_version)

        if self.server_db.exists():
            if not self.server_db.is_file():
                raise FileExistsError(
                    "Đường dẫn database LI không phải là file:\n"
                    f"{self.server_db}"
                )
            return

        # Lần chạy đầu chỉ chuẩn bị thư mục. LI_Yield.exe sẽ tạo file và toàn
        # bộ schema qua DatabaseInitWorker; Launcher không tạo file DB rỗng.
        try:
            self.server_db.parent.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            raise OSError(
                "Không thể tạo hoặc truy cập thư mục database LI:\n"
                f"{self.server_db.parent}\n\n{error}"
            ) from error
        self.write_log(
            "Chưa có database; LI Yield sẽ tự tạo database mới tại "
            f"{self.server_db}."
        )

    def get_versions(self) -> tuple[str, str]:
        """Lấy version server và version đang có trên máy."""
        return (
            self.read_required_text(self.server_version),
            self.read_optional_text(self.local_version),
        )

    def need_update(self) -> bool:
        """Xác định có cần copy lại package xuống máy hay không."""
        server_version, local_version = self.get_versions()
        return any(
            (
                server_version != local_version,
                not self.local_exe.is_file(),
                not self.local_internal.is_dir(),
            )
        )

    @staticmethod
    def is_core_running() -> bool:
        """Kiểm tra LI Yield đang mở trên máy hay không."""
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {CORE_EXE_NAME}"],
            capture_output=True,
            text=True,
            shell=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
            check=False,
        )
        return CORE_EXE_NAME.lower() in result.stdout.lower()

    @staticmethod
    def remove_folder(path: Path) -> None:
        """Xóa folder cập nhật tạm nếu tồn tại."""
        if path.is_dir():
            shutil.rmtree(path)

    def copy_to_staging(self) -> None:
        """Copy package server vào App.new, chưa thay bản đang dùng."""
        self.local_root.mkdir(parents=True, exist_ok=True)
        self.remove_folder(self.local_staging)
        command = [
            "robocopy",
            str(self.server_package),
            str(self.local_staging),
            "/MIR",
            "/R:2",
            "/W:1",
            "/NFL",
            "/NDL",
            "/NJH",
            "/NJS",
            "/NP",
        ]
        self.write_log("Run robocopy: " + subprocess.list2cmdline(command))
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            shell=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
            check=False,
        )
        self.write_log(f"Robocopy return code: {result.returncode}")
        if result.stdout:
            self.write_log(result.stdout)
        if result.stderr:
            self.write_log(result.stderr)
        # Robocopy dùng mã 0–7 cho các trạng thái thành công.
        if result.returncode >= 8:
            raise RuntimeError(
                "Copy chương trình thất bại.\n"
                f"Robocopy code: {result.returncode}"
            )

    def validate_staging(self, expected_version: str) -> None:
        """Xác nhận App.new đầy đủ trước khi thay bản local hiện tại."""
        staging_exe = self.local_staging / CORE_EXE_NAME
        staging_internal = self.local_staging / "_internal"
        staging_version = self.local_staging / "version.txt"
        if not staging_exe.is_file():
            raise FileNotFoundError(
                f"Package copy về thiếu {CORE_EXE_NAME}."
            )
        if not staging_internal.is_dir():
            raise FileNotFoundError("Package copy về thiếu folder _internal.")
        if self.read_required_text(staging_version) != expected_version:
            raise RuntimeError(
                "Version package copy về không khớp version trên server."
            )

    def activate_staging(self) -> None:
        """Đưa App.new thành App và khôi phục bản cũ nếu đổi folder lỗi."""
        self.remove_folder(self.local_backup)
        old_app_moved = False
        try:
            if self.local_app_root.is_dir():
                self.local_app_root.rename(self.local_backup)
                old_app_moved = True
            self.local_staging.rename(self.local_app_root)
        except Exception:
            if (
                old_app_moved
                and not self.local_app_root.exists()
                and self.local_backup.is_dir()
            ):
                self.local_backup.rename(self.local_app_root)
            raise

        try:
            self.remove_folder(self.local_backup)
        except Exception as error:
            self.write_log(f"Không thể xóa App.backup: {error}")

    def copy_package(self) -> None:
        """Copy và kích hoạt phiên bản mới theo cơ chế staging an toàn."""
        if self.is_core_running():
            raise RuntimeError(
                "LI Yield đang mở.\n\n"
                "Vui lòng đóng chương trình rồi mở lại để cập nhật."
            )
        expected_version = self.read_required_text(self.server_version)
        self.copy_to_staging()
        self.validate_staging(expected_version)
        self.activate_staging()
        self.write_log(
            f"Cập nhật thành công lên version {expected_version}."
        )

    def start_core_app(self) -> None:
        """Truyền DB server và mở LI Yield từ package trên máy local."""
        if not self.local_exe.is_file():
            raise FileNotFoundError(
                f"Không tìm thấy chương trình local:\n{self.local_exe}"
            )
        environment = os.environ.copy()
        environment["LI_DB_PATH"] = str(self.server_db)
        environment["LI_SERVER_ROOT"] = str(self.server_root)
        subprocess.Popen(
            [str(self.local_exe)],
            env=environment,
            cwd=str(self.local_app_root),
        )

    def run(self) -> None:
        """Thực hiện toàn bộ luồng kiểm tra, cập nhật và mở ứng dụng."""
        self.validate_server()
        server_version, local_version = self.get_versions()
        self.write_log(
            "Launcher start | "
            f"Server: {server_version} | Local: {local_version or 'NONE'}"
        )
        if self.need_update():
            self.copy_package()
        elif self.is_core_running():
            show_information("LI Yield đang được mở.")
            return
        self.start_core_app()
        self.write_log("Đã mở LI Yield.")

    def log_exception(self) -> None:
        """Ghi traceback đầy đủ vào log Launcher."""
        self.write_log(traceback.format_exc().rstrip())


def main() -> int:
    """Entry point của LI Yield Launcher."""
    if os.name != "nt":
        return 1
    mutex = acquire_single_instance()
    if mutex is None:
        return 0
    kernel32, mutex_handle = mutex
    service = UpdateService()
    try:
        service.run()
        return 0
    except Exception as error:
        service.log_exception()
        show_error(str(error).strip() or "Launcher gặp lỗi không xác định.")
        return 1
    finally:
        kernel32.CloseHandle(mutex_handle)


if __name__ == "__main__":
    sys.exit(main())
