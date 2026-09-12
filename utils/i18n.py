import copy
import json
import os

FALLBACK_LANG = "en"

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
    if isinstance(obj, dict):
        return {key: resolve_lang_refs(val, root) for key, val in obj.items()}
    if isinstance(obj, list):
        return [resolve_lang_refs(val, root) for val in obj]

    return resolve_lang_ref(obj, root, set())

def deep_merge(base: dict, override: dict) -> dict:
    merged = copy.deepcopy(base)

    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)

    return merged

def find_missing_paths(base: dict, override: dict, prefix: str = "") -> list[str]:
    missing = []

    for key, value in base.items():
        path = f"{prefix}/{key}" if prefix else key

        if not isinstance(override, dict) or key not in override:
            missing.append(path)
        elif isinstance(value, dict) and isinstance(override[key], dict):
            missing.extend(find_missing_paths(value, override[key], path))

    return missing

def load_locale_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as lines:
        data = json.load(lines)

    data["lines"] = resolve_lang_refs(data.get("lines", {}), data.get("lines", {}))

    return data

def load_locales(lang_dir: str = "./lang") -> dict:
    raw = {}

    for file in sorted(os.listdir(lang_dir)):
        if file.endswith(".json"):
            raw[file[:-5]] = load_locale_file(os.path.join(lang_dir, file))

    if FALLBACK_LANG not in raw:
        raise FileNotFoundError(f"Fallback locale '{FALLBACK_LANG}.json' not found in {lang_dir}")

    locales = {FALLBACK_LANG: raw[FALLBACK_LANG]}

    for code, data in raw.items():
        if code == FALLBACK_LANG:
            continue

        missing = find_missing_paths(raw[FALLBACK_LANG], data)
        if missing:
            print(f"WARN: locale '{code}' missing {len(missing)} keys, fell back to '{FALLBACK_LANG}': {', '.join(missing)}")

        locales[code] = deep_merge(raw[FALLBACK_LANG], data)

    return locales

def pick_locale(locales: dict, code: str | None) -> dict:
    if code and code in locales:
        return locales[code]

    if code and "-" in code:
        short = code.split("-")[0]
        if short in locales:
            return locales[short]

    return locales[FALLBACK_LANG]