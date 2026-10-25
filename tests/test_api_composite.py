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
    assert res["data"]["version_badge"] == "Release v0.1.0"
