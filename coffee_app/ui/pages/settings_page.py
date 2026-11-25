"""Páginas de Configurações e Sobre, controle da bandeja do sistema e atalhos."""

from __future__ import annotations

import os

import yt_dlp
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from coffee_app.core.constants import (
    APP_AUTHOR,
    APP_DISPLAY_NAME,
    APP_VERSION,
    AUDIO_FORMAT_LABEL,
    VIDEO_FORMAT_LABEL,
)
from coffee_app.core.storage import clear_download_archive, save_settings
from coffee_app.core.system_utils import find_ffmpeg, open_folder
from coffee_app.ui.icons import _elide_text
from coffee_app.ui.widgets.controls import ToggleSwitch
from coffee_app.ui.widgets.dialogs import HighConcurrencyWarningDialog


class SettingsAboutMixin:
    """Mixin das páginas de Configurações/Sobre, status pós-fila, bandeja e atalhos."""

    def _build_settings_page(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("GlassPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        hdr = QHBoxLayout()
        ico = QLabel()
        ico.setPixmap(self.icons.pixmap("settings", 18, "#EBB87A"))
        hdr.addWidget(ico)
        t = QLabel("Configurações Persistentes")
        t.setStyleSheet("font-size: 17px; font-weight: 700; color: #FFF8F2;")
        hdr.addWidget(t)
        hdr.addStretch()
        layout.addLayout(hdr)

        sub = QLabel("As preferências são salvas automaticamente em %APPDATA%\\CoffeeMediaDownloader.")
        sub.setStyleSheet("font-size: 12px; color: #C4AE9E;")
        layout.addWidget(sub)

        card = QFrame()
        card.setObjectName("DownloadCard")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(18, 16, 18, 16)
        c_layout.setSpacing(14)

        meta_row = QHBoxLayout()
        self.embed_meta_switch = ToggleSwitch()
        self.embed_meta_switch.setChecked(bool(self.settings.get("embed_metadata", True)))
        self.embed_meta_switch.toggled.connect(self._save_settings_from_ui)
        meta_row.addWidget(self.embed_meta_switch)
        m_lbl = QLabel("Incorporar metadados (título/artista) automaticamente ao converter MP3")
        m_lbl.setStyleSheet("font-size: 13px; color: #F6EFE9;")
        meta_row.addWidget(m_lbl, 1)
        c_layout.addLayout(meta_row)

        skip_row = QHBoxLayout()
        self.skip_existing_switch = ToggleSwitch()
        self.skip_existing_switch.setChecked(bool(self.settings.get("skip_existing", True)))
        self.skip_existing_switch.toggled.connect(self._save_settings_from_ui)
        skip_row.addWidget(self.skip_existing_switch)
        sk_lbl = QLabel("Ignorar músicas e vídeos já baixados (verifica pasta de destino e registro)")
        sk_lbl.setStyleSheet("font-size: 13px; color: #F6EFE9;")
        skip_row.addWidget(sk_lbl, 1)

        btn_reset_archive = QPushButton("Limpar Registro")
        btn_reset_archive.setObjectName("SecondaryBtn")
        btn_reset_archive.setFixedHeight(28)
        btn_reset_archive.setToolTip("Apaga a lista de IDs já baixados (mantém os arquivos na pasta).")
        btn_reset_archive.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset_archive.clicked.connect(self._clear_archive_registry)
        skip_row.addWidget(btn_reset_archive)
        c_layout.addLayout(skip_row)

        # Opções de playlist (subpasta e numeração) e bandeja
        pl_sub_row = QHBoxLayout()
        self.pl_subfolder_switch = ToggleSwitch()
        self.pl_subfolder_switch.setChecked(bool(self.settings.get("playlist_subfolder", False)))
        self.pl_subfolder_switch.toggled.connect(self._save_settings_from_ui)
        pl_sub_row.addWidget(self.pl_subfolder_switch)
        pl_sub_lbl = QLabel("Criar subpasta com o nome da playlist ao baixar playlists completas")
        pl_sub_lbl.setStyleSheet("font-size: 13px; color: #F6EFE9;")
        pl_sub_row.addWidget(pl_sub_lbl, 1)
        c_layout.addLayout(pl_sub_row)

        pl_num_row = QHBoxLayout()
        self.pl_numbering_switch = ToggleSwitch()
        self.pl_numbering_switch.setChecked(bool(self.settings.get("playlist_numbering", False)))
        self.pl_numbering_switch.toggled.connect(self._save_settings_from_ui)
        pl_num_row.addWidget(self.pl_numbering_switch)
        pl_num_lbl = QLabel("Numerar faixas da playlist (ex: 01 - Título)")
        pl_num_lbl.setStyleSheet("font-size: 13px; color: #F6EFE9;")
        pl_num_row.addWidget(pl_num_lbl, 1)
        c_layout.addLayout(pl_num_row)

        tray_row = QHBoxLayout()
        self.minimize_tray_switch = ToggleSwitch()
        self.minimize_tray_switch.setChecked(bool(self.settings.get("minimize_to_tray", False)))
        self.minimize_tray_switch.toggled.connect(self._save_settings_from_ui)
        tray_row.addWidget(self.minimize_tray_switch)
        tray_lbl = QLabel("Minimizar para a bandeja do Windows ao clicar em Fechar (×)")
        tray_lbl.setStyleSheet("font-size: 13px; color: #F6EFE9;")
        tray_row.addWidget(tray_lbl, 1)
        c_layout.addLayout(tray_row)

        # Seletores de Cookies e Ação Pós-Fila
        extra_combos = QHBoxLayout()
        extra_combos.setSpacing(14)

        ck_lbl = QLabel("Cookies do navegador:")
        ck_lbl.setStyleSheet("font-size: 12.5px; color: #C4AE9E;")
        extra_combos.addWidget(ck_lbl)
        self.cookies_combo = QComboBox()
        self.cookies_combo.addItems(["Nenhum", "Chrome", "Edge", "Firefox"])
        self.cookies_combo.setCurrentText(str(self.settings.get("cookies_browser", "Nenhum")))
        self.cookies_combo.setFixedWidth(130)
        self.cookies_combo.currentTextChanged.connect(self._on_cookies_changed)
        extra_combos.addWidget(self.cookies_combo)

        pq_lbl = QLabel("Ao concluir fila:")
        pq_lbl.setStyleSheet("font-size: 12.5px; color: #C4AE9E; margin-left: 8px;")
        extra_combos.addWidget(pq_lbl)
        self.post_queue_combo = QComboBox()
        self.post_queue_combo.addItems(["Notificar", "Abrir Pasta", "Nada"])
        self.post_queue_combo.setCurrentText(str(self.settings.get("post_queue_action", "Notificar")))
        self.post_queue_combo.setFixedWidth(140)
        self.post_queue_combo.currentTextChanged.connect(lambda _: self._save_settings_from_ui())
        extra_combos.addWidget(self.post_queue_combo)
        extra_combos.addStretch()
        c_layout.addLayout(extra_combos)

        ck_file_row = QHBoxLayout()
        ck_file_row.setSpacing(8)
        ck_file_lbl = QLabel("Arquivo cookies.txt:")
        ck_file_lbl.setStyleSheet("font-size: 12.5px; color: #C4AE9E;")
        ck_file_row.addWidget(ck_file_lbl)

        self.cookies_file_lbl = QLabel()
        self.cookies_file_lbl.setStyleSheet(
            "background: #2B1C14; border: 1px solid #4E3324; border-radius: 7px; "
            "padding: 4px 10px; color: #F6EFE9; font-size: 12px;"
        )
        self.cookies_file_lbl.setFixedHeight(28)
        self._update_cookies_file_label()
        ck_file_row.addWidget(self.cookies_file_lbl, 1)

        btn_pick_cookies = QPushButton(" Selecionar...")
        btn_pick_cookies.setIcon(self.icons.icon("folder", 13, "#F6EFE9"))
        btn_pick_cookies.setObjectName("SecondaryBtn")
        btn_pick_cookies.setFixedHeight(28)
        btn_pick_cookies.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_pick_cookies.clicked.connect(self._choose_cookies_file)
        ck_file_row.addWidget(btn_pick_cookies)

        btn_clear_cookies = QPushButton("Limpar")
        btn_clear_cookies.setObjectName("SecondaryBtn")
        btn_clear_cookies.setFixedHeight(28)
        btn_clear_cookies.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear_cookies.clicked.connect(self._clear_cookies_file)
        ck_file_row.addWidget(btn_clear_cookies)
        c_layout.addLayout(ck_file_row)

        ck_hint = QLabel(
            "Dica para vídeos +18: se Chrome/Edge falharem por bloqueio do Windows, use Firefox ou selecione um cookies.txt."
        )
        ck_hint.setWordWrap(True)
        ck_hint.setStyleSheet("font-size: 11.5px; color: #8E7565;")
        c_layout.addWidget(ck_hint)

        yt_ver = getattr(yt_dlp.version, "__version__", "desconhecida")
        ff_path = find_ffmpeg()
        ff_lbl = QLabel(
            f"yt-dlp v{yt_ver}   •   "
            + (
                f"FFmpeg detectado: {ff_path}"
                if ff_path
                else "FFmpeg NÃO encontrado. Coloque o ffmpeg.exe na pasta do app ou em bin\\ffmpeg.exe."
            )
        )
        ff_lbl.setWordWrap(True)
        ff_lbl.setStyleSheet(f"font-size: 12px; color: {'#6EE7B7' if ff_path else '#F87171'};")
        c_layout.addWidget(ff_lbl)

        layout.addWidget(card)
        layout.addStretch()
        return panel

    def _build_about_page(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("GlassPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(22, 22, 22, 22)

        card = QFrame()
        card.setObjectName("DownloadCard")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(22, 20, 22, 20)
        c_layout.setSpacing(10)

        t = QLabel(f"{APP_DISPLAY_NAME}  v{APP_VERSION}")
        t.setStyleSheet("font-size: 19px; font-weight: 700; color: #EBB87A;")
        c_layout.addWidget(t)

        body = QLabel(
            "Gerenciador desktop de downloads multimídia para Windows.\n\n"
            "• Stack: Python 3.11+, PySide6 (Qt 6 + QSS), yt-dlp (API Python), FFmpeg e ThreadPoolExecutor.\n"
            "• Recursos: downloads paralelos (1–10), playlists seletivas com extract_flat, MP3 rápido,\n"
            "  Áudio Original (M4A), MP4 até 4K, cookies de navegador, fila persistente e bandeja.\n\n"
            "Portabilidade do FFmpeg:\n"
            "Posicione ffmpeg.exe na raiz do projeto (ao lado de main.py / .exe) ou em bin\\ffmpeg.exe."
        )
        body.setStyleSheet("font-size: 13px; color: #C4AE9E; line-height: 1.4;")
        body.setWordWrap(True)
        c_layout.addWidget(body)
        c_layout.addStretch()

        sig_lbl = QLabel(f"Desenvolvido por  {APP_AUTHOR}")
        sig_lbl.setStyleSheet(
            "font-size: 12.5px; font-weight: 700; color: #EBB87A; "
            "border-top: 1px solid rgba(98, 63, 42, 130); padding-top: 12px;"
        )
        c_layout.addWidget(sig_lbl)

        layout.addWidget(card, 1)
        return panel

    def _update_output_dir_label(self) -> None:
        path = str(self.settings["output_dir"])
        self.output_dir_lbl.setText(_elide_text(path, self.output_dir_lbl.font(), 240))
        self.output_dir_lbl.setToolTip(path)

    def _choose_output_dir(self) -> None:
        chosen = QFileDialog.getExistingDirectory(
            self, "Selecionar Pasta de Destino", str(self.settings["output_dir"])
        )
        if chosen:
            self.settings["output_dir"] = os.path.normpath(chosen)
            self._update_output_dir_label()
            save_settings(self.settings)

    def _on_concurrent_changed(self, value: str) -> None:
        limit = int(value)
        if limit > 4 and not self.settings.get("high_concurrency_warned", False):
            dialog = HighConcurrencyWarningDialog(self, limit, self.icons)
            dialog.exec()
            if dialog.confirmed:
                self.settings["high_concurrency_warned"] = True
            else:
                self.concurrent_combo.blockSignals(True)
                self.concurrent_combo.setCurrentText("4")
                self.concurrent_combo.blockSignals(False)
                limit = 4

        self.high_load_badge.setVisible(limit > 4)
        self.manager.set_max_concurrent(limit)
        self._save_settings_from_ui()
        self._refresh_footer_stats()

    def _on_speed_changed(self, value: str) -> None:
        self.manager.set_speed_limit(value)
        self._save_settings_from_ui()

    def _on_cookies_changed(self, browser_name: str) -> None:
        self.manager.set_cookies_browser(browser_name)
        self._save_settings_from_ui()

    def _update_cookies_file_label(self) -> None:
        path = str(self.settings.get("cookies_file") or "").strip()
        if path:
            self.cookies_file_lbl.setText(_elide_text(path, self.cookies_file_lbl.font(), 240))
            self.cookies_file_lbl.setToolTip(path)
        else:
            self.cookies_file_lbl.setText("Nenhum selecionado (opcional)")
            self.cookies_file_lbl.setToolTip("Exporte via extensão 'Get cookies.txt LOCALLY' se precisar.")

    def _choose_cookies_file(self) -> None:
        start_dir = os.path.dirname(str(self.settings.get("cookies_file") or "")) or str(self.settings["output_dir"])
        chosen, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar arquivo cookies.txt",
            start_dir,
            "Arquivos de Cookies (*.txt);;Todos os arquivos (*.*)",
        )
        if chosen:
            norm = os.path.normpath(chosen)
            self.settings["cookies_file"] = norm
            self.manager.set_cookies_file(norm)
            self._update_cookies_file_label()
            save_settings(self.settings)
            self.footer_state_lbl.setText("Arquivo cookies.txt configurado.")

    def _clear_cookies_file(self) -> None:
        self.settings["cookies_file"] = ""
        self.manager.set_cookies_file("")
        self._update_cookies_file_label()
        save_settings(self.settings)
        self.footer_state_lbl.setText("Arquivo cookies.txt removido.")

    def _clear_archive_registry(self) -> None:
        clear_download_archive()
        self.footer_state_lbl.setText("Registro de itens já baixados foi limpo.")

    def _save_settings_from_ui(self) -> None:
        self.settings["auto_paste"] = self.auto_paste_switch.isChecked()
        self.settings["max_concurrent"] = int(self.concurrent_combo.currentText())
        self.settings["speed_limit"] = self.speed_combo.currentText()
        self.settings["default_format"] = self.format_combo.currentText()
        if self.format_combo.currentText() == AUDIO_FORMAT_LABEL:
            self.settings["default_audio_quality"] = self.quality_combo.currentText()
        elif self.format_combo.currentText() == VIDEO_FORMAT_LABEL:
            self.settings["default_video_quality"] = self.quality_combo.currentText()
        if hasattr(self, "embed_meta_switch"):
            self.settings["embed_metadata"] = self.embed_meta_switch.isChecked()
        if hasattr(self, "skip_existing_switch"):
            self.settings["skip_existing"] = self.skip_existing_switch.isChecked()
        if hasattr(self, "pl_subfolder_switch"):
            self.settings["playlist_subfolder"] = self.pl_subfolder_switch.isChecked()
        if hasattr(self, "pl_numbering_switch"):
            self.settings["playlist_numbering"] = self.pl_numbering_switch.isChecked()
        if hasattr(self, "minimize_tray_switch"):
            self.settings["minimize_to_tray"] = self.minimize_tray_switch.isChecked()
        if hasattr(self, "cookies_combo"):
            self.settings["cookies_browser"] = self.cookies_combo.currentText()
        if hasattr(self, "post_queue_combo"):
            self.settings["post_queue_action"] = self.post_queue_combo.currentText()
        save_settings(self.settings)

    def _sync_footer_state_text(self, keep_custom: bool = False) -> None:
        tasks = list(self._tasks.values())
        total = len(tasks)
        active_tasks = [t for t in tasks if t.status in ("extracting", "downloading", "converting")]
        queued_count = sum(1 for t in tasks if t.status == "queued")
        completed_count = sum(1 for t in tasks if t.status in ("completed", "skipped"))
        active = max(self.manager.active_count, len(active_tasks))
        if hasattr(self, "coffee_cup"):
            self.coffee_cup.setActiveDownloading(active > 0)

        # Atualiza badge ao vivo na barra lateral (visível em todas as telas)
        if active + queued_count > 0:
            self.nav_buttons["Downloads"].setText(f"  Downloads ({active + queued_count})")
        else:
            self.nav_buttons["Downloads"].setText("  Downloads")

        cur = self.footer_state_lbl.text()
        if active > 0 or queued_count > 0:
            self._had_active_queue = True
            self.footer_dot.setStyleSheet("color: #E88B4B; font-size: 12px;")
            overall_pct = 0
            if total > 0:
                progress_sum = sum(
                    1.0 if t.status in ("completed", "skipped", "cancelled", "error") else t.progress
                    for t in tasks
                )
                overall_pct = int(round((progress_sum / total) * 100))
            self.footer_progress_bar.setValue(overall_pct)
            self.footer_progress_bar.show()

            if not keep_custom or cur in ("Analisando link...", "Pronto para baixar") or cur.startswith("Baixando"):
                if total == 1 and active_tasks:
                    t0 = active_tasks[0]
                    short_title = t0.title[:34] + "…" if len(t0.title) > 35 else t0.title
                    self.footer_state_lbl.setText(f"Baixando: {short_title} ({int(t0.progress * 100)}%)")
                elif total > 1:
                    self.footer_state_lbl.setText(
                        f"Baixando {active} arquivo(s)  •  {completed_count}/{total} concluídos ({overall_pct}%)"
                    )
                else:
                    self.footer_state_lbl.setText("Baixando arquivos...")
        else:
            self.footer_dot.setStyleSheet("color: #6EE7B7; font-size: 12px;")
            self.footer_progress_bar.hide()
            if not keep_custom or cur in ("Analisando link...", "Baixando arquivos...") or cur.startswith("Baixando"):
                self.footer_state_lbl.setText("Pronto para baixar")
            if self._had_active_queue and total > 0:
                self._had_active_queue = False
                self._trigger_post_queue_action(completed_count, total)

    def _trigger_post_queue_action(self, completed_ok: int, total: int) -> None:
        action = str(self.settings.get("post_queue_action", "Notificar"))
        if action in ("Notificar", "Abrir Pasta") and hasattr(self, "tray_icon") and self.tray_icon.isVisible():
            self.tray_icon.showMessage(
                APP_DISPLAY_NAME,
                f"Fila concluída: {completed_ok}/{total} mídias prontas!",
                QSystemTrayIcon.MessageIcon.Information,
                4000,
            )
        if action == "Abrir Pasta":
            open_folder(str(self.settings["output_dir"]))

    def _setup_tray(self) -> None:
        self.tray_icon = QSystemTrayIcon(self.windowIcon(), self)
        self.tray_icon.setToolTip(APP_DISPLAY_NAME)
        tray_menu = QMenu()
        act_show = tray_menu.addAction("Abrir CoffeeMediaDownloader")
        act_cancel = tray_menu.addAction("Cancelar Downloads")
        tray_menu.addSeparator()
        act_quit = tray_menu.addAction("Sair")

        act_show.triggered.connect(self._restore_from_tray)
        act_cancel.triggered.connect(self._cancel_all_tasks)
        act_quit.triggered.connect(self._quit_app)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.show()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self._restore_from_tray()

    def _restore_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _quit_app(self) -> None:
        self._force_quit = True
        self.close()

    def _setup_shortcuts(self) -> None:
        sc_find = QShortcut(QKeySequence("Ctrl+F"), self)
        sc_find.activated.connect(self._focus_active_search)
        sc_esc = QShortcut(QKeySequence("Escape"), self)
        sc_esc.activated.connect(self._clear_focused_search)

    def _focus_active_search(self) -> None:
        if self.stack.currentWidget() == self.history_page:
            self.history_search_input.setFocus()
            self.history_search_input.selectAll()
        else:
            self._select_nav("Downloads")
            self.queue_search_input.setFocus()
            self.queue_search_input.selectAll()

    def _clear_focused_search(self) -> None:
        if self.queue_search_input.hasFocus():
            self.queue_search_input.clear()
            self.queue_search_input.clearFocus()
        elif self.history_search_input.hasFocus():
            self.history_search_input.clear()
            self.history_search_input.clearFocus()
