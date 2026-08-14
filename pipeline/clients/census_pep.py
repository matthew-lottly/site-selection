"""Census Population Estimates Program (PEP) -- real, free, annual place-level
population estimates. The PEP's REST API now requires a registered key (a
break from every other keyless source this project uses), so this goes
straight to the Bureau's own direct CSV file releases instead -- same
keyless-download pattern as HpdCrimeClient/LehdClient."""
from __future__ import annotations

from pathlib import Path

import requests

from ..core.paths import RAW


class CensusPepClient:
    PLACES_URL = "https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/cities/totals/sub-est2024.csv"
    HEADERS = {"User-Agent": "curl/8.7.1", "Accept": "*/*"}

    def __init__(self, cache_dir: Path = RAW) -> None:
        self.cache_dir = cache_dir

    def fetch_places_csv(self) -> Path:
        cache_path = self.cache_dir / "census_pep_places_2020_2024.csv"
        if cache_path.exists():
            return cache_path
        resp = requests.get(self.PLACES_URL, headers=self.HEADERS, timeout=60)
        resp.raise_for_status()
        cache_path.write_bytes(resp.content)
        return cache_path
