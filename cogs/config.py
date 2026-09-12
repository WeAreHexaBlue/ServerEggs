from datetime import timedelta

import discord
from discord import app_commands as app
from discord.ext import commands

import utils
from schema import Guild, Rating, User, default_ratings


class Config(commands.GroupCog, group_name="config", group_description="config_description"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def guild_setting(self, ctx: discord.Interaction, section: str):
        await ctx.response.defer(ephemeral=True)

        _, myloc = await self.bot.get_section(ctx, f"config/{section}")
        guild, _ = await Guild.get_or_create(id=ctx.guild.id)

        return myloc, guild

    async def lang_autocomplete(self, ctx: discord.Interaction, current: str) -> list[app.Choice[str]]:
        default_name = utils.pick_locale(self.bot.locales, ctx.locale.value).get("lang_default", "Server Default")
        current = current.lower()

        options = []
        if not current or current in default_name.lower():
            options.append(app.Choice(name=default_name, value=""))

        for code, data in sorted(self.bot.locales.items()):
            name = data.get("language_name", code)
            if not current or current in name.lower() or current in code.lower():
                options.append(app.Choice(name=name, value=code))

        return options[:25]

    @app.command(name="lang", description="lang_description")
    @app.rename(code="lang_language")
    @app.describe(code="lang_language_description")
    @app.autocomplete(code=lang_autocomplete)
    @app.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @utils.ratelimit("read")
    async def lang(self, ctx: discord.Interaction, code: str):
        await ctx.response.defer(ephemeral=True)

        if code != "" and code not in self.bot.locales:
            _, myloc = await self.bot.get_section(ctx, "config/lang")
            await ctx.followup.send(myloc["invalid"], ephemeral=True)
            return

        if ctx.guild:
            _, myloc = await self.bot.get_section(ctx, "config/lang")

            if code == "":
                await ctx.followup.send(myloc["no_default"], ephemeral=True)
                return

            if not ctx.permissions.manage_guild:
                await ctx.followup.send(myloc["missing_perms"], ephemeral=True)
                return

            model, id_, cache_key = Guild, ctx.guild.id, f"guild_{ctx.guild.id}"
        else:
            model, id_, cache_key = User, ctx.user.id, f"user_{ctx.user.id}"

        await model.update_or_create(defaults={ "lang": code }, id=id_)
        self.bot.lang_cache[cache_key] = code

        _, myloc = await self.bot.get_section(ctx, "config/lang")

        await ctx.followup.send(myloc["success"], ephemeral=True)

    @app.command(name="allow-user-lang", description="allow-user-lang_description")
    @app.rename(allow="allow-user-lang_allow")
    @app.describe(allow="allow-user-lang_allow_description")
    @app.allowed_contexts(guilds=True, dms=False, private_channels=False)
    @app.checks.has_permissions(manage_guild=True)
    @utils.ratelimit("read")
    async def allow_user_lang(self, ctx: discord.Interaction, allow: bool):
        myloc, guild = await self.guild_setting(ctx, "allow-user-lang")

        cache_key = f"guild_{ctx.guild.id}_allowuserlang"

        if guild.allow_user_lang == allow:
            self.bot.lang_cache[cache_key] = allow
            await ctx.followup.send(myloc["already"], ephemeral=True)
            return

        guild.allow_user_lang = allow
        await guild.save(update_fields=["allow_user_lang"])
        self.bot.lang_cache[cache_key] = guild.allow_user_lang

        await ctx.followup.send(myloc["success"].format(allow), ephemeral=True)

    @app.command(name="server-description", description="server-description_description")
    @app.rename(desc="server-description_desc")
    @app.describe(desc="server-description_desc_description")
    @app.allowed_contexts(guilds=True, dms=False, private_channels=False)
    @app.checks.has_permissions(manage_guild=True)
    @utils.ratelimit("read")
    async def server_description(self, ctx: discord.Interaction, desc: str):
        myloc, guild = await self.guild_setting(ctx, "server-description")

        guild.description = utils.truncate(desc, 300)
        await guild.save(update_fields=["description"])

        await ctx.followup.send(myloc["success"] + "\n" + guild.description, ephemeral=True)

    @app.command(name="privacy", description="privacy_description")
    @app.rename(public="privacy_public")
    @app.describe(public="privacy_public_description")
    @app.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @utils.ratelimit("read")
    async def privacy(self, ctx: discord.Interaction, public: bool):
        await ctx.response.defer(ephemeral=True)

        _, myloc = await self.bot.get_section(ctx, "config/privacy")

        if ctx.guild:
            if not ctx.permissions.manage_guild:
                await ctx.followup.send(myloc["no_permissions"], ephemeral=True)
                return

            guild, _ = await Guild.get_or_create(id=ctx.guild.id)

            has_invite = bool(guild.invite)

            if (has_invite and public) or (not has_invite and not public):
                await ctx.followup.send(myloc["already"], ephemeral=True)
                return

            invite = None
            if public:
                base_channel = ctx.guild.rules_channel or (ctx.guild.text_channels[0] if ctx.guild.text_channels else None)

                if base_channel is None:
                    await ctx.followup.send(myloc["missing_guild_perms"], ephemeral=True)
                    return

                try:
                    inviteobj = await base_channel.create_invite()
                    invite = inviteobj.url
                except discord.errors.Forbidden:
                    await ctx.followup.send(myloc["missing_invite_perms"], ephemeral=True)
                    return

            guild.invite = invite
            await guild.save(update_fields=["invite"])
        else:
            user, _ = await User.get_or_create(id=ctx.user.id)

            if user.public and public:
                await ctx.followup.send(myloc["already"], ephemeral=True)
                return

            user.public = public
            await user.save(update_fields=["public"])

        await ctx.followup.send(myloc["success"].format(myloc["public"] if public else myloc["private"]), ephemeral=True)

    @app.command(name="log", description="log_description")
    @app.rename(channel="log_channel")
    @app.describe(channel="log_channel_description")
    @app.allowed_contexts(guilds=True, dms=False, private_channels=False)
    @app.checks.has_permissions(manage_guild=True)
    @utils.ratelimit("read")
    async def log(self, ctx: discord.Interaction, channel: discord.TextChannel):
        myloc, guild = await self.guild_setting(ctx, "log")

        if channel.id == guild.logch:
            await ctx.followup.send(myloc["already"], ephemeral=True)
            return

        perms = channel.permissions_for(ctx.guild.me)
        if not (perms.view_channel and perms.send_messages and perms.embed_links):
            await ctx.followup.send(myloc["missing_perms"], ephemeral=True)
            return

        guild.logch = channel.id
        await guild.save(update_fields=["logch"])

        await ctx.followup.send(myloc["success"].format(channel.mention), ephemeral=True)

    allowed_ratings = app.Group(
        name="allowed-ratings",
        description="allowed-ratings_description",
        allowed_contexts=app.AppCommandContext(guild=True, dm_channel=False, private_channel=False)
    )

    async def set_allowed_ratings(self, ctx: discord.Interaction, group: str, safe: bool | None, questionable: bool | None, explicit: bool | None):
        myloc, guild = await self.guild_setting(ctx, "allowed-ratings")

        changes = {
            Rating.SAFE: safe,
            Rating.QUESTIONABLE: questionable,
            Rating.EXPLICIT: explicit,
        }

        if all(value is None for value in changes.values()):
            await ctx.followup.send(myloc["no_changes"], ephemeral=True)
            return

        if group == "normal" and changes[Rating.EXPLICIT]:
            await ctx.followup.send(myloc["no_explicit_in_normal"], ephemeral=True)
            return

        if not guild.ratings:
            guild.ratings = default_ratings()

        setting = set(guild.ratings.get(group, []))

        for rating, value in changes.items():
            if value is None:
                continue

            if value:
                setting.add(rating)
            else:
                setting.discard(rating)

        setting = [rating for rating in (Rating.SAFE, Rating.QUESTIONABLE, Rating.EXPLICIT) if rating in setting]

        if guild.ratings.get(group) == setting:
            await ctx.followup.send(myloc["already"], ephemeral=True)
            return

        guild.ratings[group] = setting
        await guild.save(update_fields=["ratings"])

        await ctx.followup.send(myloc["success"], ephemeral=True)

    @allowed_ratings.command(name="allowed-ratings_normal", description="allowed-ratings_normal_description")
    @app.rename(safe="allowed-ratings_normal_s", questionable="allowed-ratings_normal_q", explicit="allowed-ratings_normal_e")
    @app.describe(safe="allowed-ratings_normal_s_description", questionable="allowed-ratings_normal_q_description", explicit="allowed-ratings_normal_e_description")
    @app.checks.has_permissions(manage_guild=True)
    @utils.ratelimit("read")
    async def allowed_ratings_normal(self, ctx: discord.Interaction, safe: bool | None, questionable: bool | None, explicit: bool | None):
        await self.set_allowed_ratings(ctx, "normal", safe, questionable, explicit)

    @allowed_ratings.command(name="allowed-ratings_nsfw", description="allowed-ratings_nsfw_description")
    @app.rename(safe="allowed-ratings_nsfw_s", questionable="allowed-ratings_nsfw_q", explicit="allowed-ratings_nsfw_e")
    @app.describe(safe="allowed-ratings_nsfw_s_description", questionable="allowed-ratings_nsfw_q_description", explicit="allowed-ratings_nsfw_e_description")
    @app.checks.has_permissions(manage_guild=True)
    @utils.ratelimit("read")
    async def allowed_ratings_nsfw(self, ctx: discord.Interaction, safe: bool | None, questionable: bool | None, explicit: bool | None):
        await self.set_allowed_ratings(ctx, "nsfw", safe, questionable, explicit)
    
    @app.command(name="join-button", description="join-button_description")
    @app.rename(viewable="join-button_viewable")
    @app.describe(viewable="join-button_viewable_description")
    @app.checks.has_permissions(manage_guild=True)
    @utils.ratelimit("read")
    async def join_button(self, ctx: discord.Interaction, viewable: bool):
        myloc, guild = await self.guild_setting(ctx, "join-button")

        if guild.view_join_button == viewable:
            await ctx.followup.send(myloc["already"], ephemeral=True)
            return
        
        guild.view_join_button = viewable
        await guild.save(update_fields=["view_join_button"])

        await ctx.followup.send(myloc["success"].format(viewable), ephemeral=True)
    
    @app.command(name="battle-time", description="battle-time_description")
    @app.rename(minutes="battle-time_minutes")
    @app.describe(minutes="battle-time_minutes_description")
    @app.checks.has_permissions(manage_guild=True)
    @utils.ratelimit("read")
    async def battle_time(self, ctx: discord.Interaction, minutes: app.Range[int, 1, None]):
        myloc, guild = await self.guild_setting(ctx, "battle-time")

        newdelta = timedelta(minutes=minutes)

        if guild.battle_time == newdelta:
            await ctx.followup.send(myloc["already"], ephemeral=True)
            return
        
        guild.battle_time = newdelta
        await guild.save(update_fields=["battle_time"])

        await ctx.followup.send(myloc["success"].format(minutes), ephemeral=True)
    
    @app.command(name="channel-rating", description="channel-rating_description")
    @app.rename(channel="channel-rating_channel", rating="channel-rating_rating")
    @app.describe(channel="channel-rating_channel_description", rating="channel-rating_rating_description")
    @app.choices(rating=[
        app.Choice(name=app.locale_str("rating_safe"), value=Rating.SAFE),
        app.Choice(name=app.locale_str("rating_questionable"), value=Rating.QUESTIONABLE),
        app.Choice(name=app.locale_str("rating_explicit"), value=Rating.EXPLICIT),
    ])
    @app.checks.has_permissions(manage_guild=True)
    @utils.ratelimit("read")
    async def channel_rating(self, ctx: discord.Interaction, channel: discord.TextChannel, rating: Rating):
        myloc, guild = await self.guild_setting(ctx, "channel-rating")

        category = rating.value.lower()

        if channel.id in guild.channel_ratings[category]:
            await ctx.followup.send(myloc["already"], ephemeral=True)
            return
        
        for key in guild.channel_ratings:
            if channel.id in guild.channel_ratings[key]:
                guild.channel_ratings[key].remove(channel.id)
        
        guild.channel_ratings[category].append(channel.id)
        await guild.save(update_fields=["channel_ratings"])

        await ctx.followup.send(myloc["success"].format(channel.mention, rating), ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Config(bot))