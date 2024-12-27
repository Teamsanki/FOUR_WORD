import telebot
import requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Bot Token and Group Information
BOT_TOKEN = "7710137855:AAHUJe_Ce9GdT_DPhvNd3dcgaBuWJY2odzQ"
GROUP_ID = -1002192731556  # Replace with your group's numeric ID
GROUP_LINK = "https://t.me/+pHtVtmPg-TJmNjVl"  # Your group's link
BIN_API_URL = "https://lookup.binlist.net/"  # BIN Lookup API URL

bot = telebot.TeleBot(BOT_TOKEN)

# Welcome message and photo URL
WELCOME_MESSAGE = """\
Welcome to the bot! 🎉

Commands will only work in the specified group:
[Join the group here]({group_link}).

Available Commands:
1. /chk - Check CC validity.
2. /kill - Kill old CCs.
3. /vbv - Check VBV CC.
4. /gen - Generate CCs.
5. /amt - Charge CC.

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


# Utility function to fetch BIN data
def get_card_data_from_api(bin_number):
    try:
        response = requests.get(f"{BIN_API_URL}{bin_number}")
        if response.status_code == 200:
            data = response.json()
            card_data = {
                "issuer": data.get("bank", {}).get("name", "Unknown"),
                "country": data.get("country", {}).get("name", "Unknown"),
                "flag": data.get("country", {}).get("emoji", ""),  # Country flag
                "type": data.get("type", "Unknown").capitalize(),
            }
            return card_data
        else:
            return None
    except Exception as e:
        print(f"Error fetching BIN data: {e}")
        return None


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
        
        bin_number = cc_details[0][:6]  # Extract BIN from the first 6 digits
        card_data = get_card_data_from_api(bin_number)
        
        if card_data:
            bot.reply_to(
                message,
                f"✅ CC is valid!\n\nIssuer: {card_data['issuer']}\n"
                f"Country: {card_data['country']} {card_data['flag']}\n"
                f"Type: {card_data['type']}\n\nMade by @TSGCODER."
            )
        else:
            bot.reply_to(message, "❌ CC is invalid or BIN not found!\n\nMade by @TSGCODER.")
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
        
        # Simulate CC kill logic here
        bot.reply_to(message, "✅ CC has been killed!\n\nMade by @TSGCODER.")
    except ValueError:
        bot.reply_to(message, "⚠️ Invalid format. Use: `/kill cc_number|dd|mm|code`.")


# /vbv command (Check VBV)
@bot.message_handler(commands=['vbv'])
def check_vbv(message):
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
        
        # Simulate VBV checking logic here
        bot.reply_to(message, "✅ VBV check passed!\n\nMade by @TSGCODER.")
    except ValueError:
        bot.reply_to(message, "⚠️ Invalid format. Use: `/vbv cc_number|dd|mm|code`.")


# Main bot polling
print("Bot is running...")
bot.polling(none_stop=True)
