---
title: "User Data Privacy and Local Storage Guide"
tags:
  - budgeting-app
  - privacy
  - storage
status: active
last_modified: 2026-10-25
source_of_truth:
  - AGENTS.md
---

# User Data Privacy & Local Storage Architecture

## 1. Zero Cloud Telemetry & Complete Offline Guarantee
The Budgeting & Philippine Salary Suite operates exclusively on the local machine:
- **No Remote Endpoints**: The application makes zero HTTP/WebSocket calls during standard operation. All calculations execute locally in Python.
- **No Third-Party Analytics**: No Google Analytics, Mixpanel, or telemetry beacons exist in the UI or backend.
- **Offline CDN Free**: All fonts, SVGs, styles, and scripts are bundled locally into the `.exe` payload.

## 2. Local Storage Hierarchy
User profiles, schedule configurations, and recurring bill histories are stored in:
- **Windows Default**: `%APPDATA%\PersonalBudgetApp\data\`
- **Development Fallback**: Local `.user_data/` (strictly ignored by `.gitignore`).
- **File Format**: Plain, human-readable indented JSON or SQLite with schema versioning.

## 3. Privacy Rule for Git Repositories
- Never commit user configuration files, personal bank balances, income histories, or spreadsheets to source control.
- Test suites must use synthetic mock fixtures (e.g., standard testing incomes of ₱20,000, ₱50,000, ₱100,000).
