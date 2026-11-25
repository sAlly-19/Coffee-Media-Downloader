"""Fachada retrocompatível para a interface PySide6 em coffee_app.ui."""

from __future__ import annotations

from coffee_app.ui.icons import (
    SvgIconStore,
    _elide_text,
    _lerp_color,
    _pil_to_qpixmap,
    _render_coffee_logo_pixmap,
)
from coffee_app.ui.main_window import CoffeeMediaDownloaderApp
from coffee_app.ui.theme import (
    FILTER_ALL,
    FILTER_COMPLETED,
    FILTER_DOWNLOADING,
    FILTER_QUEUED,
    QSS_THEME,
    TOOLTIP_QSS,
    VISIBLE_BATCH_SIZE,
    _SVG_ICONS,
)
from coffee_app.ui.widgets import (
    AnimatedCoffeeCupWidget,
    AnimatedGradientButton,
    CoffeeRootFrame,
    DownloadCardWidget,
    ElidedLabel,
    HighConcurrencyWarningDialog,
    HistoryCardWidget,
    PlaylistConfirmDialog,
    TitleBar,
    ToggleSwitch,
)

__all__ = [
    "AnimatedCoffeeCupWidget",
    "AnimatedGradientButton",
    "CoffeeMediaDownloaderApp",
    "CoffeeRootFrame",
    "DownloadCardWidget",
    "ElidedLabel",
    "FILTER_ALL",
    "FILTER_COMPLETED",
    "FILTER_DOWNLOADING",
    "FILTER_QUEUED",
    "HighConcurrencyWarningDialog",
    "HistoryCardWidget",
    "PlaylistConfirmDialog",
    "QSS_THEME",
    "SvgIconStore",
    "TOOLTIP_QSS",
    "TitleBar",
    "ToggleSwitch",
    "VISIBLE_BATCH_SIZE",
    "_SVG_ICONS",
    "_elide_text",
    "_lerp_color",
    "_pil_to_qpixmap",
    "_render_coffee_logo_pixmap",
]
