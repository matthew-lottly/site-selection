"""Step 11: Build a real drive-time isochrone (5-minute and 10-minute) around
the recommended site using OSRM routing over the actual OpenStreetMap street
network -- not a generic circle buffer.

Method: cast 16 compass bearings from the site; along each bearing, query
OSRM (single batched /table call) for driving duration to 8 candidate
distances; keep the farthest candidate on each bearing that is still within
the 5-min / 10-min threshold. Connecting those points in bearing order traces
the true reachable shape (indented where the road network doesn't cooperate).

Output: data/processed/isochrone_winner.geojson
"""
from __future__ import annotations

import json
import math
import sys

import requests

from lib import OSRM, PROCESSED

N_BEARINGS = 16
CANDIDATE_MILES = [0.3, 0.6, 1.0, 1.5, 2.0, 2.8, 3.6, 4.5]
THRESHOLDS = {"5min": 300, "10min": 600}


def destination_point(lat: float, lon: float, bearing_deg: float, dist_mi: float) -> tuple[float, float]:
    r = 3958.8
    br = math.radians(bearing_deg)
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    ang = dist_mi / r
    lat2 = math.asin(math.sin(lat1) * math.cos(ang) + math.cos(lat1) * math.sin(ang) * math.cos(br))
    lon2 = lon1 + math.atan2(
        math.sin(br) * math.sin(ang) * math.cos(lat1), math.cos(ang) - math.sin(lat1) * math.sin(lat2)
    )
    return math.degrees(lat2), math.degrees(lon2)


def main() -> None:
    with open(PROCESSED / "scorecard.csv", encoding="utf-8") as fh:
        import csv

        winner = next(csv.DictReader(fh))
    with open(PROCESSED / "sites_enriched.csv", encoding="utf-8") as fh:
        import csv

        site = next(r for r in csv.DictReader(fh) if r["hcad_num"] == winner["hcad_num"])

    lat, lon = float(site["lat"]), float(site["lon"])
    print(f"Building isochrone for {site['site_label']} @ ({lat},{lon})", file=sys.stderr)

    points = []
    for b in range(N_BEARINGS):
        bearing = b * (360 / N_BEARINGS)
        for d in CANDIDATE_MILES:
            points.append((bearing, d, *destination_point(lat, lon, bearing, d)))

    coords = [f"{lon},{lat}"] + [f"{p[3]},{p[2]}" for p in points]
    url = f"{OSRM}/table/v1/driving/" + ";".join(coords)
    resp = requests.get(url, params={"sources": "0", "annotations": "duration"}, timeout=60)
    resp.raise_for_status()
    durations = resp.json()["durations"][0][1:]

    rings = {}
    for label, threshold in THRESHOLDS.items():
        ring = []
        for b in range(N_BEARINGS):
            bearing = b * (360 / N_BEARINGS)
            best = None
            for i, d in enumerate(CANDIDATE_MILES):
                idx = b * len(CANDIDATE_MILES) + i
                dur = durations[idx]
                if dur is not None and dur <= threshold:
                    best = (bearing, d)
            if best is None:
                # nothing reachable even at the shortest candidate; fall back to a small nominal radius
                best = (bearing, 0.15)
            plat, plon = destination_point(lat, lon, best[0], best[1])
            ring.append([plon, plat])
        ring.append(ring[0])
        rings[label] = ring

    out = {
        "site_label": site["site_label"],
        "site_lat": lat,
        "site_lon": lon,
        "isochrones": {
            "5min": {"type": "Polygon", "coordinates": [rings["5min"]]},
            "10min": {"type": "Polygon", "coordinates": [rings["10min"]]},
        },
    }
    out_path = PROCESSED / "isochrone_winner.json"
    out_path.write_text(json.dumps(out), encoding="utf-8")
    print(f"Wrote isochrone -> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
