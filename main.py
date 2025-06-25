# import imaplib
# import email
# import os
# import requests
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from datetime import datetime, timedelta, timezone

# # Load environment variables from .env file
# load_dotenv()
# EMAIL_USER = os.getenv("EMAIL_USER", "")
# EMAIL_PASS = os.getenv("EMAIL_PASS", "")
# TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
# TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
# raw_keywords = os.getenv("KEYWORDS", "")
# KEYWORDS = [kw.strip().lower() for kw in raw_keywords.split(",") if kw.strip()]

# # Function to send message to Telegram using your bot
# def send_telegram_message(chat_id: str, message: str) -> None:
#     url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
#     requests.post(url, data={"chat_id": chat_id, "text": message})

# # Extract the HTML part of an email
# def extract_html(msg) -> str:
#     if msg.is_multipart():
#         for part in msg.walk():
#             if part.get_content_type() == "text/html":
#                 return part.get_payload(decode=True).decode(errors="ignore")
#     elif msg.get_content_type() == "text/html":
#         return msg.get_payload(decode=True).decode(errors="ignore")
#     return ""

# # Main email-checking function
# def check_emails():
#     try:
#         # Connect to Gmail IMAP server and log in
#         mail = imaplib.IMAP4_SSL("imap.gmail.com")
#         mail.login(EMAIL_USER, EMAIL_PASS)
#         mail.select("inbox")

#         # Search for unread emails
#         result, data = mail.search(None, 'ALL')
#         if result != "OK":
#             send_telegram_message(TELEGRAM_CHAT_ID, "❗ IMAP search failed.")
#             return

#         # Process each unread email (most recent first)
#         for num in reversed(data[0].split()):
#             result, msg_data = mail.fetch(num, "(RFC822)")
#             if result != "OK":
#                 continue

#             raw_email = msg_data[0][1]
#             msg = email.message_from_bytes(raw_email)

#             # Check the email's timestamp — only process messages from last hour
#             date_tuple = email.utils.parsedate_tz(msg["Date"])
#             if not date_tuple:
#                 continue
#             msg_datetime = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple), tz=timezone.utc)
#             if datetime.now(timezone.utc) - msg_datetime > timedelta(hours=2):
#                 break # all next emails are over the hours

#             subject = msg["Subject"] or "(no subject)"
#             html = extract_html(msg)
#             if not html:
#                 send_telegram_message(TELEGRAM_CHAT_ID, f"❗ No HTML body found in email: {subject}")
#                 continue

#             soup = BeautifulSoup(html, "html.parser")
#             sent = False

#             # Look for all links (<a> tags) in the email
#             for a_tag in soup.find_all("a", href=True):
#                 href = a_tag["href"]
#                 title = a_tag.get_text(strip=True) or a_tag.get("aria-label") or "Job"

#                 # Skip generic headers or search links
#                 if any(phrase in title.lower() for phrase in ["your job alert", "see all jobs", "view all", "recommended jobs"]):
#                     continue
#                 if "/jobs/search" in href or "/comm/jobs/search" in href:
#                     continue

#                 # Match keywords in job title and confirm it's a LinkedIn link
#                 if "linkedin.com" in href and any(kw in title.lower() for kw in KEYWORDS):
                    
#                     # Try to grab company and location info from nearby <span>
#                     # Look for the <a>'s next meaningful sibling, which likely holds "Company · Location"
#                     meta = None
#                     next_node = a_tag.find_next_sibling()
#                     while next_node:
#                         text = next_node.get_text("·", strip=True)
#                         if "·" in text:
#                             meta = text
#                             break
#                         next_node = next_node.find_next_sibling()
                    
#                     parts = [p.strip() for p in meta.split("·")] if meta else []
#                     company = parts[0] if len(parts) > 0 else "Unknown"
#                     location = parts[1] if len(parts) > 1 else "Unknown"


#                     # Format message
#                     message = (
#                         f"💼 New Job Opportunity!\n"
#                         f"📝 Title: {title}\n"
#                         f"🏢 Company: {company}\n"
#                         f"📍 Location: {location}\n"
#                         f"🔗 {href}"
#                     )
#                     # Send the message to Telegram
#                     send_telegram_message(TELEGRAM_CHAT_ID, message)
#                     send_telegram_message(TELEGRAM_CHAT_ID, "--------------------")
#                     sent = True

#             # If nothing was matched and sent, notify no jobs found
#             if not sent:
#                 send_telegram_message(TELEGRAM_CHAT_ID, f"❗ No jobs found in email: {subject}")
#             else:
#                 # Mark the email as seen
#                 mail.store(num, '+FLAGS', '\\Seen')

#         # Logout when finished
#         mail.logout()

#     except Exception as e:
#         send_telegram_message(TELEGRAM_CHAT_ID, f"❗ Error while checking email: {str(e)}")

# # Run the check when the script is executed
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

# Function to send message to Telegram using your bot
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

# Main email-checking function
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

            # Check the email's timestamp
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

            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                raw_text = a_tag.get_text(strip=True) or a_tag.get("aria-label") or "Job"

                if any(phrase in raw_text.lower() for phrase in ["your job alert", "see all jobs", "view all", "recommended jobs"]):
                    continue
                if "/jobs/search" in href or "/comm/jobs/search" in href:
                    continue

                if "linkedin.com" in href and any(kw in raw_text.lower() for kw in KEYWORDS):
                    # Try to extract bolded job title
                    bold_tag = a_tag.find("strong") or a_tag.find("b")
                    title = bold_tag.get_text(strip=True) if bold_tag else raw_text

                    # Look for the sibling with "Company · Location"
                    meta = None
                    next_node = a_tag.find_next_sibling()
                    while next_node:
                        text = next_node.get_text("·", strip=True)
                        if "·" in text:
                            meta = text
                            break
                        next_node = next_node.find_next_sibling()

                    parts = [p.strip() for p in meta.split("·")] if meta else []
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
                    send_telegram_message(TELEGRAM_CHAT_ID, "--------------------")
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
