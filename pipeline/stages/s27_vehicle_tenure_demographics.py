"""Step 27: Two more real ACS demand-context variables the analysis was
missing, requested after review:

  - Zero-vehicle household rate (B25044): dollar-store customers in urban
    corridors frequently walk or take transit for top-off grocery trips.
    High zero/one-vehicle rates signal local impulse-trip dependency that
    median income alone doesn't capture.
  - Renter-occupied housing rate (B25003): multi-family renters have higher
    turnover and lean more on nearby value consumables than long-term
    homeowners with stocked pantries.

Same treatment as script 25's extended demographics: real ACS 5-year
figures for all 643 Houston tracts (context in tract map popups) plus a
real city-wide 90% confidence interval appended to the same table used
throughout the analysis. These are demand-context variables, surfaced for
the reader -- consistent with how foreign-born share, Spanish-at-home, and
household size were handled, they are NOT folded into the weighted
scorecard's six factors, to avoid re-deriving and destabilizing an already
documented, defensible weighting scheme with a new pair of variables.

Output: tract_extended_demographics.csv gets 2 new columns
        city_confidence_intervals.csv gets 2 new rows
"""
from __future__ import annotations

import csv
import math
import sys
import time

from ..clients import CensusReporterClient
from ..core import PROCESSED, PipelineStage


class VehicleTenureDemographicsStage(PipelineStage):
    id = "27"
    name = "vehicle_tenure_demographics"
    description = "Zero-vehicle & renter-occupied ACS rates merged into extended demographics + city CI table"
    outputs = (
        PROCESSED / "tract_extended_demographics.csv",
        PROCESSED / "city_confidence_intervals.csv",
    )

    TABLES = "B25044,B25003"

    def __init__(self) -> None:
        self.census = CensusReporterClient()

    @staticmethod
    def ratio_moe(x: float, moe_x: float, y: float, moe_y: float) -> float:
        if y == 0:
            return 0.0
        p = x / y
        radicand = moe_x**2 - (p**2) * (moe_y**2)
        if radicand < 0:
            radicand = moe_x**2 + (p**2) * (moe_y**2)
        return math.sqrt(radicand) / y

    def run(self) -> None:
        # ---- City-wide confidence intervals (append to the existing CI table) ----
        city_data = self.census.fetch_batch(self.TABLES, ["4835000"], geo_prefix="16000US", release="acs2024_5yr")
        city = city_data["16000US4835000"]
        veh_tot_est, veh_tot_moe = city["B25044"]["estimate"]["B25044001"], city["B25044"]["error"]["B25044001"]
        veh_zero_owner_est, veh_zero_owner_moe = city["B25044"]["estimate"]["B25044003"], city["B25044"]["error"]["B25044003"]
        veh_zero_renter_est, veh_zero_renter_moe = city["B25044"]["estimate"]["B25044010"], city["B25044"]["error"]["B25044010"]
        veh_zero_est = veh_zero_owner_est + veh_zero_renter_est
        veh_zero_moe = math.sqrt(veh_zero_owner_moe**2 + veh_zero_renter_moe**2)  # sum of two independent ACS estimates
        veh_zero_rate = veh_zero_est / veh_tot_est
        veh_zero_rate_moe = self.ratio_moe(veh_zero_est, veh_zero_moe, veh_tot_est, veh_tot_moe)

        ten_tot_est, ten_tot_moe = city["B25003"]["estimate"]["B25003001"], city["B25003"]["error"]["B25003001"]
        renter_est, renter_moe = city["B25003"]["estimate"]["B25003003"], city["B25003"]["error"]["B25003003"]
        renter_rate = renter_est / ten_tot_est
        renter_rate_moe = self.ratio_moe(renter_est, renter_moe, ten_tot_est, ten_tot_moe)

        new_ci_rows = [
            {"statistic": "Zero-vehicle household share", "estimate": f"{veh_zero_rate*100:.1f}%", "moe_90pct": f"±{veh_zero_rate_moe*100:.1f}pp",
             "ci_90pct_low": f"{(veh_zero_rate-veh_zero_rate_moe)*100:.1f}%", "ci_90pct_high": f"{(veh_zero_rate+veh_zero_rate_moe)*100:.1f}%",
             "source": "ACS 2024 5-yr B25044 (ratio MOE propagated)"},
            {"statistic": "Renter-occupied housing share", "estimate": f"{renter_rate*100:.1f}%", "moe_90pct": f"±{renter_rate_moe*100:.1f}pp",
             "ci_90pct_low": f"{(renter_rate-renter_rate_moe)*100:.1f}%", "ci_90pct_high": f"{(renter_rate+renter_rate_moe)*100:.1f}%",
             "source": "ACS 2024 5-yr B25003 (ratio MOE propagated)"},
        ]
        ci_path = PROCESSED / "city_confidence_intervals.csv"
        with open(ci_path, encoding="utf-8") as fh:
            existing_rows = list(csv.DictReader(fh))
        existing_rows = [r for r in existing_rows if r["statistic"] not in {r2["statistic"] for r2 in new_ci_rows}]
        all_rows = existing_rows + new_ci_rows
        with open(ci_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(all_rows[0].keys()))
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"Updated city-wide CI table -> {ci_path}", file=sys.stderr)
        for r in new_ci_rows:
            print(f"  {r['statistic']}: {r['estimate']} (90% CI: {r['ci_90pct_low']} to {r['ci_90pct_high']})", file=sys.stderr)

        # ---- Per-tract values for all 643 Houston tracts ----
        with open(PROCESSED / "houston_tracts.csv", encoding="utf-8") as fh:
            tracts = list(csv.DictReader(fh))

        cache_path = PROCESSED / "_vehicle_tenure_cache.csv"
        demo: dict[str, dict] = {}
        if cache_path.exists():
            with open(cache_path, newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    demo[row["geoid"]] = row
        else:
            geoids = [t["geoid"] for t in tracts]
            batch_size = 35
            for i in range(0, len(geoids), batch_size):
                batch = geoids[i : i + batch_size]
                result = self.census.fetch_batch(self.TABLES, batch, release="acs2024_5yr")
                for full_geoid, tables in result.items():
                    g = full_geoid.replace("14000US", "")
                    try:
                        vt = tables["B25044"]["estimate"]["B25044001"]
                        vzo = tables["B25044"]["estimate"]["B25044003"]
                        vzr = tables["B25044"]["estimate"]["B25044010"]
                        tt = tables["B25003"]["estimate"]["B25003001"]
                        rent = tables["B25003"]["estimate"]["B25003003"]
                    except (KeyError, TypeError):
                        continue
                    demo[g] = {
                        "zero_vehicle_rate": ((vzo + vzr) / vt) if vt else None,
                        "renter_occupied_rate": (rent / tt) if tt else None,
                    }
                print(f"  fetched vehicle/tenure demographics {i + len(batch)}/{len(geoids)}", file=sys.stderr)
                time.sleep(0.3)
            with open(cache_path, "w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=["geoid", "zero_vehicle_rate", "renter_occupied_rate"])
                writer.writeheader()
                for g, d2 in demo.items():
                    writer.writerow({"geoid": g, **d2})

        # merge into the existing extended-demographics file
        ext_path = PROCESSED / "tract_extended_demographics.csv"
        with open(ext_path, encoding="utf-8") as fh:
            ext_rows = list(csv.DictReader(fh))
        for r in ext_rows:
            d2 = demo.get(r["geoid"], {})
            r["zero_vehicle_rate"] = d2.get("zero_vehicle_rate", "")
            r["renter_occupied_rate"] = d2.get("renter_occupied_rate", "")
        with open(ext_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(ext_rows[0].keys()))
            writer.writeheader()
            writer.writerows(ext_rows)
        print(f"Merged vehicle/tenure rates into {ext_path}", file=sys.stderr)


if __name__ == "__main__":
    VehicleTenureDemographicsStage().run()
