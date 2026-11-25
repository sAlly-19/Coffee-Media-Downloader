"""Controles visuais customizados (botão gradiente animado, toggle switch e label elidido)."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QEasingCurve, QPoint, QRectF, QSize, Qt, QVariantAnimation
from PySide6.QtGui import QColor, QFontMetrics, QLinearGradient, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QCheckBox, QLabel, QPushButton, QSizePolicy, QWidget

from coffee_app.ui.icons import _lerp_color


class AnimatedGradientButton(QPushButton):
    """Botão com transição suave de degradê e brilho no hover via QVariantAnimation."""

    def __init__(
        self,
        text: str = "",
        *,
        align_left: bool = False,
        radius: int = 8,
        active: bool = True,
        active_start: str = "#DF7F3B",
        active_end: str = "#BD5C22",
        hover_start: str = "#F59E59",
        hover_end: str = "#D97232",
        inactive_start: str = "#2E1E16",
        inactive_end: str = "#22150F",
        inactive_hover_start: str = "#472F22",
        inactive_hover_end: str = "#352218",
        border_active: str = "#F2A468",
        border_inactive: str = "#4A3022",
        transparent_idle: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        self._align_left = align_left
        self._radius = radius
        self._active = active
        self._transparent_idle = transparent_idle
        self._hover_t = 0.0
        self._pressed = False

        self._active_start = QColor(active_start)
        self._active_end = QColor(active_end)
        self._hover_start = QColor(hover_start)
        self._hover_end = QColor(hover_end)
        self._inactive_start = QColor(inactive_start)
        self._inactive_end = QColor(inactive_end)
        self._inactive_hover_start = QColor(inactive_hover_start)
        self._inactive_hover_end = QColor(inactive_hover_end)
        self._border_active = QColor(border_active)
        self._border_inactive = QColor(border_inactive)

        self._anim = QVariantAnimation(self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_anim_value)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _on_anim_value(self, value: float) -> None:
        self._hover_t = float(value)
        self.update()

    def setActive(self, active: bool) -> None:
        self._active = active
        self.update()

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(self.font())
        label = self.text().lstrip() if self._align_left else self.text()
        has_icon = not self.icon().isNull()
        ico_sz = self.iconSize().width() if has_icon else 0
        gap = 8 if (has_icon and label) else 0
        w = fm.horizontalAdvance(label) + ico_sz + gap + (26 if self._align_left else 22)
        h = max(28, super().sizeHint().height())
        return QSize(w, h)

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def enterEvent(self, event: Any) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._hover_t)
        self._anim.setEndValue(1.0)
        self._anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event: Any) -> None:
        self._pressed = False
        self._anim.stop()
        self._anim.setStartValue(self._hover_t)
        self._anim.setEndValue(0.0)
        self._anim.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, _event: Any) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(0.5, 0.5, self.width() - 1.0, self.height() - 1.0)
        t = self._hover_t

        if not self.isEnabled():
            c1 = QColor("#4A3022")
            c2 = QColor("#362218")
            border_c = QColor("#5E3F2E")
            text_c = QColor("#B8A394")
        elif self._active:
            c1 = _lerp_color(self._active_start, self._hover_start, t)
            c2 = _lerp_color(self._active_end, self._hover_end, t)
            if self._pressed:
                c1 = c1.darker(110)
                c2 = c2.darker(110)
            border_c = _lerp_color(self._border_active, QColor("#FFD0A6"), t * 0.7)
            text_c = QColor("#FFF8F2")
        else:
            base_s = QColor(0, 0, 0, 0) if self._transparent_idle else self._inactive_start
            base_e = QColor(0, 0, 0, 0) if self._transparent_idle else self._inactive_end
            c1 = _lerp_color(base_s, self._inactive_hover_start, t)
            c2 = _lerp_color(base_e, self._inactive_hover_end, t)
            b_idle = QColor(0, 0, 0, 0) if self._transparent_idle else self._border_inactive
            border_c = _lerp_color(b_idle, QColor("#8A5B3E"), t)
            text_c = _lerp_color(QColor("#C4AE9E"), QColor("#FFF8F2"), t)

        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0.0, c1)
        grad.setColorAt(1.0, c2)

        p.setBrush(grad)
        p.setPen(QPen(border_c, 1.0))
        p.drawRoundedRect(rect, self._radius, self._radius)

        if self.isEnabled() and (self._active or t > 0.05):
            sheen = QLinearGradient(0, 1, 0, self.height() * 0.5)
            alpha = int((34 if self._active else 14) * (0.6 + 0.4 * t))
            sheen.setColorAt(0.0, QColor(255, 248, 242, alpha))
            sheen.setColorAt(1.0, QColor(255, 248, 242, 0))
            p.setBrush(sheen)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(rect.adjusted(1, 1, -1, -rect.height() * 0.45), self._radius - 1, self._radius - 1)

        # Desenho de ícone e texto alinhados
        p.setFont(self.font())
        p.setPen(text_c)
        fm = QFontMetrics(self.font())
        label = self.text().lstrip() if self._align_left else self.text()
        has_icon = not self.icon().isNull()
        ico_sz = self.iconSize().width() if has_icon else 0
        gap = 8 if (has_icon and label) else 0
        text_w = fm.horizontalAdvance(label)
        content_w = ico_sz + gap + text_w

        if self._align_left:
            x = 13.0
        else:
            x = max(8.0, (self.width() - content_w) / 2.0)

        if has_icon:
            iy = int((self.height() - ico_sz) / 2)
            self.icon().paint(p, int(x), iy, ico_sz, ico_sz)
            x += ico_sz + gap

        if label:
            text_rect = QRectF(x, 0, self.width() - x - 8, self.height())
            p.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)

        p.end()


class ToggleSwitch(QCheckBox):
    """Switch estilo pill moderno desenhado via QPainter."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(44, 24)

    def hitButton(self, pos: QPoint) -> bool:
        return self.rect().contains(pos)

    def paintEvent(self, _event: Any) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)
        if self.isChecked():
            p.setBrush(QColor("#D97736"))
            p.setPen(QPen(QColor("#F2A468"), 1))
        else:
            p.setBrush(QColor("#332117"))
            p.setPen(QPen(QColor("#523728"), 1))
        p.drawRoundedRect(rect, 11, 11)

        thumb_d = 16
        x = rect.right() - thumb_d - 3 if self.isChecked() else rect.left() + 3
        y = (self.height() - thumb_d) // 2
        p.setBrush(QColor("#FFF8F2"))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(x, y, thumb_d, thumb_d)
        p.end()


class ElidedLabel(QLabel):
    """Label que trunca textos longos com reticências sem expandir a largura do layout."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self._full_text = text
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(0)

    def setText(self, text: str) -> None:  # type: ignore[override]
        self._full_text = text or ""
        self.setToolTip(self._full_text)
        self._apply_elide()

    def resizeEvent(self, event: Any) -> None:
        super().resizeEvent(event)
        self._apply_elide()

    def _apply_elide(self) -> None:
        avail = max(40, self.width())
        elided = QFontMetrics(self.font()).elidedText(
            self._full_text, Qt.TextElideMode.ElideRight, avail
        )
        super().setText(elided)
