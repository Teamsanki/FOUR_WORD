from pyrogram import Client, filters
from pyrogram.types import ChatMemberUpdated
from pymongo import MongoClient
from datetime import datetime
import asyncio
import random

API_ID = 24740695  # Apni API ID yaha daalo
API_HASH = "a95990848f2b93b8131a4a7491d97092"  # Apna API Hash yaha daalo
STRING_SESSION = "BQF5g1cALeMyxZWYBkA6oOnJrUO1ObNWOyWJ7r4NU_LCjD9Drh4uXOUaAc5nVT0-rH-wYsL0j6e6LojtFfxI4ZxdmyBdy_gMZ2iVAJtocFt2R04GK7YRHB1hKKHUVCL1c4y_pCIA1ot4OMKsMyISrw4UgpJBZzbPcNv2IGIlimmmD_7IwRln2TwUuR_sEKRF0MJATiLVhJosCJcnMa5JW2CE65PKYoIaehxsaj_c18qaUkR7Fa9ZzPkQ09pk7lNlK2sfEYCxS7gWRIE4Wbo-EdtEfpjoVljV4z2-fMDM0a8KzQBjp5hpT2wLxuExK1-GLpK5Akm0NFrq1P2P-f5nsE_vrvk30AAAAAHXmBLDAA"  # Yaha apna session paste karo
MONGO_URL = "mongodb+srv://tsgcoder:tsgcoder@cluster0.1sodg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"  # Yaha MongoDB URL paste karo

app = Client("userbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING_SESSION)
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["TelegramChatDB"]
collection = db["Messages"]

# Commands ke liye messages
messages = {
    "morning": "**🌞 Good Morning Everyone! 🌞**",
    "afternoon": "**🌞 Good Afternoon Everyone! 🌞**",
    "evening": "**🌆 Good Evening Everyone! 🌆**",
    "night": "**🌙 Good Night Everyone! 🌙**"
}

@app.on_message(filters.command(["morning", "afternoon", "evening", "night"]) & filters.me)
async def send_greeting(client, message):
    command = message.text.lstrip("/")
    if command in messages:
        chat_id = message.chat.id
        async for member in app.get_chat_members(chat_id):
            if not member.user.is_bot:
                await asyncio.sleep(0.2)
                try:
                    await app.send_message(
                        chat_id, 
                        f"{messages[command]}\n[{member.user.first_name}](tg://user?id={member.user.id})", 
                        parse_mode="markdown2"
                    )
                except Exception as e:
                    print(f"Error sending message: {e}")

# Festivals Messages
festival_messages = {
    "01-01": "**🎉 Happy New Year! 🎉**",
    "26-01": "**🇮🇳 Happy Republic Day! 🇮🇳**",
    "15-08": "**🇮🇳 Happy Independence Day! 🇮🇳**",
    "02-10": "**🕊️ Happy Gandhi Jayanti! 🕊️**",
    "14-01": "**🌾 Makar Sankranti! 🪁**",
    "26-01": "**🔥 Happy Lohri! 🔥**",
    "29-03": "**🎨 Happy Holi! 🌈**",
    "14-04": "**🎉 Happy Baisakhi! 🌾**",
    "09-04": "**🙏 Ram Navami! 🏹**",
    "07-09": "**🚩 Ganesh Chaturthi! 🐘**",
    "04-11": "**🪔 Happy Diwali! 🎇**",
    "09-04": "**🌙 Ramadan Mubarak! 🌙**",
    "12-04": "**🕌 Eid-ul-Fitr Mubarak! 🌙**",
    "18-06": "**🕋 Eid-ul-Adha Mubarak! 🌙**"
}

@app.on_message(filters.me)
async def check_festival(client, message):
    today = datetime.now().strftime("%d-%m")
    if today in festival_messages:
        chat_id = message.chat.id
        try:
            await app.send_message(chat_id, festival_messages[today], parse_mode="markdown2")
        except Exception as e:
            print(f"Error sending festival message: {e}")

# Special Birthday Message for 8th June
@app.on_message(filters.me)
async def birthday_announcement(client, message):
    today = datetime.now().strftime("%d-%m")
    if today == "08-06":
        chat_id = message.chat.id
        birthday_message = "**🎂🎉 Happy Birthday to Our Special One! 🎉🎂**\n@your_username"
        try:
            sent_message = await app.send_message(chat_id, birthday_message, parse_mode="markdown2")
            await app.pin_chat_message(chat_id, sent_message.message_id, disable_notification=False)
        except Exception as e:
            print(f"Error in birthday announcement: {e}")

# Auto Welcome Message for New Members
@app.on_chat_member_updated()
async def welcome(client: Client, update: ChatMemberUpdated):
    if update.new_chat_member:
        user = update.new_chat_member.user
        chat_id = update.chat.id
        welcome_message = f"**✨ Welcome, [{user.first_name}](tg://user?id={user.id})! ✨**"
        try:
            await client.send_message(chat_id, welcome_message, parse_mode="markdown2")
        except Exception as e:
            print(f"Error sending welcome message: {e}")

# **Message Store in MongoDB**
@app.on_message(filters.group & ~filters.bot)
async def store_message(client, message):
    if message.reply_to_message or message.entities:
        return  # Agar reply ya tag hai to ignore kare

    chat_id = message.chat.id
    user_id = message.from_user.id
    text = message.text

    if text:
        collection.insert_one({"chat_id": chat_id, "user_id": user_id, "text": text})

# **Koi bhi bina tag/reply ke message likhe to DB se random reply bheje**
@app.on_message(filters.group & filters.text & ~filters.bot)
async def auto_reply(client, message):
    if message.reply_to_message or message.entities:
        return  # Agar reply ya tag hai to ignore kare

    chat_id = message.chat.id
    stored_messages = list(collection.find({"chat_id": chat_id}, {"text": 1, "_id": 0}))

    if stored_messages:
        random_msg = random.choice(stored_messages)["text"]
        try:
            await message.reply_text(f"**{random_msg}**", parse_mode="markdown2")
        except Exception as e:
            print(f"Error sending random reply: {e}")
    else:
        try:
            await message.reply_text("**Kya haal hain bhai log? 😊**", parse_mode="markdown2")
        except Exception as e:
            print(f"Error sending default reply: {e}")

app.run()
