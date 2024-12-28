import telebot
import requests

# Replace with your bot token
BOT_TOKEN = "7738772255:AAFS3v5fWSvz5sohG2Pyj0lFqHpR6DkVqSA"
SMM_API_KEY = "8fad2d01e3babd20536bbc56920c9408"
SMM_API_URL = "https://smmpanel.com/api/v2"

bot = telebot.TeleBot(BOT_TOKEN)

# Store user bonus balances (for simplicity, using in-memory storage)
user_bonus = {}

# Command to start the bot
@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(
        message,
        "Hello! I am your View Booster Bot.\n\n"
        "Commands:\n"
        "/view <link> <amount> - To increase views\n"
        "/bonus - To claim 300 bonus points\n"
    )

# Command to increase views
@bot.message_handler(commands=["view"])
def increase_views(message):
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.reply_to(
                message, "Usage: /view <link> <amount>\nExample: /view https://example.com 500"
            )
            return

        link = args[1]
        amount = int(args[2])

        if amount > 1000:
            bot.reply_to(message, "You cannot request more than 1000 views.")
            return

        # Check if user has enough bonus points
        user_id = message.from_user.id
        if user_id not in user_bonus or user_bonus[user_id] < amount:
            bot.reply_to(message, "You do not have enough bonus points.")
            return

        # Deduct bonus points
        user_bonus[user_id] -= amount

        # Place the order with the SMM Panel
        params = {
            "key": SMM_API_KEY,
            "action": "add",
            "service": "SERVICE_ID_FOR_VIEWS",  # Replace with the actual service ID for views
            "link": link,
            "quantity": amount,
        }
        response = requests.post(SMM_API_URL, data=params)
        data = response.json()

        if data.get("error"):
            bot.reply_to(message, f"Error: {data['error']}")
        else:
            order_id = data.get("order")
            bot.reply_to(
                message, f"✅ Order successful! Order ID: {order_id}\n{amount} views are being added to your link."
            )

    except Exception as e:
        bot.reply_to(message, f"Something went wrong: {e}")

# Command to claim bonus
@bot.message_handler(commands=["bonus"])
def claim_bonus(message):
    user_id = message.from_user.id

    if user_id in user_bonus:
        bot.reply_to(message, "You have already claimed your bonus!")
        return

    # Add bonus points to the user's account
    user_bonus[user_id] = 300

    # Optionally add the bonus directly to the SMM Panel
    params = {
        "key": SMM_API_KEY,
        "action": "add_balance",
        "amount": 300,  # Add 300 bonus points
        "user_id": user_id,
    }
    response = requests.post(SMM_API_URL, data=params)
    data = response.json()

    if data.get("error"):
        bot.reply_to(message, f"Error: {data['error']}")
    else:
        bot.reply_to(message, "🎉 You have received 300 bonus points!")

# Polling to keep the bot running
bot.polling()
