"""Smoke checks: public market pages must not misrepresent fixed demonstration prices as live."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SITE = ROOT / "site"
CONFIG = re.compile(
    r'<script[^>]+src="https://s3\.tradingview\.com/external-embedding/'
    r'embed-widget-[^"]+\.js"[^>]*>(.*?)</script>', re.DOTALL
)


def test_all_market_widgets_use_valid_provider_configs():
    for page in ("index.html", "markets.html", "lab.html"):
        html = (SITE / page).read_text(encoding="utf-8")
        configs = CONFIG.findall(html)
        assert configs, f"No provider embeds found on {page}"
        for widget_config in configs:
            payload = json.loads(widget_config.strip())
            assert isinstance(payload, dict)
            assert payload


def test_public_pages_include_logo_and_attribution():
    for page in ("index.html", "markets.html", "lab.html"):
        html = (SITE / page).read_text(encoding="utf-8")
        assert "pipmora-mark.svg" in html
        assert "by TradingView" in html


def test_public_market_pages_do_not_fake_live_prices():
    for page in ("index.html", "markets.html"):
        html = (SITE / page).read_text(encoding="utf-8")
        assert "1.08436" not in html
        assert "1.31248" not in html
        assert "1.08642" not in html
        assert "SYNTHETIC DATA" not in html
    # The trading lab retains the explicit distinction between real quotes
    # and synthetic fills rather than implying that widget prices drive orders.
    lab = (SITE / "lab.html").read_text(encoding="utf-8")
    assert "do not set entry, stop, P/L or outcomes" in lab
