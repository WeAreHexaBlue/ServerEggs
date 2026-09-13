import datetime
import random

import discord
from discord.ext import commands

from schema import Battle, BattleStatus, BattleVote, Egg, Guild, User

from . import attach, embed, misc


async def fight_pool_ids(user: User) -> list[int]:
    created = await Egg.filter(creator=user).values_list("id", flat=True)
    collected = await Egg.filter(collectors=user).values_list("id", flat=True)

    return list(dict.fromkeys(created + collected))

async def random_fight_egg(user: User, guild: Guild | None = None, channel=None, *, exclude_ids=None):
    ids = await fight_pool_ids(user)

    if exclude_ids:
        ids = [egg_id for egg_id in ids if egg_id not in exclude_ids]

    if not ids:
        return None

    query = Egg.filter(id__in=ids).filter(rating__in=misc.channel_ratings(guild, channel))

    if guild:
        filtered = await Egg.filter(filtered_in__id=guild.id).values_list("id", flat=True)
        if filtered:
            query = query.exclude(id__in=filtered)

        if not guild.allow_ext_lang:
            query = query.filter(lang=guild.lang)

    count = await query.count()

    if count == 0:
        return None

    return await query.offset(random.randint(0, count - 1)).first()

async def battle_side(bot: commands.Bot, lines: dict, myloc: dict, egg, side: str) -> dict:
    creator = await misc.get_or_fetch_user(bot, egg.creator_id)

    media, sfile, extrafile, extralink = attach.get_media(egg)

    header = embed.brand_header(lines, embed.egg_title(egg, myloc["eggn"].format(egg.id, side)))
    footer = embed.brand_footer(lines)

    description = embed.fit_text(egg.text, header, footer)

    body = [f"{header}\n\n{description}" if description else header]

    if creator is not None:
        value = f"**{discord.utils.escape_markdown(creator.display_name)}** ({discord.utils.escape_markdown(creator.name)})"
    else:
        value = myloc["unknown_creator"].format(egg.creator_id)

    body.append(f"### {myloc["creator"]}\n{value}")

    container = embed.egg_container(embed.get_egg_color(egg), body, media, lines=lines)

    return {
        "container": container,
        "sfile": sfile,
        "vfile": extrafile,
        "vlink": extralink
    }

async def build_battle_message(bot: commands.Bot, lines: dict, myloc: dict, egg_a, egg_b) -> list[dict]:
    return [await battle_side(bot, lines, myloc, egg_a, "A"), await battle_side(bot, lines, myloc, egg_b, "B")]

async def count_votes(battle) -> tuple[int, int]:
    rows = await BattleVote.filter(battle=battle).values("choice")

    count_a = sum(1 for row in rows if row["choice"] == 0)
    count_b = len(rows) - count_a

    return count_a, count_b

def result_layout(lines: dict, myloc: dict, winner, count_a: int, count_b: int) -> discord.ui.LayoutView:
    if winner is not None:
        color = discord.Color.gold()
        title = myloc["result_win_title"].format(winner.id)
        description = myloc["result_win"].format(winner.id, max(count_a, count_b), min(count_a, count_b))
    else:
        color = discord.Color.blurple()
        title = myloc["result_tie_title"]
        description = myloc["result_tie"].format(count_a, count_b)

    body = [f"{embed.brand_header(lines, title)}\n\n{description}"]

    view = discord.ui.LayoutView(timeout=None)
    view.add_item(embed.egg_container(color, body, lines=lines))

    return view

async def finalize_battle(bot: commands.Bot, battle):
    guild = await battle.guild
    locale = bot.locales.get(guild.lang if guild else "", bot.locales["en"])
    lines = locale["lines"]
    myloc = bot.get_lines("battles/battle", lines)

    count_a, count_b = await count_votes(battle)

    winner = None
    if count_a > count_b: winner_id = battle.egg_a_id
    elif count_b > count_a: winner_id = battle.egg_b_id
    else: winner_id = None

    if winner_id is not None:
        winner = await Egg.get_or_none(id=winner_id)

    winner_user_id = None
    if winner_id == battle.egg_a_id: winner_user_id = battle.user_a_id
    elif winner_id == battle.egg_b_id: winner_user_id = battle.user_b_id

    battle.winner_id = winner_id
    battle.winner_user_id = winner_user_id
    battle.status = BattleStatus.FINISHED
    await battle.save(update_fields=["winner_id", "winner_user_id", "status"])

    if battle.channel_id is None or battle.message_id is None:
        return

    channel = bot.get_channel(battle.channel_id)
    if channel is None:
        return

    try: message = await channel.fetch_message(battle.message_id)
    except discord.HTTPException: return

    try: await message.edit(view=result_layout(lines, myloc, winner, count_a, count_b))
    except discord.HTTPException: pass

    try: await message.reply(content=myloc["finished"])
    except discord.HTTPException: pass

FINALIZE_BATCH_LIMIT = 10

async def finalize_due_battles(bot: commands.Bot):
    due = await Battle.filter(status=BattleStatus.OPEN, ends_at__lte=datetime.datetime.now(datetime.timezone.utc)).limit(FINALIZE_BATCH_LIMIT + 1)

    if len(due) > FINALIZE_BATCH_LIMIT:
        print(f"WARN: {len(due)}+ battles due; finalizing first {FINALIZE_BATCH_LIMIT}, remainder next tick.")
        due = due[:FINALIZE_BATCH_LIMIT]

    for battle in due:
        await finalize_battle(bot, battle)