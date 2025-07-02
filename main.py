import imaplib
import email
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import re

# Load environment variables from .env file
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER", "")  # Gmail username
EMAIL_PASS = os.getenv("EMAIL_PASS", "")  # Gmail password or app password
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")  # Telegram Bot token
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")  # Chat ID to send alerts to
raw_keywords = os.getenv("KEYWORDS", "")  # Comma-separated keywords
KEYWORDS = [kw.strip().lower() for kw in raw_keywords.split(",") if kw.strip()]  # Normalize keywords

# Send a message to a Telegram chat using Markdown format
def send_telegram_message(chat_id: str, message: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"  # Allows bold, italics, and clickable links
    })

# Extract HTML content from an email message
def extract_html(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                return part.get_payload(decode=True).decode(errors="ignore")
    elif msg.get_content_type() == "text/html":
        return msg.get_payload(decode=True).decode(errors="ignore")
    return ""

# Extract LinkedIn job ID from a job link URL
def extract_job_id(url: str) -> str:
    match = re.search(r'/jobs/view/(\d+)', url)
    return match.group(1) if match else None

# Main logic to connect to Gmail, read emails, and forward job matches to Telegram
def check_emails():
    sent_job_ids = set()  # To track and avoid sending duplicate job alerts

    try:
        # Connect securely to Gmail IMAP server
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")  # Open inbox folder

        # Search for all emails
        result, data = mail.search(None, 'ALL')
        if result != "OK":
            send_telegram_message(TELEGRAM_CHAT_ID, "❗ IMAP search failed.")
            return

        # Process emails from newest to oldest
        for num in reversed(data[0].split()):
            result, msg_data = mail.fetch(num, "(RFC822)")
            if result != "OK":
                continue

            # Parse the raw email
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Parse and convert email timestamp to UTC
            date_tuple = email.utils.parsedate_tz(msg["Date"])
            if not date_tuple:
                continue
            msg_datetime = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple), tz=timezone.utc)

            # Stop checking once emails are older than 24 hours
            if datetime.now(timezone.utc) - msg_datetime > timedelta(hours=24):
                break

            subject = msg["Subject"] or "(no subject)"  # Default subject if missing
            html = extract_html(msg)
            if not html:
                continue  # Skip emails without HTML content

            soup = BeautifulSoup(html, "html.parser")  # Parse HTML
            sent = False  # Flag if any job was sent from this email

            # Find all <a> tags with hrefs (i.e., links)
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                raw_text = a_tag.get_text(strip=True) or a_tag.get("aria-label") or "Job"

                # Skip irrelevant links
                if any(phrase in raw_text.lower() for phrase in ["your job alert", "see all jobs", "view all", "recommended jobs"]):
                    continue
                if "/jobs/search" in href or "/comm/jobs/search" in href:
                    continue

                # Extract LinkedIn job ID and skip if already sent
                job_id = extract_job_id(href)
                if not job_id or job_id in sent_job_ids:
                    continue

                # Check if job matches user-defined keywords
                if "linkedin.com" in href and any(kw in raw_text.lower() for kw in KEYWORDS):
                    # Try extracting title, company, and location from job link text
                    bold_tag = a_tag.find("strong") or a_tag.find("b")
                    title = bold_tag.get_text(strip=True) if bold_tag else None

                    full_text = a_tag.get_text("·", strip=True)
                    parts = [p.strip() for p in full_text.split("·")]

                    title = title or parts[0] if len(parts) > 0 else "Unknown"
                    company = parts[1] if len(parts) > 1 else "Unknown"
                    location = parts[2] if len(parts) > 2 else "Unknown"

                    # Format the message in Markdown
                    message = (
                        f"💼 *New Job Opportunity!*\n"
                        f"📝 *Title:* {title}\n"
                        f"🏢 *Company:* {company}\n"
                        f"📍 *Location:* {location}\n"
                        f"🔗 [Apply here]({href})"
                    )

                    # Send alert to Telegram and mark job ID as sent
                    send_telegram_message(TELEGRAM_CHAT_ID, message)
                    sent_job_ids.add(job_id)
                    sent = True

            # If at least one job was sent from this email, mark it as read
            if sent:
                mail.store(num, '+FLAGS', '\\Seen')

        mail.logout()

    except Exception as e:
        # Send error message to Telegram if script fails
        send_telegram_message(TELEGRAM_CHAT_ID, f"❗ Error while checking email: {str(e)}")

# Run the script
if __name__ == "__main__":
    check_emails()
