"""Read/write %APPDATA%\\ShutStart\\config.json with atomic save."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

CONFIG_VERSION = 3
DEFAULT_THEME = "claude"
VALID_THEMES = {"claude", "mac"}

# Countdown range — UI auto-cancel timer for the main boot dialog.
COUNTDOWN_MIN = 30
COUNTDOWN_MAX = 600
DEFAULT_COUNTDOWN_SECONDS = 60


def appdata_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    d = Path(base) / "ShutStart"
    d.mkdir(parents=True, exist_ok=True)
    return d


def config_path() -> Path:
    return appdata_dir() / "config.json"


def log_path() -> Path:
    return appdata_dir() / "shutstart.log"


def default_config() -> dict[str, Any]:
    return {
        "version": CONFIG_VERSION,
        "autostart_enabled": True,
        "theme": DEFAULT_THEME,
        "window_state": {},
        "countdown_enabled": True,
        "countdown_seconds": DEFAULT_COUNTDOWN_SECONDS,
        "a_list": [],
        "b_list": [],
    }


def clamp_countdown(value: Any) -> int:
    """Coerce an arbitrary value into the valid countdown range."""
    try:
        v = int(value)
    except (TypeError, ValueError):
        return DEFAULT_COUNTDOWN_SECONDS
    return max(COUNTDOWN_MIN, min(COUNTDOWN_MAX, v))


def load() -> dict[str, Any]:
    p = config_path()
    if not p.exists():
        cfg = default_config()
        save(cfg)
        return cfg
    try:
        with p.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, json.JSONDecodeError):
        cfg = default_config()
        save(cfg)
        return cfg
    return _migrate(cfg)


def save(cfg: dict[str, Any]) -> None:
    p = config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="config.", suffix=".json.tmp", dir=str(p.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        os.replace(tmp, p)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _migrate(cfg: dict[str, Any]) -> dict[str, Any]:
    cfg.setdefault("version", CONFIG_VERSION)
    cfg.setdefault("autostart_enabled", True)
    cfg.setdefault("a_list", [])
    cfg.setdefault("b_list", [])

    # v1 → v2: add theme + window_state with safe defaults.
    theme = cfg.get("theme")
    if theme not in VALID_THEMES:
        cfg["theme"] = DEFAULT_THEME
    if not isinstance(cfg.get("window_state"), dict):
        cfg["window_state"] = {}

    # v2 → v3: add countdown auto-cancel.
    cfg.setdefault("countdown_enabled", True)
    cfg["countdown_seconds"] = clamp_countdown(
        cfg.get("countdown_seconds", DEFAULT_COUNTDOWN_SECONDS)
    )

    for item in cfg["a_list"]:
        item.setdefault("default_checked", True)
        if isinstance(item.get("process_names"), str):
            item["process_names"] = [item["process_names"]]
    for item in cfg["b_list"]:
        item.setdefault("default_checked", True)
        item.setdefault("default_admin", False)
        item.setdefault("args", "")
        item.setdefault("working_dir", "")

    cfg["version"] = CONFIG_VERSION
    return cfg


def get_window_size(cfg: dict[str, Any], dialog_name: str) -> tuple[int, int] | None:
    """Return (width, height) for the named dialog if remembered, else None."""
    ws = cfg.get("window_state") or {}
    size = ws.get(dialog_name)
    if not isinstance(size, (list, tuple)) or len(size) != 2:
        return None
    try:
        w, h = int(size[0]), int(size[1])
    except (TypeError, ValueError):
        return None
    if w < 200 or h < 150 or w > 8000 or h > 6000:
        return None
    return w, h


def set_window_size(dialog_name: str, width: int, height: int) -> None:
    """Persist a dialog size to config.json (re-reads to avoid clobbering)."""
    cfg = load()
    ws = cfg.get("window_state")
    if not isinstance(ws, dict):
        ws = {}
        cfg["window_state"] = ws
    ws[dialog_name] = [int(width), int(height)]
    save(cfg)
