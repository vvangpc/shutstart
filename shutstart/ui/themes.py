"""QSS theme definitions and runtime application."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

log = logging.getLogger(__name__)


# ----------------------------------------------------------------------------
# Claude theme — cream / warm orange
# ----------------------------------------------------------------------------
CLAUDE_QSS = """
* {
    font-family: "Segoe UI", "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 10pt;
    color: #3a3a3a;
}
QDialog, QWidget {
    background-color: #fdfaf5;
}
QLabel {
    background: transparent;
}
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #e8dccb;
    border-radius: 10px;
    margin-top: 14px;
    padding: 14px 10px 10px 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    color: #6b5a44;
    font-weight: 600;
    background-color: #fdfaf5;
}
QPushButton, QToolButton {
    background-color: #ffffff;
    border: 1px solid #e0d2b8;
    border-radius: 8px;
    padding: 6px 14px;
    color: #3a3a3a;
    min-height: 22px;
}
QPushButton:hover, QToolButton:hover {
    background-color: #f3ebde;
    border-color: #d9c4a8;
}
QPushButton:pressed, QToolButton:pressed {
    background-color: #e9dcc6;
}
QPushButton:disabled, QToolButton:disabled {
    color: #b8b0a0;
    background-color: #f7f4ee;
    border-color: #ebe3d3;
}
QPushButton:default {
    background-color: #d97757;
    color: #ffffff;
    border-color: #c46645;
}
QPushButton:default:hover {
    background-color: #c46645;
}
QPushButton:default:pressed {
    background-color: #b0573a;
}
QToolButton::menu-indicator {
    subcontrol-origin: padding;
    subcontrol-position: right center;
    right: 6px;
}
QListWidget {
    background-color: #ffffff;
    border: 1px solid #e8dccb;
    border-radius: 8px;
    padding: 4px;
    alternate-background-color: #fbf6ec;
    outline: 0;
}
QListWidget::item {
    padding: 5px 6px;
    border-radius: 4px;
}
QListWidget::item:selected {
    background-color: #f0d4be;
    color: #3a3a3a;
}
QListWidget::item:hover:!selected {
    background-color: #f8efe1;
}
QLineEdit, QTextEdit, QComboBox {
    background-color: #ffffff;
    border: 1px solid #e0d2b8;
    border-radius: 6px;
    padding: 4px 8px;
    selection-background-color: #f0d4be;
    selection-color: #3a3a3a;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border-color: #d97757;
}
QComboBox::drop-down {
    border: none;
    width: 22px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #e8dccb;
    selection-background-color: #f0d4be;
    selection-color: #3a3a3a;
    outline: 0;
}
QCheckBox {
    background: transparent;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #d9c4a8;
    background-color: #ffffff;
}
QCheckBox::indicator:hover {
    border-color: #d97757;
}
QCheckBox::indicator:checked {
    background-color: #d97757;
    border-color: #c46645;
    image: url("__CHECK_URL__");
}
QCheckBox::indicator:disabled {
    background-color: #f0ebe0;
    border-color: #e0d2b8;
}
QSplitter::handle:horizontal {
    background-color: #ebe0cb;
    width: 6px;
    margin: 4px 0;
    border-radius: 3px;
}
QSplitter::handle:horizontal:hover {
    background-color: #d9c4a8;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background-color: #e0d2b8;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background-color: #c9b793;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QMenu {
    background-color: #ffffff;
    border: 1px solid #e8dccb;
    border-radius: 8px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 18px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #f3ebde;
    color: #3a3a3a;
}
QTabWidget::pane {
    border: 1px solid #e8dccb;
    border-radius: 8px;
    background-color: #ffffff;
    top: -1px;
}
QTabBar::tab {
    background-color: #f3ebde;
    color: #6b5a44;
    padding: 6px 14px;
    border: 1px solid #e8dccb;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #ffffff;
    color: #3a3a3a;
}
QMessageBox, QFileDialog {
    background-color: #fdfaf5;
}
QToolTip {
    background-color: #3a3a3a;
    color: #fdfaf5;
    border: 1px solid #2a2a2a;
    padding: 4px 6px;
    border-radius: 4px;
}
"""


# ----------------------------------------------------------------------------
# Mac theme — cool grays / Apple blue
# ----------------------------------------------------------------------------
MAC_QSS = """
* {
    font-family: "Segoe UI Variable", "Segoe UI", "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 10pt;
    color: #1d1d1f;
}
QDialog, QWidget {
    background-color: #f5f5f7;
}
QLabel {
    background: transparent;
}
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 10px;
    margin-top: 14px;
    padding: 14px 10px 10px 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 6px;
    color: #6e6e73;
    font-weight: 600;
    background-color: #f5f5f7;
}
QPushButton, QToolButton {
    background-color: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 6px;
    padding: 6px 14px;
    color: #1d1d1f;
    min-height: 22px;
}
QPushButton:hover, QToolButton:hover {
    background-color: #f5f5f7;
    border-color: #b8b8be;
}
QPushButton:pressed, QToolButton:pressed {
    background-color: #e5e5ea;
}
QPushButton:disabled, QToolButton:disabled {
    color: #a8a8ad;
    background-color: #fafafa;
    border-color: #e1e1e6;
}
QPushButton:default {
    background-color: #0071e3;
    color: #ffffff;
    border-color: #0062c4;
}
QPushButton:default:hover {
    background-color: #0062c4;
}
QPushButton:default:pressed {
    background-color: #0058b0;
}
QToolButton::menu-indicator {
    subcontrol-origin: padding;
    subcontrol-position: right center;
    right: 6px;
}
QListWidget {
    background-color: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 10px;
    padding: 4px;
    alternate-background-color: #fafafa;
    outline: 0;
}
QListWidget::item {
    padding: 5px 6px;
    border-radius: 4px;
}
QListWidget::item:selected {
    background-color: #0071e3;
    color: #ffffff;
}
QListWidget::item:hover:!selected {
    background-color: #f0f0f3;
}
QLineEdit, QTextEdit, QComboBox {
    background-color: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 6px;
    padding: 4px 8px;
    selection-background-color: #0071e3;
    selection-color: #ffffff;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border-color: #0071e3;
}
QComboBox::drop-down {
    border: none;
    width: 22px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #d2d2d7;
    selection-background-color: #0071e3;
    selection-color: #ffffff;
    outline: 0;
}
QCheckBox {
    background: transparent;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #b8b8be;
    background-color: #ffffff;
}
QCheckBox::indicator:hover {
    border-color: #0071e3;
}
QCheckBox::indicator:checked {
    background-color: #0071e3;
    border-color: #0062c4;
    image: url("__CHECK_URL__");
}
QCheckBox::indicator:disabled {
    background-color: #f0f0f3;
    border-color: #d2d2d7;
}
QSplitter::handle:horizontal {
    background-color: #d2d2d7;
    width: 6px;
    margin: 4px 0;
    border-radius: 3px;
}
QSplitter::handle:horizontal:hover {
    background-color: #b8b8be;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background-color: #c7c7cc;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background-color: #a8a8ad;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QMenu {
    background-color: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 8px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 18px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #0071e3;
    color: #ffffff;
}
QTabWidget::pane {
    border: 1px solid #d2d2d7;
    border-radius: 8px;
    background-color: #ffffff;
    top: -1px;
}
QTabBar::tab {
    background-color: #ebebed;
    color: #6e6e73;
    padding: 6px 14px;
    border: 1px solid #d2d2d7;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #ffffff;
    color: #1d1d1f;
}
QMessageBox, QFileDialog {
    background-color: #f5f5f7;
}
QToolTip {
    background-color: #1d1d1f;
    color: #f5f5f7;
    border: 1px solid #2a2a2a;
    padding: 4px 6px;
    border-radius: 4px;
}
"""


THEMES: dict[str, dict] = {
    "claude": {
        "display_name": "Claude 风 (暖橙)",
        "qss": CLAUDE_QSS,
        "accent": "#d97757",
        "icon_filename": "icon-claude.ico",
    },
    "mac": {
        "display_name": "Mac 风 (Apple 蓝)",
        "qss": MAC_QSS,
        "accent": "#0071e3",
        "icon_filename": "icon-mac.ico",
    },
}

DEFAULT_THEME = "claude"


def _resources_dir() -> Path:
    """Resolve shutstart/resources/ for both source and PyInstaller-frozen modes."""
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        return base / "shutstart" / "resources"
    return Path(__file__).resolve().parent.parent / "resources"


def icon_path(theme_name: str) -> Path:
    """Return the ICO path for a theme; falls back to icon.ico if specific is missing."""
    meta = THEMES.get(theme_name) or THEMES[DEFAULT_THEME]
    base = _resources_dir()
    specific = base / meta["icon_filename"]
    if specific.is_file():
        return specific
    fallback = base / "icon.ico"
    return fallback if fallback.is_file() else specific  # may not exist; caller copes


def _check_image_url() -> str:
    """Absolute path to the checkmark PNG, formatted for use in QSS url(...)."""
    path = _resources_dir() / "check-white.png"
    if not path.is_file():
        return ""
    return str(path.resolve()).replace("\\", "/")


def apply_theme(app: QApplication, theme_name: str) -> None:
    """Apply QSS + window icon to the running QApplication."""
    name = theme_name if theme_name in THEMES else DEFAULT_THEME
    qss = THEMES[name]["qss"].replace("__CHECK_URL__", _check_image_url())
    try:
        app.setStyleSheet(qss)
    except Exception:
        log.exception("setStyleSheet failed for theme %s", name)

    ico = icon_path(name)
    try:
        if ico.is_file():
            app.setWindowIcon(QIcon(str(ico)))
    except Exception:
        log.exception("setWindowIcon failed for %s", ico)
