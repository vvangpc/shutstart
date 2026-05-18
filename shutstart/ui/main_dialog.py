"""Main boot-time dialog: left = A (close), right = B (launch). One 确认 button."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .. import config, killer, launcher
from .settings_dialog import SettingsDialog

log = logging.getLogger(__name__)


@dataclass
class _ARow:
    item: dict
    check: QCheckBox
    running_count: int


@dataclass
class _BRow:
    item: dict
    check: QCheckBox
    admin_check: QCheckBox
    exe_exists: bool


DIALOG_NAME = "main"


class MainDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ShutStart")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self._cfg = config.load()
        remembered = config.get_window_size(self._cfg, DIALOG_NAME)
        self.resize(*remembered) if remembered else self.resize(760, 440)
        self._a_rows: list[_ARow] = []
        self._b_rows: list[_BRow] = []
        self._scan = killer.scan(self._cfg.get("a_list", []))

        outer = QVBoxLayout(self)

        # Top bar: title + Settings button.
        top = QHBoxLayout()
        title = QLabel("ShutStart — 开机启动管理")
        title.setStyleSheet("font-size: 13pt; font-weight: bold;")
        top.addWidget(title)
        top.addStretch(1)
        settings_btn = QPushButton("设置…")
        settings_btn.clicked.connect(self._open_settings)
        top.addWidget(settings_btn)
        outer.addLayout(top)

        # Side-by-side groups in a splitter.
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_a_group())
        splitter.addWidget(self._build_b_group())
        splitter.setSizes([380, 380])
        outer.addWidget(splitter, 1)

        # Bottom buttons.
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        confirm_btn = QPushButton("确认")
        confirm_btn.setDefault(True)
        confirm_btn.setMinimumWidth(110)
        confirm_btn.clicked.connect(self._on_confirm)
        cancel_btn = QPushButton("取消")
        cancel_btn.setMinimumWidth(80)
        cancel_btn.clicked.connect(self.reject)
        bottom.addWidget(confirm_btn)
        bottom.addWidget(cancel_btn)
        outer.addLayout(bottom)

    # -------------------- A group (left) --------------------
    def _build_a_group(self) -> QGroupBox:
        group = QGroupBox("关闭以下软件 (A 类)")
        v = QVBoxLayout(group)

        # Header row mirrors B group's "管理员" column header for first-row alignment.
        header = QHBoxLayout()
        header.addWidget(QLabel(""), 1)
        state_header = QLabel("状态")
        state_header.setStyleSheet("color: #888; background: transparent;")
        state_header.setFixedWidth(140)
        state_header.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header.addWidget(state_header, 0)
        v.addLayout(header)

        a_items = self._cfg.get("a_list", [])
        if not a_items:
            v.addWidget(self._empty_label("暂无关闭项,请打开设置添加。"))
            v.addStretch(1)
            return group

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(2, 2, 2, 2)
        inner_layout.setSpacing(4)

        for item in a_items:
            count = self._scan.count(item["id"])
            running = count > 0
            row = QHBoxLayout()
            cb = QCheckBox(item.get("display_name", "(未命名)"))
            cb.setChecked(bool(item.get("default_checked", True)) and running)
            cb.setEnabled(running)
            if running:
                status = f"运行中 ({count} 个实例)" if count > 1 else "运行中"
                status_label = QLabel(f"({status})")
                status_label.setStyleSheet("color: #2a7f3e; background: transparent;")
            else:
                status_label = QLabel("(未运行)")
                status_label.setStyleSheet("color: #999; background: transparent;")
            status_label.setFixedWidth(140)
            status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row.addWidget(cb, 1)
            row.addWidget(status_label, 0)
            inner_layout.addLayout(row)
            self._a_rows.append(_ARow(item=item, check=cb, running_count=count))

        inner_layout.addStretch(1)
        scroll.setWidget(inner)
        v.addWidget(scroll)
        return group

    # -------------------- B group (right) --------------------
    def _build_b_group(self) -> QGroupBox:
        group = QGroupBox("启动以下软件 (B 类)")
        v = QVBoxLayout(group)

        # Header row for the "管理员" column. Built before items so empty B and empty A
        # panels still align with each other.
        header = QHBoxLayout()
        header.addWidget(QLabel(""), 1)
        admin_header = QLabel("管理员")
        admin_header.setStyleSheet("color: #888; background: transparent;")
        admin_header.setFixedWidth(60)
        admin_header.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        header.addWidget(admin_header, 0)
        v.addLayout(header)

        b_items = self._cfg.get("b_list", [])
        if not b_items:
            v.addWidget(self._empty_label("暂无启动项,请打开设置添加。"))
            v.addStretch(1)
            return group

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(2, 2, 2, 2)
        inner_layout.setSpacing(4)

        for item in b_items:
            exe = item.get("exe_path", "") or ""
            exists = bool(exe) and os.path.isfile(exe)
            row = QHBoxLayout()

            cb = QCheckBox(item.get("display_name", "(未命名)"))
            cb.setChecked(bool(item.get("default_checked", True)) and exists)
            cb.setEnabled(exists)
            if not exists:
                cb.setText(cb.text() + "  (路径不存在)")
                cb.setStyleSheet("color: #b22222;")
            row.addWidget(cb, 1)

            admin_cb = QCheckBox()
            admin_cb.setChecked(bool(item.get("default_admin", False)) and exists)
            admin_cb.setEnabled(exists)
            admin_cb.setFixedWidth(60)
            admin_cb.setStyleSheet("QCheckBox{margin-left:20px;}")
            row.addWidget(admin_cb, 0, Qt.AlignCenter)

            inner_layout.addLayout(row)
            self._b_rows.append(
                _BRow(item=item, check=cb, admin_check=admin_cb, exe_exists=exists)
            )

        inner_layout.addStretch(1)
        scroll.setWidget(inner)
        v.addWidget(scroll)
        return group

    def _empty_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color:#999; padding:18px;")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        return lbl

    # -------------------- Actions --------------------
    def _open_settings(self) -> None:
        dlg = SettingsDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            QMessageBox.information(
                self,
                "已保存",
                "设置已保存。请关闭当前窗口后重新启动 ShutStart 以应用新配置。",
            )

    def _on_confirm(self) -> None:
        a_to_kill: list = []
        for row in self._a_rows:
            if row.check.isChecked() and row.running_count > 0:
                a_to_kill.extend(self._scan.by_id.get(row.item["id"], []))

        b_to_launch: list[tuple[dict, bool]] = []
        for row in self._b_rows:
            if row.check.isChecked() and row.exe_exists:
                b_to_launch.append((row.item, row.admin_check.isChecked()))

        if not a_to_kill and not b_to_launch:
            QMessageBox.information(self, "没有可执行的操作", "你没有勾选任何项目。")
            return

        progress = QProgressDialog("正在执行…", "", 0, 0, self)
        progress.setWindowTitle("ShutStart")
        progress.setCancelButton(None)
        progress.setWindowModality(Qt.ApplicationModal)
        progress.show()
        # Let Qt paint before we block on kill/launch.
        from PyQt5.QtWidgets import QApplication

        QApplication.processEvents()

        kill_report = killer.kill(a_to_kill) if a_to_kill else None
        launch_report = launcher.launch_many(b_to_launch) if b_to_launch else None

        progress.close()
        self._show_summary(kill_report, launch_report)

    def done(self, result: int) -> None:
        try:
            config.set_window_size(DIALOG_NAME, self.width(), self.height())
        except OSError:
            log.exception("Failed to persist main dialog size")
        super().done(result)

    def _show_summary(self, kill_report, launch_report) -> None:
        parts: list[str] = []
        if kill_report is not None:
            parts.append(f"已关闭 {kill_report.killed} 个进程")
            if kill_report.failed:
                parts.append(f"{kill_report.failed} 个未能关闭 (可能需要管理员权限)")
        if launch_report is not None:
            parts.append(f"已启动 {launch_report.launched} 个程序")
            if launch_report.uac_denied:
                parts.append(f"{launch_report.uac_denied} 个被用户拒绝 UAC")
            if launch_report.skipped_missing:
                parts.append(f"{launch_report.skipped_missing} 个路径无效已跳过")
            if launch_report.failed:
                parts.append(f"{launch_report.failed} 个启动失败")
        msg = " | ".join(parts) if parts else "没有执行任何操作"

        toast = QDialog(self)
        toast.setWindowTitle("ShutStart")
        toast.setWindowFlags(
            Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        lay = QVBoxLayout(toast)
        lbl = QLabel(msg)
        lbl.setStyleSheet(
            "background:#2b2b2b; color:#fff; padding:14px 22px; border-radius:6px;"
            " font-size:11pt;"
        )
        lbl.setAlignment(Qt.AlignCenter)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(lbl)
        toast.adjustSize()
        # Center over main dialog.
        geom = self.frameGeometry()
        toast.move(
            geom.center().x() - toast.width() // 2,
            geom.center().y() - toast.height() // 2,
        )
        toast.show()

        QTimer.singleShot(1500, toast.close)
        QTimer.singleShot(1500, self.accept)
