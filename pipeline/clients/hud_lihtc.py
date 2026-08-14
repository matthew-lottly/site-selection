"""HUD Low-Income Housing Tax Credit (LIHTC) Properties -- real, point-level,
geocoded affordable-housing developments, served as a public ArcGIS REST
Feature Service (same access pattern as FemaClient/TxDotClient)."""
from __future__ import annotations

from ..core.api_client import ApiClient


class HudLihtcClient(ApiClient):
    BASE_URL = "https://egis.hud.gov/arcgis/rest/services/gotit/LIHTCProperties/MapServer/0/query"

    def query(self, params: dict, cache_name: str) -> dict:
        return self.get_json(self.BASE_URL, params, cache_name)
