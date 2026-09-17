import asyncio
import datetime
import random

import discord
from discord.ext import commands, tasks

import utils
import views
from schema import Rating, User

DAILY_BATCH_SIZE = 20


class Supporter(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.send_daily_eggs.start()

    async def cog_unload(self):
        self.send_daily_eggs.cancel()

    def lines_for(self, user: User) -> dict:
        return self.bot.locales.get(user.lang or "en", self.bot.locales["en"])["lines"]

    async def roll_daily_egg(self, user: User):
        collected_ids = list(await user.collected.all().values_list("id", flat=True))

        allowed = [Rating.SAFE, Rating.QUESTIONABLE]
        if user.allow_explicit_dms:
            allowed.append(Rating.EXPLICIT)

        egg = await utils.random_egg(
            None, None,
            exclude_ids=collected_ids,
            secret_chance=0.25,
            allowed_ratings=allowed,
        )

        if egg is None:
            egg = await utils.random_egg(
                None, None,
                exclude_ids=collected_ids,
                secret_chance=1.0,
                allowed_ratings=allowed,
            )

        if egg is None:
            egg = await utils.random_egg(
                None, None,
                secret_chance=0.25,
                allowed_ratings=allowed,
            )

        return egg

    async def send_daily_egg(self, dbuser: User, now: datetime.datetime):
        first = dbuser.last_daily_at is None

        user = await utils.get_or_fetch_user(self.bot, dbuser.id)

        if user is None:
            dbuser.last_daily_at = now
            await dbuser.save(update_fields=["last_daily_at"])
            return

        egg = await self.roll_daily_egg(dbuser)

        if egg is None:
            dbuser.last_daily_at = now
            await dbuser.save(update_fields=["last_daily_at"])
            return

        collected = False
        if not await dbuser.collected.filter(id=egg.id).exists():
            await dbuser.collected.add(egg)
            collected = True

        lines = self.lines_for(dbuser)
        myloc = self.bot.get_lines("supporter/daily", lines)

        creator = await utils.get_or_fetch_user(self.bot, egg.creator.id)

        container, sfile, vfile, vlink = await utils.get_egg_layout(
            self.bot, lines, egg, creator, collected,
            title=myloc["title"].format(egg.id),
        )

        try:
            await user.send(file=sfile or discord.utils.MISSING, view=views.GetEgg(self.bot, lines, egg, None, creator, container, vfile, vlink))

            if first and not dbuser.allow_explicit_dms:
                await user.send(view=views.ExplicitConsentView(self.bot, lines))
        except discord.HTTPException:
            pass

        dbuser.last_daily_at = now
        await dbuser.save(update_fields=["last_daily_at"])

    @tasks.loop(minutes=10)
    async def send_daily_eggs(self):
        try:
            if not utils.USER_SUPPORTER_SKU_ID:
                return

            try:
                supporter_ids = await utils.fetch_supporter_ids(self.bot)
            except (discord.HTTPException, discord.Forbidden) as e:
                print(f"ERROR: Supporter entitlement fetch failed: {e}")
                return

            if not supporter_ids:
                return

            now = datetime.datetime.now(tz=datetime.UTC)
            ids = list(supporter_ids)

            due = list(await User.filter(id__in=ids, last_daily_at__isnull=True).limit(DAILY_BATCH_SIZE))

            if len(due) < DAILY_BATCH_SIZE:
                seen = {user.id for user in due}
                rest = await User.filter(
                    id__in=[id for id in ids if id not in seen],
                    last_daily_at__lte=now - datetime.timedelta(hours=24),
                ).order_by("last_daily_at").limit(DAILY_BATCH_SIZE - len(due))
                due.extend(rest)

            for dbuser in due:
                try:
                    await self.send_daily_egg(dbuser, now)
                except Exception as e:  # noqa: BLE001
                    print(f"ERROR: Daily Egg failed for {dbuser.id}: {e}")

                await asyncio.sleep(random.uniform(1.0, 5.0))
        except Exception as e:  # noqa: BLE001
            print(f"ERROR: Daily Egg loop failed: {e}")

    @send_daily_eggs.before_loop
    async def before_send_daily_eggs(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(Supporter(bot))