"""Email sender. By default prints email to console (and returns the rendered
text for display in the Streamlit UI). Real SMTP code is included below,
commented out, with setup instructions.

To enable real SMTP delivery:
  1. Add to your environment / .env:
        SMTP_HOST=smtp.gmail.com
        SMTP_PORT=587
        SMTP_USER=youraddress@gmail.com
        SMTP_PASSWORD=your_app_password   # Gmail App Password, not your real password
        SMTP_FROM=youraddress@gmail.com
  2. Uncomment the `_send_via_smtp` body below.
  3. Set USE_SMTP = True (or rely on the env var SGA_USE_SMTP=1).
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv
load_dotenv() 

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

USE_SMTP = os.environ.get("SGA_USE_SMTP", "0") == "1"


@dataclass
class EmailRecord:
    to: list[str]
    subject: str
    body: str
    delivered: bool
    info: str


def send_weekly_email(
    student_email: str,
    parent_email: str,
    student_name: str,
    body: str,
) -> EmailRecord:
    subject = f"Weekly Attendance Report - {student_name}"
    recipients = [r for r in (student_email, parent_email) if r]

    if USE_SMTP:
        try:
            _send_via_smtp(recipients, subject, body)
            return EmailRecord(recipients, subject, body, True, "Sent via SMTP")
        except Exception as e:
            return EmailRecord(recipients, subject, body, False, f"SMTP error: {e}")

    # Default: log to console (visible in workflow logs) and return record
    print("=" * 60)
    print(f"[MOCK EMAIL] To: {', '.join(recipients)}")
    print(f"Subject: {subject}")
    print("-" * 60)
    print(body)
    print("=" * 60, flush=True)
    return EmailRecord(recipients, subject, body, True, "Logged to console (mock mode)")


def _send_via_smtp(recipients: list[str], subject: str, body: str) -> None:
    """Real SMTP delivery. Uncomment to enable."""
    # raise NotImplementedError(
    #     "SMTP delivery not enabled. Configure env vars and uncomment the body of _send_via_smtp."
    # )
    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASSWORD"]
    sender = os.environ.get("SMTP_FROM", user)
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(body, "plain"))
    
    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(sender, recipients, msg.as_string())
