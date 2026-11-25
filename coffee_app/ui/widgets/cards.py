"""Cards de download na fila e de itens no histórico."""

from __future__ import annotations

import os
from typing import Any, Callable

from PIL import Image
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from coffee_app.core.media_assets import compose_thumbnail_with_duration
from coffee_app.core.models import DownloadTask
from coffee_app.core.system_utils import format_bytes, format_duration, format_eta, format_speed
from coffee_app.ui.icons import SvgIconStore, _pil_to_qpixmap
from coffee_app.ui.widgets.controls import ElidedLabel


class HistoryCardWidget(QFrame):
    """Card elegante de item do Histórico com badges em pílula, ações e menu contextual."""

    def __init__(
        self,
        index: int,
        entry: dict[str, Any],
        icons: SvgIconStore,
        on_open_folder: Callable[[str], None],
        on_open_file: Callable[[str], None],
        on_redownload: Callable[[dict[str, Any]], None],
        on_copy_url: Callable[[str], None],
        on_remove: Callable[[int], None],
    ) -> None:
        super().__init__()
        self.setObjectName("DownloadCard")
        self.setFixedHeight(74)
        self._index = index
        self._entry = entry
        self._icons = icons

        fmt = str(entry.get("format") or "MP4").upper()
        ok = entry.get("status") == "completed"
        filepath = str(entry.get("filepath") or entry.get("output_dir") or "")
        url = str(entry.get("url") or "")

        root = QHBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)

        # Tile com ícone do formato (áudio / vídeo / erro)
        tile = QLabel()
        tile.setFixedSize(44, 44)
        tile.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if not ok:
            tile.setStyleSheet(
                "background: rgba(92, 34, 26, 175); border: 1px solid #8A3A2D; border-radius: 10px;"
            )
            tile.setPixmap(icons.pixmap("cancel", 20, "#F87171"))
        elif fmt == "MP3":
            tile.setStyleSheet(
                "background: rgba(75, 42, 22, 185); border: 1px solid #8C512B; border-radius: 10px;"
            )
            tile.setPixmap(icons.pixmap("audio", 20, "#F3BC7D"))
        else:
            tile.setStyleSheet(
                "background: rgba(62, 37, 23, 185); border: 1px solid #754A31; border-radius: 10px;"
            )
            tile.setPixmap(icons.pixmap("video", 20, "#EBB87A"))
        root.addWidget(tile)

        # Coluna central com título elidido e pílulas
        mid = QVBoxLayout()
        mid.setContentsMargins(0, 0, 0, 0)
        mid.setSpacing(5)

        title_lbl = ElidedLabel(str(entry.get("title") or url))
        title_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #F6EFE9;")
        mid.addWidget(title_lbl)

        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)
        meta_row.setSpacing(6)

        fmt_pill = QLabel(fmt)
        fmt_pill.setObjectName("BadgeFormat")
        meta_row.addWidget(fmt_pill)

        quality_txt = str(entry.get("quality") or "").split(" (")[0].strip()
        if quality_txt:
            q_pill = QLabel(quality_txt)
            q_pill.setObjectName("BadgeMeta")
            meta_row.addWidget(q_pill)

        size_txt = format_bytes(entry.get("size_bytes"))
        if size_txt != "—":
            s_pill = QLabel(size_txt)
            s_pill.setObjectName("BadgeMeta")
            meta_row.addWidget(s_pill)

        ts_txt = str(entry.get("timestamp") or "").strip()
        if ts_txt:
            ts_pill = QLabel(ts_txt)
            ts_pill.setObjectName("BadgeMeta")
            meta_row.addWidget(ts_pill)

        status_pill = QLabel("Concluído" if ok else "Erro")
        if ok:
            status_pill.setStyleSheet(
                "background: rgba(34, 84, 61, 130); border: 1px solid rgba(110, 231, 183, 90); "
                "border-radius: 5px; color: #6EE7B7; font-size: 11px; font-weight: 600; padding: 1px 7px;"
            )
        else:
            status_pill.setStyleSheet(
                "background: rgba(96, 34, 28, 150); border: 1px solid rgba(248, 113, 113, 100); "
                "border-radius: 5px; color: #F87171; font-size: 11px; font-weight: 600; padding: 1px 7px;"
            )
            if entry.get("error"):
                status_pill.setToolTip(str(entry["error"]))
        meta_row.addWidget(status_pill)
        meta_row.addStretch()
        mid.addLayout(meta_row)

        root.addLayout(mid, 1)

        # Ações compactas à direita
        actions = QHBoxLayout()
        actions.setContentsMargins(4, 0, 0, 0)
        actions.setSpacing(5)

        if ok:
            btn_open = QPushButton(" Pasta")
            btn_open.setObjectName("CardActionBtn")
            btn_open.setProperty("accent", "true")
            btn_open.setIcon(icons.icon("folder", 13, "#FFF8F2"))
            btn_open.setToolTip("Abrir Pasta")
            btn_open.setFixedHeight(28)
            btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_open.clicked.connect(lambda: on_open_folder(filepath))
            actions.addWidget(btn_open)

        btn_again = QPushButton(" Baixar Novamente")
        btn_again.setObjectName("SecondaryBtn")
        btn_again.setIcon(icons.icon("refresh", 13, "#F6EFE9"))
        btn_again.setFixedHeight(28)
        btn_again.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_again.clicked.connect(lambda: on_redownload(entry))
        actions.addWidget(btn_again)

        dots_btn = QPushButton()
        dots_btn.setObjectName("MenuDotsBtn")
        dots_btn.setIcon(icons.icon("dots", 15, "#C4AE9E"))
        dots_btn.setFixedSize(26, 30)
        dots_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        def _open_menu() -> None:
            menu = QMenu(self)
            act_play = (
                menu.addAction("Abrir Arquivo")
                if ok and filepath and os.path.isfile(filepath)
                else None
            )
            act_folder = menu.addAction("Abrir Pasta") if ok else None
            act_copy = menu.addAction("Copiar Link") if url else None
            act_again = menu.addAction("Baixar Novamente")
            menu.addSeparator()
            act_del = menu.addAction("Remover do Histórico")

            chosen = menu.exec(dots_btn.mapToGlobal(QPoint(0, dots_btn.height())))
            if act_play and chosen == act_play:
                on_open_file(filepath)
            elif act_folder and chosen == act_folder:
                on_open_folder(filepath)
            elif act_copy and chosen == act_copy:
                on_copy_url(url)
            elif chosen == act_again:
                on_redownload(entry)
            elif chosen == act_del:
                on_remove(index)

        dots_btn.clicked.connect(_open_menu)
        actions.addWidget(dots_btn)
        root.addLayout(actions)


class DownloadCardWidget(QFrame):
    """Card compacto de fila com miniatura, badges, progresso gradiente e ações."""

    def __init__(
        self,
        task: DownloadTask,
        icons: SvgIconStore,
        base_thumb_pil: Image.Image,
        on_cancel: Callable[[str], None],
        on_remove: Callable[[str], None],
        on_open_folder: Callable[[DownloadTask], None],
        on_retry: Callable[[DownloadTask], None],
        on_copy_url: Callable[[str], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("DownloadCard")
        self.setFixedHeight(92)
        self.task = task
        self._icons = icons
        self._base_thumb_pil = base_thumb_pil
        self._rendered_thumb_key: tuple[str | None, str] | None = None

        self._on_cancel = on_cancel
        self._on_remove = on_remove
        self._on_open_folder = on_open_folder
        self._on_retry = on_retry
        self._on_copy_url = on_copy_url

        self._build_ui()
        self.refresh(task)

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(10, 8, 12, 8)
        root.setSpacing(12)

        # Miniatura 128x72 com badge de duração embutido
        self.thumb_lbl = QLabel()
        self.thumb_lbl.setFixedSize(128, 72)
        root.addWidget(self.thumb_lbl)

        # Coluna central
        mid = QVBoxLayout()
        mid.setContentsMargins(0, 0, 0, 0)
        mid.setSpacing(3)

        self.title_lbl = ElidedLabel()
        title_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        self.title_lbl.setFont(title_font)
        self.title_lbl.setStyleSheet("color: #F6EFE9;")
        mid.addWidget(self.title_lbl)

        badges_row = QHBoxLayout()
        badges_row.setContentsMargins(0, 0, 0, 0)
        badges_row.setSpacing(6)

        self.fmt_badge = QLabel()
        self.fmt_badge.setObjectName("BadgeFormat")
        badges_row.addWidget(self.fmt_badge)

        self.quality_badge = QLabel()
        self.quality_badge.setObjectName("BadgeMeta")
        badges_row.addWidget(self.quality_badge)

        self.size_badge = QLabel()
        self.size_badge.setObjectName("BadgeMeta")
        badges_row.addWidget(self.size_badge)
        badges_row.addStretch()
        mid.addLayout(badges_row)

        prog_row = QHBoxLayout()
        prog_row.setContentsMargins(0, 2, 0, 0)
        prog_row.setSpacing(8)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        prog_row.addWidget(self.progress_bar, 1)

        self.percent_lbl = QLabel("0%")
        self.percent_lbl.setFixedWidth(36)
        self.percent_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.percent_lbl.setStyleSheet("color: #EBB87A; font-size: 12px; font-weight: 700;")
        prog_row.addWidget(self.percent_lbl)
        mid.addLayout(prog_row)

        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)
        status_row.setSpacing(5)
        self.status_icon = QLabel()
        self.status_icon.setFixedSize(13, 13)
        status_row.addWidget(self.status_icon)

        self.status_lbl = QLabel("Na fila...")
        self.status_lbl.setStyleSheet("color: #C4AE9E; font-size: 11px;")
        status_row.addWidget(self.status_lbl, 1)
        mid.addLayout(status_row)

        root.addLayout(mid, 1)

        # Ações à direita
        actions = QHBoxLayout()
        actions.setContentsMargins(4, 0, 0, 0)
        actions.setSpacing(4)

        self.action_btn = QPushButton("Cancelar")
        self.action_btn.setObjectName("CardActionBtn")
        self.action_btn.setFixedSize(106, 30)
        self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_btn.clicked.connect(self._handle_primary_action)
        actions.addWidget(self.action_btn)

        self.menu_btn = QPushButton()
        self.menu_btn.setObjectName("MenuDotsBtn")
        self.menu_btn.setIcon(self._icons.icon("dots", 16, "#C4AE9E"))
        self.menu_btn.setFixedSize(26, 30)
        self.menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu_btn.clicked.connect(self._open_context_menu)
        actions.addWidget(self.menu_btn)

        root.addLayout(actions)

    def set_base_thumbnail(self, img: Image.Image) -> None:
        self._base_thumb_pil = img
        self._rendered_thumb_key = None
        self._render_thumbnail()

    def _render_thumbnail(self) -> None:
        dur_txt = format_duration(self.task.duration_seconds)
        key = (self.task.thumbnail_url, dur_txt)
        if key == self._rendered_thumb_key:
            return
        self._rendered_thumb_key = key
        composited = compose_thumbnail_with_duration(self._base_thumb_pil, dur_txt)
        self.thumb_lbl.setPixmap(_pil_to_qpixmap(composited))

    def refresh(self, task: DownloadTask) -> None:
        self.task = task
        self.title_lbl.setText(task.title or task.url)
        self.fmt_badge.setText(task.short_format)
        self.quality_badge.setText(task.quality_label.split(" (")[0])

        if task.filesize_bytes:
            self.size_badge.setText(format_bytes(task.filesize_bytes))
            self.size_badge.show()
        else:
            self.size_badge.hide()

        self._render_thumbnail()

        pct = int(round(task.progress * 100))
        self.progress_bar.setValue(pct)
        self.percent_lbl.setText(f"{pct}%")

        status = task.status
        prog_state = "normal"
        accent_btn = False

        if status == "queued":
            self.status_icon.setPixmap(self._icons.pixmap("queue", 12, "#C4AE9E"))
            self.status_lbl.setText("Na fila...")
            self.status_lbl.setStyleSheet("color: #C4AE9E; font-size: 11px;")
            self.action_btn.setText("Cancelar")
            self.action_btn.setIcon(self._icons.icon("cancel", 13, "#F6EFE9"))
        elif status == "extracting":
            self.status_icon.setPixmap(self._icons.pixmap("refresh", 12, "#EBB87A"))
            self.status_lbl.setText("Extraindo metadados...")
            self.status_lbl.setStyleSheet("color: #EBB87A; font-size: 11px;")
            self.action_btn.setText("Cancelar")
            self.action_btn.setIcon(self._icons.icon("cancel", 13, "#F6EFE9"))
        elif status == "downloading":
            self.status_icon.setPixmap(self._icons.pixmap("download", 12, "#E88B4B"))
            self.status_lbl.setText(
                f"Baixando: {pct}%  |  {format_speed(task.speed_bps)}  |  ETA: {format_eta(task.eta_seconds)}"
            )
            self.status_lbl.setStyleSheet("color: #DFCBBF; font-size: 11px;")
            self.action_btn.setText("Cancelar")
            self.action_btn.setIcon(self._icons.icon("cancel", 13, "#F6EFE9"))
        elif status == "converting":
            prog_state = "converting"
            self.status_icon.setPixmap(self._icons.pixmap("refresh", 12, "#FBBF24"))
            self.status_lbl.setText("Convertendo para MP3..." if task.is_audio else "Mesclando áudio e vídeo...")
            self.status_lbl.setStyleSheet("color: #FBBF24; font-size: 11px;")
            self.action_btn.setText("Cancelar")
            self.action_btn.setIcon(self._icons.icon("cancel", 13, "#F6EFE9"))
        elif status == "completed":
            prog_state = "completed"
            accent_btn = True
            self.progress_bar.setValue(100)
            self.percent_lbl.setText("100%")
            self.status_icon.setPixmap(self._icons.pixmap("check", 12, "#EBB87A"))
            self.status_lbl.setText("Concluído!")
            self.status_lbl.setStyleSheet("color: #EBB87A; font-size: 11px; font-weight: 600;")
            self.action_btn.setText("Abrir Pasta")
            self.action_btn.setIcon(self._icons.icon("folder", 13, "#FFF8F2"))
        elif status == "skipped":
            prog_state = "completed"
            accent_btn = True
            self.progress_bar.setValue(100)
            self.percent_lbl.setText("100%")
            self.status_icon.setPixmap(self._icons.pixmap("check", 12, "#6EE7B7"))
            self.status_lbl.setText("Já baixado (ignorado)")
            self.status_lbl.setStyleSheet("color: #6EE7B7; font-size: 11px; font-weight: 600;")
            self.action_btn.setText("Abrir Pasta")
            self.action_btn.setIcon(self._icons.icon("folder", 13, "#FFF8F2"))
        elif status == "cancelled":
            self.status_icon.setPixmap(self._icons.pixmap("cancel", 12, "#8E7565"))
            self.status_lbl.setText("Cancelado")
            self.status_lbl.setStyleSheet("color: #8E7565; font-size: 11px;")
            self.action_btn.setText("Remover")
            self.action_btn.setIcon(self._icons.icon("trash", 13, "#C4AE9E"))
        elif status == "error":
            prog_state = "error"
            self.status_icon.setPixmap(self._icons.pixmap("cancel", 12, "#F87171"))
            self.status_lbl.setText(f"Erro: {task.error_message or 'Falha no download'}")
            self.status_lbl.setStyleSheet("color: #F87171; font-size: 11px;")
            self.action_btn.setText("Remover")
            self.action_btn.setIcon(self._icons.icon("trash", 13, "#C4AE9E"))

        self.progress_bar.setProperty("state", prog_state)
        self.progress_bar.style().unpolish(self.progress_bar)
        self.progress_bar.style().polish(self.progress_bar)

        self.action_btn.setProperty("accent", "true" if accent_btn else "false")
        self.action_btn.style().unpolish(self.action_btn)
        self.action_btn.style().polish(self.action_btn)

    def _handle_primary_action(self) -> None:
        if self.task.status in ("queued", "extracting", "downloading", "converting"):
            self._on_cancel(self.task.task_id)
        elif self.task.status in ("completed", "skipped"):
            self._on_open_folder(self.task)
        else:
            self._on_remove(self.task.task_id)

    def _open_context_menu(self) -> None:
        menu = QMenu(self)
        act_copy = menu.addAction("Copiar Link")
        act_open = menu.addAction("Abrir Pasta") if self.task.status in ("completed", "skipped") else None
        act_retry = menu.addAction("Tentar Novamente") if self.task.status in ("error", "cancelled", "skipped") else None
        act_remove = None
        if self.task.status in ("completed", "skipped", "cancelled", "error"):
            menu.addSeparator()
            act_remove = menu.addAction("Remover da Fila")

        chosen = menu.exec(self.menu_btn.mapToGlobal(QPoint(0, self.menu_btn.height())))
        if chosen == act_copy:
            self._on_copy_url(self.task.url)
        elif act_open and chosen == act_open:
            self._on_open_folder(self.task)
        elif act_retry and chosen == act_retry:
            self._on_retry(self.task)
        elif act_remove and chosen == act_remove:
            self._on_remove(self.task.task_id)
