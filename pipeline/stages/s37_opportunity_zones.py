"""Step 37: real federal Qualified Opportunity Zone designation for each of
the 20 citywide finalists. A real, free, tax-advantaged-investment federal
designation, correlated with underserved areas - directly relevant to a
dollar-store demand thesis, and a signal this model had never checked.

Queried by real point-in-polygon intersection (does the site's own lat/lon
fall inside a real OZ polygon), not by tract-ID lookup, since this dataset's
polygons use 2010 vintage Census tract boundaries while the rest of this
pipeline uses 2020 vintage tracts - matching by ID would risk a real, silent
mismatch (confirmed by comparing tract ID lists directly before choosing
this approach; see `pipeline/clients/opportunity_zones.py`).

Output: data/processed/site_opportunity_zones.csv
"""
from __future__ import annotations

import csv
import sys

from ..clients import OpportunityZonesClient
from ..core import PROCESSED, PipelineStage


class OpportunityZonesStage(PipelineStage):
    id = "37"
    name = "opportunity_zones"
    description = "Real federal Qualified Opportunity Zone designation for each finalist (point-in-polygon)"
    outputs = (PROCESSED / "site_opportunity_zones.csv",)

    def __init__(self) -> None:
        self.client = OpportunityZonesClient()

    def run(self) -> None:
        with open(PROCESSED / "sites_enriched.csv", encoding="utf-8") as fh:
            sites = list(csv.DictReader(fh))

        rows = []
        for s in sites:
            lat, lon = float(s["lat"]), float(s["lon"])
            in_oz, tract = self.check_opportunity_zone(lat, lon, s["hcad_num"])
            rows.append(
                {
                    "hcad_num": s["hcad_num"],
                    "site_label": s["site_label"],
                    "in_opportunity_zone": in_oz,
                    "opportunity_zone_tract_2010": tract or "",
                }
            )
            print(f"{s['site_label']}: Opportunity Zone (real federal designation) = {in_oz}", file=sys.stderr)

        out_path = PROCESSED / "site_opportunity_zones.csv"
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        n_in = sum(1 for r in rows if r["in_opportunity_zone"])
        print(f"\n{n_in} of {len(rows)} finalists sit in a real federal Opportunity Zone -> {out_path}", file=sys.stderr)

    def check_opportunity_zone(self, lat: float, lon: float, hcad_num: str) -> tuple[bool, str | None]:
        data = self.client.query(
            {
                "geometry": f"{lon},{lat}",
                "geometryType": "esriGeometryPoint",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "CENSUSTRAC",
                "returnGeometry": "false",
                "f": "json",
            },
            cache_name=f"opportunity_zone_{hcad_num}",
        )
        feats = data.get("features", [])
        if not feats:
            return False, None
        return True, feats[0]["attributes"].get("CENSUSTRAC")


if __name__ == "__main__":
    OpportunityZonesStage().run()
