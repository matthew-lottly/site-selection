"""Step 22: Build a real drive-time isochrone (5-minute and 10-minute) around
the CURRENT citywide-scorecard winner (script 20's rank #1) using OSRM
routing over the actual OpenStreetMap street network -- not a generic circle
buffer. Re-run this any time the scorecard winner changes; it always reads
the live top row of scorecard.csv rather than a hardcoded site.

Method: cast 16 compass bearings from the site; along each bearing, query
OSRM (single batched /table call) for driving duration to 8 candidate
distances; keep the farthest candidate on each bearing that is still within
the 5-min / 10-min threshold. Connecting those points in bearing order traces
the true reachable shape (indented where the road network doesn't cooperate).

Output: data/processed/isochrone_winner.geojson
"""
from __future__ import annotations

import csv
import json
import math
import sys

from ..clients import OsrmClient
from ..core import PROCESSED, PipelineStage


class IsochroneWinnerStage(PipelineStage):
    id = "22"
    name = "isochrone_winner"
    description = "5-min / 10-min drive-time isochrone (OSRM) around the current scorecard winner"
    outputs = (PROCESSED / "isochrone_winner.json",)

    N_BEARINGS = 16
    CANDIDATE_MILES = [0.3, 0.6, 1.0, 1.5, 2.0, 2.8, 3.6, 4.5]
    THRESHOLDS = {"5min": 300, "10min": 600}

    def __init__(self) -> None:
        self.osrm = OsrmClient()

    @staticmethod
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

    def run(self) -> None:
        with open(PROCESSED / "scorecard.csv", encoding="utf-8") as fh:
            winner = next(csv.DictReader(fh))
        with open(PROCESSED / "sites_enriched.csv", encoding="utf-8") as fh:
            site = next(r for r in csv.DictReader(fh) if r["hcad_num"] == winner["hcad_num"])

        lat, lon = float(site["lat"]), float(site["lon"])
        print(f"Building isochrone for CURRENT #1 site: {site['site_label']} @ ({lat},{lon})", file=sys.stderr)

        points = []
        for b in range(self.N_BEARINGS):
            bearing = b * (360 / self.N_BEARINGS)
            for d in self.CANDIDATE_MILES:
                points.append((bearing, d, *self.destination_point(lat, lon, bearing, d)))

        coords = [f"{lon},{lat}"] + [f"{p[3]},{p[2]}" for p in points]
        result = self.osrm.table(coords, {"sources": "0", "annotations": "duration"}, retries=1, timeout=60)
        durations = result["durations"][0][1:]

        rings = {}
        for label, threshold in self.THRESHOLDS.items():
            ring = []
            for b in range(self.N_BEARINGS):
                bearing = b * (360 / self.N_BEARINGS)
                best = None
                for i, d in enumerate(self.CANDIDATE_MILES):
                    idx = b * len(self.CANDIDATE_MILES) + i
                    dur = durations[idx]
                    if dur is not None and dur <= threshold:
                        best = (bearing, d)
                if best is None:
                    best = (bearing, 0.15)
                plat, plon = self.destination_point(lat, lon, best[0], best[1])
                ring.append([plon, plat])
            ring.append(ring[0])
            rings[label] = ring

        out = {
            "site_label": site["site_label"],
            "hcad_num": site["hcad_num"],
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
    IsochroneWinnerStage().run()
