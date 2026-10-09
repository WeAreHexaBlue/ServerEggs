import asyncio
import collections
import os

import discord
from discord import app_commands as app
from discord.ext import commands

import utils
import views
from schema import Guild, Report, User


def is_dev(ctx: discord.Interaction):
    dev_guild = utils.developer_guild()
    if dev_guild is None or not ctx.guild or ctx.guild.id != dev_guild.id: return False

    return ctx.guild.get_role(int(os.getenv("DEVELOPER_ROLE_ID"))) in ctx.user.roles

class Dev(commands.GroupCog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app.command(name="guilds", description="Check the Guilds that the bot is in.")
    @app.describe(search="Search for a name or ID.")
    @app.check(is_dev)
    async def guilds(self, ctx: discord.Interaction, search: str | None = None):
        await ctx.response.defer()

        if search and (query := search.strip()):
            guild = None
            dbguild = None

            if query.isdigit():
                gid = int(query)
                guild = self.bot.get_guild(gid)
                dbguild = await Guild.get_or_none(id=gid)
            else:
                lowered = query.lower()
                exact = [g for g in self.bot.guilds if g.name.lower() == lowered]
                matches = exact or [g for g in self.bot.guilds if lowered in g.name.lower()]

                if matches:
                    guild = min(matches, key=lambda g: g.name.lower())
                    dbguild = await Guild.get_or_none(id=guild.id)
                else:
                    dbguild = await Guild.filter(description__icontains=query).first()

            if guild is None and dbguild is None:
                await ctx.followup.send(content=f"No guild found for `{query}`.")
                return

            if dbguild is None and guild is not None:
                dbguild = await Guild.get_or_none(id=guild.id)

            view = discord.ui.LayoutView(timeout=None)
            view.add_item(await views.guild_container(self.bot, guild, dbguild))

            if dbguild and dbguild.invite:
                view.add_item(discord.ui.ActionRow(discord.ui.Button(label="Invite", url=dbguild.invite)))

            await ctx.followup.send(view=view)
            return

        guilds = sorted(self.bot.guilds, key=lambda g: g.name.lower())

        if not guilds:
            await ctx.followup.send(content="Bot is in no guilds.")
            return

        view = await views.GuildLoop.create(self.bot, ctx.user, collections.deque(guilds))
        await ctx.followup.send(view=view)

    @app.command(name="ban", description="Ban or unban a User from creating Eggs (toggle).")
    @app.describe(user="The User to toggle ban status for.")
    @app.check(is_dev)
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
    @app.check(is_dev)
    async def new_reports(self, ctx: discord.Interaction):
        await ctx.response.defer()

        oldest_report = await Report.all().order_by("created_at").first()

        if oldest_report is None:
            await ctx.followup.send(content="Queue clear!")
            return

        reportch = self.bot.get_channel(int(os.getenv("REPORT_CHANNEL")))
        message = reportch.get_partial_message(oldest_report.log_message_id)

        await ctx.followup.send(content=message.jump_url)

    @app.command(name="reload-cog", description="Reload a Cog.")
    @app.check(is_dev)
    async def reload_cog(self, ctx: discord.Interaction, cog: str):
        await ctx.response.defer()

        await self.bot.reload_extension(f"cogs.{cog}")

        await ctx.followup.send(f"Reloaded `{cog}` module successfully.")

    @app.command(name="reload-locales", description="Reload the language files.")
    @app.check(is_dev)
    async def reload_locales(self, ctx: discord.Interaction):
        await ctx.response.defer()

        self.bot.locales, warnings = await asyncio.to_thread(utils.load_locales, "./lang")
        for warning in warnings:
            await utils.log_long(self.bot, warning)

        display_locales = [f"`{locale}`" for locale in self.bot.locales]
        await ctx.followup.send(f"Reloaded locales {", ".join(display_locales)} successfully.")

    @app.command(name="sync", description="Sync the Command Tree.")
    @app.describe(devguildonly="Only sync for the DEVELOPER_GUILD.")
    @app.check(is_dev)
    async def sync(self, ctx: discord.Interaction, devguildonly: bool = False):
        await ctx.response.defer()

        dev_guild = utils.developer_guild()
        if dev_guild is None:
            await ctx.followup.send("Developer guild not configured.")
            return

        if devguildonly:
            synced = await self.bot.tree.sync(guild=dev_guild)
            await ctx.followup.send(f"Synced {len(synced)} guild command(s).")
        else:
            synced_global = await self.bot.tree.sync()
            synced_guild = await self.bot.tree.sync(guild=dev_guild)
            await ctx.followup.send(f"Synced {len(synced_global)} global and {len(synced_guild)} guild command(s).")

async def setup(bot: commands.Bot):
    await bot.add_cog(Dev(bot), guild=utils.developer_guild())