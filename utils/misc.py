import discord
from discord.ext import commands

from schema import Rating, User, default_ratings

from . import sku


def channel_is_nsfw(channel) -> bool:
    return bool(channel and hasattr(channel, "is_nsfw") and channel.is_nsfw())

def coerce_rating(value):
    if value is None or isinstance(value, Rating):
        return value

    return Rating(value)

def channel_ratings(guild, channel) -> list[Rating]:
    default = default_ratings()

    key = "nsfw" if channel_is_nsfw(channel) else "normal"

    if guild is None:
        return default[key]

    stored = getattr(guild, "ratings", None) or {}

    return stored.get(key, default[key])

async def get_or_fetch_user(bot: commands.Bot, user_id: int | None):
    if not user_id:
        return None

    user = bot.get_user(user_id)

    if user is not None:
        return user

    try:
        return await bot.fetch_user(user_id)
    except (discord.NotFound, discord.HTTPException):
        return None

def format_user_display(user, *, username: str | None = None, user_id: int | None = None) -> str:
    base = f"**{discord.utils.escape_markdown(user.display_name)}**"

    detail = discord.utils.escape_markdown(username) if username else ""
    if user_id is not None:
        detail = f"{detail}, {user_id}" if detail else str(user_id)

    return f"{base} ({detail})" if detail else base

async def beg(myloc: dict, ctx: discord.Interaction, user: User):
    is_supporter = await sku.is_ctx_supporter(ctx)

    line = myloc["beg"] if not is_supporter else myloc["beg_supporter"]

    count = await user.eggs.all().count()
    if (is_supporter and count % 90 == 0) or (not is_supporter and count % 20 == 0):
        try:
            await ctx.user.send(line.format(user=ctx.user.display_name))
        except discord.HTTPException:
            pass