import imaplib
import email
import os
import re
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from email.message import Message

# Load credentials from .env file or GitHub secrets
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Keywords for job detection
KEYWORDS = [
    "student position", "intern", "internship", "ai", "artificial intelligence",
    "machine learning", "deep learning", "computer vision", "natural language processing",
    "nlp", "data science", "data scientist", "data analyst", "software engineer",
    "software engineering", "backend developer", "full stack", "algorithm",
    "algorithms", "research intern", "סטודנט"
]

def send_telegram_message(chat_id: str, message: str) -> None:
    """
    Send a formatted message to Telegram using a bot token and chat ID.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    requests.post(url, data=data)

def extract_body(msg: Message) -> str:
    """
    Extract the plain text content from an email message.
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
    Main logic: connect to Gmail, read unread emails from the last hour,
    check for job opportunities, and notify via Telegram.
    """
    try:
        # Connect and login to Gmail via IMAP
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")

        # Get unread messages
        result, data = mail.search(None, "UNSEEN")
        if result != "OK":
            return

        for num in reversed(data[0].split()):
            result, msg_data = mail.fetch(num, "(RFC822)")
            if result != "OK":
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Skip emails older than 1 hour
            date_tuple = email.utils.parsedate_tz(msg["Date"])
            if not date_tuple:
                continue
            msg_datetime = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple), tz=timezone.utc)
            if datetime.now(timezone.utc) - msg_datetime > timedelta(hours=1):
                continue

            subject = msg["subject"] or ""
            body = extract_body(msg)

            # Skip if body doesn't contain any relevant keyword
            if not any(kw.lower() in body.lower() for kw in KEYWORDS):
                continue

            lines = body.splitlines()
            sent = False  # True if any message was sent

            for i, line in enumerate(lines):
                # Match LinkedIn job links from all /jobs/ paths
                links = re.findall(r'https://www\.linkedin\.com/jobs/[^\s<>")]+', line)
                if links:
                    link = links[0]

                    # Try to extract title from anchor tag if present
                    title_match = re.search(r'<a [^>]*>(.*?)</a>', line)
                    if title_match:
                        title = title_match.group(1).strip()
                    else:
                        # Fallback: remove link from line and use the rest
                        title = line.replace(link, "").strip() or "Unknown Position"

                    # Try to get company and location from next line
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

                    # Send Telegram message
                    message = (
                        f"💼 New Internship Opportunity Detected!\n"
                        f"📝 Title: {title}\n"
                        f"🏢 Company: {company}\n"
                        f"📍 Location: {location}\n"
                        f"🔗 {link}"
                    )
                    send_telegram_message(TELEGRAM_CHAT_ID, message)
                    sent = True

            # Mark email as read only if a message was sent
            if sent:
                mail.store(num, '+FLAGS', '\\Seen')

        mail.logout()

    except Exception as e:
        send_telegram_message(TELEGRAM_CHAT_ID, f"❗ Error while checking email: {str(e)}")

if __name__ == "__main__":
    check_emails()
