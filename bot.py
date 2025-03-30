import random
import re
import pymongo
import datetime
import asyncio
from collections import Counter
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import (
    API_ID, API_HASH, BOT_TOKEN, MONGO_URL, DEVELOPER_USERNAME, GROUP_LINK, 
    WELCOME_GIF, SANKI_LINK, FUNNY_REPLIES, ABUSE_WORDS, GROUP_CHAT_ID
)

bot = Client("IndianChatBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ✅ MongoDB Connection
mongo = pymongo.MongoClient(MONGO_URL)
db = mongo["IndianChatBot"]
group_collection = db["groups"]

# ✅ Start Command
@bot.on_message(filters.command("start"))
async def start(_, message):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Developer", url=f"https://t.me/{DEVELOPER_USERNAME[1:]}")],
        [InlineKeyboardButton("💬 Group", url=GROUP_LINK)],
        [InlineKeyboardButton("📜 Help", callback_data="help")]
    ])
    
    await message.reply_video(WELCOME_GIF, caption="🤖 **Indian Chatting Club Bot**\nMain yahan aapki madad aur security ke liye hoon!", reply_markup=buttons)

# ✅ Help Section
@bot.on_callback_query(filters.regex("help"))
async def help_section(_, query):
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("/start", callback_data="cmd_start")],
        [InlineKeyboardButton("/connect", callback_data="cmd_connect")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
    ])
    await query.message.edit_text("📜 **Help Section**\nChoose a command to know more:", reply_markup=buttons)

# ✅ Individual Command Info
@bot.on_callback_query(filters.regex("^cmd_"))
async def command_info(_, query):
    cmd = query.data.split("_")[1]
    info = {
        "start": "Ye command bot ko start karti hai.",
        "connect": "Is command se aap apne group ko bot se connect kar sakte hain."
    }
    await query.message.edit_text(f"📌 **/{cmd} Command**\n{info.get(cmd, 'No info available.')}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="help")]]))

# ✅ Auto Ban on Abuse
@bot.on_message(filters.text & filters.group)
async def check_abuse(_, message):
    if any(word in message.text.lower() for word in ABUSE_WORDS):
        await message.reply(f"🚫 {message.from_user.mention} abuse words use mat karo!", quote=True)
        await bot.ban_chat_member(message.chat.id, message.from_user.id)

# ✅ Warn User for Bio Link
@bot.on_chat_member_updated
async def check_bio(_, update):
    user = update.new_chat_member
    if user and user.bio and ("http" in user.bio or "t.me" in user.bio):
        await bot.send_message(update.chat.id, f"⚠️ {user.user.mention}, apke bio me link hai. Isko hatao warna action liya jayega!")

# ✅ Detect DM Request
@bot.on_message(filters.text & filters.group)
async def check_dm_request(_, message):
    if re.search(r"\b(dm|msg)\b", message.text.lower()):
        await message.reply(f"⚠️ {message.from_user.mention}, bina permission DM mat karo!", quote=True)

# ✅ Welcome New User
@bot.on_chat_member_updated
async def welcome_user(_, update):
    if update.new_chat_member:
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("SANKI", url=SANKI_LINK)]])
        await bot.send_animation(update.chat.id, WELCOME_GIF, caption=f"👋 Welcome {update.new_chat_member.user.mention}!\nHope you enjoy our chat!", reply_markup=buttons)

# ✅ /connect Command (Owner Group Connect & Admin Notice)
@bot.on_message(filters.command("connect") & filters.private)
async def connect_group(_, message):
    user_id = message.from_user.id
    await message.reply("🔗 **Apne group me bot add karo aur uska link bhejo!**")

    @bot.on_message(filters.text & filters.private)
    async def get_group_link(_, link_msg):
        if "t.me" not in link_msg.text:
            return await link_msg.reply("❌ **Yeh valid group link nahi hai!**")

        group_link = link_msg.text
        await message.reply("✍️ **Ab ek message likho jo aapke group ke admins ko bhejna hai!**")

        @bot.on_message(filters.text & filters.private)
        async def get_admin_message(_, msg):
            admin_message = msg.text
            group_collection.insert_one({
                "group_link": group_link,
                "owner_id": user_id,
                "admin_msg": admin_message
            })

            await message.reply("✅ **Group link aur message save ho gaya!**\n🔹 Ab bot aapke group ke admins ko notice bhejega.")

            # ✅ Bot ko group me find karne ke liye
            async for chat in bot.get_dialogs():
                if chat.chat.type in ["supergroup", "group"] and chat.chat.invite_link and chat.chat.invite_link in group_link:
                    group_id = chat.chat.id
                    break
            else:
                return await message.reply("❌ **Bot aapke group me nahi mila! Pehle bot ko group me add karein.**")

            # ✅ Sabhi Admins ka list banane ke liye
            admins = []
            async for member in bot.get_chat_members(group_id, filter="administrators"):
                if not member.user.is_bot:
                    admins.append(member.user)

            if not admins:
                return await message.reply("❌ **Aapke group me koi real admin nahi mila!**")

            # ✅ Admins ko tag karne ka format
            admin_tags = " ".join([f"@{admin.username}" if admin.username else admin.mention for admin in admins])
            notice_text = f"📢 **Important Notice for Admins!**\n\n{admin_message}\n\n👑 **Owner:** {message.from_user.mention}\n\n{admin_tags}"

            # ✅ Group me notice send + pin karega
            sent_msg = await bot.send_message(group_id, notice_text)
            await bot.pin_chat_message(group_id, sent_msg.message_id)

            await message.reply("✅ **Notice successfully group me bhej diya aur pin bhi ho gaya!**")

# ✅ Tag All Users
@bot.on_message(filters.command("utag") & filters.group)
async def tag_all_users(_, message: Message):
    members = [member.user for member in bot.get_chat_members(message.chat.id) if not member.user.is_bot]
    if not members:
        return await message.reply("❌ Group me koi member nahi hai!")
    tag_text = "👥 **Tagging All Users:**\n" + " ".join([f"@{user.username}" if user.username else user.mention for user in members])
    await message.reply(tag_text)

# ✅ Tag All Admins
@bot.on_message(filters.command("atag") & filters.group)
async def tag_admins(_, message: Message):
    admins = [member.user for member in bot.get_chat_members(message.chat.id, filter="administrators") if not member.user.is_bot]
    if not admins:
        return await message.reply("❌ Group me koi admin nahi hai!")
    tag_text = "👮‍♂️ **Tagging All Admins:**\n" + " ".join([f"@{user.username}" if user.username else user.mention for user in admins])
    await message.reply(tag_text)

# ✅ Auto Good Morning/Night Messages
async def send_daily_message(chat_id, message_type):
    quotes = {
        "morning": "🌞 **Good Morning!**\nNaya din naye mauke lekar aata hai!",
        "night": "🌙 **Good Night!**\nAaj ka din jitna bhi tough tha, kal naya din naye umeed lekar aayega!"
    }
    await bot.send_message(chat_id, quotes[message_type])

async def schedule_daily_messages():
    while True:
        now = datetime.datetime.now().strftime("%H:%M")
        if now == "07:00":
            await send_daily_message(GROUP_CHAT_ID, "morning")
        elif now == "22:00":
            await send_daily_message(GROUP_CHAT_ID, "night")
        await asyncio.sleep(60)

# ✅ Track Best Message
best_message = {"user": None, "message": "", "likes": 0, "message_id": None}

@bot.on_message(filters.text & filters.group)
async def track_best_message(_, message):
    if message.reply_to_message and ("👍" in message.text or "❤️" in message.text):
        if message.reply_to_message.from_user.id == message.from_user.id:
            return
        msg_id = message.reply_to_message.message_id
        if best_message["message_id"] == msg_id:
            best_message["likes"] += 1
        else:
            best_message.update({"user": message.reply_to_message.from_user.mention, "message": message.reply_to_message.text, "likes": 1, "message_id": msg_id})

@bot.on_message(filters.command("bestmsg") & filters.group)
async def best_msg_command(_, message):
    if best_message["likes"] >= 5:
        await message.reply(f"🏆 **Best Message of the Day!**\n👤 {best_message['user']}\n📝 {best_message['message']}\n❤️ {best_message['likes']} Likes!")
    else:
        await message.reply("❌ Koi best message nahi mila ya 5 likes nahi mile!")

# ✅ Auto Reply
@bot.on_message(filters.text & filters.group)
async def auto_reply(_, message):
    if not message.reply_to_message:
        await message.reply(random.choice(FUNNY_REPLIES))

# ✅ Run Bot
bot.run()
