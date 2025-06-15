import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# In-memory set to track users who have shared contact info
shared_contacts = set()

# Hardcoded shipment data for demonstration
shipments_data = [
    {
        "shipment_id": 7,
        "shipment_status": "in_transit",
        "eta": "2025-06-27T18:24:32.121214",
        "delivery_date": None,
        "dest_address": "1175 Reyes Crossing, East Olivia, KY 43005",
        "source_address": "8107 Rebecca Dale Apt. 074, Roytown, MA 76155"
    },
    {
        "shipment_id": 15,
        "shipment_status": "delivered",
        "eta": "2025-06-24T04:57:46.303766",
        "delivery_date": "2025-06-30T01:46:11.789912",
        "dest_address": "981 Keith Manors Apt. 090, Riosland, TN 70984",
        "source_address": "4193 Stephanie Terrace Apt. 816, East Matthew, ID 31132"
    },
    {
        "shipment_id": 35,
        "shipment_status": "pending",
        "eta": "2025-07-07T16:32:40.535072",
        "delivery_date": "2025-07-09T16:09:33.931047",
        "dest_address": "7884 Amber Roads Apt. 696, Aprilborough, VI 95700",
        "source_address": "3224 Anthony Dale Suite 238, West Georgefort, WA 19629"
    }
]

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
        keyboard = [[KeyboardButton("My shipments")]]
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
            keyboard = [[KeyboardButton("My shipments")]]
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
        keyboard = [[KeyboardButton("My shipments")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f"Thanks! What would you like to do?", reply_markup=reply_markup)

async def my_shipments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send formatted shipment data to the user."""
    user_id = update.message.from_user.id
    if user_id not in shared_contacts:
        await update.message.reply_text("Please share your phone number first.")
        return

    def format_shipment(shipment):
        status_map = {
            "in_transit": "🚚 <b>In Transit</b>",
            "delivered": "✅ <b>Delivered</b>",
            "pending": "⏳ <b>Pending</b>"
        }
        status = status_map.get(shipment["shipment_status"], shipment["shipment_status"])
        eta = shipment["eta"].replace('T', ' ') if shipment["eta"] else "N/A"
        delivery_date = shipment["delivery_date"].replace('T', ' ') if shipment["delivery_date"] else "N/A"
        return (
            f"<b>📦 Shipment #{shipment['shipment_id']}</b>\n"
            f"Status: {status}\n"
            f"<b>ETA:</b> {eta}\n"
            f"<b>Delivery Date:</b> {delivery_date}\n"
            f"<b>From:</b>\n{shipment['source_address']}\n"
            f"<b>To:</b>\n{shipment['dest_address']}\n"
            f"<code>─────────────────────────────</code>"
        )

    message = "<b>Your Shipments:</b>\n\n" + "\n\n".join([format_shipment(s) for s in shipments_data])
    await update.message.reply_text(message, parse_mode="HTML")

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
    app.add_handler(CommandHandler("my_shipments", my_shipments))
    app.add_handler(CommandHandler("phone", request_phone))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.Regex(r'^(My shipment|my shipment|My shipments|my shipments)$'), my_shipments))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Start polling and run until interrupted
    app.run_polling()

if __name__ == "__main__":
    main()