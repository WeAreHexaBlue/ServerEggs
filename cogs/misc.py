import sys

import discord
from discord import app_commands as app
from discord.ext import commands

import utils
from main import VERSION


class Misc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app.command(name="help", description="help_description")
    @app.rename(about="help_about")
    @app.describe(about="help_about_description")
    @app.choices(about=[
        app.Choice(name=app.locale_str("create"), value="create"),
        app.Choice(name=app.locale_str("lay"), value="create"),
        app.Choice(name=app.locale_str("get"), value="get"),
        app.Choice(name=app.locale_str("egg"), value="get"),
        app.Choice(name=app.locale_str("edit"), value="edit"),
        app.Choice(name=app.locale_str("report"), value="report"),
        app.Choice(name=app.locale_str("delete"), value="delete"),
        app.Choice(name=app.locale_str("Eggify"), value="eggify"),
        app.Choice(name=app.locale_str("collected"), value="collected"),
        app.Choice(name=app.locale_str("leaderboard"), value="leaderboard"),
        app.Choice(name=app.locale_str("config"), value="config"),
        app.Choice(name=app.locale_str("filter"), value="filter")
    ])
    @app.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @utils.ratelimit("read")
    async def help(self, ctx: discord.Interaction, about: str | None):
        lines, myloc = await self.bot.get_section(ctx, "misc/help")

        myloc = myloc["general"] if about is None else myloc[about]

        e = discord.Embed(title=myloc["title"], color=discord.Color.blurple(), description=myloc["desc"])

        if about is None:
            e.set_thumbnail(url="https://github.com/ActuallyFlamey/ServerEggs/blob/main/icons/seggs_bg.png?raw=true")

            e.add_field(name=myloc["about"], value=myloc["about_desc"], inline=False)
            e.add_field(name=myloc["how"], value=myloc["how_desc"], inline=False)
            e.add_field(name=myloc["donate"], value=myloc["donate_desc"], inline=False)
            e.add_field(name=myloc["credits"], value=myloc["credits_desc"], inline=False)
            e.add_field(name=myloc["versions"], value=myloc["versions_desc"].format(VERSION, discord.__version__, ".".join(map(str, sys.version_info[:3]))), inline=False)

        utils.brand_embed(e, lines)

        await ctx.response.send_message(embed=e)

    @app.command(name="donate", description="donate_description")
    @app.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @utils.ratelimit("read")
    async def donate(self, ctx: discord.Interaction):
        lines, myloc = await self.bot.get_section(ctx, "misc/donate")

        e = discord.Embed(title=myloc["title"], color=discord.Color.blurple(), description=myloc["desc"])
        if not await utils.is_ctx_supporter(ctx):
            e.add_field(name=myloc["sku"], value=myloc["sku_desc"], inline=False)
        e.add_field(name=myloc["kofi"], value=myloc["kofi_desc"], inline=False)
        utils.brand_embed(e, lines)

        await ctx.response.send_message(embed=e)

    @app.command(name="contribute", description="contribute_description")
    @app.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @utils.ratelimit("read")
    async def contribute(self, ctx: discord.Interaction):
        lines, myloc = await self.bot.get_section(ctx, "misc/contribute")
    
        e = discord.Embed(title=myloc["title"], color=discord.Color.blurple(), description=myloc["desc"])
        e.add_field(name=myloc["code"], value=myloc["code_desc"], inline=False)
        e.add_field(name=myloc["trans"], value=myloc["trans_desc"], inline=False)
        utils.brand_embed(e, lines)

        await ctx.response.send_message(embed=e)

async def setup(bot: commands.Bot):
    await bot.add_cog(Misc(bot))