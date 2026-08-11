"""Step 7: Attach ACS 5-year population + income to the submarket block
groups (finer-grained than tracts) so drive-time trade areas can be built
from block-group centroids in script 09.

Output: data/processed/blockgroups.csv
"""
from __future__ import annotations

import csv
import json
import sys
import time

import requests

from lib import CENSUS_REPORTER, PROCESSED


def main() -> None:
    fc = json.loads((PROCESSED / "submarket_blockgroups.geojson").read_text(encoding="utf-8"))
    geoids = [f["properties"]["geoid"] for f in fc["features"]]

    centroids = {}
    for f in fc["features"]:
        coords = f["geometry"]["coordinates"][0]
        lon = sum(p[0] for p in coords) / len(coords)
        lat = sum(p[1] for p in coords) / len(coords)
        centroids[f["properties"]["geoid"]] = (lat, lon)

    demo = {}
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

    rows = []
    for geoid, (lat, lon) in centroids.items():
        d = demo.get(geoid, {})
        pop = d.get("population")
        rows.append(
            {
                "geoid": geoid,
                "lat": lat,
                "lon": lon,
                "population": pop if pop is not None else 0,
                "median_hh_income": d.get("median_hh_income"),
            }
        )

    out_path = PROCESSED / "blockgroups.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["geoid", "lat", "lon", "population", "median_hh_income"])
        writer.writeheader()
        writer.writerows(rows)
    total_pop = sum(float(r["population"] or 0) for r in rows)
    print(f"Wrote {len(rows)} block groups ({total_pop:.0f} total people) -> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
