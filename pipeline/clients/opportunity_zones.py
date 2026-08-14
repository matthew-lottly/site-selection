"""Federal Qualified Opportunity Zones -- real, free, live ArcGIS Feature
Service (`Federal_User_Community` org on ArcGIS Online), verified directly
before use: ~100+ real Harris County tract polygons returned at query time.
A real federal tax-advantaged-investment designation, correlated with
underserved areas -- the same demand thesis as the food-access/LIHTC
signals already in this model.

This service's polygons use 2010 vintage Census tract boundaries, while the
rest of this pipeline uses 2020 vintage tracts (confirmed by comparing tract
IDs directly - e.g. this service's Harris County list includes
"48201311700" where this project's own 2020-vintage tract file has
"48201311701", a real post-2020-redistricting split). Matching by tract ID
would risk a real, silent mismatch, so this client is queried by real point
geometry (does a site's own lat/lon fall inside a real OZ polygon) instead
of by tract-ID lookup -- the same point-intersect approach already used for
FEMA flood zones, and immune to the vintage mismatch entirely."""
from __future__ import annotations

from ..core.api_client import ApiClient


class OpportunityZonesClient(ApiClient):
    BASE_URL = "https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/Opportunity_Zones_1/FeatureServer/0/query"

    def query(self, params: dict, cache_name: str) -> dict:
        return self.get_json(self.BASE_URL, params, cache_name)
