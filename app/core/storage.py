"""Local App Storage and Persistence Service.

Provides secure, atomic local persistence for user budget data, configuration,
and historical snapshots in the user's OS application data directory or a local
fallback directory. Strict isolation from source control is enforced.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

APP_NAME = "PersonalBudgetSuite"
DATA_FILENAME = "budget_data.json"
CONFIG_FILENAME = "app_config.json"


def get_default_data_dir() -> Path:
    """Determine the platform-appropriate local data storage directory."""
    appdata = os.getenv("APPDATA")
    if appdata:
        base_dir = Path(appdata) / APP_NAME
    else:
        # Fallback to user home directory or local project .user_data
        home = Path.home()
        base_dir = home / f".{APP_NAME.lower()}"

    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


class DecimalEncoder(json.JSONEncoder):
    """JSON Encoder that converts Decimal instances to strings or floats."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, (datetime,)):
            return obj.isoformat()
        return super().default(obj)


class StorageService:
    """Service for persisting and retrieving user budget models and app settings."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or get_default_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.data_path = self.data_dir / DATA_FILENAME
        self.config_path = self.data_dir / CONFIG_FILENAME
        self.backups_dir = self.data_dir / "backups"
        self.backups_dir.mkdir(parents=True, exist_ok=True)

    def load_data(self) -> Dict[str, Any]:
        """Load user budget data from storage.

        Returns empty template if not found.
        """
        if not self.data_path.exists():
            return self.get_empty_data_template()

        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error("Failed to load budget data from %s: %s", self.data_path, e)
            return self.get_empty_data_template()

    def save_data(self, data: Dict[str, Any], create_backup: bool = True) -> bool:
        """Atomically save user budget data.

        Optionally creates a timestamped backup first.
        """
        try:
            if create_backup and self.data_path.exists():
                self.create_backup()

            temp_path = self.data_dir / f"{DATA_FILENAME}.tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, cls=DecimalEncoder)

            # Atomic replace
            temp_path.replace(self.data_path)
            return True
        except Exception as e:
            logger.error("Failed to save budget data: %s", e)
            return False

    def create_backup(self) -> Optional[Path]:
        """Create a timestamped backup of the current budget file."""
        if not self.data_path.exists():
            return None
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backups_dir / f"budget_backup_{timestamp}.json"
        try:
            shutil.copy2(self.data_path, backup_file)
            return backup_file
        except Exception as e:
            logger.error("Backup creation failed: %s", e)
            return None

    def export_backup_file(self, target_filepath: str | Path) -> bool:
        """Export current data to a user-chosen destination file."""
        try:
            target = Path(target_filepath)
            target.parent.mkdir(parents=True, exist_ok=True)
            if self.data_path.exists():
                shutil.copy2(self.data_path, target)
            else:
                with open(target, "w", encoding="utf-8") as f:
                    json.dump(self.get_empty_data_template(), f, indent=2)
            return True
        except Exception as e:
            logger.error("Failed to export backup: %s", e)
            return False

    def import_backup_file(self, source_filepath: str | Path) -> bool:
        """Import user budget data from an external backup JSON file."""
        source = Path(source_filepath)
        if not source.exists():
            return False
        try:
            with open(source, "r", encoding="utf-8") as f:
                content = json.load(f)
            # Basic validation
            if not isinstance(content, dict) or "version" not in content:
                logger.warning("Imported file does not appear to be a valid budget state.")
            return self.save_data(content, create_backup=True)
        except Exception as e:
            logger.error("Failed to import backup: %s", e)
            return False

    def load_config(self) -> Dict[str, Any]:
        """Load application configuration."""
        if not self.config_path.exists():
            return self.get_default_config()
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return self.get_default_config()

    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save application configuration."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            logger.error("Failed to save config: %s", e)
            return False

    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        return {
            "theme": "emerald-dark",
            "currency_symbol": "₱",
            "tax_year": 2026,
            "round_splits_up": True,
            "auto_backup_on_save": True,
            "default_tenants": ["Dan", "Occupant 2", "Occupant 3"],
            "my_tenant_name": "Dan",
        }

    @staticmethod
    def get_empty_data_template() -> Dict[str, Any]:
        """Returns the default clean schema template for new users."""
        return {
            "version": "1.0.0",
            "updated_at": datetime.now().isoformat(),
            "profile": {
                "name": "Dan",
                "employment_type": "private",
                "monthly_basic": "0.00",
                "allowances": "0.00",
            },
            "salary": {
                "monthly_basic": "0.00",
                "allowances": "0.00",
                "employment_type": "private",
                "overtime": "0.00",
                "night_diff": "0.00",
                "custom_deductions": [],
            },
            "schedule": {
                "daily_units": {
                    "Mon": "0",
                    "Tue": "0",
                    "Wed": "0",
                    "Thu": "0",
                    "Fri": "0",
                    "Sat": "0",
                    "Sun": "0",
                },
                "daily_food_rate": "200.00",
                "daily_transport_rate": "150.00",
                "holidays": [],
            },
            "bills": {
                "tenants": ["Dan", "Roommate 1", "Roommate 2"],
                "my_tenant_name": "Dan",
                "items": [],
                "history": [],
            },
            "settlements": {
                "peer_name": "Calumpang Peer",
                "dan_ratio": "0.50",
                "items": [],
            },
            "groceries": {
                "recipient_name": "Mama",
                "items": [],
                "deductions": [],
            },
        }
