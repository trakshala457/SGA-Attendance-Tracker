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
    os.makedirs(DATA_DIR, exist_ok=True)
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
    """Pre-load 200 dummy students with a mix of low/medium/high attendance for current week.
    S001 is Trakshala with real emails; the rest are dummy."""
    from datetime import date as _d
    import random

    rng = random.Random(42)
    week = current_week_dates(_d.today())
    today = _d.today()
    past_days = [d for d in week if d < today]

    def make_log(target_pct: float) -> dict[str, str]:
        log = {}
        for d in past_days:
            log[fmt(d)] = PRESENT if rng.random() < target_pct else ABSENT
        return log

    first_names = [
        "Aarav", "Priya", "Rohan", "Ananya", "Kabir", "Diya", "Vivaan", "Isha",
        "Arjun", "Sara", "Reyansh", "Kavya", "Aditya", "Meera", "Krishna", "Tara",
        "Yash", "Nisha", "Dev", "Riya", "Karan", "Pooja", "Manav", "Sneha",
        "Aryan", "Aanya", "Ishaan", "Myra", "Vihaan", "Anika", "Rudra", "Aadhya",
        "Shaurya", "Avni", "Kabeer", "Pari", "Atharv", "Ira", "Veer", "Siya",
    ]
    last_names = [
        "Sharma", "Reddy", "Verma", "Iyer", "Singh", "Patel", "Kumar", "Gupta",
        "Mehta", "Rao", "Nair", "Joshi", "Bose", "Mishra", "Pillai", "Chopra",
        "Das", "Khan", "Malhotra", "Naidu", "Shetty", "Yadav", "Kulkarni", "Banerjee",
    ]

    seeds: list[Student] = [
        Student(
            "S001", "Trakshala",
            "trakshalatudgani@gmail.com", "tudganisatish@gmail.com",
            make_log(0.9),
        ),
    ]

    for i in range(2, 201):
        sid = f"S{i:03d}"
        name = f"{rng.choice(first_names)} {rng.choice(last_names)}"
        slug = name.lower().replace(" ", ".")
        # Mix attendance: ~25% low, ~25% medium, ~50% high
        roll = rng.random()
        if roll < 0.25:
            target = rng.uniform(0.20, 0.49)
        elif roll < 0.50:
            target = rng.uniform(0.55, 0.74)
        else:
            target = rng.uniform(0.78, 1.0)
        seeds.append(
            Student(
                sid, name,
                f"{slug}{i}@example.edu",
                f"parent.{slug}{i}@example.com",
                make_log(target),
            )
        )

    os.makedirs(DATA_DIR, exist_ok=True)
    save_students(seeds)
