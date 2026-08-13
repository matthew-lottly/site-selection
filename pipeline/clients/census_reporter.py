"""Census Reporter API -- ACS 5-year demographic estimates, by table id."""
from __future__ import annotations

from ..core.api_client import ApiClient


class CensusReporterClient(ApiClient):
    BASE_URL = "https://api.censusreporter.org/1.0/data/show/latest"
    HEADERS = {"User-Agent": "houston-site-selection-case-study/1.0"}

    def fetch_batch(self, table_ids: str, geoids: list[str], *, geo_prefix: str = "14000US", release: str | None = None) -> dict:
        """Uncached (the caller does its own row-level CSV caching)."""
        ids = ",".join(f"{geo_prefix}{g}" for g in geoids)
        url = self.BASE_URL if release is None else self.BASE_URL.replace("/show/latest", f"/show/{release}")
        data = self._request(url, {"table_ids": table_ids, "geo_ids": ids}, headers=self.HEADERS, timeout=40)
        return data.get("data", {})
