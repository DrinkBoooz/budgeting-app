"""Tests for UI Consistency, Canonical Version Badge, and Asset Link Integrity."""

from pathlib import Path
import re
import pytest

APP_DIR = Path(__file__).resolve().parent.parent / "app"
UI_HTML_PATH = APP_DIR / "ui.html"


def test_ui_html_exists():
    assert UI_HTML_PATH.exists() is True


def test_canonical_version_badge():
    """Verify that ui.html displays the canonical version badge Release v0.1.0."""
    content = UI_HTML_PATH.read_text(encoding="utf-8")
    match = re.search(r'<span class="badge-version">Release v(\d+\.\d+\.\d+)</span>', content)
    assert match is not None, "Missing or invalid canonical version badge in app/ui.html"
    version = match.group(1)
    assert version == "0.1.0"


def test_five_functional_tabs_exist():
    """Verify all 5 tabs exist in navigation and matching tab panes."""
    content = UI_HTML_PATH.read_text(encoding="utf-8")
    expected_tabs = [
        "tab-salary",
        "tab-schedule",
        "tab-bills",
        "tab-settlements",
        "tab-dashboard",
    ]
    for tab_id in expected_tabs:
        assert f'data-tab="{tab_id}"' in content
        assert f'id="{tab_id}"' in content


def test_all_linked_assets_exist():
    """Verify every linked CSS and JS file in ui.html exists on disk."""
    content = UI_HTML_PATH.read_text(encoding="utf-8")

    # Check CSS links
    css_matches = re.findall(r'<link rel="stylesheet" href="([^"]+)">', content)
    assert len(css_matches) >= 5
    for css_rel in css_matches:
        css_file = APP_DIR / css_rel
        assert css_file.exists() is True, f"Missing CSS asset: {css_file}"

    # Check JS scripts
    js_matches = re.findall(r'<script src="([^"]+)"></script>', content)
    assert len(js_matches) >= 8
    for js_rel in js_matches:
        js_file = APP_DIR / js_rel
        assert js_file.exists() is True, f"Missing JS asset: {js_file}"
