import random
from datetime import datetime, timedelta
from pymongo import MongoClient
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# --- Bot Config ---
TOKEN = "7762113593:AAHEhm8iuyf4W0VfnF0MkifOeW2zCOfrMVo"  # <-- Replace this with your bot token
MONGO_URL = "mongodb+srv://TSANKI:TSANKI@cluster0.u2eg9e1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # <-- Replace this with your MongoDB connection string
WELCOME_IMAGE_URL = "https://graph.org/file/c0e17724e66a68a2de3a6-5ff173af1d3498d9e7.jpg"  # <-- Replace with your welcome image

# --- MongoDB Setup ---
client = MongoClient(MONGO_URL)
db = client["wordseekbot"]
games_col = db["games"]
scores_col = db["scores"]

# --- Word List ---
WORDS = ['lamp', 'desk', 'rain', 'gold', 'fire', 'blue', 'grin', 'mint', 'word', 'cold', 'heat', 'snow', 'wind',
         'tree', 'rock', 'sand', 'lake', 'hill', 'dark', 'mild', 'bold', 'cool', 'jump', 'grab', 'walk', 'talk',
         'hear', 'look', 'fast', 'slow', 'high', 'low', 'east', 'west', 'book', 'note', 'film', 'song', 'jazz',
         'punk', 'folk', 'rope', 'kite', 'ball', 'bark', 'meow', 'lion', 'bear', 'wolf', 'deer', 'frog', 'fish',
         'crab', 'seal', 'clam', 'gale', 'hail', 'mist', 'dawn', 'dusk', 'moon', 'star', 'mars', 'opal', 'ruby',
         'pearl', 'coal', 'iron', 'lead', 'zinc', 'salt', 'soda', 'lime', 'navy', 'army', 'tank', 'jeep', 'bike',
         'road', 'path', 'ride', 'zoom', 'gate', 'door', 'bell', 'farm', 'barn', 'shed', 'tool', 'gear', 'saw',
         'nail', 'drip', 'drop', 'leak', 'pipe', 'flow', 'wave', 'surf', 'tide', 'reef', 'ship', 'sail', 'crew',
         'deck', 'mast', 'port', 'dock', 'mile', 'yard', 'inch', 'foot', 'pace', 'step', 'clap', 'snap', 'ring',
         'tone', 'beep', 'buzz', 'whip', 'slam', 'kick', 'poke', 'stab', 'burn', 'melt', 'boil', 'bake', 'fry',
         'cook', 'brew', 'pour', 'fill', 'tilt', 'flip', 'turn', 'push', 'pull', 'drag', 'lift', 'send', 'text',
         'chat', 'post', 'like', 'vote', 'rate', 'rank', 'name', 'list', 'pick', 'sort', 'plan', 'plot', 'idea',
         'fact', 'quiz', 'game', 'luck', 'goal', 'rule', 'loss', 'gain', 'risk', 'test', 'pass', 'fail', 'hope',
         'wish', 'need', 'love', 'hate', 'fear', 'calm', 'rage', 'smile', 'grim', 'wink', 'yawn', 'moan', 'sigh',
         'gulp', 'snore', 'purr', 'chirp', 'hoot', 'roar', 'grow', 'bloom', 'leaf', 'stem', 'root', 'seed', 'soil',
         'crop', 'corn', 'bean', 'peas', 'rice', 'wheat', 'flax', 'herb', 'bush', 'vine', 'wine', 'beer', 'shot',
         'rum', 'cola', 'milk', 'cake', 'pie', 'meal', 'snack', 'dish', 'fork', 'spoon', 'bowl', 'mug', 'oven',
         'sink', 'soap', 'toys', 'play', 'spin', 'roll', 'skip', 'joke', 'jest', 'code', 'data', 'file', 'byte',
         'disk', 'link', 'node', 'ping', 'hash', 'site', 'blog', 'wiki', 'page', 'user', 'pass', 'form', 'mail',
         'news', 'edit', 'view', 'read', 'load', 'save', 'slap', 'kick', 'hell', 'grow', 'time', 'fate', 'Hate', 'chat', 'info', 'hack', 'lock', 'beep', 'deep', 'jeep', 'fills', 'repo', 'some', 'form', 'from']

# --- Format Feedback ---
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

# --- Build Summary ---
def build_summary(guesses: list[str], correct_word: str, hint: str) -> str:
    summary = ""
    for guess in guesses:
        feedback = format_feedback(guess, correct_word)
        summary += f"{feedback} `{guess}`\n"
    summary += f"\n_\"{hint}\"_\n"
    return summary

# --- /start welcome ---
async def send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    keyboard = [[InlineKeyboardButton("Start Game", callback_data="/new")]]
    markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_photo(
        chat_id=chat.id,
        photo=WELCOME_IMAGE_URL,
        caption="Welcome to *Four Word*! Guess 4-letter words with color feedback.\nUse /new to begin. Owner @ll_SANKI_II",
        parse_mode="Markdown",
        reply_markup=markup
    )

# --- /new game ---
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

# --- /stop game ---
async def stop_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    games_col.delete_one({"chat_id": chat_id})
    await update.message.reply_text("Game stopped. Use /new to start a new one.")

# --- Handle guesses ---
async def handle_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    text = update.message.text.lower()

    # Ignore all non-4-letter words (so bot won't reply to random chats)
    if not text.isalpha() or len(text) != 4:
        return  # silently ignore

    if text not in WORDS:
        await update.message.reply_text("This word is not in my dictionary.")
        return

    game = games_col.find_one({"chat_id": chat_id})
    if not game:
        return

    correct_word = game["word"]
    guesses = game.get("guesses", [])

    if text in guesses:
        return

    guesses.append(text)
    games_col.update_one({"chat_id": chat_id}, {"$set": {"guesses": guesses}})
    feedback = format_feedback(text, correct_word)
    await update.message.reply_text(f"{feedback} {text}", parse_mode="Markdown")

    if text == correct_word:
        now = datetime.utcnow()

        scores_col.update_one(
            {"chat_id": chat_id, "user_id": user.id},
            {"$set": {"name": user.first_name, "updated": now}, "$inc": {"score": 12}},
            upsert=True
        )
        scores_col.update_one(
            {"chat_id": "global", "user_id": user.id},
            {"$set": {"name": user.first_name, "updated": now}, "$inc": {"score": 12}},
            upsert=True
        )

        summary = build_summary(guesses, correct_word, game.get("hint", ""))
        await update.message.reply_text(f"👻 *{user.first_name} guessed it right!*\n\n{summary}", parse_mode="Markdown")
        await context.bot.send_message(chat_id=chat_id, text=f"🎉 Congratulations *{user.first_name}*! 👻", parse_mode="Markdown")
        games_col.delete_one({"chat_id": chat_id})

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Find latest game message to reply to
    last_game = games_col.find_one({"chat_id": chat_id}, sort=[("started_at", -1)])
    reply_to = last_game.get("message_id") if last_game else None

    # Get top 10 scores for this chat (Overall)
    results = list(scores_col.find({"chat_id": chat_id}).sort("score", -1).limit(10))
    title = "🏆 Overall Leaderboard"

    if not results:
        msg = "No scores found."
    else:
        msg = f"__{title}__\n"
        for i, row in enumerate(results, 1):
            msg += f"> {i}. *{row['name']}* — {row['score']} pts\n"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Today", callback_data=f"lb_today_{chat_id}"),
            InlineKeyboardButton("Overall", callback_data=f"lb_overall_{chat_id}"),
            InlineKeyboardButton("Global", callback_data="lb_global")
        ]
    ])

    await context.bot.send_message(
        chat_id=chat_id,
        text=msg,
        reply_to_message_id=reply_to,  # This ensures quote style
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# --- Main ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", send_welcome))
    app.add_handler(CommandHandler("new", new_game))
    app.add_handler(CommandHandler("stop", stop_game))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CallbackQueryHandler(leaderboard_callback, pattern=r"^lb_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_guess))

    print("Bot is running...")
    app.run_polling()
