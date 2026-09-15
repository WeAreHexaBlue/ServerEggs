import os

import discord
import dotenv

dotenv.load_dotenv()

user_supporter_env = os.getenv("USER_SUPPORTER_SKU_ID", "0")
USER_SUPPORTER_SKU_ID = int(user_supporter_env if user_supporter_env != "" else 0)

async def is_user_supporter(ctx: discord.Interaction) -> bool:
    for entitlement in ctx.entitlements:
        if entitlement.sku_id == USER_SUPPORTER_SKU_ID and not entitlement.deleted and not entitlement.is_expired():
            return True

    return False

async def fetch_supporter_ids(bot) -> set[int]:
    if not USER_SUPPORTER_SKU_ID:
        return set()

    sku = discord.Object(id=USER_SUPPORTER_SKU_ID)

    ids = set()

    async for entitlement in bot.entitlements(limit=None, skus=[sku], exclude_ended=True):
        if entitlement.deleted or entitlement.is_expired():
            continue

        if entitlement.user_id is not None:
            ids.add(entitlement.user_id)

    return ids