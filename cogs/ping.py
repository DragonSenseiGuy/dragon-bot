import discord
from discord import app_commands, Embed
from discord.ext import commands
import arrow

DESCRIPTIONS = (
    "Command processing time",
    "Discord API latency"
)

class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Gets the ping of the bot.")
    async def ping(self, interaction: discord.Interaction) -> None:
        """Gets the ping of the bot."""
        interaction_creation_time = discord.utils.snowflake_time(interaction.id)
        bot_ping = (arrow.utcnow() - interaction_creation_time).total_seconds() * 1000

        bot_ping = f"{bot_ping:.3f} ms"

        # Discord Protocol latency return value is in seconds, must be multiplied by 1000 to get milliseconds.
        discord_ping = f"{self.bot.latency * 1000:.3f} ms"

        embed = Embed(title="🏓 Pong!")

        for desc, latency in zip(DESCRIPTIONS, [bot_ping, discord_ping], strict=True):
            embed.add_field(name=desc, value=latency, inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Ping(bot))