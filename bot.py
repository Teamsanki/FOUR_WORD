import re
import pymongo
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN, MONGO_URL, DEVELOPER_USERNAME, GROUP_LINK, WELCOME_GIF, SANKI_LINK, ABUSE_WORDS

# 🔹 Bot Initialization
bot = Client("IndianChatBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# 🔹 MongoDB Connection
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
    
    await message.reply_photo(WELCOME_GIF, caption="🤖 **Indian Chatting Club Bot**\nMain yahan aapki madad aur security ke liye hoon!", reply_markup=buttons)

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

# ✅ Back to Main Menu
@bot.on_callback_query(filters.regex("back_to_main"))
async def back_main(_, query):
    await start(_, query.message)

# ✅ Abuse Detection (Auto Ban)
@bot.on_message(filters.text & filters.group)
async def check_abuse(_, message):
    if any(word in message.text.lower() for word in ABUSE_WORDS):
        await message.reply(f"🚫 {message.from_user.mention} abuse words use mat karo!", quote=True)
        await bot.ban_chat_member(message.chat.id, message.from_user.id)

# ✅ Bio Link Detection (Warn User)
@bot.on_chat_member_updated
async def check_bio(_, update):
    user = update.new_chat_member
    if user and user.bio and ("http" in user.bio or "t.me" in user.bio):
        await bot.send_message(update.chat.id, f"⚠️ {user.user.mention}, apke bio me link hai. Isko hatao warna action liya jayega!")

# ✅ DM Request Detection (Warn Message)
@bot.on_message(filters.text & filters.group)
async def check_dm_request(_, message):
    if re.search(r"dm me aao|mujhe dm karo", message.text.lower()):
        await message.reply(f"⚠️ {message.from_user.mention}, bina permission DM mat karo!", quote=True)

# ✅ Welcome New User (GIF + Caption + Inline Button)
@bot.on_chat_member_updated
async def welcome_user(_, update):
    if update.new_chat_member:
        buttons = InlineKeyboardMarkup([[InlineKeyboardButton("SANKI", url=SANKI_LINK)]])
        await bot.send_animation(update.chat.id, WELCOME_GIF, caption=f"👋 Welcome {update.new_chat_member.user.mention}!\nHope you enjoy our chat!", reply_markup=buttons)

# ✅ /connect Command (Group Connection & Admin Tagging)
@bot.on_message(filters.command("connect") & filters.private)
async def connect_group(_, message):
    await message.reply("🔗 Apne group me bot add karo aur uska link bhejo.")
    
    @bot.on_message(filters.text & filters.private)
    async def get_group_link(_, link_msg):
        if "t.me" in link_msg.text:
            await message.reply("✍️ Ab message likho jo aap admins ko bhejna chahte ho.")

            @bot.on_message(filters.text & filters.private)
            async def get_admin_message(_, msg):
                group_collection.insert_one({"group_link": link_msg.text, "owner_msg": msg.text})
                await message.reply("✅ Message save ho gaya! Bot aapke group ke admins ko ye bhejega.")

# ✅ /utag (Tag All Users)
@bot.on_message(filters.command("utag") & filters.group)
async def tag_all_users(_, message: Message):
    chat_id = message.chat.id
    members = [member.user for member in await bot.get_chat_members(chat_id) if not member.user.is_bot]
    
    if not members:
        await message.reply("❌ Group me koi member nahi hai!")
        return

    tag_text = "👥 **Tagging All Users:**\n\n"
    tag_text += " ".join([f"@{user.username}" if user.username else user.mention for user in members])
    
    msg_text = message.text.split(maxsplit=1)
    custom_msg = f"\n\n🗣 **Message:** {msg_text[1]}" if len(msg_text) > 1 else ""

    await message.reply(tag_text + custom_msg)

# ✅ /atag (Tag All Admins)
@bot.on_message(filters.command("atag") & filters.group)
async def tag_admins(_, message: Message):
    chat_id = message.chat.id
    admins = [member.user for member in await bot.get_chat_members(chat_id, filter="administrators") if not member.user.is_bot]

    if not admins:
        await message.reply("❌ Group me koi admin nahi hai!")
        return

    tag_text = "👮‍♂️ **Tagging All Admins:**\n\n"
    tag_text += " ".join([f"@{user.username}" if user.username else user.mention for user in admins])

    msg_text = message.text.split(maxsplit=1)
    custom_msg = f"\n\n🗣 **Message:** {msg_text[1]}" if len(msg_text) > 1 else ""

    await message.reply(tag_text + custom_msg)

# ✅ Function: Send Good Morning/Night Message
async def send_daily_message(chat_id, message_type):
    quotes = {
        "morning": [
            "🌞 **Good Morning!**\nHar naya din ek naye mauke ki tarah hota hai. Khush raho, aage badho!",
            "☀️ **Subah Ki Taazgi Mubarak Ho!**\nZindagi me naye sapne dekho aur unhe pura karo!"
        ],
        "night": [
            "🌙 **Good Night!**\nAchhe sapne dekho aur ek naye din ke liye tayyar ho jao!",
            "💤 **Shubh Ratri!**\nAaj ka din jitna bhi tough tha, kal naya din naye umeed lekar aayega!"
        ]
    }
    
    image_links = {
        "morning": "https://telegra.ph/file/3d3c3b5b5d2ff1c4dce90.jpg",
        "night": "https://telegra.ph/file/bb73189c1ddf0d99a64c2.jpg"
    }

    caption = random.choice(quotes[message_type])
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("SANKI", url=SANKI_LINK)]])

    await bot.send_photo(chat_id, image_links[message_type], caption=caption, reply_markup=buttons)

# ✅ Schedule Morning/Night Messages
async def schedule_daily_messages():
    while True:
        now = datetime.now().strftime("%H:%M")
        if now == "07:00":  # Subah 7 baje Good Morning
            await send_daily_message(GROUP_CHAT_ID, "morning")
        elif now == "22:00":  # Raat 10 baje Good Night
            await send_daily_message(GROUP_CHAT_ID, "night")
        await asyncio.sleep(60)

# ✅ Function: Festival Auto Message
async def send_festival_message(chat_id):
    festivals = [
        "Holi", "Diwali", "Eid", "Christmas", "Navratri", "Raksha Bandhan", "Baisakhi"
    ]
    
    festival_name = random.choice(festivals)
    search_url = f"https://www.googleapis.com/customsearch/v1?q={festival_name}+festival&searchType=image&key=YOUR_GOOGLE_API_KEY"
    
    response = requests.get(search_url).json()
    image_url = response["items"][0]["link"] if "items" in response else None

    festival_msg = f"🎉 **{festival_name} Mubarak!**\nAap sabhi ko {festival_name} ki dher saari shubhkamnayein! 🤗"

    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("SANKI", url=SANKI_LINK)]])
    if image_url:
        await bot.send_photo(chat_id, image_url, caption=festival_msg, reply_markup=buttons)
    else:
        await bot.send_message(chat_id, festival_msg, reply_markup=buttons)

# ✅ Function: Best Message of the Day
best_message = {"user": None, "message": "", "likes": 0}

@bot.on_message(filters.text & filters.group)
async def track_best_message(_, message):
    if "👍" in message.text or "❤️" in message.text:
        if message.reply_to_message and message.reply_to_message.from_user:
            if message.reply_to_message.from_user.id == message.from_user.id:
                return  # Apne message ko like nahi kar sakte

            if best_message["likes"] < 5:  # Minimum 5 likes hone chahiye
                best_message.update({
                    "user": message.reply_to_message.from_user.mention,
                    "message": message.reply_to_message.text,
                    "likes": best_message["likes"] + 1
                })

# ✅ /bestmsg Command
@bot.on_message(filters.command("bestmsg") & filters.group)
async def best_msg_command(_, message):
    if best_message["user"]:
        await message.reply(f"🏆 **Best Message of the Day!**\n\n👤 {best_message['user']}\n📝 {best_message['message']}\n❤️ {best_message['likes']} Likes!")
    else:
        await message.reply("❌ Aaj tak koi best message select nahi hua!")

# ✅ Schedule Festival Messages
async def schedule_festival_messages():
    while True:
        now = datetime.now().strftime("%d-%m")  # Check date
        if now in ["08-03", "25-12", "14-11"]:  # Special Festival Dates
            await send_festival_message(GROUP_CHAT_ID)
        await asyncio.sleep(86400)  # 24 Hours Wait

# ✅ Dictionary to track user messages
user_messages = Counter()

@bot.on_message(filters.text & filters.group)
async def count_messages(_, message):
    user_id = message.from_user.id
    user_messages[user_id] += 1

# ✅ Function to send weekly top members list
async def send_top_members():
    while True:
        await asyncio.sleep(604800)  # 7 din (1 week)
        if user_messages:
            sorted_users = user_messages.most_common(5)
            msg = "**🏆 Weekly Top Members 🏆**\n\n"
            for rank, (user_id, msg_count) in enumerate(sorted_users, start=1):
                user = await bot.get_users(user_id)
                msg += f"**{rank}. {user.mention}** - {msg_count} messages\n"
            
            await bot.send_message(GROUP_CHAT_ID, msg)
        user_messages.clear()

# ✅ AI-Based Funny Reply System
@bot.on_message(filters.text & filters.group)
async def auto_reply(_, message):
    if message.reply_to_message is None and not message.entities:
        reply = random.choice(funny_replies)
        await message.reply(reply)

bot.run()
