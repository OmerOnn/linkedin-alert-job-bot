# 📬 LinkedIn Job Alert Bot  
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/OmerOnn/linkedin-alert-job-bot/run.yml?branch=main)](https://github.com/OmerOnn/linkedin-alert-job-bot/actions)  
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)  
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)  

🚀 **Automatically get LinkedIn job alerts sent straight to your Telegram!**  
This GitHub Action scans your Gmail for **LinkedIn job alerts**, filters jobs by your chosen **keywords**, and sends you real-time Telegram messages — fully automated & free.  

---

## ✨ Features

✅ **Automatic Gmail scanning** (IMAP)  
✅ **Filters jobs by keywords** (case-insensitive)  
✅ **Sends alerts directly to Telegram**  
✅ **Runs on GitHub Actions every 30 minutes**  
✅ **No servers needed – works entirely in the cloud**  

---

## ⚡ Quick Start

### **1️⃣ Fork This Repository**  
Click the **Fork** button on the top-right of this page.  

### **2️⃣ Add GitHub Secrets**  
Go to:  
`Settings → Secrets and variables → Actions → New repository secret`  

Add the following:

| Secret Name            | Example Value                                                              |
|------------------------|----------------------------------------------------------------------------|
| `EMAIL_USER`           | `youremail@gmail.com`                                                      |
| `EMAIL_PASS`           | Your Gmail **App Password** (see below)                                    |
| `TELEGRAM_BOT_TOKEN`   | Token from [@BotFather](https://t.me/BotFather)                             |
| `TELEGRAM_CHAT_ID`     | Your Telegram user ID from [@userinfobot](https://t.me/userinfobot)         |
| `KEYWORDS`             | `student,intern,ai,software engineer,developer`                            |

---

## 🔐 How to Get the Required Secrets

### ✅ **Gmail App Password** (for `EMAIL_PASS`)  
1. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)  
2. Select **Mail** → **Other (Custom name)** → enter "GitHub"  
3. Click **Generate** → copy the **16-character password**  
4. Paste it into the `EMAIL_PASS` secret  

*(If you don’t have 2FA, you can use your regular password — but it’s not recommended)*

### ✅ **Telegram Bot Setup**  
1. Open [@BotFather](https://t.me/BotFather) → `/newbot` → follow the steps  
2. Copy the bot token → set it as `TELEGRAM_BOT_TOKEN`  
3. Open [@userinfobot](https://t.me/userinfobot) → `/start` → copy your Telegram ID → set it as `TELEGRAM_CHAT_ID`  

---

## 🔍 Customizing Keywords  

Edit the `KEYWORDS` secret → add your own keywords (comma-separated).  
Matching is **case-insensitive**.

**Example:**  
student,intern,ai,software engineer,data scientist,backend developer

---

## ⏰ Workflow Schedule  

By default, it runs **every 30 minutes**.  
Change the schedule in `.github/workflows/run.yml`:  

yaml
schedule:
  - cron: '*/30 * * * *'  # every 30 minutes

---

# 📲 Example Telegram Alert
💼 New Job Opportunity!
📝 Title: AI Research Intern
🏢 Company: NVIDIA
📍 Location: Remote
🔗 https://www.linkedin.com/jobs/view/1234567890/

---

# 🖥️ Run Locally (Optional)
If you want to test it manually:
# 1. Clone the repo
git clone https://github.com/YOUR-USERNAME/YOUR-REPO.git
cd YOUR-REPO

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create a .env file with your secrets
EMAIL_USER=youremail@gmail.com
EMAIL_PASS=your_app_password
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_telegram_id
KEYWORDS=student,intern,ai,developer

# 4. Run the script
python main.py

---

# 📦 File Structure
📁 .github/workflows/
   └── run.yml           # GitHub Actions workflow
📄 main.py               # Main script (email parser + Telegram sender)
📄 requirements.txt      # Python dependencies
📄 README.md             # This file

---

# ❤️ Credits
Built with ❤️ by Omer
Fork it, improve it, and share it with other students or job hunters!
