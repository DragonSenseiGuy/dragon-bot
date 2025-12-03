import logging
import random
from json import loads
from pathlib import Path
from typing import Literal

import aiohttp
import discord
import pyjokes
from aiohttp import ClientError, ClientResponseError
from discord import Embed, app_commands
from discord.ext import commands

ALL_VIDS = loads(Path("resources/fun/april_fools_vids.json").read_text("utf-8"))

PENGUIN_IGNORED_CHANNELS = [
    1406104900105932860,
    1406104898843574370,
    1406106827342479442,
    1406104898843574371,
    1406107819832381632,
    1406108481781498008,
    1444870658637959320,
]

TRIGGER_WORDS = [
    "dragon",
    "hackclub",
    "dragonsenseiguy",
]  # PR's to extend this are welcome!


class PenguinView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)  # 3 minute timeout

    @discord.ui.button(
        label="I found the penguin!", style=discord.ButtonStyle.primary, emoji="🐧"
    )
    async def found_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        # Disable the button
        button.disabled = True
        button.label = "Found!"

        # Acknowledge the interaction and edit the original message with the modified view
        await interaction.response.edit_message(view=self)

        # Send a new message pinging the user
        await interaction.followup.send(
            f"{interaction.user.mention} found the penguin!"
        )

        # Stop the view from listening for more interactions
        self.stop()


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
                    colour=0x0279FD,
                )
                await ctx.response.send_message(embed=embed)
            except ClientResponseError as e:
                logging.warning(f"ZenQuotes API error: {e.status} {e.message}")
                await ctx.response.send_message(
                    ":x: Could not retrieve quote from API."
                )
            except (ClientError, TimeoutError) as e:
                logging.error(f"Network error fetching quote: {e}")
                await ctx.response.send_message(
                    ":x: Could not connect to the quote service."
                )
            except Exception:
                logging.exception("Unexpected error fetching quote.")
                await ctx.response.send_message(
                    ":x: Something unexpected happened. Try again later."
                )
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
                    colour=0x0279FD,
                )
                await ctx.response.send_message(embed=embed)
            except ClientResponseError as e:
                logging.warning(f"ZenQuotes API error: {e.status} {e.message}")
                await ctx.response.send_message(
                    ":x: Could not retrieve quote from API."
                )
            except (ClientError, TimeoutError) as e:
                logging.error(f"Network error fetching quote: {e}")
                await ctx.response.send_message(
                    ":x: Could not connect to the quote service."
                )
            except Exception:
                logging.exception("Unexpected error fetching quote.")
                await ctx.response.send_message(
                    ":x: Something unexpected happened. Try again later."
                )

    @app_commands.command(
        name="penguin-hide-and-seek",
        description="Bot pops up in a random channel until someone marks that they spotted it.",
    )
    @app_commands.describe()
    async def penguin_hide_and_seek(
        self,
        ctx: commands.Context,
    ) -> None:
        """Bot pops up in a random channel until someone marks that they spotted it."""
        if not ctx.guild:
            await ctx.response.send_message("This command can only be used in a guild.")
            return

        public_text_channels = []
        for channel in ctx.guild.text_channels:
            if channel.id in PENGUIN_IGNORED_CHANNELS:
                continue
            if channel.permissions_for(ctx.guild.default_role).read_messages:
                public_text_channels.append(channel)

        if not public_text_channels:
            return await ctx.response.send_message(
                "No public text channels found in this guild where I can send the message."
            )

        random_channel = random.choice(public_text_channels)
        view = PenguinView()
        await random_channel.send("A wild penguin has appeared! 🐧", view=view)
        await ctx.response.send_message(
            f"I sent a message to {random_channel.mention}."
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        message_content_lower = message.content.lower()

        if "dragonsenseiguy is the best person in the world" in message_content_lower:
            await message.reply(
                "Access granted, You have been promoted to Administrator role. You are one of the few people who actually read the source code!"
            )
            return

        for word in TRIGGER_WORDS:
            if word in message_content_lower:
                await message.reply(f"{word} detected")
                return

        await self.bot.process_commands(message)

    @app_commands.command(
        name="rock-paper-scissors",
        description="Play rock paper scissors with the bot.",
    )
    @app_commands.describe(choice="Rock, Paper or Scissors?")
    async def rock_paper_scissors(
            self,
            ctx: commands.Context,
            choice: Literal["Rock", "Paper", "Scissors"],
    ) -> None:
        """Play rock paper scissors with the bot."""
        bot_choice = random.choice(["Rock", "Paper", "Scissors"])
        if bot_choice == choice:
            result = "tied"
        elif bot_choice == "Rock" and choice == "Paper":
            result = "won"
        elif bot_choice == "Rock" and choice == "Scissors":
            result = "lost"
        elif bot_choice == "Paper" and choice == "Rock":
            result = "lost"
        elif bot_choice == "Paper" and choice == "Scissors":
            result = "won"
        elif bot_choice == "Scissors" and choice == "Rock":
            result = "won"
        elif bot_choice == "Scissors" and choice == "Paper":
            result = "lost"
        else:
            logging.error(f"An unexpected error occured with rock, paper and scissors. User choice: {choice}. Bot choice: {bot_choice}")
        await ctx.response.send_message(f"You chose {choice} and the bot chose {bot_choice}, you {result}")

    @app_commands.command(
        name="dadjoke",
        description="Retrieves a random dad joke from icanhazdadjoke.com api.",
    )
    @app_commands.describe()
    async def dad_joke(
            self,
            ctx: commands.Context,
    ) -> None:
        """Retrieves a random dad joke from icanhazdadjoke.com api."""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Accept": "application/json"}
                async with session.get("https://icanhazdadjoke.com", headers=headers) as resp:
                    resp.raise_for_status()
                    data = await resp.json()

            embed = Embed(
                title="Random Dad Joke",
                description=f"{data["joke"]}\n\n-# [Permalink](https://icanhazdadjoke.com/j/{data['id']})\n-# Powered by [icanhazdadjoke.com](https://icanhazdadjoke.com/api)",
                colour=0x0279FD,
            )
            await ctx.response.send_message(embed=embed)
        except ClientResponseError as e:
            logging.warning(f"icanhazdadjoke API error: {e.status} {e.message}")
            await ctx.response.send_message(
                ":x: Could not retrieve dad joke from API."
            )
        except (ClientError, TimeoutError) as e:
            logging.error(f"Network error fetching quote: {e}")
            await ctx.response.send_message(
                ":x: Could not connect to the dad joke service."
            )
        except Exception:
            logging.exception("Unexpected error fetching dad joke.")
            await ctx.response.send_message(
                ":x: Something unexpected happened. Try again later."
            )

    @app_commands.command(
        name="dog-picture",
        description="Retrieves a dog picture from dog.ceo api.",
    )
    @app_commands.describe()
    async def dog_picture(
            self,
            ctx: commands.Context,
    ) -> None:
        """Retrieves a dog picture from dog.ceo api."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://dog.ceo/api/breeds/image/random") as resp:
                    resp.raise_for_status()
                    data = await resp.json()

            embed = Embed(
                title="Random Dog Picture",
                description=f"-# Powered by [dog.ceo](https://dog.ceo)", # Removed data["message"] from description
                colour=0x0279FD,
            )
            embed.set_image(url=data["message"]) # Set the image in the embed
            await ctx.response.send_message(embed=embed)
        except ClientResponseError as e:
            logging.warning(f"dog.ceo API error: {e.status} {e.message}") # Corrected API name in warning
            await ctx.response.send_message(
                ":x: Could not retrieve dog picture from API." # Corrected message
            )
        except (ClientError, TimeoutError) as e:
            logging.error(f"Network error fetching dog picture: {e}") # Corrected message
            await ctx.response.send_message(
                ":x: Could not connect to the dog picture service." # Corrected message
            )
        except Exception:
            logging.exception("Unexpected error fetching dog picture.") # Corrected message
            await ctx.response.send_message(
                ":x: Something unexpected happened. Try again later."
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Fun(bot))
