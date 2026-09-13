import discord
from discord.ext import commands

import utils

from .base import (
    ExtraAttachmentButton,
    LangModal,
    RatingModal,
    action_button,
    text_view,
)
from .eggs import ReportEgg


class ModLogActions(discord.ui.LayoutView):
    def __init__(self, bot: commands.Bot, lines: dict, egg, formats: tuple, container: discord.ui.Container, file=None, link=None):
        super().__init__(timeout=None)

        self.bot = bot
        self.lines = lines
        self.myloc = bot.get_lines("log", lines)
        self.egg = egg
        self.formats = formats

        self.add_item(discord.ui.TextDisplay(self.myloc["log"].format(*self.formats)))
        self.add_item(container)

        if file or link:
            self.add_item(discord.ui.ActionRow(ExtraAttachmentButton(
                self.myloc["show_extra_attachment"],
                style=discord.ButtonStyle.primary,
                file=file,
                link=link
            )))

        self.add_item(discord.ui.ActionRow(
            action_button(self.myloc["change_rating"], discord.ButtonStyle.primary, self.change_rating),
            action_button(self.myloc["change_lang"], discord.ButtonStyle.primary, self.change_language),
            action_button(self.myloc["delete"], discord.ButtonStyle.danger, self.delete),
            action_button(self.myloc["report"], discord.ButtonStyle.danger, self.report),
        ))

    async def change_rating(self, ctx: discord.Interaction):
        await ctx.response.send_modal(RatingModal(self.bot.get_lines("rating", self.lines), self.egg))

    async def change_language(self, ctx: discord.Interaction):
        await ctx.response.send_modal(LangModal(self.bot, self.bot.get_lines("lang", self.lines), self.egg))

    async def delete(self, ctx: discord.Interaction):
        await ctx.response.defer(ephemeral=True)

        await ctx.edit_original_response(attachments=[], view=text_view(self.myloc["afterdel"].format(*self.formats)))

        await ctx.followup.send(self.myloc["deleted"].format(self.egg.id), ephemeral=True)
        await utils.egg_delete(self.egg)

    async def report(self, ctx: discord.Interaction):
        await ctx.response.send_modal(ReportEgg(self.bot, self.lines, self.egg, False))
