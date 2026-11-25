"""Ponto de entrada da aplicação desktop CoffeeMediaDownloader Pro (PySide6)."""

from __future__ import annotations

import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from ui import CoffeeMediaDownloaderApp


def main() -> None:
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = CoffeeMediaDownloaderApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
