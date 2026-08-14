"""Houston Police Department -- real, point-level NIBRS Part I crime incident
exports. Free, keyless, direct CSV download, back to 2009.

This is a different, real source from the one already documented as a dead
end in docs/data_validation.md #11 (Houston's data.houstontx.gov CKAN
catalog, which genuinely has no queryable crime dataset). HPD's own site
separately publishes actual incident-level data -- offense code, date, beat,
and lat/lon -- as direct static CSV files, not through the CKAN API at all.
"""
from __future__ import annotations

from pathlib import Path

import requests

from ..core.paths import RAW


class HpdCrimeClient:
    URL_TEMPLATE = "https://www.houstontx.gov/police/cs/xls/NIBRSPublicView{year}.csv"
    HEADERS = {"User-Agent": "curl/8.7.1", "Accept": "*/*"}

    def __init__(self, cache_dir: Path = RAW) -> None:
        self.cache_dir = cache_dir

    def fetch_year_csv(self, year: int) -> Path:
        """Download (or reuse the cached copy of) one calendar year's real NIBRS export."""
        cache_path = self.cache_dir / f"hpd_nibrs_{year}.csv"
        if cache_path.exists():
            return cache_path
        resp = requests.get(self.URL_TEMPLATE.format(year=year), headers=self.HEADERS, timeout=90)
        resp.raise_for_status()
        cache_path.write_bytes(resp.content)
        return cache_path
