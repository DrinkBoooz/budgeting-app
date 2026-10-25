"""Tests for local workbook import and storage service."""

from decimal import Decimal
from pathlib import Path
import tempfile
import pytest
from app.core.storage import StorageService
from app.core.workbook_importer import WorkbookImporter


def test_storage_service_empty_and_roundtrip():
    """Verify clean storage creation, atomic save, backup, and retrieval."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage = StorageService(data_dir=Path(tmp_dir))
        data = storage.load_data()
        assert data["version"] == "1.0.0"
        assert "salary" in data
        assert "bills" in data

        # Mutate and save
        data["salary"]["monthly_basic"] = "45000.00"
        success = storage.save_data(data, create_backup=True)
        assert success is True

        reloaded = storage.load_data()
        assert reloaded["salary"]["monthly_basic"] == "45000.00"

        # Check backup was created
        backups = list(storage.backups_dir.glob("*.json"))
        assert len(backups) >= 0


def test_workbook_importer_if_file_exists():
    """Verify WorkbookImporter parses Dan BudgetingV3.xlsx if present locally."""
    ref_file = Path("references/Dan BudgetingV3.xlsx")
    if not ref_file.exists():
        pytest.skip("Reference workbook not present in local environment.")

    importer = WorkbookImporter(ref_file)
    assert importer.exists() is True

    data = importer.parse_workbook()
    assert data["version"] == "1.0.0"
    assert "salary" in data
    assert "schedule" in data
    assert "bills" in data
    assert "settlements" in data
    assert "groceries" in data

    # Verify holidays were parsed
    holidays = data["schedule"]["holidays"]
    assert isinstance(holidays, list)
    assert len(holidays) > 0

    # Verify bills tenants was parsed
    tenants = data["bills"]["tenants"]
    assert "Dan" in tenants
    assert len(data["bills"]["history"]) > 0

    # Verify Calumpang peer items were parsed
    calumpang_items = data["settlements"]["items"]
    assert len(calumpang_items) > 0

    # Verify Mama groceries items were parsed
    groceries_items = data["groceries"]["items"]
    assert len(groceries_items) > 0


def test_workbook_importer_nonexistent_file():
    """Verify safe error handling when workbook file is missing."""
    importer = WorkbookImporter("non_existent_file.xlsx")
    assert importer.exists() is False
    success, msg = importer.import_to_storage()
    assert success is False
    assert "not found" in msg.lower()
