import imaplib
import email
import os
import re
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from email.message import Message

# Load environment variables from .env
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
KEYWORDS = [kw.strip().lower() for kw in os.getenv("KEYWORDS", "").split(",") if kw.strip()]

def send_telegram_message(chat_id: str, message: str) -> None:
    """Send a message via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    requests.post(url, data=data)

def extract_bodies(msg: Message) -> tuple[str, str]:
    """Extract both HTML and plain text bodies."""
    html_body = ""
    plain_body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype == "text/html":
                html_body = part.get_payload(decode=True).decode(errors="ignore")
            elif ctype == "text/plain":
                plain_body = part.get_payload(decode=True).decode(errors="ignore")
    else:
        payload = msg.get_payload(decode=True).decode(errors="ignore")
        if msg.get_content_type() == "text/html":
            html_body = payload
        else:
            plain_body = payload
    return html_body, plain_body

def check_emails() -> None:
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

            date_tuple = email.utils.parsedate_tz(msg["Date"])
            if not date_tuple:
                continue
            msg_datetime = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple), tz=timezone.utc)
            if datetime.now(timezone.utc) - msg_datetime > timedelta(hours=1):
                continue

            html_body, plain_body = extract_bodies(msg)
            content_to_check = html_body or plain_body

            if not any(kw in content_to_check.lower() for kw in KEYWORDS):
                continue

            sent = False
            search_sources = [html_body, plain_body]
            for body in search_sources:
                for match in re.finditer(r'<a[^>]+href="(https://www\.linkedin\.com/jobs/[^\"]+)"[^>]*>(.*?)</a>', body):
                    link = match.group(1).strip()
                    title = match.group(2).strip()
                    idx = body.find(match.group(0))
                    surrounding = body[idx:idx + 500]
                    company, location = "Unknown Company", "Unknown Location"
                    match_info = re.search(r'([A-Za-z0-9&.,\- ]+)\s*\u00b7\s*([A-Za-z\- ()]+)', surrounding)
                    if match_info:
                        company, location = match_info.group(1).strip(), match_info.group(2).strip()

                    message = (
                        f"\U0001F4BC New Internship Opportunity Detected!\n"
                        f"\U0001F4DD Title: {title}\n"
                        f"\U0001F3E2 Company: {company}\n"
                        f"\U0001F4CD Location: {location}\n"
                        f"\U0001F517 {link}"
                    )
                    send_telegram_message(TELEGRAM_CHAT_ID, message)
                    sent = True

            if sent:
                mail.store(num, '+FLAGS', '\\Seen')

        mail.logout()

    except Exception as e:
        send_telegram_message(TELEGRAM_CHAT_ID, f"\u2757 Error while checking email: {str(e)}")

if __name__ == "__main__":
    check_emails()
