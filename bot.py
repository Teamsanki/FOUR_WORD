import random
import re
import pymongo
import datetime
import asyncio
import openai
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

# ✅ MongoDB Collection for Connected Groups
connected_groups = db["connected_groups"]

# ✅ /connect Command (Sirf "https://t.me/" Format Wale Links)
@bot.on_message(filters.command("connect") & filters.private)
async def connect_group(_, message):
    await message.reply("🔗 **Apne group ka link bhejo (Sirf 'https://t.me/' format me).**")

    @bot.on_message(filters.text & filters.private)
    async def get_group_link(_, link_msg):
        group_link = link_msg.text.strip()

        # ✅ Validate Link (Sirf "https://t.me/" Format Allow)
        if not group_link.startswith("https://t.me/"):
            return await link_msg.reply("❌ **Invalid Link!** Sirf 'https://t.me/' format wale links bhejo.")

        await link_msg.reply("✍️ **Ab ek message likho jo bot admins ko bhejega.**")

        @bot.on_message(filters.text & filters.private)
        async def get_admin_message(_, msg):
            # ✅ Save in Database
            connected_groups.insert_one({
                "group_link": group_link,
                "owner_msg": msg.text
            })

            await msg.reply("✅ **Group connect ho gaya! Ab bot admins ko ye message bhejega.**")

            # ✅ Send Notice to Admins in Group
            group_chat_id = await get_group_id(group_link)  # ✅ Get Group ID from Link
            if not group_chat_id:
                return await msg.reply("❌ **Bot ko group me add karo phir connect karo!**")

            # ✅ Fetch All Admins
            admins = []
            async for member in bot.get_chat_members(group_chat_id, filter="administrators"):
                if not member.user.is_bot:
                    admins.append(member.user.mention)

            admin_tags = " ".join(admins) if admins else "No admins found"

            notice_msg = f"📢 **Group Connected!**\n\n🔗 **Group:** {group_link}\n✉ **Message:** {msg.text}\n👮‍♂ **Admins:** {admin_tags}"
            sent_msg = await bot.send_message(group_chat_id, notice_msg)
            await sent_msg.pin()  # ✅ Pin the message

# ✅ Function: Get Group ID from Invite Link
async def get_group_id(group_link):
    try:
        chat = await bot.get_chat(group_link)
        return chat.id
    except:
        return None

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

# ✅ MongoDB Collection for Auto Replies
funny_replies_collection = db["funny_replies"]

# ✅ Auto Reply (Random Funny Reply from DB)
@bot.on_message(filters.text & filters.group)
async def auto_reply(_, message):
    if message.reply_to_message or message.entities:
        return  # ✅ Agar reply ya koi link hai to ignore karo

    # ✅ MongoDB Collection for Auto Replies
funny_replies_collection = db["FUNNY_REPLIES"]

# ✅ Auto Reply (Random Funny Reply from Config)
@bot.on_message(filters.text & filters.group)
async def auto_reply(_, message):
    if message.reply_to_message or message.entities:
        return  # ✅ Agar reply ya koi link hai to ignore karo
    
    if FUNNY_REPLIES:  # ✅ Agar FUNNY_REPLIES list empty nahi hai
        reply_text = random.choice(FUNNY_REPLIES)  # ✅ Random Reply Choose Karo
        await message.reply(reply_text)

# ✅ OpenAI API Key (Yahan apni API key daalo)
OPENAI_API_KEY = "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"

# ✅ Function: GPT Se 18+ Content Detect Karna
async def is_adult_content(text):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "Detect if the given text contains NSFW or adult content."},
                  {"role": "user", "content": text}],
        api_key=OPENAI_API_KEY
    )
    result = response["choices"][0]["message"]["content"]
    return "yes" in result.lower()

# ✅ 18+ Sticker/GIF Auto Ban
@bot.on_message((filters.sticker | filters.animation) & filters.group)
async def check_adult_content(_, message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    chat_member = await bot.get_chat_member(chat_id, user_id)
    is_group_owner = chat_member.status == "owner"

    # ✅ Bot Owner ID (Config me define karo)
    BOT_OWNER_ID = 123456789  # 👈 Apna Telegram ID likho

    is_adult = False
    
    # ✅ Telegram AI Filter Se 18+ Content Detect Karna
    if message.sticker and message.sticker.is_animated:
        is_adult = message.sticker.emoji in ["🍆", "🍑", "🔞", "😈"]  
    elif message.animation:
        if message.caption:
            is_adult = await is_adult_content(message.caption)  # ✅ GPT Se Check Karega
    else:
        is_adult = False

    if is_adult:
        await message.delete()  # ✅ Message Delete Karega
        
        if user_id == BOT_OWNER_ID or is_group_owner:
            await message.reply(f"⚠️ **Sir, aap owner hoke 18+ content mat bhejiye!**", quote=True)
        else:
            await bot.ban_chat_member(chat_id, user_id)
            await bot.send_message(chat_id, f"❌ {message.from_user.mention} ne 18+ sticker/GIF bheja, isliye ban kar diya gaya!")

# ✅ Run Bot
bot.run()
