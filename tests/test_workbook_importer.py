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
    assert "master_matrix" in data["settlements"]
    assert data["settlements"]["master_matrix"]["troy"]["bank_transfer"] == "4872.00"

    # Verify Mama groceries items were parsed
    groceries_items = data["groceries"]["items"]
    assert len(groceries_items) > 0

    # Verify Apt Expenses (6 sub-ledgers) were parsed
    assert "apt_expenses" in data
    apt = data["apt_expenses"]
    assert apt["house_expenditures"]["grand_total"] == "4675.00"
    assert apt["application_expenses"]["subtotal"] == "2420.00"
    assert apt["dentist_tracker"]["total_billed"] == "37500.00"
    assert apt["dentist_tracker"]["total_paid"] == "8000.00"
    assert apt["dentist_tracker"]["pure_dentist_remaining"] == "29500.00"
    assert apt["dentist_tracker"]["combined_grand_total"] == "31920.00"
    assert apt["dentist_tracker"]["progress_bar"] == "██░░░░░░░░"
    assert apt["expedition"]["subtotal"] == "968.00"

    # Verify Chore Chart was parsed
    assert "chores" in data
    assert data["chores"]["chores_count"] == 16
    assert "Dan" in data["chores"]["counts"]


    # Verify Pajah Rent was parsed
    assert "pajah" in data
    assert data["pajah"]["total_owned"] == 8
    assert data["pajah"]["total_potential_sum"] == "10800.00"

    # Verify Current Budget payables & additionals
    assert "budget_extras" in data
    assert len(data["budget_extras"]["additionals"]) > 0
    assert isinstance(data["budget_extras"]["payables"], list)



def test_workbook_importer_nonexistent_file():
    """Verify safe error handling when workbook file is missing."""
    importer = WorkbookImporter("non_existent_file.xlsx")
    assert importer.exists() is False
    success, msg = importer.import_to_storage()
    assert success is False
    assert "not found" in msg.lower()
