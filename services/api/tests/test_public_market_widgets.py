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
        assert "pipmora-wordmark.svg" in html\n        assert "pipmora-icon.svg" in html
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


def test_all_site_headers_use_the_supplied_wordmark():
    for page in ("index.html", "markets.html", "lab.html"):
        html = (SITE / page).read_text(encoding="utf-8")
        assert 'pip-wordmark' in html
        assert 'pipmora-wordmark.svg?v=20261013' in html
        assert 'pipmora-mark.svg?v=2' not in html
    src = (ROOT / "apps/web/components/Brand.tsx").read_text(encoding="utf-8")
    assert 'pipmora-wordmark.svg?v=20261013' in src
    assert '/pipmora-mark.svg' not in src
    asset = (SITE / "assets/pipmora-wordmark.svg").read_text(encoding="utf-8")
    assert "PipMora candlestick wordmark" in asset
