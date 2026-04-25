# All imports come FIRST
import os
import random
import json
import asyncio
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatMemberUpdated
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ChatMemberHandler,
    filters
)

# Load .env variables
load_dotenv()

# --- Bot Config ---
TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")
WELCOME_IMAGE_URL = os.getenv("WELCOME_IMAGE_URL")
LOGGER_GROUP_ID = int(os.getenv("LOGGER_GROUP_ID"))

# --- MongoDB Setup ---
client = MongoClient(MONGO_URL)
db = client["wordseekbot"]
games_col = db["games"]
scores_col = db["scores"]
daily_col = db["daily_word"]
stats_col = db["user_stats"]
p2p_col = db["p2p_challenges"]
group_games_col = db["group_games"]
streak_freezes_col = db["streak_freezes"]
p2p_queue_col = db["p2p_queue"]  # queue for random matchmaking

# ---------- WORD LOADER FROM LOCAL JSON FILES ----------
def load_words_from_json(length: int):
    filename = f"all-{['four','five','six'][length-4]}.json"
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            words = json.load(f)
            words = [w.lower() for w in words if isinstance(w, str) and len(w) == length]
            print(f"Loaded {len(words)} {length}-letter words from {filename}")
            return words
    else:
        raise FileNotFoundError(f"{filename} not found. Please ensure the file exists.")

WORDS_4 = load_words_from_json(4)
WORDS_5 = load_words_from_json(5)
WORDS_6 = load_words_from_json(6)
WORD_LISTS = {4: WORDS_4, 5: WORDS_5, 6: WORDS_6}
print(f"Loaded 4: {len(WORDS_4)}, 5: {len(WORDS_5)}, 6: {len(WORDS_6)} words.")

# ---------- HELPER FUNCTIONS ----------
def format_feedback(guess: str, correct: str) -> str:
    fb = []
    for i in range(len(correct)):
        if guess[i] == correct[i]:
            fb.append("🟩")
        elif guess[i] in correct:
            fb.append("🟨")
        else:
            fb.append("🟥")
    return ''.join(fb)

def build_summary(guesses, correct, hint):
    s = ""
    for g in guesses:
        s += f"{format_feedback(g, correct)} `{g}`\n"
    s += f"\n_\"{hint}\"_"
    return s

def get_random_clue(word, guessed_letters=None):
    if guessed_letters is None:
        guessed_letters = set()
    clues = []
    vowels = set('aeiou')
    vc = sum(1 for ch in word if ch in vowels)
    if vc == 1:
        clues.append("🔊 Word has exactly one vowel.")
    elif vc == 2:
        clues.append("🔊 Word has two vowels.")
    elif vc == 3:
        clues.append("🔊 Word has three vowels.")
    if word[0] not in guessed_letters:
        clues.append(f"🔤 Starts with **{word[0].upper()}**.")
    if word[-1] not in guessed_letters:
        clues.append(f"🔚 Ends with **{word[-1].upper()}**.")
    for ch in 'eastnro':
        if ch in word and ch not in guessed_letters:
            clues.append(f"📌 Contains letter **{ch.upper()}**.")
            break
    if not clues:
        clues.append("💡 Common English word.")
    return random.choice(clues)

async def update_user_stats(user_id, name, won, daily=False, word_len=4):
    stats = stats_col.find_one({"user_id": user_id})
    if not stats:
        stats = {
            "user_id": user_id, "name": name,
            "total_games": 0, "total_wins": 0,
            "current_streak": 0, "best_streak": 0,
            "total_coins": 0, "last_daily": None,
            "wins_4": 0, "wins_5": 0, "wins_6": 0
        }
    stats["total_games"] += 1
    if won:
        stats["total_wins"] += 1
        stats[f"wins_{word_len}"] = stats.get(f"wins_{word_len}", 0) + 1
        coin_reward = 20 if daily else 10
        stats["total_coins"] += coin_reward
        if daily:
            today = datetime.utcnow().date()
            last = stats.get("last_daily")
            freeze = streak_freezes_col.find_one({"user_id": user_id, "used": False})
            if last == today - timedelta(days=1):
                stats["current_streak"] += 1
            elif last is None or last < today - timedelta(days=1):
                if freeze:
                    streak_freezes_col.update_one({"_id": freeze["_id"]}, {"$set": {"used": True}})
                    stats["current_streak"] = stats.get("current_streak", 0) + 1
                else:
                    stats["current_streak"] = 1
            else:
                stats["current_streak"] = 1
            stats["last_daily"] = today
            if stats["current_streak"] > stats["best_streak"]:
                stats["best_streak"] = stats["current_streak"]
        stats["name"] = name
    stats_col.update_one({"user_id": user_id}, {"$set": stats}, upsert=True)
    return stats

# ---------- STREAK FREEZE ----------
async def streakfreeze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    stats = stats_col.find_one({"user_id": user.id})
    if not stats or stats.get("total_coins", 0) < 50:
        await update.message.reply_text("❌ You need 50 coins to buy a streak freeze.")
        return
    existing = streak_freezes_col.find_one({"user_id": user.id, "used": False})
    if existing:
        await update.message.reply_text("You already have an unused streak freeze. It will be used automatically when needed.")
        return
    stats_col.update_one({"user_id": user.id}, {"$inc": {"total_coins": -50}})
    streak_freezes_col.insert_one({"user_id": user.id, "used": False, "purchased_at": datetime.utcnow()})
    await update.message.reply_text("✅ Streak freeze purchased! Protects your daily streak if you miss a day.")

# ---------- LEADERBOARD ----------
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    keyboard = [
        [InlineKeyboardButton("📅 Today", callback_data=f"lb_today_{chat_id}"),
         InlineKeyboardButton("🏆 Overall", callback_data=f"lb_overall_{chat_id}"),
         InlineKeyboardButton("🌍 Global", callback_data="lb_global")]
    ]
    await update.message.reply_text("Choose leaderboard:", reply_markup=InlineKeyboardMarkup(keyboard))

async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("lb_today_"):
        chat_id = int(data.split("_")[2])
        since = datetime.utcnow() - timedelta(days=1)
        pipeline = [{"$match": {"chat_id": chat_id, "updated": {"$gte": since}}},
                    {"$group": {"_id": "$user_id", "score": {"$max": "$score"}, "name": {"$first": "$name"}}},
                    {"$sort": {"score": -1}}, {"$limit": 10}]
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
    msg = f"**{title}**\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for idx, row in enumerate(results, 1):
        medal = medals[idx-1] if idx<=3 else f"{idx}."
        name = row.get("name", "Player")
        uid = row["_id"]
        score = row["score"]
        msg += f"➤ `{medal}` [{name}](tg://user?id={uid}) — *{score}* pts\n"
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data=f"lb_back_{query.message.chat.id}")]]
    await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# ---------- BOT COMMANDS (CLASSIC) ----------
async def send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("➕ Add me to group", url="https://t.me/TSFOURWORDBOT?startgroup=true")],
        [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/ll_SANKI_II"),
         InlineKeyboardButton("📢 Support", url="https://t.me/TEAMSANKI")],
        [InlineKeyboardButton("👻 Four Word Group", url="https://t.me/Fourwordgusser")]
    ]
    caption = (
        "✨ *Welcome to Four Word Game* ✨\n\n"
        "🔤 Guess 4, 5, or 6 letter words!\n"
        "🎯 Color feedback: 🟩🟨🟥\n"
        "🏆 Leaderboards (Today / Overall / Global)\n"
        "🎁 Coins, hints, daily challenge, streaks\n"
        "🛡️ /streakfreeze - protect your daily streak\n\n"
        "💥 /new 4|5|6 - start a game\n"
        "🌟 /daily - daily challenge\n"
        "📊 /stats - your progress\n"
        "🃏 /hint - reveal a letter (3 per game, 10s cooldown)\n"
        "🤝 /challenge - random 1v1 matchmaking (DM)\n"
        "👥 /challenge 4|5|6 - create group multiplayer game\n"
        "❌ /cancel - leave matchmaking queue\n"
        "❓ /help - full guide"
    )
    await context.bot.send_photo(chat_id=chat.id, photo=WELCOME_IMAGE_URL, caption=caption, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    if user:
        await context.bot.send_message(chat_id=LOGGER_GROUP_ID, text=f"✨ <b>Started bot</b>\nUser: {user.mention_html()}", parse_mode="HTML")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 *Four Word Game - Help*\n\n"
        "*How to play:*\n"
        "• Type any 4/5/6 letter word (depending on game mode)\n"
        "• Get feedback: 🟩=correct pos, 🟨=in word wrong pos, 🟥=not in word\n"
        "• Win within max guesses (20 classic, 6 daily)\n\n"
        "*Commands:*\n"
        "/new `4|5|6` – start new game (default 4)\n"
        "/daily – daily challenge (fixed word, bonus)\n"
        "/stop – stop current game\n"
        "/hint – reveal a letter (cost 5 coins, 3 per game, 10s cooldown)\n"
        "/stats – your stats (games, wins, streak, coins)\n"
        "/profile – your detailed profile with photo\n"
        "/leaderboard – top players (Today/Overall/Global)\n"
        "/streakfreeze – buy streak freeze (50 coins)\n"
        "/challenge – join random 1v1 PvP queue (DM)\n"
        "/challenge `4|5|6` – create group multiplayer game (group only)\n"
        "/cancel – leave the PvP queue\n"
        "/join `<gameid>` – join a group game\n"
        "/help – this message\n\n"
        "*Coins:* earned by winning. Use /hint.\n"
        "*Streak:* daily challenge consecutive wins.\n"
        "*PvP:* Random opponent, first to guess wins. 10 seconds per turn."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    length = 4
    if args and args[0] in ['4','5','6']:
        length = int(args[0])
    existing = games_col.find_one({"chat_id": chat_id})
    if existing:
        await update.message.reply_text("❌ A game is already running. Use /stop first.")
        return
    word = random.choice(WORD_LISTS[length])
    hint = f"Starts with '{word[0]}'"
    games_col.insert_one({
        "chat_id": chat_id,
        "word": word,
        "hint": hint,
        "guesses": [],
        "length": length,
        "start_time": datetime.utcnow(),
        "max_guesses": 20,
        "mode": "classic",
        "hints_used": 0,
        "last_hint_time": None
    })
    await update.message.reply_text(f"🆕 New {length}-letter game started! You have 20 guesses.")

async def stop_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    games_col.delete_one({"chat_id": chat_id})
    await update.message.reply_text("Game stopped. Start a new one with /new.")

async def handle_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    text = update.message.text.lower().strip()
    # Check for P2P game first (if in DM)
    game = None
    if update.effective_chat.type == "private":
        game = games_col.find_one({"players": user.id, "game_type": "p2p"})
    if not game:
        game = games_col.find_one({"chat_id": chat_id})
    if not game:
        return

    # P2P mode
    if game.get("game_type") == "p2p":
        if game.get("current_turn") != user.id:
            await update.message.reply_text("It's not your turn! Wait for opponent.")
            return
        # Cancel timer for this user
        if user.id in p2p_timers:
            p2p_timers[user.id].cancel()
            del p2p_timers[user.id]
        word_len = 4
        if not text.isalpha() or len(text) != word_len:
            await update.message.reply_text(f"Please enter a {word_len}-letter word.")
            return
        if text not in WORD_LISTS[word_len]:
            await update.message.reply_text("This word is not in my dictionary.")
            return
        correct = game["word"]
        if text == correct:
            # Win
            await update.message.reply_text(f"🎉 Correct! You guessed the word `{correct}`. You win the match!", parse_mode="Markdown")
            opponent = [p for p in game["players"] if p != user.id][0]
            await context.bot.send_message(opponent, f"😞 {user.first_name} guessed the word `{correct}`. You lose.", parse_mode="Markdown")
            games_col.delete_one({"_id": game["_id"]})
            # Offer rematch
            challenge_id = game["chat_id"].replace("p2p_", "")
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔁 Rematch", callback_data=f"p2p_rematch_{challenge_id}")]
            ])
            await update.message.reply_text("Want a rematch?", reply_markup=keyboard)
            await context.bot.send_message(opponent, "Want a rematch?", reply_markup=keyboard)
            return
        else:
            feedback = format_feedback(text, correct)
            await update.message.reply_text(f"{feedback} `{text}`\n❌ Wrong guess! Now opponent's turn.", parse_mode="Markdown")
            opponent = [p for p in game["players"] if p != user.id][0]
            games_col.update_one({"_id": game["_id"]}, {"$set": {"current_turn": opponent}})
            await context.bot.send_message(opponent, "Your turn! Guess a 4-letter word. (You have 10 seconds)")
            await start_p2p_timer(context, opponent, game["chat_id"].replace("p2p_", ""))
        return

    # Classic or Daily game
    word_len = game["length"]
    if not text.isalpha() or len(text) != word_len:
        await update.message.reply_text(f"Please enter a {word_len}-letter word.")
        return
    if text not in WORD_LISTS[word_len]:
        await update.message.reply_text("This word is not in my dictionary.")
        return
    correct = game["word"]
    guesses = game.get("guesses", [])
    max_guesses = game.get("max_guesses", 20)
    if text in guesses:
        await update.message.reply_text("Already guessed!")
        return
    guesses.append(text)
    games_col.update_one({"chat_id": chat_id}, {"$set": {"guesses": guesses}})
    feedback = format_feedback(text, correct)
    await update.message.reply_text(f"{feedback} `{text}`", parse_mode="Markdown")
    if text != correct:
        clue = get_random_clue(correct, set(guesses))
        await update.message.reply_text(f"💡 *Clue:* {clue}", parse_mode="Markdown")
    if text == correct:
        now = datetime.utcnow()
        is_daily = (game.get("mode") == "daily")
        points_earned = 20 if is_daily else 12
        coin_reward = 20 if is_daily else 10
        scores_col.update_one(
            {"chat_id": chat_id, "user_id": user.id},
            {"$set": {"name": user.first_name, "updated": now}, "$inc": {"score": points_earned}},
            upsert=True
        )
        scores_col.update_one(
            {"chat_id": "global", "user_id": user.id},
            {"$set": {"name": user.first_name, "updated": now}, "$inc": {"score": points_earned}},
            upsert=True
        )
        stats = await update_user_stats(user.id, user.first_name, won=True, daily=is_daily, word_len=word_len)
        try:
            await update.message.react(emoji="🎉")
        except Exception as e:
            print(f"Reaction error: {e}")
        win_msg = (
            f"🎉 *{user.first_name} GUESSED IT RIGHT!* 🎉\n\n"
            f"🔑 *Correct word:* `{correct.upper()}`\n"
            f"📊 *Attempts:* {len(guesses)}/{max_guesses}\n"
            f"⭐ *Points:* +{points_earned}\n"
            f"💰 *Coins:* +{coin_reward}\n"
            f"📈 *Total coins:* {stats.get('total_coins', 0)}\n\n"
            f"📝 *Game summary:*\n"
        )
        summary = build_summary(guesses, correct, game.get("hint", ""))
        await update.message.reply_text(win_msg + summary, parse_mode="Markdown")
        games_col.delete_one({"chat_id": chat_id})
    elif len(guesses) >= max_guesses:
        await update.message.reply_text(f"Game over! Word was `{correct}`. Use /new.", parse_mode="Markdown")
        games_col.delete_one({"chat_id": chat_id})
        await update_user_stats(user.id, user.first_name, won=False, daily=(game.get("mode")=="daily"), word_len=word_len)

async def hint_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    game = games_col.find_one({"chat_id": chat_id})
    if not game:
        await update.message.reply_text("No active game. Start one with /new.")
        return
    stats = stats_col.find_one({"user_id": user.id})
    if not stats or stats.get("total_coins", 0) < 5:
        await update.message.reply_text("❌ You need 5 coins for a hint. Win games to earn coins.")
        return
    hints_used = game.get("hints_used", 0)
    if hints_used >= 3:
        await update.message.reply_text("❌ You've already used 3 hints in this game.")
        return
    last_hint = game.get("last_hint_time")
    if last_hint:
        last_time = datetime.fromisoformat(last_hint)
        if (datetime.utcnow() - last_time).total_seconds() < 10:
            await update.message.reply_text("⏳ Please wait 10 seconds before next hint.")
            return
    correct = game["word"]
    guesses = game.get("guesses", [])
    if guesses:
        unrevealed = [i for i, ch in enumerate(correct) if ch not in [g[i] for g in guesses]]
    else:
        unrevealed = list(range(len(correct)))
    if not unrevealed:
        await update.message.reply_text("No new hint available.")
        return
    pos = random.choice(unrevealed)
    letter = correct[pos]
    stats_col.update_one({"user_id": user.id}, {"$inc": {"total_coins": -5}})
    games_col.update_one({"chat_id": chat_id}, {"$inc": {"hints_used": 1}, "$set": {"last_hint_time": datetime.utcnow().isoformat()}})
    await update.message.reply_text(f"🔍 *Hint:* Position {pos+1} is `{letter.upper()}`.", parse_mode="Markdown")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    stats = stats_col.find_one({"user_id": user.id})
    if not stats:
        await update.message.reply_text("No stats yet. Play some games!")
        return
    msg = (
        f"📊 *Stats for {user.first_name}*\n\n"
        f"🎮 Games: {stats.get('total_games', 0)}\n"
        f"🏆 Wins: {stats.get('total_wins', 0)}\n"
        f"🔥 Streak: {stats.get('current_streak', 0)} days\n"
        f"🌟 Best streak: {stats.get('best_streak', 0)}\n"
        f"💰 Coins: {stats.get('total_coins', 0)}\n"
        f"📏 Wins by length: 4:{stats.get('wins_4',0)} 5:{stats.get('wins_5',0)} 6:{stats.get('wins_6',0)}"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    stats = stats_col.find_one({"user_id": user.id})
    if not stats:
        stats = {}
    photos = await context.bot.get_user_profile_photos(user.id, limit=1)
    caption = (
        f"👤 *Profile: {user.first_name}*\n"
        f"🆔 `{user.id}`\n\n"
        f"🎮 Total games: {stats.get('total_games',0)}\n"
        f"🏆 Wins: {stats.get('total_wins',0)}\n"
        f"🔥 Daily streak: {stats.get('current_streak',0)}\n"
        f"💰 Coins: {stats.get('total_coins',0)}\n"
        f"📏 4/5/6 wins: {stats.get('wins_4',0)}/{stats.get('wins_5',0)}/{stats.get('wins_6',0)}"
    )
    if photos.total_count > 0:
        photo = photos.photos[0][-1]
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo.file_id, caption=caption, parse_mode="Markdown")
    else:
        await update.message.reply_text(caption, parse_mode="Markdown")

async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    existing = games_col.find_one({"chat_id": chat_id})
    if existing:
        await update.message.reply_text("❌ Finish current game first (/stop).")
        return
    today = datetime.utcnow().date()
    daily = daily_col.find_one({"date": today.isoformat()})
    if not daily:
        word = random.choice(WORDS_4)
        daily_col.insert_one({"date": today.isoformat(), "word": word, "hint": f"Starts with '{word[0]}'"})
    else:
        word = daily["word"]
    games_col.insert_one({
        "chat_id": chat_id,
        "word": word,
        "hint": f"Starts with '{word[0]}'",
        "guesses": [],
        "length": 4,
        "start_time": datetime.utcnow(),
        "max_guesses": 6,
        "mode": "daily",
        "hints_used": 0,
        "last_hint_time": None
    })
    await update.message.reply_text("🌟 *Daily Challenge started!* 6 guesses only. Bonus points & coins!", parse_mode="Markdown")

# ---------- P2P RANDOM MATCHMAKING (QUEUE) ----------
p2p_timers = {}

async def cancel_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    result = p2p_queue_col.delete_one({"user_id": user.id})
    if result.deleted_count:
        await update.message.reply_text("❌ You have been removed from the matchmaking queue.")
    else:
        await update.message.reply_text("You are not in the queue.")

async def challenge_random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /challenge in DM: add to queue and match if possible."""
    user = update.effective_user
    chat = update.effective_chat
    if chat.type != "private":
        # If in group, we need to allow group challenge with argument
        # But since this handler runs only when no args, we should check args length
        # Actually in main we are using the same command for both, so we need to differentiate.
        # The main logic will call this function only when no args and in private? Let's handle inside.
        if context.args and context.args[0] in ['4','5','6']:
            # group challenge will be handled by separate handler
            return
        await update.message.reply_text("For group multiplayer, use /challenge 4|5|6")
        return

    # Check if user already has an active P2P game
    active_game = games_col.find_one({"players": user.id, "game_type": "p2p"})
    if active_game:
        await update.message.reply_text("You already have an active PvP game. Finish it first.")
        return

    # Check if user already in queue
    existing = p2p_queue_col.find_one({"user_id": user.id})
    if existing:
        await update.message.reply_text("You are already in the queue. Waiting for opponent...")
        return

    # Add to queue
    p2p_queue_col.insert_one({"user_id": user.id, "name": user.first_name, "joined_at": datetime.utcnow()})
    await update.message.reply_text("✅ You have been added to the matchmaking queue. Waiting for an opponent...")

    # Try to match
    await try_match(context)

async def try_match(context):
    """Check queue and match two users if available."""
    queue = list(p2p_queue_col.find().sort("joined_at", 1))
    if len(queue) >= 2:
        user1 = queue[0]
        user2 = queue[1]
        # Remove both from queue
        p2p_queue_col.delete_many({"user_id": {"$in": [user1["user_id"], user2["user_id"]]}})
        # Create challenge
        challenge_id = f"{user1['user_id']}_{user2['user_id']}_{int(datetime.utcnow().timestamp())}"
        p2p_col.insert_one({
            "challenge_id": challenge_id,
            "from_id": user1["user_id"],
            "to_id": user2["user_id"],
            "status": "accepted",  # auto-accepted
            "from_name": user1["name"],
            "to_name": user2["name"],
            "created_at": datetime.utcnow()
        })
        word = random.choice(WORDS_4)
        game_data = {
            "chat_id": f"p2p_{challenge_id}",
            "players": [user1["user_id"], user2["user_id"]],
            "word": word,
            "guesses": {},
            "current_turn": user1["user_id"],
            "start_time": datetime.utcnow(),
            "game_type": "p2p"
        }
        games_col.insert_one(game_data)
        # Notify both players
        await context.bot.send_message(chat_id=user1["user_id"], text=f"🎮 Match found! You are playing against {user2['name']}. You go first. Guess a 4-letter word. (10 seconds per turn)")
        await context.bot.send_message(chat_id=user2["user_id"], text=f"🎮 Match found! You are playing against {user1['name']}. Wait for your turn.")
        # Start timer for first player
        await start_p2p_timer(context, user1["user_id"], challenge_id)

# ---------- P2P CALLBACKS (rematch) ----------
async def p2p_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("p2p_rematch_"):
        challenge_id = data.split("_")[2]
        original = p2p_col.find_one({"challenge_id": challenge_id})
        if not original:
            await query.edit_message_text("Original challenge not found.")
            return
        # Check if both players still exist and not in another game
        p1 = original["from_id"]
        p2 = original["to_id"]
        active1 = games_col.find_one({"players": p1, "game_type": "p2p"})
        active2 = games_col.find_one({"players": p2, "game_type": "p2p"})
        if active1 or active2:
            await query.edit_message_text("One of the players is already in another game. Rematch cancelled.")
            return
        new_challenge_id = f"{p1}_{p2}_{int(datetime.utcnow().timestamp())}"
        p2p_col.insert_one({
            "challenge_id": new_challenge_id,
            "from_id": p1,
            "to_id": p2,
            "status": "accepted",
            "from_name": original["from_name"],
            "to_name": original["to_name"],
            "created_at": datetime.utcnow()
        })
        word = random.choice(WORDS_4)
        game_data = {
            "chat_id": f"p2p_{new_challenge_id}",
            "players": [p1, p2],
            "word": word,
            "guesses": {},
            "current_turn": p1,
            "start_time": datetime.utcnow(),
            "game_type": "p2p"
        }
        games_col.insert_one(game_data)
        await context.bot.send_message(chat_id=p1, text=f"🔁 Rematch started! You go first. Guess a 4-letter word. (10 seconds)")
        await context.bot.send_message(chat_id=p2, text=f"🔁 Rematch started! Wait for your turn.")
        await start_p2p_timer(context, p1, new_challenge_id)
        await query.edit_message_text("Rematch accepted! Game started.")

async def start_p2p_timer(context, user_id, challenge_id):
    if user_id in p2p_timers:
        p2p_timers[user_id].cancel()
    async def timeout():
        await asyncio.sleep(10)
        game = games_col.find_one({"chat_id": f"p2p_{challenge_id}"})
        if game and game.get("current_turn") == user_id:
            opponent = [p for p in game["players"] if p != user_id][0]
            await context.bot.send_message(user_id, "⏰ Time's up! You took too long. You lose the match.")
            await context.bot.send_message(opponent, "🎉 Your opponent ran out of time! You win!")
            games_col.delete_one({"_id": game["_id"]})
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔁 Rematch", callback_data=f"p2p_rematch_{challenge_id}")]
            ])
            await context.bot.send_message(user_id, "Want a rematch?", reply_markup=keyboard)
            await context.bot.send_message(opponent, "Want a rematch?", reply_markup=keyboard)
        if user_id in p2p_timers:
            del p2p_timers[user_id]
    task = asyncio.create_task(timeout())
    p2p_timers[user_id] = task

# ---------- GROUP MULTIPLAYER ----------
async def challenge_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args or args[0] not in ['4','5','6']:
        await update.message.reply_text("Usage: /challenge 4|5|6 to create group game")
        return
    length = int(args[0])
    chat_id = update.effective_chat.id
    if update.effective_chat.type not in ["group", "supergroup"]:
        await update.message.reply_text("This command only works in groups.")
        return
    game_id = f"{chat_id}_{int(datetime.utcnow().timestamp())}"
    group_games_col.insert_one({
        "game_id": game_id,
        "chat_id": chat_id,
        "length": length,
        "players": [],
        "max_players": 10,
        "min_players": 4,
        "status": "waiting",
        "created_by": update.effective_user.id,
        "created_at": datetime.utcnow(),
        "word": None
    })
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Join Game", url=f"https://t.me/{context.bot.username}?start=join_{game_id}")]
    ])
    await update.message.reply_text(f"🎮 {length}-letter word game created! Need 4-10 players. /join {game_id} to join.", reply_markup=keyboard)

async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /join <gameid>")
        return
    game_id = context.args[0]
    game = group_games_col.find_one({"game_id": game_id, "status": "waiting"})
    if not game:
        await update.message.reply_text("Game not found or already started.")
        return
    user_id = update.effective_user.id
    if user_id in game["players"]:
        await update.message.reply_text("Already joined.")
        return
    group_games_col.update_one({"game_id": game_id}, {"$push": {"players": user_id}})
    players = game["players"] + [user_id]
    if len(players) >= game["min_players"]:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Start Game", callback_data=f"group_start_{game_id}")]
        ])
        await context.bot.send_message(chat_id=game["chat_id"], text=f"{len(players)} players joined. Game creator, click Start to begin.", reply_markup=keyboard)
    await update.message.reply_text(f"Joined! {len(players)}/{game['max_players']} players.")

async def group_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("group_start_"):
        game_id = data.split("_")[2]
        game = group_games_col.find_one({"game_id": game_id})
        if not game or game["status"] != "waiting":
            await query.edit_message_text("Game already started or invalid.")
            return
        if query.from_user.id != game["created_by"]:
            await query.answer("Only creator can start.", show_alert=True)
            return
        players = game["players"]
        if len(players) < game["min_players"]:
            await query.edit_message_text(f"Need at least {game['min_players']} players. Currently {len(players)}.")
            return
        word = random.choice(WORD_LISTS[game["length"]])
        group_games_col.update_one({"game_id": game_id}, {"$set": {"status": "active", "word": word, "guesses": {}}})
        for pid in players:
            try:
                await context.bot.send_message(chat_id=pid, text=f"🎮 Group game started! Word length: {game['length']}. Send your guesses here (DM).")
            except:
                pass
        await query.edit_message_text("Game started! Check your DMs.")

# ---------- BOT ADDED LOG ----------
async def log_bot_added(update: ChatMemberUpdated, context: ContextTypes.DEFAULT_TYPE):
    if update.my_chat_member.new_chat_member.status in ["member", "administrator"]:
        chat = update.my_chat_member.chat
        user = update.my_chat_member.from_user
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Support", url="https://t.me/TEAMSANKI"),
             InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/ll_SANKI_II")]
        ])
        await context.bot.send_message(chat_id=chat.id, text="Thanks for adding me! Use /help to learn how to play.", reply_markup=keyboard)
        await context.bot.send_message(chat_id=LOGGER_GROUP_ID, text=f"➕ Bot added to {chat.title} by {user.mention_html()}", parse_mode="HTML")

# ---------- MAIN ----------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", send_welcome))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("new", new_game))
    app.add_handler(CommandHandler("daily", daily_command))
    app.add_handler(CommandHandler("stop", stop_game))
    app.add_handler(CommandHandler("hint", hint_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("streakfreeze", streakfreeze_command))
    app.add_handler(CommandHandler("cancel", cancel_queue))
    # Challenge handlers: no args -> random queue; with args 4|5|6 -> group
    app.add_handler(CommandHandler("challenge", challenge_random, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("challenge", challenge_group, filters=filters.ChatType.GROUPS))
    app.add_handler(CommandHandler("join", join_game))
    app.add_handler(CallbackQueryHandler(leaderboard_callback, pattern="^lb_"))
    app.add_handler(CallbackQueryHandler(p2p_callback, pattern="^p2p_"))
    app.add_handler(CallbackQueryHandler(group_start_callback, pattern="^group_start_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_guess))
    app.add_handler(ChatMemberHandler(log_bot_added, ChatMemberHandler.MY_CHAT_MEMBER))
    print("Bot started with random PvP matchmaking, group games, streak freeze, leaderboard.")
    app.run_polling()
