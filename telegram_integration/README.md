# Telegram Bot Integration

This directory contains a simple Telegram bot implemented using `python-telegram-bot` library and `python-dotenv` for environment variable management.

## Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Rename `.env.example` to `.env` and set the `TELEGRAM_BOT_TOKEN` environment variable.
4. Run the bot:
   ```bash
   python bot.py
   ```

## Features

- `/start` command sends a "Hello! I am your bot." message.
- Bot replies to any text message with `Received <user_message>`.
