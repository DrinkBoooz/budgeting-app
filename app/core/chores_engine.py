"""Monthly Chore Chart & Roommate Household Maintenance Engine.

Implements Dan BudgetingV3.xlsx 'Chore Chart' logic:
- 5 Household zones: Kitchen, Living Room, Bedroom, Bathroom, Maintenance
- 15 Chores with recurrence frequencies (Daily, Every other day, Every after use, Weekly, Every 2 weeks, Monthly)
- Daily assignee matrix (D for Dan, J for Jaco, T for Troy) across days 1..31
- Live completion counters (=COUNTIF per roommate) for Dashboard integration
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

HOUSEHOLD_ZONES = [
    {
        "zone": "Kitchen",
        "chores": [
            {"name": "Clean Fridge", "frequency": "Monthly"},
            {"name": "Wipe Surfaces", "frequency": "Monthly"},
            {"name": "Deep Clean Sink", "frequency": "Monthly"},
            {"name": "Wash Dishes", "frequency": "Daily"},
            {"name": "Organize Pantry", "frequency": "Weekly"},
        ],
    },
    {
        "zone": "Living Room",
        "chores": [
            {"name": "Dust Surfaces", "frequency": "Weekly"},
            {"name": "Wipe Windows", "frequency": "Weekly"},
            {"name": "Organize Setup", "frequency": "Weekly"},
        ],
    },
    {
        "zone": "Bedroom",
        "chores": [
            {"name": "Change Sheets", "frequency": "Every 2 weeks"},
            {"name": "Declutter Surfaces", "frequency": "Weekly"},
            {"name": "Organize Own Items", "frequency": "Weekly"},
        ],
    },
    {
        "zone": "Bathroom",
        "chores": [
            {"name": "Refill Water", "frequency": "Every after use"},
            {"name": "Clean Bathroom", "frequency": "Monthly"},
        ],
    },
    {
        "zone": "Maintenance",
        "chores": [
            {"name": "Mop floors", "frequency": "Weekly"},
            {"name": "Broom Floor", "frequency": "Every other day"},
            {"name": "Vacuum", "frequency": "Weekly"},
        ],
    },
]


@dataclass
class ChoreEntry:
    zone: str
    chore_name: str
    frequency: str
    # Map of day string ('1'..'31') to roommate initial ('D', 'J', 'T', or '')
    daily_assignments: Dict[str, str] = field(default_factory=dict)


class ChoreEngine:
    """Manages chore schedules and counts completions per roommate."""

    def __init__(self, entries: Optional[List[ChoreEntry]] = None, month_str: str = "2026-07"):
        self.month_str = month_str
        self.entries = entries or self.get_default_chores()

    @staticmethod
    def get_default_chores() -> List[ChoreEntry]:
        """Generate default list of 15 chores across the 5 zones."""
        res = []
        for z in HOUSEHOLD_ZONES:
            zone_name = z["zone"]
            for c in z["chores"]:
                res.append(ChoreEntry(
                    zone=zone_name,
                    chore_name=c["name"],
                    frequency=c["frequency"],
                    daily_assignments={},
                ))
        return res

    def count_by_assignee(self) -> Dict[str, int]:
        """Count total completed chores per roommate (matching COUNTIF(C4:AN24, "X"))."""
        counts = {"Dan": 0, "Jaco": 0, "Troy": 0, "Other": 0}
        for entry in self.entries:
            for day, initial in entry.daily_assignments.items():
                init = str(initial or "").strip().upper()
                if init == "D":
                    counts["Dan"] += 1
                elif init == "J":
                    counts["Jaco"] += 1
                elif init == "T":
                    counts["Troy"] += 1
                elif init:
                    counts["Other"] += 1
        return counts

    def get_summary(self) -> Dict[str, Any]:
        """Summarize chore status and counts for the UI and dashboard."""
        counts = self.count_by_assignee()
        total_completed = sum(counts.values())
        return {
            "month": self.month_str,
            "counts": counts,
            "total_completed": total_completed,
            "chores_count": len(self.entries),
            "entries": [
                {
                    "zone": e.zone,
                    "chore_name": e.chore_name,
                    "frequency": e.frequency,
                    "daily_assignments": e.daily_assignments,
                }
                for e in self.entries
            ],
        }
