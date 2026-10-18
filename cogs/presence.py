import discord
from discord.ext import commands, tasks

import utils


class Presence(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.index = 0

        # LEGACY HARDCODED PRESENCES:
        #     "/help for more info!",
        #     "I am behind the tree...",
        #     "Could I offer you an /egg in these trying times?",
        #     "Eggify any message by right-clicking or pressing it!",
        #     "Giving random Eggs in {guilds} servers!",
        #     f"Donate at {utils.LINKS["kofi"].removeprefix("https://")}",
        #     "Surprisingly not about DELTARUNE.",
        #     "I like my Eggs open-source.",
        #     "Well, there is a bot here.",
        #     f"Support at {utils.LINKS["support"].removeprefix("https://")}",
        #     "Delivering {eggs} Eggs!",
        #     "Gambling without any stakes! So awesome!",
        #     "/challenge your friends to an Egg battle!",
        #     "Well, there was not a bot here.",
        #     "It's like Easter, but all year round!",

        self.update_presence.start()

    async def cog_unload(self):
        self.update_presence.cancel()

    async def render(self, presence) -> str:
        try:
            return await utils.run_presence(self.bot, presence)
        except:  # noqa: E722
            await utils.log_error(self.bot, f"Presence `{presence.id}` failed to render, falling back to its text.")
            return presence.text

    @tasks.loop(seconds=30)
    async def update_presence(self):
        presences = await self.bot.refresh_presences()

        if not presences: return

        presence = presences[self.index % len(presences)]
        self.index += 1

        for other in presences:
            other.current = other is presence

        await self.bot.change_presence(activity=discord.CustomActivity(name=await self.render(presence)))

    @update_presence.before_loop
    async def before_update_presence(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(Presence(bot))