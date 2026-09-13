import collections
import difflib
import random
import re
import unicodedata

import discord
from discord import app_commands as app
from discord.ext import commands
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

import utils
import views
from schema import Egg, Guild, Rating, User

CUSTOM_EMOJI_RE = re.compile(r"<a?:(\w+):\d+>")
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")
AUTOLINK_RE = re.compile(r"<(\w+://[^>]+)>")

EMOJI_RANGES = (
    (0x1F000, 0x1FAFF),
    (0x2600, 0x27BF),
    (0x2B00, 0x2BFF),
)

def is_emoji(code: int) -> bool:
    return any(start <= code <= end for start, end in EMOJI_RANGES)

EMOJI_ALIASES = {}
for start, end in EMOJI_RANGES:
    for code in range(start, end + 1):
        name = unicodedata.name(chr(code), None)
        if not name:
            continue
        for _word in name.lower().split():
            EMOJI_ALIASES.setdefault(_word, set()).add(chr(code))

ACCENT_RANGES = (
    (0x00C0, 0x024F),
    (0x1E00, 0x1EFF),
)

ACCENT_VARIANTS = {}
for start, end in ACCENT_RANGES:
    for code in range(start, end + 1):
        ch = chr(code)
        base = unicodedata.normalize("NFD", ch)
        if len(base) > 1:
            ACCENT_VARIANTS.setdefault(base[0], set()).add(ch)

ACCENT_BASE = {variant: base for base, variants in ACCENT_VARIANTS.items() for variant in variants}

def fold_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")

def accent_pattern(text: str) -> str:
    out = []
    for ch in text:
        base = ACCENT_BASE.get(ch, ch)
        variants = ACCENT_VARIANTS.get(base)
        if variants:
            out.append("[" + "".join(sorted(variants | {base})) + "]")
        else:
            out.append(re.escape(ch))
    return "".join(out)

def normalize(text: str) -> str:
    text = CUSTOM_EMOJI_RE.sub(r"\1", text)
    text = LINK_RE.sub(r"\1 \2", text)
    text = AUTOLINK_RE.sub(r"\1", text)

    out = []
    for ch in text:
        if is_emoji(ord(ch)):
            name = unicodedata.name(ch, "")
            if name:
                out.append(name)
                continue
        out.append(ch)

    return fold_accents("".join(out)).lower()

def expand(text: str) -> set[str]:
    terms = {text}

    terms.update(CUSTOM_EMOJI_RE.findall(text))

    for ch in text:
        if is_emoji(ord(ch)):
            terms.add(ch)
            name = unicodedata.name(ch, "")
            if name:
                terms.add(name)
                terms.update(name.lower().split())

    for word in re.findall(r"[a-z0-9']+", text.lower()):
        terms.update(EMOJI_ALIASES.get(word, ()))

    return terms

FUZZY_MIN_WORD = 4
FUZZY_CUTOFF = 0.7

def fuzzy_score(query: str, text: str) -> float:
    qwords = [w for w in re.findall(r"[a-z0-9']+", query.lower()) if len(w) >= FUZZY_MIN_WORD]

    if not qwords:
        return 0.0

    twords = re.findall(r"[a-z0-9']+", text.lower())

    if not twords:
        return 0.0

    return max(
        difflib.SequenceMatcher(None, q, t).ratio()
        for q in qwords
        for t in twords
    )

FUZZY_LIMIT = 50
FUZZY_THRESHOLD = 0.2

async def fuzzy_ids(query: str, guild_id: int | None = None, allowed_ratings: list[Rating] | None = None, lang: str | None = None) -> list[int]:
    where = ["secret = false"]

    if allowed_ratings:
        values = ", ".join(f"'{rating.value if hasattr(rating, 'value') else rating}'" for rating in allowed_ratings)
        where.append(f"rating IN ({values})")

    if lang is not None:
        lang_literal = lang.replace("'", "''")
        where.append(f"lang = '{lang_literal}'")

    if guild_id is not None:
        where.append(f"id NOT IN (SELECT egg_id FROM guild_filtered_eggs WHERE guild_id = {guild_id})")

    literal = query.replace("'", "''")

    sql = f"SELECT id FROM egg WHERE {' AND '.join(where)} AND text %> '{literal}' ORDER BY text <->> '{literal}' LIMIT {FUZZY_LIMIT}"

    async with in_transaction() as tx:
        await tx.execute_query(f"SELECT set_config('pg_trgm.word_similarity_threshold', '{FUZZY_THRESHOLD}', true)")
        _, rows = await tx.execute_query(sql)

    return [row[0] for row in rows]

class Eggstras(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def egg_loop(self, ctx: discord.Interaction, mode: str, check: int | None, rating: Rating | None, secret: bool | None):
        if not await utils.ensure_not_ratelimited(ctx, "read"):
            return

        await ctx.response.defer()

        lines, myloc = await self.bot.get_section(ctx, "eggstras/loop")

        guild = await Guild.get_or_none(id=ctx.guild.id) if ctx.guild else None

        allowed = utils.channel_ratings(guild, ctx.channel)

        user, _ = await User.get_or_create(id=ctx.user.id)

        match mode:
            case "collected":
                field = user.collected
            case "created":
                field = user.eggs

        if check is not None:
            egg = await field.filter(id=check).prefetch_related("creator", "origin").first()

            if not egg:
                await ctx.followup.send(myloc[f"not_{mode}"].format(check))
                return

            if egg.rating not in allowed:
                await ctx.followup.send(myloc["rating_not_allowed"].format(check))
                return

            if guild and not guild.allow_ext_lang and egg.lang != guild.lang:
                await ctx.followup.send(myloc["lang_not_allowed"].format(check))
                return

            loop = [egg]
        else:
            query = field.all().prefetch_related("creator", "origin")

            if rating is not None and rating not in allowed:
                await ctx.followup.send(myloc["rating_not_allowed_filter"])
                return

            query = query.filter(rating__in=allowed)

            if rating is not None:
                query = query.filter(rating=rating)

            if secret:
                query = query.filter(secret=True)

            if guild and not guild.allow_ext_lang:
                query = query.filter(lang=guild.lang)

            loop = await query

            if not loop:
                await ctx.followup.send(myloc["empty"])
                return

        eggs = collections.deque(loop)
        eggs.rotate(random.randint(0, len(eggs)))

        view = discord.utils.MISSING
        sfile = discord.utils.MISSING
        if not check:
            view = await views.EggLoop.create(self.bot, lines, myloc, ctx.user, eggs)
            sfile = view.sfile or discord.utils.MISSING

        await ctx.followup.send(file=sfile, view=view)

    @app.command(name="collected", description="collected_description")
    @app.rename(check="collected_check", rating="collected_rating", secret="collected_secret")
    @app.describe(check="collected_check_description", rating="collected_rating_description", secret="collected_secret_description")
    @app.choices(rating=[
        app.Choice(name=app.locale_str("rating_safe"), value=Rating.SAFE),
        app.Choice(name=app.locale_str("rating_questionable"), value=Rating.QUESTIONABLE),
        app.Choice(name=app.locale_str("rating_explicit"), value=Rating.EXPLICIT),
    ])
    @app.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def collected(self, ctx: discord.Interaction, check: int | None, rating: Rating | None, secret: bool | None):
        await self.egg_loop(ctx, "collected", check, rating, secret)

    @app.command(name="my-eggs", description="my-eggs_description")
    @app.rename(check="my-eggs_check", rating="my-eggs_rating", secret="my-eggs_secret")
    @app.describe(check="my-eggs_check_description", rating="my-eggs_rating_description", secret="my-eggs_secret_description")
    @app.choices(rating=[
        app.Choice(name=app.locale_str("rating_safe"), value=Rating.SAFE),
        app.Choice(name=app.locale_str("rating_questionable"), value=Rating.QUESTIONABLE),
        app.Choice(name=app.locale_str("rating_explicit"), value=Rating.EXPLICIT),
    ])
    @app.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def my_eggs(self, ctx: discord.Interaction, check: int | None, rating: Rating | None, secret: bool | None):
        await self.egg_loop(ctx, "created", check, rating, secret)

    @app.command(name="search", description="search_description")
    @app.rename(text="search_text")
    @app.describe(text="search_text_description")
    @app.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def search(self, ctx: discord.Interaction, text: str):
        if not await utils.ensure_not_ratelimited(ctx, "search"):
            return

        await ctx.response.defer()

        lines, myloc = await self.bot.get_section(ctx, "eggstras/search")

        guild = await Guild.get_or_none(id=ctx.guild.id) if ctx.guild else None

        allowed = utils.channel_ratings(guild, ctx.channel)

        query = text.strip()

        if not query:
            await ctx.followup.send(myloc["empty"].format(text))
            return

        base = Egg.all().prefetch_related("creator", "origin")
        base = base.filter(secret=False)
        base = base.filter(rating__in=allowed)

        if guild and not guild.allow_ext_lang:
            base = base.filter(lang=guild.lang)

        if ctx.guild:
            filtered = await Egg.filter(filtered_in__id=ctx.guild.id).values_list("id", flat=True)
            if filtered:
                base = base.filter(id__not_in=filtered)

        norm_query = normalize(query)

        sql = Q(text__iposix_regex=accent_pattern(query))
        for alt in expand(query) - {query}:
            sql |= Q(text__icontains=alt)

        eggs = [egg for egg in await base.filter(sql) if norm_query in normalize(egg.text or "")]

        if eggs:
            eggs.sort(key=lambda egg: (
                normalize(egg.text or "") != norm_query,
                not normalize(egg.text or "").startswith(norm_query),
                len(egg.text or ""),
                egg.id,
            ))
        else:
            lang_filter = guild.lang if (guild and not guild.allow_ext_lang) else None
            ids = await fuzzy_ids(query, ctx.guild.id if ctx.guild else None, allowed, lang_filter)

            if ids:
                fetched = {egg.id: egg for egg in await base.filter(id__in=ids)}

                scored = [(fuzzy_score(query, normalize(egg.text or "")), egg) for egg in fetched.values()]
                scored = [(score, egg) for score, egg in scored if score >= FUZZY_CUTOFF]
                scored.sort(key=lambda item: (-item[0], len(item[1].text or ""), item[1].id))
                eggs = [egg for _, egg in scored]
            else:
                eggs = []

            if not eggs:
                await ctx.followup.send(myloc["empty"].format(query))
                return

        loop = collections.deque(eggs)

        view = await views.EggLoop.create(self.bot, lines, myloc, ctx.user, loop)

        await ctx.followup.send(
            file=view.sfile or discord.utils.MISSING,
            view=view
        )

    leaderboard = app.Group(
        name="leaderboard",
        description="leaderboard_description",
        allowed_contexts=app.AppCommandContext(guild=True, dm_channel=True, private_channel=True)
    )

    async def send_leaderboard(self, ctx: discord.Interaction, leaderboard: utils.Leaderboard, title_key: str, name_resolver, self_id: int):
        if not await utils.ensure_not_ratelimited(ctx, "read"):
            return

        await ctx.response.defer()

        lines, myloc = await self.bot.get_section(ctx, "eggstras/leaderboard")

        entries = await utils.render_entries(self.bot, leaderboard, self_id, name_resolver, myloc["you"])

        e = discord.Embed(
            title=myloc[title_key],
            color=discord.Color.blurple(),
            description="\n".join(entries)
        )
        utils.brand_embed(e, lines)

        await ctx.followup.send(embed=e)

    async def resolve_user_name(self, bot, user_id: int) -> str:
        user = await utils.get_or_fetch_user(bot, user_id)

        if user is None:
            return f"User `{user_id}`"

        addon = ""
        if (await User.get_or_none(id=user_id)).public:
            addon = f" ({discord.utils.escape_markdown(user.name)})"

        return f"**{user.display_name}**{addon}"

    @leaderboard.command(name="leaderboard_collections", description="leaderboard_collections_description")
    async def lb_collections(self, ctx: discord.Interaction):
        await self.send_leaderboard(ctx, utils.Leaderboard(User, "collected"), "collections", self.resolve_user_name, ctx.user.id)

    @leaderboard.command(name="leaderboard_creations", description="leaderboard_creations_description")
    async def lb_creations(self, ctx: discord.Interaction):
        await self.send_leaderboard(ctx, utils.Leaderboard(User, "eggs"), "creations", self.resolve_user_name, ctx.user.id)

    async def resolve_egg_name(self, bot, egg_id: int) -> str:
        egg = await Egg.get_or_none(id=egg_id).prefetch_related("creator")

        if egg is None:
            return f"Egg `{egg_id}`"

        creator = await utils.get_or_fetch_user(bot, egg.creator_id)

        creator_name = f"**{creator.display_name}**" if creator is not None else f"`{egg.creator_id}`"

        return f"**Egg #{egg.id}** by {creator_name}"

    @leaderboard.command(name="leaderboard_battles", description="leaderboard_battles_description")
    async def lb_battles(self, ctx: discord.Interaction):
        await self.send_leaderboard(ctx, utils.Leaderboard(Egg, "battle_wins"), "battles", self.resolve_egg_name, None)

    @leaderboard.command(name="leaderboard_battlers", description="leaderboard_battlers_description")
    async def lb_battlers(self, ctx: discord.Interaction):
        await self.send_leaderboard(ctx, utils.Leaderboard(User, "user_battle_wins"), "battlers", self.resolve_user_name, ctx.user.id)

async def setup(bot: commands.Bot):
    await bot.add_cog(Eggstras(bot))