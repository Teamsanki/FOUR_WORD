import logging
import asyncio
import nest_asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient
from googlesearch import search  # Fetch cricket news & images

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# MongoDB setup
mongo_client = MongoClient('mongodb+srv://tsgcoder:tsgcoder@cluster0.1sodg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = mongo_client['your_database']
collection = db['your_collection']

# Telegram bot token and IDs
TELEGRAM_TOKEN = '8151465566:AAFWFcBXPE4u7Fb1XeKrBKA8zlh2uGqHlZs'  # Replace with your actual token
CHANNEL_ID = '-1002256101563'  # Owner's channel
LOGGER_GROUP_ID = '-1002100433415'  # Logger group ID
CHANNEL_LINK = "https://t.me/cricketlivescorets"  # Your channel link
OWNER_USERNAME = "@ll_SANKI_II"  # Owner's Telegram Username

# Function to fetch live score from Google
def fetch_live_score():
    query = "Live Cricket Score"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for result in search(query, num=1, stop=1):
        response = requests.get(result, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract live score (Modify based on actual Google result structure)
            score_element = soup.find('div', class_='BNeawe iBp4i AP7Wnd')  

            if score_element:
                return score_element.text.strip()
    
    return None  # No live match found

# Function to fetch cricket highlights from Google
def fetch_cricket_highlights():
    query = "Latest Cricket Match Highlights"
    headers = {"User-Agent": "Mozilla/5.0"}

    for result in search(query, num=1, stop=1):
        response = requests.get(result, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract latest news headline & image
            headline_element = soup.find('div', class_='BNeawe vvjwJb AP7Wnd')
            image_element = soup.find('img')  

            if headline_element:
                return {
                    "headline": headline_element.text.strip(),
                    "image": image_element['src'] if image_element else None,
                    "url": result
                }

    return None  # No highlights found

# Function to send live scores or highlights to the channel
async def send_updates_to_channel(context: ContextTypes.DEFAULT_TYPE):
    live_score = fetch_live_score()

    if live_score:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=f"🏏 **Live Score Update:**\n{live_score}")
    else:
        highlight = fetch_cricket_highlights()
        if highlight:
            caption = f"🔥 **Cricket Highlight:** {highlight['headline']}\n🔗 [Read More]({highlight['url']})"
            if highlight['image']:
                await context.bot.send_photo(chat_id=CHANNEL_ID, photo=highlight['image'], caption=caption, parse_mode="Markdown")
            else:
                await context.bot.send_message(chat_id=CHANNEL_ID, text=caption, parse_mode="Markdown")

# Function to send live scores or highlights to groups
async def send_updates_to_groups(context: ContextTypes.DEFAULT_TYPE):
    live_score = fetch_live_score()

    if live_score:
        message = f"🏏 **Live Score Update:**\n{live_score}"
    else:
        highlight = fetch_cricket_highlights()
        if highlight:
            message = f"🔥 **Cricket Highlight:** {highlight['headline']}\n🔗 [Read More]({highlight['url']})"
        else:
            message = None  # No data available

    if message:
        # Fetch groups from database
        groups = db.groups.find({})
        for group in groups:
            try:
                keyboard = [[InlineKeyboardButton("📢 Join for Latest Updates", url=CHANNEL_LINK)]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await context.bot.send_message(chat_id=group['group_id'], text=message, reply_markup=reply_markup, parse_mode="Markdown")
            except:
                continue  # Skip errors (e.g., bot removed from group)

# Function to send owner details
async def send_owner_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(f"👑 **Bot Owner:** {OWNER_USERNAME}")

# Function to start the bot with Custom Keyboard
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = f"🎉 Welcome {update.message.from_user.first_name} to the Cricket Live Score Bot! 🏏\n\n" \
                      "Press the buttons below to get match details."

    # Custom Inline Keyboard
    keyboard = [
        [InlineKeyboardButton("🏏 Live Score", callback_data='live_score')],
        [InlineKeyboardButton("👑 Owner", callback_data='owner_info')],
        [InlineKeyboardButton("📢 Join for Latest Updates", url=CHANNEL_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

    # Log user info in MongoDB
    user_info = {
        "user_id": update.message.from_user.id,
        "username": update.message.from_user.username,
        "first_name": update.message.from_user.first_name,
        "last_name": update.message.from_user.last_name
    }
    collection.insert_one({"action": "start", "user_info": user_info})

# Function to handle new groups where the bot is added
async def new_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.message.chat
    group_info = {
        "group_id": chat.id,
        "group_name": chat.title,
        "added_by": update.message.from_user.username
    }
    collection.insert_one({"action": "new_group", "group_info": group_info})

# Main function to run the bot
async def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(send_owner_info, pattern='owner_info'))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_group))

    # Schedule live score updates every 60 seconds
    job_queue = application.job_queue
    job_queue.run_repeating(send_updates_to_channel, interval=60, first=0)  # To Owner's Channel
    job_queue.run_repeating(send_updates_to_groups, interval=60, first=0)  # To Groups

    await application.run_polling()

# Patch the running event loop
nest_asyncio.apply()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())  # Run the bot inside the existing event loop
