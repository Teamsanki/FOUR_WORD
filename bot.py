import logging
import asyncio
import nest_asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient
from googlesearch import search  # To fetch winner images & scores

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# MongoDB setup
mongo_client = MongoClient('mongodb+srv://tsgcoder:tsgcoder@cluster0.1sodg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = mongo_client['your_database']
collection = db['your_collection']

# Telegram bot token and IDs
TELEGRAM_TOKEN = '8151465566:AAFWFcBXPE4u7Fb1XeKrBKA8zlh2uGqHlZs'  # Replace with your actual token
CHANNEL_ID = '-1002256101563'  # Owner's channel ID
LOGGER_GROUP_ID = '-1002100433415'  # Logger group ID

# Function to fetch live score from Google
def fetch_live_score():
    query = "Live Cricket Score"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for result in search(query, num=1, stop=1):
        response = requests.get(result, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the live score (Google's score section)
            score_element = soup.find('div', class_='BNeawe iBp4i AP7Wnd')  # Google's live score class
            if score_element:
                return f"🏏 Live Score (Google): {score_element.text.strip()}"
            else:
                return "⚠️ Live score not found on Google."
    
    return "❌ Failed to fetch live score."

# Function to fetch match result from Google
def fetch_match_result():
    query = "Latest Cricket Match Result"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for result in search(query, num=1, stop=1):
        response = requests.get(result, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find match result (Google's match result section)
            result_element = soup.find('div', class_='BNeawe s3v9rd AP7Wnd')  # Google's result class
            if result_element:
                return result_element.text.strip()  # Example: "India won by 5 wickets"
    
    return None

# Function to fetch winning team image from Google
def fetch_winner_image(team_name):
    query = f"{team_name} cricket team latest match winner photo"
    
    for result in search(query, num=1, stop=1):
        return result  # Returns first image result URL
    
    return None

# Function to send final match result if the match is over
async def check_and_send_match_result(context: ContextTypes.DEFAULT_TYPE) -> None:
    match_result = fetch_match_result()
    
    if match_result:
        winning_team = match_result.split(" won")[0]  # Extract winning team
        image_url = fetch_winner_image(winning_team)

        if image_url:
            caption = f"🏆 {winning_team} won the match!\n\n🎉 {match_result} 🎉"
            await context.bot.send_photo(chat_id=CHANNEL_ID, photo=image_url, caption=caption)
        else:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=f"🏆 {winning_team} won the match!\n\n🎉 {match_result} 🎉")

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

# Function to handle new groups where the bot is added
async def new_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.message.chat
    group_info = {
        "group_id": chat.id,
        "group_name": chat.title,
        "added_by": update.message.from_user.username
    }
    collection.insert_one({"action": "new_group", "group_info": group_info})

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
