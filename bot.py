import logging
import asyncio
import nest_asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient
from googlesearch import search

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# MongoDB setup
mongo_client = MongoClient('mongodb+srv://tsgcoder:tsgcoder@cluster0.1sodg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = mongo_client['your_database']
collection = db['your_collection']

# Telegram bot token and IDs
TELEGRAM_TOKEN = 'YOUR_BOT_TOKEN'  # Replace with your actual token
CHANNEL_ID = '-1002256101563'  # Replace with your channel ID (OWNER's Channel)
LOGGER_GROUP_ID = '-1001234567890'  # Replace with your logger group ID

# Function to fetch live score using web scraping
def fetch_live_score():
    url = "https://www.espncricinfo.com/"  # Replace with a reliable source for live scores
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the live score element (Adjust selector based on the actual website)
        score_element = soup.find('div', class_='live-score')  # Adjust this selector
        if score_element:
            return f"🏏 Live Score Update: {score_element.text.strip()} 🏏"
        else:
            return "⚠️ Live score not found."
    else:
        return "❌ Failed to fetch live score."

# Function to check if a match is over
def fetch_match_result():
    url = "https://www.espncricinfo.com/live-cricket-score"  # Change to a reliable source
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        result_element = soup.find('div', class_='match-result')  # Adjust selector
        if result_element:
            return result_element.text.strip()
        else:
            return None
    else:
        return None

# Function to fetch team winner image from Google
def fetch_winner_image(team_name):
    query = f"{team_name} cricket team latest match winner photo"
    
    for result in search(query, num=1):
        return result  # Returns first image result URL
    
    return None

# Function to start the bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_message = f"🎉 Welcome {update.message.from_user.first_name} to the Cricket Live Score Bot! 🏏\n\nPress the button below to get live scores."
    keyboard = [[KeyboardButton("📊 Get Live Score")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

    # Log user info in MongoDB
    user_info = {
        "user_id": update.message.from_user.id,
        "username": update.message.from_user.username,
        "first_name": update.message.from_user.first_name,
        "last_name": update.message.from_user.last_name
    }
    collection.insert_one({"action": "start", "user_info": user_info})

    # Log new user in the LOGGER GROUP
    log_message = f"📢 *New User Started Bot*\n👤 Name: {update.message.from_user.full_name}\n🆔 ID: `{update.message.from_user.id}`\n🌍 Username: @{update.message.from_user.username if update.message.from_user.username else 'N/A'}"
    await context.bot.send_message(chat_id=LOGGER_GROUP_ID, text=log_message, parse_mode="Markdown")

# Function to send live scores to users who press the button
async def live_score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    live_score = fetch_live_score()
    await update.message.reply_text(live_score)

# Function to send live scores to the owner's channel every 1 min
async def send_live_score_to_channel(context: ContextTypes.DEFAULT_TYPE) -> None:
    live_score = fetch_live_score()
    await context.bot.send_message(chat_id=CHANNEL_ID, text=live_score)

# Function to send live scores to groups every 1 min
async def send_live_score_to_groups(context: ContextTypes.DEFAULT_TYPE) -> None:
    live_score = fetch_live_score()
    
    # Get all groups from MongoDB
    groups = db.groups.find({})
    for group in groups:
        try:
            await context.bot.send_message(chat_id=group['group_id'], text=live_score)
        except:
            continue  # Skip if error occurs (e.g., bot removed from group)

# Function to check and send match results
async def check_and_send_match_result(context: ContextTypes.DEFAULT_TYPE) -> None:
    match_result = fetch_match_result()
    
    if match_result:
        # Extract the winning team
        winning_team = match_result.split(" won")[0]  # Assuming result contains "Team X won by..."
        image_url = fetch_winner_image(winning_team)

        if image_url:
            caption = f"🏆 {winning_team} won the match!\n\n🎉 {match_result} 🎉"
            await context.bot.send_photo(chat_id=CHANNEL_ID, photo=image_url, caption=caption)
        else:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=f"🏆 {winning_team} won the match!\n\n🎉 {match_result} 🎉")

# Function to handle new groups where the bot is added
async def new_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.message.chat
    group_info = {
        "group_id": chat.id,
        "group_name": chat.title,
        "added_by": update.message.from_user.username
    }
    collection.insert_one({"action": "new_group", "group_info": group_info})

    # Log new group in the LOGGER GROUP
    log_message = f"📢 *New Group Added*\n🏠 Group: {chat.title}\n🆔 Group ID: `{chat.id}`\n👤 Added By: @{update.message.from_user.username if update.message.from_user.username else 'N/A'}"
    await context.bot.send_message(chat_id=LOGGER_GROUP_ID, text=log_message, parse_mode="Markdown")

# Main function to run the bot
async def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("📊 Get Live Score"), live_score))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_group))

    # Schedule live score updates every 60 seconds
    job_queue = application.job_queue
    job_queue.run_repeating(send_live_score_to_channel, interval=60, first=0)  # To Owner's Channel
    job_queue.run_repeating(send_live_score_to_groups, interval=60, first=0)  # To Groups
    job_queue.run_repeating(check_and_send_match_result, interval=600, first=0)  # Every 10 mins check match result

    await application.run_polling()

# Patch the running event loop
nest_asyncio.apply()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())  # Run the bot inside the existing event loop
