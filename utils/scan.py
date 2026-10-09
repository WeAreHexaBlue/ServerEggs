import asyncio
import base64
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