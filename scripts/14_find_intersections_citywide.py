"""Step 14 (generalizes the old scripts/05, which hand-picked Sunnyside's
street names): for EVERY opportunity cluster identified across Houston city
limits (scripts/13), auto-discover that area's named primary/secondary/
tertiary arterial roads directly from OpenStreetMap, then find real
intersections between them via spatial grid-bucketing (fast, no hardcoded
street lists, no O(n^2) blowup).

Output: data/processed/intersections.csv (cluster_id, road_a, road_b, lat, lon)
"""
from __future__ import annotations

import csv
import json
import sys
import time
from collections import defaultdict

import requests

from lib import OVERPASS, PROCESSED, RAW, haversine_miles

GRID_DEG = 0.0009  # ~100m bucket, generous enough to catch real corner intersections
DEDUPE_MI = 0.12
MAX_INTERSECTIONS_PER_CLUSTER = 10


def fetch_roads(cluster_id: str, min_lat, min_lon, max_lat, max_lon) -> list[dict]:
    cache_path = RAW / f"overpass_roads_{cluster_id}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))["elements"]
    # primary/secondary only: major arterials realistic for a freestanding discount-store pad
    q = (
        f'[out:json][timeout:60];way["highway"~"^(primary|secondary)$"]'
        f'["name"]({min_lat},{min_lon},{max_lat},{max_lon});out geom tags;'
    )
    for attempt in range(5):
        resp = requests.post(OVERPASS, data={"data": q}, timeout=90, headers={"User-Agent": "curl/8.7.1", "Accept": "*/*"})
        if resp.status_code == 200:
            data = resp.json()
            cache_path.write_text(json.dumps(data), encoding="utf-8")
            return data["elements"]
        if resp.status_code in (429, 504):
            wait = 8 * (attempt + 1)
            print(f"  Overpass {resp.status_code}, retrying in {wait}s...", file=sys.stderr)
            time.sleep(wait)
            continue
        resp.raise_for_status()
    raise RuntimeError(f"Overpass failed for {cluster_id} after retries")


def find_intersections(elements: list[dict]) -> list[dict]:
    buckets: dict[tuple, set[str]] = defaultdict(set)
    bucket_points: dict[tuple, list] = defaultdict(list)
    for el in elements:
        name = el.get("tags", {}).get("name")
        geom = el.get("geometry") or []
        if not name or not geom:
            continue
        for pt in geom:
            key = (round(pt["lat"] / GRID_DEG), round(pt["lon"] / GRID_DEG))
            buckets[key].add(name)
            bucket_points[key].append((pt["lat"], pt["lon"], name))

    found = []
    for key, names in buckets.items():
        if len(names) < 2:
            continue
        pts = bucket_points[key]
        lat = sum(p[0] for p in pts) / len(pts)
        lon = sum(p[1] for p in pts) / len(pts)
        names_sorted = sorted(names)
        found.append({"road_a": names_sorted[0], "road_b": names_sorted[1], "lat": lat, "lon": lon})

    # dedupe intersections that are basically the same corner
    deduped = []
    for f in sorted(found, key=lambda x: (x["road_a"], x["road_b"])):
        if any(
            f["road_a"] == d["road_a"] and f["road_b"] == d["road_b"] and haversine_miles(f["lat"], f["lon"], d["lat"], d["lon"]) < DEDUPE_MI
            for d in deduped
        ):
            continue
        deduped.append(f)

    if len(deduped) > MAX_INTERSECTIONS_PER_CLUSTER:
        deduped.sort(key=lambda x: (x["lat"], x["lon"]))
        stride = len(deduped) / MAX_INTERSECTIONS_PER_CLUSTER
        deduped = [deduped[int(i * stride)] for i in range(MAX_INTERSECTIONS_PER_CLUSTER)]

    return deduped


def main() -> None:
    with open(PROCESSED / "clusters.csv", encoding="utf-8") as fh:
        clusters = list(csv.DictReader(fh))

    all_rows = []
    for c in clusters:
        elements = fetch_roads(
            c["cluster_id"],
            float(c["bbox_min_lat"]), float(c["bbox_min_lon"]),
            float(c["bbox_max_lat"]), float(c["bbox_max_lon"]),
        )
        names = {el.get("tags", {}).get("name") for el in elements if el.get("tags", {}).get("name")}
        xs = find_intersections(elements)
        print(f"{c['cluster_id']} ({c['neighborhood']}): {len(names)} named roads -> {len(xs)} intersections", file=sys.stderr)
        for x in xs:
            all_rows.append({"cluster_id": c["cluster_id"], "neighborhood": c["neighborhood"], **x})
        time.sleep(2.0)

    out_path = PROCESSED / "intersections.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["cluster_id", "neighborhood", "road_a", "road_b", "lat", "lon"])
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"\nWrote {len(all_rows)} citywide intersections -> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
