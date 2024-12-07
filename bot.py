import os
import time
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Your Cricket API key and endpoint
CRICKET_API_KEY = os.getenv("CRICKET_API_KEY", "9e143604-da14-46fa-8450-1c794febd46b")
CRICKET_API_URL = "https://api.cricapi.com/v1/currentMatches"  # CricAPI endpoint

# Logger group chat ID
LOGGER_GROUP_ID = os.getenv("LOGGER_GROUP_ID", "-1002100433415")

# Function to fetch live scores
def fetch_live_score():
    try:
        params = {"apikey": CRICKET_API_KEY}
        response = requests.get(CRICKET_API_URL, params=params)
        response.raise_for_status()
        matches = response.json().get("data", [])
        if not matches:
            return "No live matches available right now."

        live_scores = []
        for match in matches:
            team1 = match.get("teamInfo", [])[0].get("name", "Team 1")
            team2 = match.get("teamInfo", [])[1].get("name", "Team 2")
            score = match.get("score", [{}])[0].get("r", "--")
            overs = match.get("score", [{}])[0].get("o", "--")
            live_scores.append(f"{team1} vs {team2}: {score}/{overs} overs")

        return "\n".join(live_scores)
    except Exception as e:
        return f"Error fetching score: {e}"

# Command: /start
def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Send welcome message to the user
    context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"Hello {user.first_name}!\n\n"
            "Welcome to the IPL Live Score Bot! 🏏\n"
            "I will send you live cricket scores every 5 minutes. Stay tuned!"
        ),
    )

    # Log the user start action to the logger group
    context.bot.send_message(
        chat_id=LOGGER_GROUP_ID,
        text=(
            f"🚨 New User Alert! 🚨\n\n"
            f"User: {user.first_name} (@{user.username})\n"
            f"UserID: {user.id}\n"
            f"has started the bot!"
        ),
    )

    # Start sending updates every 5 minutes
    context.job_queue.run_repeating(
        send_live_score, interval=300, first=0, context=chat_id
    )

# Function to send live scores
def send_live_score(context: CallbackContext) -> None:
    chat_id = context.job.context
    live_score = fetch_live_score()
    context.bot.send_message(chat_id=chat_id, text=live_score)

if __name__ == "__main__":
    # Initialize the bot with token
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7787606800:AAGKnN5W0dTD05AYyCj5uGUxvQA-_LN58eA")
    updater = Updater(TELEGRAM_BOT_TOKEN)

    # Add handlers
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))

    # Start the bot
    updater.start_polling()
    updater.idle()
