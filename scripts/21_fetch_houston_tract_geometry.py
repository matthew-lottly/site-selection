"""Step 21: Pull real tract polygon geometry for every Census tract inside
Houston city limits (not just one submarket) so the web map can show the
opportunity-score choropleth across the whole city that was actually
screened.

Output: data/processed/houston_tracts.geojson
"""
from __future__ import annotations

import csv
import json
import sys

from lib import PROCESSED, RAW, TIGERWEB, cached_get, point_in_rings_fast, ring_bbox, simplify_ring

# Houston city bounding envelope (same as script 16)
ENVELOPE = {"xmin": -95.79, "ymin": 29.52, "xmax": -95.01, "ymax": 30.11}
SIMPLIFY_TOLERANCE_DEG = 0.0002  # ~20m; shrinks display file size, source data untouched


def main() -> None:
    boundary_raw = json.loads((RAW / "tigerweb_houston_boundary.json").read_text(encoding="utf-8"))
    rings = boundary_raw["features"][0]["geometry"]["rings"]
    bboxes = [ring_bbox(r) for r in rings]

    data = cached_get(
        f"{TIGERWEB}/8/query",
        {
            "geometry": json.dumps(ENVELOPE),
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "GEOID,NAME",
            "outSR": "4326",
            "returnGeometry": "true",
            "f": "json",
        },
        "tigerweb_houston_tract_geometry",
    )
    print(f"TIGERweb returned {len(data['features'])} tracts intersecting the Houston envelope", file=sys.stderr)

    scores = {}
    with open(PROCESSED / "tract_scores.csv", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            scores[row["geoid"]] = row

    features = []
    for f in data["features"]:
        geoid = f["attributes"]["GEOID"]
        s = scores.get(geoid)
        if not s:
            continue
        lat, lon = float(s["lat"]), float(s["lon"])
        if not point_in_rings_fast(lat, lon, rings, bboxes):
            continue
        simplified_rings = [simplify_ring(r, SIMPLIFY_TOLERANCE_DEG) for r in f["geometry"]["rings"]]
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": simplified_rings},
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
    out_path = PROCESSED / "houston_tracts.geojson"
    out_path.write_text(json.dumps(fc), encoding="utf-8")
    print(f"Wrote {len(features)} Houston-city tract polygons -> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
