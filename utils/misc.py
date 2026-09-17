import os

import discord
from discord.ext import commands

from schema import Rating, User, default_ratings

from . import sku


def dev_role(bot: commands.Bot) -> discord.Role | None:
    guild_id = int(os.getenv("DEVELOPER_GUILD_ID"))
    role_id = int(os.getenv("DEVELOPER_ROLE_ID"))

    if not guild_id or not role_id:
        return None

    devguild = bot.get_guild(guild_id)

    if devguild is None:
        return None

    return devguild.get_role(role_id)

def has_role(member, role_id: int) -> bool:
    return any(r.id == role_id for r in member.roles)

async def is_dev_user(bot: commands.Bot, user_id: int) -> bool:
    role = dev_role(bot)

    if role is None:
        return False

    member = role.guild.get_member(user_id)

    if member is None:
        try:
            member = await role.guild.fetch_member(user_id)
        except discord.NotFound:
            return False
        except (discord.Forbidden, discord.HTTPException):
            return False

    return has_role(member, role.id)

async def fetch_dev_ids(bot: commands.Bot) -> set[int]:
    role = dev_role(bot)

    if role is None:
        return set()

    if role.members:
        return {m.id for m in role.members}

    ids = set()

    try:
        async for member in role.guild.fetch_members(limit=None):
            if has_role(member, role.id):
                ids.add(member.id)
    except (discord.Forbidden, discord.HTTPException):
        pass

    return ids

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

async def get_or_fetch_user(bot: commands.Bot, user_id: int):
    user = bot.get_user(user_id)

    if user is not None:
        return user

    try:
        return await bot.fetch_user(user_id)
    except (discord.NotFound, discord.HTTPException):
        return None

async def beg(myloc: dict, ctx: discord.Interaction, user: User):
    is_supporter = await sku.is_ctx_supporter(ctx)

    line = myloc["beg"] if not is_supporter else myloc["beg_supporter"]

    count = await user.eggs.all().count()
    if (is_supporter and count % 90 == 0) or (not is_supporter and count % 20 == 0):
        try:
            await ctx.user.send(line.format(ctx.user.display_name))
        except discord.HTTPException:
            pass