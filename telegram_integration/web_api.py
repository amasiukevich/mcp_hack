import os

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request

# Load environment variables
load_dotenv()
token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    raise RuntimeError("TELEGRAM_BOT_TOKEN not set in environment variables")

app = Flask(__name__)


@app.route("/set_name", methods=["POST"])
def set_name():
    """Endpoint to update the bot's display name."""
    data = request.get_json()
    if not data or "name" not in data:
        return jsonify({"error": 'Please provide "name" in JSON body'}), 400
    name = data["name"]
    url = f"https://api.telegram.org/bot{token}/setMyName"
    response = requests.post(url, data={"name": name})
    if response.ok:
        return jsonify(response.json()), 200
    return jsonify(response.json()), response.status_code


@app.route("/set_photo", methods=["POST"])
def set_photo():
    """Endpoint to update the bot's profile photo."""
    # Telegram does not support setting profile photos via API directly.


if __name__ == "__main__":
    # Run the web server on port 5000
    app.run(host="0.0.0.0", port=5000)
