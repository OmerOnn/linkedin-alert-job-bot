import imaplib
import email
import os
import re
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from email.message import Message

# Load environment variables (used to store sensitive credentials like email and Telegram tokens)
load_dotenv()

# Email login credentials from environment variables
EMAIL_USER: str = os.getenv("EMAIL_USER", "")
EMAIL_PASS: str = os.getenv("EMAIL_PASS", "")

# Telegram bot token and chat ID (used to send alerts)
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

# Keywords to search for in job alert emails
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
    "llm",
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
    Sends a Telegram message using the Telegram Bot API.

    Args:
        chat_id (str): The Telegram chat ID to send the message to.
        message (str): The message text to send.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    requests.post(url, data=data)

def extract_body(msg: Message) -> str:
    """
    Extracts the plain text content from an email message.

    Args:
        msg (Message): The email message object.

    Returns:
        str: The plain text content of the email.
    """
    if msg.is_multipart():
        # Iterate through parts and return the first plain text part that is not an attachment
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                return part.get_payload(decode=True).decode(errors="ignore")
    else:
        # If message is not multipart, decode directly
        return msg.get_payload(decode=True).decode(errors="ignore")
    return ""

def check_emails() -> None:
    """
    Connects to the Gmail server, searches for unread emails from the last hour with subject
    "LinkedIn Job Alerts", and checks their body for relevant job-related keywords.
    If a match is found, a Telegram message is sent with the job link.
    """
    try:
        # Connect to Gmail via IMAP using SSL
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")

        # Search for all unread (UNSEEN) emails
        result, data = mail.search(None, "UNSEEN")
        if result != "OK":
            return

        # Iterate over each unread email
        for num in data[0].split():
            result, msg_data = mail.fetch(num, "(RFC822)")
            if result != "OK":
                continue

            # Parse the email content into a message object
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Extract the timestamp of the email and convert to datetime object
            date_tuple = email.utils.parsedate_tz(msg["Date"])
            if date_tuple:
                msg_datetime = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple), tz=timezone.utc)
                if datetime.now(timezone.utc) - msg_datetime > timedelta(hours=1):
                    continue  # Skip email if it's older than 1 hour

            # Get subject and body of email
            subject = msg["subject"] or ""
            body = extract_body(msg)

            # Only handle emails with exact subject match and relevant keywords
            if subject.strip() == "LinkedIn Job Alerts" and any(kw.lower() in body.lower() for kw in KEYWORDS):
                # Try to find a LinkedIn job link in the email body
                links = re.findall(r'https://www\.linkedin\.com/jobs/view/\S+', body)
                link_text = f"\n🔗 Job link: {links[0]}" if links else ""
                message = f"📬 New job email matched your keywords!\nSubject: {subject}{link_text}"
                send_telegram_message(TELEGRAM_CHAT_ID, message)

        mail.logout()

    except Exception as e:
        # In case of error, send a Telegram message with the exception text
        send_telegram_message(TELEGRAM_CHAT_ID, f"❗ Error while checking email: {str(e)}")

# Entry point of the script
if __name__ == "__main__":
    check_emails()
