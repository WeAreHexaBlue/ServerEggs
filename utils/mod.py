import os

import discord


def developer_guild() -> discord.Object | None:
    raw = os.getenv("DEVELOPER_GUILD_ID")

    if not raw:
        return None

    try:
        return discord.Object(id=int(raw))
    except ValueError:
        return None


async def is_global_mod(bot, user_id: int) -> bool:
    devguild = bot.get_guild(int(os.getenv("DEVELOPER_GUILD_ID")))

    if devguild is None:
        return False

    modrole = devguild.get_role(int(os.getenv("MOD_ROLE_ID")))

    if modrole is None:
        return False

    try:
        member = await devguild.fetch_member(user_id)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return False

    return any(role.id == modrole.id for role in member.roles)