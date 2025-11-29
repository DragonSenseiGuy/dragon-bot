from discord import app_commands
from discord.ext import commands
from typing import Literal
import pyjokes
import random
from json import loads
from pathlib import Path

ALL_VIDS = loads(Path("resources/fun/april_fools_vids.json").read_text("utf-8"))

class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="joke", description="Retrieves a joke of the specified `category` from the pyjokes api.")
    @app_commands.describe(category="The joke category")
    async def joke(self, ctx: commands.Context, category: Literal["neutral", "chuck", "all"] = "all") -> None:
        """Retrieves a joke of the specified `category` from the pyjokes api."""
        joke = pyjokes.get_joke(category=category)
        await ctx.response.send_message(joke)

    @app_commands.command(name="fool", description="Get a random April Fools' video from Youtube.")
    async def april_fools(self, ctx: commands.Context) -> None:
        """Get a random April Fools' video from Youtube."""
        video = random.choice(ALL_VIDS)

        channel, url = video["channel"], video["url"]

        await ctx.response.send_message(f"Check out this April Fools' video by {channel}.\n\n{url}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))