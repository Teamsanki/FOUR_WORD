import random
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.ext import ContextTypes
from pymongo import MongoClient
import asyncio
from PIL import Image, ImageDraw, ImageFont
import io
import nltk
from nltk.corpus import words

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

# Initialize the bot and set up logging
import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize waiting queue for game
waiting_queue = []  # List to store users waiting for opponents

# Word list for each letter A-Z
word_list_by_letter = {
    'A': ["apple", "ant", "arrow", "axe", "art", "angel"],
    'B': ["banana", "ball", "bat", "boat", "bottle", "bird"],
    'C': ["cat", "car", "circle", "cloud", "climb", "cup"],
    'D': ["dog", "drum", "duck", "door", "dance", "dove"],
    'E': ["elephant", "ear", "egg", "eagle", "engine"],
    'F': ["frog", "fish", "flag", "flower", "fan"],
    'G': ["grape", "goose", "garden", "glove", "guitar"],
    'H': ["house", "hat", "hill", "hand", "helicopter"],
    'I': ["ice", "island", "insect", "incredible"],
    'J': ["jack", "jungle", "jacket", "juice"],
    'K': ["kite", "kangaroo", "key", "king", "keyboard"],
    'L': ["lion", "lake", "lamp", "lollipop", "leaf"],
    'M': ["monkey", "mountain", "moon", "mirror", "music"],
    'N': ["necklace", "nose", "night", "nail", "notebook"],
    'O': ["orange", "octopus", "ocean", "onion", "owl"],
    'P': ["piano", "pencil", "parrot", "plane", "paper"],
    'Q': ["queen", "question", "quilt", "quicksand"],
    'R': ["rabbit", "rose", "rainbow", "rocket", "radio"],
    'S': ["snake", "sun", "ship", "star", "shovel"],
    'T': ["tree", "tiger", "train", "table", "telescope"],
    'U': ["umbrella", "unicorn", "under", "up", "universe"],
    'V': ["vampire", "vulture", "vase", "vacuum", "violin"],
    'W': ["window", "water", "wolf", "wall", "whale"],
    'X': ["xylophone", "xenon", "xmas", "x-ray"],
    'Y': ["yellow", "yoga", "yacht", "yak", "yarn"],
    'Z': ["zebra", "zoo", "zero", "zip", "zone"]
}

# Reset the game data and leaderboard
async def reset_game_data() -> None:
    game_data_collection.drop()  # Drop all game data
    leaderboard_collection.drop()  # Drop leaderboard data

# Function to generate a random word based on a random letter (A-Z)
def generate_random_word():
    random_letter = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    word_list = word_list_by_letter.get(random_letter, ["default_word"])
    return random.choice(word_list)

# Start the bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    await update.message.reply_text(f"Hello {user.first_name}, welcome to the Word Game! Use /game to start playing.")

# Game command: User initiates the game
async def game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user

    # Reset the game data and leaderboard
    await reset_game_data()

    # Check if the user is already in a game
    existing_game = game_data_collection.find_one({"user_id": user.id})
    if existing_game and existing_game.get("turn"):
        await update.message.reply_text("You are already in a game!")
        return

    # Add user to waiting queue
    waiting_queue.append(user)

    if len(waiting_queue) > 1:
        # Find the opponent (the second player in the queue)
        opponent = waiting_queue.pop(0)  # The first player in the queue is matched with the second
        # Start the game between the two users
        game_data = {
            "user_id": user.id,
            "opponent_id": opponent.id,
            "level": 1,
            "lives": 3,
            "score": 0,
            "turn": user.id,
            "opponent_name": opponent.first_name,
            "start_time": asyncio.get_event_loop().time()
        }

        # Insert game data into the database
        game_data_collection.insert_one(game_data)

        # Notify both players that the game will start in 10 seconds
        await update.message.reply_text(f"Game started with {opponent.first_name}. The game will start in 10 seconds...")
        await context.bot.send_message(chat_id=opponent.id, text=f"Game started with {user.first_name}. The game will start in 10 seconds...")

        # Wait 10 seconds before starting the game
        await asyncio.sleep(10)
        
        # Send the first word to both players
        await send_word(update, context)
        await context.bot.send_message(chat_id=opponent.id, text=f"Level 1: Write a sentence using the word.")
    else:
        await update.message.reply_text("No opponent available. Please wait for someone to join.")

# Send word for current level
async def send_word(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    game_data = game_data_collection.find_one({"user_id": update.message.from_user.id})
    level = game_data["level"]

    # Generate a random word (A-Z) for each level
    word = generate_random_word()  # Get a random word for the current level

    # Get the time for the current level
    time_for_level = 20  # Default time for each level (20 seconds)
    
    await context.bot.send_message(chat_id=update.message.from_user.id, text=f"Level {level}: You have {time_for_level} seconds to write a sentence using the word: {word}")

    # Timer countdown
    await countdown_timer(update, context, time_for_level)

# Timer countdown for the level
async def countdown_timer(update: Update, context: ContextTypes.DEFAULT_TYPE, seconds: int) -> None:
    while seconds > 0:
        await asyncio.sleep(1)
        seconds -= 1
        await context.bot.send_message(chat_id=update.message.from_user.id, text=f"{seconds} seconds remaining.")
        await context.bot.send_message(chat_id=game_data_collection.find_one({"user_id": update.message.from_user.id})["opponent_id"], text=f"{seconds} seconds remaining.")
    await check_answer(update, context)

# Validate the sentence (checks if all words are in the nltk words corpus)
def validate_sentence(sentence):
    words_in_sentence = sentence.split()
    # Check if each word in the sentence exists in the NLTK words corpus
    for word in words_in_sentence:
        if word.lower() not in words.words():
            return False
    return True

# Process user response
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    game_data = game_data_collection.find_one({"user_id": user_id})
    
    if game_data:
        if game_data["turn"] == user_id:
            if validate_sentence(update.message.text):
                # Update game status
                game_data["score"] += 1
                game_data["level"] += 1
                game_data["turn"] = game_data["opponent_id"]
                game_data_collection.update_one({"user_id": user_id}, {"$set": game_data})
                await update.message.reply_text(f"Correct! You are now at level {game_data['level']}.")
                await send_word(update, context)
            else:
                # Decrease lives if answer is incorrect
                game_data["lives"] -= 1
                game_data_collection.update_one({"user_id": user_id}, {"$set": game_data})
                if game_data["lives"] > 0:
                    await update.message.reply_text(f"Incorrect! You have {game_data['lives']} lives left.")
                    await send_word(update, context)
                else:
                    await update.message.reply_text("Game Over! You ran out of lives.")
                    # Game over, delete the game data from the database
                    game_data_collection.delete_one({"user_id": user_id})

# Main function to start the bot
async def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("game", game))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
