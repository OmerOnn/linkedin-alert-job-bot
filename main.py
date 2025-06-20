import imaplib
import email
import os
import re
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from email.message import Message

# Load environment variables from .env file
load_dotenv()

# Email and Telegram credentials loaded from environment
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Load job keywords from environment and split by comma
KEYWORDS = [kw.strip().lower() for kw in os.getenv("KEYWORDS", "").split(",") if kw.strip()]

def send_telegram_message(chat_id: str, message: str) -> None:
    """
    Send a message to the specified Telegram chat using the bot token.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    requests.post(url, data=data)

def extract_body(msg: Message) -> str:
    """
    Extract the plain text body from an email message.
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
    Connect to Gmail, read unread emails from the last hour, check for job links,
    and send a Telegram message if a relevant job is found.
    """
    try:
        # Connect to Gmail via IMAP
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")

        # Search for unread emails
        result, data = mail.search(None, "UNSEEN")
        if result != "OK":
            return

        for num in reversed(data[0].split()):
            result, msg_data = mail.fetch(num, "(RFC822)")
            if result != "OK":
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Get email date and skip if older than 1 hour
            date_tuple = email.utils.parsedate_tz(msg["Date"])
            if not date_tuple:
                continue
            msg_datetime = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple), tz=timezone.utc)
            if datetime.now(timezone.utc) - msg_datetime > timedelta(hours=1):
                continue

            # Extract email content
            body = extract_body(msg)

            # Skip if no keyword match
            if not any(kw in body.lower() for kw in KEYWORDS):
                continue

            lines = body.splitlines()
            sent = False  # Flag to check if any alert was sent

            for i, line in enumerate(lines):
                # Look for job link inside HTML anchor tag
                match = re.search(r'<a[^>]+href="(https://www\.linkedin\.com/jobs/[^"]+)"[^>]*>(.*?)</a>', line)
                if match:
                    link = match.group(1).strip()  # Extracted job link
                    title = match.group(2).strip() or "Unknown Position"  # Extracted link text as title

                    company = "Unknown Company"
                    location = "Unknown Location"

                    # Try to extract company and location from next line
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if "·" in next_line:
                            parts = [p.strip() for p in next_line.split("·", 1)]
                            if len(parts) == 2:
                                company, location = parts

                    # Compose the Telegram message
                    message = (
                        f"💼 New Internship Opportunity Detected!\n"
                        f"📝 Title: {title}\n"
                        f"🏢 Company: {company}\n"
                        f"📍 Location: {location}\n"
                        f"🔗 {link}"
                    )

                    # Send the message and mark flag
                    send_telegram_message(TELEGRAM_CHAT_ID, message)
                    sent = True

            # Mark the email as read only if a job alert was sent
            if sent:
                mail.store(num, '+FLAGS', '\\Seen')

        mail.logout()

    except Exception as e:
        # Send Telegram alert on error
        send_telegram_message(TELEGRAM_CHAT_ID, f"❗ Error while checking email: {str(e)}")

if __name__ == "__main__":
    check_emails()
