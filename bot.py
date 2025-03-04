import logging
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# MongoDB setup
mongo_client = MongoClient('mongodb+srv://tsgcoder:tsgcoder@cluster0.1sodg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = mongo_client['your_database']
collection = db['your_collection']

# Telegram bot token and channel ID
TELEGRAM_TOKEN = '8151465566:AAFWFcBXPE4u7Fb1XeKrBKA8zlh2uGqHlZs'
CHANNEL_ID = '-1002256101563'  # Replace with your channel ID
OWNER_ID = '7548678061'

# Function to start the bot
def start(update: Update, context: CallbackContext) -> None:
    welcome_message = "Welcome to the Cricket Live Score Bot!"
    photo_url = "https://graph.org/file/d28c8d11173e3742404f6-af0a006bcdf0362c71.jpg"  # Replace with your photo URL
    keyboard = [[InlineKeyboardButton("Live Score", callback_data='live_score'),
                 InlineKeyboardButton("Contact Owner", callback_data='contact_owner')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_photo(photo=photo_url, caption=welcome_message, reply_markup=reply_markup)

    # Log user info
    user_info = {
        "user_id": update.message.from_user.id,
        "username": update.message.from_user.username,
        "first_name": update.message.from_user.first_name,
        "last_name": update.message.from_user.last_name
    }
    collection.insert_one({"action": "start", "user_info": user_info})

# Function to handle inline button presses
def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    if query.data == 'live_score':
        live_score = fetch_live_score()
        query.edit_message_text(text=f"Current Live Score: {live_score}")
        
        # Save to MongoDB
        collection.insert_one({"score": live_score})

    elif query.data == 'contact_owner':
        query.edit_message_text(text=f"Contact the owner at: @{OWNER_ID}")

# Function to fetch live score using web scraping
def fetch_live_score():
    url = "https://www.espncricinfo.com/"  # Replace with a reliable source for live scores
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the live score element (this will depend on the website's structure)
        # Example: This is a placeholder; you need to inspect the actual website to find the correct selectors
        score_element = soup.find('div', class_='live-score')  # Adjust this selector based on the actual website
        if score_element:
            return score_element.text.strip()
        else:
            return "Live score not found."
    else:
        return "Failed to fetch live score."

# Function to send live score updates to the channel
def send_live_score_to_channel(context: CallbackContext) -> None:
    live_score = fetch_live_score()
    context.bot.send_message(chat_id=CHANNEL_ID, text=f"Live Score Update: {live_score}")

# Function to handle new members in groups
def new_member(update: Update, context: CallbackContext) -> None:
    for member in update.message.new_chat_members:
        user_info = {
            "user_id": member.id,
            "username": member.username,
            "first_name": member.first_name,
            "last_name": member.last_name,
            "group_id": update.message.chat.id,
            "group_name": update.message.chat.title
        }
        collection.insert_one({"action": "new_member", "user_info": user_info})

        # Start sending live scores every minute
        context.job_queue.run_repeating(send_live_score_to_group, interval=60, first=0, context=update.message.chat.id)

# Function to send live score updates to the group
def send_live_score_to_group(context: CallbackContext) -> None:
    chat_id = context.job.context
    live_score = fetch_live_score()
    context.bot .send_message(chat_id=chat_id, text=f"Live Score Update: {live_score}")

# Main function to run the bot
def main() -> None:
    updater = Updater(TELEGRAM_TOKEN)
    
    # Register handlers
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_member))
    
    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
