"""Step 32: real HUD Low-Income Housing Tax Credit (LIHTC) affordable-housing
unit counts within 1.0 mile of each of the 20 citywide finalists -- a real,
free, point-level proxy for concentration of Family Dollar's core low-income
customer base near a candidate site. Free, keyless, ArcGIS REST Feature
Service (verified live directly against the source before building this).

Output: data/processed/site_lihtc.csv
"""
from __future__ import annotations

import csv
import sys

from ..clients import HudLihtcClient
from ..core import PROCESSED, PipelineStage
from ..geometry import Geometry

RADIUS_MI = 1.0


class LihtcPropertiesStage(PipelineStage):
    id = "32"
    name = "lihtc_properties"
    description = "Real HUD LIHTC affordable-housing unit counts within 1.0mi of each finalist"
    outputs = (PROCESSED / "site_lihtc.csv", PROCESSED / "lihtc_properties_detail.csv")

    def __init__(self) -> None:
        self.client = HudLihtcClient()

    def run(self) -> None:
        with open(PROCESSED / "sites_enriched.csv", encoding="utf-8") as fh:
            sites = list(csv.DictReader(fh))

        rows = []
        detail_rows = []
        for s in sites:
            lat, lon = float(s["lat"]), float(s["lon"])
            properties = self.query_nearby(lat, lon, s["hcad_num"])

            total_units = sum(p["units"] for p in properties)
            rows.append(
                {
                    "hcad_num": s["hcad_num"],
                    "site_label": s["site_label"],
                    "lihtc_property_count_1mi": len(properties),
                    "lihtc_unit_count_1mi": total_units,
                }
            )
            for p in properties:
                detail_rows.append(
                    {"hcad_num": s["hcad_num"], "name": p["name"], "units": p["units"], "lat": p["lat"], "lon": p["lon"]}
                )
            print(
                f"{s['site_label']}: {len(properties)} real LIHTC properties, {total_units} units within 1.0mi",
                file=sys.stderr,
            )

        out_path = PROCESSED / "site_lihtc.csv"
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        detail_path = PROCESSED / "lihtc_properties_detail.csv"
        with open(detail_path, "w", newline="", encoding="utf-8") as fh:
            fieldnames = ["hcad_num", "name", "units", "lat", "lon"]
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(detail_rows)

        print(f"\nWrote real LIHTC proximity data for {len(rows)} sites -> {out_path}", file=sys.stderr)
        print(f"Wrote {len(detail_rows)} individual real LIHTC property points -> {detail_path}", file=sys.stderr)

    def query_nearby(self, lat: float, lon: float, hcad_num: str) -> list[dict]:
        lat_pad = RADIUS_MI / 69.0
        lon_pad = RADIUS_MI / 60.0
        envelope = f"{lon - lon_pad},{lat - lat_pad},{lon + lon_pad},{lat + lat_pad}"

        properties: list[dict] = []
        offset = 0
        while True:
            data = self.client.query(
                {
                    "geometry": envelope,
                    "geometryType": "esriGeometryEnvelope",
                    "inSR": "4326",
                    "outSR": "4326",
                    "spatialRel": "esriSpatialRelIntersects",
                    "outFields": "PROJECT,STD_ADDR,STD_CITY,N_UNITS,LI_UNITS",
                    "returnGeometry": "true",
                    "resultOffset": offset,
                    "resultRecordCount": 500,
                    "f": "json",
                },
                cache_name=f"hud_lihtc_{hcad_num}_{offset}",
            )
            feats = data.get("features", [])
            for feat in feats:
                a = feat["attributes"]
                geom = feat.get("geometry") or {}
                if "x" not in geom or "y" not in geom:
                    continue
                plat, plon = geom["y"], geom["x"]
                if Geometry.haversine_miles(lat, lon, plat, plon) > RADIUS_MI:
                    continue
                units = a.get("N_UNITS") or 0
                properties.append({"name": a.get("PROJECT") or "unnamed", "units": units, "lat": plat, "lon": plon})
            if not data.get("exceededTransferLimit") or not feats:
                break
            offset += len(feats)
        return properties


if __name__ == "__main__":
    LihtcPropertiesStage().run()
