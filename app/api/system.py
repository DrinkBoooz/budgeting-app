"""System API Bridge for native dialogs, workbook import/export, and OS interactions."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import webview

from app.api.base import BaseAPI
from app.core.storage import StorageService
from app.core.workbook_importer import WorkbookImporter, DEFAULT_WORKBOOK_PATH

logger = logging.getLogger(__name__)

APP_VERSION = "0.1.0"
APP_NAME = "Budgeting & Salary Suite"


class SystemAPI(BaseAPI):
    """API endpoints for file dialogs, workbook import/export, and system utilities."""

    def __init__(self, window=None, storage: StorageService = None):
        super().__init__(window)
        self.storage = storage or StorageService()

    def get_app_info(self) -> Dict[str, Any]:
        """Return application metadata and version."""
        return self.success({
            "app_name": APP_NAME,
            "version": APP_VERSION,
            "version_badge": f"Release v{APP_VERSION}",
            "data_directory": str(self.storage.data_dir),
            "has_local_workbook": DEFAULT_WORKBOOK_PATH.exists(),
        })

    def import_excel_workbook(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Import data from Dan BudgetingV3.xlsx or a user-selected Excel file."""
        target_path = Path(file_path) if file_path else None

        # If no path given and window is available, open native file dialog
        if not target_path and self.window:
            try:
                selected = self.window.create_file_dialog(
                    webview.OPEN_DIALOG,
                    allow_multiple=False,
                    file_types=("Excel Files (*.xlsx;*.xls)", "All Files (*.*)"),
                )
                if selected and len(selected) > 0:
                    target_path = Path(selected[0])
            except Exception as e:
                logger.warning("Could not open native file dialog: %s", e)

        # Fallback to default reference if exists
        if not target_path:
            if DEFAULT_WORKBOOK_PATH.exists():
                target_path = DEFAULT_WORKBOOK_PATH
            else:
                return self.error("No Excel workbook path specified or selected.")

        importer = WorkbookImporter(target_path)
        if not importer.exists():
            return self.error(f"Excel workbook not found at {target_path}")

        success, msg = importer.import_to_storage(self.storage)
        if success:
            data = self.storage.load_data()
            return self.success(data=data, message=msg)
        return self.error(msg)

    def export_backup_dialog(self) -> Dict[str, Any]:
        """Open native save dialog and export current data to JSON."""
        target_path = None
        if self.window:
            try:
                selected = self.window.create_file_dialog(
                    webview.SAVE_DIALOG,
                    save_filename="budget_backup.json",
                    file_types=("JSON Files (*.json)", "All Files (*.*)"),
                )
                if selected:
                    target_path = selected if isinstance(selected, str) else selected[0]
            except Exception as e:
                logger.warning("File dialog error: %s", e)

        if not target_path:
            # Save into default data directory
            backup_path = self.storage.create_backup()
            if backup_path:
                return self.success(
                    data={"path": str(backup_path)},
                    message=f"Backup created at {backup_path.name}",
                )
            return self.error("No destination selected for backup.")

        success = self.storage.export_backup_file(target_path)
        if success:
            return self.success(
                data={"path": str(target_path)},
                message=f"Backup successfully exported to {Path(target_path).name}",
            )
        return self.error("Failed to export backup file.")

    def import_backup_dialog(self) -> Dict[str, Any]:
        """Open native open dialog and import budget JSON file."""
        target_path = None
        if self.window:
            try:
                selected = self.window.create_file_dialog(
                    webview.OPEN_DIALOG,
                    allow_multiple=False,
                    file_types=("JSON Files (*.json)", "All Files (*.*)"),
                )
                if selected and len(selected) > 0:
                    target_path = selected[0]
            except Exception as e:
                logger.warning("File dialog error: %s", e)

        if not target_path:
            return self.error("No backup file selected.")

        success = self.storage.import_backup_file(target_path)
        if success:
            data = self.storage.load_data()
            return self.success(data=data, message="Backup restored successfully")
        return self.error("Failed to restore backup.")

    def open_data_folder(self) -> Dict[str, Any]:
        """Open the local storage folder in Windows File Explorer."""
        try:
            folder = str(self.storage.data_dir.resolve())
            os.startfile(folder)
            return self.success(message=f"Opened folder {folder}")
        except Exception as e:
            return self.error(f"Failed to open folder: {str(e)}")
