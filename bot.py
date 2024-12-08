import random
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.ext import ContextTypes
from PIL import Image, ImageDraw, ImageFont
import io
import nltk
from nltk.corpus import words
from pymongo import MongoClient

# Initialize the bot and set up logging
import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure NLTK words corpus is downloaded
nltk.download('words')

# MongoDB connection string (replace with your actual MongoDB URI)
MONGO_URL = "mongodb+srv://Teamsanki:Teamsanki@cluster0.jxme6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URL)
db = client["game_database"]  # Database name
leaderboard_collection = db["leaderboard"]  # Collection for leaderboard data
game_data_collection = db["game_data"]  # Collection for ongoing game data

# Token and owner ID (replace with your actual bot token and owner ID)
TOKEN = "7908847221:AAFo2YqgQ4jYG_Glbp96sINg79zF8T6EWoo"
OWNER_ID = "7877197608"

# Start the bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    await update.message.reply_text(f"Hello {user.first_name}, welcome to the Word Game! Use /game to start playing.")

# Game command
async def game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    opponent = find_opponent(user.id)

    if opponent:
        game_data = {
            "user_id": user.id,
            "opponent_id": opponent["user_id"],
            "level": 1,
            "lives": 3,
            "score": 0,
            "turn": user.id
        }
        game_data_collection.insert_one(game_data)
        await update.message.reply_text(f"Game started with {opponent['first_name']}. Your turn will come soon.")
        await context.bot.send_message(chat_id=opponent["user_id"], text=f"Game started with {user.first_name}. Your turn will come soon.")
        await send_word(update, context)
    else:
        await update.message.reply_text("No opponent available. Please try again later.")

# Find an opponent randomly
def find_opponent(user_id):
    # Fetch random user from the game data collection who is not currently in a game
    opponent = game_data_collection.find_one({"turn": {"$exists": False}})
    if opponent and opponent["user_id"] != user_id:
        return opponent
    return None

# Send word for current level
async def send_word(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    game_data = game_data_collection.find_one({"user_id": update.message.from_user.id})
    level = game_data["level"]
    word_length = level + 2  # Adjust word length based on level
    word = generate_word(word_length)
    await context.bot.send_message(chat_id=update.message.from_user.id, text=f"Level {level}: Write a sentence using the word: {word}")

# Generate random word based on length
def generate_word(length):
    word_list = ["apple", "banana", "cherry", "orange", "grape", "melon", "kiwi", "pear"]
    return random.choice([w for w in word_list if len(w) == length])

# Process user response
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    game_data = game_data_collection.find_one({"user_id": user_id})
    
    if game_data and user_id == game_data["turn"]:
        await process_turn(update, context)
    else:
        await update.message.reply_text("It's not your turn yet.")

# Process each turn
async def process_turn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    game_data = game_data_collection.find_one({"user_id": user_id})
    sentence = update.message.text  # Get user input (sentence)
    
    if validate_sentence(sentence):
        game_data["score"] += 20  # Increase score
        game_data["level"] += 1  # Increase level
        game_data["turn"] = game_data["opponent_id"]  # Switch turn to the opponent
        game_data_collection.update_one({"user_id": user_id}, {"$set": game_data})
        await update.message.reply_text(f"Correct! Your score: {game_data['score']}")
    else:
        game_data["lives"] -= 1
        if game_data["lives"] > 0:
            game_data_collection.update_one({"user_id": user_id}, {"$set": game_data})
            await update.message.reply_text(f"Wrong! You have {game_data['lives']} lives left.")
        else:
            game_data["turn"] = None  # Game over for the user
            game_data_collection.update_one({"user_id": user_id}, {"$set": game_data})
            await update.message.reply_text("Game Over! You lost all lives.")
            await send_game_over_message(update, context)
    
    await send_word(update, context)

# Validate the sentence (checks if all words are in the nltk words corpus)
def validate_sentence(sentence):
    words_in_sentence = sentence.split()
    # Check if each word in the sentence exists in the NLTK words corpus
    for word in words_in_sentence:
        if word.lower() not in words.words():
            return False
    return True

# Send game over message to both players
async def send_game_over_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    opponent = game_data_collection.find_one({"user_id": user_id})["opponent_id"]
    await context.bot.send_message(chat_id=user_id, text="Game Over! You lost.")
    await context.bot.send_message(chat_id=opponent, text="You won! The other player lost.")

# Leaderboard command
async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    leaderboard = leaderboard_collection.find().sort("score", -1).limit(10)  # Get top 10 players by score
    if leaderboard:
        top_player = leaderboard[0]
        name = top_player["name"]
        score = top_player["score"]
        img = generate_leaderboard_image(name, score)
        photo = telegram.InputFile(img, filename="leaderboard.png")
        
        await update.message.reply_photo(photo=photo, caption=f"Top Player: {name}\nScore: {score}", reply_markup=close_button())
    else:
        await update.message.reply_text("No leaderboard data available yet.")

# Generate the leaderboard image using a template image
def generate_leaderboard_image(name, score):
    template_image_path = "assets/sanki.png"
    img = Image.open(template_image_path)
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    
    d.text((10, 100), f"Top Player: {name}", font=font, fill=(255, 255, 255))
    d.text((10, 150), f"Score: {score}", font=font, fill=(255, 255, 255))

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return img_byte_arr

# Close button for leaderboard
def close_button():
    return telegram.InlineKeyboardMarkup([
        [telegram.InlineKeyboardButton("Close", callback_data='close')]
    ])

# Handle close button action
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Leaderboard closed.")

# Main entry point
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("game", game))
    application.add_handler(CommandHandler("rank", rank))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

if __name__ == '__main__':
    main()
