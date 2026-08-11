"""Step 5: Find real intersections between Sunnyside / South Union's named
arterial roads (pulled from OpenStreetMap in script 04b) as literal anchor
points for candidate-site search -- the same way a site selector would scan
a road atlas for corner locations on high-traffic arterials.

Output: data/processed/intersections.csv
"""
from __future__ import annotations

import csv
import itertools
import json
import sys

from lib import PROCESSED, RAW, haversine_miles

MAX_DIST_MI = 0.035  # ~185 ft: treat as the same intersection


def main() -> None:
    data = json.loads((RAW / "overpass_roads.json").read_text(encoding="utf-8"))

    roads: dict[str, list[tuple[float, float]]] = {}
    for el in data["elements"]:
        name = el["tags"].get("name")
        geom = el.get("geometry") or []
        if not name or not geom:
            continue
        roads.setdefault(name, []).extend((pt["lat"], pt["lon"]) for pt in geom)

    print(f"Loaded {len(roads)} named roads: {list(roads.keys())}", file=sys.stderr)

    found = []
    seen_coords = []
    for name_a, name_b in itertools.combinations(roads.keys(), 2):
        best = None
        for lat_a, lon_a in roads[name_a]:
            for lat_b, lon_b in roads[name_b]:
                d = haversine_miles(lat_a, lon_a, lat_b, lon_b)
                if best is None or d < best[0]:
                    best = (d, lat_a, lon_a, lat_b, lon_b)
        if best and best[0] <= MAX_DIST_MI:
            lat = (best[1] + best[3]) / 2
            lon = (best[2] + best[4]) / 2
            # dedupe near-identical intersections
            dupe = any(haversine_miles(lat, lon, s[0], s[1]) < 0.05 for s in seen_coords)
            if dupe:
                continue
            seen_coords.append((lat, lon))
            found.append({"road_a": name_a, "road_b": name_b, "lat": round(lat, 6), "lon": round(lon, 6)})

    out_path = PROCESSED / "intersections.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["road_a", "road_b", "lat", "lon"])
        writer.writeheader()
        writer.writerows(found)

    print(f"Found {len(found)} intersections -> {out_path}", file=sys.stderr)
    for f in found:
        print(f"  {f['road_a']} x {f['road_b']}  ({f['lat']}, {f['lon']})", file=sys.stderr)


if __name__ == "__main__":
    main()
