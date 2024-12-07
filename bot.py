import os
import time
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters

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
            team_info = match.get("teamInfo", [])
            if len(team_info) < 2:
                continue  # Skip if team info is incomplete

            team1 = team_info[0].get("name", "Team 1")
            team2 = team_info[1].get("name", "Team 2")

            score_info = match.get("score", [])
            if len(score_info) < 1:
                continue  # Skip if score info is incomplete

            score = score_info[0].get("r", "--")  # Runs
            overs = score_info[0].get("o", "--")  # Overs

            # Stylish and formatted live score message
            live_scores.append(
                f"🟢 **{team1}** vs **{team2}**\n"
                f"🔴 **Score:** {score} / {overs} overs\n"
                f"---------------------------------"
            )

        if live_scores:
            return "\n".join(live_scores)
        else:
            return "No live matches available right now."

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
    context.bot.send_message(chat_id=chat_id, text=live_score)

    # Start sending updates every 3 minutes
    context.job_queue.run_repeating(
        send_live_score, interval=180, first=0, context=chat_id
    )

# Function to send live scores to user/group
def send_live_score(context: CallbackContext) -> None:
    chat_id = context.job.context
    live_score = fetch_live_score()
    context.bot.send_message(chat_id=chat_id, text=live_score, parse_mode="Markdown")

# When bot is added to a group
def new_member(update: Update, context: CallbackContext) -> None:
    # Check if bot has been added to the group
    if update.message.new_chat_members:
        for member in update.message.new_chat_members:
            if member.id == context.bot.id:  # Check if the bot was added
                group_name = update.message.chat.title
                chat_id = update.message.chat.id
                user = update.message.from_user

                # Notify the logger group
                context.bot.send_message(
                    chat_id=LOGGER_GROUP_ID,
                    text=(
                        f"🚨 Bot added to new group! 🚨\n\n"
                        f"Group: {group_name} ({chat_id})\n"
                        f"Added by: {user.first_name} (@{user.username})\n"
                    ),
                )

                # Send welcome message to the group
                context.bot.send_message(
                    chat_id=chat_id,
                    text=(
                        f"Hello {group_name}!\n\n"
                        "I'm the IPL Live Score Bot 🏏\n"
                        "I will provide you with live cricket scores every 3 minutes. Stay tuned!"
                    ),
                )

                # Send the first live score immediately to the group
                live_score = fetch_live_score()
                context.bot.send_message(chat_id=chat_id, text=live_score, parse_mode="Markdown")

                # Start sending updates every 3 minutes
                context.job_queue.run_repeating(
                    send_live_score, interval=180, first=0, context=chat_id
                )

# Function to handle messages (like /start and others)
def handle_message(update: Update, context: CallbackContext) -> None:
    if update.message.text == "/start":
        start(update, context)

if __name__ == "__main__":
    # Initialize the bot with token
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7787606800:AAGKnN5W0dTD05AYyCj5uGUxvQA-_LN58eA")
    updater = Updater(TELEGRAM_BOT_TOKEN)

    # Add handlers
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_member))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_message))  # Handle other messages (like /start)

    # Start the bot
    updater.start_polling()
    updater.idle()
