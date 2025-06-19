# bot.py
import logging
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

KEYWORDS_FILE = "keywords.json"
logging.basicConfig(level=logging.INFO)

# Load saved keywords (if any)
def load_keywords():
    try:
        with open(KEYWORDS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_keywords(data):
    with open(KEYWORDS_FILE, "w") as f:
        json.dump(data, f)

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hi! I will help you get job alerts from your email.\nPlease send me the keywords you'd like me to search for (comma separated).")

# Handle incoming messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_chat.id)
    keywords = [kw.strip().lower() for kw in update.message.text.split(",") if kw.strip()]
    if not keywords:
        await update.message.reply_text("❗ Please provide at least one keyword, separated by commas.")
        return

    data = load_keywords()
    data[user_id] = keywords
    save_keywords(data)
    await update.message.reply_text(f"✅ Keywords saved: {', '.join(keywords)}\nI will now look for these in your incoming emails.")

# Start the bot
if __name__ == '__main__':
    import os
    from dotenv import load_dotenv

    load_dotenv()
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()