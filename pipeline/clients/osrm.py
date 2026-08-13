"""OSRM demo router -- real street-network drive times and routing."""
from __future__ import annotations

import json
import sys
import time

import requests

from ..core.api_client import ApiClient


class OsrmClient(ApiClient):
    BASE_URL = "https://router.project-osrm.org"

    def table(self, coords: list[str], params: dict, *, retries: int = 1, timeout: int = 60) -> dict:
        """/table call: batched many-to-one driving durations. coords are
        "lon,lat" strings, first entry is the source. retries>1 adds a
        backoff retry loop (used where the pipeline batches many chunks)."""
        url = f"{self.BASE_URL}/table/v1/driving/" + ";".join(coords)
        if retries <= 1:
            resp = requests.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp.json()

        for attempt in range(retries):
            try:
                resp = requests.get(url, params=params, timeout=timeout)
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.RequestException as exc:
                wait = 5 * (attempt + 1)
                print(f"  OSRM request failed ({exc}), retrying in {wait}s...", file=sys.stderr)
                time.sleep(wait)
        raise RuntimeError(f"OSRM request failed after retries: {url[:120]}...")

    def route_cached(
        self,
        site_lat: float,
        site_lon: float,
        target_lat: float,
        target_lon: float,
        cache_name: str,
        *,
        timeout: int = 25,
    ) -> dict | None:
        """/route call for a single site->target pair, cached to disk.
        Returns None (uncached) if OSRM responds with a non-200 status."""
        cache_path = self._cache_path(cache_name)
        if cache_path.exists():
            return json.loads(cache_path.read_text(encoding="utf-8"))

        url = f"{self.BASE_URL}/route/v1/driving/{site_lon:.6f},{site_lat:.6f};{target_lon:.6f},{target_lat:.6f}"
        resp = requests.get(url, params={"overview": "false"}, headers=self.HEADERS, timeout=timeout)
        if resp.status_code != 200:
            return None
        data = resp.json()
        cache_path.write_text(json.dumps(data), encoding="utf-8")
        return data
