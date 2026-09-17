import os

import discord
import dotenv
from discord.ext import commands

dotenv.load_dotenv()

user_supporter_env = os.getenv("USER_SUPPORTER_SKU_ID", "0")
USER_SUPPORTER_SKU_ID = int(user_supporter_env if user_supporter_env != "" else 0)

async def is_ctx_supporter(ctx: discord.Interaction) -> bool:
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

async def grant_dev_entitlements(bot: commands.Bot) -> None:
    if not USER_SUPPORTER_SKU_ID:
        return

    from schema import User

    devguild = bot.get_guild(int(os.getenv("DEVELOPER_GUILD_ID")))
    if devguild is None: return

    role = devguild.get_role(int(os.getenv("DEVELOPER_ROLE_ID")))
    if role is None: return

    entitled = await fetch_supporter_ids(bot)
    sku_obj = discord.Object(id=USER_SUPPORTER_SKU_ID)

    for user_id in await User.all().values_list("id", flat=True):
        if user_id in entitled:
            continue

        try:
            member = await devguild.fetch_member(user_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            continue

        if any(r.id == role.id for r in member.roles):
            await bot.create_entitlement(sku_obj, discord.Object(id=user_id), discord.EntitlementOwnerType.user)