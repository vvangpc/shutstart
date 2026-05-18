"""Match and terminate A-list processes via psutil."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import psutil


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
    skipped: int = 0


def scan(a_items: Iterable[dict]) -> ScanResult:
    """Return a mapping of item_id -> list of matching psutil.Process objects."""
    items = list(a_items)
    if not items:
        return ScanResult()

    targets: dict[str, set[str]] = {}
    for item in items:
        names = {n.lower() for n in item.get("process_names", []) if n}
        if names:
            targets[item["id"]] = names

    result = ScanResult(by_id={item["id"]: [] for item in items})

    for proc in psutil.process_iter(["name"]):
        try:
            name = (proc.info.get("name") or "").lower()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        if not name:
            continue
        for item_id, names in targets.items():
            if name in names:
                result.by_id[item_id].append(proc)
    return result


def kill(processes: Iterable[psutil.Process], timeout: float = 3.0) -> KillReport:
    report = KillReport()
    procs = list(processes)
    if not procs:
        return report

    alive: list[psutil.Process] = []
    for p in procs:
        try:
            p.terminate()
            alive.append(p)
        except psutil.NoSuchProcess:
            report.skipped += 1
        except psutil.AccessDenied:
            report.failed += 1
        except Exception:
            report.failed += 1

    if alive:
        gone, still_alive = psutil.wait_procs(alive, timeout=timeout)
        report.killed += len(gone)
        for p in still_alive:
            try:
                p.kill()
                report.killed += 1
            except psutil.NoSuchProcess:
                report.skipped += 1
            except psutil.AccessDenied:
                report.failed += 1
            except Exception:
                report.failed += 1
    return report
