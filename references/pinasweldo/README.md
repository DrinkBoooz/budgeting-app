# Pinasweldo Static Reverse Engineering Reference

- **Target URL**: `https://pinasweldo.com`
- **Capture Date**: 2026-10-25
- **Method**: REA (Reverse-Engineer-Anything) static JavaScript bundle analysis.
- **Source Artifacts Captured**:
  - `references/pinasweldo/raw/index.html`: Static HTML snapshot.
  - `references/pinasweldo/raw/chunks/`: Complete set of 50 client-side Next.js / Turbopack JS chunks containing the full statutory calculation engine, bracket arrays, and rate rules.
- **Core Engine Chunks**:
  - `185ecivlr9cih.js`: Core math, monthly/semi-monthly withholding tables, SSS MSC step generator, PhilHealth rates, Pag-IBIG cap, and 13th-month tax exemption pool.
  - `0ijuwl9feg6mc.js`: Historical statutory brackets, de minimis caps, and TRAIN Law tax brackets.
- **Detailed Specification**:
  See Obsidian documentation vault:
  - `[[Pinasweldo Tax and Contributions Spec]]`
  - `[[Statutory Rate Tables 2026]]`
