"""Tests for Philippine Statutory Contributions (2026) and BIR TRAIN Withholding Tax."""

from decimal import Decimal
import pytest
from app.core.tax_calculator import (
    calculate_tax_and_contributions,
    calculate_sss_2026,
    calculate_philhealth_2026,
    calculate_pagibig_2026,
    calculate_bir_withholding_annual,
    calculate_bir_withholding_semi_monthly,
    calculate_13th_month_pay,
    calculate_freelance_tax,
)


class TestSSS2026:
    def test_minimum_msc(self):
        """Salaries below 5,250 get minimum MSC of 5,000."""
        res = calculate_sss_2026(Decimal("4500"))
        assert res.msc == Decimal("5000")
        assert res.ee_regular == Decimal("250.00")
        assert res.ee_mpf == Decimal("0.00")
        assert res.er_regular == Decimal("500.00")
        assert res.er_ec == Decimal("10.00")

    def test_regular_boundary_20000(self):
        """Salary of 20,000 has MSC 20,000, 0 MPF."""
        res = calculate_sss_2026(Decimal("20000"))
        assert res.msc == Decimal("20000")
        assert res.ee_regular == Decimal("1000.00")
        assert res.ee_mpf == Decimal("0.00")
        assert res.total_ee == Decimal("1000.00")

    def test_mpf_bracket_30000(self):
        """Salary of 30,000 has MSC 30,000, MPF base 10,000 (EE 500)."""
        res = calculate_sss_2026(Decimal("30000"))
        assert res.msc == Decimal("30000")
        assert res.ee_regular == Decimal("1000.00")
        assert res.ee_mpf == Decimal("500.00")
        assert res.total_ee == Decimal("1500.00")
        assert res.er_ec == Decimal("30.00")

    def test_maximum_msc_ceiling(self):
        """Salaries 34,750 and above hit ceiling MSC 35,000."""
        res = calculate_sss_2026(Decimal("45000"))
        assert res.msc == Decimal("35000")
        assert res.ee_regular == Decimal("1000.00")
        assert res.ee_mpf == Decimal("750.00")
        assert res.total_ee == Decimal("1750.00")


class TestPhilHealth2026:
    def test_floor_under_10000(self):
        """Floor is 10,000 (EE share 250.00)."""
        res = calculate_philhealth_2026(Decimal("8000"))
        assert res.ee_share == Decimal("250.00")
        assert res.er_share == Decimal("250.00")
        assert res.total_premium == Decimal("500.00")

    def test_standard_bracket(self):
        """5% total, 2.5% EE share."""
        res = calculate_philhealth_2026(Decimal("30000"))
        assert res.ee_share == Decimal("750.00")
        assert res.er_share == Decimal("750.00")
        assert res.total_premium == Decimal("1500.00")

    def test_ceiling_over_100000(self):
        """Ceiling is 100,000 (EE share 2,500.00)."""
        res = calculate_philhealth_2026(Decimal("150000"))
        assert res.ee_share == Decimal("2500.00")
        assert res.er_share == Decimal("2500.00")
        assert res.total_premium == Decimal("5000.00")


class TestPagIBIG2026:
    def test_low_income(self):
        """Salary <= 1,500 has 1% EE share."""
        res = calculate_pagibig_2026(Decimal("1200"))
        assert res.ee_share == Decimal("12.00")
        assert res.er_share == Decimal("24.00")

    def test_standard_cap(self):
        """Fund salary capped at 10,000 (EE share 2% = 200.00, ER = 200.00)."""
        res = calculate_pagibig_2026(Decimal("30000"))
        assert res.ee_share == Decimal("200.00")
        assert res.er_share == Decimal("200.00")
        assert res.total == Decimal("400.00")


class TestBIRWithholdingTax:
    def test_annual_tax_exempt_bracket(self):
        """Under 250,000 annual taxable income is 0 tax."""
        tax = calculate_bir_withholding_annual(Decimal("240000"))
        assert tax == Decimal("0.00")

    def test_annual_second_bracket(self):
        """250,000 to 400,000: 15% of excess over 250,000."""
        # 300,000 taxable -> 15% of 50,000 = 7,500.00
        tax = calculate_bir_withholding_annual(Decimal("300000"))
        assert tax == Decimal("7500.00")

    def test_semi_monthly_withholding(self):
        """Semi-monthly bracket test."""
        # Under 10,417 is 0
        assert calculate_bir_withholding_semi_monthly(Decimal("10000")) == Decimal("0.00")
        # 12,000 semi-monthly -> 15% of (12000 - 10417) = 15% of 1583 = 237.45
        tax = calculate_bir_withholding_semi_monthly(Decimal("12000"))
        assert tax == Decimal("237.45")


class Test13thMonthBonus:
    def test_bonus_under_threshold(self):
        """Bonus within 90k is completely tax-exempt."""
        res = calculate_13th_month_pay(monthly_basic=Decimal("60000"), months_worked=12)
        assert res["total_bonus"] == Decimal("60000.00")
        assert res["non_taxable_bonus"] == Decimal("60000.00")
        assert res["taxable_bonus"] == Decimal("0.00")

    def test_bonus_exceeding_threshold(self):
        """Bonus over 90k has excess subject to tax."""
        res = calculate_13th_month_pay(monthly_basic=Decimal("120000"), months_worked=12)
        assert res["total_bonus"] == Decimal("120000.00")
        assert res["non_taxable_bonus"] == Decimal("90000.00")
        assert res["taxable_bonus"] == Decimal("30000.00")


class TestFullCalculationIntegration:
    def test_private_employee_net_pay(self):
        """Full end-to-end deduction and net pay test."""
        res = calculate_tax_and_contributions(
            monthly_basic=Decimal("30000"),
            employment_type="private",
        )
        assert res.gross_income == Decimal("30000.00")
        assert res.sss_ee == Decimal("1500.00")
        assert res.philhealth_ee == Decimal("750.00")
        assert res.pagibig_ee == Decimal("200.00")
        assert res.total_statutory_deductions == Decimal("2450.00")
        # Taxable income = 30000 - 2450 = 27550 monthly -> 330,600 annual
        # Excess over 250,000 = 80,600 * 15% = 12,090 / 12 = 1,007.50 monthly tax
        assert res.withholding_tax == Decimal("1007.50")
        # Total EE deductions = 2450 + 1007.50 = 3457.50
        assert res.total_ee_deductions == Decimal("3457.50")
        assert res.net_pay == Decimal("26542.50")
        assert res.semi_monthly_net == Decimal("13271.25")
