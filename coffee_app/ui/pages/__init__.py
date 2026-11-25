"""Mixins das páginas e componentes de navegação do CoffeeMediaDownloader Pro."""

from coffee_app.ui.pages.downloads_page import DownloadsPageMixin
from coffee_app.ui.pages.history_page import HistoryPageMixin
from coffee_app.ui.pages.settings_page import SettingsAboutMixin
from coffee_app.ui.pages.sidebar import SidebarMixin

__all__ = [
    "DownloadsPageMixin",
    "HistoryPageMixin",
    "SettingsAboutMixin",
    "SidebarMixin",
]
