import imaplib  # For connecting to and reading from your email inbox
import email  # For parsing the email content
import os  # For accessing environment variables
import requests  # For sending messages to Telegram
from bs4 import BeautifulSoup  # For parsing the HTML content of emails
from dotenv import load_dotenv  # For loading sensitive credentials from .env file
from datetime import datetime, timedelta, timezone  # For handling timestamps
import re  # For extracting unique job IDs using patterns

# Load variables from .env like email login, Telegram credentials, and job keywords
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
raw_keywords = os.getenv("KEYWORDS", "")
KEYWORDS = [kw.strip().lower() for kw in raw_keywords.split(",") if kw.strip()]  # clean keyword list

# Sends a plain-text message to your Telegram bot
def send_telegram_message(chat_id: str, message: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": message})

# Extracts the HTML portion from an email message
def extract_html(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                return part.get_payload(decode=True).decode(errors="ignore")
    elif msg.get_content_type() == "text/html":
        return msg.get_payload(decode=True).decode(errors="ignore")
    return ""

# Main logic for scanning emails and sending job alerts
def check_emails():
    try:
        # Connect to Gmail using IMAP
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")

        # Fetch all emails (you could filter by UNSEEN for production)
        result, data = mail.search(None, 'ALL')
        if result != "OK":
            send_telegram_message(TELEGRAM_CHAT_ID, "❗ IMAP search failed.")
            return

        for num in reversed(data[0].split()):
            # Fetch each email by ID
            result, msg_data = mail.fetch(num, "(RFC822)")
            if result != "OK":
                continue

            # Parse the raw email
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Only process emails from the last 2 hours
            date_tuple = email.utils.parsedate_tz(msg["Date"])
            if not date_tuple:
                continue
            msg_datetime = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple), tz=timezone.utc)
            if datetime.now(timezone.utc) - msg_datetime > timedelta(hours=2):
                break

            subject = msg["Subject"] or "(no subject)"
            html = extract_html(msg)
            if not html:
                send_telegram_message(TELEGRAM_CHAT_ID, f"❗ No HTML body found in email: {subject}")
                continue

            soup = BeautifulSoup(html, "html.parser")
            sent = False
            sent_links = set()  # Track already-processed job IDs to prevent duplicates

            # Iterate through every hyperlink in the email
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                raw_text = a_tag.get_text(strip=True) or a_tag.get("aria-label") or "Job"

                # Skip generic or navigation links
                if any(phrase in raw_text.lower() for phrase in ["your job alert", "see all jobs", "view all", "recommended jobs"]):
                    continue
                if "/jobs/search" in href or "/comm/jobs/search" in href:
                    continue

                # Prevent duplicate job postings by checking job ID in URL
                job_id_match = re.search(r"/jobs/view/(\d+)", href)
                job_id = job_id_match.group(1) if job_id_match else None
                if job_id in sent_links:
                    continue
                if job_id:
                    sent_links.add(job_id)

                # Continue only if it's a LinkedIn job and matches any of your keywords
                if "linkedin.com" in href and any(kw in raw_text.lower() for kw in KEYWORDS):
                    # Try to extract just the bolded job title (sometimes HTML wraps the real title in <strong> or <b>)
                    bold_tag = a_tag.find("strong") or a_tag.find("b")
                    full_text = a_tag.get_text("·", strip=True)  # Uses the · separator LinkedIn puts between elements
                    parts = [p.strip() for p in full_text.split("·")]

                    # Assign title/company/location from parts list or fallback values
                    title = bold_tag.get_text(strip=True) if bold_tag else parts[0] if len(parts) > 0 else "Unknown"
                    company = parts[1] if len(parts) > 1 else "Unknown"
                    location = parts[2] if len(parts) > 2 else "Unknown"

                    # Format the message cleanly for Telegram
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

            # Let you know if nothing matched this email
            if not sent:
                send_telegram_message(TELEGRAM_CHAT_ID, f"❗ No jobs found in email: {subject}")
            else:
                # Mark the email as read
                mail.store(num, '+FLAGS', '\\Seen')

        mail.logout()

    except Exception as e:
        # Catch and report unexpected issues
        send_telegram_message(TELEGRAM_CHAT_ID, f"❗ Error while checking email: {str(e)}")

# Run the script when executed
if __name__ == "__main__":
    check_emails()
