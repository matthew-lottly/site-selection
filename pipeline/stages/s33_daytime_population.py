"""Step 33: real daytime/workplace population within each finalist's 5-minute
drive-time trade area -- something this model previously had zero visibility
into. Every other demand signal in this pipeline measures RESIDENTS reachable
by drive time; it has no signal for the office/retail/industrial workforce
that passes a site on a commute or lunch break. Census LEHD LODES (the same
public data source behind the Census Bureau's own OnTheMap tool) provides
real, free, block-level total job counts for exactly this.

Reuses the real OSRM drive-time durations already cached per site in script
19 (`data/raw/osrm_durations_{hcad}.json`) -- no new routing calls -- with the
identical block-group prefilter/ordering script 19 and script 24 already use,
so the durations line up with the same block-group list index for index.

Output: data/processed/site_daytime_population.csv
"""
from __future__ import annotations

import csv
import gzip
import io
import json
import sys
from collections import defaultdict

from ..clients import LehdClient
from ..core import PROCESSED, RAW, PipelineStage
from ..geometry import Geometry

STATE = "tx"
YEAR = 2023
BLOCKGROUP_PREFILTER_MI = 10.0  # must match script 19's prefilter exactly


class DaytimePopulationStage(PipelineStage):
    id = "33"
    name = "daytime_population"
    description = "Real LEHD workplace/job counts within each finalist's 5-minute drive trade area"
    outputs = (PROCESSED / "site_daytime_population.csv", PROCESSED / "blockgroup_daytime_population.csv")

    def __init__(self) -> None:
        self.client = LehdClient()

    def run(self) -> None:
        with open(PROCESSED / "sites_enriched.csv", encoding="utf-8") as fh:
            sites = list(csv.DictReader(fh))
        with open(PROCESSED / "blockgroups.csv", encoding="utf-8") as fh:
            bgs = list(csv.DictReader(fh))

        jobs_by_bg = self.load_jobs_by_blockgroup()
        print(f"Loaded real LEHD job counts for {len(jobs_by_bg)} Texas block groups", file=sys.stderr)

        rows = []
        for s in sites:
            lat, lon = float(s["lat"]), float(s["lon"])
            hcad = s["hcad_num"]

            nearby_bgs = [b for b in bgs if Geometry.haversine_miles(lat, lon, float(b["lat"]), float(b["lon"])) <= BLOCKGROUP_PREFILTER_MI]
            durations_path = RAW / f"osrm_durations_{hcad}.json"
            durations = json.loads(durations_path.read_text(encoding="utf-8"))

            daytime_pop_5min = 0
            for bg, dur in zip(nearby_bgs, durations[1:]):
                if dur is None or dur > 300:
                    continue
                daytime_pop_5min += jobs_by_bg.get(bg["geoid"], 0)

            rows.append(
                {
                    "hcad_num": hcad,
                    "site_label": s["site_label"],
                    "daytime_workplace_pop_5min_drive": daytime_pop_5min,
                }
            )
            print(f"{s['site_label']}: {daytime_pop_5min:,} real LEHD jobs within 5-min drive", file=sys.stderr)

        out_path = PROCESSED / "site_daytime_population.csv"
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nWrote real daytime-population data for {len(rows)} sites -> {out_path}", file=sys.stderr)

        # citywide block-group-level detail, for the map's daytime-population layer
        bg_rows = [
            {"geoid": b["geoid"], "lat": b["lat"], "lon": b["lon"], "daytime_jobs": jobs_by_bg.get(b["geoid"], 0)}
            for b in bgs
        ]
        bg_path = PROCESSED / "blockgroup_daytime_population.csv"
        with open(bg_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["geoid", "lat", "lon", "daytime_jobs"])
            writer.writeheader()
            writer.writerows(bg_rows)
        print(f"Wrote real daytime job counts for {len(bg_rows)} Houston block groups -> {bg_path}", file=sys.stderr)

    def load_jobs_by_blockgroup(self) -> dict[str, int]:
        path = self.client.fetch_wac_csv_gz(STATE, YEAR)
        jobs: dict[str, int] = defaultdict(int)
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                block_geoid = row["w_geocode"]
                bg_geoid = block_geoid[:12]
                jobs[bg_geoid] += int(row["C000"])
        return dict(jobs)


if __name__ == "__main__":
    DaytimePopulationStage().run()
