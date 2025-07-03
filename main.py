import imaplib
import email
import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from typing import List, Tuple, Optional, Dict

# Load environment variables from the .env file
load_dotenv()

class TelegramNotifier:
    """Handles sending messages via Telegram Bot API."""
    def __init__(self, token: str, chat_id: str):
        self.token: str = token
        self.chat_id: str = chat_id

    def send_message(self, message: str) -> None:
        """Send a formatted message to the specified Telegram chat."""
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        requests.post(url, data={
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        })

class EmailFetcher:
    """Responsible for connecting to Gmail and retrieving emails."""
    def __init__(self, user: str, password: str):
        self.user: str = user
        self.password: str = password
        self.connection: Optional[imaplib.IMAP4_SSL] = None

    def connect(self) -> None:
        """Establish a secure connection to Gmail via IMAP."""
        self.connection = imaplib.IMAP4_SSL("imap.gmail.com")
        self.connection.login(self.user, self.password)
        self.connection.select("inbox")

    def fetch_recent_emails(self, hours: int = 24) -> List[Tuple[bytes, email.message.Message]]:
        """Fetch emails from the last 'hours' timeframe (default: 24 hours)."""
        result, data = self.connection.search(None, 'ALL')
        if result != "OK":
            raise Exception("IMAP search failed.")

        emails: List[Tuple[bytes, email.message.Message]] = []
        for num in reversed(data[0].split()):
            result, msg_data = self.connection.fetch(num, "(RFC822)")
            if result != "OK":
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            date_tuple = email.utils.parsedate_tz(msg["Date"])
            if not date_tuple:
                continue

            msg_datetime = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple), tz=timezone.utc)
            if datetime.now(timezone.utc) - msg_datetime > timedelta(hours=hours):
                break

            emails.append((num, msg))
        return emails

    def mark_as_read(self, num: bytes) -> None:
        """Mark the specified email as read in the inbox."""
        self.connection.store(num, '+FLAGS', '\\Seen')

    def logout(self) -> None:
        """Logout from the Gmail session."""
        if self.connection:
            self.connection.logout()

class JobParser:
    """Parses HTML content of emails to extract job links and metadata."""
    def __init__(self, keywords: List[str]):
        self.keywords: List[str] = [kw.lower().strip() for kw in keywords]
        self.sent_job_ids: set = set()

    def extract_html(self, msg: email.message.Message) -> str:
        """Extract the HTML body from the email message."""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    return part.get_payload(decode=True).decode(errors="ignore")
        elif msg.get_content_type() == "text/html":
            return msg.get_payload(decode=True).decode(errors="ignore")
        return ""

    def extract_job_id(self, url: str) -> Optional[str]:
        """Extract the LinkedIn job ID from a URL."""
        match = re.search(r'/jobs/view/(\d+)', url)
        return match.group(1) if match else None

    def parse_jobs(self, html: str) -> List[Dict[str, str]]:
        """Scan HTML for LinkedIn job links matching the defined keywords."""
        soup = BeautifulSoup(html, "html.parser")
        jobs: List[Dict[str, str]] = []

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            raw_text = a_tag.get_text(strip=True) or a_tag.get("aria-label") or "Job"

            # Filter out non-job or irrelevant links
            if any(p in raw_text.lower() for p in ["your job alert", "see all jobs", "view all", "recommended jobs"]):
                continue
            if "/jobs/search" in href or "/comm/jobs/search" in href:
                continue

            job_id = self.extract_job_id(href)
            if not job_id or job_id in self.sent_job_ids:
                continue

            if "linkedin.com" in href and any(kw in raw_text.lower() for kw in self.keywords):
                # Extract title, company, and location
                bold_tag = a_tag.find("strong") or a_tag.find("b")
                title = bold_tag.get_text(strip=True) if bold_tag else None
                full_text = a_tag.get_text("·", strip=True)
                parts = [p.strip() for p in full_text.split("·")]
                title = title or parts[0] if len(parts) > 0 else "Unknown"
                company = parts[1] if len(parts) > 1 else "Unknown"
                location = parts[2] if len(parts) > 2 else "Unknown"

                jobs.append({
                    "id": job_id,
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": href
                })
                self.sent_job_ids.add(job_id)
        return jobs

class JobAlertBot:
    """Main controller class that orchestrates job checking and alerting."""
    def __init__(self):
        # Load configuration from environment
        self.email_user: str = os.getenv("EMAIL_USER", "")
        self.email_pass: str = os.getenv("EMAIL_PASS", "")
        self.telegram_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
        raw_keywords: str = os.getenv("KEYWORDS", "")
        keywords: List[str] = [kw.strip() for kw in raw_keywords.split(",") if kw.strip()]

        # Initialize core components
        self.notifier: TelegramNotifier = TelegramNotifier(self.telegram_token, self.telegram_chat_id)
        self.fetcher: EmailFetcher = EmailFetcher(self.email_user, self.email_pass)
        self.parser: JobParser = JobParser(keywords)

    def format_message(self, job: Dict[str, str]) -> str:
        """Format job details into a Telegram Markdown message."""
        return (
            f"💼 *New Job Opportunity!*\n"
            f"📝 *Title:* {job['title']}\n"
            f"🏢 *Company:* {job['company']}\n"
            f"📍 *Location:* {job['location']}\n"
            f"🔗 [Apply here]({job['url']})"
        )

    def run(self) -> None:
        """Main execution logic: fetch emails, extract jobs, send alerts."""
        try:
            self.fetcher.connect()
            emails = self.fetcher.fetch_recent_emails()

            for num, msg in emails:
                html = self.parser.extract_html(msg)
                if not html:
                    continue
                jobs = self.parser.parse_jobs(html)
                if jobs:
                    for job in jobs:
                        message = self.format_message(job)
                        self.notifier.send_message(message)
                    self.fetcher.mark_as_read(num)

        except Exception as e:
            # Notify Telegram on any runtime error
            self.notifier.send_message(f"❗ Error while checking email: {str(e)}")

        finally:
            # Always logout from email session
            self.fetcher.logout()

if __name__ == "__main__":
    bot = JobAlertBot()
    bot.run()
