import pyrogram
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import firebase_admin
from firebase_admin import credentials, db
import asyncio
import random

# Telegram Bot Configuration
API_ID = "27763335"  # Replace with your Telegram API ID
API_HASH = "339bc57607286baa0d68a97a692329f0"  # Replace with your Telegram API Hash
BOT_TOKEN = "7716244648:AAFDA0GMYOMIbZNOM4afWVgeK0WrLs4n3j8"  # Replace with your Bot Token
LOGGER_GROUP = -1002100433415  # Replace with your Logger Group ID

# Firebase Setup
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://social-bite-skofficial-default-rtdb.firebaseio.com/"  # Replace with your Firebase DB URL
})

# Initialize Bot
app = Client("SuhaniBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Photo (Replace this with your welcome photo URL or local path)
WELCOME_PHOTO = "https://example.com/welcome-photo.jpg"  # Replace with the actual photo link

# Stylish Welcome Message (5 Lines)
WELCOME_MESSAGE = """
🌟 **Suhani Bot** 🌟

👤 **Welcome, {user_mention}**

🚀 Powered by Team SANKI Network  
💻 Innovated by the Best Minds  
✨ Experience Beyond Imagination  
"""

# Inline Buttons
WELCOME_BUTTONS = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("👑 Owner", url="https://t.me/TSGCODER"),  # Replace with Owner link
         InlineKeyboardButton("🛠 Support Channel", url="https://t.me/Teamsankinetworkk")]  # Replace with Support link
    ]
)

# Start Command
@app.on_message(filters.command("start") & filters.private)
async def start(bot, message: Message):
    user_mention = message.from_user.mention(style="md")

    # Animation Texts
    animation_texts = [
        "👋 **Initializing Suhani Bot...**",
        "🚀 **Loading Systems...**",
        "🔧 **Connecting to Team SANKI's Network...**",
        "💖 **Almost Ready...**",
    ]
    for anim_text in animation_texts:
        await message.reply(anim_text)
        await asyncio.sleep(1.5)

    # Final Welcome Photo with Caption and Inline Buttons
    await message.reply_photo(
        photo=WELCOME_PHOTO,
        caption=WELCOME_MESSAGE.format(user_mention=user_mention),
        reply_markup=WELCOME_BUTTONS
    )

    # Log to Logger Group
    log_message = f"🟢 **New Start Alert** 🟢\n\n👤 **User:** [{message.from_user.first_name}](tg://user?id={message.from_user.id})\n🆔 **User ID:** `{message.from_user.id}`"
    await bot.send_message(LOGGER_GROUP, log_message)

# Save Messages to Firebase
@app.on_message(filters.group & ~filters.bot)
async def save_group_messages(bot, message: Message):
    group_id = str(message.chat.id)
    user_name = message.from_user.first_name
    user_id = str(message.from_user.id)
    text = message.text or "Non-text message"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    ref = db.reference(f"SANKI/{group_id}")
    message_data = {
        "user_name": user_name,
        "user_id": user_id,
        "text": text,
        "timestamp": timestamp
    }
    ref.push(message_data)

# Typing Status and Random Response
@app.on_message(filters.group & ~filters.bot)
async def reply_random(bot, message: Message):
    group_id = str(message.chat.id)
    ref = db.reference(f"SANKI/{group_id}")
    messages = ref.get()

    # Show Typing Status
    await bot.send_chat_action(message.chat.id, "typing")
    await asyncio.sleep(1.5)  # Simulate typing time

    # Respond Randomly from Firebase
    if messages:
        random_message = random.choice(list(messages.values()))["text"]
        await message.reply(f"🤖: {random_message}")
    else:
        await message.reply("🤖: Sorry, no messages available to reply right now!")

# Run the Bot
print("Suhani Bot Started! 🚀")
app.run()
