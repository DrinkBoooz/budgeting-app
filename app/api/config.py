"""Configuration and Persistent User State API Bridge."""

from __future__ import annotations

from typing import Any, Dict

from app.api.base import BaseAPI
from app.core.storage import StorageService


class ConfigAPI(BaseAPI):
    """API endpoints for reading and updating user profile, settings, and application data."""

    def __init__(self, window=None, storage: StorageService = None):
        super().__init__(window)
        self.storage = storage or StorageService()

    def get_user_data(self) -> Dict[str, Any]:
        """Fetch all persistent user budget data."""
        try:
            data = self.storage.load_data()
            return self.success(data)
        except Exception as e:
            return self.error(f"Failed to load user data: {str(e)}")

    def save_user_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Save user budget data."""
        try:
            success = self.storage.save_data(payload, create_backup=True)
            if success:
                return self.success(message="Data saved successfully")
            return self.error("Failed to write budget data to storage")
        except Exception as e:
            return self.error(f"Failed to save user data: {str(e)}")

    def get_app_config(self) -> Dict[str, Any]:
        """Fetch application configuration."""
        try:
            cfg = self.storage.load_config()
            return self.success(cfg)
        except Exception as e:
            return self.error(f"Failed to load config: {str(e)}")

    def save_app_config(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Save application configuration."""
        try:
            success = self.storage.save_config(payload)
            if success:
                return self.success(message="Config saved successfully")
            return self.error("Failed to write config to storage")
        except Exception as e:
            return self.error(f"Failed to save config: {str(e)}")
