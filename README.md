# 📬 LinkedIn Job Alert Bot

![Workflow Status](https://github.com/your-username/linkedin-alert-job-bot/actions/workflows/run.yml/badge.svg)

A GitHub Action that monitors your Gmail inbox for **LinkedIn job alert emails**, scans for jobs that match your favorite keywords (like `"student"`, `"AI"`, `"software engineer"`), and sends job listings directly to your **Telegram** via your own bot — completely free and automatic.

---

## 🚀 What It Does

- Connects to Gmail via IMAP  
- Checks new, unread LinkedIn job alert emails (within the past hour)  
- Parses job titles, company names, and locations from the HTML content  
- Matches job titles against your own keywords  
- Sends alerts as Telegram messages  

---

## 🔐 Required GitHub Secrets

| Secret Name            | Description                                                                |
|------------------------|----------------------------------------------------------------------------|
| `EMAIL_USER`           | Your Gmail address                                                         |
| `EMAIL_PASS`           | Gmail App Password (see instructions below)                                |
| `TELEGRAM_BOT_TOKEN`   | Telegram bot token from [@BotFather](https://t.me/BotFather)               |
| `TELEGRAM_CHAT_ID`     | Your user ID from [@userinfobot](https://t.me/userinfobot)                 |
| `KEYWORDS`             | Comma-separated list of keywords (e.g. `student,ai,intern,developer`)      |

---

## ✉️ How to Get a Gmail App Password

If you use 2-Step Verification:

1. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)  
2. Select **Mail** as the app and name it something like "GitHub"  
3. Google will generate a 16-character app password  
4. Use that for `EMAIL_PASS` in your GitHub secrets  

---

## 🤖 Setting Up Your Telegram Bot

1. Open [@BotFather](https://t.me/BotFather) in Telegram  
2. Send `/newbot` and follow the steps to create one  
3. Copy the token → this is your `TELEGRAM_BOT_TOKEN`  
4. Open [@userinfobot](https://t.me/userinfobot) and send `/start`  
5. It will return your Telegram ID → use it for `TELEGRAM_CHAT_ID`  

---

## 📲 Example Telegram Message

💼 New Job Opportunity!
📝 Title: AI Research Intern
🏢 Company: NVIDIA
📍 Location: Remote
🔗 https://www.linkedin.com/jobs/view/1234567890/

---

## 🔍 Customize Your Keyword List

Your job-matching keywords come from the `KEYWORDS` GitHub secret.

**Example value:**
student,intern,ai,software engineer,data scientist,backend developer


Matching is **case-insensitive** and checks if any keyword appears in the job title.

---

## ⏰ Workflow Schedule

This bot runs every **30 minutes** by default using GitHub Actions.

To change that, edit `.github/workflows/run.yml`:

```yaml
schedule:
  - cron: '*/30 * * * *'
You can adjust the frequency with crontab.guru.
```

---

##📦 File Structure

📁 .github/workflows/
   └── run.yml           → GitHub Actions workflow

📄 main.py               → Email parser and job detector  
📄 requirements.txt      → Python dependencies  
📄 README.md             → This file  

---

##❤️ Built with love by Omer
Feel free to fork, improve, and share this bot with other students or job hunters looking to automate their search!
