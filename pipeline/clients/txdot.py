"""TxDOT -- Annual Average Daily Traffic (AADT) counts."""
from __future__ import annotations

from ..core.api_client import ApiClient


class TxDotClient(ApiClient):
    BASE_URL = "https://services.arcgis.com/KTcxiTD9dsQw4r7Z/arcgis/rest/services/TxDOT_AADT_Annuals_(Public_View)/FeatureServer/0/query"

    def query(self, params: dict, cache_name: str) -> dict:
        return self.get_json(self.BASE_URL, params, cache_name)
