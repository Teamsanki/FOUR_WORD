import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Bot Token aur Group ID
BOT_TOKEN = "7710137855:AAHUJe_Ce9GdT_DPhvNd3dcgaBuWJY2odzQ"
GROUP_ID = -1002192731556  # Apne group ka numeric ID yaha daale (use @userinfobot to get it)
GROUP_LINK = "https://t.me/+pHtVtmPg-TJmNjVl"  # Aapka group ka link

bot = telebot.TeleBot(BOT_TOKEN)

# Welcome message aur photo URL
WELCOME_MESSAGE = """\
Welcome to the bot! 🎉

Commands will only work in the specified group:
[Join the group here]({group_link}).

Available Commands:
1. /chk - Check CC validity.
2. /kill - Kill old CCs.

Made with ❤️ by @TSGCODER.
""".format(group_link=GROUP_LINK)

PHOTO_URL = "https://graph.org/file/cfdf03d8155f959c18668-3c90376a72789999f1.jpg"  # Replace with your photo URL


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
    bot.answer_callback_query(call.id, "Commands list!")
    bot.edit_message_caption(
        caption=WELCOME_MESSAGE,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode="Markdown",
    )


# /chk command
@bot.message_handler(commands=['chk'])
def check_cc(message):
    if message.chat.type != "supergroup" or message.chat.id != GROUP_ID:
        bot.reply_to(
            message,
            "⚠️ This command only works in the group [Join here]({}).".format(GROUP_LINK),
            parse_mode="Markdown",
        )
        return

    try:
        _, cc_info = message.text.split(" ", 1)
        cc_details = cc_info.split("|")
        if len(cc_details) != 4:
            raise ValueError("Invalid CC format.")
        # Example CC validation logic (customize as needed)
        if cc_details[0].isdigit() and len(cc_details[0]) == 16:
            bot.reply_to(message, "✅ CC is valid!\n\nMade by @TSGCODER.")
        else:
            bot.reply_to(message, "❌ CC is invalid!\n\nMade by @TSGCODER.")
    except ValueError:
        bot.reply_to(message, "⚠️ Invalid format. Use: `/chk cc_number|dd|mm|code`.")


# /kill command
@bot.message_handler(commands=['kill'])
def kill_cc(message):
    if message.chat.type != "supergroup" or message.chat.id != GROUP_ID:
        bot.reply_to(
            message,
            "⚠️ This command only works in the group [Join here]({}).".format(GROUP_LINK),
            parse_mode="Markdown",
        )
        return

    try:
        _, cc_info = message.text.split(" ", 1)
        cc_details = cc_info.split("|")
        if len(cc_details) != 4:
            raise ValueError("Invalid CC format.")
        # Example old CC check logic (customize as needed)
        bot.reply_to(message, "✅ CC has been killed!\n\nMade by @TSGCODER.")
    except ValueError:
        bot.reply_to(message, "⚠️ Invalid format. Use: `/kill cc_number|dd|mm|code`.")


# Bot running
print("Bot is running...")
bot.infinity_polling()
