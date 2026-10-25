---
title: "Workbook Data Model and Formulas"
tags:
  - budgeting-app
  - data-model
  - workbook-spec
  - excel-reverse-engineering
status: active
last_modified: 2026-10-25
source_of_truth:
  - references/Dan BudgetingV3.xlsx
---

# Personal Budgeting Workbook Data Model & Calculation Specification

This document provides the reverse-engineered data model, formula algebra, sheet topology, and calculation pipelines extracted from `references/Dan BudgetingV3.xlsx`.

> [!NOTE]
> **Privacy Rule Compliance**: In accordance with `AGENTS.md`, all sensitive personal financial figures, account numbers, and personal names have been sanitized into schema abstractions and configurable parameters.

---

## 1. Sheet Architecture & Functional Taxonomy

The reference workbook comprises 11 sheets operating as a relational personal finance and shared expense settlement system:

| Sheet Name | Functional Category | Purpose / Responsibility |
|:-----------|:--------------------|:-------------------------|
| **`📊 Dashboard`** | Executive Summary & Bi-Weekly Model | Consolidates bi-weekly salary cutoffs, working days, daily transit/food expenses, utility deductions, and net cash flow available. |
| **`Monthly Bills`** | Recurring Bills & Utilities | Historical ledger of rent, water, electricity, and internet; dynamically divides costs among roommates with status tracking and 3-month rolling averages. |
| **`Apt Expenses`** | Shared Asset & Setup Purchases | Itemized ledger for apartment furnishings, groceries, hardware, and one-off application expenses with discount deductions. |
| **`Calumpang`** | Shared Settlement Ledger | Peer-to-peer expense ledger tracking who paid for what and who owes whom (Dan, Roommate A, Roommate B) with 50/50 division. |
| **`Mama Groceries`** | Family Remittance Ledger | Two-column ledger calculating gross remittances less deductions to compute the exact net transfer required. |
| **`Pajah Rent`** | Equipment & Apparel Rental | Tracks item owners, rental prices, add-on margins, and net payouts per participant. |
| **`Holidays`** | Statutory Calendar Reference | Complete calendar of Philippine Regular and Special Non-Working Holidays used by `NETWORKDAYS.INTL` to compute working days. |
| **`Lists`** | Lookups & Design Tokens | Master validation lists for statuses (`Paid`, `Pending`, `Complete`), rolling dates via `EDATE`, and status color hex codes. |
| **`Spotify`** | Subscription Detail | Ancillary group sharing cost breakdown. |
| **`Current Budget`** | Operational Scratchpad | Working budget snapshot synchronized with Dashboard. |
| **`Chore Chart`** | Household Logistics | Task allocation tracking. |

---

## 2. Calculation Flow & Data Pipeline

```mermaid
graph TD
    subgraph External Inputs & Calendar
        HOL[Holidays Sheet<br/>Statutory Holiday List]
        CAL[Target Month & Year<br/>e.g. Month 9, Year 2026]
        RATE[Hourly / Unit Rate]
        SCHED[Class / Teaching Schedule<br/>Hours per Day of Week]
    end

    subgraph Bi-Weekly Working Days Engine
        NW1["Cutoff 1 Working Days (1st to 15th)<br/>NETWORKDAYS.INTL(..., Holidays)"]
        NW2["Cutoff 2 Working Days (16th to EOM)<br/>NETWORKDAYS.INTL(..., Holidays)"]
        TOT_DAYS["Monthly Working Days = Cutoff 1 + Cutoff 2"]
    end

    HOL & CAL & SCHED --> NW1
    HOL & CAL & SCHED --> NW2
    NW1 & NW2 --> TOT_DAYS

    subgraph Salary & Tax Calculation
        GROSS["Gross Cutoff Pay = Units * Unit Rate"]
        TOT_GROSS["Total Monthly Gross = Cutoff 1 + Cutoff 2"]
        TAX["Tax Withholding = Gross * Tax Rate (or BIR Table)"]
        NET_TAX["Take-Home After Tax = Gross - Tax"]
    end

    NW1 & NW2 & RATE --> GROSS
    GROSS --> TOT_GROSS
    TOT_GROSS --> TAX
    TAX --> NET_TAX

    subgraph Everyday Living Costs
        DAILY_EXP["Daily Living Cost = Transpo + Food per Day of Week"]
        MO_EXP["Monthly Living Expenses = Daily Cost * Working Days"]
        BI_EXP["Bi-Weekly Living Expenses = Monthly Expenses / 2"]
        NET_AFTER_LIVING["Operating Net = Net After Tax - Monthly Living"]
    end

    TOT_DAYS & DAILY_EXP --> MO_EXP
    MO_EXP --> BI_EXP
    NET_TAX & MO_EXP --> NET_AFTER_LIVING

    subgraph Shared Bills & Settled Payables
        MB["Monthly Bills Sheet<br/>Rent + Electricity + Water + Internet"]
        SPLIT["Roommate Split: Cost / Active Tenants"]
        CALUMPANG["Calumpang Ledger<br/>Peer Settlements & Reimbursables"]
        MAMA["Mama Groceries<br/>Net Family Remittance"]
    end

    MB --> SPLIT
    SPLIT & CALUMPANG & MAMA --> DEDUCT_TOTAL["Total Payables & Utilities"]
    NET_AFTER_LIVING & DEDUCT_TOTAL --> FINAL_NET["Final Discretionary Cash Flow<br/>Money Available After Payables"]
```

---

## 3. Detailed Formula Algebra & Cell Logic

### 3.1 Bi-Weekly Working Days & Holiday Filtering
The application dynamically computes working days per cutoff for each day of the week (Monday through Saturday) using seven-character binary day masks (`0` = working day, `1` = rest day) cross-referenced against `Holidays!$A$2:$A$100`:

- **Cutoff 1 (1st to 15th)**:
  ```excel
  =NETWORKDAYS.INTL(DATE(Year, Month, 1), DATE(Year, Month, 15), "0111111", Holidays!$A$2:$A$100) * Mon_Units
  + NETWORKDAYS.INTL(DATE(Year, Month, 1), DATE(Year, Month, 15), "1011111", Holidays!$A$2:$A$100) * Tue_Units
  + ...
  + NETWORKDAYS.INTL(DATE(Year, Month, 1), DATE(Year, Month, 15), "1111101", Holidays!$A$2:$A$100) * Sat_Units
  ```
- **Cutoff 2 (16th to End of Month)**:
  ```excel
  =NETWORKDAYS.INTL(DATE(Year, Month, 16), EOMONTH(DATE(Year, Month, 1), 0), "0111111", Holidays!$A$2:$A$100) * Mon_Units
  + ...
  ```

### 3.2 Dynamic Roommate Utility Cost Splitting (`Monthly Bills`)
Each bill row divides the total sum of utilities and rent among occupants who are marked active (`TRUE`):
```excel
=IF(TotalBill="", "", IFERROR(TotalBill / COUNTIF(Tenant1:Tenant3, TRUE), 0))
```
- If an occupant is away for that billing cycle (`FALSE`), the denominator automatically scales down without breaking spreadsheet formulas.

### 3.3 3-Month Rolling Utility Averages
Computes rolling expenditure trends for water, power, and internet:
```excel
=AVERAGE(OFFSET(UtilityColumnStart, COUNTA(UtilityColumn) - 3, 0, 3, 1))
```

### 3.4 Shared Ledger Division (`Calumpang`)
- **Shared Half**: `=ROUNDUP(ItemPrice / 2, 0)`
- **Individual Obligation**: `=IF(PaidCheckbox=1, 0, IndividualShare)`

### 3.5 Remittance Net Reconciliation (`Mama Groceries`)
```excel
NetTransfer = SUM(GroceriesAndObligations) - SUM(DeductionsAndCredits)
```

### 3.6 Apartment Expenditures & Sub-Ledgers (`Apt Expenses`)
`Apt Expenses` coordinates six specialized sub-ledgers managing shared furnishings, professional application fees, dental orthodontics, and trip cost distribution:

1. **House / IKEA Expenditures (`A1:G22`)**:
   Itemized inventory with applied promotional or cardholder discounts:
   ```excel
   TotalPrice = (Count * Price) - Discount
   GrandTotal = SUM(E3:E22)  # Benchmark: ₱4,675.00
   ```
2. **Application Expenses (`A33:E42`)**:
   Mandatory pre-employment/board credentials (Drug Test, Neuro Psych, NBI, TOR, Medical):
   ```excel
   Subtotal = SUM(D34:D40)   # Benchmark: ₱2,420.00
   ```
3. **Dentist & Braces Tracker (`A44:E67`)**:
   Orthodontic contract billing less incremental installment deductibles:
   ```excel
   TotalBilled = SUM(D46:D56)       # Benchmark: ₱37,500.00
   TotalPaid = -SUM(D58:D64)        # Benchmark: ₱8,000.00 (displayed as negative deductible)
   PureRemaining = TotalBilled - TotalPaid  # ₱29,500.00
   CombinedBalance (D67) = PureRemaining + ApplicationExpenses  # ₱31,920.00
   ProgressPct = TotalPaid / TotalBilled  # 21.33% -> Visual Bar: ██░░░░░░░░
   ```
4. **Group & Personal Mini-Ledgers**:
   - `Maple Grove SnR Food` (`A69:E79`): Itemized grocery run (Benchmark: `₱746.00`).
   - `Ate Joy` (`A99:E108`) & `Lorraine` (`A113:E122`): Reimbursable line items (Benchmark: `₱250.00`).
5. **Dynamic N-Person Expedition Ledger (`A126:F135`)**:
   Shared trip costs (gas, tollways, food) distributed dynamically among variable group sizes:
   ```excel
   ItemShare = IFERROR(ROUNDUP((Price * Count) / Divisor, 0), 0)  # Benchmark Subtotal: ₱968.00
   ```

### 3.7 Roommate Maintenance Logistics (`Chore Chart`)
Tracks household task allocations across 5 discrete residential zones (16 chores):
- **Zones**: Kitchen (5), Living Room (3), Bedroom (3), Bathroom (2), Maintenance (3).
- **Recurrence Frequencies**: *Daily, Every other day, Every after use, Weekly, Every 2 weeks, Monthly*.
- **Daily Assignee Matrix**: Columns for Days 1 through 31 tracked with initials (`D` = Dan, `J` = Jaco, `T` = Troy).
- **Live Roommate Completion Counters**:
  ```excel
  RoommateCompleted = COUNTIF(C5:AN24, "D")
  ```

### 3.8 Academic Regalia Asset Rental (`Pajah Rent`)
Toga ("Pajah") rental tracking system for 8 co-owners (`Dan, Christian, Harvin, Jiom, Josh, Noella, Rj, Troy`):
```excel
Pictorial_Fprice = Price_Pictorial (₱500) + Dan_Addon (₱100) = ₱600.00
Grad_Fprice = Price_Grad (₱650) + Dan_Addon (₱100) = ₱750.00
Sum_Package = Pictorial_Fprice + Grad_Fprice = ₱1,350.00
Owner_Revenue = Sum_Package * Active_Rentals
```

### 3.9 Master Peer Settlement Matrix (`Calumpang!M1:U39`)
Multi-party reconciliation matrix between Dan, Jaco, and Troy:
- Integrates Spotify subscription share (`₱57.40`) and Troy's monthly utility balance from `Monthly Bills!P6` (`₱3,175.00`).
- **Bank Transfer Calculation**:
  ```excel
  TotalBankTransfer = ROUNDUP(Subtotal - Deductibles, 0)  # Benchmark: ₱4,872.00
  ```
- **Cash Settlements (`M35:S39`)**: Independent cash ledger for non-bank peer transfers.

### 3.10 Holiday Unit Loss & Allowance Nuances (`Current Budget`)
- **Lost Cash/Units from Holidays (`A5:C5`)**:
  ```excel
  LostUnits = SUMPRODUCT(Holidays_Per_Weekday, Units_Per_Weekday)
  LostCash = LostUnits * Hourly_Rate
  ```
- **Everyday Living Allowance**:
  - **1-Week Base Living Allowance (`B14:B15`)**: Base weekly sum (`₱165 + ₱300 = ₱465.00`).
  - **Monthly Working-Day Living Allowance (`M17`)**: Working days multiplied by daily transit and food rates (`₱2,015.00`).
- **Payables & Additionals Flow**:
  ```excel
  MoneyAvailableAfterUtility = TotalGross - UtilitiesAndRent
  MoneyAfterAdditionals = MoneyAvailableAfterUtility + SUM(Additionals)
  MoneyAfterPayable = MoneyAfterAdditionals - SUM(Payables)
  ```

---

## 4. Proposed Desktop Software Data Model

To replicate and elevate this workbook into a modern Python + Bootstrap desktop application, the domain model will be structured as follows:

```mermaid
classDiagram
    class SalarySchedule {
        +int year
        +int month
        +float hourly_rate
        +dict daily_units
        +float tax_rate
        +calculate_cutoffs(holidays)
    }

    class DailyExpenseTracker {
        +float transpo_per_day
        +float food_per_day
        +calculate_monthly_cost(working_days)
    }

    class MonthlyBill {
        +str billing_month
        +float rent
        +float water
        +float electricity
        +float internet
        +list occupants
        +split_per_person()
    }

    class PeerSettlement {
        +str date
        +str item
        +float price
        +str paid_by
        +str owed_by
        +float split_ratio
        +bool is_settled
    }

    class BudgetReconciliation {
        +SalarySchedule salary
        +DailyExpenseTracker living
        +MonthlyBill bills
        +list settlements
        +compute_final_available_cash()
    }

    BudgetReconciliation --> SalarySchedule
    BudgetReconciliation --> DailyExpenseTracker
    BudgetReconciliation --> MonthlyBill
    BudgetReconciliation --> PeerSettlement
```
