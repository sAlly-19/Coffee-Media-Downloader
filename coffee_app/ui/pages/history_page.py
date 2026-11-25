"""Página de Histórico de Downloads: filtros, busca, registro e re-download."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from coffee_app.core.constants import VIDEO_FORMAT_LABEL
from coffee_app.core.models import DownloadTask
from coffee_app.core.storage import append_history_entry, save_history
from coffee_app.core.system_utils import open_file, open_folder
from coffee_app.ui.widgets.cards import HistoryCardWidget
from coffee_app.ui.widgets.controls import AnimatedGradientButton


class HistoryPageMixin:
    """Mixin responsável pela tela e ações do Histórico de Downloads."""

    def _build_history_page(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("GlassPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        # Cabeçalho
        hdr = QHBoxLayout()
        ico = QLabel()
        ico.setPixmap(self.icons.pixmap("history", 18, "#EBB87A"))
        hdr.addWidget(ico)
        self.history_title_lbl = QLabel(f"Histórico de Downloads ({len(self.history)})")
        self.history_title_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #FFF8F2;")
        hdr.addWidget(self.history_title_lbl)
        hdr.addStretch()

        btn_clear = QPushButton(" Limpar Histórico")
        btn_clear.setObjectName("SecondaryBtn")
        btn_clear.setIcon(self.icons.icon("trash", 14, "#F6EFE9"))
        btn_clear.setFixedHeight(32)
        btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear.clicked.connect(self._clear_history)
        hdr.addWidget(btn_clear)
        layout.addLayout(hdr)

        # Barra de busca + filtros por formato/status
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        search_box = QFrame()
        search_box.setObjectName("UrlBox")
        search_box.setFixedHeight(34)
        sb_layout = QHBoxLayout(search_box)
        sb_layout.setContentsMargins(10, 0, 10, 0)
        sb_layout.setSpacing(7)

        s_ico = QLabel()
        s_ico.setPixmap(self.icons.pixmap("search", 14, "#8E7565"))
        sb_layout.addWidget(s_ico)

        self.history_search_input = QLineEdit()
        self.history_search_input.setObjectName("UrlInput")
        self.history_search_input.setPlaceholderText("Buscar no histórico por título...")
        self.history_search_input.setClearButtonEnabled(True)
        self.history_search_input.textChanged.connect(self._on_history_search_changed)
        sb_layout.addWidget(self.history_search_input, 1)
        toolbar.addWidget(search_box, 1)

        self.history_filter_btns: dict[str, AnimatedGradientButton] = {}
        h_icons = {"Todos": "grid", "MP4": "video", "MP3": "audio", "Erros": "cancel"}
        for fname in ("Todos", "MP4", "MP3", "Erros"):
            fbtn = AnimatedGradientButton(
                f"{fname} (0)",
                radius=7,
                active=(fname == "Todos"),
            )
            fbtn.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
            fbtn.setIcon(self.icons.icon(h_icons[fname], 12, "#F6EFE9"))
            fbtn.setIconSize(QSize(12, 12))
            fbtn.setFixedHeight(30)
            fbtn.clicked.connect(lambda _=False, fn=fname: self._set_history_filter(fn))
            toolbar.addWidget(fbtn)
            self.history_filter_btns[fname] = fbtn

        layout.addLayout(toolbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.history_layout = QVBoxLayout(container)
        self.history_layout.setContentsMargins(0, 2, 10, 2)
        self.history_layout.setSpacing(7)
        self.history_layout.addStretch(1)
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        self._update_history_filter_styles()
        self._render_history_items()
        return panel

    def _record_history(self, task: DownloadTask) -> None:
        entry = {
            "title": task.title,
            "url": task.url,
            "format": task.short_format,
            "fmt_label": task.fmt_label,
            "quality": task.quality_label,
            "status": task.status,
            "filepath": task.filepath or task.output_dir,
            "output_dir": task.output_dir,
            "size_bytes": task.filesize_bytes,
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "error": task.error_message,
        }
        self.history = append_history_entry(entry)
        self._render_history_items()

    def _on_history_search_changed(self, text: str) -> None:
        self._history_search = text.strip().lower()
        self._render_history_items()

    def _set_history_filter(self, filter_name: str) -> None:
        self._history_filter = filter_name
        self._update_history_filter_styles()
        self._render_history_items()

    def _update_history_filter_styles(self) -> None:
        for key, btn in self.history_filter_btns.items():
            btn.setActive(key == self._history_filter)

    def _remove_history_item(self, index: int) -> None:
        if 0 <= index < len(self.history):
            self.history.pop(index)
            save_history(self.history)
            self._render_history_items()

    def _render_history_items(self) -> None:
        while self.history_layout.count() > 0:
            item = self.history_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.hide()
                w.deleteLater()

        total = len(self.history)
        mp4_count = sum(1 for h in self.history if str(h.get("format", "")).upper() == "MP4")
        mp3_count = sum(1 for h in self.history if str(h.get("format", "")).upper() == "MP3")
        err_count = sum(1 for h in self.history if h.get("status") != "completed")

        self.history_title_lbl.setText(f"Histórico de Downloads ({total})")
        self.history_filter_btns["Todos"].setText(f"Todos ({total})")
        self.history_filter_btns["MP4"].setText(f"MP4 ({mp4_count})")
        self.history_filter_btns["MP3"].setText(f"MP3 ({mp3_count})")
        self.history_filter_btns["Erros"].setText(f"Erros ({err_count})")

        filtered: list[tuple[int, dict[str, Any]]] = []
        for idx, entry in enumerate(self.history):
            fmt = str(entry.get("format") or "").upper()
            ok = entry.get("status") == "completed"
            if self._history_filter == "MP4" and fmt != "MP4":
                continue
            if self._history_filter == "MP3" and fmt != "MP3":
                continue
            if self._history_filter == "Erros" and ok:
                continue
            if self._history_search:
                haystack = f"{entry.get('title', '')} {entry.get('url', '')}".lower()
                if self._history_search not in haystack:
                    continue
            filtered.append((idx, entry))

        if not filtered:
            msg = (
                "Nenhum item encontrado para este filtro/busca."
                if self.history
                else "Nenhum registro no histórico ainda."
            )
            empty = QLabel(msg)
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #8E7565; font-size: 13px; padding: 44px;")
            self.history_layout.addWidget(empty)
            self.history_layout.addStretch(1)
            return

        for idx, entry in filtered[:100]:
            card = HistoryCardWidget(
                index=idx,
                entry=entry,
                icons=self.icons,
                on_open_folder=open_folder,
                on_open_file=open_file,
                on_redownload=self._redownload_history_item,
                on_copy_url=self._copy_to_clipboard,
                on_remove=self._remove_history_item,
            )
            self.history_layout.addWidget(card)
        self.history_layout.addStretch(1)

    def _redownload_history_item(self, item: dict[str, Any]) -> None:
        self._select_nav("Downloads")
        self._enqueue_single_task(
            url=str(item.get("url", "")),
            fmt_label=str(item.get("fmt_label", VIDEO_FORMAT_LABEL)),
            quality_label=str(item.get("quality", "1080p")),
            output_dir=str(item.get("output_dir") or self.settings["output_dir"]),
            title=str(item.get("title") or ""),
            skip_existing=False,
        )

    def _clear_history(self) -> None:
        self.history = []
        save_history([])
        self._render_history_items()
