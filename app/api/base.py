"""Base API class for PyWebView JavaScript bridge."""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class BaseAPI:
    """Base API providing standardized response formatting and window reference."""

    def __init__(self, window=None):
        self.window = window

    def set_window(self, window):
        """Bind the PyWebView window instance."""
        self.window = window

    @staticmethod
    def success(data: Any = None, message: str = "") -> Dict[str, Any]:
        """Format a successful JSON response."""
        return {
            "success": True,
            "data": data,
            "message": message,
            "error": None,
        }

    @staticmethod
    def error(message: str, code: str = "ERROR", data: Any = None) -> Dict[str, Any]:
        """Format an error JSON response."""
        logger.error("API Error [%s]: %s", code, message)
        return {
            "success": False,
            "data": data,
            "message": message,
            "error": {"code": code, "message": message},
        }
