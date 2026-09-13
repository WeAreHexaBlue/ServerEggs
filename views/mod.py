import discord
from discord.ext import commands

import utils
from schema import Egg, Report

from .base import (
    ExtraAttachmentButton,
    LangModal,
    RatingModal,
    action_button,
    text_view,
)


class ReportActions(discord.ui.LayoutView):
    def __init__(self, bot: commands.Bot, report, reporter, intro: str, container: discord.ui.Container, file=None, link=None, lines: dict | None = None):
        super().__init__(timeout=None)

        self.bot = bot
        self.report = report
        self.reporter = reporter
        self.lines = lines

        self.add_item(discord.ui.TextDisplay(intro))
        self.add_item(container)

        if file or link:
            self.add_item(discord.ui.ActionRow(ExtraAttachmentButton(
                bot.get_lines("common", lines or {})["show_extra_attachment"] if lines else "Show Extra Attachment",
                style=discord.ButtonStyle.primary,
                file=file,
                link=link
            )))

        self.add_item(discord.ui.ActionRow(
            action_button("Ignore", discord.ButtonStyle.secondary, self.ignore),
            action_button("Change Rating", discord.ButtonStyle.primary, self.change_rating),
            action_button("Change Language", discord.ButtonStyle.primary, self.change_language),
            action_button("Delete", discord.ButtonStyle.danger, self.delete),
            action_button("Delete and Ban", discord.ButtonStyle.danger, self.delete_ban),
        ))

    async def delete_reports(self, ctx: discord.Interaction, action: str, egg: Egg | int):
        all_reports = await egg.reports.all() if isinstance(egg, Egg) else await Report.filter(egg__id=egg).all()

        for report in all_reports:
            try:
                msg = ctx.channel.get_partial_message(report.log_message_id)
                await msg.edit(view=text_view(self.resolved(action, egg)))
            except discord.HTTPException:
                pass

            await report.delete()

    def resolved(self, action: str, egg_id):
        return f"**Resolved** report `{self.report.id}`.\n**Reporter**: `{self.reporter.id}`\n**Egg**: `{egg_id}`\n**Reason**: {self.report.reason}\n**Action**: {action}"

    async def interaction_check(self, ctx: discord.Interaction):
        if not await utils.is_global_mod(self.bot, ctx.user.id):
            await ctx.response.send_message("Not allowed.", ephemeral=True)
            return False

        return True

    async def ignore(self, ctx: discord.Interaction):
        await ctx.response.defer()

        egg = await self.report.egg

        await self.delete_reports(ctx, "Ignore", egg.id)

    async def change_rating(self, ctx: discord.Interaction):
        egg = await self.report.egg

        await ctx.response.send_modal(RatingModal(self.bot.get_lines("rating", self.lines), egg, after_set=self.after_rating))

    async def after_rating(self, ctx: discord.Interaction, egg: Egg, rating):
        await self.delete_reports(ctx, f"Change Rating to `{rating.value}`", egg.id)

    async def change_language(self, ctx: discord.Interaction):
        egg = await self.report.egg

        await ctx.response.send_modal(LangModal(self.bot, self.bot.get_lines("lang", self.lines), egg, after_set=self.after_language))

    async def after_language(self, ctx: discord.Interaction, egg: Egg, lang):
        await self.delete_reports(ctx, f"Change Language to `{lang}`", egg.id)

    async def delete(self, ctx: discord.Interaction):
        await ctx.response.defer()

        egg = await self.report.egg

        await self.delete_reports(ctx, "Delete", egg.id)
        await utils.egg_delete(egg)

    async def delete_ban(self, ctx: discord.Interaction):
        await ctx.response.defer()

        egg = await self.report.egg
        creator = await egg.creator

        action = f"Delete and Ban User `{creator.id}`"

        creator.banned = True
        await creator.save(update_fields=["banned"])

        await self.delete_reports(ctx, action, egg.id)
        await utils.egg_delete(egg)
