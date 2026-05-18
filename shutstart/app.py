"""QApplication bootstrap with HiDPI flags applied BEFORE construction."""
from __future__ import annotations

import os
import sys


def _apply_hidpi_env() -> None:
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
    os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "PassThrough")


def create_app(argv: list[str] | None = None):
    """Create a QApplication with HiDPI settings. Returns the app instance."""
    _apply_hidpi_env()
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication

    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("ShutStart")
    app.setOrganizationName("ShutStart")
    return app
