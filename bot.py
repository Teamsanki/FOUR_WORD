import logging
import asyncio
import nest_asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
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
    
    return None  

# Function to fetch winner, score & image
def fetch_match_winner():
    query = "Today's Cricket Match Winner and Score"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for result in search(query, num=1, stop=1):
        response = requests.get(result, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            winner_element = soup.find('div', class_='BNeawe vvjwJb AP7Wnd')  
            score_element = soup.find_all('div', class_='BNeawe iBp4i AP7Wnd')
            image_element = soup.find('img')

            if winner_element and len(score_element) >= 2:
                return {
                    "winner": winner_element.text.strip(),
                    "score_winner": score_element[0].text.strip(),
                    "score_opponent": score_element[1].text.strip(),
                    "image": image_element['src'] if image_element else None,
                    "url": result
                }

    return None  

# Function to fetch cricket highlights images
def fetch_highlights_image():
    query = "Latest Cricket Match Highlights"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for result in search(query, num=1, stop=1):
        response = requests.get(result, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            image_element = soup.find('img')
            
            if image_element:
                return image_element['src']

    return None  

# Function to send Inline Keyboard with Buttons (Custom Built)
def get_inline_keyboard():
    keyboard = [
        [InlineKeyboardButton("🏏 Live Score", callback_data='live_score')],
        [InlineKeyboardButton("🏆 Match Winner", callback_data='match_winner')],
        [InlineKeyboardButton("👑 Owner", callback_data='owner_info')],
        [InlineKeyboardButton("📢 Join for Updates", url=CHANNEL_LINK)]
    ]
    return InlineKeyboardMarkup(keyboard)

# Function to send Reply Keyboard (Bottom Button)
def get_reply_keyboard():
    keyboard = [
        [KeyboardButton("📊 Get Live Score")]  # Custom button at the bottom
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Function to start the bot with Custom Keyboards
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    live_score = fetch_live_score()
    live_score_text = f"🏏 **Live Score:**\n{live_score}" if live_score else "❌ No live match right now!"

    welcome_message = f"🎉 Welcome {update.message.from_user.first_name} to the Cricket Live Score Bot! 🏏\n\n" \
                      "Press the button below to get live score or select other options."

    await update.message.reply_text(welcome_message, reply_markup=get_reply_keyboard())  # Reply Keyboard (Bottom)
    await update.message.reply_text(live_score_text, reply_markup=get_inline_keyboard())  # Inline Keyboard

# Function to handle Inline Button Clicks
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "live_score":
        live_score = fetch_live_score()
        text = f"🏏 **Live Score:**\n{live_score}" if live_score else "❌ No live match right now!"
        await query.message.reply_text(text, reply_markup=get_inline_keyboard())

    elif query.data == "match_winner":
        winner_info = fetch_match_winner()
        if winner_info:
            caption = f"🏆 **Match Winner:** {winner_info['winner']}\n\n" \
                      f"✅ **Winner Score:** {winner_info['score_winner']}\n" \
                      f"❌ **Opponent Score:** {winner_info['score_opponent']}\n\n" \
                      f"🔗 [Read More]({winner_info['url']})"

            if winner_info["image"]:
                await query.message.reply_photo(photo=winner_info["image"], caption=caption, parse_mode="Markdown", reply_markup=get_inline_keyboard())
            else:
                await query.message.reply_text(caption, parse_mode="Markdown", reply_markup=get_inline_keyboard())
        else:
            await query.message.reply_text("❌ No winner info found!", reply_markup=get_inline_keyboard())

    elif query.data == "owner_info":
        await query.message.reply_text(f"👑 **Bot Owner:** {OWNER_USERNAME}", reply_markup=get_inline_keyboard())

# Function to handle reply button clicks (Live Score)
async def reply_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "📊 Get Live Score":
        live_score = fetch_live_score()
        text = f"🏏 **Live Score:**\n{live_score}" if live_score else "❌ No live match found!"
        await update.message.reply_text(text, reply_markup=get_reply_keyboard())

# Function to send updates to the channel (Live Score or Highlights)
async def send_updates_to_channel(context: ContextTypes.DEFAULT_TYPE):
    live_score = fetch_live_score()

    if live_score:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=f"🏏 **Live Score Update:**\n{live_score}")
    else:
        image = fetch_highlights_image()
        if image:
            await context.bot.send_photo(chat_id=CHANNEL_ID, photo=image, caption="📸 Latest Cricket Highlights")
        else:
            await context.bot.send_message(chat_id=CHANNEL_ID, text="📢 No live match! Join our channel for updates.")

# Main function to run the bot
async def main():
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("📊 Get Live Score"), reply_button_click))

    job_queue = application.job_queue
    job_queue.run_repeating(send_updates_to_channel, interval=60, first=0)  

    await application.run_polling()

nest_asyncio.apply()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
