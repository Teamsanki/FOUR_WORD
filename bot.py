from pyrogram import Client, filters
from pymongo import MongoClient
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import re
import time

# Bot Configuration
API_ID = "24740695"
API_HASH = "a95990848f2b93b8131a4a7491d97092"
BOT_TOKEN = "7908847221:AAFo2YqgQ4jYG_Glbp96sINg79zF8T6EWoo"
GROUP_ID = -1002100433415  # Replace with your group ID for notifications
OWNER_USERNAME = "TSGCODER"  # Owner username
OWNER_ID = 7877197608

# Initialize the bot
app = Client("tsgame_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# MongoDB connection
mongo_client = MongoClient("mongodb+srv://Teamsanki:Teamsanki@cluster0.jxme6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = mongo_client["game_bot"]
games_collection = db["games"]
scores_collection = db["scores"]
user_clicks_collection = db["user_clicks"]
bets_collection = db["bets"]

# Notify the group when the bot starts
@app.on_start()
async def notify_group_on_start(client):
    # Send a message to the group that the bot is online
    await client.send_message(
        chat_id=GROUP_ID,
        text="🤖 **The bot is now online and ready to serve!**\n\n"
             f"👨‍💻 **Owner:** @{OWNER_USERNAME}"
    )
    print("✅ Bot has started successfully!")  # Print message in console


# Welcome message with photo when a user starts the bot
@app.on_message(filters.command("start") & filters.private)
async def start_bot(client, message):
    user = message.from_user
    username = f"@{user.username}" if user.username else user.first_name

    # Photo URL (Replace with your desired image)
    photo_url = "https://graph.org/file/ae1108390e6dc4f7231cf-ce089431124e12e862.jpg"

    # Send the photo with the welcome message
    await client.send_photo(
        chat_id=message.chat.id,
        photo=photo_url,
        caption=(
            f"🌟 **Welcome to the Game Bot, {username}!** 🌟\n\n"
            "🎮 Explore exciting games, track your scores, and compete with others!\n\n"
            f"👨‍💻 **Bot Owner:** @{OWNER_USERNAME}\n"
            "Use `@tsgame` to view available games or type `/scores` to check your scores.\n"
            "Get ready for some fun and challenges ahead!"
        )
    )

    # Notify the group about the new user
    notification = (
        f"🆕 **New User Started the Bot** 🆕\n"
        f"👤 Name: {user.first_name}\n"
        f"🔗 Username: @{user.username if user.username else 'N/A'}\n"
        f"🆔 User ID: `{user.id}`"
    )
    await client.send_message(chat_id=GROUP_ID, text=notification)


# Add a game (Owner only)
@app.on_message(filters.command("gameadd") & filters.user(OWNER_ID))
async def add_game(client, message):
    if len(message.command) < 3:
        await message.reply("Usage: /gameadd <game_name> <game_link>")
        return
    game_name, game_link = message.command[1], message.command[2]
    
    # Check if the URL is valid
    if not re.match(r'^https?://', game_link):
        await message.reply("The game link is invalid. Please ensure the URL starts with http:// or https://.")
        return
    
    games_collection.insert_one({"name": game_name, "link": game_link})
    await message.reply(f"Game '{game_name}' added successfully!")


# Show game list when @tsgame is typed (Inline Query Handler in both private and group)
@app.on_message(filters.command("tsgame"))
async def show_game_list(client, message):
    # Fetch games from MongoDB
    games = list(games_collection.find())

    if not games:
        await message.reply("🎮 **No games available yet!**")
        return
    
    # Prepare the inline keyboard with game names
    game_buttons = []
    for game in games:
        # Ensure the URL is valid before creating the button
        if not re.match(r'^https?://', game["link"]):
            continue  # Skip invalid URLs

        game_buttons.append(InlineKeyboardButton(game["name"], url=game["link"]))
    
    if not game_buttons:
        await message.reply("🎮 **No valid game links available!**")
        return

    # Organize buttons in rows (3 buttons per row, adjust as needed)
    keyboard = InlineKeyboardMarkup(
        [game_buttons[i:i+3] for i in range(0, len(game_buttons), 3)]
    )

    # Reply with the game list to the user (both private and group)
    await message.reply(
        "🎮 **Choose a game to play**:",
        reply_markup=keyboard
    )


# Track user click and store game link clicked
@app.on_inline_query()
async def handle_game_click(client, inline_query):
    user_id = inline_query.from_user.id
    game_link = inline_query.query

    # Record the game link clicked by the user
    user_clicks_collection.insert_one({"user_id": user_id, "game_link": game_link, "timestamp": time.time()})
    await inline_query.answer(
        results=[],
        cache_time=0
    )


# Log scores automatically (Simulate auto-tracking)
@app.on_message(filters.regex(r"score: (\d+)") & filters.group)
async def log_score(client, message):
    score = int(message.matches[0].group(1))
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    game_name = "Example Game"  # Replace with dynamic game name based on context if possible

    # Check if the user clicked the link
    click_data = user_clicks_collection.find_one({"user_id": user_id})

    if click_data:
        # If game clicked, log the score
        scores_collection.insert_one({
            "user_id": user_id,
            "username": username,
            "game_name": game_name,
            "score": score
        })
        # Notify group of the score
        await app.send_message(
            chat_id=GROUP_ID,
            text=f"🏆 **Game Over**: {username} scored {score} in {game_name} by clicking the game link!"
        )
        # Clear the click data after the game
        user_clicks_collection.delete_one({"user_id": user_id})
    else:
        await message.reply("❌ **Game not started via the bot link, score not saved!**")


# Show leaderboard
@app.on_message(filters.command("rank"))
async def show_rank(client, message):
    pipeline = [
        {"$group": {"_id": "$user_id", "total_score": {"$sum": "$score"}, "username": {"$first": "$username"}}},
        {"$sort": {"total_score": -1}},
        {"$limit": 10},
    ]
    leaderboard = scores_collection.aggregate(pipeline)
    reply_text = "🏆 **Top Players** 🏆\n\n"
    for idx, user in enumerate(leaderboard, 1):
        reply_text += f"{idx}. {user['username']} - {user['total_score']} points\n"
    await message.reply(reply_text)


# Show individual scores
@app.on_message(filters.command("scores"))
async def show_scores(client, message):
    user_id = message.from_user.id
    scores = scores_collection.find({"user_id": user_id})
    reply_text = "🎮 **Your Scores** 🎮\n\n"
    for score in scores:
        reply_text += f"{score['game_name']} - {score['score']} points\n"
    await message.reply(reply_text)


# Command to delete a game (Only owner can use it)
@app.on_message(filters.command("delgm") & filters.user(OWNER_ID))
async def delete_game(client, message):
    if len(message.command) < 3:
        await message.reply("Usage: /delgm <game_name> <game_link>")
        return
    game_name, game_link = message.command[1], message.command[2]

    # Find and delete the game by name and link
    result = games_collection.delete_one({"name": game_name, "link": game_link})
    
    if result.deleted_count > 0:
        await message.reply(f"Game '{game_name}' deleted successfully!")
    else:
        await message.reply("No such game found!")


# Run the bot
app.run()
