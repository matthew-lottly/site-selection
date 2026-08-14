"""USDA Economic Research Service -- Food Access Research Atlas / SNAP-
authorized Retailer Access Map (SRAM), the current (2026) name for the same
long-running "food desert" dataset. Real, free, census-tract-level, direct
ZIP-of-CSVs download, no key."""
from __future__ import annotations

from pathlib import Path

import requests

from ..core.paths import RAW


class UsdaFoodAccessClient:
    URL = "https://www.ers.usda.gov/media/29395/2025-snap-authorized-retailer-access-map-sram-data.zip"
    HEADERS = {"User-Agent": "curl/8.7.1", "Accept": "*/*"}

    def __init__(self, cache_dir: Path = RAW) -> None:
        self.cache_dir = cache_dir

    def fetch_zip(self) -> Path:
        cache_path = self.cache_dir / "usda_food_access_sram.zip"
        if cache_path.exists():
            return cache_path
        resp = requests.get(self.URL, headers=self.HEADERS, timeout=120)
        resp.raise_for_status()
        cache_path.write_bytes(resp.content)
        return cache_path
