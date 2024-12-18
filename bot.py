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

    # Inform players about their opponent
    player1_name = bot.get_chat_member(player1_id, player1_id).user.username
    player2_name = bot.get_chat_member(player2_id, player2_id).user.username
    bot.send_message(player1_id, f"Your opponent is @{player2_name}. Get ready to type the word!")
    bot.send_message(player2_id, f"Your opponent is @{player1_name}. Get ready to type the word!")

    image_file = generate_word_image(word)
    bot.send_photo(player1_id, photo=open(image_file, 'rb'), caption="Type the word fast!")
    bot.send_photo(player2_id, photo=open(image_file, 'rb'), caption="Type the word fast!")


# Generate Random Word
def generate_random_word():
    word_length = random.randint(4, 8)
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=word_length))

# Generate Word Image
# Fix the error in the `generate_word_image` function
def generate_word_image(word):
    image_size = 400
    img = Image.new('RGB', (image_size, image_size), color=(255, 255, 255))
    d = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 50)  # Increased font size
    except IOError:
        font = ImageFont.load_default()

    # Corrected line to calculate text bounding box
    bbox = d.textbbox((0, 0), word, font=font)
    text_width = bbox[2] - bbox[0]  # right - left
    text_height = bbox[3] - bbox[1]  # bottom - top
    
    # Center the text
    text_x = (image_size - text_width) // 2
    text_y = (image_size - text_height) // 2
    d.text((text_x, text_y), word, fill=(0, 0, 0), font=font)

    # Adding Watermark: "Team Sanki"
    watermark_font = ImageFont.truetype("arial.ttf", 20)
    watermark_text = "Team Sanki"
    watermark_bbox = d.textbbox((0, 0), watermark_text, font=watermark_font)
    watermark_width = watermark_bbox[2] - watermark_bbox[0]
    watermark_height = watermark_bbox[3] - watermark_bbox[1]
    watermark_x = (image_size - watermark_width) // 2
    watermark_y = image_size - watermark_height - 10
    d.text((watermark_x, watermark_y), watermark_text, fill=(150, 150, 150), font=watermark_font)

    if not os.path.exists('assets'):
        os.makedirs('assets')

    file_path = f"assets/{word}.png"
    img.save(file_path)
    return file_path


# Handle User Responses
# Handle User Responses with Timer
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

    # 15-second timer for before level 5
    if game_data['level'] < 5:
        start_time = time.time()
        # Wait for response within the time limit
        while time.time() - start_time < 15:
            if user_input == word:
                update_game_progress(user_id, matched_game)
                return
        # If time is up and no correct input
        if time.time() - start_time >= 15 and user_input != word:
            game_data['lifelines'][user_id] -= 1
            bot.send_message(user_id, f"Time's up! You have {game_data['lifelines'][user_id]} lifelines left.")
            if game_data['lifelines'][user_id] <= 0:
                declare_winner(matched_game, loser_id=user_id)

# Game Progression Logic
def update_game_progress(user_id, matched_game):
    game_data = active_games[matched_game]
    word = game_data['word']
    current_level = game_data['level']
    opponent_id = [player for player in matched_game if player != user_id][0]

    # Calculate score
    points = 50 + (current_level - 1) * 10
    game_data['scores'][user_id] += points

    # Inform players about points
    bot.send_message(user_id, f"Correct! 🎉 You earned {points} points this round.")
    bot.send_message(opponent_id, f"Your opponent was faster! You earned {points // 2} points.")

    # Move to next level
    if current_level < MAX_LEVEL:
        game_data['level'] += 1
        new_word = generate_random_word()
        game_data['word'] = new_word
        image_file = generate_word_image(new_word)

        bot.send_photo(user_id, photo=open(image_file, 'rb'), caption=f"Level {game_data['level']}: Type the word fast!")
        bot.send_photo(opponent_id, photo=open(image_file, 'rb'), caption=f"Level {game_data['level']}: Type the word fast!")
    else:
        start_post_level_5_game(user_id, opponent_id)

# Rest after Level 5
def start_post_level_5_game(player1_id, player2_id):
    bot.send_message(player1_id, "10 seconds rest... the real game will begin shortly!")
    bot.send_message(player2_id, "10 seconds rest... the real game will begin shortly!")
    
    time.sleep(10)  # 10-second rest
    
    bot.send_message(player1_id, "The game is now starting! You have 30 seconds to type the word. You have 3 lifelines.")
    bot.send_message(player2_id, "The game is now starting! You have 30 seconds to type the word. You have 3 lifelines.")

    # Set new timer for real game
    start_real_game(player1_id, player2_id)

def start_real_game(player1_id, player2_id):
    word = generate_random_word()
    game_data = active_games[(player1_id, player2_id)]
    game_data['word'] = word  # Reset word for new round
    image_file = generate_word_image(word)
    
    bot.send_photo(player1_id, photo=open(image_file, 'rb'), caption="Real game starts! Type the word fast!")
    bot.send_photo(player2_id, photo=open(image_file, 'rb'), caption="Real game starts! Type the word fast!")


# Declare Winner
def declare_winner(matched_game, loser_id):
    game_data = active_games[matched_game]
    opponent_id = [player for player in matched_game if player != loser_id][0]

    # Determine winner
    winner_id = opponent_id
    winner_score = game_data['scores'][winner_id]
    loser_score = game_data['scores'][loser_id]

    # Update leaderboard
    users_collection.update_one({"user_id": winner_id}, {"$inc": {"score": winner_score}})
    users_collection.update_one({"user_id": loser_id}, {"$inc": {"score": loser_score}})

    # Notify players
    bot.send_message(winner_id, f"🎉 Congratulations! You won the game with {winner_score} points!")
    bot.send_message(loser_id, "😢 Game over! Better luck next time.")

    # Clean up game data
    del active_games[matched_game]


bot.polling()
