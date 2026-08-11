"""Step 10: Combine every real data layer collected so far into a
transparent, min-max-normalized weighted scorecard and select the
recommended site.

Weights (documented so the VP can interrogate the call):
  30% Trade-area demand   -- 5-minute drive-time population, scaled by how
                              closely the population-weighted median household
                              income in that trade area sits inside Family
                              Dollar's core $20k-$55k customer band
  25% Competitive white space -- distance to the nearest existing Family
                              Dollar / Dollar General / Dollar Tree
  20% Traffic & visibility -- AADT on the frontage road (TxDOT)
  15% Site feasibility/cost -- land cost per acre (lower is better) with a
                              bonus for shovel-ready vacant land over a
                              teardown/redevelopment parcel
  10% Flood risk           -- FEMA zone; any mapped Special Flood Hazard Area
                              is heavily penalized

Output: data/processed/scorecard.csv (ranked)
"""
from __future__ import annotations

import csv
import json
import sys

from lib import PROCESSED, RAW


def income_fit(mhi: float) -> float:
    if 20_000 <= mhi <= 55_000:
        return 1.0
    if mhi < 20_000:
        return max(0.0, mhi / 20_000)
    if mhi <= 80_000:
        return max(0.0, 1 - (mhi - 55_000) / 25_000)
    return 0.0


def minmax(values: list[float], higher_is_better: bool = True) -> list[float]:
    lo, hi = min(values), max(values)
    if hi == lo:
        return [100.0 for _ in values]
    scaled = [(v - lo) / (hi - lo) for v in values]
    if not higher_is_better:
        scaled = [1 - s for s in scaled]
    return [s * 100 for s in scaled]


def main() -> None:
    with open(PROCESSED / "sites_enriched.csv", encoding="utf-8") as fh:
        sites = {r["hcad_num"]: r for r in csv.DictReader(fh)}
    with open(PROCESSED / "site_trade_areas.csv", encoding="utf-8") as fh:
        trade = {r["hcad_num"]: r for r in csv.DictReader(fh)}
    with open(PROCESSED / "blockgroups.csv", encoding="utf-8") as fh:
        bgs = list(csv.DictReader(fh))

    hcad_nums = list(sites.keys())

    # population-weighted median HH income within each site's 5-min drive area
    trade_area_income = {}
    for h in hcad_nums:
        durations = json.loads((RAW / f"osrm_durations_{h}.json").read_text(encoding="utf-8"))
        weighted_sum, weight_total = 0.0, 0.0
        for bg, dur in zip(bgs, durations[1:]):
            if dur is None or dur > 300:
                continue
            pop = float(bg["population"] or 0)
            mhi = bg["median_hh_income"]
            if not mhi or mhi in ("", "None"):
                continue
            weighted_sum += pop * float(mhi)
            weight_total += pop
        trade_area_income[h] = (weighted_sum / weight_total) if weight_total else 35_000.0

    demand_raw = []
    for h in hcad_nums:
        pop5 = float(trade[h]["pop_5min_drive"])
        fit = income_fit(trade_area_income[h])
        demand_raw.append(pop5 * (0.4 + 0.6 * fit))  # income fit tempers but doesn't zero out population

    competition_raw = [float(sites[h]["nearest_dollar_store_mi"]) for h in hcad_nums]
    traffic_raw = [float(sites[h]["aadt"]) for h in hcad_nums]
    cost_per_acre_raw = [float(sites[h]["land_value"]) / max(float(sites[h]["acreage"]), 0.01) for h in hcad_nums]
    flood_raw = [0.0 if sites[h]["in_sfha"] == "T" else 1.0 for h in hcad_nums]

    demand_score = minmax(demand_raw, True)
    competition_score = minmax(competition_raw, True)
    traffic_score = minmax(traffic_raw, True)
    cost_score = minmax(cost_per_acre_raw, False)
    flood_score = [100.0 if f == 1.0 else 0.0 for f in flood_raw]

    vacant_bonus = [10 if "Vacant" in sites[h]["site_type"] else 0 for h in hcad_nums]

    rows = []
    for i, h in enumerate(hcad_nums):
        cost_component = min(100.0, cost_score[i] + vacant_bonus[i])
        total = (
            0.30 * demand_score[i]
            + 0.25 * competition_score[i]
            + 0.20 * traffic_score[i]
            + 0.15 * cost_component
            + 0.10 * flood_score[i]
        )
        rows.append(
            {
                "site_label": sites[h]["site_label"],
                "hcad_num": h,
                "address": sites[h]["address"],
                "acreage": sites[h]["acreage"],
                "site_type": sites[h]["site_type"],
                "flood_zone": sites[h]["flood_zone"],
                "aadt": sites[h]["aadt"],
                "nearest_dollar_store_mi": sites[h]["nearest_dollar_store_mi"],
                "nearest_dollar_store": sites[h]["nearest_dollar_store"],
                "pop_5min_drive": trade[h]["pop_5min_drive"],
                "pop_10min_drive": trade[h]["pop_10min_drive"],
                "trade_area_median_income": round(trade_area_income[h]),
                "demand_score": round(demand_score[i], 1),
                "competition_score": round(competition_score[i], 1),
                "traffic_score": round(traffic_score[i], 1),
                "cost_feasibility_score": round(cost_component, 1),
                "flood_score": round(flood_score[i], 1),
                "total_score": round(total, 1),
            }
        )

    rows.sort(key=lambda r: -r["total_score"])

    out_path = PROCESSED / "scorecard.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"{'Rank':<5}{'Site':<45}{'Demand':>8}{'Comp':>7}{'Traffic':>8}{'Cost':>7}{'Flood':>7}{'TOTAL':>8}", file=sys.stderr)
    for i, r in enumerate(rows, 1):
        print(
            f"{i:<5}{r['site_label']:<45}{r['demand_score']:>8}{r['competition_score']:>7}"
            f"{r['traffic_score']:>8}{r['cost_feasibility_score']:>7}{r['flood_score']:>7}{r['total_score']:>8}",
            file=sys.stderr,
        )
    print(f"\nRECOMMENDED SITE: {rows[0]['site_label']} ({rows[0]['address']})", file=sys.stderr)
    print(f"Wrote scorecard -> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
