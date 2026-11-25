"""Componentes estruturais da janela frameless (TitleBar e fundo CoffeeRootFrame)."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QPoint, QSize, Qt
from PySide6.QtGui import QColor, QLinearGradient, QMouseEvent, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton

from coffee_app.ui.icons import SvgIconStore


class TitleBar(QFrame):
    """Barra de título customizada integrada ao tema café escuro."""

    def __init__(self, window: QMainWindow, logo_pix: QPixmap, icons: SvgIconStore) -> None:
        super().__init__(window)
        self.setObjectName("TitleBar")
        self.setFixedHeight(40)
        self._window = window
        self._icons = icons
        self._drag_pos: QPoint | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 10, 0)
        layout.setSpacing(6)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(logo_pix.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(icon_lbl)

        title_lbl = QLabel(
            '<span style="color:#FFF8F2;">Coffee</span>'
            '<span style="color:#EBB87A;">Media</span>'
            '<span style="color:#FFF8F2;">Downloader</span>'
        )
        title_lbl.setStyleSheet("font-size: 13px; font-weight: 700;")
        layout.addWidget(title_lbl)
        layout.addStretch()

        btn_min = QPushButton()
        btn_min.setObjectName("WinBtn")
        btn_min.setIcon(icons.icon("win_min", 13, "#E6D6CA"))
        btn_min.setIconSize(QSize(13, 13))
        btn_min.setFixedSize(32, 24)
        btn_min.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_min.setToolTip("Minimizar")
        btn_min.clicked.connect(self._window.showMinimized)
        layout.addWidget(btn_min)

        self.btn_max = QPushButton()
        self.btn_max.setObjectName("WinBtn")
        self.btn_max.setIcon(icons.icon("win_max", 12, "#E6D6CA"))
        self.btn_max.setIconSize(QSize(12, 12))
        self.btn_max.setFixedSize(32, 24)
        self.btn_max.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_max.setToolTip("Maximizar / Restaurar")
        self.btn_max.clicked.connect(self._toggle_max)
        layout.addWidget(self.btn_max)

        btn_close = QPushButton()
        btn_close.setObjectName("WinCloseBtn")
        btn_close.setIcon(icons.icon("win_close", 12, "#F6EFE9"))
        btn_close.setIconSize(QSize(12, 12))
        btn_close.setFixedSize(32, 24)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setToolTip("Fechar")
        btn_close.clicked.connect(self._window.close)
        layout.addWidget(btn_close)

    def _sync_max_icon(self) -> None:
        ico = "win_restore" if self._window.isMaximized() else "win_max"
        self.btn_max.setIcon(self._icons.icon(ico, 12, "#E6D6CA"))

    def _toggle_max(self) -> None:
        if self._window.isMaximized():
            self._window.showNormal()
        else:
            self._window.showMaximized()
        self._sync_max_icon()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_max()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            if self._window.isMaximized():
                self._window.showNormal()
                self._sync_max_icon()
                self._drag_pos = QPoint(self._window.width() // 2, 18)
            self._window.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, _event: QMouseEvent) -> None:
        self._drag_pos = None


class CoffeeRootFrame(QFrame):
    """Fundo atmosférico contínuo em camadas (brilhos âmbar + ondas sedosas de café)."""

    def paintEvent(self, _event: Any) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        clip_path = QPainterPath()
        clip_path.addRoundedRect(0.5, 0.5, w - 1.0, h - 1.0, 12.0, 12.0)
        p.setClipPath(clip_path)

        # 1. Base espresso profunda
        base_grad = QLinearGradient(0, 0, w, h)
        base_grad.setColorAt(0.0, QColor("#180D08"))
        base_grad.setColorAt(0.5, QColor("#100805"))
        base_grad.setColorAt(1.0, QColor("#1B0E08"))
        p.fillRect(self.rect(), base_grad)

        # 2. Brilhos radiais quentes (halo atrás da xícara + calor ambiente)
        mug_glow = QRadialGradient(104, 122, 210)
        mug_glow.setColorAt(0.0, QColor(224, 126, 56, 68))
        mug_glow.setColorAt(0.45, QColor(148, 66, 26, 28))
        mug_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.fillRect(self.rect(), mug_glow)

        right_glow = QRadialGradient(w * 0.80, h * 0.38, 420)
        right_glow.setColorAt(0.0, QColor(196, 94, 38, 36))
        right_glow.setColorAt(0.6, QColor(110, 48, 18, 14))
        right_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.fillRect(self.rect(), right_glow)

        corner_glow = QRadialGradient(75, h - 45, 360)
        corner_glow.setColorAt(0.0, QColor(228, 120, 50, 82))
        corner_glow.setColorAt(0.55, QColor(125, 54, 20, 30))
        corner_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.fillRect(self.rect(), corner_glow)

        # 3. Ondas sedosas contínuas no canto inferior esquerdo (sem corte da barra lateral)
        w1 = QPainterPath()
        w1.moveTo(0, h - 155)
        w1.cubicTo(w * 0.14, h - 188, w * 0.28, h - 78, w * 0.56, h)
        w1.lineTo(0, h)
        w1.closeSubpath()
        g1 = QLinearGradient(0, h - 170, w * 0.45, h)
        g1.setColorAt(0.0, QColor(156, 74, 30, 92))
        g1.setColorAt(1.0, QColor(52, 22, 10, 20))
        p.fillPath(w1, g1)

        w2 = QPainterPath()
        w2.moveTo(0, h - 98)
        w2.cubicTo(w * 0.13, h - 146, w * 0.25, h - 52, w * 0.44, h)
        w2.lineTo(0, h)
        w2.closeSubpath()
        g2 = QLinearGradient(0, h - 125, w * 0.36, h)
        g2.setColorAt(0.0, QColor(218, 118, 52, 78))
        g2.setColorAt(1.0, QColor(96, 42, 16, 18))
        p.fillPath(w2, g2)

        # Borda luminosa da onda 2
        rim2 = QPainterPath()
        rim2.moveTo(0, h - 98)
        rim2.cubicTo(w * 0.13, h - 146, w * 0.25, h - 52, w * 0.44, h)
        p.strokePath(rim2, QPen(QColor(246, 174, 110, 125), 1.6))

        w3 = QPainterPath()
        w3.moveTo(0, h - 46)
        w3.cubicTo(w * 0.11, h - 92, w * 0.21, h - 28, w * 0.34, h)
        w3.lineTo(0, h)
        w3.closeSubpath()
        g3 = QLinearGradient(0, h - 80, w * 0.28, h)
        g3.setColorAt(0.0, QColor(242, 152, 82, 65))
        g3.setColorAt(1.0, QColor(120, 56, 22, 14))
        p.fillPath(w3, g3)

        rim3 = QPainterPath()
        rim3.moveTo(0, h - 46)
        rim3.cubicTo(w * 0.11, h - 92, w * 0.21, h - 28, w * 0.34, h)
        p.strokePath(rim3, QPen(QColor(255, 206, 154, 95), 1.2))

        # 4. Borda externa nítida da janela
        p.setClipping(False)
        p.setPen(QPen(QColor(96, 62, 42, 220), 1.0))
        p.drawRoundedRect(0.5, 0.5, w - 1.0, h - 1.0, 12.0, 12.0)
        p.end()
