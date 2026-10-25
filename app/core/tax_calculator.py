"""
Philippine Statutory Contributions and BIR Withholding Tax Calculator.
Reverse-engineered from Pinasweldo (2026 Rates) with 100% mathematical parity.
Strictly uses Decimal math with zero floating-point imprecision.
"""
from decimal import Decimal, ROUND_DOWN
from typing import Dict, Any, Optional
from .decimal_utils import to_decimal, quantize_currency, ZERO

# ---------------------------------------------------------------------------
# SSS Constants (RA 11199 & SSS Circular 2024-006)
# ---------------------------------------------------------------------------
SSS_RATE = Decimal("0.15")
SSS_EE_RATE = Decimal("0.05")
SSS_ER_RATE = Decimal("0.10")
SSS_MSC_FLOOR = Decimal("5000")
SSS_MSC_CEILING = Decimal("35000")
SSS_MSC_STEP = Decimal("500")
SSS_REGULAR_CEILING = Decimal("20000")
SSS_EC_THRESHOLD = Decimal("15000")
SSS_EC_LOW = Decimal("10")
SSS_EC_HIGH = Decimal("30")

# ---------------------------------------------------------------------------
# PhilHealth Constants (Universal Health Care Act - 2024 to 2026)
# ---------------------------------------------------------------------------
PH_RATE = Decimal("0.05")
PH_FLOOR = Decimal("10000")
PH_CEILING = Decimal("100000")

# ---------------------------------------------------------------------------
# Pag-IBIG Constants (HDMF 2024 to 2026)
# ---------------------------------------------------------------------------
HDMF_FUND_SALARY_CAP = Decimal("10000")
HDMF_LOW_THRESHOLD = Decimal("1500")
HDMF_LOW_EE_RATE = Decimal("0.01")
HDMF_STD_EE_RATE = Decimal("0.02")
HDMF_ER_RATE = Decimal("0.02")

# ---------------------------------------------------------------------------
# GSIS Constants (Government Employees)
# ---------------------------------------------------------------------------
GSIS_EE_RATE = Decimal("0.09")
GSIS_ER_RATE = Decimal("0.12")
GOV_PERA_MONTHLY = Decimal("2000")  # Tax-exempt Personnel Economic Relief Allowance

# ---------------------------------------------------------------------------
# Freelancer / Self-Employed Constants
# ---------------------------------------------------------------------------
VAT_THRESHOLD = Decimal("3000000")
EIGHT_PERCENT_ALLOWANCE = Decimal("250000")
EIGHT_PERCENT_RATE = Decimal("0.08")
PERCENTAGE_TAX_RATE = Decimal("0.03")
OSD_RATE = Decimal("0.40")  # 40% Optional Standard Deduction

# ---------------------------------------------------------------------------
# Tax Exemption Pool
# ---------------------------------------------------------------------------
BONUS_EXEMPT_CAP = Decimal("90000")  # NIRC Sec. 32(B)(7)(e)


def calculate_msc(salary: Decimal) -> Decimal:
    """Calculate SSS Monthly Salary Credit (MSC) in ₱500 steps from ₱5,000 to ₱35,000."""
    sal = to_decimal(salary)
    if sal <= ZERO:
        return ZERO
    half_step = SSS_MSC_STEP / Decimal("2")
    if sal < SSS_MSC_FLOOR + half_step:
        return SSS_MSC_FLOOR
    steps = ((sal - (SSS_MSC_FLOOR - half_step)) / SSS_MSC_STEP).to_integral_value(rounding=ROUND_DOWN)
    msc = SSS_MSC_FLOOR + (steps * SSS_MSC_STEP)
    return min(SSS_MSC_CEILING, msc)


def calculate_sss(salary: Decimal, status: str = "private") -> Dict[str, Decimal]:
    """Calculate SSS and Mandatory Provident Fund (MPF / MySSS Pension Booster)."""
    sal = to_decimal(salary)
    if sal <= ZERO:
        return {
            "msc": ZERO,
            "ee_regular": ZERO,
            "ee_mpf": ZERO,
            "ee_total": ZERO,
            "er_regular": ZERO,
            "er_mpf": ZERO,
            "er_total": ZERO,
            "er_ec": ZERO,
            "total_contribution": ZERO
        }

    msc = calculate_msc(sal)
    regular_msc = min(msc, SSS_REGULAR_CEILING)
    mpf_msc = max(ZERO, msc - SSS_REGULAR_CEILING)

    if status == "kasambahay" and sal < Decimal("5000"):
        # Employer pays 100% of contributions for domestic worker under ₱5,000
        ee_regular = ZERO
        ee_mpf = ZERO
        ee_total = ZERO
        er_regular = quantize_currency(regular_msc * SSS_RATE)
        er_mpf = quantize_currency(mpf_msc * SSS_RATE)
        er_total = er_regular + er_mpf
    elif status == "freelancer":
        # Freelancers/voluntary members pay full 15%
        ee_regular = quantize_currency(regular_msc * SSS_RATE)
        ee_mpf = quantize_currency(mpf_msc * SSS_RATE)
        ee_total = ee_regular + ee_mpf
        er_regular = ZERO
        er_mpf = ZERO
        er_total = ZERO
    else:
        # Standard private employee
        ee_regular = quantize_currency(regular_msc * SSS_EE_RATE)
        ee_mpf = quantize_currency(mpf_msc * SSS_EE_RATE)
        ee_total = ee_regular + ee_mpf
        er_regular = quantize_currency(regular_msc * SSS_ER_RATE)
        er_mpf = quantize_currency(mpf_msc * SSS_ER_RATE)
        er_total = er_regular + er_mpf

    er_ec = SSS_EC_LOW if msc < SSS_EC_THRESHOLD else SSS_EC_HIGH
    if status == "freelancer":
        er_ec = ZERO

    return {
        "msc": msc,
        "ee_regular": ee_regular,
        "ee_mpf": ee_mpf,
        "ee_total": ee_total,
        "er_regular": er_regular,
        "er_mpf": er_mpf,
        "er_total": er_total,
        "er_ec": er_ec,
        "total_contribution": ee_total + er_total + er_ec
    }


def calculate_philhealth(salary: Decimal, status: str = "private") -> Dict[str, Decimal]:
    """Calculate PhilHealth contribution at 5% rate with floor ₱10,000 and ceiling ₱100,000."""
    sal = to_decimal(salary)
    if sal <= ZERO:
        return {"base": ZERO, "ee_share": ZERO, "er_share": ZERO, "total": ZERO}

    base = min(PH_CEILING, max(PH_FLOOR, sal))
    total = quantize_currency(base * PH_RATE)

    if status == "kasambahay" and sal < Decimal("5000"):
        ee_share = ZERO
        er_share = total
    elif status == "freelancer":
        ee_share = total
        er_share = ZERO
    else:
        ee_share = quantize_currency(total / Decimal("2"))
        er_share = total - ee_share

    return {
        "base": base,
        "ee_share": ee_share,
        "er_share": er_share,
        "total": total
    }


def calculate_pagibig(salary: Decimal, status: str = "private") -> Dict[str, Decimal]:
    """Calculate Pag-IBIG (HDMF) contribution with ₱10,000 salary cap (max ₱200 EE / ₱200 ER)."""
    sal = to_decimal(salary)
    if sal <= ZERO:
        return {"fund_salary": ZERO, "ee_share": ZERO, "er_share": ZERO, "total": ZERO}

    fund_sal = min(HDMF_FUND_SALARY_CAP, sal)
    ee_rate = HDMF_LOW_EE_RATE if sal <= HDMF_LOW_THRESHOLD else HDMF_STD_EE_RATE
    er_rate = HDMF_ER_RATE

    ee_share = quantize_currency(fund_sal * ee_rate)
    er_share = quantize_currency(fund_sal * er_rate)

    if status == "kasambahay" and sal < Decimal("5000"):
        er_share = ee_share + er_share
        ee_share = ZERO
    elif status == "freelancer":
        ee_share = ee_share + er_share
        er_share = ZERO

    return {
        "fund_salary": fund_sal,
        "ee_share": ee_share,
        "er_share": er_share,
        "total": ee_share + er_share
    }


def calculate_gsis(salary: Decimal) -> Dict[str, Decimal]:
    """Calculate GSIS contributions for government employees (9% EE, 12% ER)."""
    sal = to_decimal(salary)
    if sal <= ZERO:
        return {"ee_share": ZERO, "er_share": ZERO, "total": ZERO}
    ee = quantize_currency(sal * GSIS_EE_RATE)
    er = quantize_currency(sal * GSIS_ER_RATE)
    return {
        "ee_share": ee,
        "er_share": er,
        "total": ee + er
    }


def calculate_annual_train_tax(annual_taxable_income: Decimal) -> Decimal:
    """Calculate annual income tax under BIR TRAIN Law (RA 10963, 2023–2026 schedule)."""
    inc = max(ZERO, to_decimal(annual_taxable_income))
    if inc <= Decimal("250000"):
        return ZERO
    elif inc <= Decimal("400000"):
        return quantize_currency((inc - Decimal("250000")) * Decimal("0.15"))
    elif inc <= Decimal("800000"):
        return quantize_currency(Decimal("22500") + (inc - Decimal("400000")) * Decimal("0.20"))
    elif inc <= Decimal("2000000"):
        return quantize_currency(Decimal("102500") + (inc - Decimal("800000")) * Decimal("0.25"))
    elif inc <= Decimal("8000000"):
        return quantize_currency(Decimal("402500") + (inc - Decimal("2000000")) * Decimal("0.30"))
    else:
        return quantize_currency(Decimal("2202500") + (inc - Decimal("8000000")) * Decimal("0.35"))


def calculate_monthly_withholding(monthly_taxable_income: Decimal, method: str = "annualized") -> Decimal:
    """
    Calculate monthly tax withholding.
    method='annualized': annualizes monthly income, calculates TRAIN tax, divides by 12.
    method='table': uses BIR RR 11-2018 monthly withholding lookup brackets.
    """
    m_inc = max(ZERO, to_decimal(monthly_taxable_income))
    if m_inc <= ZERO:
        return ZERO

    if method == "table":
        # BIR Monthly Table Lookup
        if m_inc <= Decimal("20833"):
            return ZERO
        elif m_inc <= Decimal("33333"):
            return quantize_currency((m_inc - Decimal("20833")) * Decimal("0.15"))
        elif m_inc <= Decimal("66667"):
            return quantize_currency(Decimal("1875") + (m_inc - Decimal("33333")) * Decimal("0.20"))
        elif m_inc <= Decimal("166667"):
            return quantize_currency(Decimal("8541.80") + (m_inc - Decimal("66667")) * Decimal("0.25"))
        elif m_inc <= Decimal("666667"):
            return quantize_currency(Decimal("33541.80") + (m_inc - Decimal("166667")) * Decimal("0.30"))
        else:
            return quantize_currency(Decimal("183541.80") + (m_inc - Decimal("666667")) * Decimal("0.35"))

    # Default: Annualized method
    annual_tax = calculate_annual_train_tax(m_inc * Decimal("12"))
    return quantize_currency(annual_tax / Decimal("12"))


def calculate_semimonthly_withholding(semimonthly_taxable_income: Decimal, method: str = "annualized") -> Decimal:
    """Calculate bi-weekly / semi-monthly withholding tax."""
    sm_inc = max(ZERO, to_decimal(semimonthly_taxable_income))
    if sm_inc <= ZERO:
        return ZERO

    if method == "table":
        # BIR Semi-Monthly Table Lookup
        if sm_inc <= Decimal("10417"):
            return ZERO
        elif sm_inc <= Decimal("16667"):
            return quantize_currency((sm_inc - Decimal("10417")) * Decimal("0.15"))
        elif sm_inc <= Decimal("33333"):
            return quantize_currency(Decimal("937.50") + (sm_inc - Decimal("16667")) * Decimal("0.20"))
        elif sm_inc <= Decimal("83333"):
            return quantize_currency(Decimal("4270.70") + (sm_inc - Decimal("33333")) * Decimal("0.25"))
        elif sm_inc <= Decimal("333333"):
            return quantize_currency(Decimal("16770.70") + (sm_inc - Decimal("83333")) * Decimal("0.30"))
        else:
            return quantize_currency(Decimal("91770.70") + (sm_inc - Decimal("333333")) * Decimal("0.35"))

    # Default annualized
    monthly_inc = sm_inc * Decimal("2")
    monthly_tax = calculate_monthly_withholding(monthly_inc, method="annualized")
    return quantize_currency(monthly_tax / Decimal("2"))


def calculate_13th_month(basic_monthly_salary: Decimal, months_worked: Decimal = Decimal("12")) -> Decimal:
    """Calculate pro-rated 13th month pay: (MonthlyBasic * months_worked) / 12."""
    b = to_decimal(basic_monthly_salary)
    m = to_decimal(months_worked)
    return quantize_currency((b * m) / Decimal("12"))


def calculate_bonus_tax_exemption(total_bonuses: Decimal) -> Dict[str, Decimal]:
    """Check ₱90,000 tax-exempt threshold under NIRC Sec. 32(B)(7)(e)."""
    b = max(ZERO, to_decimal(total_bonuses))
    exempt = min(BONUS_EXEMPT_CAP, b)
    taxable_excess = max(ZERO, b - BONUS_EXEMPT_CAP)
    return {
        "total_bonus": b,
        "exempt_amount": exempt,
        "taxable_excess": taxable_excess
    }


def calculate_freelancer_tax(annual_gross: Decimal, chosen_mode: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculate freelance tax comparing 8% Gross Income Tax vs Graduated Rates with 40% OSD.
    """
    gross = max(ZERO, to_decimal(annual_gross))
    eligible_8pct = gross <= VAT_THRESHOLD

    # 8% Option
    tax_8pct = quantize_currency(max(ZERO, gross - EIGHT_PERCENT_ALLOWANCE) * EIGHT_PERCENT_RATE)
    opt_8pct = {
        "key": "eight",
        "income_tax": tax_8pct,
        "percentage_tax": ZERO,
        "total": tax_8pct
    }

    # Graduated with 40% OSD
    taxable_net = gross * (Decimal("1") - OSD_RATE)
    grad_income_tax = calculate_annual_train_tax(taxable_net)
    percentage_tax = quantize_currency(gross * PERCENTAGE_TAX_RATE) if eligible_8pct else ZERO
    opt_grad = {
        "key": "graduated",
        "income_tax": grad_income_tax,
        "percentage_tax": percentage_tax,
        "total": grad_income_tax + percentage_tax
    }

    options = [opt_8pct, opt_grad] if eligible_8pct else [opt_grad]
    cheaper = "eight" if eligible_8pct and opt_8pct["total"] <= opt_grad["total"] else "graduated"
    chosen = chosen_mode if chosen_mode in ["eight", "graduated"] and (chosen_mode != "eight" or eligible_8pct) else cheaper

    return {
        "annual_gross": gross,
        "eligible_for_eight": eligible_8pct,
        "cheaper": cheaper,
        "chosen": chosen,
        "options": options
    }


def calculate_salary_payload(
    basic_monthly: Decimal,
    status: str = "private",
    taxable_allowances: Decimal = ZERO,
    non_taxable_allowances: Decimal = ZERO,
    other_deductions: Decimal = ZERO,
    withholding_method: str = "annualized",
    freelance_mode: Optional[str] = None
) -> Dict[str, Any]:
    """
    Complete composite take-home pay calculation matching Pinasweldo.
    """
    basic = to_decimal(basic_monthly)
    tax_allow = to_decimal(taxable_allowances)
    non_tax_allow = to_decimal(non_taxable_allowances)
    other_ded = to_decimal(other_deductions)

    gross_monthly = basic + tax_allow + non_tax_allow

    # Statutory Contributions
    if status == "government":
        gsis = calculate_gsis(basic)
        ph = calculate_philhealth(basic, status="government")
        pagibig = calculate_pagibig(basic, status="government")
        sss = calculate_sss(ZERO)
        statutory_ee = gsis["ee_share"] + ph["ee_share"] + pagibig["ee_share"]
        statutory_er = gsis["er_share"] + ph["er_share"] + pagibig["er_share"]
    elif status == "freelancer":
        sss = calculate_sss(basic, status="freelancer")
        ph = calculate_philhealth(basic, status="freelancer")
        pagibig = calculate_pagibig(basic, status="freelancer")
        gsis = calculate_gsis(ZERO)
        statutory_ee = sss["ee_total"] + ph["ee_share"] + pagibig["ee_share"]
        statutory_er = ZERO
    else:  # private or kasambahay
        sss = calculate_sss(basic, status=status)
        ph = calculate_philhealth(basic, status=status)
        pagibig = calculate_pagibig(basic, status=status)
        gsis = calculate_gsis(ZERO)
        statutory_ee = sss["ee_total"] + ph["ee_share"] + pagibig["ee_share"]
        statutory_er = sss["er_total"] + sss["er_ec"] + ph["er_share"] + pagibig["er_share"]

    # Taxable Base
    if status == "freelancer":
        freelance_calc = calculate_freelancer_tax(basic * Decimal("12"), chosen_mode=freelance_mode)
        chosen_opt = next(o for o in freelance_calc["options"] if o["key"] == freelance_calc["chosen"])
        month_tax = quantize_currency(chosen_opt["income_tax"] / Decimal("12"))
        month_pct = quantize_currency(chosen_opt["percentage_tax"] / Decimal("12"))
        taxable_income = max(ZERO, basic * Decimal("12"))
    else:
        freelance_calc = None
        month_pct = ZERO
        regular_taxable = max(ZERO, basic + tax_allow - statutory_ee)
        month_tax = calculate_monthly_withholding(regular_taxable, method=withholding_method)
        taxable_income = regular_taxable * Decimal("12")

    total_deductions = statutory_ee + month_tax + month_pct + other_ded
    net_monthly = max(ZERO, gross_monthly - total_deductions)

    return {
        "status": status,
        "basic_monthly": basic,
        "taxable_allowances": tax_allow,
        "non_taxable_allowances": non_tax_allow,
        "gross_monthly": gross_monthly,
        "sss": sss,
        "philhealth": ph,
        "pagibig": pagibig,
        "gsis": gsis,
        "statutory_ee": statutory_ee,
        "statutory_er": statutory_er,
        "taxable_income_annual": taxable_income,
        "withholding_tax_monthly": month_tax,
        "percentage_tax_monthly": month_pct,
        "other_deductions": other_ded,
        "total_deductions": total_deductions,
        "net_monthly": net_monthly,
        "cutoff_net": quantize_currency(net_monthly / Decimal("2")),
        "freelance_analysis": freelance_calc
    }


# ---------------------------------------------------------------------------
# High-Level Adapter Classes & Aliases
# ---------------------------------------------------------------------------
from dataclasses import dataclass


@dataclass
class SSSResult:
    msc: Decimal
    ee_regular: Decimal
    ee_mpf: Decimal
    total_ee: Decimal
    er_regular: Decimal
    er_mpf: Decimal
    total_er: Decimal
    er_ec: Decimal
    total_contribution: Decimal


@dataclass
class PhilHealthResult:
    base: Decimal
    ee_share: Decimal
    er_share: Decimal
    total_premium: Decimal


@dataclass
class PagIBIGResult:
    fund_salary: Decimal
    ee_share: Decimal
    er_share: Decimal
    total: Decimal


@dataclass
class SalaryComputationResult:
    gross_income: Decimal
    basic_salary: Decimal
    taxable_allowances: Decimal
    non_taxable_allowances: Decimal
    sss_ee: Decimal
    philhealth_ee: Decimal
    pagibig_ee: Decimal
    gsis_ee: Decimal
    total_statutory_deductions: Decimal
    withholding_tax: Decimal
    total_ee_deductions: Decimal
    net_pay: Decimal
    semi_monthly_net: Decimal
    raw_payload: Dict[str, Any]


def calculate_sss_2026(salary: Decimal, status: str = "private") -> SSSResult:
    res = calculate_sss(salary, status=status)
    return SSSResult(
        msc=res["msc"],
        ee_regular=res["ee_regular"],
        ee_mpf=res["ee_mpf"],
        total_ee=res["ee_total"],
        er_regular=res["er_regular"],
        er_mpf=res["er_mpf"],
        total_er=res["er_total"],
        er_ec=res["er_ec"],
        total_contribution=res["total_contribution"],
    )


def calculate_philhealth_2026(salary: Decimal, status: str = "private") -> PhilHealthResult:
    res = calculate_philhealth(salary, status=status)
    return PhilHealthResult(
        base=res["base"],
        ee_share=res["ee_share"],
        er_share=res["er_share"],
        total_premium=res["total"],
    )


def calculate_pagibig_2026(salary: Decimal, status: str = "private") -> PagIBIGResult:
    res = calculate_pagibig(salary, status=status)
    return PagIBIGResult(
        fund_salary=res["fund_salary"],
        ee_share=res["ee_share"],
        er_share=res["er_share"],
        total=res["total"],
    )


calculate_bir_withholding_annual = calculate_annual_train_tax


def calculate_bir_withholding_semi_monthly(semimonthly_taxable_income: Decimal, method: str = "table") -> Decimal:
    return calculate_semimonthly_withholding(semimonthly_taxable_income, method=method)


def calculate_13th_month_pay(monthly_basic: Decimal, months_worked: Decimal = Decimal("12")) -> Dict[str, Decimal]:
    bonus = calculate_13th_month(monthly_basic, months_worked)
    exempt_info = calculate_bonus_tax_exemption(bonus)
    return {
        "total_bonus": bonus,
        "non_taxable_bonus": exempt_info["exempt_amount"],
        "taxable_bonus": exempt_info["taxable_excess"],
    }


calculate_freelance_tax = calculate_freelancer_tax


def calculate_tax_and_contributions(
    monthly_basic: Decimal,
    employment_type: str = "private",
    taxable_allowances: Decimal = ZERO,
    non_taxable_allowances: Decimal = ZERO,
    other_deductions: Decimal = ZERO,
    withholding_method: str = "annualized",
    freelance_mode: Optional[str] = None,
) -> SalaryComputationResult:
    payload = calculate_salary_payload(
        basic_monthly=monthly_basic,
        status=employment_type,
        taxable_allowances=taxable_allowances,
        non_taxable_allowances=non_taxable_allowances,
        other_deductions=other_deductions,
        withholding_method=withholding_method,
        freelance_mode=freelance_mode,
    )
    return SalaryComputationResult(
        gross_income=payload["gross_monthly"],
        basic_salary=payload["basic_monthly"],
        taxable_allowances=payload["taxable_allowances"],
        non_taxable_allowances=payload["non_taxable_allowances"],
        sss_ee=payload["sss"]["ee_total"],
        philhealth_ee=payload["philhealth"]["ee_share"],
        pagibig_ee=payload["pagibig"]["ee_share"],
        gsis_ee=payload["gsis"]["ee_share"],
        total_statutory_deductions=payload["statutory_ee"],
        withholding_tax=payload["withholding_tax_monthly"],
        total_ee_deductions=payload["total_deductions"],
        net_pay=payload["net_monthly"],
        semi_monthly_net=payload["cutoff_net"],
        raw_payload=payload,
    )
