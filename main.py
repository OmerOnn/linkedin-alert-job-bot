import imaplib
import email
import os
import re
import requests
from dotenv import load_dotenv
from email.message import Message

load_dotenv()

EMAIL_USER: str = os.getenv("EMAIL_USER", "")
EMAIL_PASS: str = os.getenv("EMAIL_PASS", "")
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_IDS: list[str] = ["1111468747"]  # Replace with your actual chat ID

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
    Sends a Telegram message to a specific chat ID using the bot token.

    Args:
        chat_id (str): The recipient's Telegram chat ID.
        message (str): The message text to send.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    requests.post(url, data=data)

def extract_body(msg: Message) -> str:
    """
    Extracts the plain text body from an email message.

    Args:
        msg (Message): An email.message.Message object.

    Returns:
        str: The decoded plain text body of the email.
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
    Connects to the Gmail inbox and checks for unread messages with a subject "LinkedIn Job Alerts".
    If the email body contains any of the specified keywords, it sends a Telegram notification.
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
            subject = msg["subject"] or ""
            body = extract_body(msg)

            for chat_id in TELEGRAM_CHAT_IDS:
                if subject.strip() == "LinkedIn Job Alerts" and any(kw.lower() in body.lower() for kw in KEYWORDS):
                    links = re.findall(r'https://www\.linkedin\.com/jobs/view/\S+', body)
                    link_text = f"\n🔗 Job link: {links[0]}" if links else ""
                    message = f"📬 New job email matched your keywords!\nSubject: {subject}{link_text}"
                    send_telegram_message(chat_id, message)

        mail.logout()

    except Exception as e:
        for chat_id in TELEGRAM_CHAT_IDS:
            send_telegram_message(chat_id, f"❗ Error while checking email: {str(e)}")

if __name__ == "__main__":
    check_emails()
