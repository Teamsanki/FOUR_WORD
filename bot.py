# All imports come FIRST
import os
import random
import json
import requests
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

# Load .env variables (for local development)
load_dotenv()

# --- Bot Config (using environment variables) ---
TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")
WELCOME_IMAGE_URL = os.getenv("WELCOME_IMAGE_URL")
LOGGER_GROUP_ID = int(os.getenv("LOGGER_GROUP_ID"))  # Convert to int if using numeric IDs

# --- MongoDB Setup ---
client = MongoClient(MONGO_URL)
db = client["wordseekbot"]
games_col = db["games"]
scores_col = db["scores"]
daily_col = db["daily_word"]
stats_col = db["user_stats"]

# ---------- 🚀 DYNAMIC WORD LOADER (GitHub dwyl/english-words) ----------
def load_dynamic_words():
    cache_file = "four_letter_words.json"
    # Agar cache file pehle se hai to load karo
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            words = json.load(f)
            print(f"Loaded {len(words)} 4-letter words from cache.")
            return words
    
    # Nahi hai to internet se download karo
    url = "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"
    try:
        print("Downloading word list from GitHub... (only once)")
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        all_words = response.text.splitlines()
        # Sirf 4-letter words filter karo (lowercase)
        four_letter = list({w.lower() for w in all_words if len(w) == 4 and w.isalpha()})
        # Cache me save karo
        with open(cache_file, "w") as f:
            json.dump(four_letter, f)
        print(f"Loaded {len(four_letter)} unique 4-letter words from internet.")
        return four_letter
    except Exception as e:
        print(f"Error loading dynamic words: {e}")
        # Fallback: static list (jo neeche di gayi hai)
        print("Falling back to static word list...")
        return None

# ---------- STATIC WORD LIST (Fallback + original words) ----------
# Purani WORDS list (jo aapne di thi) – ise fallback ke taur par rakhte hain
STATIC_WORDS = [
    'able', 'acid', 'aged', 'also', 'area', 'army', 'atom', 'aunt', 'away', 'axis', 'amit', 'dick', 'slap', 'crow',
    'baby', 'back', 'bake', 'ball', 'band', 'bank', 'barn', 'base', 'bath', 'bear',
    'beat', 'been', 'bell', 'belt', 'bend', 'best', 'bike', 'bill', 'bird', 'bite',
    'blue', 'boat', 'body', 'bomb', 'bond', 'bone', 'book', 'boom', 'boot', 'bore',
    'born', 'boss', 'both', 'bowl', 'brag', 'bray', 'bred', 'brew', 'brim', 'buck',
    'buff', 'bulk', 'bull', 'bump', 'burn', 'bush', 'busy', 'buzz', 'byte',
    'cage', 'cake', 'call', 'calm', 'camp', 'card', 'care', 'cart', 'case', 'cash',
    'cast', 'cave', 'cell', 'chat', 'chip', 'city', 'clay', 'club', 'coal', 'coat',
    'cold', 'come', 'cook', 'cool', 'cope', 'cord', 'core', 'cost', 'crew', 'crop',
    'curl', 'cute', 'chill',
    'dark', 'data', 'date', 'dawn', 'deal', 'debt', 'deep', 'deer', 'desk', 'dial',
    'dice', 'died', 'diet', 'dime', 'dine', 'dish', 'disk', 'dive', 'dock', 'does',
    'doge', 'dome', 'done', 'doom', 'door', 'dose', 'down', 'drag', 'draw', 'drop',
    'drum', 'dual', 'duck', 'duke', 'dull', 'dust', 'duty',
    'each', 'earn', 'ease', 'east', 'easy', 'edge', 'edit', 'else', 'envy', 'epic',
    'even', 'ever', 'evil', 'exam', 'exit', 'eyes',
    'face', 'fact', 'fade', 'fail', 'fair', 'fake', 'fall', 'fame', 'farm', 'fast',
    'fate', 'fear', 'feed', 'feel', 'feet', 'fell', 'felt', 'file', 'fill', 'film',
    'find', 'fine', 'fire', 'firm', 'fish', 'fist', 'five', 'flag', 'flat', 'flip',
    'flow', 'fold', 'folk', 'food', 'foot', 'form', 'fort', 'four', 'free', 'frog',
    'fuel', 'full', 'fund', 'fuse',
    'gain', 'game', 'gang', 'gate', 'gave', 'gear', 'gene', 'gift', 'girl', 'give',
    'glad', 'goal', 'goat', 'gold', 'golf', 'gone', 'good', 'grab', 'gray', 'grew',
    'grid', 'grim', 'grip', 'grow', 'gulf', 'guts',
    'hair', 'half', 'hall', 'hand', 'hang', 'hard', 'harm', 'hate', 'have', 'hawk',
    'head', 'heal', 'heap', 'hear', 'heat', 'held', 'hell', 'help', 'herb', 'hero',
    'hide', 'high', 'hill', 'hire', 'hold', 'hole', 'holy', 'home', 'hope', 'horn',
    'host', 'hour', 'huge', 'hung', 'hunt', 'hurt',
    'idea', 'idle', 'inch', 'into', 'iron', 'item',
    'jack', 'jade', 'jail', 'jazz', 'jeep', 'jest', 'join', 'joke', 'jump', 'jury',
    'keep', 'kept', 'kick', 'kill', 'kind', 'king', 'kiss', 'kite', 'knee', 'knew',
    'knit', 'know',
    'lack', 'lady', 'lake', 'lamp', 'land', 'lane', 'last', 'late', 'lava', 'lazy',
    'lead', 'leaf', 'left', 'lend', 'less', 'life', 'lift', 'like', 'limb', 'line',
    'link', 'lion', 'list', 'live', 'load', 'loan', 'lock', 'logo', 'long', 'look',
    'loop', 'lord', 'lose', 'loss', 'lost', 'love', 'luck', 'lung',
    'made', 'mail', 'main', 'make', 'male', 'mall', 'many', 'mark', 'mask', 'mass',
    'mate', 'meal', 'mean', 'meat', 'meet', 'melt', 'menu', 'mere', 'mice', 'mild',
    'mile', 'milk', 'mill', 'mind', 'mine', 'mint', 'miss', 'mist', 'mode', 'mood',
    'moon', 'more', 'most', 'move', 'much', 'must', 'myth',
    'name', 'navy', 'near', 'neck', 'need', 'nest', 'news', 'next', 'nice', 'nick',
    'nine', 'node', 'none', 'noon', 'nose', 'note', 'noun', 'nuts',
    'oath', 'obey', 'omit', 'once', 'only', 'onto', 'open', 'oral', 'ours', 'oval',
    'oven', 'over', 'owed', 'own',
    'pack', 'page', 'paid', 'pain', 'pair', 'palm', 'park', 'part', 'pass', 'past',
    'path', 'peak', 'pear', 'peel', 'peer', 'peny', 'pick', 'pile', 'pill', 'pine',
    'pink', 'pipe', 'plan', 'play', 'plot', 'plug', 'plus', 'poem', 'pole', 'poll',
    'pond', 'pool', 'poor', 'port', 'post', 'pull', 'pure', 'push', 'pins',
    'quad', 'quiz', 'quit', 'quip',
    'race', 'rack', 'rage', 'raid', 'rail', 'rain', 'rank', 'rate', 'rays', 'read',
    'real', 'rear', 'redo', 'reed', 'reef', 'rest', 'rice', 'rich', 'ride', 'ring',
    'riot', 'rise', 'risk', 'road', 'rock', 'role', 'roof', 'room', 'root', 'rope',
    'rose', 'rule', 'rush', 'rust',
    'safe', 'said', 'sail', 'salt', 'same', 'sand', 'save', 'scan', 'scar', 'seal',
    'seat', 'seed', 'seek', 'seem', 'seen', 'self', 'sell', 'send', 'ship', 'shop',
    'shot', 'show', 'shut', 'side', 'sign', 'silk', 'sink', 'site', 'size', 'slip',
    'slow', 'snap', 'snow', 'soap', 'soft', 'soil', 'sold', 'sole', 'some', 'song',
    'soon', 'sort', 'soul', 'spot', 'star', 'stay', 'step', 'stop', 'such', 'suit', 'smag',
    'sure', 'swim', 'sync',
    'tail', 'take', 'tale', 'talk', 'tall', 'tank', 'tape', 'task', 'team', 'tear',
    'tech', 'tell', 'tend', 'tent', 'term', 'test', 'text', 'than', 'that', 'them',
    'then', 'they', 'thin', 'this', 'thus', 'time', 'tire', 'told', 'toll', 'tone',
    'tool', 'tops', 'torn', 'tour', 'town', 'trap', 'tree', 'trip', 'true', 'tube',
    'tune', 'turn', 'twin', 'type',
    'ugly', 'unit', 'urge', 'used', 'user', 'upon',
    'vain', 'vast', 'veil', 'verb', 'very', 'vest', 'view', 'vine', 'visa', 'vote',
    'wage', 'wait', 'wake', 'walk', 'wall', 'want', 'ward', 'warm', 'warn', 'wash',
    'wave', 'weak', 'wear', 'weed', 'week', 'well', 'west', 'what', 'when', 'whip',
    'wide', 'wife', 'wild', 'will', 'wind', 'wine', 'wing', 'wink', 'wipe', 'wire',
    'wise', 'wish', 'wolf', 'wood', 'word', 'worn', 'wrap', 'work',
    'xray',
    'yard', 'yarn', 'yawn', 'yeah', 'year', 'yell', 'your', 'yoga',
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

# Load dynamic words, fallback to static if fails
dynamic_words = load_dynamic_words()
if dynamic_words:
    WORDS = dynamic_words
else:
    WORDS = STATIC_WORDS
    print(f"Using static fallback with {len(WORDS)} words.")

# ---------- HELPER FUNCTIONS ----------
def format_feedback(guess: str, correct_word: str) -> str:
    """Return colored emoji feedback for a guess."""
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
    """Build a text summary of all guesses."""
    summary = ""
    for guess in guesses:
        feedback = format_feedback(guess, correct_word)
        summary += f"{feedback} `{guess}`\n"
    summary += f"\n_\"{hint}\"_"
    return summary

def get_random_clue(word: str, guessed_letters: set = None) -> str:
    """Return a random clue about the word (unique feature)."""
    if guessed_letters is None:
        guessed_letters = set()
    clues = []
    # Clues about letters
    vowels = set('aeiou')
    vowel_count = sum(1 for ch in word if ch in vowels)
    if vowel_count == 1:
        clues.append(f"🔊 The word has exactly one vowel.")
    elif vowel_count == 2:
        clues.append(f"🔊 The word has two vowels.")
    elif vowel_count == 3:
        clues.append(f"🔊 The word has three vowels.")
    # First letter clue
    if word[0] not in guessed_letters:
        clues.append(f"🔤 The word starts with **{word[0].upper()}**.")
    # Last letter clue
    if word[-1] not in guessed_letters:
        clues.append(f"🔚 The word ends with **{word[-1].upper()}**.")
    # Contains a specific common letter
    common = 'eastnro'
    for ch in common:
        if ch in word and ch not in guessed_letters:
            clues.append(f"📌 The word contains the letter **{ch.upper()}**.")
            break
    # If no clue generated, give a generic one
    if not clues:
        clues.append("💡 The word is a common English 4‑letter word.")
    return random.choice(clues)

async def update_user_stats(user_id: int, name: str, won: bool, daily: bool = False):
    """Update user statistics (games, wins, streaks, coins)."""
    stats = stats_col.find_one({"user_id": user_id})
    if not stats:
        stats = {
            "user_id": user_id,
            "name": name,
            "total_games": 0,
            "total_wins": 0,
            "current_streak": 0,
            "best_streak": 0,
            "total_coins": 0,
            "last_daily": None
        }
    # Increment total games
    stats["total_games"] += 1
    if won:
        stats["total_wins"] += 1
        # Add coins for winning (10 for classic, 20 for daily)
        coin_reward = 20 if daily else 10
        stats["total_coins"] += coin_reward
        # Streak handling only for daily challenge
        if daily:
            today = datetime.utcnow().date()
            last = stats.get("last_daily")
            if last == today - timedelta(days=1):
                stats["current_streak"] += 1
            else:
                stats["current_streak"] = 1
            stats["last_daily"] = today
            if stats["current_streak"] > stats["best_streak"]:
                stats["best_streak"] = stats["current_streak"]
        # Update name
        stats["name"] = name
    stats_col.update_one({"user_id": user_id}, {"$set": stats}, upsert=True)
    return stats

# ---------- BOT COMMANDS ----------
async def send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("➕ Add Me In Your Group ➕", url="https://t.me/TSFOURWORDBOT?startgroup=true")],
        [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/ll_SANKI_II"),
         InlineKeyboardButton("📢 Support Channel", url="https://t.me/TEAMSANKI")],
        [InlineKeyboardButton("👻 Four Word Group", url="https://t.me/Fourwordgusser")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    caption = (
        "✨ 𝙒𝙚𝙡𝙘𝙤𝙢𝙚 𝙏𝙤 *𝙁𝙤𝙪𝙧 𝙒𝙤𝙧𝙙* ✨\n\n"
        "🔤 Guess the hidden 4‑letter word!\n"
        "🎯 Get instant color‑coded feedback.\n"
        "🏆 Compete on leaderboards (Today / Overall / Global)\n"
        "🎁 Earn coins, use /hint for help\n"
        "📅 Play the Daily Challenge for extra rewards!\n\n"
        "💥 Use /new to start a classic game\n"
        "🌟 Use /daily for today's challenge\n"
        "💰 Use /stats to see your progress\n"
        "👑 Owner: @ll_SANKI_II\n"
        "📢 Support: @TEAMSANKI"
    )
    await context.bot.send_photo(chat_id=chat.id, photo=WELCOME_IMAGE_URL, caption=caption, parse_mode="Markdown", reply_markup=markup)
    # Logging
    if user:
        log_msg = f"✨ <b>ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ</b> ✨\n\n<b>ᴜsᴇʀ ɪᴅ:</b> <code>{user.id}</code>\n<b>ᴜsᴇʀɴᴀᴍᴇ:</b> {user.mention_html()}"
        await context.bot.send_message(chat_id=LOGGER_GROUP_ID, text=log_msg, parse_mode="HTML")

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
            "📝 <b>𝐖𝐨𝐫𝐝𝐒𝐞𝐞𝐤 𝐁𝐨𝐭 𝐀𝐝𝐝𝐞𝐝 𝐈𝐧 𝐍𝐞𝐰 𝐆𝐫𝐨𝐮𝐩</b>\n\n"
            f"📌 <b>𝐂𝐡𝐚𝐭 𝐍𝐚𝐦𝐞:</b> {chat.title}\n"
            f"🍂 <b>𝐂𝐡𝐚𝐭 𝐈𝐝:</b> <code>{chat.id}</code>\n"
            f"🔐 <b>𝐂𝐡𝐚𝐭 𝐔𝐬𝐞𝐫𝐧𝐚𝐦𝐞:</b> {chat_username}\n"
            f"🛰 <b>𝐂𝐡𝐚𝐭 𝐋𝐢𝐧𝐤:</b> {chat_link}\n"
            f"📈 <b>𝐆𝐫𝐨𝐮𝐩 𝐌𝐞𝐦𝐛𝐞𝐫𝐬:</b> {members}\n"
            f"🤔 <b>𝐀𝐝𝐝𝐞𝐝 𝐁𝐲:</b> {user.mention_html()}"
        )
        await context.bot.send_message(chat_id=LOGGER_GROUP_ID, text=msg, parse_mode="HTML")

async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE, mode="classic"):
    """Start a new game (classic or daily)."""
    chat_id = update.effective_chat.id
    if mode == "daily":
        # Get or create today's daily word
        today = datetime.utcnow().date()
        daily = daily_col.find_one({"date": today.isoformat()})
        if not daily:
            word = random.choice(WORDS)
            daily_col.insert_one({"date": today.isoformat(), "word": word, "hint": f"Starts with '{word[0]}'"})
        else:
            word = daily["word"]
        hint = f"Starts with '{word[0]}'"
        max_guesses = 6  # Daily challenge is harder
    else:
        word = random.choice(WORDS)
        hint = f"Starts with '{word[0]}'"
        max_guesses = 20

    games_col.update_one(
        {"chat_id": chat_id},
        {"$set": {
            "word": word,
            "hint": hint,
            "guesses": [],
            "start_time": datetime.utcnow(),
            "max_guesses": max_guesses,
            "mode": mode
        }},
        upsert=True
    )
    msg = f"🆕 *New {mode.capitalize()} Game Started!* Guess the 4‑letter word.\nYou have {max_guesses} guesses."
    await update.message.reply_text(msg, parse_mode="Markdown")

async def stop_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    games_col.delete_one({"chat_id": chat_id})
    await update.message.reply_text("Game stopped. Use /new or /daily to start a new one.")

async def handle_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game = games_col.find_one({"chat_id": chat_id})
    if not game:
        return
    user = update.effective_user
    text = update.message.text.lower()
    if not text.isalpha() or len(text) != 4:
        await update.message.reply_text("Please enter a valid 4‑letter word.")
        return
    if text not in WORDS:
        await update.message.reply_text("This word is not in my dictionary.")
        return
    correct_word = game["word"]
    guesses = game.get("guesses", [])
    max_guesses = game.get("max_guesses", 20)
    mode = game.get("mode", "classic")
    if text in guesses:
        await update.message.reply_text("You've already guessed that word.")
        return
    guesses.append(text)
    games_col.update_one({"chat_id": chat_id}, {"$set": {"guesses": guesses}})
    feedback = format_feedback(text, correct_word)
    await update.message.reply_text(f"{feedback} `{text}`", parse_mode="Markdown")
    # Give a clue after every wrong guess (unique feature)
    if text != correct_word:
        clue = get_random_clue(correct_word, set(guesses))
        await update.message.reply_text(f"💡 *Clue:* {clue}", parse_mode="Markdown")
    # Check win condition
    if text == correct_word:
        now = datetime.utcnow()
        is_daily = (mode == "daily")
        # --- ADD REACTION TO USER'S CORRECT GUESS MESSAGE ---
        try:
            await update.message.react(emoji="🎉")  # Party firework reaction
        except Exception as e:
            print(f"Reaction failed: {e}")  # Fallback if reaction not supported
        # Update scores (points)
        points_earned = 20 if is_daily else 12
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
        # Update user stats (coins, streaks)
        stats = await update_user_stats(user.id, user.first_name, won=True, daily=is_daily)
        # Build detailed win message
        attempts = len(guesses)
        coin_reward = 20 if is_daily else 10
        win_msg = (
            f"🎉 *{user.first_name} GUESSED IT RIGHT!* 🎉\n\n"
            f"🔑 *Correct word:* `{correct_word.upper()}`\n"
            f"📊 *Attempts:* {attempts} / {max_guesses}\n"
            f"⭐ *Points earned:* +{points_earned}\n"
            f"💰 *Coins earned:* +{coin_reward}\n"
            f"📈 *Total coins now:* {stats.get('total_coins', 0)}\n\n"
            f"📝 *Game summary:*\n"
        )
        summary = build_summary(guesses, correct_word, game.get("hint", ""))
        await update.message.reply_text(win_msg + summary, parse_mode="Markdown")
        # Share result button
        share_keyboard = [[InlineKeyboardButton("📤 Share Result", switch_inline_query=f"Just solved the word! {correct_word.upper()} in {attempts} attempts!")]]
        await update.message.reply_text("✨ Great job! Share your victory with friends.", reply_markup=InlineKeyboardMarkup(share_keyboard))
        games_col.delete_one({"chat_id": chat_id})
    elif len(guesses) >= max_guesses:
        await update.message.reply_text(f"Game over! The correct word was `{correct_word}`. Use /new or /daily to start again.", parse_mode="Markdown")
        games_col.delete_one({"chat_id": chat_id})
        # Still update stats as loss
        await update_user_stats(user.id, user.first_name, won=False, daily=(mode=="daily"))

async def hint_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reveal one random missing letter, costs 5 coins."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    game = games_col.find_one({"chat_id": chat_id})
    if not game:
        await update.message.reply_text("No active game. Start one with /new or /daily.")
        return
    # Check user coins
    stats = stats_col.find_one({"user_id": user.id})
    if not stats or stats.get("total_coins", 0) < 5:
        await update.message.reply_text("❌ You need 5 coins to use a hint! Win games to earn coins.")
        return
    correct = game["word"]
    guesses = game.get("guesses", [])
    # Find a letter not yet correctly placed and not fully guessed
    unrevealed_positions = [i for i, ch in enumerate(correct) if ch not in [g[i] for g in guesses] if len(guesses) > 0 else True]
    if not unrevealed_positions:
        await update.message.reply_text("No new hint available! Keep guessing.")
        return
    pos = random.choice(unrevealed_positions)
    letter = correct[pos]
    # Deduct coins
    stats_col.update_one({"user_id": user.id}, {"$inc": {"total_coins": -5}})
    await update.message.reply_text(f"🔍 *Hint:* The letter at position {pos+1} is `{letter.upper()}`.", parse_mode="Markdown")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    stats = stats_col.find_one({"user_id": user.id})
    if not stats:
        await update.message.reply_text("No stats yet. Play some games to see your progress!")
        return
    msg = (
        f"📊 *Stats for {user.first_name}*\n\n"
        f"🎮 Total Games: {stats.get('total_games', 0)}\n"
        f"🏆 Total Wins: {stats.get('total_wins', 0)}\n"
        f"🔥 Current Streak: {stats.get('current_streak', 0)} days\n"
        f"🌟 Best Streak: {stats.get('best_streak', 0)} days\n"
        f"💰 Coins: {stats.get('total_coins', 0)}\n\n"
        f"Use /hint (costs 5 coins) to reveal a letter!"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    is_group = update.effective_chat.type in ["group", "supergroup"]
    keyboard = [
        [InlineKeyboardButton("📅 Today", callback_data=f"lb_today_{chat_id}"),
         InlineKeyboardButton("🏆 Overall", callback_data=f"lb_overall_{chat_id}"),
         InlineKeyboardButton("🌍 Global", callback_data="lb_global")]
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
    msg = f"**{title}**\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for idx, row in enumerate(results, 1):
        medal = medals[idx-1] if idx <= 3 else f"{idx}."
        name = row.get("name", "Player")
        user_id = row["_id"]
        score = row["score"]
        msg += f"➤ `{medal}` [{name}](tg://user?id={user_id}) — *{score}* pts\n"
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data=f"lb_back_{query.message.chat.id}")]]
    await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the daily challenge."""
    await new_game(update, context, mode="daily")

# ---------- MAIN ----------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", send_welcome))
    app.add_handler(CommandHandler("new", new_game))
    app.add_handler(CommandHandler("daily", daily_command))
    app.add_handler(CommandHandler("stop", stop_game))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("hint", hint_command))
    app.add_handler(CallbackQueryHandler(leaderboard_callback, pattern=r"^lb_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_guess))
    app.add_handler(ChatMemberHandler(log_bot_added, ChatMemberHandler.MY_CHAT_MEMBER))
    print("Bot is running with dynamic word list + win reaction + detailed win message...")
    app.run_polling()
