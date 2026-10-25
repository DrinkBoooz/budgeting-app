"""Roommate Chore Chart API Bridge."""

from __future__ import annotations

from typing import Any, Dict, List

from app.api.base import BaseAPI
from app.core.chores_engine import ChoreEngine, ChoreEntry, HOUSEHOLD_ZONES


class ChoresAPI(BaseAPI):
    """API endpoints for roommate chore schedule and COUNTIF stats."""

    def get_chores_summary(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch chore chart entries and compute live roommate completion counters."""
        try:
            month_str = str(payload.get("month", "2026-07"))
            entries_raw = payload.get("entries")

            if entries_raw is not None:
                entries = [
                    ChoreEntry(
                        zone=e.get("zone", "General"),
                        chore_name=e.get("chore_name", "Chore"),
                        frequency=e.get("frequency", "Weekly"),
                        daily_assignments=e.get("daily_assignments", {}),
                    )
                    for e in entries_raw
                ]
                engine = ChoreEngine(entries=entries, month_str=month_str)
            else:
                engine = ChoreEngine(month_str=month_str)

            return self.success(engine.get_summary())
        except Exception as e:
            return self.error(f"Failed to get chores summary: {str(e)}")

    def get_household_zones(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch standard household chore zones and frequencies."""
        return self.success({"zones": HOUSEHOLD_ZONES})
