import collections
import math
import time

import discord
from discord import app_commands as app

from . import sku


class RateLimited(Exception):
    def __init__(self, retry_after: float, scope: str, tier: str):
        self.retry_after = retry_after
        self.scope = scope
        self.tier = tier
        super().__init__(f"Rate limited ({scope}/{tier}): retry in {retry_after:.1f}s")

LIMITS = {
    "create": {
        "user": {"normal": (3, 300), "supporter": (6, 300)},
        "guild": (10, 300)
    },
    "search": {
        "user": {"normal": (5, 60), "supporter": (10, 60)},
        "guild": (15, 60)
    },
    "battle": {
        "user": {"normal": (3, 60), "supporter": (6, 60)},
        "guild": (10, 60)
    },
    "read": {
        "user": {"normal": (8, 30), "supporter": (16, 30)},
        "guild": (30, 30)
    },
    "interact": {
        "user": {"normal": (5, 15), "supporter": (10, 15)},
        "guild": (20, 15)
    },
    "report": {
        "user": {"normal": (3, 300), "supporter": (6, 300)}, 
        "guild": (10, 300)
    }
}

buckets: dict[tuple[str, str, str], collections.deque] = {}

def prune(key: tuple[str, str, str], window: int, now: float) -> collections.deque:
    dq = buckets.get(key)

    if dq is None:
        dq = buckets[key] = collections.deque()
        return dq

    cutoff = now - window
    while dq and dq[0] <= cutoff:
        dq.popleft()

    return dq

def check_and_consume(user_id: int, guild_id: int | None, tier: str, is_supporter: bool = False) -> tuple[bool, float, str]:
    limits = LIMITS[tier]
    now = time.monotonic()

    user_key = ("user", str(user_id), tier)
    user_max, user_window = limits["user"]["normal"] if not is_supporter else limits["user"]["supporter"]
    user_dq = prune(user_key, user_window, now)
    if len(user_dq) >= user_max:
        return False, max(0.0, user_dq[0] + user_window - now), "user"

    if guild_id is not None:
        guild_key = ("guild", str(guild_id), tier)
        guild_max, guild_window = limits["guild"]
        guild_dq = prune(guild_key, guild_window, now)
        if len(guild_dq) >= guild_max:
            return False, max(0.0, guild_dq[0] + guild_window - now), "guild"

    user_dq.append(now)
    if guild_id is not None:
        buckets[("guild", str(guild_id), tier)].append(now)
    return True, 0.0, ""

def reset() -> None:
    buckets.clear()

async def is_bypassed(bot, user_id: int) -> bool:
    from .mod import is_global_mod

    try:
        return await is_global_mod(bot, user_id)
    except (discord.DiscordException, TimeoutError):
        return False

def ratelimit_message(retry_after: float) -> str:
    secs = max(1, math.ceil(retry_after))
    return f"You are being **rate-limited**. Try again in **{secs}s**."

async def send_ratelimited(ctx: discord.Interaction, retry_after: float) -> None:
    try:
        _, myloc = await ctx.client.get_section(ctx, "error")
        template = (myloc or {}).get("ratelimited")
    except (discord.DiscordException, TimeoutError):
        template = None

    secs = max(1, math.ceil(retry_after))
    content = template.format(secs) if template else ratelimit_message(retry_after)

    try:
        if ctx.response.is_done():
            await ctx.followup.send(content=content, ephemeral=True)
        else:
            await ctx.response.send_message(content=content, ephemeral=True)
    except discord.HTTPException:
        pass

async def ensure_not_ratelimited(ctx: discord.Interaction, tier: str) -> bool:
    if await is_bypassed(ctx.client, ctx.user.id):
        return True

    guild_id = ctx.guild.id if ctx.guild else None
    allowed, retry_after, _ = check_and_consume(ctx.user.id, guild_id, tier, is_supporter=await sku.is_ctx_supporter(ctx))

    if not allowed:
        await send_ratelimited(ctx, retry_after)
        return False

    return True

def ratelimit(tier: str):
    async def predicate(ctx: discord.Interaction) -> bool:
        if await is_bypassed(ctx.client, ctx.user.id):
            return True

        guild_id = ctx.guild.id if ctx.guild else None
        allowed, retry_after, scope = check_and_consume(ctx.user.id, guild_id, tier, is_supporter=await sku.is_ctx_supporter(ctx))

        if not allowed:
            raise RateLimited(retry_after, scope, tier)

        return True

    return app.check(predicate)