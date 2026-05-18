"""Manage HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\ShutStart."""
from __future__ import annotations

import os
import sys
import winreg

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "ShutStart"


def current_exe_path() -> str:
    """Path used for the Run-key value. Quoted later by the caller."""
    if getattr(sys, "frozen", False):
        return os.path.abspath(sys.executable)
    return os.path.abspath(sys.argv[0])


def _quote(path: str) -> str:
    return f'"{path}"' if not path.startswith('"') else path


def is_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as k:
            value, _ = winreg.QueryValueEx(k, VALUE_NAME)
            return bool(value)
    except FileNotFoundError:
        return False
    except OSError:
        return False


def get_registered_path() -> str | None:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as k:
            value, _ = winreg.QueryValueEx(k, VALUE_NAME)
            return value
    except (FileNotFoundError, OSError):
        return None


def enable(exe_path: str | None = None) -> None:
    exe_path = exe_path or current_exe_path()
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
    ) as k:
        winreg.SetValueEx(k, VALUE_NAME, 0, winreg.REG_SZ, _quote(exe_path))


def disable() -> None:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as k:
            winreg.DeleteValue(k, VALUE_NAME)
    except FileNotFoundError:
        pass
    except OSError:
        pass


def sync_if_moved() -> None:
    """If the Run-key value doesn't point at the current exe, rewrite it."""
    if not is_enabled():
        return
    stored = get_registered_path() or ""
    stored_unquoted = stored.strip('"').lower()
    current = current_exe_path().lower()
    if stored_unquoted != current:
        enable()
