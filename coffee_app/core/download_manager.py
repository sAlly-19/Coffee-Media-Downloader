"""Gerenciador concorrente de downloads baseado em yt-dlp, ThreadPoolExecutor e FFmpeg."""

from __future__ import annotations

import os
import re
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable

import yt_dlp

from coffee_app.core.constants import SPEED_LIMIT_MAP
from coffee_app.core.models import (
    DownloadCancelledError,
    DownloadTask,
    PlaylistEntry,
    PlaylistInspectResult,
)
from coffee_app.core.storage import (
    append_archive_id,
    get_archive_file_path,
    is_in_archive,
)
from coffee_app.core.system_utils import find_ffmpeg, sanitize_filename
from coffee_app.core.ydl_options import (
    _build_single_video_url,
    _make_archive_key,
    _resolve_entry_url,
    _sanitize_prefix,
    apply_cookie_options,
    build_ydl_options,
    cleanup_part_files,
)


_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


class DownloadManager:
    """Gerencia fila de downloads paralelos, controle de banda, FFmpeg e inspeção de playlists."""

    MAX_WORKERS_CAP = 10

    def __init__(
        self,
        max_concurrent: int = 3,
        speed_limit_label: str = "Ilimitado",
        on_task_update: Callable[[DownloadTask], None] | None = None,
    ) -> None:
        self._lock = threading.RLock()
        self._max_concurrent = max(1, min(self.MAX_WORKERS_CAP, int(max_concurrent)))
        self._speed_limit_bps = SPEED_LIMIT_MAP.get(speed_limit_label)
        self._on_task_update = on_task_update
        self._cookies_browser = "Nenhum"
        self._cookies_file = ""

        # Limita conversões FFmpeg simultâneas mesmo quando até 10 downloads de rede estão ativos
        ffmpeg_cap = max(1, min(4, os.cpu_count() or 2))
        self._ffmpeg_semaphore = threading.Semaphore(ffmpeg_cap)

        self._executor = ThreadPoolExecutor(
            max_workers=self.MAX_WORKERS_CAP,
            thread_name_prefix="CoffeeDL",
        )
        self._pending: deque[DownloadTask] = deque()
        self._tasks: dict[str, DownloadTask] = {}
        self._active_ids: set[str] = set()
        self._shutting_down = False

    @property
    def max_concurrent(self) -> int:
        with self._lock:
            return self._max_concurrent

    @property
    def active_count(self) -> int:
        with self._lock:
            return len(self._active_ids)

    @property
    def total_speed_bps(self) -> float:
        with self._lock:
            return sum(
                self._tasks[tid].speed_bps or 0.0
                for tid in self._active_ids
                if tid in self._tasks and self._tasks[tid].status == "downloading"
            )

    def set_max_concurrent(self, limit: int) -> None:
        """Ajusta dinamicamente o número máximo de downloads simultâneos (1..10)."""
        with self._lock:
            self._max_concurrent = max(1, min(self.MAX_WORKERS_CAP, int(limit)))
            self._dispatch_locked()

    def set_speed_limit(self, speed_limit_label: str) -> None:
        """Define o limite de banda por tarefa para os próximos downloads."""
        with self._lock:
            self._speed_limit_bps = SPEED_LIMIT_MAP.get(speed_limit_label)

    def set_cookies_browser(self, browser_name: str) -> None:
        """Define o navegador de origem dos cookies para vídeos restritos."""
        with self._lock:
            self._cookies_browser = browser_name

    def set_cookies_file(self, filepath: str) -> None:
        """Define o caminho opcional de um arquivo cookies.txt (Netscape)."""
        with self._lock:
            self._cookies_file = (filepath or "").strip()

    def enqueue(self, task: DownloadTask) -> None:
        """Adiciona uma tarefa à fila e inicia imediatamente se houver vaga."""
        with self._lock:
            if self._shutting_down:
                return
            self._tasks[task.task_id] = task
            self._pending.append(task)
            self._emit_update(task)
            self._dispatch_locked()

    def cancel_task(self, task_id: str) -> None:
        """Solicita cancelamento imediato de uma tarefa aguardando ou em execução."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            task.cancel_event.set()
            if task in self._pending:
                self._pending.remove(task)
                task.status = "cancelled"
                task.speed_bps = None
                task.eta_seconds = None
                self._emit_update(task)

    def cancel_all(self) -> None:
        """Cancela todas as tarefas pendentes e ativas na fila."""
        with self._lock:
            pending_copy = list(self._pending)
            self._pending.clear()
            for task in pending_copy:
                task.cancel_event.set()
                task.status = "cancelled"
                task.speed_bps = None
                task.eta_seconds = None
                self._emit_update(task)
            for tid in list(self._active_ids):
                active_task = self._tasks.get(tid)
                if active_task:
                    active_task.cancel_event.set()

    def remove_task(self, task_id: str) -> None:
        """Remove uma tarefa finalizada ou cancelada do registro interno."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task and task_id not in self._active_ids:
                if task in self._pending:
                    self._pending.remove(task)
                self._tasks.pop(task_id, None)

    def inspect_url_async(
        self,
        url: str,
        callback: Callable[[PlaylistInspectResult], None],
    ) -> None:
        """Verifica em thread separada se a URL corresponde a uma playlist com múltiplos vídeos."""

        def _worker() -> None:
            result = self.inspect_url(url)
            callback(result)

        threading.Thread(target=_worker, daemon=True, name="CoffeeInspect").start()

    def inspect_url(self, url: str) -> PlaylistInspectResult:
        """Executa extração rápida (extract_flat) para detectar playlists."""
        ydl_opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "no_color": True,
            "extract_flat": "in_playlist",
            "skip_download": True,
            "ignoreerrors": True,
        }
        with self._lock:
            cookies_file = self._cookies_file
            cookies_browser = self._cookies_browser
        apply_cookie_options(ydl_opts, cookies_file=cookies_file, cookies_browser=cookies_browser)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as exc:
            return PlaylistInspectResult(
                source_url=url,
                is_playlist=False,
                error=self._format_error(exc),
            )

        if not info or not isinstance(info, dict):
            return PlaylistInspectResult(source_url=url, is_playlist=False)

        raw_entries = info.get("entries")
        if raw_entries is None:
            return PlaylistInspectResult(source_url=url, is_playlist=False)

        extractor_key = str(info.get("extractor_key") or info.get("extractor") or "")
        entries: list[PlaylistEntry] = []
        for item in raw_entries:
            if not isinstance(item, dict):
                continue
            item_url = _resolve_entry_url(item, extractor_key=extractor_key)
            if not item_url:
                continue
            thumb = item.get("thumbnail")
            if not thumb and isinstance(item.get("thumbnails"), list) and item["thumbnails"]:
                thumb = item["thumbnails"][-1].get("url")
            entries.append(
                PlaylistEntry(
                    url=item_url,
                    title=str(item.get("title") or item_url),
                    duration=item.get("duration"),
                    thumbnail_url=thumb,
                )
            )

        if len(entries) <= 1:
            return PlaylistInspectResult(
                source_url=url,
                is_playlist=False,
                entries=entries,
            )

        return PlaylistInspectResult(
            source_url=url,
            is_playlist=True,
            playlist_title=str(info.get("title") or "Playlist"),
            entries=entries,
            single_video_url=_build_single_video_url(url),
        )

    def _dispatch_locked(self) -> None:
        if self._shutting_down:
            return
        while self._pending and len(self._active_ids) < self._max_concurrent:
            task = self._pending.popleft()
            if task.cancel_event.is_set():
                task.status = "cancelled"
                self._emit_update(task)
                continue
            self._active_ids.add(task.task_id)
            self._executor.submit(self._run_task, task)

    def _run_task(self, task: DownloadTask) -> None:
        prepared_path: str | None = None
        last_pp_filepath: str | None = None
        acquired_ffmpeg = False
        archive_key = ""
        archive_path = Path(task.archive_file) if task.archive_file else get_archive_file_path()

        def release_ffmpeg_if_held() -> None:
            nonlocal acquired_ffmpeg
            if acquired_ffmpeg:
                acquired_ffmpeg = False
                self._ffmpeg_semaphore.release()

        def progress_hook(data: dict[str, Any]) -> None:
            if task.cancel_event.is_set():
                raise DownloadCancelledError("Download cancelado pelo usuário.")

            status = data.get("status")
            if status == "downloading":
                downloaded = data.get("downloaded_bytes") or 0
                total = data.get("total_bytes") or data.get("total_bytes_estimate")
                if total and total > 0:
                    task.progress = max(0.0, min(1.0, downloaded / total))
                    task.filesize_bytes = int(total)
                task.speed_bps = data.get("speed")
                task.eta_seconds = data.get("eta")
                task.status = "downloading"
                self._emit_update(task)
            elif status == "finished":
                task.progress = 1.0
                task.speed_bps = None
                task.eta_seconds = 0
                if data.get("filename"):
                    nonlocal prepared_path
                    prepared_path = str(data["filename"])
                task.status = "converting" if task.is_audio else "downloading"
                self._emit_update(task)

        def postprocessor_hook(data: dict[str, Any]) -> None:
            nonlocal last_pp_filepath, acquired_ffmpeg
            if task.cancel_event.is_set():
                release_ffmpeg_if_held()
                raise DownloadCancelledError("Download cancelado pelo usuário.")

            info_dict = data.get("info_dict") or {}
            if info_dict.get("filepath"):
                last_pp_filepath = str(info_dict["filepath"])

            pp_status = data.get("status")
            if pp_status == "started":
                if not acquired_ffmpeg:
                    self._ffmpeg_semaphore.acquire()
                    acquired_ffmpeg = True
                if task.cancel_event.is_set():
                    release_ffmpeg_if_held()
                    raise DownloadCancelledError("Download cancelado pelo usuário.")
                task.status = "converting"
                task.speed_bps = None
                self._emit_update(task)
            elif pp_status == "finished":
                release_ffmpeg_if_held()

        try:
            if task.cancel_event.is_set():
                raise DownloadCancelledError("Download cancelado pelo usuário.")

            task.status = "extracting"
            self._emit_update(task)

            with self._lock:
                ratelimit_bps = self._speed_limit_bps
                if not task.cookies_browser or task.cookies_browser == "Nenhum":
                    task.cookies_browser = self._cookies_browser
                if not task.cookies_file:
                    task.cookies_file = self._cookies_file

            ffmpeg_path = find_ffmpeg()
            if task.is_audio and not ffmpeg_path:
                raise RuntimeError(
                    "FFmpeg não encontrado. Coloque o ffmpeg.exe na pasta do app para extrair áudio."
                )

            opts = build_ydl_options(
                task=task,
                ratelimit_bps=ratelimit_bps,
                ffmpeg_path=ffmpeg_path,
                progress_hook=progress_hook,
                postprocessor_hook=postprocessor_hook,
            )

            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(task.url, download=False)
                if task.cancel_event.is_set():
                    raise DownloadCancelledError("Download cancelado pelo usuário.")

                if isinstance(info, dict):
                    if "entries" in info and info["entries"]:
                        first = next((e for e in info["entries"] if e), None)
                        if isinstance(first, dict):
                            info = first

                    raw_title = info.get("title")
                    if raw_title:
                        task.title = str(raw_title)
                    task.duration_seconds = info.get("duration")
                    task.thumbnail_url = info.get("thumbnail")
                    est_size = info.get("filesize") or info.get("filesize_approx")
                    if est_size:
                        task.filesize_bytes = int(est_size)
                    archive_key = _make_archive_key(info)
                    try:
                        prepared_path = ydl.prepare_filename(info)
                    except Exception:
                        prepared_path = None

                if task.skip_existing:
                    existing_target = self._find_existing_output(task, prepared_path)
                    already_archived = is_in_archive(archive_key, archive_path=archive_path)

                    if existing_target or already_archived:
                        if existing_target and os.path.isfile(existing_target):
                            task.filepath = existing_target
                            task.filesize_bytes = os.path.getsize(existing_target)
                        else:
                            task.filepath = task.output_dir
                        task.progress = 1.0
                        task.speed_bps = None
                        task.eta_seconds = None
                        task.status = "skipped"
                        self._emit_update(task)
                        return

                task.status = "downloading"
                self._emit_update(task)

                ydl.process_ie_result(info, download=True)

            if task.cancel_event.is_set():
                raise DownloadCancelledError("Download cancelado pelo usuário.")

            final_path = self._resolve_final_filepath(
                task=task,
                last_pp_filepath=last_pp_filepath,
                prepared_path=prepared_path,
            )
            task.filepath = final_path
            if final_path and os.path.isfile(final_path):
                task.filesize_bytes = os.path.getsize(final_path)

            if archive_key:
                append_archive_id(archive_key, archive_path=archive_path)

            task.progress = 1.0
            task.speed_bps = None
            task.eta_seconds = None
            task.status = "completed"
            self._emit_update(task)

        except DownloadCancelledError:
            cleanup_part_files(prepared_path)
            task.status = "cancelled"
            task.speed_bps = None
            task.eta_seconds = None
            self._emit_update(task)
        except yt_dlp.utils.DownloadError as exc:
            if task.cancel_event.is_set():
                cleanup_part_files(prepared_path)
                task.status = "cancelled"
            else:
                task.status = "error"
                task.error_message = self._format_error(exc)
            task.speed_bps = None
            task.eta_seconds = None
            self._emit_update(task)
        except Exception as exc:
            if task.cancel_event.is_set():
                cleanup_part_files(prepared_path)
                task.status = "cancelled"
            else:
                task.status = "error"
                task.error_message = self._format_error(exc)
            task.speed_bps = None
            task.eta_seconds = None
            self._emit_update(task)
        finally:
            release_ffmpeg_if_held()
            with self._lock:
                self._active_ids.discard(task.task_id)
                self._dispatch_locked()

    def _find_existing_output(
        self,
        task: DownloadTask,
        prepared_path: str | None,
    ) -> str | None:
        ext = task.target_extension
        if prepared_path:
            stem, _ = os.path.splitext(prepared_path)
            candidate = f"{stem}{ext}"
            if os.path.isfile(candidate):
                return candidate
        safe_prefix = _sanitize_prefix(task.filename_prefix)
        safe_title = sanitize_filename(task.title)
        fallback = os.path.join(task.output_dir, f"{safe_prefix}{safe_title}{ext}")
        return fallback if os.path.isfile(fallback) else None

    def _resolve_final_filepath(
        self,
        task: DownloadTask,
        last_pp_filepath: str | None,
        prepared_path: str | None,
    ) -> str | None:
        if last_pp_filepath and os.path.isfile(last_pp_filepath):
            return last_pp_filepath
        ext = task.target_extension
        if prepared_path:
            stem, _ = os.path.splitext(prepared_path)
            expected = f"{stem}{ext}"
            if os.path.isfile(expected):
                return expected
            if os.path.isfile(prepared_path):
                return prepared_path
        safe_prefix = _sanitize_prefix(task.filename_prefix)
        safe_title = sanitize_filename(task.title)
        fallback = os.path.join(task.output_dir, f"{safe_prefix}{safe_title}{ext}")
        return fallback if os.path.isfile(fallback) else task.output_dir

    @staticmethod
    def _format_error(exc: Exception) -> str:
        msg = _ANSI_ESCAPE_RE.sub("", str(exc)).strip()
        if "ERROR:" in msg:
            msg = msg.split("ERROR:", 1)[-1].strip()
        msg = _ANSI_ESCAPE_RE.sub("", msg).strip()

        lower = msg.lower()
        if any(
            token in lower
            for token in (
                "sign in to confirm your age",
                "age-restricted",
                "inappropriate for some users",
                "confirm your age",
            )
        ):
            return "Vídeo +18 no YouTube. Ative Firefox ou selecione um cookies.txt em Configurações."
        if any(
            token in lower
            for token in (
                "could not copy chrome cookie",
                "cookie database",
                "failed to decrypt",
                "dpapi",
            )
        ):
            return "Navegador bloqueou leitura dos cookies. Use Firefox ou importe um cookies.txt em Configurações."

        if len(msg) > 140:
            msg = msg[:137] + "..."
        return msg or "Falha desconhecida durante o download."

    def _emit_update(self, task: DownloadTask) -> None:
        if self._on_task_update:
            self._on_task_update(task.snapshot())

    def shutdown(self) -> None:
        """Cancela tarefas pendentes/ativas e encerra o ThreadPoolExecutor."""
        with self._lock:
            self._shutting_down = True
            for task in self._tasks.values():
                task.cancel_event.set()
            self._pending.clear()
        self._executor.shutdown(wait=False, cancel_futures=True)
