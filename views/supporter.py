import discord
from discord.ext import commands

import utils
from schema import User

from .base import text_view


class ExplicitConsentView(discord.ui.LayoutView):
    def __init__(self, bot: commands.Bot, lines: dict):
        super().__init__(timeout=None)

        self.bot = bot
        self.myloc = bot.get_lines("supporter/consent", lines)

        self.add_item(discord.ui.TextDisplay(self.myloc["prompt"]))

        allow = discord.ui.Button(label=self.myloc["allow"], style=discord.ButtonStyle.success)
        allow.callback = self.allow

        decline = discord.ui.Button(label=self.myloc["decline"], style=discord.ButtonStyle.secondary)
        decline.callback = self.decline

        self.add_item(discord.ui.ActionRow(allow, decline))

    async def _set(self, ctx: discord.Interaction, value: bool):
        if not await utils.ensure_not_ratelimited(ctx, "interact"):
            return

        user, _ = await User.get_or_create(id=ctx.user.id)
        user.allow_explicit_dms = value
        await user.save(update_fields=["allow_explicit_dms"])

        await ctx.response.edit_message(view=text_view(self.myloc["allowed"] if value else self.myloc["declined"]))

    async def allow(self, ctx: discord.Interaction):
        await self._set(ctx, True)

    async def decline(self, ctx: discord.Interaction):
        await self._set(ctx, False)