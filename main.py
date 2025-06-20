import imaplib
import email
import os
import re
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from email.message import Message

# Load credentials from environment variables (.env locally / GitHub Secrets remotely)
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# List of keywords to detect job relevance (English + Hebrew)
KEYWORDS = [
    "student position", "intern", "internship", "ai", "artificial intelligence",
    "machine learning", "deep learning", "computer vision", "natural language processing",
    "nlp", "data science", "data scientist", "data analyst", "software engineer",
    "software engineering", "backend developer", "full stack", "algorithm",
    "algorithms", "research intern", "סטודנט"
]

def send_telegram_message(chat_id: str, message: str) -> None:
    """
    Send a Telegram message to a specific user using a bot.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    requests.post(url, data=data)

def extract_body(msg: Message) -> str:
    """
    Extract plain text content from an email message object.
    Handles multipart or plain text formats.
    """
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition")):
                return part.get_payload(decode=True).decode(errors="ignore")
    else:
        return msg.get_payload(decode=True).decode(errors="ignore")
    return ""

def check_emails() -> None:
    """
    Connects to Gmail, reads unread emails from the last hour,
    and sends Telegram alerts if any relevant job listings are found.
    Marks the email as read only if at least one alert was sent.
    """
    try:
        # Connect to Gmail
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")

        # Search for unread emails (UNSEEN)
        result, data = mail.search(None, "UNSEEN")
        if result != "OK":
            return

        for num in reversed(data[0].split()):
            result, msg_data = mail.fetch(num, "(RFC822)")
            if result != "OK":
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Filter by date: only process emails from the last hour
            date_tuple = email.utils.parsedate_tz(msg["Date"])
            if not date_tuple:
                continue
            msg_datetime = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple), tz=timezone.utc)
            if datetime.now(timezone.utc) - msg_datetime > timedelta(hours=1):
                continue

            subject = msg["subject"] or ""
            body = extract_body(msg)

            # Skip emails with no job-related keywords
            if not any(kw.lower() in body.lower() for kw in KEYWORDS):
                continue

            lines = body.splitlines()
            sent = False  # Will be set True if at least one alert is sent

            for i, line in enumerate(lines):
                # Look for job links (any path under /jobs/)
                links = re.findall(r'https://www\.linkedin\.com/jobs/[^\s<>")]+', line)
                if links:
                    link = links[0]
                    title = line.replace(link, "").strip() or "Unknown Position"

                    # Try to get company and location from the next line
                    company = "Unknown Company"
                    location = "Unknown Location"
                    if i + 1 < len(lines):
                        info_line = lines[i + 1].strip()
                        if "·" in info_line:
                            parts = [p.strip() for p in info_line.split("·", 1)]
                            if len(parts) == 2:
                                company, location = parts
                            else:
                                company = info_line

                    # Construct Telegram message
                    message = (
                        f"💼 New Internship Opportunity Detected!\n"
                        f"📝 Title: {title}\n"
                        f"🏢 Company: {company}\n"
                        f"📍 Location: {location}\n"
                        f"🔗 {link}"
                    )

                    send_telegram_message(TELEGRAM_CHAT_ID, message)
                    sent = True  # At least one job found

            if sent:
                mail.store(num, '+FLAGS', '\\Seen')  # Mark email as read only if a job was sent

        mail.logout()

    except Exception as e:
        send_telegram_message(TELEGRAM_CHAT_ID, f"❗ Error while checking email: {str(e)}")

if __name__ == "__main__":
    check_emails()
