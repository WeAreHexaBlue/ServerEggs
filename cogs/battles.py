import datetime

import discord
from discord import app_commands as app
from discord.ext import commands, tasks

import utils
import views
from schema import Battle, Egg, Guild, User


class Battles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.finalize_battles.start()

    async def cog_unload(self):
        self.finalize_battles.cancel()

    async def pool_fighter_egg(self, ctx: discord.Interaction, myloc: dict, egg_id: int, *, guild: Guild | None = None, channel=None):
        egg = await Egg.get_or_none(id=egg_id)

        if egg is None:
            await ctx.followup.send(myloc["not_found"].format(egg_id), ephemeral=True)
            return None

        if egg.rating not in utils.channel_ratings(guild, channel):
            await ctx.followup.send(myloc["rating_not_allowed"].format(egg_id), ephemeral=True)
            return None

        if guild and not guild.allow_ext_lang and egg.lang != guild.lang:
            await ctx.followup.send(myloc["lang_not_allowed"].format(egg_id), ephemeral=True)
            return None

        return egg

    async def owned_fighter_egg(self, ctx: discord.Interaction, myloc: dict, user: User, egg_id: int | None, *, guild: Guild | None = None, channel=None, exclude_ids=None):
        if egg_id is not None:
            pool = await utils.fight_pool_ids(user)

            if egg_id not in pool:
                await ctx.followup.send(myloc["not_your_egg"].format(egg_id), ephemeral=True)
                return None

            return await self.pool_fighter_egg(ctx, myloc, egg_id, guild=guild, channel=channel)

        egg = await utils.random_fight_egg(user, guild, channel, exclude_ids=exclude_ids)

        if egg is None:
            await ctx.followup.send(myloc["empty_pool"], ephemeral=True)
            return None

        return egg

    async def start_battle(self, ctx: discord.Interaction, egg_a, egg_b, *, user_a: User | None = None, user_b: User | None = None):
        lines, myloc = await self.bot.get_section(ctx, "battles/battle")

        guild, _ = await Guild.get_or_create(id=ctx.guild.id)

        battle = await Battle.create(
            guild=guild,
            egg_a=egg_a,
            egg_b=egg_b,
            user_a=user_a,
            user_b=user_b,
            ends_at=datetime.datetime.now(datetime.timezone.utc) + guild.battle_time
        )

        sides = await utils.build_battle_message(self.bot, lines, myloc, egg_a, egg_b)
        files = [side["sfile"] for side in sides if side["sfile"]]

        fighters = []
        if user_a and user_b:
            fighters.append(await utils.get_or_fetch_user(self.bot, user_a.id))
            fighters.append(await utils.get_or_fetch_user(self.bot, user_b.id))

        intro = myloc["begin_random"].format(egg_a.id, egg_b.id) if not fighters else myloc["begin_challenge"].format(egg_a.id, egg_b.id, f"**{discord.utils.escape_markdown(fighters[0].display_name)}** ({discord.utils.escape_markdown(fighters[0].name)})", f"**{discord.utils.escape_markdown(fighters[1].display_name)}** ({discord.utils.escape_markdown(fighters[1].name)})")

        message = await ctx.followup.send(
            files=files,
            view=views.BattleView(self.bot, lines, battle, sides, intro)
        )

        battle.channel_id = ctx.channel.id
        battle.message_id = message.id
        await battle.save(update_fields=["channel_id", "message_id"])

    @app.command(name="battle", description="battle_description")
    @app.rename(a="battle_a", b="battle_b")
    @app.describe(a="battle_a_description", b="battle_b_description")
    @app.allowed_installs(guilds=True, users=False)
    @app.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def battle(self, ctx: discord.Interaction, a: int | None = None, b: int | None = None):
        if not await utils.ensure_not_ratelimited(ctx, "battle"):
            return

        await ctx.response.defer()

        _, myloc = await self.bot.get_section(ctx, "battles/battle")

        guild = await Guild.get_or_none(id=ctx.guild.id)

        if a is not None and b is not None and a == b:
            await ctx.followup.send(myloc["same_egg"], ephemeral=True)
            return

        egg_a = await self.pool_fighter_egg(ctx, myloc, a, guild=guild, channel=ctx.channel) if a is not None else None
        if a is not None and egg_a is None:
            return

        egg_b = await self.pool_fighter_egg(ctx, myloc, b, guild=guild, channel=ctx.channel) if b is not None else None
        if b is not None and egg_b is None:
            return

        if egg_a is None:
            egg_a = await utils.random_egg(guild, ctx.channel, exclude_ids={b} if b is not None else None)

        if egg_b is None:
            excluded = {egg_a.id} if egg_a is not None else ({a} if a is not None else None)
            egg_b = await utils.random_egg(guild, ctx.channel, exclude_ids=excluded)

        if egg_a is None or egg_b is None:
            await ctx.followup.send(myloc["no_egg"])
            return

        await self.start_battle(ctx, egg_a, egg_b)

    @app.command(name="challenge", description="challenge_description")
    @app.rename(against="challenge_against", using="challenge_using")
    @app.describe(against="challenge_against_description", using="challenge_using_description")
    @app.allowed_installs(guilds=True, users=False)
    @app.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def challenge(self, ctx: discord.Interaction, against: discord.User, using: int | None = None):
        if not await utils.ensure_not_ratelimited(ctx, "battle"):
            return

        await ctx.response.defer(ephemeral=True)

        lines, myloc = await self.bot.get_section(ctx, "battles/challenge")

        if against.id == ctx.user.id:
            await ctx.followup.send(myloc["self"], ephemeral=True)
            return

        if against.bot:
            await ctx.followup.send(myloc["bot"], ephemeral=True)
            return

        challenger, _ = await User.get_or_create(id=ctx.user.id)

        guild = await Guild.get_or_none(id=ctx.guild.id)

        egg_a = await self.owned_fighter_egg(ctx, myloc, challenger, using, guild=guild, channel=ctx.channel)
        if egg_a is None:
            return

        challenge_view = views.ChallengeView(self.bot, lines, None, ctx.user, against, egg_a)

        prompt = await ctx.channel.send(
            content=myloc["prompt"].format(against.mention, ctx.user.mention),
            view=challenge_view
        )

        challenge_view.prompt = prompt

        await ctx.followup.send(myloc["sent"], ephemeral=True)

    async def accept_challenge(self, ctx: discord.Interaction, prompt: discord.Message, challenger: discord.User, challenged: discord.User, egg_a, egg_id_text: str | None):
        if not await utils.ensure_not_ratelimited(ctx, "battle"):
            return

        _, myloc = await self.bot.get_section(ctx, "battles/challenge")

        target, _ = await User.get_or_create(id=challenged.id)

        guild = await Guild.get_or_none(id=ctx.guild.id) if ctx.guild else None

        await ctx.response.defer(ephemeral=True)

        raw = (egg_id_text or "").strip()

        if raw:
            try:
                egg_id = int(raw)
            except ValueError:
                await ctx.followup.send(myloc["invalid_egg"].format(raw), ephemeral=True)
                return

            if egg_id == egg_a.id:
                await ctx.followup.send(myloc["same_egg"], ephemeral=True)
                return

            egg_b = await self.owned_fighter_egg(ctx, myloc, target, egg_id, guild=guild, channel=ctx.channel)
            if egg_b is None:
                return
        else:
            egg_b = await utils.random_fight_egg(target, guild, ctx.channel, exclude_ids={egg_a.id})
            if egg_b is None:
                await ctx.followup.send(myloc["empty_pool"], ephemeral=True)
                return

        user_a, _ = await User.get_or_create(id=challenger.id)

        await self.start_battle(ctx, egg_a, egg_b, user_a=user_a, user_b=target)

        await prompt.edit(content=myloc["accepted"].format(challenged.display_name), view=None)

    @tasks.loop(minutes=1)
    async def finalize_battles(self):
        try:
            await utils.finalize_due_battles(self.bot)
        except Exception as e:  # noqa: BLE001
            print(f"ERROR: Battle finalization failed: {e}")

    @finalize_battles.before_loop
    async def before_finalize_battles(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(Battles(bot))
