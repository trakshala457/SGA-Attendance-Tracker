"""Automated follow-up tasks for students with attendance < 50%.

Tasks are persisted as JSON in app/data/follow_ups.json. One open task per
(student_id, week_start) is auto-created when a student's weekly attendance
drops below the critical threshold.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import date, timedelta
from typing import Iterable

from utils import current_week_dates, fmt

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
TASKS_PATH = os.path.join(DATA_DIR, "follow_ups.json")

CRITICAL_THRESHOLD = 50.0  # below this %, auto-create a follow-up


@dataclass
class FollowUpTask:
    task_id: str
    student_id: str
    student_name: str
    parent_email: str
    week_start: str          # YYYY-MM-DD (Monday of the week the task is for)
    due_date: str            # YYYY-MM-DD
    attendance_percent: float
    action: str              # human-readable instruction
    status: str              # "open" | "done"
    created_at: str          # YYYY-MM-DD


def _load_all() -> list[FollowUpTask]:
    if not os.path.exists(TASKS_PATH):
        return []
    try:
        with open(TASKS_PATH, encoding="utf-8") as f:
            raw = json.load(f)
        return [FollowUpTask(**t) for t in raw]
    except (json.JSONDecodeError, TypeError):
        return []


def _save_all(tasks: Iterable[FollowUpTask]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(TASKS_PATH, "w", encoding="utf-8") as f:
        json.dump([asdict(t) for t in tasks], f, indent=2)


def _friday_of(week_start: date) -> date:
    return week_start + timedelta(days=4)


def auto_generate_for_students(students, today: date | None = None) -> list[FollowUpTask]:
    """Inspect students; create open tasks for any with avg < CRITICAL_THRESHOLD
    that don't already have an open task for the current week. Returns the
    list of newly created tasks."""
    today = today or date.today()
    week = current_week_dates(today)
    week_start_str = fmt(week[0])
    due_str = fmt(_friday_of(week[0]))

    tasks = _load_all()
    existing_keys = {(t.student_id, t.week_start) for t in tasks if t.status == "open"}
    new: list[FollowUpTask] = []

    for s in students:
        stats = s.weekly_stats(today)
        # Need at least one marked day before flagging
        if stats["days_marked"] == 0:
            continue
        if stats["average"] >= CRITICAL_THRESHOLD:
            continue
        key = (s.student_id, week_start_str)
        if key in existing_keys:
            continue
        task = FollowUpTask(
            task_id=f"FU-{s.student_id}-{week_start_str}",
            student_id=s.student_id,
            student_name=s.name,
            parent_email=s.parent_email,
            week_start=week_start_str,
            due_date=due_str,
            attendance_percent=stats["average"],
            action=(
                f"Call {s.parent_email} by Friday ({due_str}) - "
                f"{s.name}'s attendance dropped to {stats['average']}%."
            ),
            status="open",
            created_at=fmt(today),
        )
        new.append(task)
        tasks.append(task)

    if new:
        _save_all(tasks)
    return new


def list_tasks(status: str | None = None) -> list[FollowUpTask]:
    tasks = _load_all()
    if status:
        tasks = [t for t in tasks if t.status == status]
    tasks.sort(key=lambda t: (t.status != "open", t.due_date, t.student_id))
    return tasks


def mark_done(task_id: str) -> bool:
    tasks = _load_all()
    changed = False
    for t in tasks:
        if t.task_id == task_id and t.status != "done":
            t.status = "done"
            changed = True
    if changed:
        _save_all(tasks)
    return changed


def reopen(task_id: str) -> bool:
    tasks = _load_all()
    changed = False
    for t in tasks:
        if t.task_id == task_id and t.status != "open":
            t.status = "open"
            changed = True
    if changed:
        _save_all(tasks)
    return changed


def open_count() -> int:
    return sum(1 for t in _load_all() if t.status == "open")
