"""Step 17 (generalizes the old scripts/07, which only covered the Sunnyside
submarket): pull every Census block group in Harris County, keep the ones
whose centroid falls inside the real City of Houston boundary (script 13),
and attach ACS 5-year population + median household income. This is the
population base used for every candidate site's real drive-time trade area
(script 18).

Output: data/processed/blockgroups.csv
"""
from __future__ import annotations

import csv
import json
import sys
import time

import requests

from lib import (
    CENSUS_REPORTER,
    HARRIS_COUNTY_FIPS,
    HARRIS_STATE_FIPS,
    PROCESSED,
    RAW,
    TIGERWEB,
    cached_get,
    point_in_rings_fast,
    ring_bbox,
)


def main() -> None:
    boundary_raw = json.loads((RAW / "tigerweb_houston_boundary.json").read_text(encoding="utf-8"))
    rings = boundary_raw["features"][0]["geometry"]["rings"]
    bboxes = [ring_bbox(r) for r in rings]

    data = cached_get(
        f"{TIGERWEB}/10/query",
        {
            "where": f"STATE='{HARRIS_STATE_FIPS}' AND COUNTY='{HARRIS_COUNTY_FIPS}'",
            "outFields": "GEOID,NAME,AREALAND,CENTLAT,CENTLON",
            "returnGeometry": "false",
            "f": "json",
        },
        "tigerweb_harris_blockgroups_all",
    )
    all_bgs = [f["attributes"] for f in data["features"]]
    print(f"TIGERweb returned {len(all_bgs)} Harris County block groups", file=sys.stderr)

    in_city = [
        bg for bg in all_bgs
        if point_in_rings_fast(float(bg["CENTLAT"]), float(bg["CENTLON"]), rings, bboxes)
    ]
    print(f"{len(in_city)} block groups have centroids inside Houston city limits", file=sys.stderr)

    demo_cache = PROCESSED / "_bg_demo_cache.csv"
    demo: dict[str, dict] = {}
    if demo_cache.exists():
        with open(demo_cache, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                demo[row["geoid"]] = row
    else:
        geoids = [bg["GEOID"] for bg in in_city]
        batch_size = 40
        for i in range(0, len(geoids), batch_size):
            batch = geoids[i : i + batch_size]
            ids = ",".join(f"15000US{g}" for g in batch)
            resp = requests.get(
                CENSUS_REPORTER,
                params={"table_ids": "B01003,B19013", "geo_ids": ids},
                headers={"User-Agent": "curl/8.7.1"},
                timeout=40,
            )
            resp.raise_for_status()
            result = resp.json().get("data", {})
            for full_geoid, tables in result.items():
                g = full_geoid.replace("15000US", "")
                pop = tables.get("B01003", {}).get("estimate", {}).get("B01003001")
                mhi = tables.get("B19013", {}).get("estimate", {}).get("B19013001")
                demo[g] = {"population": pop, "median_hh_income": mhi}
            print(f"  fetched block group demographics {i + len(batch)}/{len(geoids)}", file=sys.stderr)
            time.sleep(0.3)
        with open(demo_cache, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["geoid", "population", "median_hh_income"])
            writer.writeheader()
            for g, d in demo.items():
                writer.writerow({"geoid": g, **d})

    rows = []
    for bg in in_city:
        d = demo.get(bg["GEOID"], {})
        pop = d.get("population")
        rows.append(
            {
                "geoid": bg["GEOID"],
                "lat": float(bg["CENTLAT"]),
                "lon": float(bg["CENTLON"]),
                "population": pop if pop not in (None, "", "None") else 0,
                "median_hh_income": d.get("median_hh_income"),
            }
        )

    out_path = PROCESSED / "blockgroups.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["geoid", "lat", "lon", "population", "median_hh_income"])
        writer.writeheader()
        writer.writerows(rows)
    total_pop = sum(float(r["population"] or 0) for r in rows)
    print(f"Wrote {len(rows)} citywide block groups ({total_pop:,.0f} total people) -> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
