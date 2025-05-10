# All imports come FIRST
import random
from datetime import datetime, timedelta
from pymongo import MongoClient
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatMemberUpdated  # <-- Ye yahan hona chahiye
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ChatMemberHandler,  # <-- Ye bhi chahiye agar tum ChatMemberUpdated use kar rahe ho
    filters
)

# Now your function definitions can begin
async def log_bot_added(update: ChatMemberUpdated, context: ContextTypes.DEFAULT_TYPE):
    # your logic
    pass

# --- Bot Config ---
TOKEN = os.environ.get("8051196592:AAFAUOslCAPFszXfvjJB0nMVe7vRAUAene0")
MONGO_URL = os.environ.get("mongodb+srv://TSANKI:TSANKI@cluster0.u2eg9e1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")  # <-- Replace this with your MongoDB connection string
WELCOME_IMAGE_URL = "https://graph.org/file/c0e17724e66a68a2de3a6-5ff173af1d3498d9e7.jpg"  # <-- Replace with your welcome image
LOGGER_GROUP_ID = -1002100433415

# --- MongoDB Setup ---
client = MongoClient(MONGO_URL)
db = client["wordseekbot"]
games_col = db["games"]
scores_col = db["scores"]

# --- Word List ---
WORDS = [
    # A
    'able', 'acid', 'aged', 'also', 'area', 'army', 'atom', 'aunt', 'away', 'axis', 'amit', 'dick', 'slap', 'crow',
    # B
    'baby', 'back', 'bake', 'ball', 'band', 'bank', 'barn', 'base', 'bath', 'bear',
    'beat', 'been', 'bell', 'belt', 'bend', 'best', 'bike', 'bill', 'bird', 'bite',
    'blue', 'boat', 'body', 'bomb', 'bond', 'bone', 'book', 'boom', 'boot', 'bore',
    'born', 'boss', 'both', 'bowl', 'brag', 'bray', 'bred', 'brew', 'brim', 'buck',
    'buff', 'bulk', 'bull', 'bump', 'burn', 'bush', 'busy', 'buzz', 'byte',
    # C
    'cage', 'cake', 'call', 'calm', 'camp', 'card', 'care', 'cart', 'case', 'cash',
    'cast', 'cave', 'cell', 'chat', 'chip', 'city', 'clay', 'club', 'coal', 'coat',
    'cold', 'come', 'cook', 'cool', 'cope', 'cord', 'core', 'cost', 'crew', 'crop',
    'curl', 'cute', 'chill'
    # D
    'dark', 'data', 'date', 'dawn', 'deal', 'debt', 'deep', 'deer', 'desk', 'dial',
    'dice', 'died', 'diet', 'dime', 'dine', 'dish', 'disk', 'dive', 'dock', 'does',
    'doge', 'dome', 'done', 'doom', 'door', 'dose', 'down', 'drag', 'draw', 'drop',
    'drum', 'dual', 'duck', 'duke', 'dull', 'dust', 'duty',
    # E
    'each', 'earn', 'ease', 'east', 'easy', 'edge', 'edit', 'else', 'envy', 'epic',
    'even', 'ever', 'evil', 'exam', 'exit', 'eyes',
    # F
    'face', 'fact', 'fade', 'fail', 'fair', 'fake', 'fall', 'fame', 'farm', 'fast',
    'fate', 'fear', 'feed', 'feel', 'feet', 'fell', 'felt', 'file', 'fill', 'film',
    'find', 'fine', 'fire', 'firm', 'fish', 'fist', 'five', 'flag', 'flat', 'flip',
    'flow', 'fold', 'folk', 'food', 'foot', 'form', 'fort', 'four', 'free', 'frog',
    'fuel', 'full', 'fund', 'fuse',
    # G
    'gain', 'game', 'gang', 'gate', 'gave', 'gear', 'gene', 'gift', 'girl', 'give',
    'glad', 'goal', 'goat', 'gold', 'golf', 'gone', 'good', 'grab', 'gray', 'grew',
    'grid', 'grim', 'grip', 'grow', 'gulf', 'guts',
    # H
    'hair', 'half', 'hall', 'hand', 'hang', 'hard', 'harm', 'hate', 'have', 'hawk',
    'head', 'heal', 'heap', 'hear', 'heat', 'held', 'hell', 'help', 'herb', 'hero',
    'hide', 'high', 'hill', 'hire', 'hold', 'hole', 'holy', 'home', 'hope', 'horn',
    'host', 'hour', 'huge', 'hung', 'hunt', 'hurt',
    # I
    'idea', 'idle', 'inch', 'into', 'iron', 'item',
    # J
    'jack', 'jade', 'jail', 'jazz', 'jeep', 'jest', 'join', 'joke', 'jump', 'jury',
    # K
    'keep', 'kept', 'kick', 'kill', 'kind', 'king', 'kiss', 'kite', 'knee', 'knew',
    'knit', 'know',
    # L
    'lack', 'lady', 'lake', 'lamp', 'land', 'lane', 'last', 'late', 'lava', 'lazy',
    'lead', 'leaf', 'left', 'lend', 'less', 'life', 'lift', 'like', 'limb', 'line',
    'link', 'lion', 'list', 'live', 'load', 'loan', 'lock', 'logo', 'long', 'look',
    'loop', 'lord', 'lose', 'loss', 'lost', 'love', 'luck', 'lung',
    # M
    'made', 'mail', 'main', 'make', 'male', 'mall', 'many', 'mark', 'mask', 'mass',
    'mate', 'meal', 'mean', 'meat', 'meet', 'melt', 'menu', 'mere', 'mice', 'mild',
    'mile', 'milk', 'mill', 'mind', 'mine', 'mint', 'miss', 'mist', 'mode', 'mood',
    'moon', 'more', 'most', 'move', 'much', 'must', 'myth',
    # N
    'name', 'navy', 'near', 'neck', 'need', 'nest', 'news', 'next', 'nice', 'nick',
    'nine', 'node', 'none', 'noon', 'nose', 'note', 'noun', 'nuts',
    # O
    'oath', 'obey', 'omit', 'once', 'only', 'onto', 'open', 'oral', 'ours', 'oval',
    'oven', 'over', 'owed', 'own',
    # P
    'pack', 'page', 'paid', 'pain', 'pair', 'palm', 'park', 'part', 'pass', 'past',
    'path', 'peak', 'pear', 'peel', 'peer', 'peny', 'pick', 'pile', 'pill', 'pine',
    'pink', 'pipe', 'plan', 'play', 'plot', 'plug', 'plus', 'poem', 'pole', 'poll',
    'pond', 'pool', 'poor', 'port', 'post', 'pull', 'pure', 'push', 'pins', 
    # Q
    'quad', 'quiz', 'quit', 'quip',
    # R
    'race', 'rack', 'rage', 'raid', 'rail', 'rain', 'rank', 'rate', 'rays', 'read',
    'real', 'rear', 'redo', 'reed', 'reef', 'rest', 'rice', 'rich', 'ride', 'ring',
    'riot', 'rise', 'risk', 'road', 'rock', 'role', 'roof', 'room', 'root', 'rope',
    'rose', 'rule', 'rush', 'rust',
    # S
    'safe', 'said', 'sail', 'salt', 'same', 'sand', 'save', 'scan', 'scar', 'seal',
    'seat', 'seed', 'seek', 'seem', 'seen', 'self', 'sell', 'send', 'ship', 'shop',
    'shot', 'show', 'shut', 'side', 'sign', 'silk', 'sink', 'site', 'size', 'slip',
    'slow', 'snap', 'snow', 'soap', 'soft', 'soil', 'sold', 'sole', 'some', 'song',
    'soon', 'sort', 'soul', 'spot', 'star', 'stay', 'step', 'stop', 'such', 'suit', 'smag',
    'sure', 'swim', 'sync',
    # T
    'tail', 'take', 'tale', 'talk', 'tall', 'tank', 'tape', 'task', 'team', 'tear',
    'tech', 'tell', 'tend', 'tent', 'term', 'test', 'text', 'than', 'that', 'them',
    'then', 'they', 'thin', 'this', 'thus', 'time', 'tire', 'told', 'toll', 'tone',
    'tool', 'tops', 'torn', 'tour', 'town', 'trap', 'tree', 'trip', 'true', 'tube',
    'tune', 'turn', 'twin', 'type',
    # U
    'ugly', 'unit', 'urge', 'used', 'user', 'upon',
    # V
    'vain', 'vast', 'veil', 'verb', 'very', 'vest', 'view', 'vine', 'visa', 'vote',
    # W
    'wage', 'wait', 'wake', 'walk', 'wall', 'want', 'ward', 'warm', 'warn', 'wash',
    'wave', 'weak', 'wear', 'weed', 'week', 'well', 'west', 'what', 'when', 'whip',
    'wide', 'wife', 'wild', 'will', 'wind', 'wine', 'wing', 'wink', 'wipe', 'wire',
    'wise', 'wish', 'wolf', 'wood', 'word', 'worn', 'wrap', 'work',
    # X
    'xray',
    # Y
    'yard', 'yarn', 'yawn', 'yeah', 'year', 'yell', 'your', 'yoga',
    # Z
    'zero', 'zinc', 'zone', 'zoom', 'okay', 'love', 'cool', 'yeah', 'nope', 'okay', 'sure', 'fine', 'oops', 'haha',
    'bruh', 'dude', 'lmao', 'omfg', 'yess', 'nooo', 'wait', 'stop', 'yolo', 'done',
    'nice', 'hmmn', 'help', 'soon', 'gone', 'late', 'meet', 'talk', 'ping', 'miss',
    'babe', 'hold', 'call', 'chat', 'text', 'busy', 'back', 'left', 'seen', 'join',
    'kick', 'cool', 'fire', 'drop', 'true', 'lame', 'vibe', 'hide', 'stay', 'walk',
    'ride', 'camp', 'snap', 'post', 'send', 'show', 'list', 'work', 'rest', 'play',
    'move', 'plan', 'skip', 'fail', 'pass', 'save', 'load', 'push', 'pull', 'pick',
    'pack', 'open', 'shut', 'turn', 'roll', 'hate', 'exit', 'kick', 'join', 'edit',
    'zoom', 'mute', 'like', 'love', 'okay', 'sure', 'cool', 'haha', 'nope', 'yeah',
    'hype', 'mood', 'rofl', 'kbye', 'ughh', 'idfc', 'frfr', 'ttyl', 'g2g', 'bruh',
    'yass', 'pfft', 'omfg', 'lmao', 'yolo', 'amir', 'fomo', 'bffs', 'noob', 'prol',
    'defs', 'jkid', 'whut', 'hruu', 'heyy', 'hiya', 'plss', 'thnx', 'bbye', 'okie',
    'gotu', 'gtfo', 'stop', 'goon', 'ugly', 'neat', 'fail', 'gold', 'cute', 'glow',
    'grim', 'dead', 'live', 'wish', 'pray', 'heal', 'ouch', 'aaaa', 'ohno', 'dang',
    'ewww', 'hype', 'mood', 'bros', 'slow', 'fast', 'high', 'solo', 'crew', 'team',
    'lose', 'gain', 'hard', 'easy', 'flex', 'bent', 'hurt', 'calm', 'deep', 'open',
    'lock', 'free', 'lost', 'good', 'dark', 'safe', 'evil', 'cool', 'wild', 'rain',
    'wind', 'heat', 'cold', 'snow', 'mist', 'dusk', 'dawn', 'moon', 'star', 'cute',
    'baby', 'girl', 'boii', 'lady', 'wife', 'huby', 'mate', 'best', 'fave', 'gang',
    'bros', 'sisr', 'kids', 'bros', 'bros', 'home', 'room', 'door', 'hall', 'lamp',
    'sofa', 'food', 'cook', 'bake', 'rice', 'cake', 'milk', 'fish', 'meal', 'dish',
    'pick', 'drop', 'pour', 'boil', 'open', 'snap', 'push', 'grab', 'jump', 'rest',
    'walk', 'ride', 'camp', 'trip', 'tour', 'stay', 'plan', 'date', 'hang', 'call',
    'text', 'ring', 'vibe', 'chat', 'ping', 'note', 'post', 'send', 'save', 'view',
    'like', 'read', 'skip', 'next', 'edit', 'play', 'stop', 'load', 'save', 'exit',
    'fast', 'slow', 'jump', 'walk', 'drop', 'hide', 'seek', 'look', 'help', 'give',
    'take', 'make', 'move', 'keep', 'hold', 'pull', 'push', 'quit', 'stay', 'rest',
    'feel', 'wish', 'hate', 'love', 'need', 'want', 'miss', 'join', 'kick', 'mute',
    'hype', 'boss', 'rich', 'broke', 'debt', 'cash', 'card', 'paid', 'send', 'loan',
    'grab', 'cute', 'sexy', 'bold', 'kind', 'mean', 'nice', 'calm', 'lazy', 'cool',
    'work', 'task', 'deal', 'meet', 'chat', 'talk', 'hold', 'plan', 'type', 'code',
    'note', 'list', 'done', 'soon', 'time', 'date', 'year', 'week', 'hour', 'mins',
    'mood', 'zone', 'area', 'land', 'side', 'city', 'road', 'lane', 'view', 'spot',
    'park', 'shop', 'mall', 'home', 'stay', 'room', 'hall', 'seat', 'lamp', 'door',
    'lock', 'open', 'pass', 'fail', 'test', 'exam', 'quiz', 'goal', 'task', 'plan',
    'luck', 'hope', 'heal', 'feel', 'hurt', 'ouch', 'pain', 'calm', 'bore', 'hype',
    'noob', 'proo', 'flex', 'game', 'play', 'lose', 'winr', 'fail', 'team', 'solo',
    'duo', 'loot', 'drop', 'grab', 'kill', 'ping', 'camp', 'jump', 'move', 'zone',
    'rush', 'mute', 'chat', 'rage', 'load', 'save', 'exit', 'next', 'edit', 'reel',
    'like', 'post', 'feed', 'link', 'live', 'snap', 'view', 'read', 'send', 'chat',
    'help', 'safe', 'cool', 'cute', 'bold', 'vibe', 'ride', 'zoom', 'wait', 'okay',
    'same', 'news', 'info', 'data', 'pass', 'fail', 'join', 'left', 'back', 'soon',
    'hope', 'pray', 'need', 'miss', 'gone', 'done', 'talk', 'meet', 'plan', 'call',
    'cool', 'play', 'game', 'task', 'work', 'done', 'boss', 'safe', 'deal', 'chat',
    'cash', 'loan', 'bill', 'paid', 'card', 'send', 'paid', 'bank', 'gpay', 'earn',
    'wish', 'goal', 'task', 'list', 'note', 'idea', 'memo', 'soon', 'date', 'time',
    'text', 'okay', 'kbye', 'nope', 'heyy', 'stop', 'love', 'pain', 'gift', 'ring',
    'wife', 'babe', 'cute', 'girl', 'boii', 'date', 'kiss', 'hold', 'plan', 'ride',
    'drop', 'call', 'chat', 'miss', 'back', 'soon', 'home', 'stay', 'feel', 'hope',
    'fuel', 'ride', 'walk', 'cash', 'card', 'bank', 'send', 'paid', 'drop', 'ping',
    'bump', 'fast', 'slow', 'glow', 'mask', 'heal', 'dark', 'chat', 'save', 'play',
    'turn', 'cool', 'pass', 'fail', 'note', 'read', 'edit', 'text', 'view', 'snap',
    'hide', 'show', 'hold', 'drop', 'stop', 'open', 'list', 'link', 'site', 'page',
    'shop', 'sale', 'deal', 'item', 'size', 'shoe', 'jean', 'belt', 'cart', 'bill',
    'rate', 'like', 'post', 'news', 'feed', 'info', 'data', 'memo', 'call', 'talk',
    'plan', 'goal', 'idea', 'wish', 'luck', 'hope', 'stay', 'live', 'move', 'camp',
    'trip', 'zone', 'area', 'site', 'home', 'room', 'lamp', 'door', 'lock', 'seat',
    'pick', 'pull', 'push', 'grab', 'make', 'type', 'skip', 'load', 'exit', 'join',
    'mute', 'hear', 'buzz', 'ring', 'tone', 'beep', 'flip', 'hold', 'drop', 'walk',
    'feel', 'pain', 'ouch', 'hurt', 'cold', 'warm', 'heat', 'rain', 'snow', 'damp',
    'dusk', 'dawn', 'nite', 'noon', 'date', 'year', 'week', 'time', 'mins', 'secs',
    'soon', 'gone', 'past', 'next', 'then', 'late', 'meet', 'chat', 'miss', 'seen',
    'back', 'away', 'rest', 'play', 'game', 'solo', 'duo', 'team', 'winr', 'lose',
    'fail', 'skip', 'done', 'view', 'grab', 'hunt', 'camp', 'ping', 'text', 'chat',
    'vote', 'poll', 'like', 'rate', 'rank', 'list', 'item', 'cart', 'deal', 'cost',
    'loan', 'debt', 'rich', 'poor', 'work', 'task', 'done', 'soon', 'late', 'plan',
    'fire', 'safe', 'cool', 'warm', 'wind', 'snow', 'haze', 'mist', 'drop', 'pour',
    'boil', 'cook', 'bake', 'rice', 'milk', 'salt', 'meat', 'fish', 'food', 'cake',
    'fork', 'spoon', 'dine', 'seat', 'hall', 'room', 'lamp', 'home', 'stay', 'move',
    'text', 'chat', 'buzz', 'note', 'edit', 'clip', 'film', 'snap', 'reel', 'live',
    'ping', 'link', 'site', 'news', 'post', 'like', 'save', 'view', 'load', 'exit',
    'open', 'lock', 'door', 'bell', 'lamp', 'shop', 'mall', 'plaza', 'road', 'lane',
    'city', 'zone', 'area', 'side', 'path', 'walk', 'jump', 'ride', 'bike', 'jeep',
    'gear', 'auto', 'fuel', 'toll', 'pass', 'road', 'sign', 'trip', 'stay', 'park',
    'seat', 'belt', 'safe', 'exit', 'turn', 'wait', 'slow', 'move', 'rush', 'stop',
    'mute', 'buzz', 'call', 'ring', 'vibe', 'tone', 'load', 'save', 'exit', 'boot',
    'tech', 'apps', 'game', 'play', 'quit', 'fail', 'pass', 'test', 'quiz', 'exam',
    'task', 'work', 'deal', 'mail', 'send', 'ship', 'load', 'pack', 'pick', 'drop',
    'done', 'skip', 'view', 'list', 'note', 'memo', 'text', 'edit', 'link', 'page',
    'site', 'wiki', 'post', 'news', 'clip', 'film', 'snap', 'show', 'load', 'live',
    'cash', 'paid', 'card', 'debt', 'loan', 'earn', 'rate', 'bank', 'save', 'send',
    'bill', 'cost', 'deal', 'item', 'shop', 'cart', 'size', 'jean', 'belt', 'pair',
    'look', 'vibe', 'cool', 'dark', 'cute', 'bold', 'wild', 'calm', 'kind', 'mean',
    'lazy', 'sore', 'grim', 'wish', 'pray', 'gift', 'pack', 'wrap', 'ring', 'neck',
    'babe', 'wife', 'lady', 'baby', 'kids', 'girl', 'boii', 'bros', 'best', 'gang',
    'mate', 'crew', 'team', 'bros', 'home', 'base', 'stay', 'room', 'hall', 'gate',
    'open', 'shut', 'pull', 'push', 'buzz', 'ring', 'bell', 'door', 'seat', 'lamp',
    'trip', 'tour', 'camp', 'tent', 'ride', 'bike', 'walk', 'move', 'rush', 'goon',
    'text', 'snap', 'edit', 'clip', 'load', 'play', 'join', 'exit', 'pass', 'fail',
    'plan', 'goal', 'idea', 'note', 'memo', 'test', 'quiz', 'exam', 'task', 'work',
    'meet', 'call', 'chat', 'talk', 'type', 'ping', 'buzz', 'hold', 'drop', 'stay',
    'jump', 'ride', 'bike', 'jeep', 'gear', 'fast', 'slow', 'hype', 'news', 'page',
    'rate', 'rank', 'poll', 'vote', 'pass', 'skip', 'list', 'link', 'site', 'edit',
    'time', 'year', 'date', 'week', 'soon', 'past', 'late', 'gone', 'next', 'done',
    'cold', 'warm', 'cool', 'fire', 'rain', 'snow', 'heat', 'mist', 'hail', 'wind',
    'okay', 'fine', 'yeah', 'nope', 'nooo', 'yess', 'okay', 'idk', 'bruh', 'lmao',
    'kbye', 'ttyl', 'omfg', 'ughh', 'yolo', 'fomo', 'bffs', 'defz', 'whut', 'frfr'
]

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
    user = update.effective_user

    # Send welcome photo and buttons
    keyboard = [
        [InlineKeyboardButton("➕ Add Me In Your Group ➕", url="https://t.me/SANKIWORDSEEKBOT?startgroup=true")],
        [
            InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/ll_SANKI_II"),
            InlineKeyboardButton("📢 Support Channel", url="https://t.me/SANKINETWORK")
        ],
        [InlineKeyboardButton("👻 Four Word Group", url="https://t.me/Fourwordgusser")]
    ]
    markup = InlineKeyboardMarkup(keyboard)

    caption = (
        "✨ 𝙒𝙚𝙡𝙘𝙤𝙢𝙚 𝙏𝙤 *𝙁𝙤𝙪𝙧 𝙒𝙤𝙧𝙙* ✨\n\n"
        "🔤 Guess the hidden 4-letter word!\n"
        "🎯 Get instant color-coded feedback.\n"
        "🏆 Compete on leaderboards (Today / Overall / Global)\n\n"
        "💥 Use /new to start playing now!\n"
        "👑 Owner: @ll_SANKI_II\n"
        "📢 Support: @SANKINETWORK"
    )

    await context.bot.send_photo(
        chat_id=chat.id,
        photo=WELCOME_IMAGE_URL,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=markup
    )

    # Logging start event to logger group
    if user:
        log_msg = (
            f"✨ <b>ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ</b> ✨\n\n"
            f"<b>ᴜsᴇʀ ɪᴅ:</b> <code>{user.id}</code>\n"
            f"<b>ᴜsᴇʀɴᴀᴍᴇ:</b> {user.mention_html()}"
        )
        await context.bot.send_message(
            chat_id=LOGGER_GROUP_ID,
            text=log_msg,
            parse_mode="HTML"
        )

# Group Add Logger
async def log_bot_added(update: ChatMemberUpdated, context: ContextTypes.DEFAULT_TYPE):
    member = update.my_chat_member
    chat = member.chat
    user = member.from_user

    if member.new_chat_member.status in ["member", "administrator"]:
        chat_username = f"@{chat.username}" if chat.username else "Private"
        chat_link = f"https://t.me/{chat.username}" if chat.username else "Not Available"

        try:
            members = await context.bot.get_chat_members_count(chat.id)
        except:
            members = "Unknown"

        msg = (
            "📝 <b>𝐌𝐮𝐬𝐢𝐜 𝐁𝐨𝐭 𝐀𝐝𝐝𝐞𝐝 𝐈𝐧 𝐍𝐞𝐰 𝐆𝐫𝐨𝐮𝐩</b>\n\n"
            f"📌 <b>𝐂𝐡𝐚𝐭 𝐍𝐚𝐦𝐞:</b> {chat.title}\n"
            f"🍂 <b>𝐂𝐡𝐚𝐭 𝐈𝐝:</b> <code>{chat.id}</code>\n"
            f"🔐 <b>𝐂𝐡𝐚𝐭 𝐔𝐬𝐞𝐫𝐧𝐚𝐦𝐞:</b> {chat_username}\n"
            f"🛰 <b>𝐂𝐡𝐚𝐭 𝐋𝐢𝐧𝐤:</b> {chat_link}\n"
            f"📈 <b>𝐆𝐫𝐨𝐮𝐩 𝐌𝐞𝐦𝐛𝐞𝐫𝐬:</b> {members}\n"
            f"🤔 <b>𝐀𝐝𝐝𝐞𝐝 𝐁𝐲:</b> {user.mention_html()}"
        )

        await context.bot.send_message(
            chat_id=LOGGER_GROUP_ID,
            text=msg,
            parse_mode="HTML"
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
            "start_time": datetime.utcnow(),
            "max_guesses": 20  # Limit the number of guesses
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
    game = games_col.find_one({"chat_id": chat_id})
    if not game:
        return  # Game not running, ignore all messages

    user = update.effective_user
    text = update.message.text.lower()

    if not text.isalpha() or len(text) != 4:
        await update.message.reply_text("Please enter a valid 4-letter word.")
        return

    if text not in WORDS:
        await update.message.reply_text("This word is not in my dictionary.")
        return

    correct_word = game["word"]
    guesses = game.get("guesses", [])
    max_guesses = game.get("max_guesses", 20)

    if text in guesses:
        await update.message.reply_text("You've already guessed that word.")
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
    elif len(guesses) >= max_guesses:
        await update.message.reply_text(f"Game over! The correct word was `{correct_word}`. Use /new to start again.")
        games_col.delete_one({"chat_id": chat_id})

# --- /leaderboard Command ---
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    is_group = update.effective_chat.type in ["group", "supergroup"]
    keyboard = [
        [
            InlineKeyboardButton("📅 Today", callback_data=f"lb_today_{chat_id}"),
            InlineKeyboardButton("🏆 Overall", callback_data=f"lb_overall_{chat_id}"),
            InlineKeyboardButton("🌍 Global", callback_data="lb_global")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if is_group:
        await show_leaderboard(update, context, mode="overall", chat_id=chat_id, show_back=False)
    else:
        await show_leaderboard(update, context, mode="today", chat_id=chat_id, show_back=False)

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
            {"$group": {"_id": "$user_id", "score": {"$max": "$score"}, "name": {"$first": "$name"}}},
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

    # Styled leaderboard message with quote block
    msg = f"**{title}**\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for idx, row in enumerate(results, 1):
        medal = medals[idx-1] if idx <= 3 else f"{idx}."
        name = row.get("name", "Player")
        user_id = row["_id"]
        score = row["score"]
        msg += f"➤ `{medal}` [{name}](tg://user?id={user_id}) — *{score}* pts\n"

    keyboard = [
        [
            InlineKeyboardButton("📅 Today", callback_data=f"lb_today_{query.message.chat.id}"),
            InlineKeyboardButton("🏆 Overall", callback_data=f"lb_overall_{query.message.chat.id}"),
            InlineKeyboardButton("🌍 Global", callback_data="lb_global")
        ]
    ]

    await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


async def show_leaderboard(update_or_query, context, mode, chat_id, show_back=True):
    query = getattr(update_or_query, "callback_query", None)
    since = datetime.utcnow() - timedelta(days=1)

    if mode == "today":
        pipeline = [
            {"$match": {"chat_id": chat_id, "updated": {"$gte": since}}},
            {"$group": {"_id": "$user_id", "score": {"$max": "$score"}, "name": {"$first": "$name"}}},
            {"$sort": {"score": -1}},
            {"$limit": 10}
        ]
        results = list(scores_col.aggregate(pipeline))
        title = "📅 Today's Leaderboard"

    elif mode == "overall":
        results = list(scores_col.find({"chat_id": chat_id}).sort("score", -1).limit(10))
        title = "🏆 Overall Leaderboard"

    elif mode == "global":
        results = list(scores_col.find({"chat_id": "global"}).sort("score", -1).limit(10))
        title = "🌍 Global Leaderboard"

    else:
        return

    if not results:
        if query:
            await query.edit_message_text("No scores found.")
        else:
            await update_or_query.message.reply_text("No scores found.")
        return

    # Styled leaderboard message with quote block
    msg = f"**{title}**\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for idx, row in enumerate(results, 1):
        medal = medals[idx-1] if idx <= 3 else f"{idx}."
        name = row.get("name", "Player")
        user_id = row["_id"]
        score = row["score"]
        msg += f"➤ `{medal}` [{name}](tg://user?id={user_id}) — *{score}* pts\n"

    keyboard = []
    if show_back and query:
        back_btn = InlineKeyboardButton("🔙 Back", callback_data=f"lb_back_{chat_id}")
        keyboard.append([back_btn])

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    if query:
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update_or_query.message.reply_text(msg, parse_mode="Markdown", reply_markup=reply_markup)

# --- Main ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", send_welcome))
    app.add_handler(CommandHandler("new", new_game))
    app.add_handler(CommandHandler("stop", stop_game))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CallbackQueryHandler(leaderboard_callback, pattern=r"^lb_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_guess))
    app.add_handler(ChatMemberHandler(log_bot_added, ChatMemberHandler.MY_CHAT_MEMBER))

    print("Bot is running...")
    app.run_polling()
