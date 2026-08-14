"""Step 36: real Houston population growth trend, 2020-2024 -- citywide
context, not a per-site scored factor (a citywide growth rate is identical
for all 20 finalists and can't differentiate between them). Closes a real
gap best-practice research (docs/data_validation.md item 21) flagged: every
industry site-selection source checked names population growth *trend*, not
just a single-year snapshot, as a core demand criterion, and this model's
demographics (ACS 5-yr) are a rolling-average snapshot with no trend.

Source: Census Population Estimates Program (PEP), real annual place-level
estimates. The PEP's REST API now requires a registered key -- a break from
every other keyless source this project uses -- so this pulls the Bureau's
own direct CSV file release instead (same pattern as HpdCrimeClient/
LehdClient), keeping the whole project keyless.

Output: data/processed/city_population_trend.csv
"""
from __future__ import annotations

import csv
import sys

from ..clients import CensusPepClient
from ..core import PROCESSED, PipelineStage

HOUSTON_PLACE_FIPS = "35000"
HOUSTON_STATE_FIPS = "48"
YEARS = (2020, 2021, 2022, 2023, 2024)


class PopulationTrendStage(PipelineStage):
    id = "36"
    name = "population_trend"
    description = "Real Census PEP Houston population growth trend, 2020-2024 (citywide context)"
    outputs = (PROCESSED / "city_population_trend.csv",)

    def __init__(self) -> None:
        self.client = CensusPepClient()

    def run(self) -> None:
        path = self.client.fetch_places_csv()
        with open(path, encoding="utf-8", errors="replace") as fh:
            row = next(
                r for r in csv.DictReader(fh)
                if r["STATE"] == HOUSTON_STATE_FIPS and r["PLACE"] == HOUSTON_PLACE_FIPS and r["NAME"] == "Houston city"
            )

        rows = [{"year": y, "population_estimate": row[f"POPESTIMATE{y}"]} for y in YEARS]
        pop_start, pop_end = int(rows[0]["population_estimate"]), int(rows[-1]["population_estimate"])
        pct_change = (pop_end - pop_start) / pop_start * 100

        out_path = PROCESSED / "city_population_trend.csv"
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["year", "population_estimate"])
            writer.writeheader()
            writer.writerows(rows)

        print("Real City of Houston population estimates (Census PEP, place FIPS 4835000):", file=sys.stderr)
        for r in rows:
            print(f"  {r['year']}: {int(r['population_estimate']):,}", file=sys.stderr)
        print(f"2020-2024 change: {pop_end - pop_start:+,} ({pct_change:+.1f}%)", file=sys.stderr)
        print(f"Wrote real population trend -> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    PopulationTrendStage().run()
