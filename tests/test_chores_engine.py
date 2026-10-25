"""Unit tests for Chore Chart and COUNTIF completion counters."""

import pytest
from app.core.chores_engine import ChoreEngine, ChoreEntry, HOUSEHOLD_ZONES


def test_default_chores_structure():
    """Verify 15 chores across 5 household zones."""
    engine = ChoreEngine()
    summary = engine.get_summary()
    assert summary["chores_count"] == 16
    assert len(HOUSEHOLD_ZONES) == 5

    zones = [z["zone"] for z in HOUSEHOLD_ZONES]
    assert "Kitchen" in zones
    assert "Living Room" in zones
    assert "Bedroom" in zones
    assert "Bathroom" in zones
    assert "Maintenance" in zones


def test_chore_assignee_counts():
    """Verify live COUNTIF per roommate (D, J, T)."""
    entries = [
        ChoreEntry(zone="Kitchen", chore_name="Wash Dishes", frequency="Daily", daily_assignments={"1": "D", "2": "D", "3": "J"}),
        ChoreEntry(zone="Bathroom", chore_name="Clean Bathroom", frequency="Monthly", daily_assignments={"15": "T"}),
        ChoreEntry(zone="Maintenance", chore_name="Mop floors", frequency="Weekly", daily_assignments={"7": "J", "14": "T", "21": "D"}),
    ]
    engine = ChoreEngine(entries=entries)
    counts = engine.count_by_assignee()
    # Dan: 1 (Wash Dishes day 1) + 1 (Wash Dishes day 2) + 1 (Mop floors day 21) = 3
    # Jaco: 1 (Wash Dishes day 3) + 1 (Mop floors day 7) = 2
    # Troy: 1 (Clean Bathroom day 15) + 1 (Mop floors day 14) = 2
    assert counts["Dan"] == 3
    assert counts["Jaco"] == 2
    assert counts["Troy"] == 2
    summary = engine.get_summary()
    assert summary["total_completed"] == 7
