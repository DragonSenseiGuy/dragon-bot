import discord
from discord import app_commands
from discord.ext import commands
from discord import Embed
import aiohttp
from random import randint
import logging


class Xkcd(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _fetch_and_embed_xkcd(
        self, ctx: discord.Interaction, xkcd_id: str = None
    ):
        """Helper function to fetch and embed an xkcd comic."""
        url = (
            "https://xkcd.com/info.0.json"
            if xkcd_id is None
            else f"https://xkcd.com/{xkcd_id}/info.0.json"
        )
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logging.error(
                            f"Failed to fetch XKCD comic. Status code: {response.status}"
                        )
                        embed = Embed(
                            title="Error",
                            description="Could not retrieve xkcd comic.",
                            colour=0xCD6D6D,
                        )
                        if ctx.response.is_done():
                            await ctx.followup.send(embed=embed)
                        else:
                            await ctx.response.send_message(embed=embed)
                        return

                    info = await response.json()

            embed = Embed(
                title=f"XKCD comic #{info['num']}",
                url=f"https://xkcd.com/{info['num']}",
                colour=0x68C290,
            )
            embed.description = info["alt"]
            date = f"{info['year']}/{info['month']}/{info['day']}"
            embed.set_footer(text=f"{date} - #{info['num']}, '{info['safe_title']}'")

            if info["img"].endswith(("jpg", "png", "gif")):
                embed.set_image(url=info["img"])
            else:
                embed.description = (
                    "The selected comic is interactive, and cannot be displayed within an embed.\n"
                    f"Comic can be viewed [here](https://xkcd.com/{info['num']})."
                )

            if ctx.response.is_done():
                await ctx.followup.send(embed=embed)
            else:
                await ctx.response.send_message(embed=embed)

        except Exception as e:
            logging.error(f"An error occurred during XKCD fetch: {e}")
            embed = Embed(
                title="Error", description=f"An error occurred: {e}", colour=0xCD6D6D
            )
            if ctx.response.is_done():
                await ctx.followup.send(embed=embed)
            else:
                await ctx.response.send_message(embed=embed)

    @app_commands.command(name="xkcd-fetch", description="Fetches a specific xkcd")
    @app_commands.describe(xkcd_id="The id of the xkcd")
    async def xkcd_fetch(self, ctx: discord.Interaction, xkcd_id: str):
        """Fetches a specific xkcd."""
        await self._fetch_and_embed_xkcd(ctx, xkcd_id)

    @app_commands.command(name="xkcd-random", description="Fetches a random xkcd")
    async def xkcd_random(self, ctx: discord.Interaction):
        """Fetches a random xkcd."""
        await ctx.response.defer()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://xkcd.com/info.0.json") as response:
                    if response.status != 200:
                        logging.error(
                            f"Failed to fetch latest XKCD comic. Status code: {response.status}"
                        )
                        embed = Embed(
                            title="Error",
                            description="Could not retrieve the latest xkcd comic.",
                            colour=0xCD6D6D,
                        )
                        await ctx.followup.send(embed=embed)
                        return

                    latest_comic_info = await response.json()
                    latest_comic_num = latest_comic_info["num"]

            random_xkcd_id = str(randint(1, latest_comic_num))
            await self._fetch_and_embed_xkcd(ctx, random_xkcd_id)

        except Exception as e:
            logging.error(f"An error occurred during random XKCD fetch: {e}")
            embed = Embed(
                title="Error", description=f"An error occurred: {e}", colour=0xCD6D6D
            )
            await ctx.followup.send(embed=embed)

    @app_commands.command(name="xkcd-latest", description="Fetches the latest xkcd")
    async def xkcd_latest(self, ctx: discord.Interaction):
        """Fetches the latest xkcd."""
        await ctx.response.defer()
        await self._fetch_and_embed_xkcd(ctx)


async def setup(bot: commands.Bot):
    await bot.add_cog(Xkcd(bot))
