import telebot
import time
import random
from threading import Timer
from pymongo import MongoClient
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import os

# Bot Token and MongoDB URL
BOT_TOKEN = "7396395072:AAG-B-zKxB8LFoKGwf0sbzwropNq-OlxFKk"
MONGO_URL = "mongodb+srv://Teamsanki:Teamsanki@cluster0.jxme6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
LOGGER_GROUP_ID = "-1002100433415"

bot = telebot.TeleBot(BOT_TOKEN)

# MongoDB Setup
client = MongoClient(MONGO_URL)
db = client['game_bot']
users_collection = db['users']
games_collection = db['games']

# Game Variables
queue = []  # Queue of players waiting for a match
active_games = {}  # Tracking active games
uptime = time.time()

# Constants
MAX_LEVEL = 5
BONUS_LEVEL_INTERVAL = 4
BONUS_POINTS = 500

# Start Command
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    
    # Add user to the database if not exists
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({"user_id": user_id, "username": username, "score": 0})
    
    # Welcome message
    bot.send_photo(
        message.chat.id,
        photo="https://graph.org/file/ae1108390e6dc4f7231cf-ce089431124e12e862.jpg",  # Replace with your photo URL
        caption=(
            f"🎮 **Welcome to the Game Bot!** 🎮\n\n"
            f"Hello {message.from_user.first_name}! Ready to have some fun?\n\n"
            "📝 **Commands**:\n"
            "/leaderboard - Check rankings\n"
            "/play - Start a typing challenge\n"
            "/ping - Check bot status\n\n"
            "🤖 **Owner**: @TSGCODER"
        ),
        parse_mode="Markdown"
    )
    
    bot.send_message(
        LOGGER_GROUP_ID,
        f"User @{username} (ID: {user_id}) has started the bot."
    )

# Leaderboard Command
@bot.message_handler(commands=['leaderboard'])
def leaderboard(message):
    users = list(users_collection.find().sort("score", -1).limit(5))
    if not users:
        bot.reply_to(message, "Leaderboard is empty!")
        return

    leaderboard_text = "🏆 **Leaderboard** 🏆\n\n"
    for i, user in enumerate(users, 1):
        leaderboard_text += f"{i}. @{user['username']} - {user['score']} points\n"
    
    bot.reply_to(message, leaderboard_text)

# Ping Command
@bot.message_handler(commands=['ping'])
def ping(message):
    current_uptime = time.time() - uptime
    uptime_text = time.strftime("%H:%M:%S", time.gmtime(current_uptime))
    bot.reply_to(message, f"Pong! 🏓\nUptime: {uptime_text}")

# Play Command
@bot.message_handler(commands=['play'])
def play(message):
    user_id = message.from_user.id

    if user_id in queue:
        bot.reply_to(message, "You are already in the queue. Please wait for a match!")
        return
    
    queue.append(user_id)
    bot.reply_to(message, "You have been added to the queue. Waiting for an opponent...")

    if len(queue) >= 2:
        player1_id = queue.pop(0)
        player2_id = queue.pop(0)
        start_game(player1_id, player2_id)

# Start Game
def start_game(player1_id, player2_id):
    word = generate_random_word()
    game_data = {
        'level': 1,
        'word': word,
        'scores': {player1_id: 0, player2_id: 0},
        'lifelines': {player1_id: 3, player2_id: 3},
        'start_time': time.time(),
    }
    active_games[(player1_id, player2_id)] = game_data

    image_file = generate_word_image(word)
    bot.send_photo(player1_id, photo=open(image_file, 'rb'), caption="Type the word fast!")
    bot.send_photo(player2_id, photo=open(image_file, 'rb'), caption="Type the word fast!")

# Generate Random Word
def generate_random_word():
    word_length = random.randint(4, 8)
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=word_length))

# Generate Word Image
def generate_word_image(word):
    image_size = 400
    img = Image.new('RGB', (image_size, image_size), color=(255, 255, 255))
    d = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except IOError:
        font = ImageFont.load_default()

    text_width, text_height = d.textsize(word, font=font)
    text_x = (image_size - text_width) // 2
    text_y = (image_size - text_height) // 2
    d.text((text_x, text_y), word, fill=(0, 0, 0), font=font)

    if not os.path.exists('assets'):
        os.makedirs('assets')

    file_path = f"assets/{word}.png"
    img.save(file_path)
    return file_path

# Handle User Responses
@bot.message_handler(func=lambda message: True)
def handle_response(message):
    user_id = message.from_user.id
    matched_game = None

    # Check which game the user is part of
    for game in active_games.keys():
        if user_id in game:
            matched_game = game
            break

    if not matched_game:
        return
    
    game_data = active_games[matched_game]
    word = game_data['word'].strip().lower()
    user_input = message.text.strip().lower()

    if user_input == word:
        update_game_progress(user_id, matched_game)
    else:
        game_data['lifelines'][user_id] -= 1
        if game_data['lifelines'][user_id] <= 0:
            declare_winner(matched_game, opponent_id=user_id)
        else:
            bot.send_message(user_id, f"Incorrect! Remaining lifelines: {game_data['lifelines'][user_id]}")

# Game Progression Logic
def update_game_progress(user_id, matched_game):
    pass  # Add scoring, leveling, and progression logic here

# Declare Winner
def declare_winner(matched_game, opponent_id):
    pass  # Add logic to declare winner here

bot.polling()
