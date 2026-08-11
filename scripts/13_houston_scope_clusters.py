"""Step 13 (supersedes the single-submarket shortcut in scripts 04-06):
Scope the analysis to the REAL City of Houston boundary (not all of Harris
County, which also contains separate incorporated cities like Pasadena,
Baytown, Pearland, and Katy) and identify multiple, geographically spread
opportunity clusters across the whole city -- not just one neighborhood.

Data: TIGERweb Incorporated Places (GEOID 4835000 = "Houston city"), the
real city limits polygon, ~70,800 boundary vertices reflecting Houston's
actual (very irregular, annexation-driven) shape.

Output:
  data/processed/houston_boundary.geojson   (real city limits, for the map)
  data/processed/houston_tracts.csv         (tract_scores.csv filtered to tracts whose
                                              centroid falls inside city limits)
  data/processed/clusters.csv               (top spread-out opportunity clusters
                                              citywide, each with a search bbox)
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict

from lib import PROCESSED, RAW, haversine_miles, point_in_rings_fast, ring_bbox, simplify_ring

SIMPLIFY_TOLERANCE_DEG = 0.0003  # ~30m; shrinks display file size, source data untouched

N_CLUSTERS = 10
MIN_CLUSTER_SEPARATION_MI = 2.75
GRID_CELL_DEG = 0.035
MIN_TRACT_DENSITY_PER_SQMI = 1200  # exclude sparse/non-neighborhood tracts (parks, industrial, airports)


def main() -> None:
    boundary_raw = json.loads((RAW / "tigerweb_houston_boundary.json").read_text(encoding="utf-8"))
    feat = boundary_raw["features"][0]
    rings = feat["geometry"]["rings"]
    bboxes = [ring_bbox(r) for r in rings]
    print(f"Loaded Houston city boundary: {len(rings)} rings, {sum(len(r) for r in rings)} vertices", file=sys.stderr)

    # simplify only the copy written for map display -- `rings`/`bboxes` above stay at
    # full source precision for the point-in-polygon tract/site filtering below
    simplified_rings = [simplify_ring(r, SIMPLIFY_TOLERANCE_DEG) for r in rings]
    print(f"Simplified for display: {sum(len(r) for r in simplified_rings)} vertices", file=sys.stderr)

    boundary_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Houston city limits"},
                "geometry": {"type": "Polygon", "coordinates": simplified_rings},
            }
        ],
    }
    (PROCESSED / "houston_boundary.geojson").write_text(json.dumps(boundary_geojson), encoding="utf-8")

    with open(PROCESSED / "tract_scores.csv", encoding="utf-8") as fh:
        tracts = list(csv.DictReader(fh))

    in_city = []
    for t in tracts:
        lat, lon = float(t["lat"]), float(t["lon"])
        if point_in_rings_fast(lat, lon, rings, bboxes):
            in_city.append(t)
    print(f"{len(in_city)} of {len(tracts)} Harris County tracts have centroids inside Houston city limits", file=sys.stderr)

    with open(PROCESSED / "houston_tracts.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(tracts[0].keys()))
        writer.writeheader()
        writer.writerows(in_city)

    # density filter to avoid parks/industrial/airport tracts skewing clusters
    def density(r):
        a = float(r["aland_sqmi"])
        return float(r["population"]) / a if a > 0 else 0

    candidates = sorted(
        [r for r in in_city if density(r) >= MIN_TRACT_DENSITY_PER_SQMI],
        key=lambda r: -float(r["gap_score"]),
    )[:250]

    grid: dict[tuple, list] = defaultdict(list)
    for r in candidates:
        key = (round(float(r["lat"]) / GRID_CELL_DEG), round(float(r["lon"]) / GRID_CELL_DEG))
        grid[key].append(r)

    cell_clusters = []
    for key, members in grid.items():
        if len(members) < 2:
            continue
        score = sum(float(m["gap_score"]) for m in members)
        lat = sum(float(m["lat"]) for m in members) / len(members)
        lon = sum(float(m["lon"]) for m in members) / len(members)
        cell_clusters.append({"score": score, "n": len(members), "lat": lat, "lon": lon, "members": members})
    cell_clusters.sort(key=lambda c: -c["score"])

    picked = []
    for c in cell_clusters:
        if any(haversine_miles(c["lat"], c["lon"], p["lat"], p["lon"]) < MIN_CLUSTER_SEPARATION_MI for p in picked):
            continue
        picked.append(c)
        if len(picked) >= N_CLUSTERS:
            break

    rows = []
    for i, c in enumerate(picked, start=1):
        lats = [float(m["lat"]) for m in c["members"]]
        lons = [float(m["lon"]) for m in c["members"]]
        pad = 0.045
        rows.append(
            {
                "cluster_id": f"C{i}",
                "score": round(c["score"]),
                "n_tracts": c["n"],
                "lat": round(c["lat"], 5),
                "lon": round(c["lon"], 5),
                "bbox_min_lat": round(min(lats) - pad, 5),
                "bbox_max_lat": round(max(lats) + pad, 5),
                "bbox_min_lon": round(min(lons) - pad, 5),
                "bbox_max_lon": round(max(lons) + pad, 5),
                "sample_tracts": "; ".join(m["name"] for m in c["members"][:4]),
            }
        )

    out_path = PROCESSED / "clusters.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nTop {len(rows)} opportunity clusters, spread across Houston city limits:", file=sys.stderr)
    for r in rows:
        print(f"  {r['cluster_id']}: score={r['score']:>6}  n_tracts={r['n_tracts']}  ({r['lat']},{r['lon']})  e.g. {r['sample_tracts']}", file=sys.stderr)
    print(f"\nWrote {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
