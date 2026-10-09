import os

import discord
from discord.ext import commands

import views

from . import embed


async def log_error(bot: commands.Bot | None, message: str) -> None:
    if bot is None:
        print(message)
        return

    try:
        logch_id = int(os.getenv("DEVELOPER_LOG_CHANNEL") or 0)
    except ValueError:
        return

    if not logch_id:
        return

    logch = bot.get_channel(logch_id)
    if logch is None:
        return

    try:
        await logch.send(f"⚠️ {message}")
    except discord.HTTPException:
        pass


async def log_egg(bot: commands.Bot, lines: dict, guild, egg, creator: discord.User, actor: discord.User, edit: bool = False):
    myloc = bot.get_lines("eggs/create_edit", lines)

    logch = bot.get_channel(guild.logch)

    if not logch: return

    container, sfile, vfile, vlink = await embed.get_egg_layout(bot, lines, egg, creator)

    await logch.send(
        file=sfile or discord.utils.MISSING,
        view=views.ModLogActions(
            bot, lines, egg,
            {
                "actor": discord.utils.escape_markdown(actor.display_name),
                "username": discord.utils.escape_markdown(actor.name),
                "action": myloc["edited"] if edit else myloc["created"],
                "egg_id": egg.id
            },
            container, vfile, vlink
        )
    )