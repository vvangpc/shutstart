"""Add/edit dialog for a single A-item or B-item."""
from __future__ import annotations

import os
import re
import uuid
from typing import Optional

import psutil
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


def _slugify(text: str, fallback: str = "item") -> str:
    s = re.sub(r"[^a-zA-Z0-9_-]+", "-", text.strip().lower()).strip("-")
    return s or f"{fallback}-{uuid.uuid4().hex[:8]}"


_SYSTEM_USERNAMES = {
    "nt authority\\system",
    "nt authority\\local service",
    "nt authority\\network service",
    "system",
    "local service",
    "network service",
}


def _is_system_process(proc: psutil.Process) -> bool:
    """Heuristic: process belongs to a system service / SYSTEM user."""
    try:
        user = (proc.username() or "").lower()
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        # Protected processes typically deny username() — treat as system.
        return True
    except OSError:
        return False
    if not user:
        return False
    if user in _SYSTEM_USERNAMES:
        return True
    return user.startswith("nt authority\\") or user.startswith("nt service\\")


class ProcessPicker(QDialog):
    """Pick one or more running process names from a live list.

    Default view hides system / service processes (SYSTEM, LOCAL/NETWORK SERVICE,
    NT SERVICE\\*, plus anything we can't query). A checkbox unhides them with
    a grey '(系统)' suffix.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("从运行中的进程选择")
        self.resize(440, 500)
        self._selected: list[str] = []
        # All discovered processes, deduped by lowercase name.
        # Each entry: (display_name, is_system).
        self._rows: list[tuple[str, bool]] = []

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("勾选要添加的进程 (可多选):"))

        self.show_system_cb = QCheckBox("显示系统进程 (services、svchost 等)")
        self.show_system_cb.setChecked(False)
        self.show_system_cb.stateChanged.connect(self._render)
        layout.addWidget(self.show_system_cb)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.NoSelection)
        layout.addWidget(self.list_widget)

        self._scan()
        self._render()

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _scan(self) -> None:
        # Rule: a process name is "system" if ANY instance is system-owned or
        # denies username() access. svchost.exe / dwm.exe etc. typically have
        # privileged instances we can't query — those should be hidden by default
        # even if a user-context instance also exists.
        seen: dict[str, bool] = {}  # lowercase name -> is_system
        display_names: dict[str, str] = {}
        for p in psutil.process_iter(["name"]):
            try:
                n = p.info.get("name") or ""
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            if not n:
                continue
            key = n.lower()
            is_sys = _is_system_process(p)
            if key in seen:
                if is_sys:
                    seen[key] = True
            else:
                seen[key] = is_sys
                display_names[key] = n
        self._rows = sorted(
            ((display_names[k], v) for k, v in seen.items()),
            key=lambda t: t[0].lower(),
        )

    def _render(self) -> None:
        show_system = self.show_system_cb.isChecked()
        # Preserve current check state by name.
        checked: set[str] = set()
        for i in range(self.list_widget.count()):
            it = self.list_widget.item(i)
            if it.checkState() == Qt.Checked:
                checked.add(it.data(Qt.UserRole))
        self.list_widget.clear()
        for name, is_sys in self._rows:
            if is_sys and not show_system:
                continue
            display = f"{name}  (系统)" if is_sys else name
            it = QListWidgetItem(display)
            it.setData(Qt.UserRole, name)
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Checked if name in checked else Qt.Unchecked)
            if is_sys:
                it.setForeground(Qt.gray)
            self.list_widget.addItem(it)

    def _accept(self) -> None:
        self._selected = []
        for i in range(self.list_widget.count()):
            it = self.list_widget.item(i)
            if it.checkState() == Qt.Checked:
                self._selected.append(it.data(Qt.UserRole))
        self.accept()

    def selected(self) -> list[str]:
        return self._selected


class AItemEditor(QDialog):
    """Edit a single A-list (close) item."""

    def __init__(self, parent=None, item: Optional[dict] = None):
        super().__init__(parent)
        self.setWindowTitle("编辑关闭项 (A 类)" if item else "新增关闭项 (A 类)")
        self._original = item

        form = QFormLayout()
        self.name_edit = QLineEdit(item["display_name"] if item else "")
        self.name_edit.setPlaceholderText("例如: AnyDesk")
        form.addRow("显示名:", self.name_edit)

        self.proc_edit = QTextEdit()
        self.proc_edit.setPlaceholderText("一行一个进程名,或用逗号分隔。例如:\nAnyDesk.exe\nAnyDesk_Service.exe")
        self.proc_edit.setFixedHeight(90)
        if item:
            self.proc_edit.setPlainText("\n".join(item.get("process_names", [])))
        form.addRow("进程名:", self.proc_edit)

        pick_btn = QPushButton("从运行中的进程选择…")
        pick_btn.clicked.connect(self._pick_processes)
        form.addRow("", pick_btn)

        self.default_check = QCheckBox("默认勾选 (主对话框打开时自动勾上)")
        self.default_check.setChecked(item.get("default_checked", True) if item else True)
        form.addRow("", self.default_check)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self.resize(440, 280)

    def _pick_processes(self) -> None:
        dlg = ProcessPicker(self)
        if dlg.exec_() == QDialog.Accepted:
            picked = dlg.selected()
            if not picked:
                return
            existing = self._parse_proc_names()
            for n in picked:
                if n not in existing:
                    existing.append(n)
            self.proc_edit.setPlainText("\n".join(existing))

    def _parse_proc_names(self) -> list[str]:
        raw = self.proc_edit.toPlainText()
        tokens: list[str] = []
        for chunk in raw.replace(",", "\n").replace("，", "\n").splitlines():
            t = chunk.strip()
            if t and t not in tokens:
                tokens.append(t)
        return tokens

    def _on_accept(self) -> None:
        name = self.name_edit.text().strip()
        procs = self._parse_proc_names()
        if not name:
            QMessageBox.warning(self, "缺少信息", "请填写显示名。")
            return
        if not procs:
            QMessageBox.warning(self, "缺少信息", "请至少填写一个进程名 (例如 AnyDesk.exe)。")
            return
        self.accept()

    def result_item(self) -> dict:
        return {
            "id": (self._original or {}).get("id") or _slugify(self.name_edit.text(), "a"),
            "display_name": self.name_edit.text().strip(),
            "process_names": self._parse_proc_names(),
            "default_checked": self.default_check.isChecked(),
        }


class BItemEditor(QDialog):
    """Edit a single B-list (launch) item."""

    def __init__(self, parent=None, item: Optional[dict] = None):
        super().__init__(parent)
        self.setWindowTitle("编辑启动项 (B 类)" if item else "新增启动项 (B 类)")
        self._original = item

        form = QFormLayout()
        self.name_edit = QLineEdit(item["display_name"] if item else "")
        self.name_edit.setPlaceholderText("例如: Clash Verge")
        form.addRow("显示名:", self.name_edit)

        path_row = QHBoxLayout()
        self.path_edit = QLineEdit(item["exe_path"] if item else "")
        self.path_edit.setPlaceholderText(r"C:\Program Files\XXX\xxx.exe")
        browse_exe = QPushButton("浏览…")
        browse_exe.clicked.connect(self._browse_exe)
        path_row.addWidget(self.path_edit)
        path_row.addWidget(browse_exe)
        form.addRow("程序路径:", path_row)

        self.args_edit = QLineEdit(item.get("args", "") if item else "")
        self.args_edit.setPlaceholderText("可选,例如: --silent")
        form.addRow("启动参数:", self.args_edit)

        wd_row = QHBoxLayout()
        self.wd_edit = QLineEdit(item.get("working_dir", "") if item else "")
        self.wd_edit.setPlaceholderText("留空 = 使用程序所在目录")
        browse_wd = QPushButton("浏览…")
        browse_wd.clicked.connect(self._browse_wd)
        wd_row.addWidget(self.wd_edit)
        wd_row.addWidget(browse_wd)
        form.addRow("工作目录:", wd_row)

        self.admin_check = QCheckBox("默认以管理员身份启动 (会触发 UAC)")
        self.admin_check.setChecked(item.get("default_admin", False) if item else False)
        form.addRow("", self.admin_check)

        self.default_check = QCheckBox("默认勾选 (主对话框打开时自动勾上)")
        self.default_check.setChecked(item.get("default_checked", True) if item else True)
        form.addRow("", self.default_check)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._on_accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self.resize(520, 280)

    def _browse_exe(self) -> None:
        start = self.path_edit.text() or os.environ.get("ProgramFiles", "")
        path, _ = QFileDialog.getOpenFileName(
            self, "选择程序", start, "可执行文件 (*.exe);;所有文件 (*.*)"
        )
        if path:
            self.path_edit.setText(os.path.normpath(path))
            if not self.name_edit.text().strip():
                self.name_edit.setText(os.path.splitext(os.path.basename(path))[0])

    def _browse_wd(self) -> None:
        start = self.wd_edit.text() or os.path.dirname(self.path_edit.text()) or ""
        path = QFileDialog.getExistingDirectory(self, "选择工作目录", start)
        if path:
            self.wd_edit.setText(os.path.normpath(path))

    def _on_accept(self) -> None:
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "缺少信息", "请填写显示名。")
            return
        if not self.path_edit.text().strip():
            QMessageBox.warning(self, "缺少信息", "请选择程序路径。")
            return
        self.accept()

    def result_item(self) -> dict:
        return {
            "id": (self._original or {}).get("id") or _slugify(self.name_edit.text(), "b"),
            "display_name": self.name_edit.text().strip(),
            "exe_path": self.path_edit.text().strip(),
            "args": self.args_edit.text().strip(),
            "working_dir": self.wd_edit.text().strip(),
            "default_admin": self.admin_check.isChecked(),
            "default_checked": self.default_check.isChecked(),
        }
