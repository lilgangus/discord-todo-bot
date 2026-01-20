import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "!"

# Create bot instance with intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)


@bot.event
async def on_ready():
    print(f"{bot.user} is now online!")


@bot.command()
async def ping(ctx):
    """Responds with the bot's latency."""
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")


@bot.command()
async def hello(ctx):
    """Sends a greeting."""
    await ctx.send(f"Hello, {ctx.author.name}!")


# Run the bot
bot.run(TOKEN)
