import os

import discord
from discord import app_commands as app
from discord.ext import commands

import utils
from schema import Egg, Guild, Report, User


def is_global_mod(ctx: discord.Interaction):
    dev_guild = utils.developer_guild()
    if dev_guild is None or not ctx.guild or ctx.guild.id != dev_guild.id: return False

    return ctx.guild.get_role(int(os.getenv("MOD_ROLE_ID"))) in ctx.user.roles

class Mod(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app.command(name="filter", description="filter_description")
    @app.rename(id="filter_id")
    @app.describe(id="filter_id_description")
    @app.allowed_contexts(guilds=True, dms=False, private_channels=False)
    @app.checks.has_permissions(manage_guild=True)
    @utils.ratelimit("read")
    async def filter_egg(self, ctx: discord.Interaction, id: int):
        await ctx.response.defer(ephemeral=True)

        _, myloc = await self.bot.get_section(ctx, "mod/filter")

        egg = await Egg.get_or_none(id=id)
        if not egg:
            await ctx.followup.send(myloc["not_found"].format(egg_id=id), ephemeral=True)
            return

        guild, _ = await Guild.get_or_create(id=ctx.guild.id)

        current_state = await guild.filtered.filter(id=egg.id).exists()

        if current_state:
            await guild.filtered.remove(egg)
            await ctx.followup.send(myloc["unfiltered"].format(egg_id=egg.id), ephemeral=True)
        else:
            await guild.filtered.add(egg)
            await ctx.followup.send(myloc["filtered"].format(egg_id=egg.id), ephemeral=True)
    
    @app.command(name="ban", description="Ban or unban a User from creating Eggs (toggle).")
    @app.describe(user="The User to toggle ban status for.")
    @app.guilds(utils.developer_guild())
    @app.check(is_global_mod)
    async def ban(self, ctx: discord.Interaction, user: discord.User):
        await ctx.response.defer()

        db_user = await User.get_or_none(id=user.id)

        if db_user is None:
            await ctx.followup.send(content="User not found.")
            return

        db_user.banned = not db_user.banned
        await db_user.save(update_fields=["banned"])

        await ctx.followup.send(content=f"{"Banned" if db_user.banned else "Unbanned"} user `{db_user.id}`.")

    @app.command(name="new-reports", description="Link to the top of the report queue.")
    @app.guilds(utils.developer_guild())
    @app.check(is_global_mod)
    async def new_reports(self, ctx: discord.Interaction):
        await ctx.response.defer()

        oldest_report = await Report.all().order_by("created_at").first()

        if oldest_report is None:
            await ctx.followup.send(content="Queue clear!")
            return

        reportch = self.bot.get_channel(int(os.getenv("REPORT_CHANNEL")))
        message = reportch.get_partial_message(oldest_report.log_message_id)

        await ctx.followup.send(content=message.jump_url)

async def setup(bot: commands.Bot):
    await bot.add_cog(Mod(bot))