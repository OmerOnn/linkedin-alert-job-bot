# import imaplib
# import email
# import os
# import requests
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from datetime import datetime, timedelta, timezone
# import re  # For extracting job IDs

# # Load environment variables
# load_dotenv()
# EMAIL_USER = os.getenv("EMAIL_USER", "")
# EMAIL_PASS = os.getenv("EMAIL_PASS", "")
# TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
# TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
# raw_keywords = os.getenv("KEYWORDS", "")
# KEYWORDS = [kw.strip().lower() for kw in raw_keywords.split(",") if kw.strip()]

# # Send message to Telegram
# def send_telegram_message(chat_id: str, message: str) -> None:
#     url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
#     requests.post(url, data={"chat_id": chat_id, "text": message})

# # Extract HTML from email
# def extract_html(msg) -> str:
#     if msg.is_multipart():
#         for part in msg.walk():
#             if part.get_content_type() == "text/html":
#                 return part.get_payload(decode=True).decode(errors="ignore")
#     elif msg.get_content_type() == "text/html":
#         return msg.get_payload(decode=True).decode(errors="ignore")
#     return ""

# # Main function
# def check_emails():
#     try:
#         mail = imaplib.IMAP4_SSL("imap.gmail.com")
#         mail.login(EMAIL_USER, EMAIL_PASS)
#         mail.select("inbox")

#         result, data = mail.search(None, 'ALL')
#         if result != "OK":
#             send_telegram_message(TELEGRAM_CHAT_ID, "❗ IMAP search failed.")
#             return

#         for num in reversed(data[0].split()):
#             result, msg_data = mail.fetch(num, "(RFC822)")
#             if result != "OK":
#                 continue

#             raw_email = msg_data[0][1]
#             msg = email.message_from_bytes(raw_email)

#             # Only process emails from last 2 hours
#             date_tuple = email.utils.parsedate_tz(msg["Date"])
#             if not date_tuple:
#                 continue
#             msg_datetime = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple), tz=timezone.utc)
#             if datetime.now(timezone.utc) - msg_datetime > timedelta(hours=48):
#                 break

#             subject = msg["Subject"] or "(no subject)"
#             html = extract_html(msg)
#             if not html:
#                 continue

#             soup = BeautifulSoup(html, "html.parser")
#             sent_job_ids = set()
#             sent = False

#             for a_tag in soup.find_all("a", href=True):
#                 href = a_tag["href"]
#                 raw_text = a_tag.get_text(strip=True) or a_tag.get("aria-label") or "Job"

#                 # Skip generic or unrelated links
#                 if any(phrase in raw_text.lower() for phrase in ["your job alert", "see all jobs", "view all", "recommended jobs"]):
#                     continue
#                 if "/jobs/search" in href or "/comm/jobs/search" in href:
#                     continue

#                 # Skip duplicates
#                 job_id_match = re.search(r"/jobs/view/(\d+)", href)
#                 job_id = job_id_match.group(1) if job_id_match else None
#                 if job_id in sent_job_ids:
#                     continue
#                 if job_id:
#                     sent_job_ids.add(job_id)

#                 if "linkedin.com" in href and any(kw in raw_text.lower() for kw in KEYWORDS):
#                     # Extract job title
#                     bold_tag = a_tag.find("strong") or a_tag.find("b")
#                     full_text = a_tag.get_text("·", strip=True)
#                     parts = [p.strip() for p in full_text.split("·")]

#                     title = bold_tag.get_text(strip=True) if bold_tag else parts[0] if len(parts) > 0 else "Unknown"
#                     company = parts[1] if len(parts) > 1 else "Unknown"
#                     location = parts[2] if len(parts) > 2 else "Unknown"

#                     message = (
#                         f"💼 New Job Opportunity!\n"
#                         f"📝 Title: {title}\n"
#                         f"🏢 Company: {company}\n"
#                         f"📍 Location: {location}\n"
#                         f"🔗 {href}"
#                     )
#                     send_telegram_message(TELEGRAM_CHAT_ID, message)
#                     send_telegram_message(TELEGRAM_CHAT_ID, "--------------------")
#                     sent = True

#             if sent:
#                 mail.store(num, '+FLAGS', '\\Seen')  # Only mark seen if we sent something

#         mail.logout()

#     except Exception as e:
#         send_telegram_message(TELEGRAM_CHAT_ID, f"❗ Error while checking email: {str(e)}")

# # Run it
# if __name__ == "__main__":
#     check_emails()





import imaplib
import email
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# Load environment variables from .env file
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
raw_keywords = os.getenv("KEYWORDS", "")
KEYWORDS = [kw.strip().lower() for kw in raw_keywords.split(",") if kw.strip()]

# Function to send a message to Telegram
def send_telegram_message(chat_id: str, message: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": message})

# Extract the HTML part of an email
def extract_html(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                return part.get_payload(decode=True).decode(errors="ignore")
    elif msg.get_content_type() == "text/html":
        return msg.get_payload(decode=True).decode(errors="ignore")
    return ""

# Main function to process emails
def check_emails():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")

        result, data = mail.search(None, 'ALL')
        if result != "OK":
            send_telegram_message(TELEGRAM_CHAT_ID, "❗ IMAP search failed.")
            return

        for num in reversed(data[0].split()):
            result, msg_data = mail.fetch(num, "(RFC822)")
            if result != "OK":
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Only check emails from the past 2 hours
            date_tuple = email.utils.parsedate_tz(msg["Date"])
            if not date_tuple:
                continue
            msg_datetime = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple), tz=timezone.utc)
            if datetime.now(timezone.utc) - msg_datetime > timedelta(hours=48):
                break

            subject = msg["Subject"] or "(no subject)"
            html = extract_html(msg)
            if not html:
                send_telegram_message(TELEGRAM_CHAT_ID, f"❗ No HTML body found in email: {subject}")
                continue

            soup = BeautifulSoup(html, "html.parser")
            sent = False

            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                raw_text = a_tag.get_text(strip=True) or a_tag.get("aria-label") or "Job"

                if any(phrase in raw_text.lower() for phrase in ["your job alert", "see all jobs", "view all", "recommended jobs"]):
                    continue
                if "/jobs/search" in href or "/comm/jobs/search" in href:
                    continue

                if "linkedin.com" in href and any(kw in raw_text.lower() for kw in KEYWORDS):
                    # Get the job title from bold tag if available
                    bold_tag = a_tag.find("strong") or a_tag.find("b")
                    title = bold_tag.get_text(strip=True) if bold_tag else None

                    # If no bold tag, try splitting the raw text at dots
                    full_text = a_tag.get_text("·", strip=True)
                    parts = [p.strip() for p in full_text.split("·")]

                    # Assign values gracefully
                    title = title or parts[0] if len(parts) > 0 else "Unknown"
                    company = parts[1] if len(parts) > 1 else "Unknown"
                    location = parts[2] if len(parts) > 2 else "Unknown"

                    message = (
                        f"💼 New Job Opportunity!\n"
                        f"📝 Title: {title}\n"
                        f"🏢 Company: {company}\n"
                        f"📍 Location: {location}\n"
                        f"🔗 {href}"
                    )
                    send_telegram_message(TELEGRAM_CHAT_ID, message)
                    send_telegram_message(TELEGRAM_CHAT_ID, "--------------------")
                    sent = True

            if not sent:
                send_telegram_message(TELEGRAM_CHAT_ID, f"❗ No jobs found in email: {subject}")
            else:
                mail.store(num, '+FLAGS', '\\Seen')

        mail.logout()

    except Exception as e:
        send_telegram_message(TELEGRAM_CHAT_ID, f"❗ Error while checking email: {str(e)}")

# Run the job check
if __name__ == "__main__":
    check_emails()
