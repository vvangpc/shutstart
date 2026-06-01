"""Match and terminate A-list processes via psutil.

Matching is by executable name, case-insensitive, with a trailing ``.exe``
treated as optional — "UU", "uu.exe" and "UU.EXE" all match the same process.

Why termination is more than a single ``terminate()``: remote-desktop / RMM
tools (向日葵 AweSun, ToDesk, AnyDesk, 网易UU 远程 …) typically run as a main UI
process plus one or more *guard* / *service* processes that relaunch the main
process the instant it dies. Killing only the matched PIDs — or killing them one
at a time — lets a guard respawn its partner before the sweep finishes. So we:

  1. re-scan by name every round (catches late-starting and respawned PIDs),
  2. expand to the whole process tree (a guard is often a child),
  3. suspend the whole batch first so nothing can respawn mid-kill,
  4. force-kill (these tools routinely ignore a graceful terminate),
  5. repeat a few rounds, stopping early once a round kills nothing.

Anything still alive after the last round is reported as ``failed`` — usually a
SYSTEM service that needs the admin-mode autostart (task scheduler) to kill.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Iterable

import psutil

log = logging.getLogger(__name__)

# Sweep tuning. wait_procs returns as soon as everything dies, so these are
# worst-case bounds that only bite when something genuinely refuses to die.
_KILL_ROUNDS = 4
_WAIT_TIMEOUT = 2.0


def _norm(name: str) -> str:
    """Normalize a process name for matching: lowercase, trailing .exe optional."""
    n = (name or "").strip().lower()
    return n[:-4] if n.endswith(".exe") else n


def item_names(item: dict) -> set[str]:
    """Normalized process-name set configured for an A-item."""
    return {m for m in (_norm(n) for n in item.get("process_names", []) if n) if m}


@dataclass
class ScanResult:
    by_id: dict[str, list[psutil.Process]] = field(default_factory=dict)

    def count(self, item_id: str) -> int:
        return len(self.by_id.get(item_id, []))

    def is_running(self, item_id: str) -> bool:
        return self.count(item_id) > 0


@dataclass
class KillReport:
    killed: int = 0
    failed: int = 0


def scan(a_items: Iterable[dict]) -> ScanResult:
    """Map item_id -> matching psutil.Process list (by normalized exe name)."""
    items = list(a_items)
    targets: dict[str, set[str]] = {}
    for item in items:
        names = item_names(item)
        if names:
            targets[item["id"]] = names

    result = ScanResult(by_id={item["id"]: [] for item in items})
    if not targets:
        return result

    for proc in psutil.process_iter(["name"]):
        try:
            name = _norm(proc.info.get("name") or "")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        if not name:
            continue
        for item_id, names in targets.items():
            if name in names:
                result.by_id[item_id].append(proc)
    return result


def _self_pids() -> set[int]:
    """Our own PID, parent (PyInstaller onefile bootloader) and children.

    Excluded from every sweep so we can never suspend or kill the process doing
    the killing, even if the user (mistakenly) lists ShutStart's own exe.
    """
    me = os.getpid()
    pids = {me}
    try:
        proc = psutil.Process(me)
        parent = proc.parent()
        if parent is not None:
            pids.add(parent.pid)
        for child in proc.children(recursive=True):
            pids.add(child.pid)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return pids


def _collect(name_set: set[str], exclude: set[int]) -> dict[int, psutil.Process]:
    """Processes whose name is in name_set, plus their descendants, keyed by pid."""
    matched: list[psutil.Process] = []
    for proc in psutil.process_iter(["name"]):
        try:
            if _norm(proc.info.get("name") or "") in name_set:
                matched.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    tree: dict[int, psutil.Process] = {}
    for p in matched:
        try:
            if p.pid not in exclude:
                tree.setdefault(p.pid, p)
            for child in p.children(recursive=True):
                if child.pid not in exclude:
                    tree.setdefault(child.pid, child)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return tree


def kill_by_names(
    name_set: set[str],
    rounds: int = _KILL_ROUNDS,
    wait_timeout: float = _WAIT_TIMEOUT,
) -> KillReport:
    """Aggressively terminate every process matching name_set (plus its tree).

    Re-scans each round so a guard's respawn is caught; suspends the batch
    before killing so guards can't relaunch their partners mid-sweep. Returns
    counts of distinctly-killed PIDs and of processes still alive at the end.
    """
    report = KillReport()
    if not name_set:
        return report

    exclude = _self_pids()
    killed_pids: set[int] = set()

    for _ in range(max(1, rounds)):
        procs = list(_collect(name_set, exclude).values())
        if not procs:
            break

        # Freeze the whole batch first: a suspended guard can't notice its
        # partner dying and relaunch it while we work through the list.
        for p in procs:
            try:
                p.suspend()
            except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                pass

        for p in procs:
            try:
                p.kill()
            except psutil.NoSuchProcess:
                pass
            except (psutil.AccessDenied, OSError):
                pass

        gone, alive = psutil.wait_procs(procs, timeout=wait_timeout)
        for p in gone:
            killed_pids.add(p.pid)

        # Anything we couldn't kill must not be left frozen — un-suspend it.
        for p in alive:
            try:
                p.resume()
            except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                pass

        # Nothing died this round → the survivors are unkillable here (need
        # admin); further rounds would only spin. Stop.
        if not gone:
            break

    leftover = _collect(name_set, exclude)
    report.killed = len(killed_pids)
    report.failed = len(leftover)
    if report.failed:
        log.info(
            "kill_by_names: %d killed, %d still alive for names=%s",
            report.killed,
            report.failed,
            sorted(name_set),
        )
    return report
