import discord

import utils
from schema import Rating


class ExtraAttachmentButton(discord.ui.Button):
    def __init__(self, label: str, *, style=discord.ButtonStyle.primary, file=None, link=None):
        super().__init__(label=label, style=style, custom_id="servereggs:extra_attachment")

        self.extrafile = file
        self.extralink = link

    async def callback(self, ctx: discord.Interaction):
        if not await utils.ensure_not_ratelimited(ctx, "interact"):
            return

        await utils.send_extra(ctx, self.extrafile, self.extralink)

def action_button(label: str, style, callback) -> discord.ui.Button:
    button = discord.ui.Button(label=label, style=style)
    button.callback = callback
    return button

def text_view(content: str) -> discord.ui.LayoutView:
    view = discord.ui.LayoutView(timeout=None)
    view.add_item(discord.ui.TextDisplay(content))

    return view

class EggSelectModal(discord.ui.Modal):
    FIELD = ""
    LABEL_KEY = ""
    DESC_KEY = ""
    PLACEHOLDER_KEY = ""

    def __init__(self, myloc: dict, egg, *, after_set=None):
        self.myloc = myloc
        self.egg = egg
        self.after_set = after_set

        super().__init__(title=myloc["title"])

        self.field = discord.ui.Label(
            text=myloc[self.LABEL_KEY],
            description=myloc[self.DESC_KEY],
            component=discord.ui.Select(
                placeholder=myloc[self.PLACEHOLDER_KEY],
                options=self.build_options(),
            )
        )

        self.add_item(self.field)

    def build_options(self) -> list[discord.SelectOption]:
        raise NotImplementedError

    def parse(self, raw: str):
        raise NotImplementedError

    async def on_submit(self, ctx: discord.Interaction):
        await ctx.response.defer(ephemeral=True)

        try:
            value, display = self.parse(self.field.component.values[0])
        except (ValueError, KeyError):
            await ctx.followup.send(self.myloc["invalid"], ephemeral=True)
            return

        setattr(self.egg, self.FIELD, value)
        await self.egg.save(update_fields=[self.FIELD])

        await ctx.followup.send(self.myloc["success"].format(self.egg.id, display), ephemeral=True)

        if self.after_set:
            await self.after_set(ctx, self.egg, value)

class RatingModal(EggSelectModal):
    FIELD = "rating"
    LABEL_KEY = "rating"
    DESC_KEY = "rating_desc"
    PLACEHOLDER_KEY = "rating_placeholder"

    def __init__(self, myloc: dict, egg, *, after_set=None):
        self.names = {
            Rating.SAFE: myloc["safe"],
            Rating.QUESTIONABLE: myloc["questionable"],
            Rating.EXPLICIT: myloc["explicit"],
        }
        super().__init__(myloc, egg, after_set=after_set)

    def build_options(self):
        current = utils.coerce_rating(self.egg.rating).value
        return [
            discord.SelectOption(label=self.names[rating], value=rating.value, default=(current == rating.value))
            for rating in (Rating.SAFE, Rating.QUESTIONABLE, Rating.EXPLICIT)
        ]

    def parse(self, raw: str):
        rating = Rating(raw)
        return rating, self.names[rating]

class LangModal(EggSelectModal):
    FIELD = "lang"
    LABEL_KEY = "lang"
    DESC_KEY = "lang_desc"
    PLACEHOLDER_KEY = "lang_placeholder"

    def __init__(self, bot, myloc: dict, egg, *, after_set=None):
        self.bot = bot
        super().__init__(myloc, egg, after_set=after_set)

    def build_options(self):
        current = self.egg.lang
        return [
            discord.SelectOption(
                label=data.get("language_name", code),
                value=code,
                default=(code == current),
            )
            for code, data in sorted(self.bot.locales.items())
        ][:25]

    def parse(self, raw: str):
        if raw not in self.bot.locales:
            raise ValueError(f"Unknown language: {raw}")
        return raw, self.bot.locales[raw].get("language_name", raw)