from pyrogram import Client, filters
from pymongo import MongoClient
from pyrogram.types import InputMediaPhoto

# Bot Configuration
API_ID = "24740695"
API_HASH = "a95990848f2b93b8131a4a7491d97092"
BOT_TOKEN = "7908847221:AAFo2YqgQ4jYG_Glbp96sINg79zF8T6EWoo"
GROUP_ID = -1002148651992  # Replace with your group ID for notifications
OWNER_USERNAME = "TSGCODER"  # Owner username
OWNER_ID = 7877197608

# Initialize the bot
app = Client("game_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# MongoDB connection
mongo_client = MongoClient("mongodb+srv://Teamsanki:Teamsanki@cluster0.jxme6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = mongo_client["game_bot"]
games_collection = db["games"]
scores_collection = db["scores"]


# Notify the group when the bot starts
async def notify_group_on_start():
    # Send a message to the group that the bot is online
    await app.send_message(
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
            "Use `@sanki` to view available games or type `/scores` to check your scores.\n"
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
    games_collection.insert_one({"name": game_name, "link": game_link})
    await message.reply(f"Game '{game_name}' added successfully!")


# Display game list (@sanki)
@app.on_inline_query()
async def show_game_list(client, query):
    games = games_collection.find()
    results = [
        {
            "type": "article",
            "title": game["name"],
            "input_message_content": {"message_text": f"[Play {game['name']}]({game['link']})"},
            "description": f"Click to play {game['name']}",
        }
        for game in games
    ]
    await query.answer(results, cache_time=0)


# Log scores automatically (Simulate auto-tracking)
@app.on_message(filters.regex(r"score: (\d+)") & filters.group)
async def log_score(client, message):
    score = int(message.matches[0].group(1))
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    game_name = "Example Game"  # Replace with dynamic game name based on context if possible

    # Save to MongoDB
    scores_collection.insert_one({
        "user_id": user_id,
        "username": username,
        "game_name": game_name,
        "score": score
    })
    await message.reply(f"Score of {score} logged for {username} in {game_name}!")


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
        reply_text += f"{score['game_name']}: {score['score']} points\n"
    await message.reply(reply_text)


if __name__ == "__main__":
    print("🔄 Starting the bot...")
    app.start()
    app.loop.run_until_complete(notify_group_on_start())
    app.idle()
