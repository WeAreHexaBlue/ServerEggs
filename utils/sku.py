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