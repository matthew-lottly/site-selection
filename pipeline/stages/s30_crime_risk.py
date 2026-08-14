"""Step 30: real Houston Police Department NIBRS crime-risk score for each of
the 20 citywide finalists -- Part I violent and property offense counts
within a 0.5-mile radius of each site, trailing 12 months.

Closes a documented gap (docs/data_validation.md #11 / limitations_and_
diligence.md): the earlier check queried only Houston's open-data CKAN
catalog (package_search / package_show), which genuinely has no queryable
crime dataset -- but HPD's own site separately publishes real, point-level
NIBRS incident CSVs (offense code, date, lat/lon) as direct downloads, free
and keyless, back to 2009. That direct source was missed the first time;
this stage adds it.

Offense classification follows the standard FBI UCR Part I "index crime"
definition -- the same standard used nationally for retail crime-risk
screening, not an ad hoc one:
  violent  = murder (09A), rape (11A-11D), robbery (120), aggravated assault (13A)
  property = burglary (220), larceny/theft (23A-23H), motor vehicle theft (240)

A fixed 0.5-mile radius is used for every site, so raw incident counts are
already an apples-to-apples comparison (same search area everywhere) without
needing a separate per-capita normalization step.

Output: data/processed/site_crime_risk.csv
"""
from __future__ import annotations

import csv
import sys
from datetime import date

from ..clients import HpdCrimeClient
from ..core import PROCESSED, PipelineStage
from ..geometry import Geometry

VIOLENT_CODES = {"09A", "11A", "11B", "11C", "11D", "120", "13A"}
PROPERTY_CODES = {"220", "240"} | {f"23{c}" for c in "ABCDEFGH"}

RADIUS_MI = 0.5
# Trailing 12 months as of HPD's most recent published refresh of the yearly
# export files (2026 file "current as of 7/30/2026" per the source page).
WINDOW_START = date(2025, 8, 1)
WINDOW_END = date(2026, 7, 31)
YEARS_NEEDED = (2025, 2026)


class CrimeRiskStage(PipelineStage):
    id = "30"
    name = "crime_risk"
    description = "Real HPD NIBRS Part I violent/property crime counts within 0.5mi of each finalist (trailing 12mo)"
    outputs = (PROCESSED / "site_crime_risk.csv",)

    def __init__(self) -> None:
        self.client = HpdCrimeClient()

    def run(self) -> None:
        with open(PROCESSED / "sites_enriched.csv", encoding="utf-8") as fh:
            sites = list(csv.DictReader(fh))

        incidents = self.load_incidents()
        print(
            f"Loaded {len(incidents)} real HPD Part I violent/property incidents, "
            f"{WINDOW_START} - {WINDOW_END}",
            file=sys.stderr,
        )

        # cheap bounding-box prefilter (~0.5 mi in degrees at Houston's latitude)
        # before the exact haversine check -- same pattern as the grid-bucketing
        # used for intersection search in script 14
        lat_pad = RADIUS_MI / 69.0
        lon_pad = RADIUS_MI / 60.0

        rows = []
        for s in sites:
            lat, lon = float(s["lat"]), float(s["lon"])
            violent = property_ = 0
            for inc in incidents:
                if abs(inc["lat"] - lat) > lat_pad or abs(inc["lon"] - lon) > lon_pad:
                    continue
                if Geometry.haversine_miles(lat, lon, inc["lat"], inc["lon"]) > RADIUS_MI:
                    continue
                if inc["code"] in VIOLENT_CODES:
                    violent += 1
                else:
                    property_ += 1
            total = violent + property_
            rows.append(
                {
                    "hcad_num": s["hcad_num"],
                    "site_label": s["site_label"],
                    "violent_crime_count_12mo_0_5mi": violent,
                    "property_crime_count_12mo_0_5mi": property_,
                    "total_index_crime_count_12mo_0_5mi": total,
                }
            )
            print(
                f"{s['site_label']}: {violent} violent, {property_} property (real HPD Part I incidents, "
                f"0.5mi, trailing 12mo)",
                file=sys.stderr,
            )

        out_path = PROCESSED / "site_crime_risk.csv"
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nWrote real crime-risk data for {len(rows)} sites -> {out_path}", file=sys.stderr)

    def load_incidents(self) -> list[dict]:
        incidents = []
        for year in YEARS_NEEDED:
            path = self.client.fetch_year_csv(year)
            with open(path, encoding="utf-8-sig", errors="replace") as fh:
                for row in csv.DictReader(fh):
                    code = (row.get("NIBRS Class") or "").strip()
                    if code not in VIOLENT_CODES and code not in PROPERTY_CODES:
                        continue
                    try:
                        occ_date = date.fromisoformat((row.get("Occurrence Date") or "")[:10])
                    except ValueError:
                        continue
                    if not (WINDOW_START <= occ_date <= WINDOW_END):
                        continue
                    try:
                        lat = float(row["Map Latitude"])
                        lon = float(row["Map Longitude"])
                    except (ValueError, KeyError):
                        continue
                    if lat == 0.0 or lon == 0.0:
                        continue
                    incidents.append({"lat": lat, "lon": lon, "code": code})
        return incidents


if __name__ == "__main__":
    CrimeRiskStage().run()
