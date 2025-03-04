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
TELEGRAM_TOKEN = '8151465566:AAFWFcBXPE4u7Fb1XeKrBKA8zlh2uGqHlZs'  
CHANNEL_ID = '-1002256101563'  
CHANNEL_LINK = "https://t.me/cricketlivescorets"  
OWNER_USERNAME = "@ll_SANKI_II"  
TELEGRAPH_URL = "https://graph.org/file/d28c8d11173e3742404f6-af0a006bcdf0362c71.jpg"  # Replace with Cricket Image

# Function to fetch live score from Google
def fetch_live_score():
    query = "Live Cricket Score"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for result in search(query, num=1, stop=1):
        response = requests.get(result, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            score_element = soup.find('div', class_='BNeawe iBp4i AP7Wnd')  
            if score_element:
                return score_element.text.strip()
    
    return "❌ No Live Match Right Now"

# Function to fetch winner, score & opponent score
def fetch_match_winner():
    query = "Latest Cricket Match Winner site:espncricinfo.com OR site:icc-cricket.com OR site:gettyimages.com"
    headers = {"User-Agent": "Mozilla/5.0"}

    for result in search(query, num=3, stop=3):
        response = requests.get(result, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # 1️⃣ Try extracting Winner from OpenGraph meta tag
            winner_element = soup.find('meta', property='og:title')
            if winner_element:
                winner = winner_element['content']
            else:
                winner = soup.find('title').text.strip()

            # 2️⃣ Try extracting scores from Google-style divs
            score_elements = soup.find_all('div', class_='BNeawe iBp4i AP7Wnd')
            if len(score_elements) >= 2:
                score_winner = score_elements[0].text.strip()
                score_opponent = score_elements[1].text.strip()
            else:
                score_winner = "❌ Score Not Found"
                score_opponent = "❌ Score Not Found"

            return {
                "winner": winner,
                "score_winner": score_winner,
                "score_opponent": score_opponent
            }

    return None  # If nothing is found

# Function to send Reply Keyboard (Bottom Buttons)
def get_reply_keyboard():
    keyboard = [
        [KeyboardButton("📊 Get Live Score")],
        [KeyboardButton("🏆 Match Winner"), KeyboardButton("👑 Owner")],
        [KeyboardButton("📢 Join for Updates")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Function to start the bot with Custom Buttons
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    live_score = fetch_live_score()

    welcome_message = f"🎉 Welcome {update.message.from_user.first_name} to Cricket Live Score Bot! 🏏\n\n" \
                      "📊 Stay Updated with Live Scores, Match Highlights, and More!"

    await update.message.reply_photo(photo=TELEGRAPH_URL, caption=welcome_message, reply_markup=get_reply_keyboard())
    await update.message.reply_text(f"🏏 **Live Score:**\n{live_score}", reply_markup=get_reply_keyboard())

# Function to handle button clicks
async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📊 Get Live Score":
        live_score = fetch_live_score()
        await update.message.reply_text(f"🏏 **Live Score:**\n{live_score}", reply_markup=get_reply_keyboard())

    elif text == "🏆 Match Winner":
        winner_info = fetch_match_winner()
        if winner_info:
            caption = f"🏆 **Match Winner:** {winner_info['winner']}\n\n" \
                      f"✅ **Winner Score:** {winner_info['score_winner']}\n" \
                      f"❌ **Opponent Score:** {winner_info['score_opponent']}"
            await update.message.reply_text(caption, reply_markup=get_reply_keyboard())
        else:
            await update.message.reply_text("❌ No winner info found!", reply_markup=get_reply_keyboard())

    elif text == "👑 Owner":
        await update.message.reply_text(f"👑 **Bot Owner:** {OWNER_USERNAME}", reply_markup=get_reply_keyboard())

    elif text == "📢 Join for Updates":
        await update.message.reply_text(f"📢 **Join Our Channel for Latest Updates:**\n{CHANNEL_LINK}", reply_markup=get_reply_keyboard())

# Function to send updates to the channel (Only Winner & Score, No Image)
async def send_updates_to_channel(context: ContextTypes.DEFAULT_TYPE):
    live_score = fetch_live_score()

    if live_score and "❌" not in live_score:  # If Match is Live
        await context.bot.send_message(chat_id=CHANNEL_ID, text=f"🏏 **Live Score Update:**\n{live_score}")
    else:  # If No Match is Live, Send Winner Update
        winner_info = fetch_match_winner()
        if winner_info:
            caption = f"🏆 **Match Winner:** {winner_info['winner']}\n\n" \
                      f"✅ **Winner Score:** {winner_info['score_winner']}\n" \
                      f"❌ **Opponent Score:** {winner_info['score_opponent']}"
            await context.bot.send_message(chat_id=CHANNEL_ID, text=caption)
        else:
            await context.bot.send_message(chat_id=CHANNEL_ID, text="⚡ Stay Tuned for Cricket Updates!")

# Main function to run the bot
async def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT, handle_button_click))

    job_queue = application.job_queue
    job_queue.run_repeating(send_updates_to_channel, interval=60, first=0)  

    await application.run_polling()

nest_asyncio.apply()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
