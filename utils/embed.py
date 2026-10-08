import discord
from discord.ext import commands

from schema import Rating

from . import attach, misc
from .i18n import BRAND, brand_values, icon_url

HEADER_EMOJI = BRAND["emojis"]["header"]
FOOTER_EMOJI = BRAND["emojis"]["footer"]

CV2_TEXT_LIMIT = 4000

def egg_title(egg, base: str) -> str:
    if egg.rating == Rating.EXPLICIT:
        marker = "🌶️"
    elif egg.rating == Rating.QUESTIONABLE:
        marker = "⚠️"
    else:
        marker = ""

    return base + (" ⭐" if egg.secret else " ") + marker

def brand_embed(e: discord.Embed, lines: dict | None = None):
    if lines is None:
        lines = {
            "embed": {
                "author": BRAND["name"],
                "footer": brand_values()["footer"]
            }
        }

    e.set_author(name=lines["embed"]["author"], icon_url=icon_url("author"))
    e.set_footer(text=lines["embed"]["footer"], icon_url=icon_url("footer"))

def get_egg_color(egg):
    color = discord.Color.blurple()

    if egg.secret and egg.rating == Rating.EXPLICIT:
        color = discord.Color.fuchsia()
    elif egg.secret:
        color = discord.Color.gold()
    elif egg.rating == Rating.EXPLICIT:
        color = discord.Color.red()
    elif egg.rating == Rating.QUESTIONABLE:
        color = discord.Color.orange()

    return color

def brand_header(lines: dict | None = None, title: str = "") -> str:
    author = lines["embed"]["author"] if lines else BRAND["name"]

    prefix = f"{HEADER_EMOJI} " if HEADER_EMOJI else ""
    header = f"{prefix}**{author}**"
    return f"{header}\n# {title}" if title else header

def brand_footer(lines: dict | None = None) -> str:
    footer = lines["embed"]["footer"] if lines else brand_values()["footer"]

    prefix = f"{FOOTER_EMOJI}  " if FOOTER_EMOJI else ""
    return f"-# {prefix}{footer}"

def fit_text(description: str | None, *fixed: str) -> str | None:
    if not description:
        return None

    budget = max(CV2_TEXT_LIMIT - sum(len(text) for text in fixed) - len(fixed), 0)

    if len(description) <= budget:
        return description

    return description[:budget] + "…"

def egg_container(color: discord.Color, body: list[str], media=None, lines: dict | None = None) -> discord.ui.Container:
    container = discord.ui.Container(accent_color=color)

    for text in body:
        container.add_item(discord.ui.TextDisplay(text))

    if media is not None:
        container.add_item(discord.ui.MediaGallery(media))

    container.add_item(discord.ui.TextDisplay(brand_footer(lines)))

    return container

def egg_creator_block(myloc: dict, egg, creator, *, public = False, include_id = False) -> str:
    if creator is not None:
        value = misc.format_user_display(creator, username=creator.name if public or include_id else None, user_id=creator.id if include_id else None)
    else:
        value = myloc["unknown_creator"].format(user_id=egg.creator_id or "")

    return f"### {myloc["creator"]}\n{value}"

def egg_origin_block(myloc: dict, egg, origin) -> str:
    if origin is None:
        value = myloc["unknown_origin"].format(guild_id=egg.origin_id or "")
    else:
        parts = [f"**{myloc["origin_name"]}**: {discord.utils.escape_markdown(origin.name)}"]

        if egg.origin.description is not None:
            parts.append(f"**{myloc["origin_desc"]}**: {egg.origin.description}")

        value = "\n".join(parts)

    return f"### {myloc["origin"]}\n{value}"

async def get_egg_layout(
    bot: commands.Bot,
    lines: dict,
    egg,
    creator: discord.User = None,
    collected = False,
    include_id = False,
    *,
    title: str | None = None,
    created: bool = False
) -> tuple[discord.ui.Container, discord.File | None, str | None, str | None]:
    myloc = bot.get_lines("eggs/send", lines)

    if creator is None:
        creator = await misc.get_or_fetch_user(bot, egg.creator_id)

    origin = bot.get_guild(egg.origin_id) if egg.origin_id else None

    media, sfile, extrafile, extralink = attach.get_media(egg)

    collections = await egg.collectors.all().count()
    wins = await egg.battle_wins.all().count()

    fields = [
        egg_creator_block(myloc, egg, creator, public=egg.creator_id is not None and egg.creator.public, include_id=include_id)
    ]

    if not created:
        fields.append(egg_origin_block(myloc, egg, origin))
        fields.append(f"### {myloc["collection_status"]}\n{myloc["collected"].format(egg_id=egg.id, count=collections) if collected else myloc["collections"].format(egg_id=egg.id, count=collections)}")
        fields.append(f"### {myloc["battle_wins"]}\n{myloc["wins"].format(egg_id=egg.id, count=wins)}")

    if title is None:
        title = egg_title(egg, myloc["eggn"].format(egg_id=egg.id))

    header = brand_header(lines, title)
    footer = brand_footer(lines)

    description = fit_text(egg.text, header, footer, *fields)

    body = [f"{header}\n\n{description}" if description else header, *fields]

    return egg_container(get_egg_color(egg), body, media, lines=lines), sfile, extrafile, extralink
