import imaplib
import email
import os
import re
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from email.message import Message

# Load credentials from environment (.env locally or GitHub Secrets)
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Keywords to search for (English + Hebrew)
KEYWORDS = [
    "student position", "intern", "internship", "ai", "artificial intelligence",
    "machine learning", "deep learning", "computer vision", "natural language processing",
    "nlp", "data science", "data scientist", "data analyst", "software engineer",
    "software engineering", "backend developer", "full stack", "algorithm",
    "algorithms", "research intern", "סטודנט"
]

def send_telegram_message(chat_id: str, message: str) -> None:
    """Send a Telegram message."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    requests.post(url, data=data)

def extract_body(msg: Message) -> str:
    """Extract plain text content from an email message."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition")):
                return part.get_payload(decode=True).decode(errors="ignore")
    else:
        return msg.get_payload(decode=True).decode(errors="ignore")
    return ""

def check_emails() -> None:
    """Check unread emails from the last hour and alert if relevant job info is found."""
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")

        result, data = mail.search(None, "UNSEEN")
        if result != "OK":
            return

        for num in reversed(data[0].split()):
            result, msg_data = mail.fetch(num, "(RFC822)")
            if result != "OK":
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Check timestamp (only emails from the last hour)
            date_tuple = email.utils.parsedate_tz(msg["Date"])
            if not date_tuple:
                continue
            msg_datetime = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple), tz=timezone.utc)
            if datetime.now(timezone.utc) - msg_datetime > timedelta(hours=1):
                continue

            subject = msg["subject"] or ""
            body = extract_body(msg)

            if any(kw.lower() in body.lower() for kw in KEYWORDS):
                links = re.findall(r'https://www\.linkedin\.com/jobs/[^\s<>")]+', body)
                if not links:
                    continue  # Don't proceed without a valid job link

                title = "Unknown Position"
                for line in body.splitlines():
                    if links[0] in line:
                        possible_title = line.replace(links[0], "").strip()
                        if possible_title:
                            title = possible_title
                        break
                else:
                    lines = body.splitlines()
                    for i, line in enumerate(lines):
                        if links[0] in line and i > 0:
                            title_candidate = lines[i - 1].strip()
                            if title_candidate:
                                title = title_candidate
                            break

                # Send message to Telegram and mark as read
                message = f"💼 New Internship Opportunity Detected!\n📝 Title: {title}\n🔗 {links[0]}"
                send_telegram_message(TELEGRAM_CHAT_ID, message)
                mail.store(num, '+FLAGS', '\\Seen')  # Mark as read only if message sent

        mail.logout()

    except Exception as e:
        send_telegram_message(TELEGRAM_CHAT_ID, f"❗ Error while checking email: {str(e)}")

if __name__ == "__main__":
    check_emails()
