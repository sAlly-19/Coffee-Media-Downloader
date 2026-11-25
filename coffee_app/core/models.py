"""Modelos de dados e exceções do motor de downloads."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field, replace

from coffee_app.core.constants import AUDIO_FORMAT_LABEL, AUDIO_ORIGINAL_FORMAT_LABEL


class DownloadCancelledError(Exception):
    """Exceção levantada dentro do progress_hook para abortar o download imediatamente."""


@dataclass
class PlaylistEntry:
    """Representa um item individual extraído de uma playlist."""

    url: str
    title: str
    duration: float | None = None
    thumbnail_url: str | None = None


@dataclass
class PlaylistInspectResult:
    """Resultado da inspeção rápida de URL para detecção de playlist."""

    source_url: str
    is_playlist: bool
    playlist_title: str = ""
    entries: list[PlaylistEntry] = field(default_factory=list)
    single_video_url: str | None = None
    error: str | None = None


@dataclass
class DownloadTask:
    """Estado isolado de uma tarefa de download na fila."""

    url: str
    fmt_label: str
    quality_label: str
    output_dir: str
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    title: str = ""
    status: str = "queued"  # queued, extracting, downloading, converting, completed, skipped, cancelled, error
    progress: float = 0.0
    speed_bps: float | None = None
    eta_seconds: float | None = None
    filesize_bytes: int | None = None
    duration_seconds: float | None = None
    thumbnail_url: str | None = None
    filepath: str | None = None
    error_message: str | None = None
    embed_metadata: bool = True
    skip_existing: bool = True
    archive_file: str | None = None
    cookies_browser: str = "Nenhum"
    cookies_file: str = ""
    filename_prefix: str = ""
    cancel_event: threading.Event = field(default_factory=threading.Event)

    def __post_init__(self) -> None:
        if not self.title:
            self.title = self.url

    @property
    def is_mp3(self) -> bool:
        return self.fmt_label == AUDIO_FORMAT_LABEL

    @property
    def is_m4a(self) -> bool:
        return self.fmt_label == AUDIO_ORIGINAL_FORMAT_LABEL

    @property
    def is_audio(self) -> bool:
        return self.is_mp3 or self.is_m4a

    @property
    def short_format(self) -> str:
        if self.is_mp3:
            return "MP3"
        if self.is_m4a:
            return "M4A"
        return "MP4"

    @property
    def target_extension(self) -> str:
        if self.is_mp3:
            return ".mp3"
        if self.is_m4a:
            return ".m4a"
        return ".mp4"

    def snapshot(self) -> DownloadTask:
        """Cria cópia rasa com os valores escalares atuais para envio seguro entre threads."""
        return replace(self)
