import os
import time
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from datetime import datetime

# Your Cricket API key and endpoint
CRICKET_API_KEY = os.getenv("CRICKET_API_KEY", "9e143604-da14-46fa-8450-1c794febd46b")
CRICKET_API_URL = "https://api.cricapi.com/v1/currentMatches"  # CricAPI endpoint

# Logger group chat ID
LOGGER_GROUP_ID = os.getenv("LOGGER_GROUP_ID", "-1002100433415")

# Global variable to store the last live score (to avoid repeated messages)
last_score = None

# Function to fetch live scores
def fetch_live_score():
    global last_score
    try:
        # Adding a timestamp to avoid caching
        params = {"apikey": CRICKET_API_KEY, "t": int(time.time())}
        response = requests.get(CRICKET_API_URL, params=params)
        
        # Log the API response for debugging
        print(f"API Response: {response.json()}")  # Log the entire response to check if data is updating
        
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
            match_time = match.get("startTime", "N/A")

            # Creating the score message
            score_message = f"🏏 *{team1}* 🆚 *{team2}*\n"
            score_message += f"🔴 Score: {score}/{overs} overs\n"
            score_message += f"🕒 Match Time: {match_time}\n"
            score_message += f"⏳ Waiting for more updates... Stay tuned!"

            # Only add the score if it is different from the last score
            if score_message != last_score:
                last_score = score_message  # Update the last score
                live_scores.append(score_message)

        # If no new score, inform the user
        if not live_scores:
            return "The score is being updated. You will be notified once the new score is available."
        
        return "\n\n".join(live_scores)

    except Exception as e:
        return f"Error fetching score: {e}"

# Command: /start
def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Send welcome message to the user with owner info and support channel
    context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"Hello {user.first_name}!\n\n"
            "Welcome to the IPL Live Score Bot! 🏏\n"
            "I will now send you live cricket scores every 3 minutes. Stay tuned!\n\n"
            "This bot is owned by @TSGCODER.\n"
            "For support, join the channel: @matalbi_duniya"
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

    # Send the first live score immediately
    live_score = fetch_live_score()
    context.bot.send_message(chat_id=chat_id, text=live_score, parse_mode='Markdown')

    # Start sending updates every 3 minutes
    context.job_queue.run_repeating(
        send_live_score, interval=180, first=0, context=chat_id
    )

# Function to send live scores with interval time and match status
def send_live_score(context: CallbackContext) -> None:
    chat_id = context.job.context
    live_score = fetch_live_score()

    # Send the score update to the group first
    context.bot.send_message(chat_id=LOGGER_GROUP_ID, text="Live score update sent to user.")
    
    # Send the score update to the user
    context.bot.send_message(chat_id=chat_id, text=live_score, parse_mode='Markdown')

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
