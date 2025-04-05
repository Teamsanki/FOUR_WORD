import random
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ChatMemberHandler
)

TOKEN = "7762113593:AAHEhm8iuyf4W0VfnF0MkifOeW2zCOfrMVo"  # Replace with your bot token

# Bot Owner and Support Info
OWNER_USERNAME = "@ll_SANKI_II"  # Replace with your @username
SUPPORT_CHANNEL = "https://t.me/SANKINETWORK"
WELCOME_IMAGE_URL = "https://graph.org/file/2e37a57d083183ea24761-9cc38246fecc1af393.jpg"  # Replace with image URL

# Word list (400 4-letter words)
WORDS = [
    "able", "acid", "aged", "also", "area", "army", "away", "baby", "back", "ball",
    "band", "bank", "base", "bath", "bear", "beat", "been", "beer", "bell", "belt",
    "best", "bill", "bird", "blow", "blue", "boat", "body", "bomb", "bond", "bone",
    "book", "boom", "boot", "born", "boss", "both", "bowl", "bulk", "burn", "bush",
    "busy", "cafe", "cake", "call", "calm", "came", "camp", "card", "care", "case",
    "cash", "cast", "cell", "chat", "chip", "city", "club", "coal", "coat", "code",
    "cold", "come", "cook", "cool", "cope", "copy", "core", "cost", "crew", "crop",
    "dark", "data", "date", "dawn", "dead", "deal", "dean", "dear", "debt", "deep",
    "deer", "desk", "dial", "died", "diet", "disc", "disk", "does", "done", "door",
    "dose", "down", "draw", "drop", "drum", "duck", "dust", "duty", "each", "earn",
    "ease", "east", "easy", "edge", "else", "even", "ever", "evil", "exit", "face",
    "fact", "fail", "fair", "fall", "fame", "farm", "fast", "fate", "fear", "feed",
    "feel", "feet", "fell", "felt", "file", "fill", "film", "find", "fine", "fire",
    "firm", "fish", "five", "flat", "flow", "fold", "folk", "food", "fool", "foot",
    "form", "fort", "four", "free", "from", "fuel", "full", "fund", "gain", "game",
    "gate", "gave", "gear", "gene", "gift", "girl", "give", "glad", "goal", "goes",
    "gold", "golf", "gone", "good", "gray", "grew", "grey", "grow", "gulf", "hair",
    "half", "hall", "hand", "hang", "hard", "harm", "hate", "have", "head", "hear",
    "heat", "held", "hell", "help", "herb", "hero", "hide", "high", "hill", "hire",
    "hold", "hole", "holy", "home", "hope", "host", "hour", "huge", "hung", "hunt",
    "hurt", "idea", "inch", "into", "iron", "item", "jack", "jane", "jean", "john",
    "join", "jump", "jury", "just", "keep", "kent", "kept", "kick", "kill", "kind",
    "king", "knee", "knew", "know", "lack", "lady", "laid", "lake", "land", "lane",
    "last", "late", "lead", "left", "less", "life", "lift", "like", "line", "link",
    "list", "live", "load", "loan", "lock", "logo", "long", "look", "lord", "lose",
    "loss", "lost", "love", "luck", "made", "mail", "main", "make", "male", "many",
    "mark", "mass", "matt", "meal", "mean", "meat", "meet", "menu", "mere", "mild",
    "mile", "milk", "mill", "mind", "mine", "miss", "mode", "mood", "moon", "more",
    "most", "move", "much", "must", "name", "navy", "near", "neck", "need", "news",
    "next", "nice", "nick", "nine", "none", "nose", "note", "okay", "once", "only",
    "onto", "open", "oral", "over", "pace", "pack", "page", "paid", "pain", "pair",
    "palm", "park", "part", "pass", "past", "path", "peak", "pick", "pipe", "plan",
    "play", "plot", "plug", "plus", "poll", "pool", "poor", "port", "post", "pull",
    "pure", "push", "race", "rail", "rain", "rank", "rare", "rate", "read", "real",
    "rear", "rely", "rent", "rest", "rice", "rich", "ride", "ring", "rise", "risk",
    "road", "rock", "role", "roof", "room", "root", "rose", "rule", "rush", "safe",
    "said", "sake", "sale", "salt", "same", "sand", "save", "seat", "seed", "seek",
    "seem", "seen", "self", "sell", "send", "sent", "sept", "ship", "shop", "shot",
    "show", "shut", "sick", "side", "sign", "site", "size", "skin", "slip", "slow",
    "snow", "soft", "soil", "sold", "sole", "some", "song", "soon", "sort", "soul",
    "spot", "star", "stay", "step", "stop", "such", "suit", "sure", "take", "tale",
    "talk", "tall", "tank", "tape", "task", "team", "tech", "tell", "tend", "term",
    "test", "text", "than", "that", "them", "then", "they", "thin", "this", "thus",
    "till", "time", "tiny", "told", "toll", "tone", "tony", "took", "tool", "tour",
    "town", "tree", "trip", "true", "tube", "tune", "turn", "type", "unit", "upon",
    "used", "user", "vary", "vast", "very", "view", "vote", "wait", "wake", "walk",
    "wall", "want", "ward", "warm", "wash", "wave", "ways", "weak", "wear", "week",
    "well", "went", "were", "west", "what", "when", "whom", "wide", "wife", "wild",
    "will", "wind", "wine", "wing", "wins", "wipe", "wise", "wish", "with", "wood",
    "word", "wore", "work", "yard", "yeah", "year", "your", "zero", "zone"
]

games = {}
scores = {}

# Welcome message
async def send_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("👤 Contact Owner", url=f"https://t.me/{OWNER_USERNAME}"),
            InlineKeyboardButton("💬 Support Channel", url=SUPPORT_CHANNEL)
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    caption = (
        "**Welcome to WordSeekBot!**\n\n"
        "Guess 4-letter words with friends in groups.\n"
        "Start a game with /new and see scores with /leaderboard.\n"
        "Bot gives color feedback + 👻 when you guess right!"
    )

    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=WELCOME_IMAGE_URL,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# /start handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_welcome_message(update, context)

# when bot added to group
async def added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.my_chat_member.new_chat_member.status == "member":
        await send_welcome_message(update, context)

# /new command
async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    word = random.choice(WORDS)
    games[chat_id] = word
    await update.message.reply_text(f"New game started! Guess the 4-letter word.")

# /leaderboard command
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in scores:
        await update.message.reply_text("No scores yet!")
        return

    sorted_scores = sorted(scores[chat_id].items(), key=lambda x: x[1], reverse=True)
    msg = "**Leaderboard:**\n"
    for user, score in sorted_scores:
        msg += f"{user}: {score} pts\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

# Handle guesses
async def handle_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in games:
        return

    guess = update.message.text.lower()
    if len(guess) != 4 or not guess.isalpha():
        return

    correct_word = games[chat_id]
    colored = ""
    for i in range(4):
        if guess[i] == correct_word[i]:
            colored += "🟩"
        elif guess[i] in correct_word:
            colored += "🟨"
        else:
            colored += "🟥"

    await update.message.reply_text(colored)

    if guess == correct_word:
        await context.bot.send_message(chat_id, f"{update.effective_user.first_name} guessed it! {correct_word}")
        await update.message.reply_text("👻")
        user = update.effective_user.first_name
        if chat_id not in scores:
            scores[chat_id] = {}
        scores[chat_id][user] = scores[chat_id].get(user, 0) + 1
        del games[chat_id]

# Main function
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(ChatMemberHandler(added_to_group, chat_member_types=["my_chat_member"]))
    app.add_handler(CommandHandler("new", new_game))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_guess))

    print("WordSeekBot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
