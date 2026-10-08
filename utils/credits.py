from discord.ext import commands

from . import misc

CREDITS = {
    "programming": [450678229192278036],
    "localization": {
        "de": [512242962407882752],
        "en": [450678229192278036],
        "es": [643458237991092226, 966753405219504159],
        "it": [450678229192278036],
        "nl": [391262221457424405],
    },
}

async def credit_name(bot: commands.Bot, uid: int) -> str | None:
    user = await misc.get_or_fetch_user(bot, uid)

    if user is None:
        return None

    return misc.format_user_display(user, username=user.name)

async def render_credits(bot: commands.Bot, roles: dict, locales: dict) -> str:
    sections = []

    for role, entries in CREDITS.items():
        lines = [f"**__{roles.get(role) or role.capitalize()}__**:"]

        if isinstance(entries, dict):
            for code, uids in entries.items():
                users = [name for uid in uids if (name := await credit_name(bot, uid))]

                if not users:
                    continue

                lang = locales.get(code, {}).get("language_name", code)
                lines.append(f"- ***{lang}***: {', '.join(users)}")
        else:
            for uid in entries:
                if name := await credit_name(bot, uid):
                    lines.append(f"- {name}")

        sections.append("\n".join(lines))

    return "\n".join(sections)