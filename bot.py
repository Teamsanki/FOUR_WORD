import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import string
from datetime import datetime

# Bot Token aur Group ID
BOT_TOKEN = "7710137855:AAHUJe_Ce9GdT_DPhvNd3dcgaBuWJY2odzQ"
GROUP_ID = -1002192731556  # Apne group ka numeric ID yaha daale (use @userinfobot to get it)
GROUP_LINK = "https://t.me/+pHtVtmPg-TJmNjVl"  # Aapka group ka link
OWNER_ID = 7877197608  # Replace with your Telegram ID

bot = telebot.TeleBot(BOT_TOKEN)

# Welcome message aur photo URL
WELCOME_MESSAGE = """\
Welcome to the bot! 🎉

Click on the "Commands" button below to see available commands.

Commands will only work in the specified group:
[Join the group here]({group_link}).

Made with ❤️ by @TSGCODER.
""".format(group_link=GROUP_LINK)

PHOTO_URL = "https://graph.org/file/cfdf03d8155f959c18668-3c90376a72789999f1.jpg"  # Replace with your photo URL

# Commands message
COMMANDS_MESSAGE = """\
Available Commands:
1. /chk - Check CC validity.
2. /kill - Kill old CCs.
3. /vbv - Check VBV CC.
4. /gen - Generate CC from BIN.
5. /amt - Charge CC (subscription required).
6. /redeem - Redeem codes.

Made with ❤️ by @TSGCODER.
"""

# Subscription details
SUBSCRIBERS = [OWNER_ID]  # Add user IDs who have subscription
REDEEM_CODES = {}  # Redeem codes storage
OWNER_USE_LIMIT = 10  # Limit for owner command usage
owner_command_count = 0


# /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Commands", callback_data="commands"))
    bot.send_photo(
        message.chat.id,
        PHOTO_URL,
        caption=WELCOME_MESSAGE,
        parse_mode="Markdown",
        reply_markup=markup,
    )


# Callback for inline button
@bot.callback_query_handler(func=lambda call: call.data == "commands")
def show_commands(call):
    bot.answer_callback_query(call.id, "Showing commands...")
    bot.edit_message_caption(
        caption=COMMANDS_MESSAGE,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode="Markdown",
    )


# /chk command
@bot.message_handler(commands=['chk'])
def check_cc(message):
    validate_cc(message, "chk")


# /kill command
@bot.message_handler(commands=['kill'])
def kill_cc(message):
    validate_cc(message, "kill")


# /vbv command
@bot.message_handler(commands=['vbv'])
def vbv_cc(message):
    validate_cc(message, "vbv")


# Function to validate CC
def validate_cc(message, command_type):
    if message.chat.type != "supergroup" or message.chat.id != GROUP_ID:
        bot.reply_to(
            message,
            f"⚠️ This command only works in the group [Join here]({GROUP_LINK}).",
            parse_mode="Markdown",
        )
        return

    try:
        _, cc_info = message.text.split(" ", 1)
        cc_details = cc_info.split("|")
        if len(cc_details) != 4:
            raise ValueError("Invalid CC format.")
        if cc_details[0].isdigit() and len(cc_details[0]) == 16:
            response = f"""
𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅

𝗖𝗮𝗿𝗱: {cc_details[0]}
𝐆𝐚𝐭𝐞𝐰𝐚𝐲: {command_type.upper()}
𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: Valid

Card 𝗜𝗻𝗳𝗼:
𝐈𝐬𝐬𝐮𝐞𝐫: Example Bank
𝐂𝐨𝐮𝐧𝐭𝐫𝐲: Example Country

𝗧𝗶𝗺𝗲: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        else:
            response = f"""
𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌

𝗖𝗮𝗿𝗱: Invalid
𝗥𝗲𝐬𝗽𝐨𝐧𝐬𝐞: Invalid details provided.
"""
        bot.reply_to(message, response)
    except ValueError:
        bot.reply_to(message, "⚠️ Invalid format. Use: `/chk cc_number|dd|mm|code`.")


# /gen command
@bot.message_handler(commands=['gen'])
def generate_cc(message):
    try:
        _, bin_info = message.text.split(" ", 1)
        if len(bin_info) != 6:
            raise ValueError("Invalid BIN format.")
        generated_ccs = [
            f"{bin_info}{random.randint(1000000000, 9999999999)}|{random.randint(1, 12)}|{random.randint(23, 30)}|{random.randint(100, 999)}"
            for _ in range(5)
        ]
        response = "Generated CCs:\n\n" + "\n".join(generated_ccs)
        bot.reply_to(message, response)
    except ValueError:
        bot.reply_to(message, "⚠️ Invalid format. Use: `/gen bin_number`.")


# /amt command
@bot.message_handler(commands=['amt'])
def charge_cc(message):
    if message.from_user.id not in SUBSCRIBERS:
        bot.reply_to(
            message,
            "⚠️ You need a subscription to use this command. Contact @TSGCODER for subscription.",
        )
        return

    try:
        _, cc_info = message.text.split(" ", 1)
        cc_details = cc_info.split(" ")
        if len(cc_details) != 3:
            raise ValueError("Invalid format.")
        response = f"✅ CC {cc_details[0]} has been charged ${cc_details[2]} successfully.\n\nMade by @TSGCODER."
        bot.reply_to(message, response)
    except ValueError:
        bot.reply_to(message, "⚠️ Invalid format. Use: `/amt cc_number age amount`.")


# /genrdm command
@bot.message_handler(commands=['genrdm'])
def generate_redeem_code(message):
    global owner_command_count
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "⚠️ Only the bot owner can use this command.")
        return

    if owner_command_count >= OWNER_USE_LIMIT:
        bot.reply_to(message, "⚠️ Command limit reached for generating redeem codes.")
        return

    redeem_code = "-".join(
        ["".join(random.choices(string.ascii_uppercase, k=x)) for x in [3, 2, 4, 2]]
    )
    REDEEM_CODES[redeem_code] = False  # Code not yet redeemed
    owner_command_count += 1
    bot.reply_to(message, f"✅ Redeem code generated: {redeem_code}")


# /redeem command
@bot.message_handler(commands=['redeem'])
def redeem_code(message):
    try:
        _, code = message.text.split(" ", 1)
        if code in REDEEM_CODES and not REDEEM_CODES[code]:
            REDEEM_CODES[code] = True  # Mark as redeemed
            bot.reply_to(message, "✅ Redeem code successfully used!")
        else:
            bot.reply_to(message, "⚠️ Invalid or already used redeem code.")
    except ValueError:
        bot.reply_to(message, "⚠️ Invalid format. Use: `/redeem code`.")


# Bot running
print("Bot is running...")
bot.infinity_polling()
