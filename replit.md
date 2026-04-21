# SGA Attendance Tracker

## Overview
Streamlit web app for SGAs at GR University. Marks daily attendance Mon–Sat for assigned students, computes weekly averages, flags low attendance (<75%), and uses Google Gemini (`gemini-1.5-flash`) to generate personalized weekly emails for students and parents on Sunday (or via a manual test trigger). Emails are printed to console by default; full SMTP code is included (commented) in `app/email_sender.py`.

## Stack
- **UI/Backend**: Streamlit (Python 3.11)
- **LLM**: `google-generativeai` (Gemini 1.5 Flash)
- **Persistence**: CSV at `app/data/students.csv`
- **Email**: console mock (default) / `smtplib` SMTP (opt-in)

## Layout
```
app/
  main.py                # Streamlit UI
  attendance_manager.py  # CSV load/save + weekly stats
  gemini_service.py      # Gemini email body generation (with fallback)
  email_sender.py        # Console mock + commented SMTP
  utils.py               # Date helpers
  .streamlit/config.toml # port 5000, headless
  data/students.csv      # Auto-seeded with 5 demo students
requirements.txt
.env.example
```

## Run
- Workflow `Start application` → `streamlit run app/main.py` on port 5000
- Requires `GEMINI_API_KEY` secret
