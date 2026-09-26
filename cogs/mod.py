import discord
from discord import app_commands as app
from discord.ext import commands

import utils
from schema import Egg, Guild


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

async def setup(bot: commands.Bot):
    await bot.add_cog(Mod(bot))