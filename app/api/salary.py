"""Salary and Philippine Statutory Contribution API Bridge."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional

from app.api.base import BaseAPI
from app.core.decimal_utils import to_decimal
from app.core.tax_calculator import (
    calculate_tax_and_contributions,
    calculate_13th_month_pay,
    calculate_freelance_tax,
)


class SalaryAPI(BaseAPI):
    """API endpoints for salary, statutory contributions, and BIR TRAIN tax."""

    def compute_salary(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Compute full take-home pay, SSS, PhilHealth, Pag-IBIG, and tax."""
        try:
            monthly_basic = to_decimal(payload.get("monthly_basic", 0))
            employment_type = str(payload.get("employment_type", "private")).lower()
            taxable_allowances = to_decimal(payload.get("taxable_allowances", 0))
            non_taxable_allowances = to_decimal(payload.get("non_taxable_allowances", 0))
            other_deductions = to_decimal(payload.get("other_deductions", 0))
            withholding_method = str(payload.get("withholding_method", "annualized"))
            freelance_mode = payload.get("freelance_mode", None)

            res = calculate_tax_and_contributions(
                monthly_basic=monthly_basic,
                employment_type=employment_type,
                taxable_allowances=taxable_allowances,
                non_taxable_allowances=non_taxable_allowances,
                other_deductions=other_deductions,
                withholding_method=withholding_method,
                freelance_mode=freelance_mode,
            )

            raw = res.raw_payload
            # Format numbers to string for JSON serialization
            serialized = {
                "gross_income": str(res.gross_income),
                "basic_salary": str(res.basic_salary),
                "taxable_allowances": str(res.taxable_allowances),
                "non_taxable_allowances": str(res.non_taxable_allowances),
                "sss": {
                    "msc": str(raw["sss"]["msc"]),
                    "ee_regular": str(raw["sss"]["ee_regular"]),
                    "ee_mpf": str(raw["sss"]["ee_mpf"]),
                    "total_ee": str(res.sss_ee),
                    "er_regular": str(raw["sss"]["er_regular"]),
                    "er_mpf": str(raw["sss"]["er_mpf"]),
                    "total_er": str(raw["sss"]["er_total"]),
                    "er_ec": str(raw["sss"]["er_ec"]),
                    "total_contribution": str(raw["sss"]["total_contribution"]),
                },
                "philhealth": {
                    "base": str(raw["philhealth"]["base"]),
                    "ee_share": str(res.philhealth_ee),
                    "er_share": str(raw["philhealth"]["er_share"]),
                    "total": str(raw["philhealth"]["total"]),
                },
                "pagibig": {
                    "fund_salary": str(raw["pagibig"]["fund_salary"]),
                    "ee_share": str(res.pagibig_ee),
                    "er_share": str(raw["pagibig"]["er_share"]),
                    "total": str(raw["pagibig"]["total"]),
                },
                "gsis": {
                    "ee_share": str(res.gsis_ee),
                    "er_share": str(raw["gsis"]["er_share"]),
                    "total": str(raw["gsis"]["total"]),
                },
                "total_statutory_deductions": str(res.total_statutory_deductions),
                "taxable_income_annual": str(raw["taxable_income_annual"]),
                "withholding_tax_monthly": str(res.withholding_tax),
                "percentage_tax_monthly": str(raw["percentage_tax_monthly"]),
                "total_ee_deductions": str(res.total_ee_deductions),
                "net_pay": str(res.net_pay),
                "semi_monthly_net": str(res.semi_monthly_net),
                "freelance_analysis": raw["freelance_analysis"],
            }
            return self.success(serialized)
        except Exception as e:
            return self.error(f"Failed to calculate salary: {str(e)}")

    def compute_13th_month(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate 13th month bonus with ₱90,000 exemption threshold."""
        try:
            monthly_basic = to_decimal(payload.get("monthly_basic", 0))
            months_worked = to_decimal(payload.get("months_worked", 12))
            res = calculate_13th_month_pay(monthly_basic, months_worked)
            return self.success({
                "total_bonus": str(res["total_bonus"]),
                "non_taxable_bonus": str(res["non_taxable_bonus"]),
                "taxable_bonus": str(res["taxable_bonus"]),
            })
        except Exception as e:
            return self.error(f"Failed to calculate 13th month: {str(e)}")
