"""Overpass API (OpenStreetMap) -- POIs, road network, transit stops."""
from __future__ import annotations

from ..core.api_client import ApiClient


class OverpassClient(ApiClient):
    BASE_URL = "https://overpass-api.de/api/interpreter"

    def query(self, ql: str, cache_name: str, *, timeout: int = 90) -> dict:
        return self.post_json(self.BASE_URL, {"data": ql}, cache_name, timeout=timeout)
