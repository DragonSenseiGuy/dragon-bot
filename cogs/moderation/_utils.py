# cogs/moderation/_utils.py
import datetime
from typing import Union
from dateutil.relativedelta import relativedelta
import arrow
import discord
from discord.ext.commands import Context
from .constants import MAXIMUM_TIMEOUT_DAYS, TIMEOUT_CAP_MESSAGE


# The user did not provide the implementation for is_mod_channel and Channels.
# I will use placeholders.
def is_mod_channel(channel):
    return "mod" in channel.name


class Channels:
    mods = 1234567890  # Placeholder


def cap_timeout_duration(
    duration: Union[datetime.datetime, relativedelta],
) -> tuple[bool, datetime.datetime]:
    """Cap the duration of a duration to Discord's limit."""
    now = arrow.utcnow()
    capped = False
    if isinstance(duration, relativedelta):
        duration += now

    if duration > now + MAXIMUM_TIMEOUT_DAYS:
        duration = (
            now + MAXIMUM_TIMEOUT_DAYS - datetime.timedelta(minutes=1)
        )  # Duration cap is exclusive.
        capped = True
    elif duration > now + MAXIMUM_TIMEOUT_DAYS - datetime.timedelta(minutes=1):
        # Duration cap is exclusive. This is to still allow specifying "28d".
        duration -= datetime.timedelta(minutes=1)
    return capped, duration


async def notify_timeout_cap(
    bot: discord.Client, ctx: Union[Context, discord.Interaction], user: discord.Member
) -> None:
    """Notify moderators about a timeout duration being capped."""
    cap_message_for_user = TIMEOUT_CAP_MESSAGE.format(user.mention)

    # Determine author and reply method based on context type
    if isinstance(ctx, discord.Interaction):
        author = ctx.user
        reply = ctx.response.send_message
    else:
        author = ctx.author
        reply = ctx.reply

    if is_mod_channel(ctx.channel):
        if isinstance(ctx, discord.Interaction):
            await reply(f":warning: {cap_message_for_user}", ephemeral=True)
        else:
            await reply(f":warning: {cap_message_for_user}")
    else:
        # For mod channel notification, we need to ensure the channel exists
        mod_channel = bot.get_channel(Channels.mods)
        if mod_channel:
            await mod_channel.send(f":warning: {author.mention} {cap_message_for_user}")
