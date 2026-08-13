"""TIGERweb (Census Bureau) -- tract / block-group boundaries and geometry."""
from __future__ import annotations

from ..core.api_client import ApiClient

HARRIS_STATE_FIPS = "48"
HARRIS_COUNTY_FIPS = "201"


class TigerWebClient(ApiClient):
    BASE_URL = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer"

    def query(self, layer: int, params: dict, cache_name: str) -> dict:
        return self.get_json(f"{self.BASE_URL}/{layer}/query", params, cache_name)
