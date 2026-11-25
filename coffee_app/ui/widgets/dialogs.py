"""Diálogos modais customizados do CoffeeMediaDownloader Pro."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from coffee_app.core.models import PlaylistEntry, PlaylistInspectResult
from coffee_app.core.system_utils import format_duration
from coffee_app.ui.icons import SvgIconStore
from coffee_app.ui.widgets.controls import AnimatedGradientButton


class HighConcurrencyWarningDialog(QDialog):
    """Aviso exibido na primeira vez que o usuário seleciona 5 a 10 downloads simultâneos."""

    def __init__(self, parent: QWidget, count: int, icons: SvgIconStore) -> None:
        super().__init__(parent)
        self.confirmed = False
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(460, 220)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        card = QFrame()
        card.setStyleSheet(
            "QFrame { background: #21140E; border: 1px solid #8A5430; border-radius: 12px; }"
        )
        outer.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)

        hdr = QHBoxLayout()
        ico = QLabel()
        ico.setPixmap(icons.pixmap("alert", 20, "#FBBF24"))
        hdr.addWidget(ico)
        title = QLabel(f"Alta concorrência ({count} simultâneos)")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #FFF8F2; border: none;")
        hdr.addWidget(title)
        hdr.addStretch()
        layout.addLayout(hdr)

        desc = QLabel(
            f"Baixar {count} arquivos ao mesmo tempo consome mais CPU (FFmpeg), memória e banda.\n"
            "Recomendado para computadores mais potentes e conexões rápidas.\n\n"
            "Deseja manter essa configuração?"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 12.5px; color: #C4AE9E; border: none;")
        layout.addWidget(desc)
        layout.addStretch()

        btns = QHBoxLayout()
        btns.setSpacing(8)
        btns.addStretch()

        btn_back = QPushButton("Voltar para 4")
        btn_back.setObjectName("SecondaryBtn")
        btn_back.setFixedHeight(34)
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.clicked.connect(self.reject)
        btns.addWidget(btn_back)

        btn_keep = AnimatedGradientButton(f"Entendi, usar {count}", radius=8)
        btn_keep.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        btn_keep.setFixedSize(160, 34)
        btn_keep.clicked.connect(self._keep)
        btns.addWidget(btn_keep)
        layout.addLayout(btns)

    def _keep(self) -> None:
        self.confirmed = True
        self.accept()


class PlaylistConfirmDialog(QDialog):
    """Modal seletivo exibido quando a URL contém uma playlist com múltiplos vídeos."""

    def __init__(self, parent: QWidget, result: PlaylistInspectResult, icons: SvgIconStore) -> None:
        super().__init__(parent)
        self.choice: str = "cancel"
        self.selected_entries: list[PlaylistEntry] = []
        self._entries = result.entries
        self._items: list[QListWidgetItem] = []

        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(560, 470 if result.single_video_url else 435)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("GlassPanel")
        card.setStyleSheet(
            "QFrame#GlassPanel { background: #21140E; border: 1px solid #6B4834; border-radius: 12px; }"
        )
        root_layout.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(icons.pixmap("queue", 18, "#EBB87A"))
        header.addWidget(icon_lbl)
        title_lbl = QLabel("Playlist detectada")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #FFF8F2;")
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)

        count = len(result.entries)
        pl_title = result.playlist_title or "Playlist"
        if len(pl_title) > 52:
            pl_title = pl_title[:51] + "…"
        desc = QLabel(f'"{pl_title}" contém {count} itens. Selecione o que deseja baixar:')
        desc.setStyleSheet("font-size: 12.5px; color: #C4AE9E;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Barra de filtro rápido + Marcar Todas / Desmarcar
        tools = QHBoxLayout()
        tools.setSpacing(6)

        search_box = QFrame()
        search_box.setObjectName("UrlBox")
        search_box.setFixedHeight(30)
        sb_lay = QHBoxLayout(search_box)
        sb_lay.setContentsMargins(8, 0, 8, 0)
        sb_lay.setSpacing(6)
        s_ico = QLabel()
        s_ico.setPixmap(icons.pixmap("search", 13, "#8E7565"))
        sb_lay.addWidget(s_ico)
        self.search_input = QLineEdit()
        self.search_input.setObjectName("UrlInput")
        self.search_input.setPlaceholderText("Filtrar faixas...")
        self.search_input.textChanged.connect(self._filter_list)
        sb_lay.addWidget(self.search_input, 1)
        tools.addWidget(search_box, 1)

        btn_all_chk = QPushButton("Todas")
        btn_all_chk.setObjectName("SecondaryBtn")
        btn_all_chk.setFixedHeight(30)
        btn_all_chk.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_all_chk.clicked.connect(lambda: self._set_all_checked(True))
        tools.addWidget(btn_all_chk)

        btn_none_chk = QPushButton("Nenhuma")
        btn_none_chk.setObjectName("SecondaryBtn")
        btn_none_chk.setFixedHeight(30)
        btn_none_chk.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_none_chk.clicked.connect(lambda: self._set_all_checked(False))
        tools.addWidget(btn_none_chk)
        layout.addLayout(tools)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("PlaylistList")
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        for idx, entry in enumerate(self._entries, start=1):
            dur = format_duration(entry.duration)
            dur_suffix = f"  [{dur}]" if dur else ""
            item = QListWidgetItem(f"{idx:02d}. {entry.title}{dur_suffix}")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            item.setData(Qt.ItemDataRole.UserRole, entry)
            self.list_widget.addItem(item)
            self._items.append(item)
        self.list_widget.itemChanged.connect(lambda _it: self._refresh_cta())
        layout.addWidget(self.list_widget, 1)

        if result.single_video_url:
            btn_single = QPushButton("Baixar apenas este vídeo")
            btn_single.setObjectName("SecondaryBtn")
            btn_single.setFixedHeight(34)
            btn_single.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_single.clicked.connect(self._choose_single)
            layout.addWidget(btn_single)

        bottom_btns = QHBoxLayout()
        bottom_btns.setSpacing(8)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("SecondaryBtn")
        btn_cancel.setFixedHeight(36)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        bottom_btns.addWidget(btn_cancel)

        self.btn_all = AnimatedGradientButton(f"Baixar selecionados ({count})", radius=8)
        self.btn_all.setIcon(icons.icon("download", 16, "#FFF8F2"))
        self.btn_all.setIconSize(QSize(16, 16))
        self.btn_all.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.btn_all.setFixedHeight(36)
        self.btn_all.clicked.connect(self._choose_playlist)
        bottom_btns.addWidget(self.btn_all, 1)
        layout.addLayout(bottom_btns)

    def _filter_list(self, text: str) -> None:
        q = text.strip().lower()
        for item in self._items:
            item.setHidden(bool(q) and q not in item.text().lower())

    def _set_all_checked(self, checked: bool) -> None:
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        self.list_widget.blockSignals(True)
        for item in self._items:
            if not item.isHidden():
                item.setCheckState(state)
        self.list_widget.blockSignals(False)
        self._refresh_cta()

    def _selected_count(self) -> int:
        return sum(1 for item in self._items if item.checkState() == Qt.CheckState.Checked)

    def _refresh_cta(self) -> None:
        cnt = self._selected_count()
        self.btn_all.setText(f"Baixar selecionados ({cnt})")
        self.btn_all.setEnabled(cnt > 0)

    def _choose_single(self) -> None:
        self.choice = "single"
        self.accept()

    def _choose_playlist(self) -> None:
        self.selected_entries = [
            item.data(Qt.ItemDataRole.UserRole)
            for item in self._items
            if item.checkState() == Qt.CheckState.Checked
        ]
        if not self.selected_entries:
            return
        self.choice = "playlist"
        self.accept()
