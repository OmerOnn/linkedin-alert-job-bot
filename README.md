# 📬 LinkedIn Job Alert Bot

This GitHub Action monitors your Gmail inbox for new **LinkedIn job alert** emails that match specific keywords (like "student", "AI", "software engineer", etc).  
If a match is found, the bot sends a notification directly to your **Telegram** account via your personal bot.

---

## 🚀 What It Does

- Connects to your Gmail inbox using IMAP every 30 minutes
- Checks for **unread emails** with subject `LinkedIn Job Alerts`
- Filters only those received within the **last hour**
- Scans the email body for **predefined keywords**
- Sends a **Telegram message** via bot with the relevant job link

---

## 🔐 GitHub Secrets Required

To run this workflow, define the following secrets in your repository:

| Secret Name            | Description                                                                |
|------------------------|----------------------------------------------------------------------------|
| `EMAIL_USER`           | Your Gmail address (e.g., `you@gmail.com`)                                 |
| `EMAIL_PASS`           | A Gmail App Password (not your real password — see instructions below)     |
| `TELEGRAM_BOT_TOKEN`   | Token from [@BotFather](https://t.me/BotFather) when you create your bot   |
| `TELEGRAM_CHAT_ID`     | Your personal Telegram ID (see how to get it below)                        |

---

## ✉️ How to Get a Gmail App Password

If you have 2-Step Verification enabled on your Gmail account:

1. Go to [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Select **Mail** as the app, **Other (Custom name)** for device, and name it like "GitHub"
3. Google will generate a 16-character app password
4. Use that password as `EMAIL_PASS` in your GitHub secrets

---

## 🤖 How to Set Up a Telegram Bot

1. Open [@BotFather](https://t.me/BotFather) in Telegram
2. Send `/newbot` and follow the prompts
3. Save the **API token** → use it for `TELEGRAM_BOT_TOKEN`
4. Get your **Chat ID** using [@userinfobot](https://t.me/userinfobot)
   - Send `/start` to it
   - It will respond with your Telegram ID → use it for `TELEGRAM_CHAT_ID`

---

## 💡 Example Telegram Message

💼 New Internship Opportunity Detected!
📝 Title: AI Research Intern
🔗 https://www.linkedin.com/jobs/view/1234567890

---

## 🔍 Keyword Matching

Edit the keyword list in `main.py` to filter jobs by your interests:

```python
KEYWORDS = [
    "student", "intern", "internship", "ai", "software engineer", "nlp",
    "machine learning", "data science", "סטודנט"
]
```

The script will match emails that contain any of the keywords above.

---

## 🕒 Frequency
The workflow runs every 30 minutes by default.
You can change this in .github/workflows/run.yml:

schedule:
  - cron: '*/30 * * * *'  # every 30 minutes

---
## 🗂️ File Structure

```
📁 .github/workflows/
   └── run.yml        # GitHub Actions workflow config

📄 main.py            # Core Python script  
📄 requirements.txt   # Python dependencies  
📄 README.md          # You are here  
```

Built with ❤️ to help students and developers find job opportunities instantly.
