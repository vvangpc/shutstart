"""Task Scheduler-based autostart with `/rl highest` for silent UAC-free elevation.

Why this exists: HKCU\\Run gives a normal-user token, so ShutStart can't terminate
SYSTEM-owned processes (e.g. AweSun.exe, awesun_guard.exe, ToDesk_Service.exe).
The only Windows-sanctioned way to get an admin token at logon without prompting
for UAC every boot is a pre-authorised Task Scheduler task with "Run with highest
privileges". Creating/deleting such a task itself needs admin, so those ops go
through ShellExecuteW runas (one UAC prompt per toggle). Once created, every
subsequent logon-triggered run is silent.
"""
from __future__ import annotations

import ctypes
import logging
import os
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

log = logging.getLogger(__name__)

TASK_NAME = r"\ShutStart\ShutStart Logon"

# ShellExecuteW: SW_HIDE = 0
_SW_HIDE = 0
# ShellExecuteW return code on UAC refusal.
_SE_ERR_ACCESSDENIED = 5

# Hide subprocess.run console windows on Windows.
_CREATE_NO_WINDOW = 0x08000000


def _schtasks_query() -> subprocess.CompletedProcess:
    return subprocess.run(
        ["schtasks", "/query", "/tn", TASK_NAME],
        capture_output=True,
        text=True,
        check=False,
        creationflags=_CREATE_NO_WINDOW,
    )


def is_enabled() -> bool:
    """Return True iff the logon task exists. Does not need admin."""
    try:
        rv = _schtasks_query()
    except OSError:
        return False
    return rv.returncode == 0


def _run_schtasks_elevated(schtasks_args: str, timeout: float = 30.0) -> bool:
    """Run `schtasks <args>` in an elevated shell. Returns True on exit code 0.

    We can't capture exit codes from ShellExecuteW directly, so we wrap the command
    in a temp .bat that writes a marker file on success and poll for it.
    """
    tmp_dir = Path(tempfile.gettempdir())
    suffix = uuid.uuid4().hex[:8]
    bat_path = tmp_dir / f"shutstart_schtasks_{suffix}.bat"
    marker = tmp_dir / f"shutstart_schtasks_{suffix}.ok"

    bat_path.write_text(
        "@echo off\r\n"
        f"schtasks {schtasks_args}\r\n"
        f'if %errorlevel%==0 (type nul > "{marker}")\r\n',
        encoding="mbcs",
    )

    try:
        try:
            rv = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", str(bat_path), None, None, _SW_HIDE
            )
        except OSError as e:
            log.exception("ShellExecuteW failed: %s", e)
            return False

        if rv <= 32:
            if rv == _SE_ERR_ACCESSDENIED:
                log.info("User denied UAC for schtasks operation")
            else:
                log.warning("ShellExecuteW returned %s", rv)
            return False

        deadline = time.time() + timeout
        while time.time() < deadline:
            if marker.exists():
                return True
            time.sleep(0.2)

        log.warning("schtasks marker not produced within %ss", timeout)
        return False
    finally:
        for p in (bat_path, marker):
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass


def create(exe_path: str) -> bool:
    """Create (or replace) the logon task. Prompts UAC. Returns True on success."""
    exe_path = os.path.abspath(exe_path)
    # /tr accepts a single quoted-token TR=program; quote inner exe path so paths
    # with spaces work. We single-quote the whole /tr value at shell level via
    # escaping the outer double-quotes for cmd's parser inside the .bat file.
    tr = f'\\"{exe_path}\\"'
    args = (
        f'/create /tn "{TASK_NAME}" /tr "{tr}" '
        f"/sc onlogon /rl highest /it /f"
    )
    return _run_schtasks_elevated(args)


def delete() -> bool:
    """Delete the logon task. Prompts UAC. Returns True on success.

    Returns True if the task is already absent (treated as a no-op success).
    """
    if not is_enabled():
        return True
    args = f'/delete /tn "{TASK_NAME}" /f'
    return _run_schtasks_elevated(args)
