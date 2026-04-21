"""Load/save students, mark attendance, calculate weekly averages."""
from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Iterable

from utils import current_week_dates, fmt, is_weekday_mon_sat

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CSV_PATH = os.path.join(DATA_DIR, "students.csv")

PRESENT = "Present"
ABSENT = "Absent"


@dataclass
class Student:
    student_id: str
    name: str
    student_email: str
    parent_email: str
    attendance_log: dict[str, str] = field(default_factory=dict)

    def weekly_stats(self, today: date | None = None) -> dict:
        week = current_week_dates(today)
        marked = [(d, self.attendance_log.get(fmt(d))) for d in week]
        marked = [(d, status) for d, status in marked if status in (PRESENT, ABSENT)]
        total = len(marked)
        attended = sum(1 for _, s in marked if s == PRESENT)
        missed = total - attended
        avg = round((attended / total) * 100, 1) if total else 0.0
        return {
            "days_attended": attended,
            "days_missed": missed,
            "days_marked": total,
            "average": avg,
        }

    def average_attendance(self, today: date | None = None) -> float:
        return self.weekly_stats(today)["average"]


def _ensure_data_file() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CSV_PATH):
        seed_default_students()


def load_students() -> list[Student]:
    _ensure_data_file()
    students: list[Student] = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            log_raw = row.get("attendance_log", "").strip()
            try:
                log = json.loads(log_raw) if log_raw else {}
            except json.JSONDecodeError:
                log = {}
            students.append(
                Student(
                    student_id=row["student_id"],
                    name=row["name"],
                    student_email=row["student_email"],
                    parent_email=row["parent_email"],
                    attendance_log=log,
                )
            )
    return students


def save_students(students: Iterable[Student]) -> None:
    _ensure_data_file()
    fieldnames = ["student_id", "name", "student_email", "parent_email", "attendance_log"]
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for s in students:
            d = asdict(s)
            d["attendance_log"] = json.dumps(s.attendance_log)
            writer.writerow(d)


def mark_today_attendance(students: list[Student], updates: dict[str, str], target_date: date) -> None:
    """updates maps student_id -> 'Present' | 'Absent'."""
    if not is_weekday_mon_sat(target_date):
        return
    key = fmt(target_date)
    for s in students:
        if s.student_id in updates:
            status = updates[s.student_id]
            if status in (PRESENT, ABSENT):
                s.attendance_log[key] = status
    save_students(students)


def seed_default_students() -> None:
    """Pre-load 5 dummy students with a mix of low/medium/high attendance for current week."""
    from datetime import date as _d

    week = current_week_dates(_d.today())
    # We seed days *before today* with varied data so averages display nicely.
    today = _d.today()
    past_days = [d for d in week if d < today]

    def make_log(pattern: list[str]) -> dict[str, str]:
        # pattern aligned to past_days length; pad with ABSENT if shorter
        log = {}
        for i, d in enumerate(past_days):
            log[fmt(d)] = pattern[i] if i < len(pattern) else ABSENT
        return log

    seeds = [
        Student(
            "S001", "Aarav Sharma",
            "aarav@example.edu", "parent.aarav@example.com",
            make_log([PRESENT] * 6),  # high
        ),
        Student(
            "S002", "Priya Reddy",
            "priya@example.edu", "parent.priya@example.com",
            make_log([PRESENT, PRESENT, ABSENT, PRESENT, PRESENT, PRESENT]),  # high
        ),
        Student(
            "S003", "Rohan Verma",
            "rohan@example.edu", "parent.rohan@example.com",
            make_log([PRESENT, ABSENT, PRESENT, ABSENT, PRESENT, ABSENT]),  # medium ~50%
        ),
        Student(
            "S004", "Ananya Iyer",
            "ananya@example.edu", "parent.ananya@example.com",
            make_log([ABSENT, ABSENT, PRESENT, ABSENT, ABSENT, PRESENT]),  # low ~33%
        ),
        Student(
            "S005", "Kabir Singh",
            "kabir@example.edu", "parent.kabir@example.com",
            make_log([ABSENT, ABSENT, ABSENT, PRESENT, ABSENT, ABSENT]),  # very low
        ),
    ]
    os.makedirs(DATA_DIR, exist_ok=True)
    save_students(seeds)
