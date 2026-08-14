"""Step 38: real HUD Multifamily Properties (FHA-insured/HUD-assisted
apartments, senior housing, assisted living) within 1.0 mile of each of the
20 citywide finalists -- a real, free, point-level proxy for concentration
of Family Dollar's core customer base, complementary to (not a duplicate of)
the LIHTC signal already in the model: LIHTC properties are funded through
tax credits, these through FHA mortgage insurance and project-based rental
assistance -- a different federal program with a real, only partially
overlapping property universe. Verified live (`curl`) before building:
165 real Houston-city properties returned at query time.

Only the real `TOTAL_ASSISTED_UNIT_COUNT` field is used, not total unit
count -- some HUD-insured multifamily properties are market-rate with no
income restriction, so counting all units would misstate the low-income
demand signal this factor is meant to capture.

This layer's query endpoint returns `"geometry": null` for every feature
despite declaring point geometry and despite `returnGeometry=true` -- a
real, confirmed limitation of this specific HUD service (checked directly
with `f=geojson` before writing any workaround, not assumed). The server's
spatial filter still works correctly server-side, so an envelope query
still returns the real, correct set of nearby properties; each one is then
geocoded from its own real street address via Nominatim
(`HudMultifamilyClient.geocode_address`) to recover real coordinates,
rather than silently dropping the source or approximating a location.

Output: data/processed/site_hud_multifamily.csv
"""
from __future__ import annotations

import csv
import sys

from ..clients import HudMultifamilyClient
from ..core import PROCESSED, PipelineStage
from ..geometry import Geometry

RADIUS_MI = 1.0


class HudMultifamilyStage(PipelineStage):
    id = "38"
    name = "hud_multifamily"
    description = "Real HUD Multifamily (FHA-insured/assisted) unit counts within 1.0mi of each finalist"
    outputs = (PROCESSED / "site_hud_multifamily.csv", PROCESSED / "hud_multifamily_detail.csv")

    def __init__(self) -> None:
        self.client = HudMultifamilyClient()

    def run(self) -> None:
        with open(PROCESSED / "sites_enriched.csv", encoding="utf-8") as fh:
            sites = list(csv.DictReader(fh))

        rows = []
        detail_rows = []
        geocode_misses = 0
        for s in sites:
            lat, lon = float(s["lat"]), float(s["lon"])
            properties = self.query_nearby(lat, lon, s["hcad_num"])
            geocode_misses += sum(1 for p in properties if p is None)
            properties = [p for p in properties if p is not None]
            in_radius = [p for p in properties if Geometry.haversine_miles(lat, lon, p["lat"], p["lon"]) <= RADIUS_MI]

            total_assisted_units = sum(p["assisted_units"] for p in in_radius)
            rows.append(
                {
                    "hcad_num": s["hcad_num"],
                    "site_label": s["site_label"],
                    "hud_multifamily_property_count_1mi": len(in_radius),
                    "hud_multifamily_assisted_unit_count_1mi": total_assisted_units,
                }
            )
            for p in in_radius:
                detail_rows.append(
                    {"hcad_num": s["hcad_num"], "name": p["name"], "assisted_units": p["assisted_units"], "lat": p["lat"], "lon": p["lon"]}
                )
            print(
                f"{s['site_label']}: {len(in_radius)} real HUD Multifamily properties, {total_assisted_units} assisted units within 1.0mi",
                file=sys.stderr,
            )

        out_path = PROCESSED / "site_hud_multifamily.csv"
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        detail_path = PROCESSED / "hud_multifamily_detail.csv"
        with open(detail_path, "w", newline="", encoding="utf-8") as fh:
            fieldnames = ["hcad_num", "name", "assisted_units", "lat", "lon"]
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(detail_rows)

        print(f"\nWrote real HUD Multifamily proximity data for {len(rows)} sites -> {out_path}", file=sys.stderr)
        print(f"Wrote {len(detail_rows)} individual real HUD Multifamily property points -> {detail_path}", file=sys.stderr)
        if geocode_misses:
            print(f"Note: {geocode_misses} real property record(s) could not be geocoded from their address and were excluded, not guessed.", file=sys.stderr)

    def query_nearby(self, lat: float, lon: float, hcad_num: str) -> list[dict | None]:
        lat_pad = RADIUS_MI / 69.0
        lon_pad = RADIUS_MI / 60.0
        envelope = f"{lon - lon_pad},{lat - lat_pad},{lon + lon_pad},{lat + lat_pad}"

        properties: list[dict | None] = []
        offset = 0
        while True:
            data = self.client.query(
                {
                    "geometry": envelope,
                    "geometryType": "esriGeometryEnvelope",
                    "inSR": "4326",
                    "outSR": "4326",
                    "spatialRel": "esriSpatialRelIntersects",
                    "outFields": "PROPERTY_NAME_TEXT,STD_ADDR,STD_CITY,STD_ST,STD_ZIP5,TOTAL_ASSISTED_UNIT_COUNT,TOTAL_UNIT_COUNT",
                    "returnGeometry": "true",
                    "resultOffset": offset,
                    "resultRecordCount": 500,
                    "f": "json",
                },
                cache_name=f"hud_multifamily_{hcad_num}_{offset}",
            )
            feats = data.get("features", [])
            for feat in feats:
                a = feat["attributes"]
                assisted_units = a.get("TOTAL_ASSISTED_UNIT_COUNT") or 0
                if assisted_units <= 0:
                    continue
                coords = self.client.geocode_address(
                    a.get("STD_ADDR") or "", a.get("STD_CITY") or "", a.get("STD_ST") or "", a.get("STD_ZIP5") or ""
                )
                if coords is None:
                    properties.append(None)
                    continue
                plat, plon = coords
                properties.append({"name": a.get("PROPERTY_NAME_TEXT") or "unnamed", "assisted_units": assisted_units, "lat": plat, "lon": plon})
            if not data.get("exceededTransferLimit") or not feats:
                break
            offset += len(feats)
        return properties


if __name__ == "__main__":
    HudMultifamilyStage().run()
