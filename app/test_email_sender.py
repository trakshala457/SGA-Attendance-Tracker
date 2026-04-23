import os
from dotenv import load_dotenv
load_dotenv()

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

host = os.getenv("SMTP_HOST")
port = int(os.getenv("SMTP_PORT", 587))
user = os.getenv("SMTP_USER")
password = os.getenv("SMTP_PASSWORD")
sender = os.getenv("SMTP_FROM", user)

recipients = ["your_real_email@gmail.com"]  # CHANGE THIS TO YOUR EMAIL
subject = "Standalone Test"
body = "If you receive this, SMTP works."

if not all([host, user, password]):
    print("❌ Missing env vars. Check .env file.")
    exit(1)

msg = MIMEMultipart("alternative")
msg["Subject"] = subject
msg["From"] = sender
msg["To"] = ", ".join(recipients)
msg.attach(MIMEText(body, "plain"))

try:
    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(sender, recipients, msg.as_string())
    print("✅ Email sent! Check inbox/spam.")
except Exception as e:
    print(f"❌ Error: {e}")