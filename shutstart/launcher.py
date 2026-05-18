"""Launch B-list programs, optionally elevated via ShellExecuteW runas."""
from __future__ import annotations

import ctypes
import logging
import os
import shlex
import subprocess
from dataclasses import dataclass

log = logging.getLogger(__name__)

# Windows process creation flags (so children survive after we exit and no console flashes).
_DETACHED_PROCESS = 0x00000008
_CREATE_NEW_PROCESS_GROUP = 0x00000200
_CREATE_NO_WINDOW = 0x08000000

# ShellExecuteW: SW_SHOWNORMAL = 1
_SW_SHOWNORMAL = 1


@dataclass
class LaunchReport:
    launched: int = 0
    uac_denied: int = 0
    failed: int = 0
    skipped_missing: int = 0


def _split_args(s: str) -> list[str]:
    s = (s or "").strip()
    if not s:
        return []
    try:
        return shlex.split(s, posix=False)
    except ValueError:
        return s.split()


def _working_dir(item: dict) -> str:
    wd = (item.get("working_dir") or "").strip()
    if wd:
        return wd
    exe = item.get("exe_path") or ""
    return os.path.dirname(exe) or os.getcwd()


def launch_one(item: dict, as_admin: bool) -> str:
    """Launch a single B-item. Returns one of: 'launched', 'uac_denied', 'failed', 'missing'."""
    exe = (item.get("exe_path") or "").strip()
    if not exe or not os.path.isfile(exe):
        log.warning("B-item %r exe path missing: %s", item.get("display_name"), exe)
        return "missing"

    args = _split_args(item.get("args", ""))
    wd = _working_dir(item)

    if as_admin:
        # ctypes.windll.shell32.ShellExecuteW(hwnd, op, file, params, dir, show)
        # Returns HINSTANCE; value > 32 means success.
        params = " ".join(f'"{a}"' if " " in a else a for a in args)
        try:
            rv = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", exe, params or None, wd, _SW_SHOWNORMAL
            )
        except OSError as e:
            log.exception("ShellExecuteW failed for %s: %s", exe, e)
            return "failed"
        if rv > 32:
            return "launched"
        if rv == 5:  # SE_ERR_ACCESSDENIED — user clicked No on UAC
            log.info("UAC denied for %s", exe)
            return "uac_denied"
        log.warning("ShellExecuteW returned %s for %s", rv, exe)
        return "failed"

    try:
        subprocess.Popen(
            [exe, *args],
            cwd=wd,
            creationflags=_DETACHED_PROCESS
            | _CREATE_NEW_PROCESS_GROUP
            | _CREATE_NO_WINDOW,
            close_fds=True,
        )
    except OSError as e:
        log.exception("Popen failed for %s: %s", exe, e)
        return "failed"
    return "launched"


def launch_many(items_with_admin: list[tuple[dict, bool]]) -> LaunchReport:
    """Launch a list of (item, as_admin) pairs sequentially.

    Admin items are still serialized so UAC prompts queue cleanly.
    """
    report = LaunchReport()
    for item, as_admin in items_with_admin:
        outcome = launch_one(item, as_admin)
        if outcome == "launched":
            report.launched += 1
        elif outcome == "uac_denied":
            report.uac_denied += 1
        elif outcome == "missing":
            report.skipped_missing += 1
        else:
            report.failed += 1
    return report
