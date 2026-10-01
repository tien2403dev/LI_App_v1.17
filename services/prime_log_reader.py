
import codecs
import os
import re
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from database.schema import PRIME_FIELDS
from database.diagnostics import event
from domain.prime import COLUMNS, PrimeRecord, ValidationError, check_cancel

BATCH_SIZE = 5000
KEY_VALUE = re.compile(r"([A-Za-z0-9_]+)=([^\s]+)")
# Ngày ở đầu tên; _TCP ở cuối tên trước phần mở rộng (hoặc không có đuôi).
TCP_NAME = re.compile(r"^([0-9]{8})(?:.*)_TCP$", re.IGNORECASE)
TIME_PREFIX = re.compile(
    r"^\s*\[?(?:[0-9]{4}[-/][0-9]{2}[-/][0-9]{2}[ _T])?"
    r"([0-9]{2}:[0-9]{2}:[0-9]{2})(?:[.,][0-9]+)?(?=\]|\s|$)"
)


def integer(value: str, label: str, minimum: int,
            maximum: int | None = None) -> int:
    """Kiểm tra số nguyên có dấu, giới hạn SQLite và phạm vi của trường."""
    if not re.fullmatch(r"-?[0-9]+", value):
        raise ValidationError(f"{label}: cần số nguyên, nhận {value!r}")

    try:
        result = int(value)
    except ValueError as error:
        raise ValidationError(f"{label}: số nguyên quá lớn") from error

    if not -9223372036854775808 <= result <= 9223372036854775807:
        raise ValidationError(f"{label}: vượt giới hạn INTEGER của SQLite")

    if result < minimum or (maximum is not None and result > maximum):
        raise ValidationError(f"{label}: giá trị ngoài phạm vi: {value}")

    return result

class LiPrimeLogReader:
    def __init__(self, encoding="utf-8-sig"):
        self.encoding = encoding

    @staticmethod
    def file_date(path: Path) -> str | None:
        """Nhận YYYYMMDD..._TCP.txt hoặc YYYYMMDD..._TCP, không dùng mtime."""
        match = TCP_NAME.fullmatch(Path(path).stem)
        if match is None:
            return None
        value = match.group(1)
        try:
            datetime.strptime(value, "%Y%m%d")
        except ValueError:
            return None
        return value

    def read_file(self, path: Path):
        """Đọc log TCP; lỗi luôn có đường dẫn và số dòng nếu xác định được."""
        path = Path(path)
        try:
            day = self.file_date(path)
            if day is None:
                raise ValidationError("Tên file phải có ngày YYYYMMDD ở đầu và kết thúc bằng _TCP")
            # Read a bounded snapshot. Later appends belong to the next import.
            event('FILE_READ_BEGIN', path=str(path))
            with path.open('rb') as stream:
                limit = os.fstat(stream.fileno()).st_size
                data = stream.read(limit)
            event('FILE_READ_END', path=str(path), snapshot_bytes=len(data), initial_bytes=limit)
            if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
                newline = b'\n\x00' if data.startswith(codecs.BOM_UTF16_LE) else b'\x00\n'
                end = next((i + 2 for i in range(len(data)-2, 1, -1)
                            if i % 2 == 0 and data[i:i+2] == newline), 2)
                if end < len(data):
                    event('FILE_TAIL_DEFERRED', path=str(path))
                text = data[:end].decode("utf-16")
            else:
                # Drop partial final bytes before decoding (including partial UTF-8).
                if data and not data.endswith((b'\n', b'\r')):
                    end = max(data.rfind(b'\n'), data.rfind(b'\r')) + 1
                    data = data[:end]
                    event('FILE_TAIL_DEFERRED', path=str(path))
                # Cùng các fallback trong file mẫu. latin-1 giải mã được mọi byte.
                for encoding in dict.fromkeys((self.encoding, "utf-8-sig", "utf-8", "cp949", "iso-8859-1", "windows-1252")):
                    try:
                        text = data.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
            # A producer may be halfway through the last line at the boundary.
            # Defer that line rather than import a truncated serial/value.
            if text and not text.endswith(('\n', '\r')):
                boundary = max(text.rfind('\n'), text.rfind('\r'))
                text = text[:boundary + 1]
                event('FILE_TAIL_DEFERRED', path=str(path))
            yield from self.parse_text(text, day)
        except (ValueError, UnicodeError, OSError, ValidationError) as error:
            raise ValidationError(f"{path}: {error}") from error

    @staticmethod
    def parse_text(text: str, business_date: str):
        """Mỗi FUNCTION=SLOT_END là một sản phẩm; giữ nguyên schema PRIME."""
        if not re.fullmatch(r"[0-9]{8}", business_date):
            raise ValidationError(f"Ngày không hợp lệ: {business_date}")
        try:
            datetime.strptime(business_date, "%Y%m%d")
        except ValueError as error:
            raise ValidationError(f"Ngày không hợp lệ: {business_date}") from error
        for line_number, line in enumerate(text.splitlines(), 1):
            data = {key.upper(): value.strip() for key, value in KEY_VALUE.findall(line)}
            if data.get("FUNCTION", "").upper() != "SLOT_END":
                continue

            def first(*keys, default=""):
                return next((data[key] for key in keys if data.get(key)), default)

            def required(*keys):
                value = first(*keys)
                if value.upper() in ("", "NULL", "-"):
                    raise ValidationError(f"{keys[0]} không được thiếu/rỗng/NULL")
                return value

            try:
                serial = first("SERIAL", "SERIALNO", "SERIAL_NO")
                if serial.upper() == "NULL":
                    continue  # Giữ quy tắc cũ: không tính vị trí không có sản phẩm.
                serial = required("SERIAL", "SERIALNO", "SERIAL_NO")
                match = TIME_PREFIX.match(line)
                if match is None:
                    raise ValidationError("Không đọc được giờ HH:MM:SS ở đầu dòng")
                time = match.group(1)
                datetime.strptime(time, "%H:%M:%S")
                eqp = required("EQPID", "EQP_ID", "EQP")
                lot = required("LOTID", "LOT_ID")
                part = required("PARTNO", "PART_NO", "MODEL")
                if len(part) < 5:
                    raise ValidationError("PARTNO phải có ít nhất 5 ký tự")
                slot = integer(required("SLOT", "SLOTNO", "SLOT_NO"), "SLOT", 1, 48)
                result = required("TESTRESULT", "TEST_RESULT", "RESULT").upper()
                if result not in ("PASS", "FAIL"):
                    raise ValidationError(f"TESTRESULT phải là PASS/FAIL, nhận {result!r}")
                count = integer(required("TEST_COUNT", "TESTCOUNT", "COUNT"), "TEST_COUNT", 0)
                scrap = first("SCRAP_CODE", "SCRAPCODE", "SCRAP")
                scrap = None if scrap.upper() in ("", "0", "NULL", "-") else scrap
                yield PrimeRecord(business_date, time, eqp, part, lot, slot,
                                  result, scrap, count, serial, 1, part[:5])
            except (ValueError, ValidationError) as error:
                raise ValidationError(f"Dòng {line_number}: {error}") from error

    @staticmethod
    def discover(root: Path, dates: tuple[str, ...]) -> list[Path]:
        """Quét mọi cấp dưới Interface; chỉ chọn _TCP có ngày trong tên phù hợp."""
        root = Path(root)
        if not root.is_dir():
            raise ValidationError(f"Không truy cập được folder log: {root}")
        selected = set(dates)
        for value in selected:
            try:
                if not re.fullmatch(r"[0-9]{8}", value):
                    raise ValueError(value)
                datetime.strptime(value, "%Y%m%d")
            except ValueError as error:
                raise ValidationError(f"Ngày không hợp lệ: {value}") from error

        def walk_error(error):
            # Không coi lỗi quyền truy cập/mạng là không có ngày cần tìm.
            raise ValidationError(f"Không đọc được folder log: {error}") from error

        files = []
        for folder, directories, names in os.walk(root, topdown=True, onerror=walk_error, followlinks=False):
            # Cắt nhánh trước khi os.walk đi vào LOT, ở mọi cấp thư mục.
            directories[:] = [name for name in directories if name.upper() != "LOT"]
            if Path(folder).name.upper() == "LOT":
                directories[:] = []
                continue
            for name in names:
                path = Path(folder) / name
                if LiPrimeLogReader.file_date(path) in selected and path.is_file():
                    files.append(path)
        return sorted(files)

    def stage_folder(self, root, dates, stage_path, progress, cancel=None):
        """Đọc snapshot từng file vào staging; không kiểm tra lại nguồn sau khi đọc."""
        root = Path(root)
        files = self.discover(root, dates)
        if not files:
            # Giữ thông báo này vì hai tác vụ auto-import dùng nó để nhận biết SKIPPED.
            raise ValidationError("Không tìm thấy file .txt trong các folder ngày được chọn")
        total = 0
        with closing(sqlite3.connect(str(stage_path))) as conn:
            conn.execute(f"CREATE TABLE staging_prime_data({PRIME_FIELDS})")
            batch = []
            sql = f"INSERT INTO staging_prime_data({','.join(COLUMNS)}) VALUES({','.join('?' for _ in COLUMNS)})"
            for number, path in enumerate(files, 1):
                check_cancel(cancel)
                for record in self.read_file(path):
                    check_cancel(cancel)
                    batch.append(record.values())
                    total += 1
                    if len(batch) >= BATCH_SIZE:
                        conn.executemany(sql, batch)
                        batch.clear()
                if number == 1 or number % 50 == 0 or number == len(files):
                    progress(f"Đã đọc {number}/{len(files)} file; {total} dòng sản phẩm")
            if batch:
                conn.executemany(sql, batch)
            if not total:
                raise ValidationError("Không có sản phẩm hợp lệ; không xóa dữ liệu cũ")
            conn.execute(
                "CREATE INDEX idx_stage_date_eqp_time_slot "
                "ON staging_prime_data(DATE, EQP, TIME, SLOT)")
            conn.commit()
        return len(files)