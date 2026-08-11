"""Step 9: Real street-network drive times (OSRM, OpenStreetMap road graph)
from each of the 5 candidate sites to every block-group population centroid
in the submarket. This replaces a straight-line "as the crow flies" radius
with an actual routable trade area: population reachable within a 5-minute
and 10-minute drive.

Output: data/processed/site_trade_areas.csv
        data/raw/osrm_durations_<hcad_num>.json (cached per-site duration matrix,
        reused in script 11 to draw the winning site's isochrone polygon)
"""
from __future__ import annotations

import csv
import json
import sys

import requests

from lib import OSRM, PROCESSED, RAW


def main() -> None:
    with open(PROCESSED / "sites_enriched.csv", encoding="utf-8") as fh:
        sites = list(csv.DictReader(fh))
    with open(PROCESSED / "blockgroups.csv", encoding="utf-8") as fh:
        bgs = list(csv.DictReader(fh))

    rows = []
    for s in sites:
        cache_path = RAW / f"osrm_durations_{s['hcad_num']}.json"
        if cache_path.exists():
            durations = json.loads(cache_path.read_text(encoding="utf-8"))
        else:
            coords = [f"{s['lon']},{s['lat']}"] + [f"{b['lon']},{b['lat']}" for b in bgs]
            url = f"{OSRM}/table/v1/driving/" + ";".join(coords)
            resp = requests.get(url, params={"sources": "0", "annotations": "duration"}, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            durations = data["durations"][0]
            cache_path.write_text(json.dumps(durations), encoding="utf-8")

        pop_5min = 0.0
        pop_10min = 0.0
        for bg, dur in zip(bgs, durations[1:]):
            pop = float(bg["population"] or 0)
            if dur is None:
                continue
            if dur <= 300:
                pop_5min += pop
            if dur <= 600:
                pop_10min += pop

        rows.append(
            {
                "site_label": s["site_label"],
                "hcad_num": s["hcad_num"],
                "pop_5min_drive": round(pop_5min),
                "pop_10min_drive": round(pop_10min),
            }
        )
        print(f"{s['site_label']}: 5-min pop={pop_5min:.0f}  10-min pop={pop_10min:.0f}", file=sys.stderr)

    out_path = PROCESSED / "site_trade_areas.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["site_label", "hcad_num", "pop_5min_drive", "pop_10min_drive"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {len(rows)} site trade areas -> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
