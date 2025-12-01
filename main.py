import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging

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
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")
    try:
        await bot.tree.sync()
        print("Slash commands synced!")
    except Exception as e:
        logging.error(f"Failed to sync slash commands: {e}")


async def load_cogs():
    for root, dirs, files in os.walk("./cogs"):
        for filename in files:
            if filename.endswith(".py") and not filename.startswith("__"):
                # Construct the extension name from the file path
                # e.g., cogs/moderation/cog.py -> cogs.moderation.cog
                path = os.path.join(root, filename)
                # remove ./ and .py, and replace / with .
                ext_name = path[2:-3].replace(os.path.sep, ".")
                if "moderation.cog" in ext_name:
                    try:
                        await bot.load_extension(ext_name)
                        logging.info(f"Loaded extension: {ext_name}")
                    except Exception as e:
                        logging.error(f"Failed to load cog {ext_name}: {e}")
                elif "moderation" in ext_name:
                    pass
                else:
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
