"""Composite ScriptAPI for PyWebView JavaScript bridge."""

from __future__ import annotations

from typing import Optional

from app.api.base import BaseAPI
from app.api.bills import BillsAPI
from app.api.budget import BudgetAPI
from app.api.config import ConfigAPI
from app.api.salary import SalaryAPI
from app.api.settlements import SettlementsAPI
from app.api.system import SystemAPI
from app.core.storage import StorageService


class ScriptAPI(SalaryAPI, BudgetAPI, BillsAPI, SettlementsAPI, ConfigAPI, SystemAPI):
    """Composite API exposed to PyWebView frontend as `window.pywebview.api`."""

    def __init__(self, window=None, storage: Optional[StorageService] = None):
        st = storage or StorageService()
        BaseAPI.__init__(self, window)
        SalaryAPI.__init__(self, window)
        BudgetAPI.__init__(self, window)
        BillsAPI.__init__(self, window)
        SettlementsAPI.__init__(self, window)
        ConfigAPI.__init__(self, window, st)
        SystemAPI.__init__(self, window, st)

    def set_window(self, window):
        """Bind window instance across all API components."""
        self.window = window
        SalaryAPI.set_window(self, window)
        BudgetAPI.set_window(self, window)
        BillsAPI.set_window(self, window)
        SettlementsAPI.set_window(self, window)
        ConfigAPI.set_window(self, window)
        SystemAPI.set_window(self, window)


__all__ = ["ScriptAPI", "BaseAPI", "SalaryAPI", "BudgetAPI", "BillsAPI", "SettlementsAPI", "ConfigAPI", "SystemAPI"]
