---
title: "Statutory Rate Tables 2026"
tags:
  - budgeting-app
  - tax-spec
  - rate-tables
status: active
last_modified: 2026-10-25
source_of_truth:
  - references/pinasweldo/raw/chunks/185ecivlr9cih.js
---

# Philippine Statutory Contribution Rate Tables (2026)

This document provides lookup tables for SSS, PhilHealth, Pag-IBIG, and Regional Minimum Wages as implemented in the desktop calculation engine.

## 1. SSS Contribution Schedule (RA 11199 & Circular 2024-006)

*Note: SSS contribution rate is 15% (Employee: 5%, Employer: 10%). For MSC > ₱20,000, the excess up to ₱35,000 is credited to the Mandatory Provident Fund (MPF / MySSS Pension Booster).*

| Range of Compensation | Monthly Salary Credit (MSC) | Regular SSS (EE 5%) | MPF (EE 5%) | Total EE Share | Employer Share (10%) | EC (ER) | Total Remittance |
|:----------------------|:---------------------------:|:-------------------:|:-----------:|:--------------:|:--------------------:|:-------:|:----------------:|
| ₱0 – ₱5,249.99 | ₱5,000 | ₱250.00 | ₱0.00 | **₱250.00** | ₱500.00 | ₱10.00 | ₱760.00 |
| ₱5,250 – ₱5,749.99 | ₱5,500 | ₱275.00 | ₱0.00 | **₱275.00** | ₱550.00 | ₱10.00 | ₱835.00 |
| ₱9,750 – ₱10,249.99 | ₱10,000 | ₱500.00 | ₱0.00 | **₱500.00** | ₱1,000.00 | ₱10.00 | ₱1,510.00 |
| ₱14,750 – ₱15,249.99 | ₱15,000 | ₱750.00 | ₱0.00 | **₱750.00** | ₱1,500.00 | ₱30.00 | ₱2,280.00 |
| ₱19,750 – ₱20,249.99 | ₱20,000 | ₱1,000.00 | ₱0.00 | **₱1,000.00** | ₱2,000.00 | ₱30.00 | ₱3,030.00 |
| ₱24,750 – ₱25,249.99 | ₱25,000 | ₱1,000.00 | ₱250.00 | **₱1,250.00** | ₱2,500.00 | ₱30.00 | ₱3,780.00 |
| ₱29,750 – ₱30,249.99 | ₱30,000 | ₱1,000.00 | ₱500.00 | **₱1,500.00** | ₱3,000.00 | ₱30.00 | ₱4,530.00 |
| ₱34,750 and above | ₱35,000 | ₱1,000.00 | ₱750.00 | **₱1,750.00** | ₱3,500.00 | ₱30.00 | ₱5,280.00 |

---

## 2. PhilHealth Contribution Table (5.0%)

- **Salary Floor**: ₱10,000.00 (Fixed total ₱500.00 $\rightarrow$ ₱250.00 EE / ₱250.00 ER).
- **Salary Ceiling**: ₱100,000.00 (Fixed total ₱5,000.00 $\rightarrow$ ₱2,500.00 EE / ₱2,500.00 ER).
- **Between ₱10,000 and ₱100,000**:
  $$\text{EE Share} = \frac{\text{Monthly Basic} \times 0.05}{2} = \text{Monthly Basic} \times 0.025$$

---

## 3. Pag-IBIG (HDMF) Table

| Monthly Compensation | Fund Salary Base | Employee Share (%) | Employee Amount | Employer Share (%) | Employer Amount | Total Monthly |
|:---------------------|:----------------:|:-------------------:|:---------------:|:-------------------:|:---------------:|:-------------:|
| ₱1,500 and below | Actual | 1.0% | Max ₱15.00 | 2.0% | Max ₱30.00 | Max ₱45.00 |
| Over ₱1,500 to ₱10,000 | Actual | 2.0% | Up to ₱200.00 | 2.0% | Up to ₱200.00 | Up to ₱400.00 |
| Over ₱10,000 (Capped) | ₱10,000 | 2.0% | **₱200.00** | 2.0% | **₱200.00** | **₱400.00** |

---

## 4. Key Regional Daily Minimum Wages (Late 2026 Reference)

- **NCR (Metro Manila - Wage Order NCR-28)**:
  - Non-Agriculture: **₱755.00 / day**
  - Agriculture / Small Retail: **₱718.00 / day**
- **Region IV-A (CALABARZON - Wage Order IVA-23)**:
  - Cities (Bacoor, Dasmariñas, Imus, etc.): **₱645.00 / day**
  - 1st Class Municipalities: **₱590.00 / day**
  - Other Municipalities / Agriculture: **₱550.00 / day**
- **Region III (Central Luzon - Wage Order RBIII-26)**:
  - Non-Agriculture: **₱600.00 / day**
- **Region VII (Central Visayas - ROVII-27)**:
  - Class A (Metro Cebu): **₱582.00 / day**
