import discord
from discord.ext import commands

import utils
from schema import BattleStatus, BattleVote, User

from .base import ExtraAttachmentButton, action_button


class BattleView(discord.ui.LayoutView):
    def __init__(self, bot: commands.Bot, lines: dict, battle, sides: list[dict], intro: str):
        super().__init__(timeout=None)

        self.bot = bot
        self.lines = lines
        self.myloc = bot.get_lines("battles/battle", lines)
        self.battle = battle
        self.sides = sides

        extras = []
        for side_index, side_name in ((0, "A"), (1, "B")):
            side = self.sides[side_index]

            if side["vfile"] or side["vlink"]:
                extras.append(ExtraAttachmentButton(
                    self.myloc["show"].format(side=side_name),
                    style=discord.ButtonStyle.secondary,
                    file=side["vfile"],
                    link=side["vlink"]
                ))

        self.add_item(discord.ui.TextDisplay(intro))
        self.add_item(sides[0]["container"])
        self.add_item(sides[1]["container"])

        self.vote_a_button = action_button(self.myloc["vote"].format(side="A"), discord.ButtonStyle.primary, self.vote_a)
        self.vote_b_button = action_button(self.myloc["vote"].format(side="B"), discord.ButtonStyle.primary, self.vote_b)

        self.add_item(discord.ui.ActionRow(self.vote_a_button, self.vote_b_button))

        if extras:
            self.add_item(discord.ui.ActionRow(*extras))

    async def interaction_check(self, ctx: discord.Interaction):
        if self.battle.status != BattleStatus.OPEN:
            await ctx.response.send_message(self.myloc["ended"], ephemeral=True)
            return False

        return True

    async def vote(self, ctx: discord.Interaction, choice: int):
        if not await utils.ensure_not_ratelimited(ctx, "interact"):
            return

        voter, _ = await User.get_or_create(id=ctx.user.id)

        if voter.banned:
            await ctx.response.send_message(self.myloc["banned"], ephemeral=True)
            return

        await BattleVote.update_or_create(battle=self.battle, voter=voter, defaults={"choice": choice})

        count_a, count_b = await utils.count_votes(self.battle)

        self.vote_a_button.label = f"{self.myloc["vote"].format(side="A")} ({count_a})"
        self.vote_b_button.label = f"{self.myloc["vote"].format(side="B")} ({count_b})"

        await ctx.response.edit_message(view=self)

    async def vote_a(self, ctx: discord.Interaction):
        await self.vote(ctx, 0)

    async def vote_b(self, ctx: discord.Interaction):
        await self.vote(ctx, 1)

class ChallengeView(discord.ui.View):
    def __init__(self, bot: commands.Bot, lines: dict, prompt: discord.Message, challenger: discord.User, challenged: discord.User, egg):
        super().__init__(timeout=3600)

        self.bot = bot
        self.lines = lines
        self.myloc = bot.get_lines("battles/challenge", lines)
        self.prompt = prompt
        self.challenger = challenger
        self.challenged = challenged
        self.egg = egg
        self.done = False

        self.accept.label = self.myloc["accept"]
        self.decline.label = self.myloc["decline"]

    async def interaction_check(self, ctx: discord.Interaction):
        if ctx.user.id != self.challenged.id:
            await ctx.response.send_message(self.myloc["not_yours"], ephemeral=True)
            return False

        return True

    async def on_timeout(self):
        if self.done:
            return

        try:
            await self.prompt.edit(content=self.myloc["expired"], view=None)
        except discord.HTTPException:
            pass

    @discord.ui.button(style=discord.ButtonStyle.primary)
    async def accept(self, ctx: discord.Interaction, button: discord.ui.Button):
        if not await utils.ensure_not_ratelimited(ctx, "interact"):
            return

        self.done = True

        await ctx.response.send_modal(ChallengeModal(self.bot, self.lines, self.prompt, self.challenger, self.challenged, self.egg))

    @discord.ui.button(style=discord.ButtonStyle.secondary)
    async def decline(self, ctx: discord.Interaction, button: discord.ui.Button):
        if not await utils.ensure_not_ratelimited(ctx, "interact"):
            return

        self.done = True

        await ctx.response.edit_message(content=self.myloc["declined"], view=None)

class ChallengeModal(discord.ui.Modal):
    def __init__(self, bot: commands.Bot, lines: dict, prompt: discord.Message, challenger: discord.User, challenged: discord.User, egg):
        self.bot = bot
        self.myloc = bot.get_lines("battles/challenge", lines)
        self.prompt = prompt
        self.challenger = challenger
        self.challenged = challenged
        self.egg = egg

        super().__init__(title=self.myloc["modal_title"])

        self.egg_id = discord.ui.TextInput(
            label=self.myloc["modal_id"],
            placeholder=self.myloc["modal_id_placeholder"],
            required=False,
            max_length=10
        )

        self.add_item(self.egg_id)

    async def on_submit(self, ctx: discord.Interaction):
        cog = self.bot.get_cog("Battles")

        await cog.accept_challenge(ctx, self.prompt, self.challenger, self.challenged, self.egg, self.egg_id.value)