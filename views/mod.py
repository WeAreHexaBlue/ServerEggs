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
    def __init__(self, bot: commands.Bot, report, reporter, intro: str, container: discord.ui.Container, file=None, link=None):
        super().__init__(timeout=None)

        self.bot = bot
        self.report = report
        self.reporter = reporter

        self.add_item(discord.ui.TextDisplay(intro))
        self.add_item(container)

        if file or link:
            self.add_item(discord.ui.ActionRow(ExtraAttachmentButton(
                "Show Extra Attachment",
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

    async def delete_reports(self, ctx: discord.Interaction, action: str, egg: Egg | int, **action_formats):
        egg_id = egg.id if isinstance(egg, Egg) else egg
        all_reports = await Report.filter(egg__id=egg_id).all()

        enloc = self.bot.get_lines("eggs/report", self.bot.locales["en"]["lines"])
        for report in all_reports:
            try:
                msg = ctx.channel.get_partial_message(report.log_message_id)
                await msg.edit(view=text_view(self.resolved(enloc["actions"][action].format(**action_formats), egg_id)))
            except discord.HTTPException:
                pass

            reporter = await report.reporter
            lines = utils.pick_locale(self.bot.locales, reporter.lang)["lines"]
            myloc = self.bot.get_lines("eggs/report", lines)

            user = await utils.get_or_fetch_user(self.bot, reporter.id)

            try:
                await user.send(myloc["result"].format(egg_id=egg_id, action=myloc["actions"][action].format(**action_formats)))
            except (AttributeError, discord.HTTPException):
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

        await self.delete_reports(ctx, "ignore", egg.id)

    async def change_rating(self, ctx: discord.Interaction):
        egg = await self.report.egg

        _, myloc = await self.bot.get_section(ctx, "rating")

        await ctx.response.send_modal(RatingModal(myloc, egg, after_set=self.after_rating))

    async def after_rating(self, ctx: discord.Interaction, egg: Egg, rating):
        await self.delete_reports(ctx, "rating", egg.id, rating=rating)

    async def change_language(self, ctx: discord.Interaction):
        egg = await self.report.egg

        _, myloc = await self.bot.get_section(ctx, "lang")

        await ctx.response.send_modal(LangModal(self.bot, myloc, egg, after_set=self.after_language))

    async def after_language(self, ctx: discord.Interaction, egg: Egg, lang):
        await self.delete_reports(ctx, "lang", egg.id, lang=lang)

    async def delete(self, ctx: discord.Interaction):
        await ctx.response.defer()

        egg = await self.report.egg

        await self.delete_reports(ctx, "delete", egg.id)
        await utils.egg_delete(egg)

    async def delete_ban(self, ctx: discord.Interaction):
        await ctx.response.defer()

        egg = await self.report.egg
        creator = await egg.creator

        if creator is not None:
            creator.banned = True
            await creator.save(update_fields=["banned"])

        await self.delete_reports(ctx, "delete_ban", egg.id, user_id=creator.id if creator else "unknown")
        await utils.egg_delete(egg)
