"""Settings dialog: side-by-side A/B lists, shared right-side button column."""
from __future__ import annotations

import copy
import os
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QAction,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .. import autostart, config
from . import themes
from .item_editor import AItemEditor, BItemEditor


DIALOG_NAME = "settings"


class _DeletableListWidget(QListWidget):
    """QListWidget that emits a custom signal when Delete is pressed."""

    def __init__(self, on_delete_key, parent=None):
        super().__init__(parent)
        self._on_delete_key = on_delete_key

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace) and self.currentRow() >= 0:
            self._on_delete_key()
            return
        super().keyPressEvent(event)


class SettingsDialog(QDialog):
    def __init__(self, parent=None, banner: Optional[str] = None):
        super().__init__(parent)
        self.setWindowTitle("ShutStart 设置")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self._cfg = config.load()
        remembered = config.get_window_size(self._cfg, DIALOG_NAME)
        self.resize(*remembered) if remembered else self.resize(820, 520)

        self._a_items: list[dict] = copy.deepcopy(self._cfg.get("a_list", []))
        self._b_items: list[dict] = copy.deepcopy(self._cfg.get("b_list", []))
        self._current_kind: Optional[str] = None  # "A" / "B" / None

        # Track the theme that was active when the dialog opened, for revert-on-cancel.
        self._original_theme = self._cfg.get("theme", themes.DEFAULT_THEME)

        outer = QVBoxLayout(self)

        if banner:
            lbl = QLabel(banner)
            lbl.setStyleSheet(
                "background:#fff4d6; border:1px solid #e0c060; padding:6px;"
            )
            lbl.setWordWrap(True)
            outer.addWidget(lbl)

        # Autostart toggle + theme selector row.
        top_row = QHBoxLayout()
        self.autostart_cb = QCheckBox("开机自动启动 ShutStart (写入 HKCU\\Run 注册表)")
        self.autostart_cb.setChecked(bool(self._cfg.get("autostart_enabled", True)))
        top_row.addWidget(self.autostart_cb)
        top_row.addStretch(1)

        theme_label = QLabel("外观主题:")
        theme_label.setStyleSheet("background: transparent;")
        top_row.addWidget(theme_label)
        self.theme_combo = QComboBox()
        for key, meta in themes.THEMES.items():
            self.theme_combo.addItem(meta["display_name"], userData=key)
        idx = self.theme_combo.findData(self._original_theme)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        top_row.addWidget(self.theme_combo)

        outer.addLayout(top_row)

        # Middle: two lists in a splitter + button column on the right.
        middle = QHBoxLayout()
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_list_panel("A"))
        splitter.addWidget(self._build_list_panel("B"))
        splitter.setSizes([400, 400])
        middle.addWidget(splitter, 1)
        middle.addLayout(self._build_button_column(), 0)
        outer.addLayout(middle, 1)

        # Bottom hint.
        hint = QLabel(
            "提示: A 类是开机后要关闭的进程 (例如 AnyDesk、向日葵);"
            "B 类是想按需启动的程序 (例如 Clash、v2rayN)。"
            " 双击列表项 = 编辑, Delete 键 = 删除。"
        )
        hint.setStyleSheet("color: #666;")
        hint.setWordWrap(True)
        outer.addWidget(hint)

        # Bottom buttons.
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("确定")
        btns.button(QDialogButtonBox.Cancel).setText("取消")
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        outer.addWidget(btns)

        self._refresh_a()
        self._refresh_b()
        self._update_button_states()

    # -------------------- Panel/button builders --------------------
    def _build_list_panel(self, kind: str) -> QWidget:
        panel = QWidget()
        v = QVBoxLayout(panel)
        v.setContentsMargins(0, 0, 0, 0)
        header = QLabel(
            "关闭列表 (A 类)" if kind == "A" else "启动列表 (B 类)"
        )
        header.setStyleSheet("font-weight: bold; padding: 2px 0;")
        v.addWidget(header)

        if kind == "A":
            self.a_list = _DeletableListWidget(self._on_delete)
            lw = self.a_list
        else:
            self.b_list = _DeletableListWidget(self._on_delete)
            lw = self.b_list

        lw.setSelectionMode(QAbstractItemView.SingleSelection)
        lw.setAlternatingRowColors(True)
        lw.setFrameShape(QFrame.StyledPanel)
        lw.itemDoubleClicked.connect(self._on_edit)
        lw.itemSelectionChanged.connect(
            lambda k=kind: self._on_selection_changed(k)
        )
        v.addWidget(lw, 1)
        return panel

    def _build_button_column(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(6)

        # 新增 with dropdown menu.
        self.add_btn = QToolButton()
        self.add_btn.setText("新增")
        self.add_btn.setPopupMode(QToolButton.InstantPopup)
        self.add_btn.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.add_btn.setMinimumWidth(96)
        menu = QMenu(self.add_btn)
        act_a = QAction("新增关闭项 (A 类)…", self)
        act_a.triggered.connect(lambda: self._on_add("A"))
        act_b = QAction("新增启动项 (B 类)…", self)
        act_b.triggered.connect(lambda: self._on_add("B"))
        menu.addAction(act_a)
        menu.addAction(act_b)
        self.add_btn.setMenu(menu)
        col.addWidget(self.add_btn)

        self.edit_btn = QPushButton("编辑…")
        self.edit_btn.setMinimumWidth(96)
        self.edit_btn.clicked.connect(self._on_edit)
        col.addWidget(self.edit_btn)

        self.del_btn = QPushButton("删除")
        self.del_btn.setMinimumWidth(96)
        self.del_btn.clicked.connect(self._on_delete)
        col.addWidget(self.del_btn)

        col.addStretch(1)
        return col

    # -------------------- Selection / state --------------------
    def _on_selection_changed(self, kind: str) -> None:
        # Mutual-exclusion: when a row in one list becomes selected,
        # clear the other list's selection so 编辑/删除 has a single target.
        other_list = self.b_list if kind == "A" else self.a_list
        if self._lw_for(kind).currentRow() >= 0:
            self._current_kind = kind
            other_list.blockSignals(True)
            other_list.clearSelection()
            other_list.setCurrentRow(-1)
            other_list.blockSignals(False)
        else:
            # Lost selection in this list — check if the other list has one.
            if other_list.currentRow() < 0:
                self._current_kind = None
        self._update_button_states()

    def _update_button_states(self) -> None:
        has_target = self._current_kind is not None and (
            self._lw_for(self._current_kind).currentRow() >= 0
        )
        self.edit_btn.setEnabled(has_target)
        self.del_btn.setEnabled(has_target)

    def _lw_for(self, kind: str) -> QListWidget:
        return self.a_list if kind == "A" else self.b_list

    def _items_for(self, kind: str) -> list[dict]:
        return self._a_items if kind == "A" else self._b_items

    # -------------------- List rendering --------------------
    def _refresh_a(self) -> None:
        self.a_list.blockSignals(True)
        self.a_list.clear()
        for it in self._a_items:
            label = it.get("display_name", "(未命名)")
            procs = ", ".join(it.get("process_names", []))
            if procs:
                label = f"{label}  —  {procs}"
            self.a_list.addItem(QListWidgetItem(label))
        self.a_list.blockSignals(False)

    def _refresh_b(self) -> None:
        self.b_list.blockSignals(True)
        self.b_list.clear()
        for it in self._b_items:
            label = it.get("display_name", "(未命名)")
            exe = it.get("exe_path", "")
            tags = []
            if it.get("default_admin"):
                tags.append("管理员")
            if not exe or not os.path.isfile(exe):
                tags.append("路径不存在")
            suffix = f"  [{' / '.join(tags)}]" if tags else ""
            label = f"{label}  —  {exe}{suffix}"
            self.b_list.addItem(QListWidgetItem(label))
        self.b_list.blockSignals(False)

    # -------------------- CRUD actions --------------------
    def _on_add(self, kind: str) -> None:
        editor = AItemEditor(self) if kind == "A" else BItemEditor(self)
        if editor.exec_() != QDialog.Accepted:
            return
        items = self._items_for(kind)
        items.append(editor.result_item())
        if kind == "A":
            self._refresh_a()
        else:
            self._refresh_b()
        lw = self._lw_for(kind)
        lw.setCurrentRow(len(items) - 1)
        self._current_kind = kind
        self._update_button_states()

    def _on_edit(self, *_args) -> None:
        kind = self._current_kind
        if kind is None:
            return
        lw = self._lw_for(kind)
        row = lw.currentRow()
        if row < 0:
            return
        items = self._items_for(kind)
        current = items[row]
        editor = AItemEditor(self, item=current) if kind == "A" else BItemEditor(self, item=current)
        if editor.exec_() != QDialog.Accepted:
            return
        items[row] = editor.result_item()
        if kind == "A":
            self._refresh_a()
        else:
            self._refresh_b()
        lw.setCurrentRow(row)
        self._update_button_states()

    def _on_delete(self) -> None:
        kind = self._current_kind
        if kind is None:
            return
        lw = self._lw_for(kind)
        row = lw.currentRow()
        if row < 0:
            return
        items = self._items_for(kind)
        name = items[row].get("display_name", "")
        if (
            QMessageBox.question(
                self,
                "确认删除",
                f"确定要删除 '{name}' 吗?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            != QMessageBox.Yes
        ):
            return
        items.pop(row)
        if kind == "A":
            self._refresh_a()
        else:
            self._refresh_b()
        if items:
            lw.setCurrentRow(min(row, len(items) - 1))
        else:
            lw.setCurrentRow(-1)
            self._current_kind = None
        self._update_button_states()

    # -------------------- Theme --------------------
    def _on_theme_changed(self, _idx: int) -> None:
        """Live-preview the new theme without persisting yet."""
        key = self.theme_combo.currentData()
        if not key:
            return
        app = QApplication.instance()
        if app is not None:
            themes.apply_theme(app, key)

    # -------------------- Save --------------------
    def _on_ok(self) -> None:
        self._cfg["a_list"] = self._a_items
        self._cfg["b_list"] = self._b_items
        self._cfg["autostart_enabled"] = self.autostart_cb.isChecked()
        self._cfg["theme"] = self.theme_combo.currentData() or themes.DEFAULT_THEME
        try:
            config.save(self._cfg)
        except OSError as e:
            QMessageBox.critical(self, "保存失败", f"无法写入配置文件:\n{e}")
            return

        try:
            if self._cfg["autostart_enabled"]:
                autostart.enable()
            else:
                autostart.disable()
        except OSError as e:
            QMessageBox.warning(
                self, "自启设置失败", f"配置已保存,但写入注册表失败:\n{e}"
            )
        # Theme is already applied live; OK just persists. Update _original_theme so
        # done() doesn't try to revert.
        self._original_theme = self._cfg["theme"]
        self.accept()

    # -------------------- Lifecycle hooks --------------------
    def done(self, result: int) -> None:
        # Revert theme on cancel/close-X if user changed it but didn't save.
        current_theme = self.theme_combo.currentData() if hasattr(self, "theme_combo") else None
        if result != QDialog.Accepted and current_theme and current_theme != self._original_theme:
            app = QApplication.instance()
            if app is not None:
                themes.apply_theme(app, self._original_theme)
        # Persist window size regardless of accept/reject.
        try:
            config.set_window_size(DIALOG_NAME, self.width(), self.height())
        except OSError:
            pass
        super().done(result)
