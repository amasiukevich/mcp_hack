import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# In-memory set to track users who have shared contact info
shared_contacts = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a greeting message and ask for contact info if not already shared."""
    user_id = update.message.from_user.id
    if user_id not in shared_contacts:
        keyboard = [[KeyboardButton("Share phone number", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            "Welcome! Please share your phone number to continue.",
            reply_markup=reply_markup
        )
    else:
        keyboard = [[KeyboardButton("My orders")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "Welcome back! What would you like to do?",
            reply_markup=reply_markup
        )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages. If contact not shared, ask for phone number manually."""
    user_id = update.message.from_user.id
    if user_id not in shared_contacts:
        user_msg = update.message.text
        # Simple phone number validation (basic, can be improved)
        if user_msg and user_msg.replace('+', '').replace('-', '').isdigit() and 7 < len(user_msg) < 20:
            shared_contacts.add(user_id)
            keyboard = [[KeyboardButton("My orders")]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(f"Thanks! What would you like to do?", reply_markup=reply_markup)
        else:
            await update.message.reply_text(
                "You need to share your phone number to continue. Please enter it manually (with country code, e.g. +1234567890):"
            )
    else:
        user_msg = update.message.text
        await update.message.reply_text(f"Received {user_msg}")

async def request_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask the user to share their phone number."""
    keyboard = [
        [KeyboardButton("Share phone number", request_contact=True)]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Please share your phone number:",
        reply_markup=reply_markup
    )

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the contact information sent by the user and store user id."""
    contact = update.message.contact
    if contact:
        shared_contacts.add(contact.user_id)
        keyboard = [[KeyboardButton("My orders")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f"Thanks! Your phone number is {contact.phone_number}", reply_markup=reply_markup)

async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send hardcoded order data to the user."""
    user_id = update.message.from_user.id
    if user_id not in shared_contacts:
        await update.message.reply_text("Please share your phone number first.")
        return
    # Hardcoded order data
    orders = "Your orders:\n1. Order #12345 - Status: Delivered\n2. Order #67890 - Status: In progress"
    await update.message.reply_text(orders)

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
    app.add_handler(CommandHandler("my_orders", my_orders))
    app.add_handler(CommandHandler("phone", request_phone))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.Regex(r'^(My order|my order|My orders|my orders)$'), my_orders))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Start polling and run until interrupted
    app.run_polling()

if __name__ == "__main__":
    main()