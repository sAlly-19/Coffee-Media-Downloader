"""Construção da barra lateral de navegação e barra de status inferior."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizeGrip,
    QVBoxLayout,
)

from coffee_app.core.constants import APP_AUTHOR
from coffee_app.ui.widgets.coffee_cup import AnimatedCoffeeCupWidget
from coffee_app.ui.widgets.controls import AnimatedGradientButton


class SidebarMixin:
    """Mixin responsável pela barra lateral e barra de status da janela principal."""

    def _build_sidebar(self) -> QFrame:
        sb = QFrame()
        sb.setObjectName("Sidebar")
        sb.setFixedWidth(206)

        layout = QVBoxLayout(sb)
        layout.setContentsMargins(0, 14, 0, 0)
        layout.setSpacing(6)

        self.coffee_cup = AnimatedCoffeeCupWidget(sb)
        layout.addWidget(self.coffee_cup, 0, Qt.AlignmentFlag.AlignHCenter)

        brand_lbl = QLabel(
            '<div style="text-align:center;">'
            '<span style="color:#FFF8F2;">Coffee</span>'
            '<span style="color:#EBB87A;">Media</span><br>'
            '<span style="color:#F6EFE9;">Downloader</span>'
            '</div>'
        )
        brand_lbl.setStyleSheet("font-size: 17px; font-weight: 700; line-height: 1.15;")
        brand_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(brand_lbl)

        pill_row = QHBoxLayout()
        pill_row.addStretch()
        pro_pill = QLabel("Pro")
        pro_pill.setObjectName("ProPill")
        pill_row.addWidget(pro_pill)
        pill_row.addStretch()
        layout.addLayout(pill_row)

        tagline = QLabel("Baixe vídeos, áudios e\nplaylists com rapidez,\nqualidade e estilo.")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setStyleSheet("color: #C4AE9E; font-size: 11px; margin: 4px 12px 14px 12px;")
        layout.addWidget(tagline)

        self.nav_buttons: dict[str, AnimatedGradientButton] = {}
        for key, icon_name in (
            ("Downloads", "download"),
            ("Histórico", "history"),
            ("Configurações", "settings"),
            ("Sobre", "info"),
        ):
            btn = AnimatedGradientButton(
                f"  {key}",
                align_left=True,
                radius=9,
                active=(key == "Downloads"),
                transparent_idle=True,
            )
            btn.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
            btn.setIcon(self.icons.icon(icon_name, 16, "#F6EFE9"))
            btn.setIconSize(QSize(16, 16))
            btn.setFixedHeight(38)
            btn.clicked.connect(lambda _=False, k=key: self._select_nav(k))
            wrap = QHBoxLayout()
            wrap.setContentsMargins(14, 0, 14, 0)
            wrap.addWidget(btn)
            layout.addLayout(wrap)
            self.nav_buttons[key] = btn

        layout.addStretch()

        author_lbl = QLabel(APP_AUTHOR)
        author_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        author_lbl.setStyleSheet(
            "color: rgba(235, 184, 122, 165); font-size: 10.5px; font-weight: 600; margin: 6px 10px 14px 10px;"
        )
        layout.addWidget(author_lbl)
        return sb

    @staticmethod
    def _make_divider() -> QFrame:
        div = QFrame()
        div.setObjectName("DividerV")
        div.setFixedHeight(42)
        return div

    def _build_status_bar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("StatusBar")
        bar.setFixedHeight(32)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 0, 8, 0)
        layout.setSpacing(10)

        self.footer_dot = QLabel("●")
        self.footer_dot.setStyleSheet("color: #6EE7B7; font-size: 12px;")
        layout.addWidget(self.footer_dot)

        self.footer_state_lbl = QLabel("Pronto para baixar")
        self.footer_state_lbl.setStyleSheet("color: #C4AE9E; font-size: 12px;")
        layout.addWidget(self.footer_state_lbl, 1)

        self.footer_progress_bar = QProgressBar()
        self.footer_progress_bar.setRange(0, 100)
        self.footer_progress_bar.setTextVisible(False)
        self.footer_progress_bar.setFixedSize(110, 6)
        self.footer_progress_bar.hide()
        layout.addWidget(self.footer_progress_bar)

        a_ico = QLabel()
        a_ico.setPixmap(self.icons.pixmap("download", 13, "#C4AE9E"))
        layout.addWidget(a_ico)
        self.footer_active_lbl = QLabel(f"Downloads ativos: 0/{self.manager.max_concurrent}")
        self.footer_active_lbl.setStyleSheet("color: #C4AE9E; font-size: 12px;")
        layout.addWidget(self.footer_active_lbl)

        sep = QLabel("|")
        sep.setStyleSheet("color: #4A3022;")
        layout.addWidget(sep)

        s_ico = QLabel()
        s_ico.setPixmap(self.icons.pixmap("speed", 13, "#EBB87A"))
        layout.addWidget(s_ico)
        self.footer_speed_lbl = QLabel("Velocidade total: 0 KB/s")
        self.footer_speed_lbl.setStyleSheet("color: #EBB87A; font-size: 12px; font-weight: 700;")
        layout.addWidget(self.footer_speed_lbl)

        grip = QSizeGrip(bar)
        grip.setFixedSize(14, 14)
        layout.addWidget(grip, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        return bar
