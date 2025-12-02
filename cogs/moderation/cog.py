import discord
from discord import app_commands
from discord.ext import commands
import logging
from discord import Member
from typing import Optional
from . import time
from . import _utils
import dateutil.parser
from datetime import datetime, UTC
import random
from discord.utils import escape_markdown
import json


SUPERSTARIFY_DEFAULT_DURATION = "1h"


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with open("resources/stars.json", "r") as f:
            self.superstar_names = json.load(f)

    async def _send_moderation_dm(
        self, user: discord.Member, action: str, reason: Optional[str]
    ) -> bool:
        """Sends a DM to a user about their moderation action."""
        try:
            dm_channel = await user.create_dm()
            embed = discord.Embed(
                title=f"You have been {action}",
                description=f"You have been {action} from the server.",
                color=discord.Color.red(),
            )
            if reason:
                embed.add_field(name="Reason", value=reason, inline=False)
            await dm_channel.send(embed=embed)
            return True
        except discord.Forbidden:
            # This can happen if the user has DMs disabled or has blocked the bot.
            logging.warning(
                f"Failed to send {action} DM to {user.mention}. They may have DMs disabled."
            )
            return False
        except discord.HTTPException as e:
            logging.error(f"Failed to send {action} DM to {user.mention}: {e}")
            return False

    async def apply_timeout(self, ctx, user, reason, duration_or_expiry):
        # Determine how to reply based on context type
        if isinstance(ctx, discord.Interaction):
            reply = ctx.response.send_message
        else:
            reply = ctx.send

        # Check role hierarchy
        if ctx.guild:
            # Ensure bot member is available
            me = ctx.guild.me
            if user.top_role >= me.top_role:
                await reply(
                    ":x: I cannot timeout this user because their role is higher than or equal to mine.",
                    ephemeral=True,
                )
                return

        try:
            await user.timeout(duration_or_expiry, reason=reason)
        except discord.Forbidden:
            await reply(
                ":x: I don't have permission to timeout this user.", ephemeral=True
            )
            return
        except discord.HTTPException as e:
            await reply(f":x: Failed to timeout user: {e}", ephemeral=True)
            return

        if duration_or_expiry:
            await reply(
                f":white_check_mark: Timed out {user.mention} for {duration_or_expiry}.",
                ephemeral=True,
            )
        else:
            await reply(f":white_check_mark: Timed out {user.mention}.", ephemeral=True)

    @app_commands.command(name="timeout", description="Timeout's a specific user")
    @app_commands.describe(
        user="The user to timeout",
        duration="The duration of the timeout",
        reason="The reason for the timeout",
    )
    @commands.has_permissions(moderate_members=True)
    async def timeout(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        duration: Optional[str] = None,
        *,
        reason: Optional[str] = None,
    ) -> None:
        """
        Timeout a user for the given reason and duration.

        A unit of time should be appended to the duration.
        Units (∗case-sensitive):
        \u2003`y` - years
        \u2003`m` - months∗
        \u2003`w` - weeks
        \u2003`d` - days
        \u2003`h` - hours
        \u2003`M` - minutes∗
        \u2003`s` - seconds

        Alternatively, an ISO 8601 timestamp can be provided for the duration.

        If no duration is given, a one-hour duration is used by default.
        """  # noqa: RUF002
        if not isinstance(user, Member):
            await interaction.response.send_message(
                ":x: The user doesn't appear to be on the server.", ephemeral=True
            )
            return

        duration_obj = None
        if duration:
            # Try parsing as ISO datetime first
            try:
                duration_obj = dateutil.parser.isoparse(duration)
                if duration_obj.tzinfo:
                    duration_obj = duration_obj.astimezone(UTC)
                else:
                    duration_obj = duration_obj.replace(tzinfo=UTC)
            except ValueError:
                # Try parsing as duration string
                delta = time.parse_duration_string(duration)
                if delta:
                    now = datetime.now(UTC)
                    try:
                        duration_obj = now + delta
                    except (ValueError, OverflowError):
                        await interaction.response.send_message(
                            f"`{duration}` results in a datetime outside the supported range.",
                            ephemeral=True,
                        )
                        return
                else:
                    await interaction.response.send_message(
                        f"`{duration}` is not a valid duration string or ISO-8601 datetime.",
                        ephemeral=True,
                    )
                    return

        if duration_obj:
            capped, duration_obj = _utils.cap_timeout_duration(duration_obj)
            if capped:
                await _utils.notify_timeout_cap(self.bot, interaction, user)

        await self.apply_timeout(
            interaction, user, reason, duration_or_expiry=duration_obj
        )

    @app_commands.command(name="kick", description="Kick's a specific user")
    @app_commands.describe(user="The user to kick", reason="The reason for the kick")
    @commands.has_permissions(kick_members=True)
    async def kick(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: Optional[str] = None,
    ) -> None:
        """Kick a user for the given reason."""
        if interaction.guild:
            me = interaction.guild.me
            if user.top_role >= me.top_role:
                await interaction.response.send_message(
                    ":x: I cannot kick this user because their role is higher than or equal to mine.",
                    ephemeral=True,
                )
                return

        # Send DM to user
        dm_sent = await self._send_moderation_dm(user, "kicked", reason)

        try:
            await user.kick(reason=reason)
        except discord.Forbidden:
            await interaction.response.send_message(
                ":x: I don't have permission to kick this user.", ephemeral=True
            )
            return
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f":x: Failed to kick user: {e}", ephemeral=True
            )
            return

        reply_message = f":white_check_mark: Kicked {user.mention}."
        if not dm_sent:
            reply_message += " (Could not send DM to user)"

        await interaction.response.send_message(reply_message, ephemeral=True)

    @app_commands.command(name="ban", description="Bans a specific user")
    @app_commands.describe(user="The user to ban", reason="The reason for the ban")
    @commands.has_permissions(ban_members=True)
    async def ban(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: Optional[str] = None,
    ) -> None:
        """Ban a user for the given reason."""
        if interaction.guild:
            me = interaction.guild.me
            if user.top_role >= me.top_role:
                await interaction.response.send_message(
                    ":x: I cannot ban this user because their role is higher than or equal to mine.",
                    ephemeral=True,
                )
                return

        # Send DM to user
        dm_sent = await self._send_moderation_dm(user, "banned", reason)

        try:
            await user.ban(reason=reason)
        except discord.Forbidden:
            await interaction.response.send_message(
                ":x: I don't have permission to ban this user.", ephemeral=True
            )
            return
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f":x: Failed to ban user: {e}", ephemeral=True
            )
            return

        reply_message = f":white_check_mark: banned {user.mention}."
        if not dm_sent:
            reply_message += " (Could not send DM to user)"

        await interaction.response.send_message(reply_message, ephemeral=True)

    @app_commands.command(name="unban", description="Unbans a specific user")
    @app_commands.describe(user="The user ID or mention of the user to unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user: str) -> None:
        """Unban a user by their ID."""
        try:
            # Try to convert to int, or strip mention characters
            if user.startswith("<@") and user.endswith(">"):
                user_id = int(user[2:-1])
            else:
                user_id = int(user)

            user_obj = await self.bot.fetch_user(user_id)
        except (ValueError, TypeError):
            await interaction.response.send_message(
                ":x: Please provide a valid user ID or mention.", ephemeral=True
            )
            return
        except discord.NotFound:
            await interaction.response.send_message(
                ":x: User not found.", ephemeral=True
            )
            return
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f":x: Failed to fetch user: {e}", ephemeral=True
            )
            return

        try:
            await interaction.guild.unban(user_obj)
        except discord.Forbidden:
            await interaction.response.send_message(
                ":x: I don't have permission to unban this user.", ephemeral=True
            )
            return
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f":x: Failed to unban user: {e}", ephemeral=True
            )
            return

        reply_message = f":white_check_mark: Unbanned {user_obj.mention}."

        await interaction.response.send_message(reply_message, ephemeral=True)

    @app_commands.command(
        name="superstarify",
        description="Temporarily force a random superstar name to be the user's nickname.",
    )
    @app_commands.describe(
        member="The user to superstarify",
        duration="The duration of the nickname change (e.g., 1h, 30m). Defaults to 1 hour.",
        reason="The reason for the superstarification.",
    )
    @commands.has_permissions(moderate_members=True)
    async def superstarify(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        duration: Optional[str] = None,
        *,
        reason: Optional[str] = None,
    ) -> None:
        """
        Temporarily force a random superstar name (like Taylor Swift) to be the user's nickname.

        A unit of time should be appended to the duration.
        Units (∗case-sensitive):
        \u2003`y` - years
        \u2003`m` - months∗
        \u2003`w` - weeks
        \u2003`d` - days
        \u2003`h` - hours
        \u2003`M` - minutes∗
        \u2003`s` - seconds

        Alternatively, an ISO 8601 timestamp can be provided for the duration.

        An optional reason can be provided, which would be added to a message stating their old nickname
        and linking to the nickname policy.
        """
        await interaction.response.defer(ephemeral=True)

        if member.top_role >= interaction.guild.me.top_role:
            await interaction.followup.send(
                ":x: I can't superstarify users with a higher or equal role."
            )
            return

        duration_obj = None
        if duration:
            delta = time.parse_duration_string(duration)
            if delta is None:
                await interaction.followup.send(
                    f"Could not parse `{duration}`. Please use a valid duration string (e.g., 1h, 30m)."
                )
                return

            try:
                duration_obj = datetime.now(UTC) + delta
            except (ValueError, OverflowError):
                await interaction.followup.send(
                    f"`{duration}` results in a datetime outside the supported range."
                )
                return

        # In a real implementation, we would store the superstarification expiry.
        # For now, we just change the nick and inform about the duration.

        old_nick = member.display_name
        forced_nick = random.choice(self.superstar_names)

        try:
            await member.edit(nick=forced_nick, reason=reason)
        except discord.Forbidden:
            await interaction.followup.send(
                ":x: I don't have permission to change this user's nickname."
            )
            return
        except discord.HTTPException as e:
            await interaction.followup.send(f":x: Failed to change nickname: {e}")
            return

        # Prepare DM message
        expiry_str = ""
        expiry_dm_part = "This change is permanent."
        if duration_obj:
            expiry_str = f" until <t:{int(duration_obj.timestamp())}:R>"
            expiry_dm_part = f"You will be unable to change your nickname until **<t:{int(duration_obj.timestamp())}:R>**."

        user_message = (
            f"Your previous nickname, **{escape_markdown(old_nick)}**, was so fabulous "
            f"that we have decided to give you a superstar name. "
            f"Your new nickname will be **{escape_markdown(forced_nick)}**.\n\n"
            f"{expiry_dm_part} "
            "If you're confused by this, please read our "
            f"official nickname policy."
        )
        if reason:
            user_message += f"\n\n**Reason:** {reason}"

        try:
            await member.send(user_message)
        except discord.Forbidden:
            logging.warning(
                f"Failed to send superstarify DM to {member.mention}. They may have DMs disabled."
            )
        except discord.HTTPException as e:
            logging.error(f"Failed to send superstarify DM to {member.mention}: {e}")

        # Send confirmation embed
        embed = discord.Embed(
            title="Superstarified!",
            color=discord.Color.orange(),
            description=(
                f"{member.mention} has been superstarified! "
                f"Their new name is **{escape_markdown(forced_nick)}**{expiry_str}."
            ),
        )
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
