import discord
from discord import app_commands as app

from .i18n import FALLBACK_LANG, pick_locale


class UITranslator(app.Translator):
    def __init__(self, bot):
        self.bot = bot

    async def translate(self, line: app.locale_str, locale: discord.Locale, ctx: app.TranslationContext) -> str | None:
        lines = pick_locale(self.bot.locales, locale.value)

        return lines.get(line.message, self.bot.locales[FALLBACK_LANG].get(line.message))