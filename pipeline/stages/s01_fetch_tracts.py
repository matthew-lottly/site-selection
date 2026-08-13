"""Step 1: Pull every Census tract in Harris County, TX (TIGERweb) and attach
ACS 5-year demographic estimates (Census Reporter API). No API key required.

Output: data/processed/tracts.csv
Columns: geoid, name, lat, lon, aland_sqmi, population, median_hh_income,
         poverty_total, poverty_below, poverty_rate, snap_households, total_households, snap_rate
"""
from __future__ import annotations

import csv
import sys
import time

from ..clients import CensusReporterClient, HARRIS_COUNTY_FIPS, HARRIS_STATE_FIPS, TigerWebClient
from ..core import PROCESSED, PipelineStage


class FetchTractsStage(PipelineStage):
    id = "01"
    name = "fetch_tracts"
    description = "Harris County tracts (TIGERweb) + ACS 5yr demographics (Census Reporter)"
    outputs = (PROCESSED / "tracts.csv",)

    DEMO_TABLE_IDS = "B01003,B19013,B17001,B22010"
    DEMO_BATCH_SIZE = 40
    DEMO_CACHE_FIELDS = [
        "geoid", "population", "median_hh_income", "poverty_total",
        "poverty_below", "total_households", "snap_households",
    ]
    OUTPUT_FIELDS = [
        "geoid", "name", "lat", "lon", "aland_sqmi", "population",
        "median_hh_income", "poverty_rate", "snap_rate",
    ]

    def __init__(self) -> None:
        self.tigerweb = TigerWebClient()
        self.census = CensusReporterClient()

    def run(self) -> None:
        tracts = self._fetch_tract_geoids()
        print(f"TIGERweb returned {len(tracts)} Harris County tracts", file=sys.stderr)

        by_geoid = {t["GEOID"]: t for t in tracts}
        demo = self._load_or_fetch_demographics(list(by_geoid.keys()))
        rows = self._build_rows(by_geoid, demo)

        out_path = PROCESSED / "tracts.csv"
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=self.OUTPUT_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote {len(rows)} tracts to {out_path}", file=sys.stderr)

    def _fetch_tract_geoids(self) -> list[dict]:
        data = self.tigerweb.query(
            8,
            {
                "where": f"STATE='{HARRIS_STATE_FIPS}' AND COUNTY='{HARRIS_COUNTY_FIPS}'",
                "outFields": "GEOID,NAME,AREALAND,CENTLAT,CENTLON",
                "returnGeometry": "false",
                "f": "json",
            },
            "tigerweb_harris_tracts",
        )
        return [f["attributes"] for f in data["features"]]

    def _load_or_fetch_demographics(self, all_geoids: list[str]) -> dict:
        demo: dict = {}
        cache_file = PROCESSED / "_demo_cache.csv"
        if cache_file.exists():
            with open(cache_file, newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    demo[row["geoid"]] = row
            return demo

        for i in range(0, len(all_geoids), self.DEMO_BATCH_SIZE):
            batch = all_geoids[i : i + self.DEMO_BATCH_SIZE]
            try:
                result = self.census.fetch_batch(self.DEMO_TABLE_IDS, batch)
            except Exception as exc:  # noqa: BLE001
                print(f"batch {i} failed: {exc}", file=sys.stderr)
                continue
            for full_geoid, tables in result.items():
                g = full_geoid.replace("14000US", "")
                pop = tables.get("B01003", {}).get("estimate", {}).get("B01003001")
                mhi = tables.get("B19013", {}).get("estimate", {}).get("B19013001")
                pov = tables.get("B17001", {}).get("estimate", {})
                pov_total = pov.get("B17001001")
                pov_below = pov.get("B17001002")
                snap = tables.get("B22010", {}).get("estimate", {})
                snap_total = snap.get("B22010001")
                snap_yes = snap.get("B22010002")
                demo[g] = {
                    "population": pop,
                    "median_hh_income": mhi,
                    "poverty_total": pov_total,
                    "poverty_below": pov_below,
                    "total_households": snap_total,
                    "snap_households": snap_yes,
                }
            print(f"  fetched demographics {i + len(batch)}/{len(all_geoids)}", file=sys.stderr)
            time.sleep(0.3)

        with open(cache_file, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=self.DEMO_CACHE_FIELDS)
            writer.writeheader()
            for geoid, d in demo.items():
                writer.writerow({"geoid": geoid, **d})
        return demo

    @staticmethod
    def _build_rows(by_geoid: dict, demo: dict) -> list[dict]:
        rows = []
        for geoid, attrs in by_geoid.items():
            d = demo.get(geoid, {})
            try:
                pop = float(d.get("population") or 0)
                mhi = d.get("median_hh_income")
                mhi = float(mhi) if mhi not in (None, "", "None") else None
                pov_total = float(d.get("poverty_total") or 0)
                pov_below = float(d.get("poverty_below") or 0)
                hh_total = float(d.get("total_households") or 0)
                snap_hh = float(d.get("snap_households") or 0)
            except (TypeError, ValueError):
                continue
            poverty_rate = (pov_below / pov_total) if pov_total else None
            snap_rate = (snap_hh / hh_total) if hh_total else None
            rows.append(
                {
                    "geoid": geoid,
                    "name": attrs.get("NAME"),
                    "lat": float(attrs["CENTLAT"]),
                    "lon": float(attrs["CENTLON"]),
                    "aland_sqmi": float(attrs["AREALAND"]) / 2_589_988.11,
                    "population": pop,
                    "median_hh_income": mhi,
                    "poverty_rate": poverty_rate,
                    "snap_rate": snap_rate,
                }
            )
        return rows


if __name__ == "__main__":
    FetchTractsStage().run()
