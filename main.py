# main.py
import imaplib
import email
import os
import re
import json
import requests
from dotenv import load_dotenv

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
KEYWORDS_FILE = "keywords.json"

def get_keywords(chat_id):
    try:
        with open(KEYWORDS_FILE, "r") as f:
            data = json.load(f)
            return data.get(str(chat_id), [])
    except FileNotFoundError:
        return []

def send_telegram_message(chat_id, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    requests.post(url, data=data)

def extract_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                return part.get_payload(decode=True).decode(errors="ignore")
    else:
        return msg.get_payload(decode=True).decode(errors="ignore")
    return ""

def check_emails():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")

        result, data = mail.search(None, "UNSEEN")
        if result != "OK":
            return

        with open(KEYWORDS_FILE, "r") as f:
            users_keywords = json.load(f)

        for num in data[0].split():
            result, msg_data = mail.fetch(num, "(RFC822)")
            if result != "OK":
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            subject = msg["subject"] or ""
            body = extract_body(msg)

            for chat_id, keywords in users_keywords.items():
                if any(kw.lower() in subject.lower() or kw.lower() in body.lower() for kw in keywords):
                    links = re.findall(r'https://www\.linkedin\.com/jobs/view/\S+', body)
                    link_text = f"\n🔗 Job link: {links[0]}" if links else ""
                    message = f"📬 New job email matched your keywords!\nSubject: {subject}{link_text}"
                    send_telegram_message(chat_id, message)

        mail.logout()

    except Exception as e:
        for chat_id in get_all_chat_ids():
            send_telegram_message(chat_id, f"❗ Error while checking email: {str(e)}")

def get_all_chat_ids():
    try:
        with open(KEYWORDS_FILE, "r") as f:
            return list(json.load(f).keys())
    except FileNotFoundError:
        return []

if __name__ == "__main__":
    check_emails()