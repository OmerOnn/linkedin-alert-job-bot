import imaplib
import email
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# Load environment variables
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
KEYWORDS = [kw.strip().lower() for kw in os.getenv("KEYWORDS", "").split(",") if kw.strip()]

for k in KEYWORDS:
    send_telegram_message(TELEGRAM_CHAT_ID, k)

def send_telegram_message(chat_id: str, message: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": message})

def extract_html(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                return part.get_payload(decode=True).decode(errors="ignore")
    elif msg.get_content_type() == "text/html":
        return msg.get_payload(decode=True).decode(errors="ignore")
    return ""

def check_emails():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")
        result, data = mail.search(None, "UNSEEN")
        if result != "OK":
            send_telegram_message(TELEGRAM_CHAT_ID, "❗ IMAP search failed.")
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

            subject = msg["Subject"] or "(no subject)"
            html = extract_html(msg)
            if not html:
                send_telegram_message(TELEGRAM_CHAT_ID, f"❗ No HTML body found in email: {subject}")
                continue

            soup = BeautifulSoup(html, "html.parser")
            sent = False

            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                title = a_tag.get_text(strip=True) or a_tag.get("aria-label") or "Job"
                send_telegram_message(TELEGRAM_CHAT_ID, str(title))
                send_telegram_message(TELEGRAM_CHAT_ID, str(href))
            
                if "linkedin.com" in href and any(kw in title.lower() for kw in KEYWORDS):
                    # Find the next <span> next to the <a> — where company and location might be
                    span = a_tag.find_next("span")
                    meta = span.get_text(strip=True) if span else "Unknown Company · Unknown Location"
                    parts = [p.strip() for p in meta.split("·")]
                    company = parts[0] if len(parts) > 0 else "Unknown"
                    location = parts[1] if len(parts) > 1 else "Unknown"
            
                    message = (
                        f"💼 New Job Opportunity!\n"
                        f"📝 Title: {title}\n"
                        f"🏢 Company: {company}\n"
                        f"📍 Location: {location}\n"
                        f"🔗 {href}"
                    )
                    send_telegram_message(TELEGRAM_CHAT_ID, message)
                    sent = True


            if not sent:
                send_telegram_message(TELEGRAM_CHAT_ID, f"❗ No jobs found in email: {subject}")
            else:
                mail.store(num, '+FLAGS', '\\Seen')

        mail.logout()

    except Exception as e:
        send_telegram_message(TELEGRAM_CHAT_ID, f"❗ Error while checking email: {str(e)}")

if __name__ == "__main__":
    check_emails()
