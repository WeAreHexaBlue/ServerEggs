import copy
import json
import os
import re
from collections.abc import Callable

import discord
from discord import app_commands as app

FALLBACK_LANG = "en"
DISCORD_APP_ID = "886686500845138041"

BRAND = {
    "name": "Server Eggs",
    "owner": "HexaBlue",
    "footer": "{name} by {owner}",
    "repository": "WeAreHexaBlue/ServerEggs",
    "app_id": DISCORD_APP_ID,
    "icons": {
        "author": "icons/seggs.png",
        "footer": "icons/hexablue.png",
        "icon": "icons/seggs_bg.png",
    },
    "emojis": {
        "header": "<:egg:1535645170400370729>",
        "footer": "<:HexaBlue:1544850025375465512>",
    },
    "links": {
        "github": "https://github.com/WeAreHexaBlue/ServerEggs",
        "kofi": "https://ko-fi.com/hexablue",
        "weblate": "https://hosted.weblate.org/projects/seggs",
        "support": "https://discord.gg/G9vfEZGZnT",
        "dm": f"https://discord.com/users/{DISCORD_APP_ID}",
        "store": f"https://discord.com/discovery/applications/{DISCORD_APP_ID}/store",
    },
}
LINKS = BRAND["links"]

def brand_values() -> dict[str, str]:
    values = {key: value for key, value in BRAND.items() if isinstance(value, str)}

    def resolve(value: str) -> str:
        for key, resolved in values.items():
            value = value.replace("{" + key + "}", resolved)

        return value

    return {key: resolve(value) for key, value in values.items()}

def icon_url(name: str) -> str:
    path = BRAND["icons"][name]

    if path.startswith(("http://", "https://")):
        return path

    return f"https://github.com/{BRAND['repository']}/blob/main/{path}?raw=true"

def map_strings(obj, fn):
    if isinstance(obj, dict):
        return {key: map_strings(val, fn) for key, val in obj.items()}
    if isinstance(obj, list):
        return [map_strings(val, fn) for val in obj]

    return fn(obj)

def resolve_lang_ref(value, root, seen):
    if not isinstance(value, str) or not value.startswith("$"):
        return value

    if value in seen:
        raise ValueError(f"Circular language reference: {value}")

    seen.add(value)

    node = root
    for part in value[1:].split("."):
        if not isinstance(node, dict) or part not in node:
            raise KeyError(f"Unresolved language reference: {value}")
        node = node[part]

    return resolve_lang_ref(node, root, seen)

def resolve_lang_refs(obj, root):
    return map_strings(obj, lambda value: resolve_lang_ref(value, root, set()))

def resolve_lines(data: dict) -> dict:
    lines = data.get("lines", {})
    data["lines"] = resolve_lang_refs(lines, lines)

    return data

def deep_merge(base: dict, override: dict) -> dict:
    merged = copy.deepcopy(base)

    for key, value in override.items():
        if value == "":
            continue
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)

    return merged

def find_missing_paths(base: dict, override: dict, prefix: str = "") -> list[str]:
    missing = []

    for key, value in base.items():
        path = f"{prefix}/{key}" if prefix else key

        if isinstance(value, str) and value.startswith("$"):
            continue

        if not isinstance(override, dict) or key not in override or override[key] == "":
            missing.append(path)
        elif isinstance(value, dict) and isinstance(override[key], dict):
            missing.extend(find_missing_paths(value, override[key], path))

    return missing

TOKEN = re.compile(r"\{(?P<prefix>[a-z][a-z0-9]*)_(?P<name>[a-z0-9][a-z0-9_-]*)\}")
LOCALE_TOKEN_PREFIXES = ("command", "param", "choice")

TokenResolver = Callable[[str], str | None]

def token_resolvers(locales: dict | None = None, locale: str | None = None) -> dict[str, TokenResolver]:
    resolvers: dict[str, TokenResolver] = {
        "brand": brand_values().get,
        "link": LINKS.get,
    }

    if locales is not None and locale is not None:
        locale_data = pick_locale(locales, locale)
        for prefix in LOCALE_TOKEN_PREFIXES:
            resolvers[prefix] = locale_data.get

    return resolvers

def token_names(value, prefix: str) -> set[str]:
    names: set[str] = set()

    def walk(node):
        if isinstance(node, dict):
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)
        elif isinstance(node, str):
            names.update(match.group("name") for match in TOKEN.finditer(node) if match.group("prefix") == prefix)

    walk(value)

    return names

def resolve_tokens(value, resolvers: dict[str, TokenResolver], unknown: set[str] | None = None):
    def replace(match: re.Match) -> str:
        prefix, name = match.group("prefix"), match.group("name")
        resolver = resolvers.get(prefix)

        if resolver is None:
            return match.group(0)

        resolved = resolver(name)
        if resolved is None:
            if unknown is not None:
                unknown.add(f"{prefix}_{name}")
            return match.group(0)

        return resolved

    def substitute(text):
        if not isinstance(text, str) or "{" not in text:
            return text

        return TOKEN.sub(replace, text)

    return map_strings(value, substitute)

def load_locales(lang_dir: str = "./lang") -> tuple[dict[str, dict], list[str]]:
    warnings: list[str] = []
    raw = {}

    for file in sorted(os.listdir(lang_dir)):
        if file.endswith(".json"):
            with open(os.path.join(lang_dir, file), encoding="utf-8") as handle:
                raw[file[:-5]] = json.load(handle)

    if FALLBACK_LANG not in raw:
        raise FileNotFoundError(f"Fallback locale `{FALLBACK_LANG}.json` not found in {lang_dir}")

    fallback = copy.deepcopy(raw[FALLBACK_LANG])
    locales = {FALLBACK_LANG: resolve_lines(raw[FALLBACK_LANG])}

    for code, data in raw.items():
        if code == FALLBACK_LANG:
            continue

        missing = find_missing_paths(fallback, data)
        if missing:
            warnings.append(f"Locale `{code}` missing {len(missing)} keys, fell back to `{FALLBACK_LANG}`: {", ".join(missing)}")

        locales[code] = resolve_lines(deep_merge(fallback, data))

    unknown: set[str] = set()
    resolvers = token_resolvers()
    for code, data in locales.items():
        locales[code] = resolve_tokens(data, resolvers, unknown)

    if unknown:
        warnings.append(f"Unknown tokens, left unresolved: {", ".join(sorted("{" + name + "}" for name in unknown))}")

    name_keys = set(fallback) - { "language_name", "lines" }
    for prefix in LOCALE_TOKEN_PREFIXES:
        unknown_names: set[str] = set()
        for data in raw.values():
            unknown_names.update(token_names(data, prefix) - name_keys)

        if unknown_names:
            warnings.append(f"Unknown {prefix} tokens: {", ".join(sorted("{" + name + "}" for name in unknown_names))}")

    return locales, warnings

def lang_base(code: str | None) -> str | None:
    if not code:        return code

    return str(code).split("-", 1)[0]

def pick_locale(locales: dict, code: str | None) -> dict:
    if code and code in locales:
        return locales[code]

    if code and "-" in code:
        short = code.split("-")[0]
        if short in locales:
            return locales[short]

    return locales[FALLBACK_LANG]

async def lang_autocomplete(ctx: discord.Interaction, current: str) -> list[app.Choice[str]]:
    default_name = pick_locale(ctx.client.locales, ctx.locale.value).get("lang_default", "Server Default")
    current = current.lower()

    options = []
    if not current or current in default_name.lower():
        options.append(app.Choice(name=default_name, value=""))

    for code, data in sorted(ctx.client.locales.items()):
        name = data.get("language_name", code)
        if not current or current in name.lower() or current in code.lower():
            options.append(app.Choice(name=name, value=code))

    return options[:25]