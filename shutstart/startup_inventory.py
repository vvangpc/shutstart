"""Enumerate and toggle Windows startup items (Run / RunOnce + Startup folders).

Toggling enabled state uses the Task-Manager-compatible StartupApproved mechanism:
write a REG_BINARY value whose first byte is 0x02 (enabled) or 0x03 (disabled).
The original Run value / Startup-folder shortcut is left untouched.

By design this module never reads HKLM\\SYSTEM\\CurrentControlSet\\Services —
Windows services are excluded by mechanism, not just by filter.
"""
from __future__ import annotations

import os
import re
import shlex
import winreg
from typing import Iterable

_RUN_RELPATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
_RUNONCE_RELPATH = r"Software\Microsoft\Windows\CurrentVersion\RunOnce"
_WOW_RUN_RELPATH = r"Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Run"
_WOW_RUNONCE_RELPATH = r"Software\Wow6432Node\Microsoft\Windows\CurrentVersion\RunOnce"

_APPROVED_RUN_RELPATH = (
    r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"
)
_APPROVED_WOW_RUN_RELPATH = (
    r"Software\Wow6432Node\Microsoft\Windows\CurrentVersion"
    r"\Explorer\StartupApproved\Run"
)
_APPROVED_STARTUPFOLDER_RELPATH = (
    r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\StartupFolder"
)


# (label, hive, run_subkey, approved_subkey, is_writable)
_REG_SOURCES: list[tuple[str, int, str, str, bool]] = [
    ("HKCU\\Run", winreg.HKEY_CURRENT_USER, _RUN_RELPATH, _APPROVED_RUN_RELPATH, True),
    ("HKCU\\RunOnce", winreg.HKEY_CURRENT_USER, _RUNONCE_RELPATH, _APPROVED_RUN_RELPATH, True),
    ("HKLM\\Run", winreg.HKEY_LOCAL_MACHINE, _RUN_RELPATH, _APPROVED_RUN_RELPATH, False),
    ("HKLM\\RunOnce", winreg.HKEY_LOCAL_MACHINE, _RUNONCE_RELPATH, _APPROVED_RUN_RELPATH, False),
    ("HKLM\\Wow6432Node\\Run", winreg.HKEY_LOCAL_MACHINE, _WOW_RUN_RELPATH, _APPROVED_WOW_RUN_RELPATH, False),
    ("HKLM\\Wow6432Node\\RunOnce", winreg.HKEY_LOCAL_MACHINE, _WOW_RUNONCE_RELPATH, _APPROVED_WOW_RUN_RELPATH, False),
]

_FOLDER_SUFFIX = r"Microsoft\Windows\Start Menu\Programs\Startup"
_FOLDER_EXTS = (".lnk", ".exe", ".bat", ".cmd")

_SVC_FNAME_RE = re.compile(
    r"(?i)(service|svc|daemon|agent|update|updater|helper)[a-z0-9_]*\.exe$"
)
_SVC_NAME_RE = re.compile(r"(?i)(service|svc|daemon)")


def is_enabled_byte(blob: bytes) -> bool:
    """StartupApproved convention: first byte 0x03 means disabled; anything else enabled."""
    if not blob:
        return True
    return blob[0] != 0x03


def parse_command(cmdline: str) -> tuple[str, str]:
    """Split a Run-value command into (target_exe, args). Best-effort."""
    cmd = (cmdline or "").strip()
    if not cmd:
        return "", ""
    if cmd.startswith('"'):
        end = cmd.find('"', 1)
        if end > 0:
            return cmd[1:end], cmd[end + 1 :].strip()
    try:
        tokens = shlex.split(cmd, posix=False)
    except ValueError:
        tokens = cmd.split()
    if tokens:
        first = tokens[0].strip('"')
        if first and (os.path.isfile(first) or first.lower().endswith(_FOLDER_EXTS)):
            rest = cmd[len(tokens[0]) :].strip()
            return first, rest
    lower = cmd.lower()
    for ext in (".exe", ".bat", ".cmd"):
        idx = lower.find(ext)
        if idx > 0:
            cut = idx + len(ext)
            return cmd[:cut].strip('"'), cmd[cut:].strip()
    return cmd, ""


def is_service_like(entry: dict) -> bool:
    if _SVC_NAME_RE.search(entry.get("name", "") or ""):
        return True
    exe = (entry.get("target_exe") or "").lower().replace("/", "\\")
    if not exe:
        return False
    if "\\windows\\system32\\" in exe or "\\windows\\syswow64\\" in exe:
        return True
    return bool(_SVC_FNAME_RE.search(os.path.basename(exe)))


def _read_approved_byte(hive: int, subkey: str, value_name: str) -> bytes | None:
    try:
        with winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ) as k:
            value, _ = winreg.QueryValueEx(k, value_name)
            if isinstance(value, (bytes, bytearray)):
                return bytes(value)
    except FileNotFoundError:
        return None
    except OSError:
        return None
    return None


def _iter_reg_values(hive: int, subkey: str) -> Iterable[tuple[str, str]]:
    try:
        k = winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ)
    except FileNotFoundError:
        return
    except OSError:
        return
    try:
        i = 0
        while True:
            try:
                name, data, _typ = winreg.EnumValue(k, i)
            except OSError:
                break
            i += 1
            if not name:
                continue
            yield name, str(data) if data is not None else ""
    finally:
        k.Close()


def _build_reg_entry(
    source: str,
    hive: int,
    name: str,
    command: str,
    approved_subkey: str,
    is_writable: bool,
) -> dict:
    target_exe, args = parse_command(command)
    approved_blob = _read_approved_byte(hive, approved_subkey, name)
    enabled = is_enabled_byte(approved_blob) if approved_blob is not None else True
    entry = {
        "id": f"{source}::{name}",
        "name": name,
        "source": source,
        "command": command,
        "target_exe": target_exe,
        "args": args,
        "enabled": enabled,
        "is_writable": is_writable,
        "approved_hive": hive,
        "approved_subkey": approved_subkey,
        "approved_value": name,
        "is_service_like": False,
    }
    entry["is_service_like"] = is_service_like(entry)
    return entry


def _build_folder_entry(
    label: str, folder: str, filename: str, is_writable: bool
) -> dict:
    full = os.path.join(folder, filename)
    target_exe = full if filename.lower().endswith((".exe", ".bat", ".cmd")) else ""
    approved_blob = _read_approved_byte(
        winreg.HKEY_CURRENT_USER, _APPROVED_STARTUPFOLDER_RELPATH, filename
    )
    enabled = is_enabled_byte(approved_blob) if approved_blob is not None else True
    entry = {
        "id": f"{label}::{filename}",
        "name": os.path.splitext(filename)[0],
        "source": label,
        "command": full,
        "target_exe": target_exe,
        "args": "",
        "enabled": enabled,
        "is_writable": is_writable,
        "approved_hive": winreg.HKEY_CURRENT_USER,
        "approved_subkey": _APPROVED_STARTUPFOLDER_RELPATH,
        "approved_value": filename,
        "is_service_like": False,
    }
    entry["is_service_like"] = is_service_like(entry)
    return entry


def _user_startup_folder() -> str | None:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None
    return os.path.join(appdata, _FOLDER_SUFFIX)


def _common_startup_folder() -> str | None:
    base = os.environ.get("ProgramData") or r"C:\ProgramData"
    return os.path.join(base, _FOLDER_SUFFIX)


def _scan_folder(folder: str | None) -> list[str]:
    if not folder or not os.path.isdir(folder):
        return []
    out: list[str] = []
    try:
        for name in os.listdir(folder):
            if name.lower().endswith(_FOLDER_EXTS):
                out.append(name)
    except OSError:
        return []
    return out


def enumerate_entries() -> list[dict]:
    entries: list[dict] = []

    for label, hive, run_subkey, approved_subkey, writable in _REG_SOURCES:
        for name, command in _iter_reg_values(hive, run_subkey):
            entries.append(
                _build_reg_entry(label, hive, name, command, approved_subkey, writable)
            )

    user_folder = _user_startup_folder()
    for fname in _scan_folder(user_folder):
        entries.append(_build_folder_entry("Startup (用户)", user_folder, fname, True))

    common_folder = _common_startup_folder()
    for fname in _scan_folder(common_folder):
        entries.append(_build_folder_entry("Startup (公共)", common_folder, fname, False))

    entries.sort(key=lambda e: (e.get("is_service_like", False), e.get("name", "").lower()))
    return entries


def set_enabled(entry: dict, enabled: bool) -> None:
    """Soft-toggle via StartupApproved. Raises PermissionError for non-writable entries."""
    if not entry.get("is_writable"):
        raise PermissionError("HKLM / 公共启动项需要管理员权限")
    payload = bytes([0x02 if enabled else 0x03]) + b"\x00" * 11
    with winreg.CreateKeyEx(
        entry["approved_hive"], entry["approved_subkey"], 0, winreg.KEY_SET_VALUE
    ) as k:
        winreg.SetValueEx(k, entry["approved_value"], 0, winreg.REG_BINARY, payload)
    entry["enabled"] = enabled
