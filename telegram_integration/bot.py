import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a greeting message when /start is issued."""
    await update.message.reply_text("Hello! I am your bot.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Echo the user message with a prefix."""
    user_msg = update.message.text
    await update.message.reply_text(f"Received {user_msg}")

def main():
    # Load environment variables from .env
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not found in environment.")
        return

    # Initialize application
    app = Application.builder().token(token).build()

    # Handlers for commands and messages
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Start polling and run until interrupted
    app.run_polling()

if __name__ == "__main__":
    main()