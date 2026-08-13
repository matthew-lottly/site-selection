"""FEMA National Flood Hazard Layer (NFHL) -- flood zone identify."""
from __future__ import annotations

from ..core.api_client import ApiClient


class FemaClient(ApiClient):
    BASE_URL = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"

    def query(self, params: dict, cache_name: str) -> dict:
        return self.get_json(self.BASE_URL, params, cache_name)
