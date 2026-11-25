"""Fachada retrocompatível para o motor de downloads em coffee_app.core."""

from __future__ import annotations

import yt_dlp

from coffee_app.core.constants import (
    AUDIO_FORMAT_LABEL,
    AUDIO_ORIGINAL_FORMAT_LABEL,
    AUDIO_ORIGINAL_QUALITY_MAP,
    AUDIO_QUALITY_MAP,
    SPEED_LIMIT_MAP,
    VIDEO_FORMAT_LABEL,
    VIDEO_QUALITY_MAP,
)
from coffee_app.core.download_manager import DownloadManager
from coffee_app.core.models import (
    DownloadCancelledError,
    DownloadTask,
    PlaylistEntry,
    PlaylistInspectResult,
)
from coffee_app.core.ydl_options import (
    _build_single_video_url,
    _make_archive_key,
    _resolve_entry_url,
    _sanitize_prefix,
    apply_cookie_options,
    build_ydl_options,
    cleanup_part_files,
)

__all__ = [
    "AUDIO_FORMAT_LABEL",
    "AUDIO_ORIGINAL_FORMAT_LABEL",
    "AUDIO_ORIGINAL_QUALITY_MAP",
    "AUDIO_QUALITY_MAP",
    "DownloadCancelledError",
    "DownloadManager",
    "DownloadTask",
    "PlaylistEntry",
    "PlaylistInspectResult",
    "SPEED_LIMIT_MAP",
    "VIDEO_FORMAT_LABEL",
    "VIDEO_QUALITY_MAP",
    "_build_single_video_url",
    "_make_archive_key",
    "_resolve_entry_url",
    "_sanitize_prefix",
    "apply_cookie_options",
    "build_ydl_options",
    "cleanup_part_files",
    "yt_dlp",
]
