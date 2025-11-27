import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

# Initialize your bot with appropriate intents
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content for commands
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user}')
    await bot.tree.sync()
    print("Slash commands synced!")

# Channel Commands
@bot.tree.command(name="create-channel", description="Creates a new text channel")
@app_commands.describe(channel_name="The name of the channel to create", category_id="The ID of the category to create the channel in", description="The description of the channel")
@commands.has_permissions(manage_channels=True) # Ensure the user has permission
async def create_text_channel(ctx: discord.Interaction, channel_name: str, category_id: str, description: str):
    """Creates a new text channel in the current guild."""
    try:
        try:
            cat_id = int(category_id)
        except ValueError:
            await ctx.response.send_message("Category ID must be a valid number.")
            return
        await ctx.guild.create_text_channel(name=channel_name, category=discord.utils.get(ctx.guild.categories, id=cat_id), topic=description)
        await ctx.response.send_message(f'Text channel "{channel_name}" created successfully!')
    except discord.Forbidden:
        await ctx.response.send_message("I don't have permission to create channels here.")
    except Exception as e:
        await ctx.response.send_message(f"An error occurred: {e}")

@bot.tree.command(name="delete-channel", description="Deletes a text channel")
@app_commands.describe(channel_id="The ID of the channel to delete")
@commands.has_permissions(manage_channels=True) # Ensure the user has permission
async def delete_text_channel(ctx: discord.Interaction, channel_id: str):
    """Deletes a text channel in the current guild."""
    try:
        try:
            chan_id = int(channel_id)
        except ValueError:
            await ctx.response.send_message("Channel ID must be a valid number.")
            return
        channel = discord.utils.get(ctx.guild.channels, id=chan_id)
        if channel:
            await channel.delete()
            await ctx.response.send_message(f'Text channel "{channel.name}" deleted successfully!')
        else:
            await ctx.response.send_message(f'Channel with ID "{channel_id}" not found.')
    except discord.Forbidden:
        await ctx.response.send_message("I don't have permission to delete channels here.")
    except Exception as e:
        await ctx.response.send_message(f"An error occurred: {e}")

# Sync
@bot.tree.command(name="sync", description="Syncs the slash commands to Discord.")
async def sync(ctx: discord.Interaction):
    if ctx.user.id == ctx.guild.owner_id: # Only allow guild owner to sync
        await bot.tree.sync()
        await ctx.response.send_message("Slash commands synced!")
    else:
        await ctx.response.send_message("You must be the guild owner to use this command.")

bot.run(BOT_TOKEN)