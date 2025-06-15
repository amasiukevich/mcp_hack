# 3PL Copilot

## Essentials

Demo page: http://plcopilot.xyz/

Telegram bot: https://t.me/3pl_copilot_bot

Email through which you can reach the bot: 3plcopilot@gmail.com

## Presentation

Pitch deck can be found [here](presentation.pdf)


## History

Project was created entirely from scratch during the hackathon.

What was developed:

1. Admin page through which user can connect email (only emails added to the Google Cloud Platform as test users due to app being in test mode), TMS and change the name of the telegram bot.
2. MCP server which can get and update data in the TMS.
3. Telegram bot which can recieve messages from couriers and ask MCP server to update the data in the TMS.
4. Gmail client which can recieves emails from the users and answer their questions about the shipments.


## Locall installation

1. Clone the repository

```
git clone --recurse-submodules https://github.com/Ogon-AI/3pl-copilot.git
```

2. Create a virtual environment

```
python -m venv venv && source venv/bin/activate
```

3. Install dependencies

```
pip install -r requirements.txt
```

4. Create .env file


```
OPENAI_API_KEY=<your_openai_api_key>
DB_PATH=sqlite:///database/test_shipments.db
ANTHROPIC_API_KEY=<your_anthropic_api_key>
TELEGRAM_BOT_TOKEN=<your_telegram_bot_token>
```

5. Create [credentials](https://developers.google.com/workspace/gmail/api/quickstart/python) for the Google Cloud Platform


6. Run the application

```
chmod +x run_all.sh
./run_all.sh
```
