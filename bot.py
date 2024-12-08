import random
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.ext import ContextTypes
from pymongo import MongoClient
import asyncio
import time

# Set up logging
import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection string (replace with your actual MongoDB URI)
MONGO_URL = "mongodb+srv://Teamsanki:Teamsanki@cluster0.jxme6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URL)
db = client["new_game_database"]  # New database name for reset
leaderboard_collection = db["leaderboard"]  # Collection for leaderboard data
game_data_collection = db["game_data"]  # Collection for ongoing game data

# Bot Token (Replace with your bot's token)
TOKEN = "7908847221:AAFo2YqgQ4jYG_Glbp96sINg79zF8T6EWoo"

# Set of letters with corresponding words for the random word generation
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

# Function to generate a random word for a player based on a random letter (A-Z)
def generate_random_word():
    random_letter = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    word_list = word_list_by_letter.get(random_letter, ["default_word"])  # Default if no words found for that letter
    return random.choice(word_list)

# Function to start the game
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    await update.message.reply_text(f"Hello {user.first_name}, welcome to the Word Game! Use /game to start playing.")

# Function to start a game between two users
async def game(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    waiting_queue = []

    # Check if the user is already in a game
    existing_game = game_data_collection.find_one({"user_id": user.id})
    if existing_game and existing_game.get("turn"):
        await update.message.reply_text("You are already in a game!")
        return

    # Add user to the waiting queue
    waiting_queue.append(user)
    if len(waiting_queue) > 1:
        opponent = waiting_queue.pop(0)  # Get the opponent
        # Create a new game between user and opponent
        game_data = {
            "user_id": user.id,
            "opponent_id": opponent.id,
            "level": 1,
            "lives": 3,
            "score": 0,
            "turn": user.id  # Set the first turn to the user
        }

        # Insert game data into the database
        game_data_collection.insert_one(game_data)

        # Notify both players that the game will start in 10 seconds
        await update.message.reply_text(f"Game started with {opponent.first_name}. The game will start in 10 seconds...")
        await context.bot.send_message(chat_id=opponent.id, text=f"Game started with {user.first_name}. The game will start in 10 seconds...")

        # Wait 10 seconds before starting the game
        await asyncio.sleep(10)

        # Start the game by sending the first word
        await send_word(update, context)
        await context.bot.send_message(chat_id=opponent.id, text=f"Level 1: Write a sentence using the word.")

    else:
        await update.message.reply_text("No opponent available. Please wait for someone to join.")

# Function to send the word for the current level
async def send_word(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    game_data = game_data_collection.find_one({"user_id": update.message.from_user.id})
    level = game_data["level"]

    # Generate a random word (A-Z) for the current level
    word = generate_random_word()  # Get a random word for the current level

    # Send the word and level to the player
    await context.bot.send_message(chat_id=update.message.from_user.id, text=f"Level {level}: Write a sentence using the word: {word}")
    # Send the time limit for the current level
    time_limit = 20  # Set a time limit (in seconds) for the current level
    await context.bot.send_message(chat_id=update.message.from_user.id, text=f"You have {time_limit} seconds to complete this level.")

# Function to handle the user input for sentences
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    game_data = game_data_collection.find_one({"user_id": user_id})
    
    if game_data and user_id == game_data["turn"]:
        await process_turn(update, context)
    else:
        await update.message.reply_text("It's not your turn yet.")

# Function to process each turn
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
            await update.message.reply_text("Game Over! You lost all your lives.")
            await context.bot.send_message(chat_id=game_data["opponent_id"], text="Game Over! Your opponent lost all their lives.")
            game_data_collection.delete_one({"user_id": user_id})

# Function to validate if the sentence entered by the user is valid
def validate_sentence(sentence: str) -> bool:
    # You can implement a better validation here, such as using a dictionary or NLP model
    return sentence != ""

# Main function to start the bot
def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("game", game))

    # Message Handler
    application.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Start polling for the bot
    application.run_polling()

if __name__ == '__main__':
    main()
