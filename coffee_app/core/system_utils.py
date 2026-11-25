"""Funções utilitárias de sistema, URLs, nomes de arquivo e formatação."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import urllib.parse
from pathlib import Path

from coffee_app.core.constants import (
    _INVALID_WIN_CHARS_RE,
    _KNOWN_MEDIA_HOSTS,
    _RESERVED_WIN_NAMES,
)


def get_resource_base_dirs() -> list[Path]:
    """Retorna os diretórios onde recursos portáteis (como ffmpeg.exe) podem estar."""
    dirs: list[Path] = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        dirs.append(Path(meipass))
    if getattr(sys, "frozen", False):
        dirs.append(Path(sys.executable).resolve().parent)
    dirs.append(Path(__file__).resolve().parents[2])
    return dirs


def find_ffmpeg() -> str | None:
    """Localiza o ffmpeg.exe no pacote PyInstaller, na pasta local ou no PATH do sistema."""
    exe_names = ("ffmpeg.exe", "ffmpeg") if os.name == "nt" else ("ffmpeg",)
    for base_dir in get_resource_base_dirs():
        for rel in ("", "bin", "ffmpeg", os.path.join("ffmpeg", "bin")):
            candidate_dir = base_dir / rel if rel else base_dir
            for exe_name in exe_names:
                candidate = candidate_dir / exe_name
                if candidate.is_file():
                    return str(candidate)

    system_ffmpeg = shutil.which("ffmpeg")
    return system_ffmpeg if system_ffmpeg else None


def is_valid_media_url(text: str) -> bool:
    """Valida se o texto é uma URL HTTP/HTTPS plausível para extração de mídia."""
    if not text or not isinstance(text, str):
        return False
    cleaned = text.strip()
    if len(cleaned) > 2048 or any(ch.isspace() for ch in cleaned):
        return False

    try:
        parsed = urllib.parse.urlparse(cleaned)
    except ValueError:
        return False

    if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
        return False

    host = (parsed.hostname or "").lower()
    if not host or ("." not in host and host != "localhost"):
        return False

    has_target = bool(parsed.path.strip("/") or parsed.query)
    if not has_target:
        return False

    if any(host == known or host.endswith(f".{known}") for known in _KNOWN_MEDIA_HOSTS):
        return True

    # Para outros domínios suportados pelo yt-dlp, exige caminho com pelo menos 2 caracteres.
    return len(parsed.path.strip("/")) >= 2 or bool(parsed.query)


def extract_media_urls(raw_text: str) -> list[str]:
    """Extrai múltiplas URLs válidas de texto multilinha ou separado por espaços."""
    if not raw_text:
        return []
    seen: set[str] = set()
    urls: list[str] = []
    for token in re.split(r"[\s,;]+", raw_text.strip()):
        cleaned = token.strip()
        if cleaned and cleaned not in seen and is_valid_media_url(cleaned):
            seen.add(cleaned)
            urls.append(cleaned)
    return urls


def sanitize_filename(name: str, max_length: int = 180) -> str:
    """Remove caracteres inválidos no Windows e evita nomes reservados pelo sistema."""
    cleaned = _INVALID_WIN_CHARS_RE.sub("_", (name or "").strip())
    cleaned = cleaned.rstrip(". ")
    if not cleaned:
        cleaned = "download"

    stem = cleaned.split(".")[0].upper()
    if stem in _RESERVED_WIN_NAMES:
        cleaned = f"_{cleaned}"

    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip(". ")
    return cleaned or "download"


def get_default_downloads_dir() -> str:
    """Obtém a pasta Downloads padrão do usuário no Windows."""
    candidates = [Path.home() / "Downloads", Path.home()]
    for folder in candidates:
        if folder.exists() and folder.is_dir():
            return str(folder)
    return str(Path.cwd())


def open_folder(path: str) -> bool:
    """Abre a pasta no Windows Explorer (selecionando o arquivo se existir)."""
    if not path:
        return False
    norm_path = os.path.normpath(path)
    try:
        if os.path.isfile(norm_path):
            if os.name == "nt":
                subprocess.Popen(["explorer", "/select,", norm_path])
            else:
                subprocess.Popen(["xdg-open", os.path.dirname(norm_path)])
            return True

        target_dir = norm_path if os.path.isdir(norm_path) else os.path.dirname(norm_path)
        if target_dir and os.path.isdir(target_dir):
            if os.name == "nt":
                os.startfile(target_dir)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", target_dir])
            return True
    except OSError:
        return False
    return False


def open_file(path: str) -> bool:
    """Abre o arquivo baixado no player padrão do sistema operacional."""
    if not path:
        return False
    norm_path = os.path.normpath(path)
    if not os.path.isfile(norm_path):
        return False
    try:
        if os.name == "nt":
            os.startfile(norm_path)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", norm_path])
        return True
    except OSError:
        return False


def format_bytes(num_bytes: int | float | None) -> str:
    """Formata bytes em KB, MB ou GB legíveis."""
    if num_bytes is None or num_bytes <= 0:
        return "—"
    value = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024.0 or unit == "TB":
            if unit in ("B", "KB"):
                return f"{value:.0f} {unit}"
            return f"{value:.2f} {unit}".replace(".", ",") if unit == "GB" else f"{value:.1f} {unit}".replace(".", ",")
        value /= 1024.0
    return "—"


def format_speed(bps: float | None) -> str:
    """Formata velocidade de transferência em KB/s ou MB/s."""
    if bps is None or bps <= 0:
        return "0 KB/s"
    if bps < 1024 * 1024:
        return f"{bps / 1024:.0f} KB/s"
    return f"{bps / (1024 * 1024):.1f} MB/s"


def format_eta(seconds: int | float | None) -> str:
    """Formata tempo restante em MM:SS ou HH:MM:SS."""
    if seconds is None or seconds < 0:
        return "--:--"
    total = int(seconds)
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_duration(seconds: int | float | None) -> str:
    """Formata duração de vídeo/áudio (ex: 10:24 ou 1:05:30)."""
    if seconds is None or seconds <= 0:
        return ""
    total = int(seconds)
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"
