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

from .attach import UPLOAD_LIMIT, get_content_type


async def scan_csam(file: discord.File) -> (bool, bool, bytes):
    scanbytes = file.fp.read()
    file.fp.seek(0)

    content_type = get_content_type(file.filename)

    if content_type in {"audio", "video"} and len(scanbytes) > UPLOAD_LIMIT:
            print(f"ERROR: Rejected upload: media size {round(len(scanbytes) / 1024 / 1024, 1)}MB exceeds limit of {UPLOAD_LIMIT // 1024 // 1024}MB")
            return False, True, scanbytes

    if content_type in {"audio"}:
        return False, False, scanbytes

    api_user = os.getenv("ARACHNID_USER")
    api_password = os.getenv("ARACHNID_PASSWORD")

    if not api_user or not api_password:
        print("[Warning] Arachnid Shield credentials missing. Skipping CSAM scan.")
        return False, False, scanbytes

    endpoint = "https://shield.projectarachnid.com/v1/media"
    auth = aiohttp.BasicAuth(api_user, api_password)
    headers = {"Content-Type": content_type or "application/octet-stream"}

    if content_type in {"video"}:
        hashes = await extract_video_pdq_hashes(scanbytes)
        if not hashes:
            print("WARN: Could not extract frame hashes from video.")
            return False, False, scanbytes

        endpoint = "https://shield.projectarachnid.com/v1/pdq"
        payload = {"hashes": hashes}

        try:
            async with aiohttp.ClientSession() as session, session.post(endpoint, auth=auth, json=payload, timeout=900) as response:
                    if response.status == 200:
                        data = await response.json()

                        for match in data.get("scanned_hashes", {}).values():
                            classification = match.get("classification", "")

                            if classification in ["csam", "harmful-abusive-material"]:
                                print(f"CRITICAL: HARMFUL CONTENT DETECTED: {classification}")
                                return True, False, None

                        return False, False, scanbytes
                    else:
                        print(f"ERROR: Arachnid Shield PDQ Error: HTTP {response.status} {await response.text()}")
                        return False, False, scanbytes
        except (TimeoutError, aiohttp.ClientError) as e:
            print(f"ERROR: Arachnid Shield connection error: {e}")
            return False, False, scanbytes

    endpoint = "https://shield.projectarachnid.com/v1/media"
    guessed_mime, _ = mimetypes.guess_type(file.filename)
    headers = {"Content-Type": guessed_mime or "application/octet-stream"}

    try:
        async with aiohttp.ClientSession() as session, session.post(endpoint, auth=auth, data=scanbytes, headers=headers, timeout=20) as response:
                if response.status == 200:
                    data = await response.json()

                    classification = data.get("classification", "")
                    if classification in ["csam", "harmful-abusive-material"]:
                        print(f"CRITICAL: HARMFUL CONTENT DETECTED: {classification}")
                        return True, False, None

                    return False, False, scanbytes
                else:
                    print(f"ERROR: Arachnid Shield Media Error: HTTP {response.status} {await response.text()}")
                    return False, False, scanbytes
    except (TimeoutError, aiohttp.ClientError) as e:
        print(f"ERROR: Arachnid Shield connection error: {e}")
        return False, False, scanbytes

async def extract_video_pdq_hashes(vidbytes: bytes) -> list[str]:
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
            print(f"ERROR: FFmpeg extraction failed: {stderr.decode(errors='replace')}")
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
        print(f"ERROR: Failed extracting PDQ hashes: {e}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return hashes