import os
import random

from schema import Egg, Guild, Rating

from . import misc


def safe_remove(path: str | None) -> None:
    if not path or not os.path.exists(path):
        return

    try:
        os.remove(path)
    except OSError:
        print(f"log: failed to delete file {path}")

def truncate(text: str | None, limit: int) -> str | None:
    if not text:
        return None

    return text[:limit] + ("…" if len(text) > limit else "")

async def egg_delete(egg):
    safe_remove(egg.attach_path)

    await egg.delete()

async def random_egg(guild: Guild | None, channel, *, rating: Rating = None, exclude_ids = None, secret_chance: float = 0.0):
    filtered_ids: list[int] = []
    if guild:
        filtered_ids = list(await Egg.filter(filtered_in__id=guild.id).values_list("id", flat=True))

    def build_query(secret: bool):
        query = Egg.all()

        if guild:
            if filtered_ids:
                query = query.filter(id__not_in=filtered_ids)

            if not guild.allow_ext_lang:
                query = query.filter(lang=guild.lang)

        allowed = misc.channel_ratings(guild, channel)

        if rating:
            query = query.filter(rating=rating)
        else:
            query = query.filter(rating__in=allowed)

        query = query.filter(secret=secret)

        if exclude_ids:
            query = query.exclude(id__in=list(exclude_ids))

        return query

    async def pick(secret: bool):
        query = build_query(secret)
        count = await query.count()

        if count == 0:
            return None

        return await query.offset(random.randint(0, count - 1)).prefetch_related("creator", "origin").first()

    if secret_chance > 0 and random.random() < secret_chance:
        secret_egg = await pick(True)
        if secret_egg is not None:
            return secret_egg

    return await pick(False)