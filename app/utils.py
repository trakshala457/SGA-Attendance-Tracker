"""Date helpers for the SGA Attendance Tracker."""
from datetime import date, datetime, timedelta


def is_sunday(d: date | None = None) -> bool:
    d = d or date.today()
    return d.weekday() == 6


def is_weekday_mon_sat(d: date) -> bool:
    return d.weekday() <= 5


def current_week_dates(today: date | None = None) -> list[date]:
    """Return Mon..Sat dates of the week containing `today`."""
    today = today or date.today()
    monday = today - timedelta(days=today.weekday())
    return [monday + timedelta(days=i) for i in range(6)]


def fmt(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def parse(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()
