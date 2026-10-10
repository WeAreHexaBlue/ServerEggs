import asyncio
import base64
import io
import mimetypes
import os
import tempfile

import aiohttp
import discord
import numpy
import pdqhash
from PIL import Image

from . import log, misc
from .attach import UPLOAD_LIMIT, get_content_type

HARMFUL_CLASSIFICATIONS = ("csam", "harmful-abusive-material")

async def run_csam_scan(endpoint: str, auth: aiohttp.BasicAuth, bot, scanbytes: bytes, label: str, get_classifications, *, timeout, json=None, data=None, headers=None) -> (bool, bool, bytes | None):
    session = misc.http_session(bot)

    try:
        async with session.post(endpoint, auth=auth, json=json, data=data, headers=headers, timeout=timeout) as response:
            if response.status == 200:
                payload = await response.json()

                for classification in get_classifications(payload):
                    if classification in HARMFUL_CLASSIFICATIONS:
                        await log.log_error(bot, f"CRITICAL: HARMFUL CONTENT DETECTED: {classification}")
                        return True, False, None

                return False, False, scanbytes
            else:
                await log.log_error(bot, f"ERROR: Arachnid Shield {label} Error: HTTP {response.status} {await response.text()}")
                return False, False, scanbytes
    except (TimeoutError, aiohttp.ClientError) as e:
        await log.log_error(bot, f"ERROR: Arachnid Shield connection error: {e}")
        return False, False, scanbytes

async def scan_csam(file: discord.File, bot=None) -> (bool, bool, bytes):
    scanbytes = file.fp.read()
    file.fp.seek(0)

    content_type = get_content_type(file.filename)

    if content_type in {"audio", "video"} and len(scanbytes) > UPLOAD_LIMIT:
        await log.log_error(bot, f"ERROR: Rejected upload: media size {round(len(scanbytes) / 1024 / 1024, 1)}MB exceeds limit of {UPLOAD_LIMIT // 1024 // 1024}MB")
        return False, True, scanbytes

    if content_type == "audio":
        return False, False, scanbytes

    api_user = os.getenv("ARACHNID_USER")
    api_password = os.getenv("ARACHNID_PASSWORD")

    if not api_user or not api_password:
        await log.log_error(bot, "[Warning] Arachnid Shield credentials missing. Skipping CSAM scan.")
        return False, False, scanbytes

    endpoint = "https://shield.projectarachnid.com/v1/media"
    auth = aiohttp.BasicAuth(api_user, api_password)

    if content_type == "video":
        hashes = await extract_video_pdq_hashes(scanbytes, bot)
        if not hashes:
            await log.log_error(bot, "WARN: Could not extract frame hashes from video.")
            return False, False, scanbytes

        endpoint = "https://shield.projectarachnid.com/v1/pdq"
        payload = {"hashes": hashes}

        return await run_csam_scan(
            endpoint, auth, bot, scanbytes, "PDQ",
            lambda data: [match.get("classification", "") for match in data.get("scanned_hashes", {}).values()],
            timeout=900, json=payload,
        )

    endpoint = "https://shield.projectarachnid.com/v1/media"
    guessed_mime, _ = mimetypes.guess_type(file.filename)
    headers = {"Content-Type": guessed_mime or "application/octet-stream"}

    return await run_csam_scan(
        endpoint, auth, bot, scanbytes, "Media",
        lambda data: [data.get("classification", "")],
        timeout=20, data=scanbytes, headers=headers,
    )

def csam_scan_configured() -> bool:
    return bool(os.getenv("ARACHNID_USER") and os.getenv("ARACHNID_PASSWORD"))

def csam_scan_needed(filename: str | None) -> bool:
    if not filename or not csam_scan_configured():
        return False

    return get_content_type(filename) in {"image", "video"}

async def _notify_uploader(bot, egg, key: str) -> None:
    from schema import Guild, User

    from .i18n import pick_locale

    dbuser = await User.get_or_none(id=egg.creator_id)
    guild = await Guild.get_or_none(id=egg.origin_id) if egg.origin_id else None

    lang = (dbuser.lang if dbuser and dbuser.lang else None) or (guild.lang if guild else None) or "en"
    myloc = bot.get_lines("eggs/create_edit", pick_locale(bot.locales, lang)["lines"])

    user = await misc.get_or_fetch_user(bot, egg.creator_id)

    try:
        await user.send(myloc[key])
    except (AttributeError, discord.HTTPException):
        pass

async def _log_cleared_egg(bot, egg, guild_id: int | None, actor_id: int | None, is_edit: bool) -> None:
    from schema import Guild

    from .i18n import pick_locale

    if guild_id is None:
        return

    guild = await Guild.get_or_none(id=guild_id)
    if guild is None:
        return

    lines = pick_locale(bot.locales, guild.lang)["lines"]
    creator = await misc.get_or_fetch_user(bot, egg.creator_id)
    actor = await misc.get_or_fetch_user(bot, actor_id)

    await log.log_egg(bot, lines, guild, egg, creator, actor, is_edit)

def _still_same_upload(egg, expected_hash: str | None, expected_link: str | None) -> bool:
    if expected_hash is not None:
        return egg.attach_hash == expected_hash

    if expected_link is not None:
        return egg.attach_link == expected_link

    return False

async def _finish_csam_scan(bot, egg_id: int, scanbytes: bytes, filename: str, *, expected_hash: str | None = None, expected_link: str | None = None, guild_id: int | None = None, actor_id: int | None = None, is_edit: bool = False) -> None:
    from schema import Egg, User

    from .eggs import egg_delete

    try:
        scan, too_long, _ = await scan_csam(discord.File(io.BytesIO(scanbytes), filename=filename), bot)
    except Exception as e:  # noqa: BLE001
        await log.log_error(bot, f"ERROR: Background CSAM scan failed for Egg #{egg_id}: {e}")
        return

    egg = await Egg.get_or_none(id=egg_id)
    if egg is None or not egg.pending_scan or not _still_same_upload(egg, expected_hash, expected_link):
        return

    if scan or too_long:
        await egg_delete(egg)

        if scan and egg.creator_id is not None:
            creator = await User.get_or_none(id=egg.creator_id)
            if creator is not None:
                creator.banned = True
                await creator.save(update_fields=["banned"])

        await _notify_uploader(bot, egg, "illegal" if scan else "too_big")
        return

    egg.pending_scan = False
    await egg.save(update_fields=["pending_scan"])

    await _log_cleared_egg(bot, egg, guild_id, actor_id, is_edit)

def schedule_csam_scan(bot, egg_id: int, scanbytes: bytes, filename: str, **kwargs) -> asyncio.Task:
    return asyncio.create_task(_finish_csam_scan(bot, egg_id, scanbytes, filename, **kwargs), name=f"csam-scan-{egg_id}")

async def resume_pending_scans(bot) -> None:
    from schema import Egg

    from .attach import url_to_file

    await bot.wait_until_ready()

    for egg in await Egg.filter(pending_scan=True).all():
        try:
            scanbytes = None
            filename = "media"

            if egg.attach_path and os.path.exists(egg.attach_path):
                filename = os.path.basename(egg.attach_path)
                with open(egg.attach_path, "rb") as handle:
                    scanbytes = handle.read()
            elif egg.attach_link:
                scanned = await url_to_file(egg.attach_link, bot)
                if scanned is not None:
                    filename = scanned.filename
                    scanbytes = scanned.fp.read()

            if scanbytes is None:
                await log.log_error(bot, f"ERROR: Could not resume CSAM scan for Egg #{egg.id}: no media available")
                continue

            await _finish_csam_scan(
                bot, egg.id, scanbytes, filename,
                expected_hash=egg.attach_hash, expected_link=egg.attach_link,
                guild_id=egg.origin_id, actor_id=egg.creator_id, is_edit=False,
            )
        except Exception as e:  # noqa: BLE001
            await log.log_error(bot, f"ERROR: Could not resume CSAM scan for Egg #{egg.id}: {e}")

async def extract_video_pdq_hashes(vidbytes: bytes, bot=None) -> list[str]:
    with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as tmp:
        tmp.write(vidbytes)
        tmp_path = tmp.name

    out_pattern = f"{tmp_path}_%03d.jpg"
    hashes = []

    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", tmp_path,
            "-vf", "fps=0.5,scale=256:256",
            "-vframes", "30",
            "-q:v", "4",
            out_pattern,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()

        if proc.returncode != 0:
            await log.log_error(bot, f"ERROR: FFmpeg extraction failed: {stderr.decode(errors='replace')}")
            return []

        dir_name = os.path.dirname(tmp_path)
        base_name = os.path.basename(tmp_path)

        for fname in sorted(os.listdir(dir_name)):
            if fname.startswith(base_name) and fname.endswith(".jpg"):
                frame_path = os.path.join(dir_name, fname)
                try:
                    with Image.open(frame_path) as img:
                        rgb_img = img.convert("RGB")
                        arr = numpy.asarray(rgb_img)
                        hash_res = pdqhash.compute(arr)

                        hash_vec = hash_res[0] if isinstance(hash_res, tuple) else hash_res

                        if len(hash_vec) == 256:
                            raw_32_bytes = numpy.packbits(hash_vec).tobytes()
                        else:
                            raw_32_bytes = bytes(hash_vec[:32])

                        b64_hash = base64.b64encode(raw_32_bytes).decode("ascii")
                        hashes.append(b64_hash)
                finally:
                    if os.path.exists(frame_path):
                        os.remove(frame_path)
    except (FileNotFoundError, OSError, ValueError, TypeError) as e:
        await log.log_error(bot, f"ERROR: Failed extracting PDQ hashes: {e}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return hashes