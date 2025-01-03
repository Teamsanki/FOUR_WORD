import discord
from discord.ext import commands
import random
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("MTMyNDgzNzUyNzgwMjA4OTU1NA.GB9AYm.M3E-qwNN0yycJiY9ow6KBl_Jznpu3FtvW31vUA")

# Bot setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# In-memory database for player coins
player_coins = {}

# Function to get player balance
def get_balance(player_id):
    return player_coins.get(player_id, 100)  # Default balance is 100 coins

# Function to update player balance
def update_balance(player_id, amount):
    player_coins[player_id] = get_balance(player_id) + amount

# Bot event: On Ready
@bot.event
async def on_ready():
    print(f"{bot.user} is now online!")

# Command: Check Balance
@bot.command()
async def balance(ctx):
    """Check your coin balance."""
    coins = get_balance(ctx.author.id)
    await ctx.send(f"{ctx.author.mention}, you have **{coins} coins**.")

# Command: Coin Flip
@bot.command()
async def flip(ctx, bet: int, choice: str):
    """Flip a coin! Bet on 'heads' or 'tails'."""
    if choice.lower() not in ["heads", "tails"]:
        await ctx.send("Please bet on 'heads' or 'tails'.")
        return

    coins = get_balance(ctx.author.id)
    if bet > coins:
        await ctx.send("You don't have enough coins to make this bet!")
        return

    result = random.choice(["heads", "tails"])
    if result == choice.lower():
        update_balance(ctx.author.id, bet)
        await ctx.send(f"The coin landed on **{result}**! You won {bet} coins!")
    else:
        update_balance(ctx.author.id, -bet)
        await ctx.send(f"The coin landed on **{result}**. You lost {bet} coins.")

# Command: Slot Machine
@bot.command()
async def slot(ctx, bet: int):
    """Play the slot machine!"""
    coins = get_balance(ctx.author.id)
    if bet > coins:
        await ctx.send("You don't have enough coins to play!")
        return

    # Slot symbols
    symbols = ["🍒", "🍋", "🍇", "🔔", "⭐"]
    slots = [random.choice(symbols) for _ in range(3)]
    await ctx.send(f"🎰 {' | '.join(slots)} 🎰")

    if len(set(slots)) == 1:  # All symbols match
        winnings = bet * 5
        update_balance(ctx.author.id, winnings)
        await ctx.send(f"Jackpot! You won {winnings} coins!")
    elif len(set(slots)) == 2:  # Two symbols match
        winnings = bet * 2
        update_balance(ctx.author.id, winnings)
        await ctx.send(f"Nice! You won {winnings} coins!")
    else:
        update_balance(ctx.author.id, -bet)
        await ctx.send("Better luck next time!")

# Command: Blackjack (Simple Version)
@bot.command()
async def blackjack(ctx, bet: int):
    """Play Blackjack!"""
    coins = get_balance(ctx.author.id)
    if bet > coins:
        await ctx.send("You don't have enough coins to play!")
        return

    def draw_card():
        return random.randint(1, 11)  # Simulates a card draw

    player_score = draw_card() + draw_card()
    dealer_score = draw_card() + draw_card()

    await ctx.send(f"Your cards total: **{player_score}**")
    await ctx.send(f"Dealer's cards total: **{dealer_score}**")

    if player_score > 21:
        update_balance(ctx.author.id, -bet)
        await ctx.send("You busted! Dealer wins!")
    elif dealer_score > 21 or player_score > dealer_score:
        update_balance(ctx.author.id, bet)
        await ctx.send("You win!")
    else:
        update_balance(ctx.author.id, -bet)
        await ctx.send("Dealer wins!")

# Run the bot
bot.run(TOKEN)
