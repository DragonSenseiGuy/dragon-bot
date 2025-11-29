from discord import app_commands
from discord.ext import commands
from typing import Literal
import pyjokes

class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="joke", description="Retrieves a joke of the specified `category` from the pyjokes api.")
    @app_commands.describe(category="The joke category")
    async def joke(self, ctx: commands.Context, category: Literal["neutral", "chuck", "all"] = "all") -> None:
        """Retrieves a joke of the specified `category` from the pyjokes api."""
        joke = pyjokes.get_joke(category=category)
        await ctx.response.send_message(joke)

async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))