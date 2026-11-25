"""Persistência local em %APPDATA% (configurações, histórico, fila e archive thread-safe)."""

from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

from coffee_app.core.constants import APP_NAME
from coffee_app.core.system_utils import get_default_downloads_dir

_ARCHIVE_LOCK = threading.RLock()


def get_app_data_dir() -> Path:
    """Retorna e garante o diretório de dados persistentes em %APPDATA%."""
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home()
    target = base / APP_NAME
    target.mkdir(parents=True, exist_ok=True)
    return target


def get_default_settings() -> dict[str, Any]:
    """Configurações padrão da aplicação."""
    return {
        "output_dir": get_default_downloads_dir(),
        "max_concurrent": 3,
        "speed_limit": "Ilimitado",
        "auto_paste": False,
        "default_format": "Vídeo (MP4)",
        "default_video_quality": "1080p",
        "default_audio_quality": "320 kbps (Alta)",
        "embed_metadata": True,
        "skip_existing": True,
        "high_concurrency_warned": False,
        "cookies_browser": "Nenhum",
        "cookies_file": "",
        "minimize_to_tray": False,
        "playlist_subfolder": False,
        "playlist_numbering": False,
        "post_queue_action": "Notificar",
    }


def get_archive_file_path(data_dir: Path | None = None) -> Path:
    """Retorna o caminho do arquivo de registro de mídias já baixadas."""
    return (data_dir or get_app_data_dir()) / "downloaded_archive.txt"


def get_staging_temp_dir() -> str:
    """Pasta temporária no disco local (SSD) para download/conversão antes de mover ao destino."""
    staging = Path(tempfile.gettempdir()) / f"{APP_NAME}_staging"
    staging.mkdir(parents=True, exist_ok=True)
    return str(staging)


def load_archive_ids(archive_path: Path | None = None) -> set[str]:
    """Lê de forma thread-safe todos os IDs registrados no arquivo de archive."""
    target = archive_path or get_archive_file_path()
    with _ARCHIVE_LOCK:
        if not target.is_file():
            return set()
        try:
            with target.open("r", encoding="utf-8", errors="ignore") as fh:
                return {line.strip() for line in fh if line.strip()}
        except OSError:
            return set()


def is_in_archive(archive_key: str, archive_path: Path | None = None) -> bool:
    """Verifica de forma thread-safe se uma mídia já consta no registro local."""
    if not archive_key:
        return False
    return archive_key in load_archive_ids(archive_path)


def append_archive_id(archive_key: str, archive_path: Path | None = None) -> None:
    """Registra um ID concluído no arquivo de archive com exclusão mútua entre threads."""
    if not archive_key:
        return
    target = archive_path or get_archive_file_path()
    with _ARCHIVE_LOCK:
        existing = load_archive_ids(target)
        if archive_key in existing:
            return
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8") as fh:
                fh.write(f"{archive_key}\n")
        except OSError:
            pass


def clear_download_archive(data_dir: Path | None = None) -> None:
    """Limpa o registro local de mídias já baixadas."""
    archive = get_archive_file_path(data_dir=data_dir)
    with _ARCHIVE_LOCK:
        try:
            if archive.is_file():
                archive.unlink()
        except OSError:
            pass


def _read_json(path: Path, fallback: Any) -> Any:
    if not path.is_file():
        return fallback
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return fallback


def _write_json(path: Path, data: Any) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        tmp_path.replace(path)
    except OSError:
        pass


def load_queue_state(data_dir: Path | None = None) -> list[dict[str, Any]]:
    """Carrega tarefas pendentes salvas na sessão anterior."""
    base = data_dir or get_app_data_dir()
    items = _read_json(base / "queue_state.json", [])
    return items if isinstance(items, list) else []


def save_queue_state(items: list[dict[str, Any]], data_dir: Path | None = None) -> None:
    """Persiste tarefas pendentes para retomada futura."""
    base = data_dir or get_app_data_dir()
    path = base / "queue_state.json"
    if not items:
        try:
            if path.is_file():
                path.unlink()
        except OSError:
            pass
        return
    _write_json(path, items)


def load_settings(data_dir: Path | None = None) -> dict[str, Any]:
    """Carrega configurações persistidas mesclando com os padrões."""
    base = data_dir or get_app_data_dir()
    defaults = get_default_settings()
    saved = _read_json(base / "settings.json", {})
    if isinstance(saved, dict):
        defaults.update(saved)
    if not defaults.get("output_dir") or not os.path.isdir(defaults["output_dir"]):
        defaults["output_dir"] = get_default_downloads_dir()
    return defaults


def save_settings(settings: dict[str, Any], data_dir: Path | None = None) -> None:
    """Salva configurações no disco."""
    base = data_dir or get_app_data_dir()
    _write_json(base / "settings.json", settings)


def load_history(data_dir: Path | None = None) -> list[dict[str, Any]]:
    """Carrega histórico de downloads persistido."""
    base = data_dir or get_app_data_dir()
    items = _read_json(base / "history.json", [])
    return items if isinstance(items, list) else []


def save_history(items: list[dict[str, Any]], data_dir: Path | None = None) -> None:
    """Salva lista de histórico no disco."""
    base = data_dir or get_app_data_dir()
    _write_json(base / "history.json", items)


def append_history_entry(
    entry: dict[str, Any],
    limit: int = 200,
    data_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Adiciona um registro no topo do histórico respeitando o limite máximo."""
    history = load_history(data_dir=data_dir)
    history.insert(0, entry)
    trimmed = history[:limit]
    save_history(trimmed, data_dir=data_dir)
    return trimmed
