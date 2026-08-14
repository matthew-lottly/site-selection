"""Census LEHD LODES (Longitudinal Employer-Household Dynamics) -- real,
free, block-level workplace/employment counts. Direct gzipped-CSV download,
no key, same distribution the Census Bureau's own OnTheMap tool is built on."""
from __future__ import annotations

from pathlib import Path

import requests

from ..core.paths import RAW


class LehdClient:
    URL_TEMPLATE = "https://lehd.ces.census.gov/data/lodes/LODES8/{state}/wac/{state}_wac_S000_JT00_{year}.csv.gz"
    HEADERS = {"User-Agent": "curl/8.7.1", "Accept": "*/*"}

    def __init__(self, cache_dir: Path = RAW) -> None:
        self.cache_dir = cache_dir

    def fetch_wac_csv_gz(self, state: str, year: int) -> Path:
        """Download (or reuse the cached copy of) one state's Workplace Area
        Characteristics file -- real total job counts (field C000) per Census
        block (field w_geocode)."""
        cache_path = self.cache_dir / f"lehd_wac_{state}_{year}.csv.gz"
        if cache_path.exists():
            return cache_path
        resp = requests.get(self.URL_TEMPLATE.format(state=state, year=year), headers=self.HEADERS, timeout=90)
        resp.raise_for_status()
        cache_path.write_bytes(resp.content)
        return cache_path
