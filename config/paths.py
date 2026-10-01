# """Đường dẫn và hằng số; không đọc JSON."""
# import sys
# from pathlib import Path
#
# APP_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]
# DATABASE_PATH = APP_DIR / "database" / "li_app.db"
# LOG_ENCODING = "utf-8-sig"
# # Khi dùng chung ổ mạng: đổi DATABASE_PATH thành Path("//SERVER/Shared/LI/li_app.db").
"""Đường dẫn và hằng số; không đọc JSON."""
import os
import sys
from pathlib import Path

APP_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]
DATABASE_PATH = Path(
    os.environ.get("LI_DB_PATH", APP_DIR / "database" / "li_app.db")
)
LOG_ENCODING = "utf-8-sig"
# Launcher truyền LI_DB_PATH để EXE local luôn dùng database trên server.
