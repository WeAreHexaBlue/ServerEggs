import collections

import discord
from discord.ext import commands

import utils
from schema import Egg, Guild


async def guild_container(bot: commands.Bot, guild: discord.Guild | None, dbguild: Guild | None, *, position: str | None = None) -> discord.ui.Container:
    gid = guild.id if guild else dbguild.id
    name = guild.name if guild else f"Unknown guild ({gid})"

    header = f"# {discord.utils.escape_markdown(name)}"
    if position:
        header += f"\n-# Guild {position}"

    body = [f"**ID:** `{gid}`"]

    if guild:
        body.append(f"**Members**: {guild.member_count}")

        owner = await utils.get_or_fetch_user(bot, guild.owner_id)

        body.append(f"**Owner**: {discord.utils.escape_markdown(owner.display_name)} (`{owner.id}`)" if owner else "**Owner:** Unknown")
        body.append(f"**Created At**: {discord.utils.format_dt(guild.created_at, 'R')}")
    elif dbguild is None:
        body.append("Not in cache and not in database.")

    if dbguild is not None:
        body.append(f"**Description**: {dbguild.description or "None"}")
        body.append(f"**Invite**: {dbguild.invite or "None"}")
        body.append(f"**Language**: `{dbguild.lang}`")
        body.append(f"**External Languages**: {"Allowed" if dbguild.allow_ext_lang else "Not allowed"}")
        body.append(f"**Allows Joining Others**: {dbguild.view_join_button}")
        body.append(f"**Has log channel**: {f"Yes (`{dbguild.logch}`)" if dbguild.logch else "None"}")
        body.append(f"**Battle time:** {dbguild.battle_time}")

        eggs = await Egg.filter(origin_id=dbguild.id).count()
        filtered = await dbguild.filtered.all().count()
        body.append(f"**Eggs:** {eggs} (filtered: {filtered})")
    else:
        body.append("Not in database.")

    container = discord.ui.Container(accent_color=discord.Color.blurple())
    container.add_item(discord.ui.TextDisplay(header + "\n" + "\n".join(body)))

    return container

class GuildLoop(discord.ui.LayoutView):
    def __init__(self, bot: commands.Bot, user: discord.User, guilds: collections.deque):
        super().__init__(timeout=None)

        self.bot = bot
        self.user = user
        self.guilds = guilds
        self.total = len(guilds)
        self.index = 0

    @classmethod
    async def create(cls, bot: commands.Bot, user: discord.User, guilds: collections.deque):
        self = cls(bot, user, guilds)
        await self.refresh()
        return self

    async def refresh(self):
        guild = self.guilds[0]
        dbguild = await Guild.get_or_none(id=guild.id)

        for child in list(self.children):
            self.remove_item(child)

        disabled = len(self.guilds) <= 1

        prev = discord.ui.Button(label="◀️", style=discord.ButtonStyle.primary, disabled=disabled)
        prev.callback = self.prev_page

        next = discord.ui.Button(label="▶️", style=discord.ButtonStyle.primary, disabled=disabled)
        next.callback = self.next_page

        buttons = [prev, next]

        if dbguild and dbguild.invite:
            buttons.append(discord.ui.Button(label="Invite", url=dbguild.invite))

        position = f"{self.index + 1} / {self.total}" if self.total > 1 else None
        self.add_item(await guild_container(self.bot, guild, dbguild, position=position))
        self.add_item(discord.ui.ActionRow(*buttons))

    async def interaction_check(self, ctx: discord.Interaction):
        if ctx.user.id != self.user.id:
            await ctx.response.send_message("This view is not yours.", ephemeral=True)
            return False

        return True

    async def respond(self, ctx: discord.Interaction):
        await ctx.response.defer()

        await self.refresh()
        await ctx.edit_original_response(view=self)

    async def prev_page(self, ctx: discord.Interaction):
        self.guilds.rotate(1)
        self.index = (self.index - 1) % self.total
        await self.respond(ctx)

    async def next_page(self, ctx: discord.Interaction):
        self.guilds.rotate(-1)
        self.index = (self.index + 1) % self.total
        await self.respond(ctx)
