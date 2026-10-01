from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import (
    Iterable,
    Union,
)

from database.connection import create_connection

@dataclass(frozen=True)
class MailTemplate:
    """Template được người dùng lưu trong database."""

    subject: str
    heading: str
    closing: str


class MailTemplateRepository:
    """Đọc template và dữ liệu Alarm cho email."""

    TEMPLATE_ID = 1

    def __init__(
        self,
        database_path: Union[str, Path],
    ):
        self.database_path = Path(
            database_path
        )

    def get_template(self) -> MailTemplate:
        """Đọc template hiện tại từ database."""

        connection = create_connection(
            self.database_path
        )

        try:
            row = connection.execute(
                """
                SELECT
                    subject,
                    heading,
                    closing
                FROM mail_template
                WHERE id = ?
                """,
                (self.TEMPLATE_ID,),
            ).fetchone()

            if row is None:
                raise RuntimeError(
                    "Không tìm thấy Mail Template."
                )

            return MailTemplate(
                subject=str(
                    row["subject"] or ""
                ),
                heading=str(
                    row["heading"] or ""
                ),
                closing=str(
                    row["closing"] or ""
                ),
            )

        finally:
            connection.close()

    def save_template(
        self,
        subject: str,
        heading: str,
        closing: str,
    ) -> None:
        """Lưu template, không lưu Body Preview."""

        subject = subject.strip()

        if not subject:
            raise ValueError(
                "Subject không được để trống."
            )

        connection = create_connection(
            self.database_path
        )

        try:
            connection.execute(
                """
                INSERT INTO mail_template (
                    id,
                    subject,
                    heading,
                    closing
                )
                VALUES (?, ?, ?, ?)

                ON CONFLICT(id)
                DO UPDATE SET
                    subject = excluded.subject,
                    heading = excluded.heading,
                    closing = excluded.closing
                """,
                (
                    self.TEMPLATE_ID,
                    subject,
                    heading.strip(),
                    closing.strip(),
                ),
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()

    def get_alarm_previews(self, target_dates):
        """Đọc đúng Alarm Date và bằng chứng, độc lập bộ lọc trên giao diện."""
        import json
        from datetime import datetime
        dates = list(dict.fromkeys([target_dates] if isinstance(target_dates, str) else target_dates))
        for value in dates:
            datetime.strptime(value, "%Y%m%d")
        if not dates:
            return []
        conn = create_connection(self.database_path)
        try:
            conn.execute('BEGIN')
            alarms = [dict(row) for row in conn.execute(
                f"SELECT * FROM slot_fail_alarm WHERE alarm_date IN ({','.join('?' for _ in dates)}) "
                "ORDER BY alarm_date DESC,eqp,slot", dates)]
            # Prepare exact evidence ranges, then fetch all details in one query.
            ranges = []
            for alarm in alarms:
                alarm['evidence'] = json.loads(alarm['evidence_json'])
                for index, run in enumerate(alarm['evidence'].get('1', [])):
                    start_day, start_time = run['start'].split(' ')
                    end_day, end_time = run['end'].split(' ')
                    ranges.append((alarm['id'], index, alarm['eqp'], alarm['slot'],
                                   start_day.replace('-', ''), start_time,
                                   end_day.replace('-', ''), end_time))
            conn.execute('CREATE TEMP TABLE mail_ranges(alarm_id,run_index,eqp,slot,first_day,first_time,last_day,last_time)')
            conn.executemany('INSERT INTO mail_ranges VALUES(?,?,?,?,?,?,?,?)', ranges)
            rows = conn.execute("""SELECT r.alarm_id,r.run_index,
                    p.DATE,p.TIME,p.MODEL,p.LOTNO,p.SCRAPCODE,p.QTY
                FROM mail_ranges AS r CROSS JOIN prime_data AS p
                WHERE p.EQP=r.eqp AND p.SLOT=r.slot AND p.RESULT='FAIL'
                  AND p.DATE BETWEEN r.first_day AND r.last_day
                  AND (p.DATE>r.first_day OR p.TIME>=r.first_time)
                  AND (p.DATE<r.last_day OR p.TIME<=r.last_time)
                ORDER BY r.alarm_id,r.run_index,p.DATE DESC,p.TIME DESC,p.id DESC""").fetchall()
        finally:
            conn.close()
        # Group/filter/render only after releasing the shared read transaction.
        by_run = {}
        for row in rows:
            detail = dict(row)
            key = (detail.pop('alarm_id'), detail.pop('run_index'))
            by_run.setdefault(key, []).append(detail)
        for alarm in alarms:
            evidence = alarm['evidence']
            alarm['runs'] = [dict(run, details=run['tests'], different_scrap=True)
                             for run in evidence.get('different_scrap', [])]
            for index, run in enumerate(evidence.get('1', [])):
                details = [row for row in by_run.get((alarm['id'], index), [])
                           if row['MODEL'] in run['models'] and row['SCRAPCODE'] in run['scraps']]
                alarm['runs'].append(dict(run, details=details))
        return alarms
