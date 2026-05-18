"""Local-machine startup item manager: lists Run/RunOnce + Startup-folder entries."""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .. import config, startup_inventory


DIALOG_NAME = "startup_manager"

_COLS = ("名称", "命令", "来源", "启用")


class StartupManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("本机启动项管理")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self._cfg = config.load()
        remembered = config.get_window_size(self._cfg, DIALOG_NAME)
        self.resize(*remembered) if remembered else self.resize(900, 540)

        self._entries: list[dict] = []

        outer = QVBoxLayout(self)

        title = QLabel("本机启动项 (注册表 Run/RunOnce + 启动文件夹)")
        title.setStyleSheet("font-weight: bold; padding: 2px 0;")
        outer.addWidget(title)

        filter_row = QHBoxLayout()
        self.show_service_cb = QCheckBox("显示服务类自启动项")
        self.show_service_cb.setChecked(bool(self._cfg.get("show_service_startups", False)))
        self.show_service_cb.setToolTip(
            "默认只显示主要的应用类自启动条目。勾选后,Service / 系统目录下的辅助进程也会列出。"
        )
        self.show_service_cb.stateChanged.connect(self._on_filter_changed)
        filter_row.addWidget(self.show_service_cb)

        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._reload)
        filter_row.addWidget(refresh_btn)
        filter_row.addStretch(1)
        outer.addLayout(filter_row)

        self.table = QTableWidget(0, len(_COLS))
        self.table.setHorizontalHeaderLabels(list(_COLS))
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        outer.addWidget(self.table, 1)

        hint = QLabel(
            "切换启用状态会写入 StartupApproved 注册表 (与任务管理器『启动应用』页一致),"
            "原 Run 条目保留,可随时恢复。HKLM / 公共启动项需要管理员权限,本对话框只读显示。"
        )
        hint.setStyleSheet("color: #666;")
        hint.setWordWrap(True)
        outer.addWidget(hint)

        btns = QDialogButtonBox(QDialogButtonBox.Close)
        btns.button(QDialogButtonBox.Close).setText("关闭")
        btns.rejected.connect(self.reject)
        btns.accepted.connect(self.accept)
        outer.addWidget(btns)

        self._reload()

    # -------------------- Data --------------------
    def _reload(self) -> None:
        try:
            self._entries = startup_inventory.enumerate_entries()
        except OSError as e:
            QMessageBox.critical(self, "读取失败", f"无法枚举启动项:\n{e}")
            self._entries = []
        self._render()

    # -------------------- Render --------------------
    def _render(self) -> None:
        show_service = self.show_service_cb.isChecked()
        visible = [e for e in self._entries if show_service or not e.get("is_service_like")]
        self.table.setRowCount(len(visible))
        for row, entry in enumerate(visible):
            name = entry.get("name", "")
            if entry.get("is_service_like"):
                name = f"{name}  (服务类)"
            cells = [
                QTableWidgetItem(name),
                QTableWidgetItem(entry.get("command", "")),
                QTableWidgetItem(entry.get("source", "")),
            ]
            for col, item in enumerate(cells):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if entry.get("is_service_like"):
                    item.setForeground(Qt.gray)
                self.table.setItem(row, col, item)

            cb_container = QWidget()
            cb_layout = QHBoxLayout(cb_container)
            cb_layout.setContentsMargins(0, 0, 0, 0)
            cb_layout.setAlignment(Qt.AlignCenter)
            cb = QCheckBox()
            cb.setChecked(bool(entry.get("enabled", True)))
            if not entry.get("is_writable"):
                cb.setEnabled(False)
                cb.setToolTip("需要管理员权限")
            cb.toggled.connect(
                lambda checked, e=entry, c=cb: self._on_toggle(e, checked, c)
            )
            cb_layout.addWidget(cb)
            self.table.setCellWidget(row, 3, cb_container)

    # -------------------- Actions --------------------
    def _on_filter_changed(self, _state: int) -> None:
        show = self.show_service_cb.isChecked()
        try:
            cfg = config.load()
            cfg["show_service_startups"] = bool(show)
            config.save(cfg)
        except OSError:
            pass
        self._render()

    def _on_toggle(self, entry: dict, checked: bool, cb: QCheckBox) -> None:
        try:
            startup_inventory.set_enabled(entry, checked)
        except PermissionError as e:
            QMessageBox.warning(self, "无权限", str(e))
            cb.blockSignals(True)
            cb.setChecked(not checked)
            cb.blockSignals(False)
        except OSError as e:
            QMessageBox.critical(self, "写入失败", f"无法更新启用状态:\n{e}")
            cb.blockSignals(True)
            cb.setChecked(not checked)
            cb.blockSignals(False)

    # -------------------- Lifecycle --------------------
    def done(self, result: int) -> None:
        try:
            config.set_window_size(DIALOG_NAME, self.width(), self.height())
        except OSError:
            pass
        super().done(result)
