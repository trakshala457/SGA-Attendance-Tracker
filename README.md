# SGA Attendance Tracker

A Streamlit web app for Student Government Associates (SGAs) at GR University to:

- Mark daily attendance (Mon–Sat) for assigned students in one place
- Auto-calculate each student's weekly average attendance
- Flag low-attendance students (<75%)
- Generate personalized AI emails (via Google Gemini) for student + parent on Sunday
- Send (or mock-send) those emails via SMTP

## File structure

```
project/
├── .env.example
├── requirements.txt
├── README.md
└── app/
    ├── main.py                  # Streamlit UI + session state
    ├── attendance_manager.py    # CSV persistence + averages
    ├── gemini_service.py        # Gemini API email body generation
    ├── email_sender.py          # SMTP / console mock sender
    ├── utils.py                 # Date helpers
    ├── .streamlit/config.toml
    └── data/
        └── students.csv         # Auto-seeded with 5 demo students
```

## Setup

1. Install Python 3.11+
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate    # Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and add your Gemini API key
   (get one free at https://aistudio.google.com/app/apikey):
   ```
   GEMINI_API_KEY=...
   ```
5. Run:
   ```bash
   streamlit run app/main.py
   ```

The app starts at `http://localhost:5000` and auto-creates `app/data/students.csv`
with 5 demo students covering low/medium/high attendance.

## Email delivery

By default emails are **printed to console** and logged in the app's "Email log"
expander. To send real email, set the `SMTP_*` env vars in `.env`, set
`SGA_USE_SMTP=1`, and uncomment the SMTP block in `app/email_sender.py`.

## Notes

- The "Test Weekly Report (Send Now)" button bypasses the Sunday check.
- If the Gemini API call fails the app falls back to a templated message so it
  keeps working offline.
