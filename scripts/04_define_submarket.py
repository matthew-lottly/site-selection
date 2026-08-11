"""Step 4: Lock in the target submarket identified by the macro gap screen
(scripts/03_gap_analysis.py) -- Sunnyside / South Union, Houston, TX -- and
pull real tract + block group polygon geometry for it, plus real TxDOT AADT
traffic-count points inside the study area.

Why Sunnyside / South Union:
  - The four highest-scoring adjacent tract clusters in the county-wide gap
    screen (scripts/03_gap_analysis.py output) all sit inside this ~3x3 mile
    corridor (roughly Loop 610 / MLK Blvd / Reed Rd / Cullen Blvd).
  - Zero existing Family Dollar, Dollar General, or Dollar Tree locations
    inside the corridor (verified against the OSM competitor pull).
  - It is a real, named, well-documented Houston neighborhood (City of
    Houston Complete Communities target area), not a statistical artifact.

Output:
  data/processed/submarket_tracts.geojson    (tract polygons + demo/gap fields)
  data/processed/submarket_blockgroups.geojson (block group polygons + pop)
  data/processed/aadt_points.csv             (real TxDOT AADT counts in area)
"""
from __future__ import annotations

import csv
import json
import sys

import requests

from lib import PROCESSED, RAW, TIGERWEB, TXDOT_AADT, cached_get

# Sunnyside / South Union / Reveille Park study envelope (lon_min, lat_min, lon_max, lat_max)
SUBMARKET_BBOX = (-95.41, -95.29, 29.615, 29.725)  # unused ordering placeholder
ENVELOPE = {"xmin": -95.41, "ymin": 29.615, "xmax": -95.29, "ymax": 29.725}


def fetch_polygons(layer: int, cache_name: str) -> dict:
    data = cached_get(
        f"{TIGERWEB}/{layer}/query",
        {
            "geometry": json.dumps(ENVELOPE),
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "GEOID,NAME,AREALAND",
            "outSR": "4326",
            "returnGeometry": "true",
            "f": "json",
        },
        cache_name,
    )
    return data


def esri_to_geojson_polygon(rings: list) -> dict:
    return {"type": "Polygon", "coordinates": rings}


def main() -> None:
    scores = {}
    with open(PROCESSED / "tract_scores.csv", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            scores[row["geoid"]] = row

    tract_data = fetch_polygons(8, "tigerweb_submarket_tracts")
    features = []
    for f in tract_data["features"]:
        geoid = f["attributes"]["GEOID"]
        s = scores.get(geoid, {})
        features.append(
            {
                "type": "Feature",
                "geometry": esri_to_geojson_polygon(f["geometry"]["rings"]),
                "properties": {
                    "geoid": geoid,
                    "name": f["attributes"]["NAME"],
                    "population": s.get("population"),
                    "median_hh_income": s.get("median_hh_income"),
                    "poverty_rate": s.get("poverty_rate"),
                    "nearest_dollar_store_mi": s.get("nearest_dollar_store_mi"),
                    "gap_score": s.get("gap_score"),
                },
            }
        )
    fc = {"type": "FeatureCollection", "features": features}
    (PROCESSED / "submarket_tracts.geojson").write_text(json.dumps(fc), encoding="utf-8")
    print(f"Wrote {len(features)} submarket tracts", file=sys.stderr)

    bg_data = fetch_polygons(10, "tigerweb_submarket_blockgroups")
    bg_features = []
    for f in bg_data["features"]:
        bg_features.append(
            {
                "type": "Feature",
                "geometry": esri_to_geojson_polygon(f["geometry"]["rings"]),
                "properties": {
                    "geoid": f["attributes"]["GEOID"],
                    "name": f["attributes"]["NAME"],
                    "arealand": f["attributes"]["AREALAND"],
                },
            }
        )
    bg_fc = {"type": "FeatureCollection", "features": bg_features}
    (PROCESSED / "submarket_blockgroups.geojson").write_text(json.dumps(bg_fc), encoding="utf-8")
    print(f"Wrote {len(bg_features)} submarket block groups", file=sys.stderr)

    # TxDOT AADT points inside the same envelope
    cache_path = RAW / "txdot_aadt_submarket.json"
    if cache_path.exists():
        aadt_data = json.loads(cache_path.read_text(encoding="utf-8"))
    else:
        resp = requests.get(
            f"{TXDOT_AADT}",
            params={
                "geometry": f"{ENVELOPE['xmin']},{ENVELOPE['ymin']},{ENVELOPE['xmax']},{ENVELOPE['ymax']}",
                "geometryType": "esriGeometryEnvelope",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "TRFC_STATN_ID,AADT_RPT_YEAR,AADT_RPT_QTY,ON_ROAD,LATITUDE,LONGITUDE,ACTIVE",
                "returnGeometry": "false",
                "f": "json",
            },
            timeout=30,
        )
        resp.raise_for_status()
        aadt_data = resp.json()
        cache_path.write_text(json.dumps(aadt_data), encoding="utf-8")

    rows = []
    for f in aadt_data.get("features", []):
        a = f["attributes"]
        rows.append(
            {
                "station_id": a["TRFC_STATN_ID"],
                "year": a["AADT_RPT_YEAR"],
                "aadt": a["AADT_RPT_QTY"],
                "road": a["ON_ROAD"],
                "lat": a["LATITUDE"],
                "lon": a["LONGITUDE"],
                "active": a["ACTIVE"],
            }
        )
    with open(PROCESSED / "aadt_points.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["station_id", "year", "aadt", "road", "lat", "lon", "active"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} TxDOT AADT stations in submarket", file=sys.stderr)
    for r in sorted(rows, key=lambda r: -r["aadt"])[:15]:
        print(f"  {r['road']:<12} AADT {r['aadt']:>7} ({r['year']}) @ {r['lat']},{r['lon']}", file=sys.stderr)


if __name__ == "__main__":
    main()
