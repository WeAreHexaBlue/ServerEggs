import copy
import json
import os
import re

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

TOKEN = re.compile(r"\{(link|brand)_([a-z0-9_]+)\}")

def substitute_tokens(value, unknown: set[str]):
    def replace(match: re.Match) -> str:
        prefix, name = match.group(1), match.group(2)
        table = LINKS if prefix == "link" else brand_values()

        if name not in table:
            unknown.add(f"{prefix}_{name}")
            return match.group(0)

        return table[name]

    def substitute(text):
        if not isinstance(text, str) or "{" not in text:
            return text

        return TOKEN.sub(replace, text)

    return map_strings(value, substitute)

def load_locales(lang_dir: str = "./lang") -> dict[str, dict]:
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
            print(f"WARN: locale `{code}` missing {len(missing)} keys, fell back to `{FALLBACK_LANG}`: {", ".join(missing)}")

        locales[code] = resolve_lines(deep_merge(fallback, data))

    unknown: set[str] = set()
    for code, data in locales.items():
        locales[code] = substitute_tokens(data, unknown)

    if unknown:
        print(f"WARN: unknown tokens, left unresolved: {", ".join(sorted("{" + name + "}" for name in unknown))}")

    return locales

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