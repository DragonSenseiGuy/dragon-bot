import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("discord.log"), logging.StreamHandler()],
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Initialize your bot with appropriate intents
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content for commands
intents.guilds = True  # Required for accessing guild information
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")
    try:
        await bot.tree.sync()
        print("Slash commands synced!")
    except Exception as e:
        logging.error(f"Failed to sync slash commands: {e}")
    
    bot.remove_command('help')


async def load_cogs():
    for root, dirs, files in os.walk("./cogs"):
        for filename in files:
            if filename.endswith(".py") and filename not in ["time.py", "constants.py"] and not filename.startswith("__") and not filename.startswith("_"): # Exclude __init__.py, _utils.py, time.py, and constants.py
                path = os.path.join(root, filename)
                ext_name = path[2:-3].replace(os.path.sep, ".")
                try:
                    await bot.load_extension(ext_name)
                    logging.info(f"Loaded extension: {ext_name}")
                except Exception as e:
                    logging.error(f"Failed to load cog {ext_name}: {e}")


async def main():
    try:
        async with bot:
            await load_cogs()
            await bot.start(BOT_TOKEN)
    except Exception as e:
        logging.critical(f"Bot failed to start: {e}")


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except Exception as e:
        logging.critical(f"Bot crashed: {e}")
