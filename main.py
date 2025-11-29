import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("discord.log"),
                        logging.StreamHandler()
                    ])

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

# Initialize your bot with appropriate intents
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content for commands
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user}')
    try:
        await bot.tree.sync()
        print("Slash commands synced!")
    except Exception as e:
        logging.error(f"Failed to sync slash commands: {e}")

async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
            except Exception as e:
                logging.error(f"Failed to load cog {filename}: {e}")

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