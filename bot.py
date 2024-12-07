import os
import time
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
from datetime import datetime

# Your Cricket API key and endpoint
CRICKET_API_KEY = os.getenv("CRICKET_API_KEY", "9e143604-da14-46fa-8450-1c794febd46b")
CRICKET_API_URL = "https://api.cricapi.com/v1/currentMatches"  # CricAPI endpoint

# Logger group chat ID
LOGGER_GROUP_ID = os.getenv("LOGGER_GROUP_ID", "-1002100433415")

# Variable to track the last score sent
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
            # Extracting detailed information about each match
            team1 = match.get("teamInfo", [])[0].get("name", "Team 1")
            team2 = match.get("teamInfo", [])[1].get("name", "Team 2")
            score = match.get("score", [{}])[0].get("r", "--")
            overs = match.get("score", [{}])[0].get("o", "--")
            match_time = match.get("startTime", "N/A")

            # Stylish and unique message formatting with emojis and markdown
            score_message = f"🏏 *{team1}* 🆚 *{team2}*\n"
            score_message += f"🔴 Score: {score}/{overs} overs\n"
            score_message += f"🕒 Match Time: {match_time}\n"
            score_message += f"⏳ Waiting for more updates... Stay tuned!"
            
            live_scores.append(score_message)

        # If the score has changed, update the last_score and return the new score
        new_score = "\n\n".join(live_scores)
        if new_score != last_score:
            last_score = new_score
            return new_score
        else:
            return "The score is being updated. You will be notified once the new score is available."
    
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

# Function to handle when the bot is added to a group
def welcome_new_group(update: Update, context: CallbackContext) -> None:
    if update.message.new_chat_members:
        for member in update.message.new_chat_members:
            if member.id == context.bot.id:
                added_by_user = update.message.from_user
                context.bot.send_message(
                    chat_id=update.message.chat.id,
                    text=(
                        f"Thanks @{added_by_user.username} for adding me to the group! 🎉\n"
                        "I will notify you about live IPL scores whenever they change.\n\n"
                        "Stay tuned for score updates! 🏏"
                    ),
                )
                # Log this addition to the logger group
                context.bot.send_message(
                    chat_id=LOGGER_GROUP_ID,
                    text=(
                        f"🚨 New Group Addition 🚨\n\n"
                        f"User @{added_by_user.username} added the bot to the group: {update.message.chat.title}\n"
                    ),
                )

# Function to send live scores with interval time and match status
def send_live_score(context: CallbackContext) -> None:
    chat_id = context.job.context
    live_score = fetch_live_score()
    match_time_message = check_match_time()  # Check if it's time for the match to start
    context.bot.send_message(chat_id=chat_id, text=live_score + "\n\n" + match_time_message, parse_mode='Markdown')

# Function to check match time
def check_match_time():
    try:
        # Placeholder match start time, can be updated to actual data from the API
        match_start_time = "14:00"  # Example, replace with actual data fetched from the API
        
        # Calculate time until match starts
        current_time = datetime.now()
        match_time = datetime.strptime(match_start_time, "%H:%M")
        time_diff = match_time - current_time

        if time_diff.total_seconds() <= 0:
            return "Now it's time to join the match! 🚀"
        else:
            return f"⏳ Match starts in {str(time_diff).split('.')[0]}."

    except Exception as e:
        return "Match time info is not available."

if __name__ == "__main__":
    # Initialize the bot with token
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7787606800:AAGKnN5W0dTD05AYyCj5uGUxvQA-_LN58eA")
    updater = Updater(TELEGRAM_BOT_TOKEN)

    # Add handlers
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome_new_group))

    # Start the bot
    updater.start_polling()
    updater.idle()
