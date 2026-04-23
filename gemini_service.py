"""Gemini API wrapper for generating personalized weekly attendance emails."""
from __future__ import annotations

import os

import google.generativeai as genai

_MODEL_NAME = "gemini-1.5-flash"
_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set in environment.")
    genai.configure(api_key=api_key)
    _configured = True


def _category(percent: float) -> str:
    if percent < 50:
        return "ALERT"
    if percent < 75:
        return "WARNING"
    return "APPRECIATION"


def generate_email_body(
    name: str,
    attendance_percent: float,
    days_attended: int,
    days_missed: int,
) -> str:
    """Generate a personalized email body using Gemini. Falls back to a templated
    message if the API call fails so the app continues to function."""
    category = _category(attendance_percent)
    prompt = f"""
You are an SGA assistant at GR University. Write a short, professional email to both the student and their parent.

Student: {name}
Weekly attendance: {attendance_percent}% (out of 6 days, attended {days_attended}, missed {days_missed})

Category:
- Below 50%: ALERT - urgent, serious tone, suggest meeting with SGA.
- 51-74%: WARNING - concerned but encouraging.
- 75% and above: APPRECIATION - proud, maintain good work.

This student falls into: {category}

Write only the email body (no subject line). Keep it warm, specific, and actionable.
Address both the student and the parent. Sign off as "SGA, GR University".
"""
    try:
        _configure()
        model = genai.GenerativeModel(_MODEL_NAME)
        resp = model.generate_content(prompt)
        text = (resp.text or "").strip()
        if text:
            return text
        raise RuntimeError("Empty response from Gemini")
    except Exception as e:
        return _fallback_body(name, attendance_percent, days_attended, days_missed, category, str(e))


def _fallback_body(name, percent, attended, missed, category, error) -> str:
    intro = {
        "ALERT": (
            f"This is an urgent note regarding {name}'s attendance this week. "
            f"Only {attended} of 6 days were attended ({percent}%). We strongly recommend "
            f"a meeting with the SGA at the earliest to discuss this together."
        ),
        "WARNING": (
            f"We wanted to share that {name}'s attendance this week was {percent}% "
            f"({attended}/6 days, missed {missed}). It's slipping a bit and we want to "
            f"help get it back on track. Please encourage steady attendance next week."
        ),
        "APPRECIATION": (
            f"Wonderful news - {name} maintained {percent}% attendance this week "
            f"({attended}/6 days). Thank you for the consistent effort. Keep it up!"
        ),
    }[category]
    return (
        f"Dear {name} and parent,\n\n"
        f"{intro}\n\n"
        f"Please reach out if you'd like to discuss anything.\n\n"
        f"Warm regards,\nSGA, GR University\n\n"
        f"(Note: AI generation unavailable - fallback message used. {error})"
    )
