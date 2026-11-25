"""Constantes visuais, ícones SVG embutidos e folhas de estilo QSS do tema café escuro."""

from __future__ import annotations

FILTER_ALL = "Todos"
FILTER_DOWNLOADING = "Baixando"
FILTER_QUEUED = "Na Fila"
FILTER_COMPLETED = "Concluídos"
VISIBLE_BATCH_SIZE = 40

_SVG_ICONS: dict[str, str] = {
    "link": '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
    "paste": '<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>',
    "trash": '<path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
    "download": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>',
    "history": '<circle cx="12" cy="12" r="9"/><polyline points="12 7 12 12 15 14"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9c.26.6.85 1 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>',
    "info": '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>',
    "folder": '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>',
    "stack": '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
    "speed": '<path d="M12 14l4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/>',
    "cancel": '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
    "check": '<polyline points="20 6 9 17 4 12"/>',
    "video": '<rect x="2" y="6" width="14" height="12" rx="2"/><polygon points="22 8 16 12 22 16 22 8"/>',
    "audio": '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>',
    "refresh": '<polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>',
    "grid": '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    "dots": '<circle cx="12" cy="5" r="1.5" fill="currentColor"/><circle cx="12" cy="12" r="1.5" fill="currentColor"/><circle cx="12" cy="19" r="1.5" fill="currentColor"/>',
    "queue": '<line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><circle cx="4" cy="6" r="1"/><circle cx="4" cy="12" r="1"/><circle cx="4" cy="18" r="1"/>',
    "search": '<circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
    "play": '<polygon points="6 4 20 12 6 20 6 4"/>',
    "plus_circle": '<circle cx="12" cy="12" r="9"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>',
    "win_min": '<line x1="6" y1="12" x2="18" y2="12"/>',
    "win_max": '<rect x="6.5" y="6.5" width="11" height="11" rx="2"/>',
    "win_restore": '<rect x="8.5" y="5.5" width="10" height="10" rx="1.8"/><path d="M5.5 9.5v7.5a2 2 0 0 0 2 2h7.5"/>',
    "win_close": '<line x1="7" y1="7" x2="17" y2="17"/><line x1="17" y1="7" x2="7" y2="17"/>',
    "alert": '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
}

QSS_THEME = """
* {
    font-family: "Segoe UI", "Inter", sans-serif;
    color: #F6EFE9;
}

QFrame#RootFrame {
    background: transparent;
    border-radius: 12px;
}

QFrame#TitleBar {
    background: rgba(16, 9, 6, 155);
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    border-bottom: 1px solid rgba(96, 62, 42, 115);
}

QPushButton#WinBtn, QPushButton#WinCloseBtn {
    background: rgba(255, 248, 242, 10);
    border: 1px solid rgba(96, 62, 42, 95);
    border-radius: 7px;
}
QPushButton#WinBtn:hover {
    background: rgba(217, 119, 54, 70);
    border-color: rgba(235, 184, 122, 145);
}
QPushButton#WinCloseBtn:hover {
    background: rgba(205, 58, 46, 215);
    border-color: #F87171;
}

QFrame#Sidebar {
    background: rgba(22, 13, 8, 90);
    border-right: 1px solid rgba(96, 62, 42, 85);
    border-bottom-left-radius: 12px;
}

QLabel#ProPill {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E0823E, stop:1 #B85B24);
    border: 1px solid #F2A468;
    border-radius: 6px;
    color: #FFF8F2;
    font-size: 11px;
    font-weight: 700;
    padding: 2px 10px;
}

QFrame#GlassPanel {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(46, 28, 18, 172), stop:1 rgba(24, 15, 10, 190));
    border: 1px solid rgba(105, 68, 45, 145);
    border-top: 1px solid rgba(164, 110, 74, 125);
    border-radius: 12px;
}

QFrame#UrlBox {
    background: rgba(34, 21, 14, 210);
    border: 1px solid rgba(92, 60, 41, 185);
    border-radius: 8px;
}
QFrame#UrlBox[flash="accent"] {
    border: 2px solid #E88B4B;
}
QFrame#UrlBox[flash="error"] {
    border: 2px solid #F87171;
}

QLineEdit#UrlInput {
    background: transparent;
    border: none;
    color: #F6EFE9;
    font-size: 13px;
    selection-background-color: #D47534;
}

QPushButton#SecondaryBtn {
    background: #332117;
    border: 1px solid #523728;
    border-radius: 8px;
    color: #F6EFE9;
    font-size: 12px;
    font-weight: 600;
    padding: 0 12px;
}
QPushButton#SecondaryBtn:hover {
    background: #422B1E;
    border-color: #6B4834;
}

QPushButton#DangerBtn {
    background: #4A231B;
    border: 1px solid #753428;
    border-radius: 7px;
    color: #FFD7D0;
    font-size: 11px;
    font-weight: 700;
    padding: 0 10px;
}
QPushButton#DangerBtn:hover {
    background: #6B2F23;
}

QListWidget#PlaylistList {
    background: #1B110C;
    border: 1px solid #4A3022;
    border-radius: 8px;
    padding: 4px;
    outline: 0;
}
QListWidget#PlaylistList::item {
    padding: 5px 8px;
    border-radius: 6px;
    color: #F6EFE9;
}
QListWidget#PlaylistList::item:hover {
    background: #2C1D15;
}
QListWidget#PlaylistList::indicator {
    width: 15px;
    height: 15px;
    border-radius: 4px;
    border: 1px solid #7A5036;
    background: #2B1C14;
}
QListWidget#PlaylistList::indicator:checked {
    background: #D97736;
    border-color: #F2A468;
}

QComboBox {
    background: #2B1C14;
    border: 1px solid #4E3324;
    border-radius: 8px;
    padding: 4px 10px;
    color: #F6EFE9;
    font-size: 12px;
    min-height: 24px;
}
QComboBox:hover {
    border-color: #6B4834;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: url("__CHEVRON_SVG__");
    width: 12px;
    height: 12px;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background: #241711;
    border: 1px solid #523728;
    selection-background-color: #D47534;
    selection-color: #FFF8F2;
    outline: 0;
}

QFrame#DownloadCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(52, 32, 21, 182), stop:1 rgba(32, 20, 14, 194));
    border: 1px solid rgba(98, 63, 42, 155);
    border-top: 1px solid rgba(154, 102, 68, 115);
    border-radius: 11px;
}
QFrame#DownloadCard:hover {
    border-color: rgba(168, 108, 70, 220);
}

QLabel#BadgeFormat {
    background: #4B2A16;
    border: 1px solid #784526;
    border-radius: 5px;
    color: #F3BC7D;
    font-size: 11px;
    font-weight: 700;
    padding: 1px 7px;
}
QLabel#BadgeMeta {
    background: #362319;
    border: 1px solid #4A3022;
    border-radius: 5px;
    color: #C4AE9E;
    font-size: 11px;
    padding: 1px 7px;
}

QProgressBar {
    background: #1A100B;
    border: 1px solid #3A261B;
    border-radius: 3px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #C96628, stop:1 #F4B272);
    border-radius: 3px;
}
QProgressBar[state="converting"]::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #D97706, stop:1 #FBBF24);
}
QProgressBar[state="completed"]::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #D49A45, stop:1 #F5D08A);
}
QProgressBar[state="error"]::chunk {
    background: #F87171;
}

QPushButton#CardActionBtn {
    background: #342218;
    border: 1px solid #523728;
    border-radius: 7px;
    color: #F6EFE9;
    font-size: 12px;
    font-weight: 600;
    padding: 0 10px;
}
QPushButton#CardActionBtn:hover {
    background: #462D20;
    border-color: #704933;
}
QPushButton#CardActionBtn[accent="true"] {
    background: #4B2A16;
    border-color: #D47534;
    color: #FFF8F2;
}
QPushButton#CardActionBtn[accent="true"]:hover {
    background: #D47534;
}

QPushButton#MenuDotsBtn {
    background: transparent;
    border: none;
    border-radius: 6px;
}
QPushButton#MenuDotsBtn:hover {
    background: #38251B;
}

QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {
    background: transparent;
    border: none;
}
QScrollBar:vertical {
    background: rgba(20, 12, 8, 120);
    width: 8px;
    margin: 2px 0;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #5A3A28;
    border-radius: 4px;
    min-height: 28px;
}
QScrollBar::handle:vertical:hover {
    background: #D47534;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}
QScrollBar:horizontal {
    height: 0px;
    background: transparent;
}

QFrame#DividerV {
    background: #3D281D;
    max-width: 1px;
    min-width: 1px;
}

QFrame#StatusBar {
    background: rgba(16, 9, 6, 175);
    border-top: 1px solid rgba(96, 62, 42, 115);
    border-bottom-right-radius: 12px;
}

QMenu {
    background: #241711;
    border: 1px solid #523728;
    border-radius: 8px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 16px;
    border-radius: 5px;
    color: #F6EFE9;
}
QMenu::item:selected {
    background: #D47534;
    color: #FFF8F2;
}
"""

TOOLTIP_QSS = """
QToolTip {
    background-color: #2B1A12;
    color: #FFF8F2;
    border: 1px solid #D47534;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}
"""
