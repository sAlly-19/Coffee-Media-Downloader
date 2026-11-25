"""Construção de opções do yt-dlp e helpers de arquivos/URLs de mídia."""

from __future__ import annotations

import glob
import os
import urllib.parse
from typing import Any, Callable

from coffee_app.core.constants import AUDIO_QUALITY_MAP, VIDEO_QUALITY_MAP
from coffee_app.core.models import DownloadTask
from coffee_app.core.storage import get_staging_temp_dir
from coffee_app.core.system_utils import find_ffmpeg, sanitize_filename


def _build_single_video_url(url: str) -> str | None:
    """Extrai URL de vídeo individual quando o link possui vídeo + parâmetro de playlist."""
    try:
        parsed = urllib.parse.urlparse(url)
        query = urllib.parse.parse_qs(parsed.query)
    except ValueError:
        return None

    if "v" in query and query["v"]:
        clean_params = {k: v for k, v in query.items() if k not in ("list", "index", "start_radio")}
        new_query = urllib.parse.urlencode(clean_params, doseq=True)
        return urllib.parse.urlunparse(parsed._replace(query=new_query))
    return None


def _resolve_entry_url(entry: dict[str, Any], extractor_key: str = "") -> str | None:
    """Constrói uma URL reproduzível a partir de uma entrada de extract_flat."""
    raw_url = entry.get("webpage_url") or entry.get("url")
    if not raw_url:
        entry_id = entry.get("id")
        if entry_id and "youtube" in extractor_key.lower():
            return f"https://www.youtube.com/watch?v={entry_id}"
        return None

    if str(raw_url).startswith(("http://", "https://")):
        return str(raw_url)

    entry_id = entry.get("id") or raw_url
    if "youtube" in extractor_key.lower() or len(str(entry_id)) == 11:
        return f"https://www.youtube.com/watch?v={entry_id}"
    return str(raw_url)


def _make_archive_key(info: dict[str, Any] | None) -> str:
    if not isinstance(info, dict):
        return ""
    ie_key = str(info.get("extractor_key") or info.get("ie_key") or "").strip().lower()
    vid_id = str(info.get("id") or "").strip()
    if ie_key and vid_id:
        return f"{ie_key} {vid_id}"
    return vid_id


def _sanitize_prefix(prefix: str) -> str:
    if not prefix:
        return ""
    cleaned = sanitize_filename(prefix, max_length=24)
    return f"{cleaned} " if prefix.endswith(" ") else cleaned


def apply_cookie_options(
    opts: dict[str, Any],
    cookies_file: str = "",
    cookies_browser: str = "",
) -> None:
    """Aplica cookiefile (prioritário) ou cookiesfrombrowser às opções do yt-dlp."""
    clean_file = (cookies_file or "").strip()
    if clean_file and os.path.isfile(clean_file):
        opts["cookiefile"] = clean_file
        return
    browser = (cookies_browser or "").strip().lower()
    if browser in ("chrome", "edge", "firefox"):
        opts["cookiesfrombrowser"] = (browser,)


def build_ydl_options(
    task: DownloadTask,
    ratelimit_bps: int | None = None,
    ffmpeg_path: str | None = None,
    progress_hook: Callable[[dict[str, Any]], None] | None = None,
    postprocessor_hook: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Monta o dicionário de opções do yt-dlp conforme formato, qualidade, staging e banda."""
    os.makedirs(task.output_dir, exist_ok=True)
    safe_prefix = _sanitize_prefix(task.filename_prefix)
    outtmpl = f"{safe_prefix}%(title).150B.%(ext)s"

    opts: dict[str, Any] = {
        "outtmpl": outtmpl,
        "paths": {
            "home": task.output_dir,
            "temp": get_staging_temp_dir(),
        },
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "no_color": True,
        "noplaylist": True,
        "windowsfilenames": True,
        "concurrent_fragment_downloads": 4,
        "retries": 3,
        "fragment_retries": 3,
        "progress_hooks": [progress_hook] if progress_hook else [],
        "postprocessor_hooks": [postprocessor_hook] if postprocessor_hook else [],
    }

    if ratelimit_bps is not None and ratelimit_bps > 0:
        opts["ratelimit"] = ratelimit_bps

    resolved_ffmpeg = ffmpeg_path or find_ffmpeg()
    if resolved_ffmpeg:
        opts["ffmpeg_location"] = resolved_ffmpeg

    if task.skip_existing:
        opts["nooverwrites"] = True

    apply_cookie_options(opts, cookies_file=task.cookies_file, cookies_browser=task.cookies_browser)

    if task.is_mp3:
        bitrate = AUDIO_QUALITY_MAP.get(task.quality_label, "192")
        postprocessors: list[dict[str, Any]] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": bitrate,
            }
        ]
        if task.embed_metadata and resolved_ffmpeg:
            postprocessors.append({"key": "FFmpegMetadata"})
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = postprocessors
        opts["postprocessor_args"] = {"extractaudio": ["-compression_level", "7"]}
    elif task.is_m4a:
        postprocessors_m4a: list[dict[str, Any]] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "m4a",
                "preferredquality": "0",
            }
        ]
        if task.embed_metadata and resolved_ffmpeg:
            postprocessors_m4a.append({"key": "FFmpegMetadata"})
        opts["format"] = "bestaudio[ext=m4a]/bestaudio/best"
        opts["postprocessors"] = postprocessors_m4a
    else:
        resolution = VIDEO_QUALITY_MAP.get(task.quality_label)
        if resolution is None:
            opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        else:
            opts["format"] = (
                f"bestvideo[height<={resolution}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
            )
        opts["merge_output_format"] = "mp4"

    return opts


def cleanup_part_files(base_filepath: str | None) -> None:
    """Remove arquivos temporários .part e .ytdl no destino e na pasta de staging."""
    if not base_filepath:
        return
    stem, _ = os.path.splitext(base_filepath)
    base_name = os.path.basename(base_filepath)
    stem_name = os.path.basename(stem)
    staging = get_staging_temp_dir()

    patterns = (
        f"{base_filepath}.part",
        f"{base_filepath}.ytdl",
        f"{stem}*.part",
        f"{stem}*.ytdl",
        f"{stem}.temp.*",
        os.path.join(staging, f"{base_name}.part"),
        os.path.join(staging, f"{stem_name}*.part"),
        os.path.join(staging, f"{stem_name}*.ytdl"),
    )
    for pattern in patterns:
        for candidate in glob.glob(pattern):
            try:
                if os.path.isfile(candidate):
                    os.remove(candidate)
            except OSError:
                pass
