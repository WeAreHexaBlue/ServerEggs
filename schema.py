from datetime import timedelta
from enum import StrEnum

from tortoise import fields, models
from tortoise.fields.base import OnDelete


class Rating(StrEnum):
    SAFE = "SAFE"
    QUESTIONABLE = "QUESTIONABLE"
    EXPLICIT = "EXPLICIT"

class BattleStatus(StrEnum):
    OPEN = "OPEN"
    FINISHED = "FINISHED"

def default_ratings() -> dict:
    return {
        "normal": [Rating.SAFE, Rating.QUESTIONABLE],
        "nsfw": [Rating.SAFE, Rating.QUESTIONABLE, Rating.EXPLICIT]
    }

def default_rated_channels() -> dict:
    return {
        "safe": [],
        "questionable": [],
        "explicit": []
    }

class Egg(models.Model):
    id = fields.IntField(primary_key=True)

    text = fields.TextField(null=True)
    attach_path = fields.TextField(null=True)
    attach_hash = fields.CharField(64, null=True, index=True)
    attach_link = fields.TextField(null=True)

    lang = fields.CharField(5, default="en")
    rating = fields.CharEnumField(enum_type=Rating, default=Rating.SAFE)

    secret = fields.BooleanField(default=False)

    reports = fields.ReverseRelation["Report"]

    creator = fields.ForeignKeyField("eggs.User", "eggs", null=True, on_delete=OnDelete.SET_NULL)
    origin = fields.ForeignKeyField("eggs.Guild", "eggs", null=True, on_delete=OnDelete.SET_NULL)

    created_at = fields.DatetimeField(auto_now_add=True)
    edited_at = fields.DatetimeField(auto_now=True)

    @classmethod
    async def get_with_related(cls, id):
        return await cls.get_or_none(id=id).prefetch_related("creator", "origin")

class Guild(models.Model):
    id = fields.BigIntField(primary_key=True, generated=False, unique=True, db_index=True)

    description = fields.TextField(null=True)
    invite = fields.TextField(null=True)

    lang = fields.CharField(5, default="en")
    allow_ext_lang = fields.BooleanField(default=True)
    view_join_button = fields.BooleanField(default=True)

    ratings = fields.JSONField(default=default_ratings)
    channel_ratings = fields.JSONField(default=default_rated_channels)

    logch = fields.BigIntField(null=True)

    battle_time = fields.TimeDeltaField(default=timedelta(minutes=10))

    filtered: fields.ManyToManyField["Egg"] = fields.ManyToManyField("eggs.Egg", related_name="filtered_in", through="guild_filtered_eggs")

    eggs = fields.ReverseRelation["Egg"]

class User(models.Model):
    id = fields.BigIntField(primary_key=True, generated=False, unique=True, db_index=True)

    lang = fields.CharField(5, default="")
    banned = fields.BooleanField(default=False)
    public = fields.BooleanField(default=True)

    allow_explicit_dms = fields.BooleanField(default=False)
    last_daily_at = fields.DatetimeField(null=True, db_index=True)

    collected: fields.ManyToManyRelation["Egg"] = fields.ManyToManyField("eggs.Egg", related_name="collectors", through="user_collected_eggs")

    eggs = fields.ReverseRelation["Egg"]
    reports = fields.ReverseRelation["Report"]

class Battle(models.Model):
    id = fields.BigIntField(primary_key=True)

    guild = fields.ForeignKeyField("eggs.Guild", "battles")

    egg_a = fields.ForeignKeyField("eggs.Egg", "battles_as_a")
    egg_b = fields.ForeignKeyField("eggs.Egg", "battles_as_b")

    user_a = fields.ForeignKeyField("eggs.User", "challenges_sent", null=True)
    user_b = fields.ForeignKeyField("eggs.User", "challenges_received", null=True)

    channel_id = fields.BigIntField(null=True)
    message_id = fields.BigIntField(null=True)

    ends_at = fields.DatetimeField(db_index=True)
    status = fields.CharEnumField(enum_type=BattleStatus, default=BattleStatus.OPEN, max_length=10)
    winner = fields.ForeignKeyField("eggs.Egg", "battle_wins", null=True)
    winner_user = fields.ForeignKeyField("eggs.User", "user_battle_wins", null=True)

    class Meta:
        table = "battle"

class BattleVote(models.Model):
    id = fields.BigIntField(primary_key=True)

    battle = fields.ForeignKeyField("eggs.Battle", "votes")
    voter = fields.ForeignKeyField("eggs.User", "battle_votes")
    choice = fields.IntField()

    class Meta:
        table = "battle_vote"
        unique_together = (("battle", "voter"),)

class Report(models.Model):
    id = fields.BigIntField(primary_key=True)

    egg = fields.ForeignKeyField("eggs.Egg", "reports")
    reporter = fields.ForeignKeyField("eggs.User", "reports")

    reason = fields.CharField(max_length=200, null=True)
    log_message_id = fields.BigIntField(null=True)

    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        unique_together = (("egg", "reporter"),)