"""Entry point: route to first-run setup, settings, or the main boot dialog."""
from __future__ import annotations

import argparse
import logging
import sys

from . import autostart, config


def _setup_logging() -> None:
    log_file = config.log_path()
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        # Rotate manually if the log gets too big (>1MB).
        if log_file.exists() and log_file.stat().st_size > 1_000_000:
            backup = log_file.with_suffix(".log.1")
            try:
                backup.unlink(missing_ok=True)
            except OSError:
                pass
            try:
                log_file.rename(backup)
            except OSError:
                pass
    except OSError:
        pass

    logging.basicConfig(
        filename=str(log_file),
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        encoding="utf-8",
    )


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="ShutStart")
    p.add_argument(
        "--settings",
        action="store_true",
        help="直接打开设置页面 (跳过主对话框)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    args = _parse_args(argv)

    _setup_logging()
    logging.getLogger(__name__).info("ShutStart starting (settings_mode=%s)", args.settings)

    from .app import create_app
    from .ui import themes
    from .ui.main_dialog import MainDialog
    from .ui.settings_dialog import SettingsDialog

    app = create_app([sys.argv[0]])

    cfg = config.load()
    is_empty = not cfg.get("a_list") and not cfg.get("b_list")

    themes.apply_theme(app, cfg.get("theme", themes.DEFAULT_THEME))

    # Keep the registry value aligned with the current exe path if user moved it.
    try:
        autostart.sync_if_moved()
    except OSError:
        logging.getLogger(__name__).exception("autostart.sync_if_moved failed")

    if args.settings or is_empty:
        banner = (
            "首次使用,请先添加要管理的软件: 上半部分(A 类)是要关闭的,"
            "下半部分(B 类)是要启动的。\n保存后下次开机会自动弹出主对话框。"
            if is_empty
            else None
        )
        dlg = SettingsDialog(banner=banner)
        dlg.exec_()
        return 0

    dlg = MainDialog()
    dlg.exec_()
    return 0


if __name__ == "__main__":
    sys.exit(main())
