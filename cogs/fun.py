from discord import app_commands
from discord.ext import commands
from typing import Literal
import pyjokes
import random
from json import loads
from pathlib import Path
import aiohttp
from aiohttp import ClientError, ClientResponseError
from discord import Embed
import logging

ALL_VIDS = loads(Path("resources/fun/april_fools_vids.json").read_text("utf-8"))


class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="joke",
        description="Retrieves a joke of the specified `category` from the pyjokes api.",
    )
    @app_commands.describe(category="The joke category")
    async def joke(
        self,
        ctx: commands.Context,
        category: Literal["neutral", "chuck", "all"] = "all",
    ) -> None:
        """Retrieves a joke of the specified `category` from the pyjokes api."""
        joke = pyjokes.get_joke(category=category)
        await ctx.response.send_message(joke)

    @app_commands.command(
        name="fool", description="Get a random April Fools' video from Youtube."
    )
    async def april_fools(self, ctx: commands.Context) -> None:
        """Get a random April Fools' video from Youtube."""
        video = random.choice(ALL_VIDS)

        channel, url = video["channel"], video["url"]

        await ctx.response.send_message(
            f"Check out this April Fools' video by {channel}.\n\n{url}"
        )

    @app_commands.command(
        name="quote",
        description="Retrieves a quote from the zenquotes.io api.",
    )
    @app_commands.describe(subcommands="Random or daily")
    async def quote(
            self,
            ctx: commands.Context,
            subcommands: Literal["daily", "random"],
    ) -> None:
        """Retrieves a quote from the zenquotes.io api."""
        if subcommands == "daily":
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://zenquotes.io/api/today") as resp:
                        resp.raise_for_status()
                        data = await resp.json()
                        quote = f"{data[0]['q']}\n*— {data[0]['a']}*"

                embed = Embed(
                    title="Daily Quote",
                    description=f"> {quote}\n\n-# Powered by [zenquotes.io](https://zenquotes.io)",
                    colour=0x0279FD
                )
                await ctx.response.send_message(embed=embed)
            except ClientResponseError as e:
                logging.warning(f"ZenQuotes API error: {e.status} {e.message}")
                await ctx.response.send_message(":x: Could not retrieve quote from API.")
            except (ClientError, TimeoutError) as e:
                logging.error(f"Network error fetching quote: {e}")
                await ctx.response.send_message(":x: Could not connect to the quote service.")
            except Exception:
                logging.exception("Unexpected error fetching quote.")
                await ctx.response.send_message(":x: Something unexpected happened. Try again later.")
        if subcommands == "random":
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://zenquotes.io/api/random") as resp:
                        resp.raise_for_status()
                        data = await resp.json()
                        quote = f"{data[0]['q']}\n*— {data[0]['a']}*"

                embed = Embed(
                    title="Random Quote",
                    description=f"> {quote}\n\n-# Powered by [zenquotes.io](https://zenquotes.io)",
                    colour=0x0279FD
                )
                await ctx.response.send_message(embed=embed)
            except ClientResponseError as e:
                logging.warning(f"ZenQuotes API error: {e.status} {e.message}")
                await ctx.response.send_message(":x: Could not retrieve quote from API.")
            except (ClientError, TimeoutError) as e:
                logging.error(f"Network error fetching quote: {e}")
                await ctx.response.send_message(":x: Could not connect to the quote service.")
            except Exception:
                logging.exception("Unexpected error fetching quote.")
                await ctx.response.send_message(":x: Something unexpected happened. Try again later.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
