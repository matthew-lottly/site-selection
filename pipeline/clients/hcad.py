"""Harris County Appraisal District (HCAD) -- real parcel boundaries and land use."""
from __future__ import annotations

from ..core.api_client import ApiClient


class HcadClient(ApiClient):
    BASE_URL = "https://www.gis.hctx.net/arcgis/rest/services/HCAD/Parcels/MapServer/0/query"

    def query(self, params: dict, cache_name: str) -> dict:
        return self.get_json(self.BASE_URL, params, cache_name)
