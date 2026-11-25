"""Janela principal orquestradora do CoffeeMediaDownloader Pro."""

from __future__ import annotations

import os
from typing import Any

from PIL import Image
from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QIcon, QMouseEvent, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QSystemTrayIcon,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from coffee_app.core.constants import APP_DISPLAY_NAME
from coffee_app.core.download_manager import DownloadManager
from coffee_app.core.media_assets import (
    create_placeholder_thumbnail,
    get_or_create_app_icon_ico,
    get_or_create_chevron_svg,
)
from coffee_app.core.models import DownloadTask
from coffee_app.core.storage import load_history, load_queue_state, load_settings, save_queue_state
from coffee_app.core.system_utils import extract_media_urls, format_speed
from coffee_app.ui.icons import SvgIconStore, _render_coffee_logo_pixmap
from coffee_app.ui.pages.downloads_page import DownloadsPageMixin
from coffee_app.ui.pages.history_page import HistoryPageMixin
from coffee_app.ui.pages.settings_page import SettingsAboutMixin
from coffee_app.ui.pages.sidebar import SidebarMixin
from coffee_app.ui.theme import FILTER_ALL, QSS_THEME, TOOLTIP_QSS, VISIBLE_BATCH_SIZE
from coffee_app.ui.widgets.cards import DownloadCardWidget
from coffee_app.ui.widgets.chrome import CoffeeRootFrame, TitleBar


class CoffeeMediaDownloaderApp(
    QMainWindow,
    SidebarMixin,
    DownloadsPageMixin,
    HistoryPageMixin,
    SettingsAboutMixin,
):
    """Janela principal do CoffeeMediaDownloader Pro em PySide6."""

    task_updated_signal = Signal(object)
    inspect_finished_signal = Signal(object, str, str, str)
    thumb_fetched_signal = Signal(str, object)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_DISPLAY_NAME)
        self.resize(1040, 720)
        self.setMinimumSize(860, 620)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)

        ico_path = get_or_create_app_icon_ico()
        if ico_path and os.path.isfile(ico_path):
            self.setWindowIcon(QIcon(ico_path))

        self.settings: dict[str, Any] = load_settings()
        self.history: list[dict[str, Any]] = load_history()
        self.icons = SvgIconStore()

        self._closing = False
        self._force_quit = False
        self._had_active_queue = False
        self._active_filter = FILTER_ALL
        self._queue_search = ""
        self._history_filter = "Todos"
        self._history_search = ""
        self._render_limit = VISIBLE_BATCH_SIZE
        self._last_clipboard_text = ""
        self._inspecting_urls: set[str] = set()
        self._last_progress_ui_ts: dict[str, float] = {}
        self._recorded_history_ids: set[str] = set()
        self._saved_queue_items: list[dict[str, Any]] = load_queue_state()

        self._tasks: dict[str, DownloadTask] = {}
        self._task_order: list[str] = []
        self._last_known_statuses: dict[str, str] = {}
        self._cards: dict[str, DownloadCardWidget] = {}
        self._thumb_cache: dict[str, Image.Image] = {}
        self._thumb_fetching: set[str] = set()
        self._load_more_btn: QPushButton | None = None

        self._placeholder_video_pil = create_placeholder_thumbnail((128, 72), is_audio=False)
        self._placeholder_audio_pil = create_placeholder_thumbnail((128, 72), is_audio=True)
        self._logo_pixmap = _render_coffee_logo_pixmap(82)

        self.manager = DownloadManager(
            max_concurrent=int(self.settings.get("max_concurrent", 3)),
            speed_limit_label=str(self.settings.get("speed_limit", "Ilimitado")),
            on_task_update=self._emit_task_update,
        )
        self.manager.set_cookies_browser(str(self.settings.get("cookies_browser", "Nenhum")))
        self.manager.set_cookies_file(str(self.settings.get("cookies_file", "")))

        self.task_updated_signal.connect(self._apply_task_update_ui)
        self.inspect_finished_signal.connect(self._handle_inspect_result)
        self.thumb_fetched_signal.connect(self._apply_cached_thumbnail)

        self._build_ui()
        self._setup_tray()
        self._setup_shortcuts()
        chevron_path = get_or_create_chevron_svg() or ""
        self.setStyleSheet(QSS_THEME.replace("__CHEVRON_SVG__", chevron_path) + "\n" + TOOLTIP_QSS)
        tip_palette = QToolTip.palette()
        tip_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#2B1A12"))
        tip_palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#FFF8F2"))
        QToolTip.setPalette(tip_palette)
        qapp = QApplication.instance()
        if isinstance(qapp, QApplication):
            qapp.setStyleSheet(TOOLTIP_QSS)
        self._select_nav("Downloads")

        self._clipboard_timer = QTimer(self)
        self._clipboard_timer.timeout.connect(self._poll_clipboard)
        self._clipboard_timer.start(1500)

        self._footer_timer = QTimer(self)
        self._footer_timer.timeout.connect(self._refresh_footer_stats)
        self._footer_timer.start(350)

    def _add_soft_glow(self, widget: QWidget, color: str = "#D47534", blur: int = 18) -> None:
        effect = QGraphicsDropShadowEffect(widget)
        effect.setBlurRadius(blur)
        effect.setOffset(0, 2)
        c = QColor(color)
        c.setAlpha(75)
        effect.setColor(c)
        widget.setGraphicsEffect(effect)

    def _build_ui(self) -> None:
        root_frame = CoffeeRootFrame()
        root_frame.setObjectName("RootFrame")
        root_frame.setMouseTracking(True)
        self.setCentralWidget(root_frame)

        outer = QVBoxLayout(root_frame)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.title_bar = TitleBar(self, self._logo_pixmap, self.icons)
        outer.addWidget(self.title_bar)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self.sidebar = self._build_sidebar()
        body.addWidget(self.sidebar)

        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.setContentsMargins(14, 12, 14, 8)
        self.downloads_page = self._build_downloads_page()
        self.history_page = self._build_history_page()
        self.settings_page = self._build_settings_page()
        self.about_page = self._build_about_page()

        self.pages = {
            "Downloads": self.downloads_page,
            "Histórico": self.history_page,
            "Configurações": self.settings_page,
            "Sobre": self.about_page,
        }
        for page in self.pages.values():
            self.stack.addWidget(page)

        right_col.addWidget(self.stack, 1)
        right_col.addWidget(self._build_status_bar())
        body.addLayout(right_col, 1)

        outer.addLayout(body, 1)

    def _select_nav(self, name: str) -> None:
        self.stack.setCurrentWidget(self.pages[name])
        for key, btn in self.nav_buttons.items():
            btn.setActive(key == name)
        if name == "Downloads":
            self._relayout_cards()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        mime = event.mimeData()
        if mime.hasUrls() or mime.hasText():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        mime = event.mimeData()
        collected: list[str] = []
        if mime.hasUrls():
            for qurl in mime.urls():
                if qurl.isLocalFile():
                    local = qurl.toLocalFile()
                    if local.lower().endswith(".txt") and os.path.isfile(local):
                        try:
                            with open(local, "r", encoding="utf-8", errors="ignore") as fh:
                                collected.extend(extract_media_urls(fh.read()))
                        except OSError:
                            pass
                else:
                    collected.extend(extract_media_urls(qurl.toString()))
        if mime.hasText():
            collected.extend(extract_media_urls(mime.text()))

        unique_urls = list(dict.fromkeys(collected))
        if not unique_urls:
            return
        self._select_nav("Downloads")
        if len(unique_urls) == 1:
            self.url_input.setText(unique_urls[0])
            self._flash_url_box("accent")
            self._on_add_clicked()
        else:
            fmt_label = self.format_combo.currentText()
            quality_label = self.quality_combo.currentText()
            output_dir = str(self.settings["output_dir"])
            tasks = [
                self._create_task(u, fmt_label, quality_label, output_dir)
                for u in unique_urls
            ]
            self._enqueue_batch(tasks)
            self.footer_state_lbl.setText(f"{len(tasks)} links importados por arraste.")
            self._sync_footer_state_text(keep_custom=True)

    def _detect_resize_edges(self, pos: QPoint) -> Qt.Edge:
        if self.isMaximized():
            return Qt.Edge(0)
        margin = 6
        edges = Qt.Edge(0)
        if pos.x() <= margin:
            edges |= Qt.Edge.LeftEdge
        elif pos.x() >= self.width() - margin:
            edges |= Qt.Edge.RightEdge
        if pos.y() <= margin:
            edges |= Qt.Edge.TopEdge
        elif pos.y() >= self.height() - margin:
            edges |= Qt.Edge.BottomEdge
        return edges

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        edges = self._detect_resize_edges(event.position().toPoint())
        if edges in (Qt.Edge.LeftEdge | Qt.Edge.TopEdge, Qt.Edge.RightEdge | Qt.Edge.BottomEdge):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif edges in (Qt.Edge.RightEdge | Qt.Edge.TopEdge, Qt.Edge.LeftEdge | Qt.Edge.BottomEdge):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif edges & (Qt.Edge.LeftEdge | Qt.Edge.RightEdge):
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif edges & (Qt.Edge.TopEdge | Qt.Edge.BottomEdge):
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:
            self.unsetCursor()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            edges = self._detect_resize_edges(event.position().toPoint())
            if edges and self.windowHandle() is not None:
                self.windowHandle().startSystemResize(edges)
                return
        super().mousePressEvent(event)

    def _persist_pending_queue(self) -> None:
        pending_payload = [
            {
                "url": t.url,
                "fmt_label": t.fmt_label,
                "quality_label": t.quality_label,
                "output_dir": t.output_dir,
                "title": t.title,
                "duration_seconds": t.duration_seconds,
                "thumbnail_url": t.thumbnail_url,
                "skip_existing": t.skip_existing,
                "filename_prefix": t.filename_prefix,
            }
            for tid in self._task_order
            if (t := self._tasks.get(tid)) is not None
            and t.status in ("queued", "extracting", "downloading", "converting")
        ]
        save_queue_state(pending_payload)

    def _refresh_footer_stats(self) -> None:
        if self._closing:
            return

        status_drift = False
        for tid, task in list(self._tasks.items()):
            if self._last_known_statuses.get(tid) != task.status:
                self._last_known_statuses[tid] = task.status
                status_drift = True
                if task.status in ("completed", "error") and tid not in self._recorded_history_ids:
                    self._recorded_history_ids.add(tid)
                    self._record_history(task)

        if status_drift:
            self._relayout_cards()
        else:
            for card in list(self._cards.values()):
                if card.task.status in ("extracting", "downloading", "converting"):
                    live_task = self._tasks.get(card.task.task_id)
                    if live_task is not None:
                        card.refresh(live_task.snapshot())

        active_ui = sum(
            1 for t in self._tasks.values() if t.status in ("extracting", "downloading", "converting")
        )
        active = max(self.manager.active_count, active_ui)
        self.footer_active_lbl.setText(
            f"Downloads ativos: {active}/{self.manager.max_concurrent}"
        )
        self.footer_speed_lbl.setText(f"Velocidade total: {format_speed(self.manager.total_speed_bps)}")
        if not self._inspecting_urls:
            self._sync_footer_state_text(keep_custom=False)

    def closeEvent(self, event: Any) -> None:
        if (
            not self._force_quit
            and bool(self.settings.get("minimize_to_tray", False))
            and hasattr(self, "tray_icon")
            and self.tray_icon.isVisible()
        ):
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                APP_DISPLAY_NAME,
                "Aplicativo minimizado para a bandeja do Windows.",
                QSystemTrayIcon.MessageIcon.Information,
                2500,
            )
            return

        self._closing = True
        self._clipboard_timer.stop()
        self._footer_timer.stop()
        if hasattr(self, "coffee_cup"):
            self.coffee_cup.stop_animation()
        self._save_settings_from_ui()
        self._persist_pending_queue()
        self.manager.shutdown()
        if hasattr(self, "tray_icon"):
            self.tray_icon.hide()
        super().closeEvent(event)
