---
title: "Packaging and Windows Build Recipe"
tags:
  - budgeting-app
  - pyinstaller
  - packaging
status: active
last_modified: 2026-10-25
source_of_truth:
  - AGENTS.md
---

# Packaging and Standalone Windows Executable Build Recipe

This document defines the PyInstaller build specification and PE version resource configuration for compiling the desktop application into a standalone `.exe`.

## 1. PyInstaller Build Architecture
- **Tool**: PyInstaller 6.22.2+
- **Mode**: `--onefile --windowed` (no console window).
- **Target OS**: Windows 10/11 x64.
- **Embedded Bundles**:
  - `ui.html`
  - `css/` directory
  - `js/` directory
  - Default holiday and tax rate tables

## 2. Windows PE Version Information (`file_version_info.txt`)
Contains standard Windows resource metadata for Explorer Properties:
- `CompanyName`: Dan Joseph Ortega
- `FileDescription`: Personal Budgeting & Philippine Salary Suite
- `LegalCopyright`: Copyright © 2026 Dan Joseph Ortega. All rights reserved.
- `ProductName`: Personal Budgeting & Salary Suite
- `FileVersion` & `ProductVersion`: Synchronized with `ui.html` badge (`Release vX.Y.Z`).

## 3. Build Command
```cmd
build.bat
```
Which executes:
```cmd
python -m PyInstaller --noconfirm --clean --onefile --windowed ^
    --name "BudgetApp" ^
    --version-file "file_version_info.txt" ^
    --add-data "ui.html;." ^
    --add-data "css;css/" ^
    --add-data "js;js/" ^
    "main.py"
```
