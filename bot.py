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
        caption=f"Welcome {message.from_user.first_name}! 🎮\n"
                "Use /leaderboard to check rankings and /play to start a game."
    )
    
    # Log the user start
    bot.send_message(
        LOGGER_GROUP_ID,
        f"User @{username} (ID: {user_id}) has started the bot."
    )

# Leaderboard Command
@bot.message_handler(commands=['leaderboard'])
def leaderboard(message):
    # Get top 5 players from the database
    users = list(users_collection.find().sort("score", -1).limit(5))
    if not users:
        bot.reply_to(message, "Leaderboard is empty!")
        return

    leaderboard_text = "🏆 Leaderboard 🏆\n\n"
    for i, user in enumerate(users, 1):
        leaderboard_text += f"{i}. @{user['username']} - {user['score']} points\n"
    
    bot.reply_to(message, leaderboard_text)

# Ping Command
@bot.message_handler(commands=['ping'])
def ping(message):
    current_uptime = time.time() - uptime
    uptime_text = time.strftime("%H:%M:%S", time.gmtime(current_uptime))
    bot.reply_to(message, f"Pong! 🏓\nUptime: {uptime_text}")

# Typing Game Play Command
@bot.message_handler(commands=['play'])
def play(message):
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"

    # Add user to the queue
    if user_id in queue:
        bot.reply_to(message, "You are already in the queue. Please wait for a match!")
        return
    
    queue.append(user_id)
    bot.reply_to(message, "You have been added to the queue. Waiting for an opponent...")

    # Check if two players are in the queue
    if len(queue) >= 2:
        player1_id = queue.pop(0)
        player2_id = queue.pop(0)
        
        player1 = users_collection.find_one({"user_id": player1_id})
        player2 = users_collection.find_one({"user_id": player2_id})

        start_game(player1, player2)

def start_game(player1, player2):
    level = 1
    time_limit = 10  # Starting with 10 seconds for each word
    active_games[player1['user_id']] = {'level': level, 'score': 0, 'time': time.time(), 'word': generate_random_word(level)}
    active_games[player2['user_id']] = {'level': level, 'score': 0, 'time': time.time(), 'word': generate_random_word(level)}

    word = active_games[player1['user_id']]['word']

    def send_word(player):
        image_file = generate_word_image(word)
        bot.send_photo(player, photo=open(image_file, 'rb'))
        start_time = time.time()

        def timeout():
            if time.time() - start_time >= time_limit:
                disqualify(player, "Time limit exceeded!")

        Timer(time_limit, timeout).start()

    send_word(player1['user_id'])
    send_word(player2['user_id'])

# Generate Random Word (A to Z)
def generate_random_word(level):
    word_length = level + 3  # Length of the word increases as the level increases
    word = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=word_length))
    return word

# Generate Word Image
def generate_word_image(word):
    # Create a simple PNG image with the word written on it
    img = Image.new('RGB', (300, 100), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    d.text((10, 40), word, fill=(0, 0, 0), font=font)
    
    file_path = f"assets/{sanki}.png"
    img.save(file_path)
    return file_path

# Handle user response and scoring
@bot.message_handler(func=lambda message: True)
def handle_response(message):
    user_id = message.from_user.id
    if user_id not in active_games:
        return
    
    game = active_games[user_id]
    current_level = game['level']
    word = game['word']  # Get the word from the current game state

    # Handle correct/incorrect response
    if message.text.strip().lower() != word.lower():
        # Incorrect word penalty
        new_score = max(0, game['score'] - 5)
        active_games[user_id]['score'] = new_score
        bot.send_message(user_id, f"Incorrect word! Your score has been reduced by 5 points. Current score: {new_score}")
    else:
        # Correct word, increase level
        active_games[user_id]['level'] += 1
        game['score'] += current_level * 10  # Score based on level

        bot.send_message(user_id, f"Correct! You are now on level {game['level']} with score: {game['score']}.")

        # Check if player completed the level and has reached level 5
        if game['level'] >= 5:
            opponent = get_opponent(user_id)
            declare_winner(user_id, opponent)

def get_opponent(user_id):
    # Logic to find the opponent (you can define based on your system)
    pass

def disqualify(player, reason):
    # Logic to disqualify a player for not completing in time or wrong word
    bot.send_message(player, f"Disqualified! {reason}. You lost the game.")
    # You can also proceed to the next level with 0 score
    bot.send_message(player, "Next time, try to type faster! You are moved to the next level with 0 score.")
    # Update scores and game database
    pass

def declare_winner(winner_id, loser_id):
    winner = users_collection.find_one({"user_id": winner_id})
    loser = users_collection.find_one({"user_id": loser_id})

    # Update scores
    users_collection.update_one({"user_id": winner_id}, {"$inc": {"score": 10 * winner['level']}})
    
    # Send winning message to the winner
    bot.send_message(winner_id, f"🎉 Congrats! You won the game! Your current score: {winner['score']}")
    
    # Send losing message to the loser
    bot.send_message(loser_id, f"😞 Sorry, you lost this game. Better luck next time!")

    # Log the game in the database
    games_collection.insert_one({
        "player1": winner_id,
        "player2": loser_id,
        "winner": winner_id,
        "timestamp": datetime.utcnow()
    })
    
    # Update the leaderboard (Top 5 players)
    update_leaderboard()

def update_leaderboard():
    # Fetch the top 5 players
    top_users = list(users_collection.find().sort("score", -1).limit(5))
    leaderboard_text = "🏆 Updated Leaderboard 🏆\n\n"
    
    # Prepare the leaderboard text
    for i, user in enumerate(top_users, 1):
        leaderboard_text += f"{i}. @{user['username']} - {user['score']} points\n"
    
    # Send the updated leaderboard to a log group or any specific group if needed
    bot.send_message(LOGGER_GROUP_ID, leaderboard_text)

# Polling 
bot.polling()
