"""Step 20 (generalizes the old scripts/10 to all 20 citywide finalists, and
folds in the Huff gravity market-capture score): combine every real data
layer collected so far into a transparent, min-max-normalized weighted
scorecard spanning all 10 Houston neighborhoods evaluated, and select the
citywide recommendation.

Weights (documented so the VP can interrogate the call):
  25% Trade-area demand      -- 5-minute drive-time population, scaled by how
                                 closely the population-weighted median HH
                                 income in that trade area sits inside Family
                                 Dollar's core $20k-$55k customer band
  20% Huff market capture     -- population-weighted gravity-model capture
                                 probability against every real nearby
                                 competitor (script 19)
  15% Competitive white space -- straight-line distance to the nearest
                                 existing direct dollar-store competitor
                                 (simple, exec-legible cross-check on the
                                 Huff score)
  15% Traffic & visibility    -- AADT on the actual frontage/arterial road
                                 (freeway mainlane counts excluded, script 18)
  15% Site feasibility/cost   -- land cost per acre (lower is better), bonus
                                 for shovel-ready vacant land
  10% Flood risk              -- any mapped Special Flood Hazard Area (FEMA
                                 Zone A/AE/etc.) is heavily penalized

Output: data/processed/scorecard.csv (ranked, all 20 citywide candidates)
"""
from __future__ import annotations

import csv
import sys

from ..core import PROCESSED, PipelineStage


class ScoreSitesCitywideStage(PipelineStage):
    id = "20"
    name = "score_sites_citywide"
    description = "Weighted, min-max-normalized citywide scorecard and primary site recommendation"
    outputs = (PROCESSED / "scorecard.csv",)

    # industry rule-of-thumb minimum viable frontage traffic for a discount-retail pad
    AADT_BENCHMARK = 8_000

    def run(self) -> None:
        with open(PROCESSED / "sites_enriched.csv", encoding="utf-8") as fh:
            sites = {r["hcad_num"]: r for r in csv.DictReader(fh)}
        with open(PROCESSED / "site_trade_areas.csv", encoding="utf-8") as fh:
            trade = {r["hcad_num"]: r for r in csv.DictReader(fh)}

        hcad_nums = list(sites.keys())

        demand_raw = []
        for h in hcad_nums:
            pop5 = float(trade[h]["pop_5min_drive"])
            mhi = trade[h]["trade_area_median_income"]
            fit = self.income_fit(float(mhi)) if mhi not in (None, "") else 0.5
            demand_raw.append(pop5 * (0.4 + 0.6 * fit))

        huff_raw = [float(trade[h]["huff_capture_pct"]) for h in hcad_nums]
        competition_raw = [float(sites[h]["nearest_dollar_store_mi"]) for h in hcad_nums]
        cost_per_acre_raw = [float(sites[h]["land_value"]) / max(float(sites[h]["acreage"]), 0.01) for h in hcad_nums]
        flood_raw = [0.0 if sites[h]["in_sfha"] == "T" else 1.0 for h in hcad_nums]

        # A retail pad has no driveway onto a limited-access freeway, so a station flagged
        # aadt_on_freeway (script 18) is not a real frontage-traffic reading for that site.
        # Rather than reward the (irrelevant) freeway mainlane count or unfairly zero it out,
        # treat it as unverified: score it at the low end of the VERIFIED arterial readings.
        verified_aadt = [float(sites[h]["aadt"]) for h in hcad_nums if sites[h]["aadt_on_freeway"] != "True"]
        fallback_aadt = min(verified_aadt) if verified_aadt else 0.0
        traffic_raw = [
            fallback_aadt if sites[h]["aadt_on_freeway"] == "True" else float(sites[h]["aadt"])
            for h in hcad_nums
        ]

        demand_score = self.minmax(demand_raw, True)
        huff_score = self.minmax(huff_raw, True)
        competition_score = self.minmax(competition_raw, True)
        traffic_score = self.minmax(traffic_raw, True)
        cost_score = self.minmax(cost_per_acre_raw, False)
        flood_score = [100.0 if f == 1.0 else 0.0 for f in flood_raw]
        vacant_bonus = [10 if "Vacant" in sites[h]["site_type"] else 0 for h in hcad_nums]

        rows = []
        for i, h in enumerate(hcad_nums):
            cost_component = min(100.0, cost_score[i] + vacant_bonus[i])
            total = (
                0.25 * demand_score[i]
                + 0.20 * huff_score[i]
                + 0.15 * competition_score[i]
                + 0.15 * traffic_score[i]
                + 0.15 * cost_component
                + 0.10 * flood_score[i]
            )
            rows.append(
                {
                    "site_label": sites[h]["site_label"],
                    "hcad_num": h,
                    "neighborhood": sites[h]["neighborhood"],
                    "cluster_id": sites[h]["cluster_id"],
                    "address": sites[h]["address"],
                    "acreage": sites[h]["acreage"],
                    "site_type": sites[h]["site_type"],
                    "flood_zone": sites[h]["flood_zone"],
                    "in_sfha": sites[h]["in_sfha"],
                    "aadt": sites[h]["aadt"],
                    "aadt_road_verified": sites[h]["aadt_road_verified"],
                    "aadt_on_freeway": sites[h]["aadt_on_freeway"],
                    "meets_8000_aadt_benchmark": traffic_raw[i] >= self.AADT_BENCHMARK,
                    "raw_traffic_aadt_used_for_gate": round(traffic_raw[i]),
                    "nearest_dollar_store_mi": sites[h]["nearest_dollar_store_mi"],
                    "nearest_dollar_store": sites[h]["nearest_dollar_store"],
                    "pop_5min_drive": trade[h]["pop_5min_drive"],
                    "pop_10min_drive": trade[h]["pop_10min_drive"],
                    "trade_area_median_income": trade[h]["trade_area_median_income"],
                    "huff_capture_pct": trade[h]["huff_capture_pct"],
                    "demand_score": round(demand_score[i], 1),
                    "huff_score": round(huff_score[i], 1),
                    "competition_score": round(competition_score[i], 1),
                    "traffic_score": round(traffic_score[i], 1),
                    "cost_feasibility_score": round(cost_component, 1),
                    "flood_score": round(flood_score[i], 1),
                    "total_score": round(total, 1),
                }
            )

        rows.sort(key=lambda r: -r["total_score"])
        for i, r in enumerate(rows, start=1):
            r["raw_score_rank"] = i

        # The weighted score treats traffic as one factor among six (15%), but a
        # site that fails the industry-standard 8,000 AADT minimum viable-traffic
        # benchmark is not a real candidate regardless of how well it scores on
        # everything else -- a discount retailer depends on drive-by visibility a
        # low-traffic frontage road cannot provide. Rather than silently let the
        # weighted average paper over that, the PRIMARY recommendation is the
        # highest scoring site that also clears the benchmark; any higher-raw-score
        # site that fails it is kept in the table (for transparency) but explicitly
        # is not eligible to be "the" recommendation.
        qualified = [r for r in rows if r["meets_8000_aadt_benchmark"]]
        primary = qualified[0] if qualified else rows[0]
        for r in rows:
            r["primary_recommendation"] = r["hcad_num"] == primary["hcad_num"]
        # move the primary recommendation to the front of the file so downstream
        # scripts (isochrone, map) that read row 0 as "the winner" pick it up
        # correctly, while raw_score_rank preserves the pure-score ordering
        rows.sort(key=lambda r: (not r["primary_recommendation"], -r["total_score"]))

        out_path = PROCESSED / "scorecard.csv"
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        print(f"{'#':<5}{'ScoreRk':<8}{'Neighborhood':<14}{'Site':<40}{'Demand':>7}{'Huff':>6}{'Comp':>6}{'Traf':>6}{'Cost':>6}{'Flood':>6}{'TOTAL':>7}  AADT>=8k?", file=sys.stderr)
        for i, r in enumerate(rows, 1):
            tag = " <- PRIMARY RECOMMENDATION" if r["primary_recommendation"] else ""
            print(
                f"{i:<5}{r['raw_score_rank']:<8}{r['neighborhood']:<14}{r['address'][:39]:<40}{r['demand_score']:>7}{r['huff_score']:>6}"
                f"{r['competition_score']:>6}{r['traffic_score']:>6}{r['cost_feasibility_score']:>6}{r['flood_score']:>6}{r['total_score']:>7}  "
                f"{'yes' if r['meets_8000_aadt_benchmark'] else 'NO'}{tag}",
                file=sys.stderr,
            )
        if rows[0]["raw_score_rank"] != 1:
            print(
                f"\nNote: raw score rank #1 ({[r for r in rows if r['raw_score_rank']==1][0]['address']}) "
                f"fails the 8,000 AADT benchmark and was NOT selected as the primary recommendation.",
                file=sys.stderr,
            )
        print(f"\nRECOMMENDED SITE: {rows[0]['site_label']} ({rows[0]['address']}, {rows[0]['neighborhood']})", file=sys.stderr)
        print(f"Wrote scorecard -> {out_path}", file=sys.stderr)

    @staticmethod
    def income_fit(mhi: float) -> float:
        if 20_000 <= mhi <= 55_000:
            return 1.0
        if mhi < 20_000:
            return max(0.0, mhi / 20_000)
        if mhi <= 80_000:
            return max(0.0, 1 - (mhi - 55_000) / 25_000)
        return 0.0

    @staticmethod
    def minmax(values: list[float], higher_is_better: bool = True) -> list[float]:
        lo, hi = min(values), max(values)
        if hi == lo:
            return [100.0 for _ in values]
        scaled = [(v - lo) / (hi - lo) for v in values]
        if not higher_is_better:
            scaled = [1 - s for s in scaled]
        return [s * 100 for s in scaled]


if __name__ == "__main__":
    ScoreSitesCitywideStage().run()
