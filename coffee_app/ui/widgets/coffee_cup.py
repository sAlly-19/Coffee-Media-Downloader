"""Widget animado da xícara de café com vapor contínuo, halo pulsante e destaque no hover."""

from __future__ import annotations

import math
from typing import Any

from PySide6.QtCore import QByteArray, QEasingCurve, QPointF, QRectF, Qt, QTimer, QVariantAnimation
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QWidget

from coffee_app.core.media_assets import COFFEE_CUP_BASE_SVG


class AnimatedCoffeeCupWidget(QWidget):
    """Xícara vetorial com vapor animado contínuo, brilho pulsante ativo e destaque ao passar o mouse."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(116, 94)
        self.setMouseTracking(True)
        self._renderer = QSvgRenderer(QByteArray(COFFEE_CUP_BASE_SVG.encode("utf-8")))
        self._phase = 0.0
        self._active_downloading = False
        self._hover_t = 0.0

        self._hover_anim = QVariantAnimation(self)
        self._hover_anim.setDuration(180)
        self._hover_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._hover_anim.valueChanged.connect(self._on_hover_value)

        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _on_hover_value(self, value: float) -> None:
        self._hover_t = float(value)
        self.update()

    def _tick(self) -> None:
        step = 0.048 if self._active_downloading else 0.028
        self._phase = (self._phase + step) % (math.tau * 100.0)
        self.update()

    def setActiveDownloading(self, active: bool) -> None:
        if self._active_downloading != active:
            self._active_downloading = active
            self.update()

    def stop_animation(self) -> None:
        if self._timer.isActive():
            self._timer.stop()

    def showEvent(self, event: Any) -> None:
        if not self._timer.isActive():
            self._timer.start()
        super().showEvent(event)

    def hideEvent(self, event: Any) -> None:
        if self._timer.isActive():
            self._timer.stop()
        super().hideEvent(event)

    def enterEvent(self, event: Any) -> None:
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_t)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event: Any) -> None:
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_t)
        self._hover_anim.setEndValue(0.0)
        self._hover_anim.start()
        super().leaveEvent(event)

    def paintEvent(self, _event: Any) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        svg_size = 92.0
        ox = (self.width() - svg_size) / 2.0
        oy = 2.0
        s = svg_size / 128.0

        # Aura radial atrás da xícara (pulsa em âmbar quando há downloads ativos)
        aura_cx = ox + 62.0 * s
        aura_cy = oy + 70.0 * s
        pulse = 0.5 + 0.5 * math.sin(self._phase * 1.9) if self._active_downloading else 0.0
        aura_r = (56.0 + (8.0 * pulse if self._active_downloading else 3.0 * self._hover_t)) * s
        aura_alpha = int((62 + 68 * pulse) if self._active_downloading else (42 + 30 * self._hover_t))
        aura = QRadialGradient(aura_cx, aura_cy, aura_r)
        aura.setColorAt(0.0, QColor(232, 134, 62, aura_alpha))
        aura.setColorAt(0.6, QColor(217, 119, 54, int(aura_alpha * 0.45)))
        aura.setColorAt(1.0, QColor(217, 119, 54, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(aura)
        p.drawEllipse(QPointF(aura_cx, aura_cy), aura_r, aura_r)

        # Desenha a xícara base SVG
        self._renderer.render(p, QRectF(ox, oy, svg_size, svg_size))

        # Destaque sutil no emblema Play ao passar o mouse ou baixar ativamente
        if self._hover_t > 0.01 or self._active_downloading:
            play_cx = ox + 62.0 * s
            play_cy = oy + 77.0 * s
            ring_alpha = int(190 * max(self._hover_t, 0.35 * pulse if self._active_downloading else 0.0))
            ring_r = (15.2 + 1.6 * self._hover_t) * s
            halo = QRadialGradient(play_cx, play_cy, ring_r + 6.0 * s)
            halo.setColorAt(0.45, QColor(255, 198, 138, int(ring_alpha * 0.35)))
            halo.setColorAt(1.0, QColor(255, 176, 98, 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(halo)
            p.drawEllipse(QPointF(play_cx, play_cy), ring_r + 6.0 * s, ring_r + 6.0 * s)

            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor(255, 208, 162, ring_alpha), 1.6))
            p.drawEllipse(QPointF(play_cx, play_cy), ring_r, ring_r)

        # Três trilhas contínuas de vapor subindo e ondulando acima da xícara
        streams = (
            (46.0, 42.0, 0.0, 27.0, 3.0),
            (62.0, 40.0, 2.09, 32.0, 3.8),
            (78.0, 42.0, 4.18, 26.0, 3.0),
        )
        speed_boost = 1.25 if self._active_downloading else 0.85
        for base_x, base_y, phase_off, height_span, amp in streams:
            for layer in (0.0, 0.5):
                u = (self._phase * 0.14 * speed_boost + phase_off / math.tau + layer) % 1.0
                fade = math.sin(math.pi * u) ** 0.85
                if fade <= 0.02:
                    continue

                y_bot = oy + (base_y - u * (height_span * 0.55)) * s
                seg_h = (13.0 + 5.0 * u) * s
                y_top = max(2.0, y_bot - seg_h)
                sway1 = amp * math.sin(u * math.tau + phase_off) * s
                sway2 = -amp * 0.85 * math.cos(u * math.tau * 1.1 + phase_off) * s
                cx_bot = ox + base_x * s + sway1 * 0.35
                cx_top = ox + base_x * s + sway2

                w_mid = (2.1 - 0.8 * u) * s
                path = QPainterPath()
                path.moveTo(cx_bot, y_bot)
                path.cubicTo(
                    cx_bot + sway1 - w_mid,
                    (y_bot + y_top) * 0.5 + seg_h * 0.12,
                    cx_top - sway2 * 0.4,
                    y_top + seg_h * 0.25,
                    cx_top,
                    y_top,
                )
                path.cubicTo(
                    cx_top - sway2 * 0.4 + w_mid * 0.65,
                    y_top + seg_h * 0.25,
                    cx_bot + sway1 + w_mid,
                    (y_bot + y_top) * 0.5 + seg_h * 0.12,
                    cx_bot + w_mid * 0.35,
                    y_bot,
                )
                path.closeSubpath()

                alpha_mul = (1.05 if self._active_downloading else 0.85) * fade
                steam_grad = QLinearGradient(cx_bot, y_bot, cx_top, y_top)
                steam_grad.setColorAt(0.0, QColor(235, 152, 88, min(255, int(195 * alpha_mul))))
                steam_grad.setColorAt(0.6, QColor(247, 206, 166, min(255, int(155 * alpha_mul))))
                steam_grad.setColorAt(1.0, QColor(255, 243, 230, 0))
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(steam_grad)
                p.drawPath(path)

        p.end()
