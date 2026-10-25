# Project Rules & Agent Governance: Budgeting & Philippine Salary/Tax App

## 0. Agent Governance & Rule Modification

- **Controlled Artifact**: `AGENTS.md` defines the immutable operating rules for agents in this workspace.
- **No Unauthorized Modifications**: Agents must NEVER modify `AGENTS.md`, `.agents/agents/`, `.agents/rules/`, or `.agents/workflows/` simply because they believe instructions could be improved.
- **No Silent Updates**: Documentation audits, refactors, or feature implementations must not silently alter agent governance.
- **Reporting Issues**: If a task exposes a governance problem or contradiction, the agent must report it to the user rather than changing governance rules without explicit authorization.

## 1. Tests Location

All test programs, test suites, test fixtures, and testing utilities must always be placed under the `tests/` directory:

- Automated tests (`test_*.py`) belong in `tests/`.
- Regression, edge cases, diff, and verification scripts belong in `tests/`.
- Do not place test scripts in the root directory.

## 2. Git Commit Formatting

All git commit messages must strictly follow the format:
`<commit_number>: <description based on chat changes>`

- **Format**: `<commit_number>: <description based on chat changes>`
- **`<commit_number>`**: The sequential commit number for the repository (e.g. `git rev-list --count HEAD + 1`).
- **`<description based on chat changes>`**: Clear, descriptive summary of the modifications implemented during the chat/task.
- **Example**: `1: initialize repository scaffold, AGENTS.md, and Obsidian reverse engineering documentation`

## 3. Git Branching & Merging Rules

- **Development on `dev`**: All active work, feature implementations, tests, and task commits belong strictly on the `dev` branch and `origin/dev`.
- **Do NOT Auto-Merge to `main`**: Merging into `main` must **NEVER** happen automatically at the end of a task or chat. Merging to `main` requires an explicit user prompt or request.
- **Merging into `main` (Only When Prompted by User)**:
  When the user explicitly instructs to merge `dev` into `main`:
  - **Always use `--no-ff` (No Fast-Forward)**: Never perform fast-forward merges into `main`. Always force a dedicated merge commit using `git merge --no-ff <branch>` to ensure the Git commit history preserves a distinct visual branch tree with fork-and-merge nodes.
  - **Merge Commit Message Formatting**: Merge commits must also follow the commit numbering rule and clearly summarize the changes being merged into the target branch:
    `<commit_number>: merge <source_branch> into <target_branch> - <description of merged changes>`
    Example: `15: merge dev into main - implement salary calculator and budget reconciliation engine`
  - **Standard Merge Workflow**:
    1. Ensure all work is committed and pushed on `dev`.
    2. `git checkout main`
    3. `git merge --no-ff dev -m "<commit_number>: merge dev into main - <description of merged changes>"`
    4. `git push origin main`
    5. `git checkout dev`

## 4. Version Numbering & Synchronization

- **Single Source of Truth**: The active application version is displayed in `app/ui.html` via the `<span class="badge-version">Release vX.Y.Z</span>` badge in the navigation header. This is the canonical application-version representation; all other locations are synchronized consumers.
- **Development Changes**: Normal bug fixes, internal improvements, refactors, tests, documentation changes, and other development commits do **NOT** automatically require a version bump. Do not interpret every development commit as a release.
- **When to Bump the Version**:
  - A version bump is required ONLY when the project is intentionally producing a new application release, or when the user/task explicitly requests a version bump (e.g. from `Release v1.0.0` -> `Release v1.0.1`).
  - Never leave the version number stale across releases or major feature updates.
- **Synchronization Checklist**:
  1. `app/ui.html`: Update the header badge `<span class="badge-version">Release vX.Y.Z</span>`.
  2. `tests/test_ui_consistency.py`: Ensure test assertions verify the current version badge.
  3. `app/README.md`: If version numbers or changelog items are listed, keep them synchronized.
  4. `app/file_version_info.txt`: Synchronize `filevers`, `prodvers`, `FileVersion`, and `ProductVersion`.
  5. `budgeting-app-documentation/05 - Releases & Changelog/`: Add or update release notes for the new version in the Obsidian documentation vault.

## 5. Obsidian Documentation Vault Protocol

> [!IMPORTANT]
> ## Project and Documentation Relationship
>
> The project coordinates two primary workspace components:
> 1. **Application Codebase & Tooling**: Located in `app/`, `tests/`, and root scripts.
> 2. **Companion Obsidian Documentation Vault**: Located in `budgeting-app-documentation/`.
>
> The Obsidian vault is the project's **primary human-readable knowledge repository** and architectural single source of truth for:
> - Software architecture, PyWebView bridge contracts, and module boundaries.
> - Philippine tax and statutory contribution formulas (BIR TRAIN, SSS, PhilHealth, Pag-IBIG).
> - Personal budgeting data models, expense hierarchies, and reconciliation flows derived from `references/Dan BudgetingV3.xlsx`.
>
> **Mandatory Rule**: Any architectural change, statutory formula update, or new feature must be documented and cross-linked in `budgeting-app-documentation` using Obsidian Markdown (`[[wikilinks]]`, YAML frontmatter, and Mermaid diagrams).

### 5.1 Source-of-Truth Hierarchy

When discrepancies arise, agents must strictly observe this priority hierarchy:
1. **Executable / Application Source Code**: Active Python and frontend runtime code in `app/`.
2. **Automated Tests**: Validated test suites and test fixtures (`tests/`).
3. **Reference Artifacts**: Shipped/verified reference files in `references/` (e.g. `references/pinasweldo/`, `references/Dan BudgetingV3.xlsx`).
4. **Obsidian Documentation Vault**: Primary human-readable knowledge repository (`budgeting-app-documentation/`).
5. **README / Supplementary Documentation**: High-level overviews and quickstarts.

### 5.2 Documentation Synchronization Triggers

Any change altering calculations, schemas, API endpoints, or user workflows requires updating the vault:
- Philippine tax rates or contribution brackets (SSS, PhilHealth, Pag-IBIG).
- Budgeting workbook category definitions, sheet structures, or metric formulas.
- PyWebView Python-to-JavaScript bridge methods and data contracts.
- Application configuration management or local user profile schemas.
- Standalone packaging or PyInstaller recipes.

### 5.3 Privacy & Data Sanitization Rule

- **Strict Anonymization**: The original Excel workbook (`references/Dan BudgetingV3.xlsx`) contains personal financial data.
- **NEVER** hardcode real salary figures, personal account balances, transaction names, or private information into application source code, tests, or public documentation.
- All application modules must use configurable defaults, placeholder fixture data, or user-supplied local JSON/SQLite files stored outside source control.

### 5.4 Vault Structure & Taxonomy

Documentation within `budgeting-app-documentation/` must adhere to:
- **`00 - Index/`**: Maps of Content (MOC), root indexes, and high-level navigation (`[[MOC - Budgeting App]]`).
- **`01 - Architecture/`**: Core technical architecture, PyWebView API bridge, state management, and UI layout.
- **`02 - Tax & Salary Specs/`**: Reverse-engineered specifications for BIR TRAIN Law, SSS, PhilHealth, Pag-IBIG, and 13th-month bonus logic.
- **`03 - Budgeting Specs/`**: Workbook data models, income/expense hierarchies, savings rates, and metric calculations.
- **`04 - User Guides/`**: User manual, local data storage guides, and privacy documentation.
- **`05 - Releases & Changelog/`**: Historical release notes (`vX.Y.Z.md`).
- **`06 - Development/`**: Developer workflow, testing strategy, and PyInstaller build recipes.

### 5.5 Obsidian Markdown Conventions

- **YAML Frontmatter**: Standardized frontmatter for every note:
  ```yaml
  ---
  title: "<Note Title>"
  tags:
    - budgeting-app
    - <category-tag>
  status: active # active | draft | deprecated | archived
  last_modified: YYYY-MM-DD
  source_of_truth:
    - <relative/path/to/source/file>
  ---
  ```
- **Wikilinks**: Use `[[Target Note Name]]` or `[[Target Note Name|Display Text]]`.
- **Mermaid Diagrams**: Use flowcharts and sequence diagrams to visualize calculation pipelines and user workflows.

## 6. Executable Packaging & Code Signing

Whenever the application is exported, compiled, or packaged as a standalone Windows executable (`.exe`):
- **Windows PE Version Information**: `app/file_version_info.txt` must always be maintained with official copyright (`Copyright © 2026 Dan Joseph Ortega. All rights reserved.`), product name (`Budgeting & Salary Suite`), and version numbers synchronized with `app/ui.html`.
- **PyInstaller Integration**: Packaging scripts (`build.bat` and `budget_app.spec`) must embed `file_version_info.txt` via `--version-file` / `version='file_version_info.txt'`.
- **Authenticode Code Signing**: If a valid project Authenticode certificate is available, executable binaries compiled in `dist/` should be digitally signed via `sign_exe.ps1` using `signtool.exe`. Never fabricate certificates or thumbprints.
