"""Conversores de imagem, cache de ícones SVG e utilitários de pintura Qt."""

from __future__ import annotations

from PIL import Image
from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from coffee_app.core.media_assets import COFFEE_LOGO_SVG
from coffee_app.ui.theme import _SVG_ICONS


def _render_coffee_logo_pixmap(size: int = 78) -> QPixmap:
    renderer = QSvgRenderer(QByteArray(COFFEE_LOGO_SVG.encode("utf-8")))
    scale = 2
    pix = QPixmap(size * scale, size * scale)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    pix.setDevicePixelRatio(scale)
    return pix


def _pil_to_qpixmap(img: Image.Image) -> QPixmap:
    rgba = img.convert("RGBA")
    data = rgba.tobytes("raw", "RGBA")
    qimg = QImage(data, rgba.width, rgba.height, rgba.width * 4, QImage.Format.Format_RGBA8888).copy()
    return QPixmap.fromImage(qimg)


def _elide_text(text: str, font: QFont, max_width: int) -> str:
    metrics = QFontMetrics(font)
    return metrics.elidedText(text, Qt.TextElideMode.ElideRight, max_width)


def _lerp_color(c1: QColor, c2: QColor, t: float) -> QColor:
    return QColor(
        int(c1.red() + (c2.red() - c1.red()) * t),
        int(c1.green() + (c2.green() - c1.green()) * t),
        int(c1.blue() + (c2.blue() - c1.blue()) * t),
        int(c1.alpha() + (c2.alpha() - c1.alpha()) * t),
    )


class SvgIconStore:
    """Renderiza e faz cache de ícones SVG vetoriais nítidos."""

    def __init__(self) -> None:
        self._cache: dict[tuple[str, int, str], QIcon] = {}
        self._pix_cache: dict[tuple[str, int, str], QPixmap] = {}

    def pixmap(self, name: str, size: int = 16, color: str = "#F6EFE9") -> QPixmap:
        key = (name, size, color)
        if key not in self._pix_cache:
            body = _SVG_ICONS.get(name, _SVG_ICONS["info"])
            svg = (
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
                f'fill="none" stroke="{color}" stroke-width="2" '
                f'stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
            )
            renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
            scale = 2
            pix = QPixmap(size * scale, size * scale)
            pix.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pix)
            renderer.render(painter)
            painter.end()
            pix.setDevicePixelRatio(scale)
            self._pix_cache[key] = pix
        return self._pix_cache[key]

    def icon(self, name: str, size: int = 16, color: str = "#F6EFE9") -> QIcon:
        key = (name, size, color)
        if key not in self._cache:
            self._cache[key] = QIcon(self.pixmap(name, size=size, color=color))
        return self._cache[key]
