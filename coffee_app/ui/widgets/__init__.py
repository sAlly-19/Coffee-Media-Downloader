"""Widgets customizados reutilizáveis do CoffeeMediaDownloader Pro."""

from coffee_app.ui.widgets.cards import DownloadCardWidget, HistoryCardWidget
from coffee_app.ui.widgets.chrome import CoffeeRootFrame, TitleBar
from coffee_app.ui.widgets.coffee_cup import AnimatedCoffeeCupWidget
from coffee_app.ui.widgets.controls import AnimatedGradientButton, ElidedLabel, ToggleSwitch
from coffee_app.ui.widgets.dialogs import HighConcurrencyWarningDialog, PlaylistConfirmDialog

__all__ = [
    "AnimatedCoffeeCupWidget",
    "AnimatedGradientButton",
    "CoffeeRootFrame",
    "DownloadCardWidget",
    "ElidedLabel",
    "HighConcurrencyWarningDialog",
    "HistoryCardWidget",
    "PlaylistConfirmDialog",
    "TitleBar",
    "ToggleSwitch",
]
