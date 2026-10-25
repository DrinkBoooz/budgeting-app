"""Tests for composite ScriptAPI endpoints and serialization."""

from decimal import Decimal
import pytest
from app.api import ScriptAPI
from app.core.storage import StorageService
import tempfile
from pathlib import Path


@pytest.fixture
def api():
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage = StorageService(data_dir=Path(tmp_dir))
        script_api = ScriptAPI(window=None, storage=storage)
        yield script_api


def test_api_salary_computation(api):
    res = api.compute_salary({"monthly_basic": "30000.00", "employment_type": "private"})
    assert res["success"] is True
    data = res["data"]
    assert data["gross_income"] == "30000.00"
    assert data["sss"]["total_ee"] == "1500.00"
    assert data["philhealth"]["ee_share"] == "750.00"
    assert data["pagibig"]["ee_share"] == "200.00"
    assert data["total_statutory_deductions"] == "2450.00"
    assert data["net_pay"] == "26542.50"


def test_api_13th_month(api):
    res = api.compute_13th_month({"monthly_basic": "60000.00", "months_worked": 12})
    assert res["success"] is True
    assert res["data"]["total_bonus"] == "60000.00"
    assert res["data"]["non_taxable_bonus"] == "60000.00"
    assert res["data"]["taxable_bonus"] == "0.00"


def test_api_cutoff_schedule(api):
    res = api.compute_cutoff_schedule({
        "year": 2026,
        "month": 10,
        "daily_units": {"Mon": "4", "Wed": "5"},
        "hourly_rate": "200.00",
        "daily_food_rate": "200.00",
        "daily_transport_rate": "150.00"
    })
    assert res["success"] is True
    assert "cutoff1" in res["data"]
    assert "cutoff2" in res["data"]
    assert "monthly_totals" in res["data"]


def test_api_bills_summary(api):
    res = api.compute_bills_summary({
        "my_tenant_name": "Dan",
        "bills": [
            {"name": "Internet", "category": "Internet", "total_amount": "1600.00", "is_active": True, "active_tenants": ["Dan", "Jaco"]},
            {"name": "Rent", "category": "Rent", "total_amount": "6000.00", "is_active": True, "active_tenants": ["Dan", "Jaco"]}
        ]
    })
    assert res["success"] is True
    assert res["data"]["grand_total"] == "7600.00"
    assert res["data"]["my_total_share"] == "3800.00"


def test_api_peer_settlement(api):
    res = api.compute_peer_settlement({
        "peer_name": "Troy",
        "items": [
            {"description": "angels pizza", "total_amount": "1034.00", "paid_by": "Dan"},
            {"description": "water", "total_amount": "90.00", "paid_by": "Dan"}
        ]
    })
    assert res["success"] is True
    # 517 + 45 = 562
    assert res["data"]["dan_total_share"] == "562.00"
    assert res["data"]["net_peer_owes_dan"] == "562.00"


def test_api_groceries_remittance(api):
    res = api.compute_groceries_remittance({
        "recipient_name": "Mama",
        "items": [
            {"description": "Rice", "amount": "1200.00"},
            {"description": "Meat", "amount": "800.00"}
        ],
        "deductions": [
            {"description": "Refund", "amount": "200.00"}
        ]
    })
    assert res["success"] is True
    assert res["data"]["gross_amount"] == "2000.00"
    assert res["data"]["total_deductions"] == "200.00"
    assert res["data"]["net_transfer_amount"] == "1800.00"


def test_api_cash_flow_waterfall(api):
    res = api.compute_cash_flow_waterfall({
        "net_salary": "25000.00",
        "other_income": "5000.00",
        "monthly_bills_share": "4000.00",
        "living_budget": "6000.00",
        "peer_settlement_payable": "0.00",
        "groceries_remittance": "5000.00"
    })
    assert res["success"] is True
    assert res["data"]["total_inflow"] == "30000.00"
    assert res["data"]["total_outflow"] == "15000.00"
    assert res["data"]["net_surplus"] == "15000.00"
    assert res["data"]["savings_rate_pct"] == "50.00"


def test_api_get_app_info(api):
    res = api.get_app_info()
    assert res["success"] is True
    assert "version" in res["data"]
    assert res["data"]["version_badge"] == "Release v0.2.0"


def test_api_apt_expenses_endpoints(api):
    res_house = api.compute_house_expenditures({"items": [{"item": "Table", "count": "1", "price": "1000", "discount": "200"}]})
    assert res_house["success"] is True
    assert res_house["data"]["grand_total"] == "800.00"

    res_dentist = api.compute_dentist_tracker({
        "billed_items": [{"label": "Braces", "count": "1", "price": "37500.00"}],
        "deductibles": [{"label": "Payment", "count": "1", "price": "8000.00"}],
        "app_expenses_subtotal": "2420.00"
    })
    assert res_dentist["success"] is True
    assert res_dentist["data"]["pure_dentist_remaining"] == "29500.00"
    assert res_dentist["data"]["combined_grand_total"] == "31920.00"
    assert res_dentist["data"]["progress_bar"] == "██░░░░░░░░"


def test_api_chores_and_pajah_endpoints(api):
    res_chores = api.get_chores_summary({"month": "2026-07"})
    assert res_chores["success"] is True
    assert res_chores["data"]["chores_count"] == 16


    res_pajah = api.compute_pajah_summary({})
    assert res_pajah["success"] is True
    assert res_pajah["data"]["total_owned"] == 8
    assert res_pajah["data"]["total_potential_sum"] == "10800.00"


def test_api_recipient_and_master_matrix_endpoints(api):
    res_rec = api.compute_recipient_breakdown({"rent_amount": "7000.00", "utilities_amount": "3175.00"})
    assert res_rec["success"] is True
    assert len(res_rec["data"]["rows"]) == 3

    res_mat = api.compute_master_matrix({
        "troy_entries": [{"amount": "1000.00", "is_paid": True}],
        "spotify_amount": "57.40",
        "troy_utilities": "3175.00"
    })
    assert res_mat["success"] is True
    assert res_mat["data"]["troy"]["bank_transfer"] == "4233.00"


def test_api_unified_budget_and_ytd_endpoints(api):
    # Test compute_unified_budget
    res_uni = api.compute_unified_budget({
        "year": 2026,
        "month": 9,
        "daily_units": {"0": 9, "1": 0, "2": 10, "3": 0, "4": 10, "5": 7},
        "hourly_rate": "198.85",
        "tax_mode": "pinasweldo_private",
    })
    assert res_uni["success"] is True
    assert res_uni["data"]["b8_gross_total"] == "30622.90"
    assert res_uni["data"]["statutory_breakdown"]["sss"] == "1525.00"

    # Test compute_ytd_summary
    res_ytd = api.compute_ytd_summary({
        "history": [
            {"total": "6625.00", "per_person": "2208.33", "status": "Paid"},
            {"total": "7688.00", "per_person": "2562.67", "status": "Paid"},
        ]
    })
    assert res_ytd["success"] is True
    assert res_ytd["data"]["months_paid"] == 2

    # Test compute_cutoff_split
    res_split = api.compute_cutoff_split({
        "cutoff1_gross": "14317.20",
        "cutoff2_gross": "16305.70",
        "salary_payload": {
            "sss": {"ee_total": "1525.00"},
            "philhealth": {"ee_share": "765.57"},
            "pagibig": {"ee_share": "200.00"},
            "withholding_tax_monthly": "1094.85",
        },
        "split_method": "equal_split",
    })
    assert res_split["success"] is True
    assert res_split["data"]["total_deductions"] == "3585.42"

    # Test compute_holiday_pay
    res_hol = api.compute_holiday_pay({
        "hourly_rate": "198.85",
        "hours_worked": "8",
        "holiday_type": "Regular Holiday",
    })
    assert res_hol["success"] is True
    assert res_hol["data"]["total_holiday_pay"] == "3181.60"

    # Test sync_external_holidays
    res_ext = api.sync_external_holidays({"year": 2026})
    assert res_ext["success"] is True
    assert "source" in res_ext["data"]
    assert len(res_ext["data"]["holidays"]) >= 18


