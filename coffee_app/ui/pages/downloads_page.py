"""Página principal de Downloads: entrada de URLs, fila em lotes, filtros e callbacks de cards."""

from __future__ import annotations

import os
import threading
import time

from PIL import Image
from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from coffee_app.core.constants import (
    AUDIO_FORMAT_LABEL,
    AUDIO_ORIGINAL_FORMAT_LABEL,
    AUDIO_ORIGINAL_QUALITY_MAP,
    AUDIO_QUALITY_MAP,
    SPEED_LIMIT_MAP,
    VIDEO_FORMAT_LABEL,
    VIDEO_QUALITY_MAP,
)
from coffee_app.core.media_assets import fetch_rounded_thumbnail
from coffee_app.core.models import DownloadTask, PlaylistInspectResult
from coffee_app.core.storage import save_queue_state
from coffee_app.core.system_utils import extract_media_urls, is_valid_media_url, open_folder, sanitize_filename
from coffee_app.ui.theme import (
    FILTER_ALL,
    FILTER_COMPLETED,
    FILTER_DOWNLOADING,
    FILTER_QUEUED,
    VISIBLE_BATCH_SIZE,
)
from coffee_app.ui.widgets.cards import DownloadCardWidget
from coffee_app.ui.widgets.controls import AnimatedGradientButton, ToggleSwitch
from coffee_app.ui.widgets.dialogs import PlaylistConfirmDialog


class DownloadsPageMixin:
    """Mixin da página de Downloads, gerenciamento da fila, clipboard e playlists."""

    def _build_downloads_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 1. Painel Superior
        top_panel = QFrame()
        top_panel.setObjectName("GlassPanel")
        top_layout = QVBoxLayout(top_panel)
        top_layout.setContentsMargins(16, 12, 16, 12)
        top_layout.setSpacing(10)

        header = QHBoxLayout()
        h_icon = QLabel()
        h_icon.setPixmap(self.icons.pixmap("link", 16, "#EBB87A"))
        header.addWidget(h_icon)
        h_lbl = QLabel("Adicionar à Fila")
        h_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #FFF8F2;")
        header.addWidget(h_lbl)
        header.addStretch()

        auto_lbl = QLabel("Auto-colar Links")
        auto_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #C4AE9E;")
        header.addWidget(auto_lbl)

        info_hint = QLabel()
        info_hint.setPixmap(self.icons.pixmap("info", 14, "#8E7565"))
        info_hint.setToolTip("Monitora a área de transferência a cada 1.5s para preencher links novos automaticamente.")
        header.addWidget(info_hint)

        self.auto_paste_switch = ToggleSwitch()
        self.auto_paste_switch.setChecked(bool(self.settings.get("auto_paste", False)))
        self.auto_paste_switch.toggled.connect(self._on_auto_paste_toggled)
        header.addWidget(self.auto_paste_switch)
        top_layout.addLayout(header)

        # Barra de URL + Colar / Limpar
        url_row = QHBoxLayout()
        url_row.setSpacing(8)

        self.url_box = QFrame()
        self.url_box.setObjectName("UrlBox")
        self.url_box.setFixedHeight(38)
        ub_layout = QHBoxLayout(self.url_box)
        ub_layout.setContentsMargins(10, 0, 10, 0)
        ub_layout.setSpacing(8)

        in_icon = QLabel()
        in_icon.setPixmap(self.icons.pixmap("link", 15, "#8E7565"))
        ub_layout.addWidget(in_icon)

        self.url_input = QLineEdit()
        self.url_input.setObjectName("UrlInput")
        self.url_input.setPlaceholderText("Cole um ou mais links, playlist ou arraste um .txt aqui...")
        self.url_input.returnPressed.connect(self._on_add_clicked)
        ub_layout.addWidget(self.url_input, 1)
        url_row.addWidget(self.url_box, 1)

        btn_paste = QPushButton(" Colar")
        btn_paste.setObjectName("SecondaryBtn")
        btn_paste.setIcon(self.icons.icon("paste", 14, "#F6EFE9"))
        btn_paste.setFixedHeight(38)
        btn_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_paste.clicked.connect(self._paste_from_clipboard)
        url_row.addWidget(btn_paste)

        btn_clear = QPushButton(" Limpar")
        btn_clear.setObjectName("SecondaryBtn")
        btn_clear.setIcon(self.icons.icon("trash", 14, "#F6EFE9"))
        btn_clear.setFixedHeight(38)
        btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear.clicked.connect(self._clear_url_entry)
        url_row.addWidget(btn_clear)
        top_layout.addLayout(url_row)

        # Linha Formato / Qualidade / Adicionar
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(10)

        lbl_fmt = QLabel("Formato:")
        lbl_fmt.setStyleSheet("font-size: 12px; font-weight: 600; color: #C4AE9E;")
        ctrl_row.addWidget(lbl_fmt)

        self.format_combo = QComboBox()
        self.format_combo.addItem(self.icons.icon("video", 14, "#EBB87A"), VIDEO_FORMAT_LABEL)
        self.format_combo.addItem(self.icons.icon("audio", 14, "#EBB87A"), AUDIO_FORMAT_LABEL)
        self.format_combo.addItem(self.icons.icon("audio", 14, "#6EE7B7"), AUDIO_ORIGINAL_FORMAT_LABEL)
        default_fmt = str(self.settings.get("default_format", VIDEO_FORMAT_LABEL))
        if default_fmt in (VIDEO_FORMAT_LABEL, AUDIO_FORMAT_LABEL, AUDIO_ORIGINAL_FORMAT_LABEL):
            self.format_combo.setCurrentText(default_fmt)
        self.format_combo.setFixedWidth(185)
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        ctrl_row.addWidget(self.format_combo)

        lbl_qual = QLabel("Qualidade:")
        lbl_qual.setStyleSheet("font-size: 12px; font-weight: 600; color: #C4AE9E; margin-left: 6px;")
        ctrl_row.addWidget(lbl_qual)

        self.quality_combo = QComboBox()
        self.quality_combo.setFixedWidth(185)
        self._populate_quality_combo(self.format_combo.currentText())
        self.quality_combo.currentTextChanged.connect(lambda _: self._save_settings_from_ui())
        ctrl_row.addWidget(self.quality_combo)

        ctrl_row.addStretch()

        self.add_btn = AnimatedGradientButton("Adicionar à Fila", radius=8)
        self.add_btn.setIcon(self.icons.icon("plus_circle", 16, "#FFF8F2"))
        self.add_btn.setIconSize(QSize(16, 16))
        self.add_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.add_btn.setFixedSize(176, 36)
        self.add_btn.clicked.connect(self._on_add_clicked)
        self._add_soft_glow(self.add_btn, "#D97736", 18)
        ctrl_row.addWidget(self.add_btn)

        top_layout.addLayout(ctrl_row)
        layout.addWidget(top_panel)

        # 2. Painel Central: Fila de Downloads
        queue_panel = QFrame()
        queue_panel.setObjectName("GlassPanel")
        q_layout = QVBoxLayout(queue_panel)
        q_layout.setContentsMargins(14, 10, 14, 10)
        q_layout.setSpacing(8)

        # Linha 1 do cabeçalho: título + progresso geral + Cancelar Tudo
        q_header = QHBoxLayout()
        q_header.setSpacing(8)
        q_icon = QLabel()
        q_icon.setPixmap(self.icons.pixmap("download", 16, "#EBB87A"))
        q_header.addWidget(q_icon)

        self.queue_title_lbl = QLabel("Fila de Downloads (0)")
        self.queue_title_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #FFF8F2;")
        q_header.addWidget(self.queue_title_lbl)

        self.queue_summary_pill = QLabel("")
        self.queue_summary_pill.setObjectName("BadgeMeta")
        self.queue_summary_pill.hide()
        q_header.addWidget(self.queue_summary_pill)
        q_header.addStretch()

        self.cancel_all_btn = QPushButton(" Cancelar Tudo")
        self.cancel_all_btn.setObjectName("DangerBtn")
        self.cancel_all_btn.setIcon(self.icons.icon("cancel", 12, "#FFD7D0"))
        self.cancel_all_btn.setFixedHeight(28)
        self.cancel_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_all_btn.clicked.connect(self._cancel_all_tasks)
        self.cancel_all_btn.hide()
        q_header.addWidget(self.cancel_all_btn)
        q_layout.addLayout(q_header)

        # Linha 2 do cabeçalho: busca na fila + pílulas de filtro (nunca corta com 3+ dígitos)
        q_toolbar = QHBoxLayout()
        q_toolbar.setSpacing(8)

        q_search_box = QFrame()
        q_search_box.setObjectName("UrlBox")
        q_search_box.setFixedHeight(30)
        qs_layout = QHBoxLayout(q_search_box)
        qs_layout.setContentsMargins(9, 0, 8, 0)
        qs_layout.setSpacing(6)

        qs_ico = QLabel()
        qs_ico.setPixmap(self.icons.pixmap("search", 13, "#8E7565"))
        qs_layout.addWidget(qs_ico)

        self.queue_search_input = QLineEdit()
        self.queue_search_input.setObjectName("UrlInput")
        self.queue_search_input.setPlaceholderText("Filtrar fila por título...")
        self.queue_search_input.setClearButtonEnabled(True)
        self.queue_search_input.textChanged.connect(self._on_queue_search_changed)
        qs_layout.addWidget(self.queue_search_input, 1)
        q_toolbar.addWidget(q_search_box, 1)

        self.filter_buttons: dict[str, AnimatedGradientButton] = {}
        filter_icons = {
            FILTER_ALL: "grid",
            FILTER_DOWNLOADING: "download",
            FILTER_QUEUED: "queue",
            FILTER_COMPLETED: "check",
        }
        for fname in (FILTER_ALL, FILTER_DOWNLOADING, FILTER_QUEUED, FILTER_COMPLETED):
            fbtn = AnimatedGradientButton(
                f"{fname} (0)",
                radius=7,
                active=(fname == FILTER_ALL),
            )
            fbtn.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
            fbtn.setIcon(self.icons.icon(filter_icons[fname], 12, "#F6EFE9"))
            fbtn.setIconSize(QSize(12, 12))
            fbtn.setFixedHeight(28)
            fbtn.clicked.connect(lambda _=False, fn=fname: self._set_queue_filter(fn))
            q_toolbar.addWidget(fbtn)
            self.filter_buttons[fname] = fbtn

        q_layout.addLayout(q_toolbar)

        # Banner discreto para retomar fila salva na sessão anterior
        self.resume_banner = QFrame()
        self.resume_banner.setStyleSheet(
            "QFrame { background: rgba(75, 42, 22, 165); border: 1px solid #C86D30; border-radius: 8px; }"
        )
        rb_lay = QHBoxLayout(self.resume_banner)
        rb_lay.setContentsMargins(12, 6, 10, 6)
        rb_lay.setSpacing(8)
        rb_ico = QLabel()
        rb_ico.setPixmap(self.icons.pixmap("refresh", 14, "#F3BC7D"))
        rb_ico.setStyleSheet("border: none; background: transparent;")
        rb_lay.addWidget(rb_ico)
        self.resume_banner_lbl = QLabel()
        self.resume_banner_lbl.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #FFF8F2; border: none; background: transparent;"
        )
        rb_lay.addWidget(self.resume_banner_lbl, 1)

        btn_resume = AnimatedGradientButton("Retomar Fila", radius=6)
        btn_resume.setIcon(self.icons.icon("refresh", 13, "#FFF8F2"))
        btn_resume.setIconSize(QSize(13, 13))
        btn_resume.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        btn_resume.setFixedSize(124, 26)
        btn_resume.clicked.connect(self._resume_saved_queue)
        rb_lay.addWidget(btn_resume)

        btn_discard = QPushButton("Descartar")
        btn_discard.setObjectName("SecondaryBtn")
        btn_discard.setFixedHeight(26)
        btn_discard.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_discard.clicked.connect(self._discard_saved_queue)
        rb_lay.addWidget(btn_discard)

        if self._saved_queue_items:
            self.resume_banner_lbl.setText(
                f"Fila anterior encontrada ({len(self._saved_queue_items)} itens pendentes)."
            )
            self.resume_banner.show()
        else:
            self.resume_banner.hide()
        q_layout.addWidget(self.resume_banner)

        self.queue_scroll = QScrollArea()
        self.queue_scroll.setWidgetResizable(True)
        self.queue_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.queue_container = QWidget()
        self.queue_container.setStyleSheet("background: transparent;")
        self.queue_cards_layout = QVBoxLayout(self.queue_container)
        self.queue_cards_layout.setContentsMargins(0, 2, 10, 2)
        self.queue_cards_layout.setSpacing(7)

        self.empty_queue_lbl = QLabel(
            "Nenhum download na fila.\nCole um link acima ou ative o Auto-colar Links."
        )
        self.empty_queue_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_queue_lbl.setStyleSheet("color: #8E7565; font-size: 13px; padding: 48px;")
        self.queue_cards_layout.addWidget(self.empty_queue_lbl)
        self.queue_cards_layout.addStretch(1)

        self.queue_scroll.setWidget(self.queue_container)
        q_layout.addWidget(self.queue_scroll, 1)
        layout.addWidget(queue_panel, 1)

        # 3. Painel Inferior: Configurações Globais
        bottom_panel = QFrame()
        bottom_panel.setObjectName("GlassPanel")
        b_layout = QHBoxLayout(bottom_panel)
        b_layout.setContentsMargins(14, 10, 14, 10)
        b_layout.setSpacing(12)

        # Pasta de destino
        dest_col = QVBoxLayout()
        dest_col.setSpacing(4)
        dest_hdr = QHBoxLayout()
        dest_hdr.setSpacing(5)
        f_ico = QLabel()
        f_ico.setPixmap(self.icons.pixmap("folder", 13, "#EBB87A"))
        dest_hdr.addWidget(f_ico)
        dest_hdr.addWidget(QLabel("Pasta de Destino:"))
        dest_hdr.addStretch()
        dest_col.addLayout(dest_hdr)

        dest_val_row = QHBoxLayout()
        dest_val_row.setSpacing(6)
        self.output_dir_lbl = QLabel()
        self.output_dir_lbl.setStyleSheet(
            "background: #2B1C14; border: 1px solid #4E3324; border-radius: 7px; "
            "padding: 4px 10px; color: #F6EFE9; font-size: 12px;"
        )
        self.output_dir_lbl.setFixedHeight(30)
        self._update_output_dir_label()
        dest_val_row.addWidget(self.output_dir_lbl, 1)

        btn_browse = QPushButton(" Alterar")
        btn_browse.setIcon(self.icons.icon("folder", 14, "#F6EFE9"))
        btn_browse.setIconSize(QSize(14, 14))
        btn_browse.setObjectName("SecondaryBtn")
        btn_browse.setFixedHeight(30)
        btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_browse.clicked.connect(self._choose_output_dir)
        dest_val_row.addWidget(btn_browse)
        dest_col.addLayout(dest_val_row)
        b_layout.addLayout(dest_col, 2)

        b_layout.addWidget(self._make_divider())

        # Downloads simultâneos (1 a 10 com selo de aviso acima de 4)
        conc_col = QVBoxLayout()
        conc_col.setSpacing(4)
        conc_hdr = QHBoxLayout()
        conc_hdr.setSpacing(5)
        s_ico = QLabel()
        s_ico.setPixmap(self.icons.pixmap("stack", 13, "#EBB87A"))
        conc_hdr.addWidget(s_ico)
        conc_hdr.addWidget(QLabel("Simultâneos"))
        self.high_load_badge = QLabel("⚠ Alta carga")
        self.high_load_badge.setToolTip("Acima de 4 downloads simultâneos exige mais CPU (FFmpeg), memória e rede.")
        self.high_load_badge.setStyleSheet(
            "background: rgba(92, 54, 18, 180); border: 1px solid #D97706; border-radius: 5px; "
            "color: #FBBF24; font-size: 10px; font-weight: 700; padding: 1px 5px;"
        )
        self.high_load_badge.setVisible(int(self.settings.get("max_concurrent", 3)) > 4)
        conc_hdr.addWidget(self.high_load_badge)
        conc_hdr.addStretch()
        conc_col.addLayout(conc_hdr)

        self.concurrent_combo = QComboBox()
        self.concurrent_combo.addItems([str(i) for i in range(1, 11)])
        self.concurrent_combo.setCurrentText(str(self.settings.get("max_concurrent", 3)))
        self.concurrent_combo.setFixedHeight(30)
        self.concurrent_combo.currentTextChanged.connect(self._on_concurrent_changed)
        conc_col.addWidget(self.concurrent_combo)
        b_layout.addLayout(conc_col, 1)

        b_layout.addWidget(self._make_divider())

        # Limite de velocidade
        spd_col = QVBoxLayout()
        spd_col.setSpacing(4)
        spd_hdr = QHBoxLayout()
        spd_hdr.setSpacing(5)
        sp_ico = QLabel()
        sp_ico.setPixmap(self.icons.pixmap("speed", 13, "#EBB87A"))
        spd_hdr.addWidget(sp_ico)
        spd_hdr.addWidget(QLabel("Limite de Velocidade"))
        spd_hdr.addStretch()
        spd_col.addLayout(spd_hdr)

        self.speed_combo = QComboBox()
        self.speed_combo.addItems(list(SPEED_LIMIT_MAP.keys()))
        self.speed_combo.setCurrentText(str(self.settings.get("speed_limit", "Ilimitado")))
        self.speed_combo.setFixedHeight(30)
        self.speed_combo.currentTextChanged.connect(self._on_speed_changed)
        spd_col.addWidget(self.speed_combo)
        b_layout.addLayout(spd_col, 1)

        b_layout.addWidget(self._make_divider())

        btn_clean = QPushButton(" Limpar Concluídos")
        btn_clean.setObjectName("SecondaryBtn")
        btn_clean.setIcon(self.icons.icon("trash", 14, "#F6EFE9"))
        btn_clean.setFixedHeight(34)
        btn_clean.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clean.clicked.connect(self._clear_finished_cards)
        b_layout.addWidget(btn_clean, 0, Qt.AlignmentFlag.AlignBottom)

        layout.addWidget(bottom_panel)
        self._update_filter_styles()
        return page

    def _on_queue_search_changed(self, text: str) -> None:
        self._queue_search = text.strip().lower()
        self._render_limit = VISIBLE_BATCH_SIZE
        self._relayout_cards()

    def _set_queue_filter(self, filter_name: str) -> None:
        self._active_filter = filter_name
        self._render_limit = VISIBLE_BATCH_SIZE
        self._update_filter_styles()
        self._relayout_cards()

    def _update_filter_styles(self) -> None:
        for key, btn in self.filter_buttons.items():
            btn.setActive(key == self._active_filter)

    def _matches_filter(self, task: DownloadTask) -> bool:
        if self._queue_search:
            haystack = f"{task.title} {task.url}".lower()
            if self._queue_search not in haystack:
                return False
        if self._active_filter == FILTER_ALL:
            return True
        if self._active_filter == FILTER_DOWNLOADING:
            return task.status in ("extracting", "downloading", "converting")
        if self._active_filter == FILTER_QUEUED:
            return task.status == "queued"
        if self._active_filter == FILTER_COMPLETED:
            return task.status in ("completed", "skipped", "cancelled", "error")
        return True

    def _get_ordered_filtered_tasks(self) -> list[DownloadTask]:
        priority = {
            "downloading": 0,
            "converting": 0,
            "extracting": 0,
            "queued": 1,
            "completed": 2,
            "skipped": 2,
            "error": 2,
            "cancelled": 2,
        }
        matching = [
            self._tasks[tid]
            for tid in self._task_order
            if tid in self._tasks and self._matches_filter(self._tasks[tid])
        ]
        matching.sort(key=lambda t: priority.get(t.status, 3))
        return matching

    def _get_or_create_card(self, task: DownloadTask) -> DownloadCardWidget:
        card = self._cards.get(task.task_id)
        if card is not None:
            return card

        placeholder = self._placeholder_audio_pil if task.is_audio else self._placeholder_video_pil
        cached = self._thumb_cache.get(task.thumbnail_url) if task.thumbnail_url else None
        card = DownloadCardWidget(
            task=task,
            icons=self.icons,
            base_thumb_pil=cached or placeholder,
            on_cancel=self.manager.cancel_task,
            on_remove=self._remove_card,
            on_open_folder=self._open_task_folder,
            on_retry=self._retry_task,
            on_copy_url=self._copy_to_clipboard,
            parent=self.queue_container,
        )
        self._cards[task.task_id] = card
        if task.thumbnail_url and cached is None:
            self._ensure_thumbnail_fetched(task.thumbnail_url)
        return card

    def _relayout_cards(self) -> None:
        # Remove itens do layout mantendo o parent=self.queue_container para nunca virarem janelas soltas
        while self.queue_cards_layout.count() > 0:
            item = self.queue_cards_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.hide()

        ordered = self._get_ordered_filtered_tasks()
        visible = ordered[: self._render_limit]
        visible_ids = {t.task_id for t in visible}

        for tid in list(self._cards.keys()):
            if tid not in self._tasks or (len(self._cards) > VISIBLE_BATCH_SIZE * 2 and tid not in visible_ids):
                self._cards[tid].hide()
                self._cards[tid].deleteLater()
                del self._cards[tid]

        if not visible:
            self.empty_queue_lbl.show()
            self.queue_cards_layout.addWidget(self.empty_queue_lbl)
        else:
            self.empty_queue_lbl.hide()
            for task in visible:
                card = self._get_or_create_card(task)
                card.show()
                self.queue_cards_layout.addWidget(card)

        remaining = len(ordered) - len(visible)
        if remaining > 0:
            if self._load_more_btn is None:
                self._load_more_btn = QPushButton(self.queue_container)
                self._load_more_btn.setObjectName("SecondaryBtn")
                self._load_more_btn.setFixedHeight(34)
                self._load_more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                self._load_more_btn.clicked.connect(self._load_more_cards)
            next_chunk = min(VISIBLE_BATCH_SIZE, remaining)
            self._load_more_btn.setText(f"Mostrar mais {next_chunk} itens (restam {remaining} na fila)")
            self._load_more_btn.show()
            self.queue_cards_layout.addWidget(self._load_more_btn)

        self.queue_cards_layout.addStretch(1)
        self._update_queue_counters()

    def _load_more_cards(self) -> None:
        self._render_limit += VISIBLE_BATCH_SIZE
        self._relayout_cards()

    def _update_queue_counters(self) -> None:
        tasks = list(self._tasks.values())
        total = len(tasks)
        active = sum(1 for t in tasks if t.status in ("extracting", "downloading", "converting"))
        queued = sum(1 for t in tasks if t.status == "queued")
        completed_ok = sum(1 for t in tasks if t.status in ("completed", "skipped"))
        done = sum(1 for t in tasks if t.status in ("completed", "skipped", "cancelled", "error"))

        self.queue_title_lbl.setText(f"Fila de Downloads ({total})")
        if total > 1:
            self.queue_summary_pill.setText(f"{completed_ok}/{total} concluídos")
            self.queue_summary_pill.show()
        else:
            self.queue_summary_pill.hide()

        self.filter_buttons[FILTER_ALL].setText(f"{FILTER_ALL} ({total})")
        self.filter_buttons[FILTER_DOWNLOADING].setText(f"{FILTER_DOWNLOADING} ({active})")
        self.filter_buttons[FILTER_QUEUED].setText(f"{FILTER_QUEUED} ({queued})")
        self.filter_buttons[FILTER_COMPLETED].setText(f"{FILTER_COMPLETED} ({done})")
        self.cancel_all_btn.setVisible(active + queued > 0)

    def _populate_quality_combo(self, fmt_label: str) -> None:
        self.quality_combo.blockSignals(True)
        self.quality_combo.clear()
        if fmt_label == AUDIO_FORMAT_LABEL:
            options = list(AUDIO_QUALITY_MAP.keys())
            preferred = str(self.settings.get("default_audio_quality", options[0]))
        elif fmt_label == AUDIO_ORIGINAL_FORMAT_LABEL:
            options = list(AUDIO_ORIGINAL_QUALITY_MAP.keys())
            preferred = options[0]
        else:
            options = list(VIDEO_QUALITY_MAP.keys())
            preferred = str(self.settings.get("default_video_quality", "1080p"))
        self.quality_combo.addItems(options)
        self.quality_combo.setCurrentText(preferred if preferred in options else options[0])
        self.quality_combo.blockSignals(False)

    def _on_format_changed(self, fmt_label: str) -> None:
        self._populate_quality_combo(fmt_label)
        self._save_settings_from_ui()

    def _paste_from_clipboard(self) -> None:
        text = QApplication.clipboard().text().strip()
        if text:
            self.url_input.setText(text)
            self._flash_url_box("accent")

    def _clear_url_entry(self) -> None:
        self.url_input.clear()
        self.url_input.clearFocus()

    def _flash_url_box(self, kind: str = "accent") -> None:
        self.url_box.setProperty("flash", kind)
        self.url_box.style().unpolish(self.url_box)
        self.url_box.style().polish(self.url_box)
        QTimer.singleShot(1800, self._restore_url_box)

    def _restore_url_box(self) -> None:
        if not self._closing:
            self.url_box.setProperty("flash", "")
            self.url_box.style().unpolish(self.url_box)
            self.url_box.style().polish(self.url_box)

    def _on_auto_paste_toggled(self, checked: bool) -> None:
        self._save_settings_from_ui()
        if checked:
            self._last_clipboard_text = QApplication.clipboard().text().strip()

    def _poll_clipboard(self) -> None:
        if self._closing or not self.auto_paste_switch.isChecked():
            return
        current = QApplication.clipboard().text().strip()
        if current and current != self._last_clipboard_text and is_valid_media_url(current):
            self._last_clipboard_text = current
            self.url_input.setText(current)
            self._flash_url_box("accent")
            self.footer_state_lbl.setText("Link detectado da área de transferência!")

    def _on_add_clicked(self) -> None:
        raw_text = self.url_input.text().strip()
        urls = extract_media_urls(raw_text)
        if not urls:
            self._flash_url_box("error")
            self.footer_state_lbl.setText("Informe uma ou mais URLs válidas de vídeo ou playlist.")
            return

        fmt_label = self.format_combo.currentText()
        quality_label = self.quality_combo.currentText()
        output_dir = str(self.settings["output_dir"])

        if len(urls) > 1:
            tasks = [
                self._create_task(url=u, fmt_label=fmt_label, quality_label=quality_label, output_dir=output_dir)
                for u in urls
            ]
            self._enqueue_batch(tasks)
            self._clear_url_entry()
            self.footer_state_lbl.setText(f"{len(tasks)} links adicionados à fila.")
            self._sync_footer_state_text(keep_custom=True)
            return

        url = urls[0]
        if url in self._inspecting_urls:
            return

        self._inspecting_urls.add(url)
        self.add_btn.setEnabled(False)
        self.add_btn.setText("Verificando...")
        self.footer_state_lbl.setText("Analisando link...")

        self.manager.inspect_url_async(
            url,
            lambda res: self.inspect_finished_signal.emit(res, fmt_label, quality_label, output_dir)
            if not self._closing
            else None,
        )

    def _handle_inspect_result(
        self,
        result: PlaylistInspectResult,
        fmt_label: str,
        quality_label: str,
        output_dir: str,
    ) -> None:
        if self._closing:
            return
        self._inspecting_urls.discard(result.source_url)
        self.add_btn.setEnabled(True)
        self.add_btn.setText("Adicionar à Fila")
        self._sync_footer_state_text()

        if result.error and not result.entries:
            self._enqueue_single_task(result.source_url, fmt_label, quality_label, output_dir)
            self._clear_url_entry()
            return

        if result.is_playlist and len(result.entries) > 1:
            dialog = PlaylistConfirmDialog(self, result, self.icons)
            dialog.exec()

            if dialog.choice == "single" and result.single_video_url:
                self._enqueue_single_task(result.single_video_url, fmt_label, quality_label, output_dir)
                self._clear_url_entry()
            elif dialog.choice == "playlist" and dialog.selected_entries:
                target_dir = output_dir
                if self.settings.get("playlist_subfolder", False):
                    folder_name = sanitize_filename(result.playlist_title or "Playlist", max_length=80)
                    target_dir = os.path.join(output_dir, folder_name)

                use_num = bool(self.settings.get("playlist_numbering", False))
                tasks = [
                    self._create_task(
                        url=e.url,
                        fmt_label=fmt_label,
                        quality_label=quality_label,
                        output_dir=target_dir,
                        title=e.title,
                        duration=e.duration,
                        thumbnail_url=e.thumbnail_url,
                        filename_prefix=f"{idx:02d} - " if use_num else "",
                    )
                    for idx, e in enumerate(dialog.selected_entries, start=1)
                ]
                self._enqueue_batch(tasks)
                self._clear_url_entry()
            else:
                self.footer_state_lbl.setText("Adição de playlist cancelada.")
            self._sync_footer_state_text(keep_custom=True)
            return

        self._enqueue_single_task(result.source_url, fmt_label, quality_label, output_dir)
        self._clear_url_entry()

    def _create_task(
        self,
        url: str,
        fmt_label: str,
        quality_label: str,
        output_dir: str,
        title: str = "",
        duration: float | None = None,
        thumbnail_url: str | None = None,
        skip_existing: bool | None = None,
        filename_prefix: str = "",
    ) -> DownloadTask:
        should_skip = (
            bool(self.settings.get("skip_existing", True))
            if skip_existing is None
            else skip_existing
        )
        return DownloadTask(
            url=url,
            fmt_label=fmt_label,
            quality_label=quality_label,
            output_dir=output_dir,
            title=title or url,
            duration_seconds=duration,
            thumbnail_url=thumbnail_url,
            embed_metadata=bool(self.settings.get("embed_metadata", True)),
            skip_existing=should_skip,
            cookies_browser=str(self.settings.get("cookies_browser", "Nenhum")),
            cookies_file=str(self.settings.get("cookies_file", "")),
            filename_prefix=filename_prefix,
        )

    def _enqueue_single_task(
        self,
        url: str,
        fmt_label: str,
        quality_label: str,
        output_dir: str,
        title: str = "",
        duration: float | None = None,
        thumbnail_url: str | None = None,
        skip_existing: bool | None = None,
    ) -> None:
        self._enqueue_batch(
            [
                self._create_task(
                    url, fmt_label, quality_label, output_dir, title, duration, thumbnail_url, skip_existing
                )
            ]
        )

    def _enqueue_batch(self, tasks: list[DownloadTask]) -> None:
        for task in tasks:
            self._tasks[task.task_id] = task
            self._task_order.append(task.task_id)
            self._last_known_statuses[task.task_id] = task.status
        self._relayout_cards()
        for task in tasks:
            self.manager.enqueue(task)
        self._refresh_footer_stats()

    def _emit_task_update(self, task: DownloadTask) -> None:
        if not self._closing:
            self.task_updated_signal.emit(task)

    def _apply_task_update_ui(self, task: DownloadTask) -> None:
        if self._closing or task.task_id not in self._tasks:
            return

        previous_status = self._last_known_statuses.get(task.task_id)
        status_changed = previous_status != task.status

        now = time.monotonic()
        if not status_changed and task.status == "downloading":
            last_ts = self._last_progress_ui_ts.get(task.task_id, 0.0)
            if now - last_ts < 0.08 and task.progress < 1.0:
                return
        self._last_progress_ui_ts[task.task_id] = now
        self._last_known_statuses[task.task_id] = task.status

        card = self._cards.get(task.task_id)
        if card is not None:
            card.refresh(task)
            if task.thumbnail_url and task.thumbnail_url not in self._thumb_cache:
                self._ensure_thumbnail_fetched(task.thumbnail_url)
            if status_changed:
                self._relayout_cards()
        else:
            if status_changed:
                self._relayout_cards()
            else:
                self._update_queue_counters()

        if task.status in ("completed", "error") and task.task_id not in self._recorded_history_ids:
            self._recorded_history_ids.add(task.task_id)
            self._record_history(task)

        if status_changed:
            self._refresh_footer_stats()

    def _ensure_thumbnail_fetched(self, url: str) -> None:
        if not url or url in self._thumb_cache or url in self._thumb_fetching:
            return
        self._thumb_fetching.add(url)

        def _worker() -> None:
            img = fetch_rounded_thumbnail(url, size=(128, 72))
            self._thumb_fetching.discard(url)
            if img is not None and not self._closing:
                self.thumb_fetched_signal.emit(url, img)

        threading.Thread(target=_worker, daemon=True, name="CoffeeThumb").start()

    def _apply_cached_thumbnail(self, url: str, img: Image.Image) -> None:
        self._thumb_cache[url] = img
        for card in self._cards.values():
            if card.task.thumbnail_url == url:
                card.set_base_thumbnail(img)

    def _cancel_all_tasks(self) -> None:
        self.manager.cancel_all()
        self._relayout_cards()
        self.footer_state_lbl.setText("Todos os downloads pendentes/ativos foram cancelados.")

    def _remove_card(self, task_id: str) -> None:
        self._tasks.pop(task_id, None)
        self._last_known_statuses.pop(task_id, None)
        if task_id in self._task_order:
            self._task_order.remove(task_id)
        card = self._cards.pop(task_id, None)
        if card:
            card.deleteLater()
        self.manager.remove_task(task_id)
        self._relayout_cards()

    def _clear_finished_cards(self) -> None:
        finished_ids = [
            tid for tid, t in self._tasks.items() if t.status in ("completed", "skipped", "cancelled", "error")
        ]
        for tid in finished_ids:
            self._tasks.pop(tid, None)
            self._last_known_statuses.pop(tid, None)
            if tid in self._task_order:
                self._task_order.remove(tid)
            card = self._cards.pop(tid, None)
            if card:
                card.deleteLater()
            self.manager.remove_task(tid)
        self._relayout_cards()

    def _open_task_folder(self, task: DownloadTask) -> None:
        if not open_folder(task.filepath or task.output_dir):
            open_folder(task.output_dir)

    def _retry_task(self, old_task: DownloadTask) -> None:
        self._remove_card(old_task.task_id)
        self._enqueue_single_task(
            url=old_task.url,
            fmt_label=old_task.fmt_label,
            quality_label=old_task.quality_label,
            output_dir=old_task.output_dir,
            title=old_task.title,
            duration=old_task.duration_seconds,
            thumbnail_url=old_task.thumbnail_url,
            skip_existing=False,
        )

    def _copy_to_clipboard(self, text: str) -> None:
        QApplication.clipboard().setText(text)
        self.footer_state_lbl.setText("Link copiado para a área de transferência.")

    def _resume_saved_queue(self) -> None:
        items = list(self._saved_queue_items)
        self._saved_queue_items = []
        self.resume_banner.hide()
        save_queue_state([])
        if not items:
            return
        tasks = [
            self._create_task(
                url=str(it.get("url", "")),
                fmt_label=str(it.get("fmt_label", VIDEO_FORMAT_LABEL)),
                quality_label=str(it.get("quality_label", "1080p")),
                output_dir=str(it.get("output_dir") or self.settings["output_dir"]),
                title=str(it.get("title") or ""),
                duration=it.get("duration_seconds"),
                thumbnail_url=it.get("thumbnail_url"),
                skip_existing=bool(it.get("skip_existing", True)),
                filename_prefix=str(it.get("filename_prefix") or ""),
            )
            for it in items
            if it.get("url")
        ]
        if tasks:
            self._enqueue_batch(tasks)

    def _discard_saved_queue(self) -> None:
        self._saved_queue_items = []
        self.resume_banner.hide()
        save_queue_state([])
