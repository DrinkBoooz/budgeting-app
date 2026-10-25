"""Main Desktop Application Entry Point using PyWebView and ScriptAPI."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import webview

from app.api import ScriptAPI
from app.core.storage import StorageService

logger = logging.getLogger("BudgetApp")


def get_ui_path() -> Path:
    """Resolve absolute path to ui.html, handling both dev and PyInstaller bundle modes."""
    if getattr(sys, "frozen", False):
        # PyInstaller temp folder
        base_dir = Path(sys._MEIPASS)
        ui_path = base_dir / "app" / "ui.html"
        if not ui_path.exists():
            ui_path = base_dir / "ui.html"
    else:
        # Development mode
        base_dir = Path(__file__).resolve().parent
        ui_path = base_dir / "ui.html"

    if not ui_path.exists():
        raise FileNotFoundError(f"ui.html not found at {ui_path}")
    return ui_path


def main():
    parser = argparse.ArgumentParser(description="Budgeting & Philippine Salary/Tax Suite")
    parser.add_argument("--debug", action="store_true", help="Enable developer tools and debug mode")
    parser.add_argument("--import-workbook", type=str, help="Import specified Excel workbook at startup")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    ui_file = get_ui_path()
    storage = StorageService()

    # If --import-workbook was supplied, seed data immediately
    if args.import_workbook:
        from app.core.workbook_importer import WorkbookImporter
        importer = WorkbookImporter(args.import_workbook)
        if importer.exists():
            success, msg = importer.import_to_storage(storage)
            logger.info("CLI Import: %s", msg)

    api = ScriptAPI(window=None, storage=storage)

    window = webview.create_window(
        title="Budgeting & Philippine Salary/Tax Suite",
        url=str(ui_file.resolve().as_uri()),
        js_api=api,
        width=1280,
        height=850,
        min_size=(1024, 700),
        background_color="#0b0f14",
    )
    api.set_window(window)

    logger.info("Starting PyWebView application window...")
    webview.start(debug=args.debug)


if __name__ == "__main__":
    main()
