import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters

# Your API Key from CricAPI
API_KEY = "9e143604-da14-46fa-8450-1c794febd46b"  # Replace with your CricAPI key
BASE_URL = f"https://cricapi.com/api/matches?apikey={API_KEY}"

# Logger group chat ID
LOGGER_GROUP_ID = os.getenv("LOGGER_GROUP_ID", "-1002100433415")

# Store the previous match status, score, and interval status
previous_match_status = {}
previous_score = {}
interval_status = {}

# Function to fetch live scores from CricAPI
def fetch_live_score():
    global previous_match_status, previous_score, interval_status  # Access global previous status and score variables
    try:
        response = requests.get(BASE_URL)
        response.raise_for_status()  # This will raise an error if the response code is not 200
        data = response.json()
        
        # Check if API returned error in the response
        if response.status_code != 200 or not data.get('matches'):
            return "No live matches currently available."

        live_scores = []
        score_updated = False  # Track if there is a score update
        
        for match in data.get("matches", []):
            match_id = match.get("unique_id", "")
            team1 = match.get("team1", "Team 1")
            team2 = match.get("team2", "Team 2")
            status = match.get("status", "")  # Match status (LIVE, COMPLETED, etc.)
            score = match.get("score", "")
            
            # Interval status update
            if status == "Live":
                if score != previous_score.get(match_id, score):
                    previous_score[match_id] = score
                    live_scores.append(
                        f"🟢 **{team1}** vs **{team2}**\n"
                        f"🔴 **Updated Score:** {score}\n"
                        f"---------------------------------"
                    )
                    score_updated = True  # Mark as score updated
                else:
                    live_scores.append(
                        f"🟢 **{team1}** vs **{team2}**\n"
                        f"🔴 **No update yet**\n"
                        f"⏳ We are monitoring the match. You’ll be notified once the score changes.\n"
                        f"---------------------------------"
                    )
            elif status == "Completed":
                live_scores.append(
                    f"⚪ **{team1}** vs **{team2}**\n"
                    f"✅ **Match Completed**\n"
                    f"Score: {score}\n"
                    f"---------------------------------"
                )

        # If no scores updated, send a reminder
        if not score_updated:
            return "🟢 I'm currently monitoring the match. You will be notified once the score is updated!"

        # If score updated, return the updated score
        if live_scores:
            return "\n".join(live_scores)
        else:
            return "No live matches available right now."

    except requests.exceptions.RequestException as e:
        return f"Error fetching score: {str(e)}"

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
            "I will now send you live cricket scores every 3 minutes. Stay tuned!"
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
    context.bot.send_message(chat_id=chat_id, text=live_score, parse_mode="Markdown")

    # Start sending updates every 3 minutes
    context.job_queue.run_repeating(
        send_live_score, interval=180, first=0, context=chat_id
    )

# Command: /update
def update(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    live_score = fetch_live_score()
    context.bot.send_message(chat_id=chat_id, text=live_score, parse_mode="Markdown")

# Command: /interval
def interval(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    match_status = []

    try:
        for match_id, status in interval_status.items():
            if status == "Interval":
                match_status.append(f"⏸️ Match in Interval")
            else:
                match_status.append(f"🏏 Match is Live")

        if match_status:
            context.bot.send_message(chat_id=chat_id, text="\n".join(match_status))
        else:
            context.bot.send_message(chat_id=chat_id, text="No match found.")
    except Exception as e:
        # Log the error and send a message to the user
        context.bot.send_message(chat_id=chat_id, text=f"Error: {e}")
        print(f"Error in interval_status: {e}")

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
    dispatcher.add_handler(CommandHandler("update", update))  # Changed command name to /update
    dispatcher.add_handler(CommandHandler("interval", interval))  # Changed command name to /interval
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_member))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_message))  # Handle other messages (like /start)

    # Start the bot
    updater.start_polling()
    updater.idle()
