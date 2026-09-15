import collections
import os

import discord
import dotenv
from discord.ext import commands
from tortoise.exceptions import IntegrityError

import utils
from schema import Rating, Report, User

from .base import ExtraAttachmentButton, action_button, text_view
from .mod import ReportActions

dotenv.load_dotenv()

class CreateEgg(discord.ui.LayoutView):
    def __init__(self, myloc: dict, container: discord.ui.Container, file=None, link=None):
        super().__init__(timeout=None)

        self.add_item(container)

        if file or link:
            self.add_item(discord.ui.ActionRow(
                ExtraAttachmentButton(myloc["show_extra_attachment"], file=file, link=link)
            ))

class PreEggify(discord.ui.View):
    def __init__(self, bot: commands.Bot, lines: dict, text: str | None, file: discord.Attachment | None, link: str | None):
        super().__init__(timeout=None)

        self.bot = bot
        self.lines = lines
        self.myloc = bot.get_lines("eggs/eggify", lines)
        self.text = text
        self.file = file
        self.link = link

        self.confirm.label = self.myloc["confirm"]
        self.cancel.label = self.myloc["cancel"]

    @discord.ui.button(style=discord.ButtonStyle.primary)
    async def confirm(self, ctx: discord.Interaction, button: discord.ui.Button):
        if not await utils.ensure_not_ratelimited(ctx, "interact"):
            return

        default_name = utils.pick_locale(self.bot.locales, ctx.locale.value).get("lang_default", "Server Default")
        await ctx.response.send_modal(Eggify(self.bot, self.lines, self.text, self.file, self.link, server_default=default_name))

    @discord.ui.button(style=discord.ButtonStyle.secondary)
    async def cancel(self, ctx: discord.Interaction, button: discord.ui.Button):
        await ctx.response.edit_message(content=self.myloc["cancelled"], embed=None, attachments=[], view=None)

class Eggify(discord.ui.Modal):
    SERVER_DEFAULT_VALUE = "server_default"

    def __init__(self, bot: commands.Bot, lines: dict, text: str | None, file: discord.Attachment | None, link: str | None, *, server_default: str = "Server Default"):
        self.bot = bot
        self.lines = lines
        self.myloc = bot.get_lines("eggs/eggify", lines)

        self.text = text
        self.file = file
        self.link = link

        super().__init__(title=self.myloc["title"])

        self.eggtext = discord.ui.TextInput(
            label=self.myloc["text"],
            placeholder=self.myloc["text_placeholder"],
            default=text,
            required=False,
            style=discord.TextStyle.paragraph
        )

        self.secret = discord.ui.Label(
            text=self.myloc["secret"],
            description=self.myloc["secret_desc"],
            component=discord.ui.Checkbox()
        )

        self.rating = discord.ui.Label(
            text=self.myloc["rating"],
            description=self.myloc["rating_desc"],
            component=discord.ui.Select(
                placeholder=self.myloc["rating_placeholder"],
                options=[
                    discord.SelectOption(label=self.myloc["rating_safe"], value=Rating.SAFE.value),
                    discord.SelectOption(label=self.myloc["rating_questionable"], value=Rating.QUESTIONABLE.value),
                    discord.SelectOption(label=self.myloc["rating_explicit"], value=Rating.EXPLICIT.value),
                ]
            )
        )

        self.lang = discord.ui.Label(
            text=self.myloc["lang"],
            description=self.myloc["lang_desc"],
            component=discord.ui.Select(
                placeholder=self.myloc["lang_placeholder"],
                options=[
                    discord.SelectOption(label=server_default, value=self.SERVER_DEFAULT_VALUE, default=True),
                    *[
                        discord.SelectOption(label=data.get("language_name", code), value=code)
                        for code, data in sorted(bot.locales.items())
                    ][:24],
                ]
            )
        )

        self.add_item(self.eggtext)
        self.add_item(self.secret)
        self.add_item(self.rating)
        self.add_item(self.lang)

    async def on_submit(self, ctx: discord.Interaction):
        if not await utils.ensure_not_ratelimited(ctx, "create"):
            return

        await ctx.response.edit_message(content=self.myloc["continued"], view=None)

        lang_raw = self.lang.component.values[0] if self.lang.component.values else self.SERVER_DEFAULT_VALUE
        lang = None if lang_raw in ("", self.SERVER_DEFAULT_VALUE) else lang_raw

        if lang is not None and lang not in self.bot.locales:
            bad_lang = self.bot.get_lines("eggs/create_edit", self.lines)["bad_lang"]
            await ctx.followup.send(bad_lang)
            return

        cog = self.bot.get_cog("Eggs")
        await cog.create_or_edit(ctx, None, self.eggtext.value, self.file, self.link, Rating(self.rating.component.values[0]), self.secret.component.value, lang=lang, skip_ratelimit=True)

class GetEgg(discord.ui.LayoutView):
    def __init__(self, bot: commands.Bot, lines: dict, egg, guild, creator: discord.User, container: discord.ui.Container, file=None, link=None):
        super().__init__(timeout=None)

        self.bot = bot
        self.lines = lines
        self.myloc = bot.get_lines("eggs/send", lines)
        self.egg = egg

        buttons = []

        if file or link:
            buttons.append(ExtraAttachmentButton(self.myloc["button"]["show_extra_attachment"], file=file, link=link))

        buttons.append(action_button(self.myloc["button"]["report"], discord.ButtonStyle.danger, self.report))

        if egg.origin.invite is not None and (guild.view_join_button if guild else True):
            buttons.append(discord.ui.Button(
                label=self.myloc["button"]["origin"],
                url=egg.origin.invite
            ))

        if creator is not None and egg.creator.public:
            buttons.append(discord.ui.Button(
                label=self.myloc["button"]["creator"],
                url=f"https://discord.com/users/{creator.id}"
            ))

        self.add_item(container)
        self.add_item(discord.ui.ActionRow(*buttons))

    async def report(self, ctx: discord.Interaction):
        if not await utils.ensure_not_ratelimited(ctx, "interact"):
            return

        await ctx.response.send_modal(ReportEgg(self.bot, self.lines, self.egg, False))

class EggLoop(discord.ui.LayoutView):
    def __init__(self, bot: commands.Bot, lines: dict, myloc: dict, user: discord.User, eggs: collections.deque):
        super().__init__(timeout=None)

        self.bot = bot
        self.lines = lines
        self.myloc = myloc
        self.user = user
        self.eggs = eggs
        self.sfile = None

    @classmethod
    async def create(cls, bot: commands.Bot, lines: dict, myloc: dict, user: discord.User, eggs: collections.deque):
        self = cls(bot, lines, myloc, user, eggs)
        await self.refresh()
        return self

    async def refresh(self) -> discord.File | None:
        container, sfile, vfile, vlink = await utils.get_egg_layout(self.bot, self.lines, self.eggs[0])

        self.sfile = sfile

        for child in list(self.children):
            self.remove_item(child)

        disabled = len(self.eggs) <= 1

        prev = discord.ui.Button(label="◀️", style=discord.ButtonStyle.primary, disabled=disabled)
        prev.callback = self.prev_page

        next = discord.ui.Button(label="▶️", style=discord.ButtonStyle.primary, disabled=disabled)
        next.callback = self.next_page

        buttons = [prev]

        if vfile or vlink:
            buttons.append(ExtraAttachmentButton(
                self.myloc["show_extra_attachment"],
                style=discord.ButtonStyle.secondary,
                file=vfile,
                link=vlink
            ))

        buttons.append(next)

        self.add_item(container)
        self.add_item(discord.ui.ActionRow(*buttons))

        return sfile

    async def interaction_check(self, ctx: discord.Interaction):
        if ctx.user.id != self.user.id:
            await ctx.response.send_message(self.myloc["not_yours"], ephemeral=True)
            return False

        return True

    async def respond(self, ctx: discord.Interaction):
        await ctx.response.defer()

        if not await utils.ensure_not_ratelimited(ctx, "interact"):
            return

        sfile = await self.refresh()

        await ctx.edit_original_response(view=self, attachments=[sfile] if sfile else [])

    async def prev_page(self, ctx: discord.Interaction):
        self.eggs.rotate(1)
        await self.respond(ctx)

    async def next_page(self, ctx: discord.Interaction):
        self.eggs.rotate(-1)
        await self.respond(ctx)

class DeleteEgg(discord.ui.LayoutView):
    def __init__(self, bot: commands.Bot, lines: dict, egg, container: discord.ui.Container, file=None, link=None):
        super().__init__(timeout=60)

        self.myloc = bot.get_lines("eggs/delete", lines)
        self.egg = egg

        buttons = [action_button(self.myloc["confirm"], discord.ButtonStyle.danger, self.confirm)]

        if file or link:
            buttons.append(ExtraAttachmentButton(
                self.myloc["show_extra_attachment"],
                style=discord.ButtonStyle.secondary,
                file=file,
                link=link
            ))

        buttons.append(action_button(self.myloc["cancel"], discord.ButtonStyle.secondary, self.cancel))

        self.add_item(container)
        self.add_item(discord.ui.ActionRow(*buttons))

    async def confirm(self, ctx: discord.Interaction):
        if not await utils.ensure_not_ratelimited(ctx, "report"):
            return

        eggid = self.egg.id

        await utils.egg_delete(self.egg)

        await ctx.response.edit_message(view=text_view(self.myloc["success"].format(eggid)))

    async def cancel(self, ctx: discord.Interaction):
        await ctx.response.edit_message(view=text_view(self.myloc["cancelled"]))

class PreReportEgg(discord.ui.LayoutView):
    def __init__(self, bot: commands.Bot, lines: dict, egg, container: discord.ui.Container, file=None, link=None):
        super().__init__(timeout=60)

        self.bot = bot
        self.lines = lines
        self.myloc = bot.get_lines("eggs/report", lines)
        self.egg = egg

        buttons = [action_button(self.myloc["confirm"], discord.ButtonStyle.danger, self.confirm)]

        if file or link:
            buttons.append(ExtraAttachmentButton(
                self.myloc["show_extra_attachment"],
                style=discord.ButtonStyle.secondary,
                file=file,
                link=link
            ))

        buttons.append(action_button(self.myloc["cancel"], discord.ButtonStyle.secondary, self.cancel))

        self.add_item(container)
        self.add_item(discord.ui.ActionRow(*buttons))

    async def confirm(self, ctx: discord.Interaction):
        if not await utils.ensure_not_ratelimited(ctx, "interact"):
            return

        await ctx.response.send_modal(ReportEgg(self.bot, self.lines, self.egg))

    async def cancel(self, ctx: discord.Interaction):
        await ctx.response.edit_message(view=text_view(self.myloc["cancelled"]))

class ReportEgg(discord.ui.Modal):
    def __init__(self, bot: commands.Bot, lines: dict, egg, from_report_command=True):
        self.bot = bot
        self.lines = lines
        self.myloc = bot.get_lines("eggs/report", lines)
        self.egg = egg
        self.from_report_command = from_report_command

        super().__init__(title=self.myloc["title"].format(egg.id))

        self.reason = discord.ui.Label(
            text=self.myloc["rule"],
            description=self.myloc["rule_desc"],
            component=discord.ui.Select(
                placeholder=self.myloc["rule_placeholder"],
                options=[
                    discord.SelectOption(label=self.myloc["rules"]["bad_rating"], description=self.myloc["rules"]["bad_rating_desc"]),
                    discord.SelectOption(label=self.myloc["rules"]["hateful"], description=self.myloc["rules"]["hateful_desc"]),
                    discord.SelectOption(label=self.myloc["rules"]["other"], description=self.myloc["rules"]["other_desc"]),
                ]
            )
        )

        self.specify = discord.ui.TextInput(
            label=self.myloc["other"],
            required=False,
            max_length=200,
            placeholder=self.myloc["other_placeholder"]
        )

        self.add_item(self.reason)
        self.add_item(self.specify)

    async def finish(self, ctx: discord.Interaction, key: str):
        content = self.myloc[key].format(self.egg.id)

        if self.from_report_command:
            await ctx.edit_original_response(view=text_view(content))
        else:
            await ctx.followup.send(content=content, ephemeral=True)

    async def on_submit(self, ctx: discord.Interaction):
        if not await utils.ensure_not_ratelimited(ctx, "report"):
            return

        await ctx.response.defer(ephemeral=True)

        reporter, _ = await User.get_or_create(id=ctx.user.id)

        reason = self.reason.component.values[0]
        extra = (self.specify.value or "").strip()
        if reason == self.myloc["rules"]["other"]:
            reason = extra
        elif extra:
            reason = utils.truncate(f"{reason}: {extra}", 200)

        try:
            report = await Report.create(
                egg=self.egg,
                reporter=reporter,
                reason=reason
            )

            reportch = self.bot.get_channel(int(os.getenv("REPORT_CHANNEL")))

            container, sfile, vfile, vlink = await utils.get_egg_layout(self.bot, self.lines, self.egg, None, False, True)

            msg = await reportch.send(
                file=sfile or discord.utils.MISSING,
                view=ReportActions(
                    self.bot, report, reporter,
                    f"New report from **{ctx.user.name}** ({reporter.id}).\n**Reason**: {report.reason}",
                    container, vfile, vlink, lines=self.lines
                )
            )

            report.log_message_id = msg.id
            await report.save(update_fields=["log_message_id"])

            await self.finish(ctx, "success")
        except IntegrityError:
            await self.finish(ctx, "already")