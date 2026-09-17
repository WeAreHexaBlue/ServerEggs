import asyncio
import hashlib
import html
import io
import json
import mimetypes
import os
import re
import tempfile
from urllib.parse import urlparse

import aiohttp
import discord
import dotenv
import imagehash
from PIL import Image

dotenv.load_dotenv()

SUPPORTED_FILETYPE_REGEX = r'\.(gif|png|jpg|jpeg|webp|mp4|webm|mp3|ogg|wav|opus|m4a)(?:[?#].*)?$'

UPLOAD_LIMIT = 20 * 1024 * 1024

NATIVE_VIDEO_CODECS = {"h264", "vp8", "vp9", "av1"}
NATIVE_AUDIO_CODECS = {"aac", "mp3", "opus", "vorbis"}
SUPPORTED_MEDIA_EXTS = {
    "video": {"mp4", "webm"},
    "audio": {"mp3", "ogg", "m4a", "wav", "opus"},
}

class UnsupportedMedia(Exception):
    pass

def get_content_type(file: discord.Attachment | str) -> str | None:
    if isinstance(file, discord.Attachment):
        content_type = file.content_type
    else:
        clean_name = file.split("?")[0].split("#")[0]
        guessed = mimetypes.guess_type(clean_name)[0]
        content_type = guessed if guessed else ""

    if not content_type or not content_type.startswith(("image", "video", "audio")):
        return None

    return content_type.split("/")[0]

async def get_stream_info(filebytes: bytes) -> list[dict]:
    with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as tmp:
        tmp.write(filebytes)
        tmp_path = tmp.name

    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "stream=codec_type,codec_name,disposition",
        "-of", "json",
        tmp_path,
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode == 0:
            data = json.loads(stdout.decode(errors="ignore"))
            return data.get("streams", [])
        else:
            print(f"ERROR: ffprobe failed: {stderr.decode(errors='replace')}")
    except (FileNotFoundError, OSError, ValueError, TypeError) as e:
        print(f"ERROR: Failed to probe media streams: {e}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return []

def supported_media_ext(attach: discord.Attachment, content_type: str, streams: list[dict]) -> str | None:
    ext_match = re.search(r"\.([a-zA-Z0-9]+)$", attach.filename or "")
    if not ext_match:
        return None

    ext = ext_match.group(1).lower()
    if ext not in SUPPORTED_MEDIA_EXTS.get(content_type, set()):
        return None

    for stream in streams:
        codec = stream.get("codec_name", "")
        match stream.get("codec_type"):
            case "video":
                if content_type == "audio" and stream.get("disposition", {}).get("attached_pic"):
                    continue
                if codec not in NATIVE_VIDEO_CODECS:
                    return None
            case "audio":
                if codec not in NATIVE_AUDIO_CODECS and not codec.startswith("pcm"):
                    return None

    return ext

async def process_attachment(attach: discord.Attachment, prebytes: bytes | None):
    attach_bytes = prebytes if prebytes else await attach.read()

    media_dir = os.getenv('MEDIA_PATH')

    content_type = get_content_type(attach)
    if not content_type:
        return None

    match content_type:
        case "image":
            file_hash = []
            file_path = f"{media_dir}/{attach.id}.webp"

            def save():
                with Image.open(io.BytesIO(attach_bytes)) as img:
                    file_hash = str(imagehash.average_hash(img))

                    if getattr(img, "is_animated", False):
                        img.save(
                            file_path,
                            "WEBP",
                            save_all=True,
                            quality=80,
                            method=4,
                            loop=img.info.get("loop", 0),
                            duration=img.info.get("duration", 100)
                        )
                    else:
                        img.save(file_path, "WEBP", quality=80)

                return file_hash

            file_hash = await asyncio.to_thread(save)
        case "video" | "audio":
            if len(attach_bytes) > UPLOAD_LIMIT:
                raise UnsupportedMedia

            streams = await get_stream_info(attach_bytes)
            if not streams:
                print("ERROR: Could not probe attachment, aborting")
                return None, None

            ext = supported_media_ext(attach, content_type, streams)
            if not ext:
                raise UnsupportedMedia

            file_path = f"{media_dir}/{attach.id}.{ext}"
            file_hash = hashlib.sha256(attach_bytes).hexdigest()

            def save():
                with open(file_path, "wb") as file:
                    file.write(attach_bytes)

            await asyncio.to_thread(save)

    return file_path, file_hash

async def url_to_file(url: str) -> discord.File | None:
    file = None

    try:
        async with aiohttp.ClientSession() as session, session.get(url, timeout=10) as res:
            if res.status == 200:
                filebytes = await res.read()

                parsed_path = urlparse(url).path
                filename = os.path.basename(parsed_path) or "media.mp4"

                return discord.File(io.BytesIO(filebytes), filename=filename)
    except (aiohttp.ClientError, asyncio.TimeoutError):
        pass

    return file

def get_media(egg):
    if egg.attach_path and os.path.exists(egg.attach_path):
        filename = os.path.basename(egg.attach_path)
        kind = get_content_type(filename)

        if kind in ("image", "video"):
            item = discord.MediaGalleryItem(media=f"attachment://{filename}")
            return item, discord.File(egg.attach_path, filename=filename), None, None

        return None, None, egg.attach_path, None
    elif getattr(egg, "attach_link", None) and egg.attach_link.startswith(("http://", "https://")):
        if get_content_type(egg.attach_link) in ("image", "video"):
            return discord.MediaGalleryItem(media=egg.attach_link), None, None, None

        return None, None, None, egg.attach_link

    return None, None, None, None

def file_path(file: discord.File | str | None) -> str | None:
    if isinstance(file, str):
        return file

    if file is None:
        return None

    name = getattr(file.fp, "name", None)
    return name if isinstance(name, str) else None

async def send_extra(ctx: discord.Interaction, file, link):
    if isinstance(file, discord.File):
        file = file_path(file)

    extra = discord.File(file) if file else None

    await ctx.response.send_message(link, file=extra or discord.utils.MISSING, ephemeral=True)

EMBEDDABLE_MEDIA_HOSTS = (
    "youtube.com", "youtu.be",
    "twitter.com", "x.com",
    "fxtwitter.com", "fixupx.com", "fxbsky.app",
    "vxtwitter.com", "fixvx.com",
    "girlcockx.com",
    "instagram.com", "kkinstagram.com",
    "tiktok.com",
    "twitch.tv",
    "bsky.app",
    "vimeo.com",
    "streamable.com",
    "soundcloud.com",
    "spotify.com",
    "bandcamp.com",
)

def is_native_embed(url: str) -> bool:
    try:
        netloc = urlparse(url).netloc.lower()
        return any(netloc == host or netloc.endswith(f".{host}") for host in EMBEDDABLE_MEDIA_HOSTS)
    except ValueError:
        return False

async def resolve_media_url(url: str) -> str | None:
    if not url.startswith(("http://", "https://")):
        return None

    if is_native_embed(url):
        return url

    if re.search(SUPPORTED_FILETYPE_REGEX, url, re.IGNORECASE):
        if "tenor.com" in url.lower():
            m = re.search(r"tenor\.com/(?:m/)?([a-zA-Z0-9_-]+)/", url)
            if m:
                return f"https://c.tenor.com/{m.group(1)}/tenor.gif"
        return url

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Discordbot/2.0; +https://discord.com)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=20) as response:
                if response.status != 200:
                    return None

                html_text = await response.text()

                candidates = {"video": None, "audio": None, "image": None, "gif": None}

                for tag in re.findall(r"<meta[^>]+>", html_text, re.IGNORECASE):
                    prop_match = re.search(r'(?:property|name|itemprop)=[\'"]([^\'"]+)[\'"]', tag, re.IGNORECASE)
                    cont_match = re.search(r'content=[\'"]([^\'"]+)[\'"]', tag, re.IGNORECASE)

                    if not prop_match or not cont_match:
                        continue

                    prop = prop_match.group(1).lower()
                    media_link = html.unescape(cont_match.group(1).strip())

                    if "tenor.com" in media_link.lower():
                        m = re.search(r"tenor\.com/(?:m/)?([a-zA-Z0-9_-]+)/", media_link)
                        if m:
                            media_link = f"https://c.tenor.com/{m.group(1)}/tenor.gif"

                    if not re.search(SUPPORTED_FILETYPE_REGEX, media_link, re.IGNORECASE):
                        continue

                    if prop in ("og:video", "og:video:url", "og:video:secure_url", "twitter:player:stream"):
                        if not candidates["video"]:
                            candidates["video"] = media_link

                    elif prop in ("og:audio", "og:audio:url", "og:audio:secure_url"):
                        if not candidates["audio"]:
                            candidates["audio"] = media_link

                    elif prop in ("og:image", "og:image:url", "og:image:secure_url", "twitter:image", "twitter:image:src"):
                        if not candidates["image"]:
                            candidates["image"] = media_link
                        if not candidates["gif"] and re.search(r"\.gif(?:[?#].*)?$", media_link, re.IGNORECASE):
                            candidates["gif"] = media_link

                return candidates["gif"] or candidates["video"] or candidates["audio"] or candidates["image"]

        except (aiohttp.ClientError, asyncio.TimeoutError, UnicodeDecodeError) as e:
            print(f"ERROR: Failed resolving {url}: {e}")

    return None