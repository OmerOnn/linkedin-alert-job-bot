import imaplib
import email
import os
import re
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from email.message import Message

# Load environment variables (used in GitHub Secrets or .env locally)
load_dotenv()

EMAIL_USER: str = os.getenv("EMAIL_USER", "")
EMAIL_PASS: str = os.getenv("EMAIL_PASS", "")
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")  # Your personal Telegram chat ID

# Keywords to look for in job alert emails (English + Hebrew)
KEYWORDS: list[str] = [
    "student position",
    "intern",
    "internship",
    "ai",
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "computer vision",
    "natural language processing",
    "nlp",
    "data science",
    "data scientist",
    "data analyst",
    "software engineer",
    "software engineering",
    "backend developer",
    "full stack",
    "algorithm",
    "algorithms",
    "research intern",
    "סטודנט"
]

def send_telegram_message(chat_id: str, message: str) -> None:
    """
    Sends a Telegram message to the specified chat ID.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    requests.post(url, data=data)

def extract_body(msg: Message) -> str:
    """
    Extracts plain text content from an email message.
    """
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                return part.get_payload(decode=True).decode(errors="ignore")
    else:
        return msg.get_payload(decode=True).decode(errors="ignore")
    return ""

def check_emails() -> None:
    """
    Connects to Gmail, reads unread emails from the last hour, and checks for relevant job alerts.
    If matching content is found, sends a formatted Telegram message with job title and link.
    """
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")

        result, data = mail.search(None, "UNSEEN")
        if result != "OK":
            return

        for num in data[0].split():
            result, msg_data = mail.fetch(num, "(RFC822)")
            if result != "OK":
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Check email timestamp (only process emails from the last hour)
            date_tuple = email.utils.parsedate_tz(msg["Date"])
            if date_tuple:
                msg_datetime = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple), tz=timezone.utc)
                if datetime.now(timezone.utc) - msg_datetime > timedelta(hours=1):
                    continue

            subject = msg["subject"] or ""
            body = extract_body(msg)

            # Process only if subject matches and any keyword appears in body
            if subject.strip() == "LinkedIn Job Alerts" and any(kw.lower() in body.lower() for kw in KEYWORDS):
                links = re.findall(r'https://www\.linkedin\.com/jobs/view/[^\s<>"]+', body)
                if links:
                    # Try to extract the line before the link as the job title
                    lines = body.splitlines()
                    title = "Unknown Position"
                    for i, line in enumerate(lines):
                        if links[0] in line and i > 0:
                            title_candidate = lines[i - 1].strip()
                            if title_candidate:
                                title = title_candidate
                            break

                    # Format and send the Telegram message
                    message = (
                        f"💼 New Internship Opportunity Detected!\n"
                        f"📝 Title: {title}\n"
                        f"🔗 {links[0]}"
                    )
                    send_telegram_message(TELEGRAM_CHAT_ID, message)

        mail.logout()

    except Exception as e:
        # Notify on error
        send_telegram_message(TELEGRAM_CHAT_ID, f"❗ Error while checking email: {str(e)}")

if __name__ == "__main__":
    check_emails()
