"""Constantes globais e mapas de configuração do CoffeeMediaDownloader Pro."""

from __future__ import annotations

import re

APP_NAME = "CoffeeMediaDownloader"
APP_DISPLAY_NAME = "CoffeeMediaDownloader Pro"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Café - Sistemas & Softwares"

_INVALID_WIN_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED_WIN_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)

_KNOWN_MEDIA_HOSTS = (
    "youtube.com",
    "youtu.be",
    "music.youtube.com",
    "vimeo.com",
    "tiktok.com",
    "instagram.com",
    "twitch.tv",
    "clips.twitch.tv",
    "twitter.com",
    "x.com",
    "soundcloud.com",
    "dailymotion.com",
    "dai.ly",
    "facebook.com",
    "fb.watch",
    "reddit.com",
    "bilibili.com",
    "rumble.com",
    "odysee.com",
)

VIDEO_FORMAT_LABEL = "Vídeo (MP4)"
AUDIO_FORMAT_LABEL = "Áudio (MP3)"
AUDIO_ORIGINAL_FORMAT_LABEL = "Áudio Original (M4A)"

VIDEO_QUALITY_MAP: dict[str, int | None] = {
    "Melhor Disponível": None,
    "4K (2160p)": 2160,
    "1080p": 1080,
    "720p": 720,
    "480p": 480,
}

AUDIO_QUALITY_MAP: dict[str, str] = {
    "320 kbps (Alta)": "320",
    "192 kbps (Média)": "192",
    "128 kbps (Padrão)": "128",
}

AUDIO_ORIGINAL_QUALITY_MAP: dict[str, str] = {
    "Melhor Disponível": "best",
}

SPEED_LIMIT_MAP: dict[str, int | None] = {
    "Ilimitado": None,
    "10 MB/s": 10 * 1024 * 1024,
    "5 MB/s": 5 * 1024 * 1024,
    "2 MB/s": 2 * 1024 * 1024,
    "1 MB/s": 1 * 1024 * 1024,
    "500 KB/s": 500 * 1024,
}
