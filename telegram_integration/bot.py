import os
import urllib.parse

import aiohttp
from dotenv import load_dotenv
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# In-memory set to track users who have shared contact info
shared_contacts = dict()
api_base_url =  "http://0.0.0.0:8000"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a greeting message and ask for contact info if not already shared."""
    user_id = update.message.from_user.id
    if user_id not in shared_contacts:
        keyboard = [[KeyboardButton("Share phone number", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, one_time_keyboard=True, resize_keyboard=True
        )
        await update.message.reply_text(
            "Welcome! Please share your phone number to continue.",
            reply_markup=reply_markup,
        )
    else:
        keyboard = [[KeyboardButton("My shipments")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "Welcome back! What would you like to do?", reply_markup=reply_markup
        )


async def update_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send user message as shipment status update to the API and reply with API response."""
    user_id = update.message.from_user.id
    if user_id not in shared_contacts:
        user_msg = update.message.text
        # Simple phone number validation (basic, can be improved)
        if (
            user_msg
            and user_msg.replace("+", "").replace("-", "").isdigit()
            and 7 < len(user_msg) < 20
        ):
            shared_contacts[user_id] = user_msg
            keyboard = [[KeyboardButton("My shipments")]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(
                "Thanks! What would you like to do?", reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "You need to share your phone number to continue. Please enter it manually (with country code, e.g. +1234567890):"
            )
    else:
        user_msg = update.message.text
        contact_number = shared_contacts.get(user_id)
        encoded_contact_number = urllib.parse.quote_plus(contact_number) if contact_number else ''
        url = f"{api_base_url}/courier_shipment_updates?phone_number={encoded_contact_number}&shipment_query={user_msg}"
        headers = {"accept": "application/json"}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data="") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    reply = data.get("response", "Update successful.")
                else:
                    reply = f"Failed to update status. Error code: {resp.status}"
        await update.message.reply_text(reply)


async def request_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask the user to share their phone number."""
    keyboard = [[KeyboardButton("Share phone number", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )
    await update.message.reply_text(
        "Please share your phone number:", reply_markup=reply_markup
    )


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the contact information sent by the user and store user id."""
    user_id = update.message.from_user.id
    contact = update.message.contact
    if contact:
        
        shared_contacts[user_id] = contact.phone_number
        keyboard = [[KeyboardButton("My shipments")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "Thanks! What would you like to do?", reply_markup=reply_markup
        )


async def fetch_shipments(contact_number: str, api_base_url: str):
    """Fetch shipments from the API for the given contact number."""
    encoded_contact_number = urllib.parse.quote_plus(contact_number) if contact_number else ''
    url = f"{api_base_url}/get_courier_shipments?contact_number={encoded_contact_number}"
    headers = {"accept": "application/json"}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("response", [])
            else:
                return None


async def my_shipments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send formatted shipment data to the user."""
    user_id = update.message.from_user.id
    if user_id not in shared_contacts:
        await update.message.reply_text("Please share your phone number first.")
        return

    contact_number = shared_contacts.get(user_id)
    shipments_data = await fetch_shipments(contact_number, api_base_url)
    if shipments_data is None:
        await update.message.reply_text(
            "Failed to retrieve shipments. Please try again later."
        )
        return
    if not shipments_data:
        await update.message.reply_text("No shipments found for your contact number.")
        return

    def format_shipment(shipment):
        status_map = {
            "in_transit": "🚚 <b>In Transit</b>",
            "delivered": "✅ <b>Delivered</b>",
            "pending": "⏳ <b>Pending</b>",
        }
        status = status_map.get(
            shipment["shipment_status"], shipment["shipment_status"]
        )
        eta = shipment["eta"].replace("T", " ") if shipment["eta"] else "N/A"
        delivery_date = (
            shipment["delivery_date"].replace("T", " ")
            if shipment["delivery_date"]
            else "N/A"
        )
        return (
            f"<b>📦 Shipment #{shipment['shipment_id']}</b>\n"
            f"Status: {status}\n"
            f"<b>ETA:</b> {eta}\n"
            f"<b>Delivery Date:</b> {delivery_date}\n"
            f"<b>From:</b>\n{shipment['source_address']}\n"
            f"<b>To:</b>\n{shipment['dest_address']}\n"
            f"<code>─────────────────────────────</code>"
        )

    message = "<b>Your Shipments:</b>\n\n" + "\n\n".join(
        [format_shipment(s) for s in shipments_data]
    )
    await update.message.reply_text(message, parse_mode="HTML")


def main():
    # Load environment variables from .env
    load_dotenv(".env")
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
    app.add_handler(
        MessageHandler(
            filters.Regex(r"^(My shipment|my shipment|My shipments|my shipments)$"),
            my_shipments,
        )
    )
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, update_status))

    # Start polling and run until interrupted
    app.run_polling()


if __name__ == "__main__":
    main()
