import tempfile
import unittest

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import auto_import_today_main as auto_today

from database.connection import connection
from database.schema import initialize_database
from repositories.auto_import_scheduler_repository import (
    AutoImportSchedulerRepository,
)


class AutoImportTodayTests(unittest.TestCase):
    """Kiểm tra tác vụ Today độc lập, không cần khởi tạo PyQt."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.database = self.base / "database" / "li.db"
        self.database.parent.mkdir()
        self.log_root = self.base / "logs"
        self.log_root.mkdir()
        initialize_database(self.database)
        AutoImportSchedulerRepository(self.database).save_config(
            enabled=True,
            import_time="00:00",
            log_folder=str(self.log_root),
        )

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def _log_text(serial: str) -> str:
        today = datetime.now().strftime("%Y%m%d")
        return (
            f"<ENDTIME>{today}120000</ENDTIME>"
            "<TESTER>AI-H903</TESTER>"
            "<PARTID>MZWLO3T8HCLS-01AGG-JZ7</PARTID>"
            "<LOTID>LOT1</LOTID>"
            "<PORT>1:2:3:4:</PORT>"
            "<HBIN>1:0:0:0:</HBIN>"
            "<SCRAP_CODE>0:0:0:0:</SCRAP_CODE>"
            f"<SERIAL_NO>{serial}:NULL:NULL:NULL:</SERIAL_NO>"
            "<TESTCNT>1:NULL:NULL:NULL:</TESTCNT>"
        )

    def test_replaces_current_day_every_run_and_keeps_last_date(self):
        day_folder = (
            self.log_root
            / "AI-H903"
            / datetime.now().strftime("%y%m%d")
        )
        day_folder.mkdir(parents=True)
        log_file = day_folder / "li.txt"
        log_file.write_text(
            self._log_text("SERIAL-OLD"),
            encoding="utf-8",
        )

        with patch.object(
            auto_today,
            "append_auto_import_log",
        ) as write_log:
            self.assertEqual(
                auto_today.run_auto_import_today(
                    self.database
                ),
                0,
            )
            log_file.write_text(
                self._log_text("SERIAL-NEW"),
                encoding="utf-8",
            )
            self.assertEqual(
                auto_today.run_auto_import_today(
                    self.database
                ),
                0,
            )

        with connection(self.database) as conn:
            rows = conn.execute(
                "SELECT SERIAL FROM prime_data"
            ).fetchall()

        self.assertEqual(
            [row["SERIAL"] for row in rows],
            ["SERIAL-NEW"],
        )
        self.assertIsNone(
            AutoImportSchedulerRepository(
                self.database
            ).get_config().last_import_date
        )
        success_messages = [
            call.args[1]
            for call in write_log.call_args_list
            if call.args[0] == "SUCCESS"
        ]
        self.assertEqual(len(success_messages), 2)
        self.assertIn("Deleted: 1", success_messages[-1])

    def test_missing_today_file_is_skipped_without_deleting_data(self):
        with connection(self.database) as conn:
            conn.execute(
                """
                INSERT INTO prime_data(
                    DATE, TIME, EQP, PARTNO, LOTNO, SLOT,
                    RESULT, TEST_COUNT, SERIAL, MODEL
                ) VALUES (?, '08:00:00', 'AI-H903', 'ABCDE-123',
                          'LOT1', 1, 'PASS', 1, 'EXISTING', 'ABCDE')
                """,
                (datetime.now().strftime("%Y%m%d"),),
            )

        with patch.object(
            auto_today,
            "append_auto_import_log",
        ) as write_log:
            self.assertEqual(
                auto_today.run_auto_import_today(
                    self.database
                ),
                0,
            )

        self.assertEqual(
            write_log.call_args_list[-1].args[0],
            "SKIPPED",
        )
        with connection(self.database) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM prime_data"
            ).fetchone()[0]
        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
