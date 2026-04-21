"""SGA Attendance Tracker - Streamlit app.

Assumptions (per spec):
- The SGA is already authenticated; no login screen for the demo.
- Attendance is marked per student for the current day only (extendable to past days).
- The app detects Sunday automatically; a manual "Send Weekly Reports" trigger also exists.
- SMTP credentials are placeholders; emails are printed to console by default.
  Full SMTP code is included (commented) in email_sender.py with setup notes.
"""
from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from attendance_manager import (
    ABSENT,
    PRESENT,
    Student,
    load_students,
    mark_today_attendance,
    save_students,
)
from email_sender import EmailRecord, send_weekly_email
from gemini_service import generate_email_body
from utils import current_week_dates, fmt, is_sunday, is_weekday_mon_sat

load_dotenv()

st.set_page_config(page_title="SGA Attendance Tracker", page_icon="📚", layout="wide")


def _init_session() -> None:
    if "students" not in st.session_state:
        st.session_state.students = load_students()
    if "email_log" not in st.session_state:
        st.session_state.email_log = []  # list[EmailRecord]


def _refresh_students() -> None:
    st.session_state.students = load_students()


def render_header() -> None:
    st.title("SGA Attendance Tracker")
    st.caption("GR University - Weekly attendance and AI-generated reports")
    today = date.today()
    cols = st.columns(3)
    cols[0].metric("Today", today.strftime("%A, %d %b %Y"))
    cols[1].metric("Students assigned", len(st.session_state.students))
    low = sum(1 for s in st.session_state.students if s.average_attendance() < 75)
    cols[2].metric("Low-attendance students (<75%)", low)


def render_dashboard() -> None:
    students: list[Student] = st.session_state.students
    today = date.today()
    today_key = fmt(today)
    sunday = is_sunday(today)

    st.subheader("Dashboard")

    if sunday:
        st.info("Today is Sunday - no attendance marking. The weekly reports can be sent below.")
    elif not is_weekday_mon_sat(today):
        st.warning("Today is not a weekday (Mon-Sat). Marking is disabled.")

    fcols = st.columns([3, 2, 2])
    search = fcols[0].text_input("Search by name or ID", "").strip().lower()
    show_only_low = fcols[1].checkbox("Only low attendance (< 75%)", value=False)
    page_size = fcols[2].selectbox("Rows per page", [25, 50, 100, 200], index=0)

    filtered = [
        s for s in students
        if ((not show_only_low) or s.average_attendance() < 75)
        and (not search or search in s.name.lower() or search in s.student_id.lower())
    ]

    if not filtered:
        st.success("No students match the current filter.")
        return

    total_pages = max(1, (len(filtered) + page_size - 1) // page_size)
    page = st.number_input(
        f"Page (1 - {total_pages}) — showing {len(filtered)} of {len(students)}",
        min_value=1, max_value=total_pages, value=1, step=1,
    )
    start = (page - 1) * page_size
    visible = filtered[start:start + page_size]

    with st.form("attendance_form"):
        rows = []
        marking_widgets: dict[str, str] = {}

        # Header row
        h = st.columns([2, 1.2, 2.5, 2.5, 1.4, 1.5])
        h[0].markdown("**Name**")
        h[1].markdown("**ID**")
        h[2].markdown("**Student email**")
        h[3].markdown("**Parent email**")
        h[4].markdown("**Avg %**")
        h[5].markdown(f"**Today ({today.strftime('%a')})**")

        for s in visible:
            stats = s.weekly_stats(today)
            avg = stats["average"]
            low = avg < 75
            c = st.columns([2, 1.2, 2.5, 2.5, 1.4, 1.5])
            name_html = f"<span style='color:#b00020;font-weight:600'>⚠ {s.name}</span>" if low else s.name
            c[0].markdown(name_html, unsafe_allow_html=True)
            c[1].write(s.student_id)
            c[2].write(s.student_email)
            c[3].write(s.parent_email)
            c[4].write(f"{avg}%")
            current = s.attendance_log.get(today_key, PRESENT)
            disabled = sunday or not is_weekday_mon_sat(today)
            choice = c[5].selectbox(
                f"today_{s.student_id}",
                options=[PRESENT, ABSENT],
                index=0 if current == PRESENT else 1,
                key=f"sel_{s.student_id}",
                label_visibility="collapsed",
                disabled=disabled,
            )
            marking_widgets[s.student_id] = choice
            rows.append(
                {
                    "ID": s.student_id,
                    "Name": s.name,
                    "Avg %": avg,
                    "Days attended (this week)": stats["days_attended"],
                    "Days missed (this week)": stats["days_missed"],
                    "Days marked": stats["days_marked"],
                }
            )

        submitted = st.form_submit_button(
            "Save Today's Attendance",
            type="primary",
            disabled=sunday or not is_weekday_mon_sat(today),
        )
        if submitted:
            mark_today_attendance(students, marking_widgets, today)
            save_students(students)
            _refresh_students()
            st.success(f"Saved attendance for {today_key}.")
            st.rerun()

    with st.expander("Weekly summary table"):
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)


def render_weekly_email_section() -> None:
    students: list[Student] = st.session_state.students
    today = date.today()
    sunday = is_sunday(today)

    st.subheader("Weekly Reports")
    st.write(
        "On Sundays the app sends a personalized AI-generated email to each student and "
        "their parent. You can also trigger reports manually below."
    )

    col1, col2 = st.columns(2)
    auto_label = "Send Weekly Reports (Sunday)"
    send_auto = col1.button(auto_label, disabled=not sunday, type="primary" if sunday else "secondary")
    send_test = col2.button("Test Weekly Report (Send Now)")

    if send_auto or send_test:
        sent: list[EmailRecord] = []
        progress = st.progress(0.0)
        for i, s in enumerate(students, start=1):
            stats = s.weekly_stats(today)
            body = generate_email_body(
                name=s.name,
                attendance_percent=stats["average"],
                days_attended=stats["days_attended"],
                days_missed=stats["days_missed"],
            )
            rec = send_weekly_email(s.student_email, s.parent_email, s.name, body)
            sent.append(rec)
            progress.progress(i / max(len(students), 1))
        st.session_state.email_log = sent + st.session_state.email_log
        ok = sum(1 for r in sent if r.delivered)
        st.success(f"Generated and dispatched {ok}/{len(sent)} weekly reports.")

    if st.session_state.email_log:
        st.markdown("#### Email log")
        for rec in st.session_state.email_log[:20]:
            with st.expander(f"{'✅' if rec.delivered else '❌'} {rec.subject}  →  {', '.join(rec.to)}"):
                st.caption(rec.info)
                st.text(rec.body)


def render_sidebar() -> None:
    with st.sidebar:
        st.header("About")
        st.write(
            "Demo app for a single SGA managing 5 students. Attendance is persisted "
            "to `app/data/students.csv`."
        )
        st.divider()
        st.subheader("Week")
        for d in current_week_dates():
            st.write(("• " + d.strftime("%a %d %b")))
        st.divider()
        if st.button("Reset demo data"):
            from attendance_manager import seed_default_students
            seed_default_students()
            _refresh_students()
            st.success("Reseeded demo students.")
            st.rerun()


def main() -> None:
    _init_session()
    render_sidebar()
    render_header()
    st.divider()
    render_dashboard()
    st.divider()
    render_weekly_email_section()


if __name__ == "__main__":
    main()
