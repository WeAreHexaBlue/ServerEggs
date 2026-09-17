import os

import discord
import dotenv

dotenv.load_dotenv()

user_supporter_env = os.getenv("USER_SUPPORTER_SKU_ID", "0")
USER_SUPPORTER_SKU_ID = int(user_supporter_env if user_supporter_env != "" else 0)

async def is_ctx_supporter(ctx: discord.Interaction) -> bool:
    for entitlement in ctx.entitlements:
        if entitlement.sku_id == USER_SUPPORTER_SKU_ID and not entitlement.deleted and not entitlement.is_expired():
            return True

    from .misc import is_dev_user

    try:
        return await is_dev_user(ctx.client, ctx.user.id)
    except (discord.DiscordException, TimeoutError):
        return False

async def fetch_supporter_ids(bot) -> set[int]:
    from .misc import fetch_dev_ids

    ids = set()

    if USER_SUPPORTER_SKU_ID:
        sku = discord.Object(id=USER_SUPPORTER_SKU_ID)

        async for entitlement in bot.entitlements(limit=None, skus=[sku], exclude_ended=True):
            if entitlement.deleted or entitlement.is_expired():
                continue

            if entitlement.user_id is not None:
                ids.add(entitlement.user_id)

    try:
        ids |= await fetch_dev_ids(bot)
    except (discord.DiscordException, TimeoutError):
        pass

    return ids