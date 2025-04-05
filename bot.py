import random
from datetime import datetime, timedelta
from pymongo import MongoClient
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    ContextTypes,
    filters
)

# ---------------- CONFIGURATION ----------------
TOKEN = "7762113593:AAHEhm8iuyf4W0VfnF0MkifOeW2zCOfrMVo"  # Replace with your bot token
OWNER_USERNAME = "ll_SANKI_II"  # Replace with your @username
SUPPORT_CHANNEL = "https://t.me/SANKINETWORK"
WELCOME_IMAGE_URL = "https://graph.org/file/2e37a57d083183ea24761-9cc38246fecc1af393.jpg"  # Hosted image link

MONGO_URL = "mongodb+srv://TSANKI:TSANKI@cluster0.u2eg9e1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# ---------------- DATABASE ----------------
client = MongoClient(MONGO_URL)
db = client["wordseekbot"]
games_col = db["games"]
scores_col = db["scores"]

# ---------------- WORD LIST ----------------
WORDS = ['lamp', 'desk', 'rain', 'gold', 'fire', 'blue', 'grin', 'mint']

# ---------------- HELPERS ----------------
def format_feedback(guess: str, correct_word: str) -> str:
    feedback = []
    for i in range(4):
        if guess[i] == correct_word[i]:
            feedback.append("🟩")
        elif guess[i] in correct_word:
            feedback.append("🟨")
        else:
            feedback.append("🟥")
    return ''.join(feedback)

def build_summary(guesses: list[str], correct_word: str, hint: str) -> str:
    summary = ""
    for guess in guesses:
        feedback = format_feedback(guess, correct_word)
        summary += f"{feedback} `{guess}`\n"
    summary += f"\n_\"{hint}\"_\n"
    return summary

# ---------------- WELCOME MESSAGE ----------------
async def send_welcome(chat, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("▶️ Start Game", switch_inline_query_current_chat="/new")],
        [InlineKeyboardButton("🏆 Leaderboard", switch_inline_query_current_chat="/leaderboard")],
        [InlineKeyboardButton("Support", url=SUPPORT_CHANNEL)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_photo(
        chat_id=chat.id,
        photo=WELCOME_IMAGE_URL,
        caption=(
            f"Welcome to *WordSeekBot*!\n\n"
            f"Guess the 4-letter word. Use /new to start playing!\n\n"
            f"Made by [@{OWNER_USERNAME}]"
        ),
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_welcome(update.effective_chat, context)

async def new_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.chat_member.new_chat_members:
        if member.id == context.bot.id:
            await send_welcome(update.chat_member.chat, context)

# ---------------- GAME COMMANDS ----------------
async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    word = random.choice(WORDS)
    hint = f"Starts with '{word[0]}'"
    games_col.update_one(
        {"chat_id": chat_id},
        {"$set": {
            "word": word,
            "hint": hint,
            "guesses": [],
            "start_time": datetime.utcnow()
        }},
        upsert=True
    )
    await update.message.reply_text("New game started! Guess the 4-letter word.")

async def handle_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text.lower()
    if len(text) != 4 or not text.isalpha():
        await update.message.reply_text("This word is invalid.")
        return

    game = games_col.find_one({"chat_id": chat_id})
    if not game:
        return

    correct_word = game["word"]
    guesses = game.get("guesses", [])

    if text in guesses:
        await update.message.reply_text("You’ve already guessed this word.")
        return

    guesses.append(text)
    games_col.update_one(
        {"chat_id": chat_id},
        {"$set": {"guesses": guesses}}
    )

    feedback = format_feedback(text, correct_word)
    await update.message.reply_text(f"{feedback} `{text}`", parse_mode="Markdown")

    if text == correct_word:
        user = update.effective_user
        now = datetime.utcnow()

        scores_col.update_one(
            {"chat_id": chat_id, "user_id": user.id},
            {"$inc": {"score": 1}, "$set": {"name": user.first_name, "updated": now}},
            upsert=True
        )
        scores_col.update_one(
            {"chat_id": "global", "user_id": user.id},
            {"$inc": {"score": 1}, "$set": {"name": user.first_name, "updated": now}},
            upsert=True
        )
        scores_col.insert_one({
            "chat_id": chat_id,
            "user_id": user.id,
            "name": user.first_name,
            "score": 1,
            "updated": now,
            "type": "today"
        })

        summary = build_summary(guesses, correct_word, game.get("hint", ""))
        await update.message.reply_text(f"👻 {user.first_name} guessed it right!\n\n{summary}", parse_mode="Markdown")
        games_col.delete_one({"chat_id": chat_id})

# ---------------- LEADERBOARD ----------------
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    keyboard = [
        [
            InlineKeyboardButton("📅 Today", callback_data=f"lb_today_{chat_id}"),
            InlineKeyboardButton("🏆 Overall", callback_data=f"lb_overall_{chat_id}"),
            InlineKeyboardButton("🌍 Global", callback_data="lb_global")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose a leaderboard:", reply_markup=reply_markup)

async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("lb_today_"):
        chat_id = int(data.split("_")[2])
        since = datetime.utcnow() - timedelta(days=1)
        pipeline = [
            {"$match": {"chat_id": chat_id, "updated": {"$gte": since}}},
            {"$group": {"_id": "$user_id", "score": {"$sum": "$score"}, "name": {"$first": "$name"}}},
            {"$sort": {"score": -1}},
            {"$limit": 10}
        ]
        results = list(scores_col.aggregate(pipeline))
        title = "📅 Today's Leaderboard"

    elif data.startswith("lb_overall_"):
        chat_id = int(data.split("_")[2])
        results = list(scores_col.find({"chat_id": chat_id}).sort("score", -1).limit(10))
        title = "🏆 Overall Leaderboard"

    elif data == "lb_global":
        results = list(scores_col.find({"chat_id": "global"}).sort("score", -1).limit(10))
        title = "🌍 Global Leaderboard"

    else:
        return

    if not results:
        await query.edit_message_text("No scores found.")
        return

    msg = f"**{title}**\n"
    for idx, row in enumerate(results, 1):
        name = row.get("name", "Unknown")
        score = row["score"]
        msg += f"{idx}. {name} — {score} pts\n"

    await query.edit_message_text(msg, parse_mode="Markdown")

# ---------------- MAIN ----------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(ChatMemberHandler(new_chat_member, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CommandHandler("new", new_game))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CallbackQueryHandler(leaderboard_callback, pattern=r"^lb_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_guess))

    print("Bot is running...")
    app.run_polling()
