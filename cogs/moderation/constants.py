# cogs/moderation/constants.py
import discord
from discord.ext import commands
from discord.ext.commands import MemberConverter, UserConverter, Converter, BadArgument
from datetime import datetime, UTC, timedelta
from dateutil.relativedelta import relativedelta
import dateutil.parser
import arrow
from . import time
from typing import Union

# The user did not provide the following constants. I will use placeholders.
AMBIGUOUS_ARGUMENT_MSG = "Could not resolve '{argument}' to a user. Please use a mention or a user ID."
MAXIMUM_TIMEOUT_DAYS = timedelta(days=28)
TIMEOUT_CAP_MESSAGE = "The timeout duration for {0} was capped to 28 days."

def _is_an_unambiguous_user_argument(argument: str) -> bool:
    """Check if an argument is a mention or a user ID."""
    return argument.startswith("<@") or argument.isdigit()


class UnambiguousMember(MemberConverter):
    """
    Converts to a `discord.Member`, but only if a mention or userID is provided.

    Unlike the default `MemberConverter`, it doesn't allow conversion from a name or nickname.
    This is useful in cases where that lookup strategy would lead to too much ambiguity.
    """

    async def convert(self, ctx: commands.Context, argument: str) -> discord.Member:
        """Convert the `argument` to a `discord.Member`."""
        if _is_an_unambiguous_user_argument(argument):
            return await super().convert(ctx, argument)
        raise BadArgument(AMBIGUOUS_ARGUMENT_MSG.format(argument=argument))


class UnambiguousUser(UserConverter):
    """
    Converts to a `discord.User`, but only if a mention or userID is provided.

    Unlike the default `UserConverter`, it doesn't allow conversion from a name.
    This is useful in cases where that lookup strategy would lead to too much ambiguity.
    """

    async def convert(self, ctx: commands.Context, argument: str) -> discord.User:
        """Convert the `argument` to a `discord.User`."""
        if _is_an_unambiguous_user_argument(argument):
            return await super().convert(ctx, argument)
        raise BadArgument(AMBIGUOUS_ARGUMENT_MSG.format(argument=argument))




class DurationDelta(Converter):
    """Convert duration strings into dateutil.relativedelta.relativedelta objects."""

    async def convert(self, ctx: commands.Context, duration: str) -> relativedelta:
        """
        Converts a `duration` string to a relativedelta object.

        The converter supports the following symbols for each unit of time:
        - years: `Y`, `y`, `year`, `years`
        - months: `m`, `month`, `months`
        - weeks: `w`, `W`, `week`, `weeks`
        - days: `d`, `D`, `day`, `days`
        - hours: `H`, `h`, `hour`, `hours`
        - minutes: `M`, `minute`, `minutes`
        - seconds: `S`, `s`, `second`, `seconds`

        The units need to be provided in descending order of magnitude.
        """
        if not (delta := time.parse_duration_string(duration)):
            raise BadArgument(f"`{duration}` is not a valid duration string.")

        return delta


class ISODateTime(Converter):
    """Converts an ISO-8601 datetime string into a datetime.datetime."""

    async def convert(self, ctx: commands.Context, datetime_string: str) -> datetime:
        """
        Converts a ISO-8601 `datetime_string` into a `datetime.datetime` object.

        The converter is flexible in the formats it accepts, as it uses the `isoparse` method of
        `dateutil.parser`. In general, it accepts datetime strings that start with a date,
        optionally followed by a time. Specifying a timezone offset in the datetime string is
        supported, but the `datetime` object will be converted to UTC. If no timezone is specified, the datetime will
        be assumed to be in UTC already. In all cases, the returned object will have the UTC timezone.

        See: https://dateutil.readthedocs.io/en/stable/parser.html#dateutil.parser.isoparse

        Formats that are guaranteed to be valid by our tests are:

        - `YYYY-mm-ddTHH:MM:SSZ` | `YYYY-mm-dd HH:MM:SSZ`
        - `YYYY-mm-ddTHH:MM:SS±HH:MM` | `YYYY-mm-dd HH:MM:SS±HH:MM`
        - `YYYY-mm-ddTHH:MM:SS±HHMM` | `YYYY-mm-dd HH:MM:SS±HHMM`
        - `YYYY-mm-ddTHH:MM:SS±HH` | `YYYY-mm-dd HH:MM:SS±HH`
        - `YYYY-mm-ddTHH:MM:SS` | `YYYY-mm-dd HH:MM:SS`
        - `YYYY-mm-ddTHH:MM` | `YYYY-mm-dd HH:MM`
        - `YYYY-mm-dd`
        - `YYYY-mm`
        - `YYYY`

        Note: ISO-8601 specifies a `T` as the separator between the date and the time part of the
        datetime string. The converter accepts both a `T` and a single space character.
        """
        try:
            dt = dateutil.parser.isoparse(datetime_string)
        except ValueError:
            raise BadArgument(f"`{datetime_string}` is not a valid ISO-8601 datetime string")

        if dt.tzinfo:
            dt = dt.astimezone(UTC)
        else:  # Without a timezone, assume it represents UTC.
            dt = dt.replace(tzinfo=UTC)

        return dt


class Duration(DurationDelta):
    """Convert duration strings into UTC datetime.datetime objects."""

    async def convert(self, ctx: commands.Context, duration: str) -> datetime:
        """
        Converts a `duration` string to a datetime object that's `duration` in the future.

        The converter supports the same symbols for each unit of time as its parent class.
        """
        delta = await super().convert(ctx, duration)
        now = datetime.now(UTC)

        try:
            return now + delta
        except (ValueError, OverflowError):
            raise BadArgument(f"`{duration}` results in a datetime outside the supported range.")