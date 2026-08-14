"""Step 20 (generalizes the old scripts/10 to all 20 citywide finalists, and
folds in the Huff gravity market-capture score): combine every real data
layer collected so far into a transparent, min-max-normalized weighted
scorecard spanning all 10 Houston neighborhoods evaluated, and select the
citywide recommendation.

Weights (documented so the VP can interrogate the call). Rebalanced from the
original 25/20/15/15/15/10 split to make room for a real crime-risk factor
(script 30, real HPD NIBRS Part I incident data) at the same 10% weight as
flood risk -- both are risk-mitigation factors, scored the same way,
penalizing sites with a worse real reading:
  22% Trade-area demand      -- a blended composite (see below), still led by
                                 5-minute drive-time RESIDENTIAL population
                                 scaled by income fit, now also incorporating
                                 three real signals this model previously had
                                 no visibility into at all (scripts 32-34)
  18% Huff market capture     -- population-weighted gravity-model capture
                                 probability against every real nearby
                                 competitor (script 19)
  13% Competitive white space -- straight-line distance to the nearest
                                 existing direct dollar-store competitor,
                                 corrected where Overture Maps found a real
                                 competitor OSM missed (script 35) -- simple,
                                 exec-legible cross-check on the Huff score
  13% Traffic & visibility    -- AADT on the actual frontage/arterial road
                                 (freeway mainlane counts excluded, script 18)
  14% Site feasibility/cost   -- land cost per acre (lower is better), bonus
                                 for shovel-ready vacant land
  10% Flood risk              -- any mapped Special Flood Hazard Area (FEMA
                                 Zone A/AE/etc.) is heavily penalized
  10% Crime risk               -- real HPD Part I violent + property incident
                                 count within 0.5 mi, trailing 12 months
                                 (script 30); more incidents is penalized

Trade-area demand sub-weights (blended the same way cost_feasibility_score
already blends land-cost-per-acre with a vacant-land bonus into one line --
each sub-component stays visible as its own column for transparency, only
the top-level factor count stays fixed at seven):
  50% Residential 5-min drive population x income fit (original signal)
  12% Real LIHTC affordable-housing units within 1mi (script 32) -- proxy for
      concentration of Family Dollar's core low-income customer base
  12% Real LEHD daytime workplace population within 5-min drive (script 33)
      -- a signal this model had zero visibility into before: office/retail/
      industrial workers who pass a site on a commute or lunch break
   8% Real USDA share of tract population beyond 0.5mi from a SNAP-authorized
      food retailer (script 34) -- a real, on-topic "underserved area" signal
      for a dollar-store expansion thesis
  10% Real HUD Multifamily (FHA-insured/assisted) units within 1mi (script 38)
      -- a different federal program than LIHTC (mortgage insurance/project-
      based assistance, not tax credits), so a real, complementary signal,
      not a duplicate
   8% Real federal Qualified Opportunity Zone designation (script 37) -- a
      binary flag (100/0), same pattern as flood risk, since a site's tract
      either carries the real federal designation or it doesn't

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
        with open(PROCESSED / "site_crime_risk.csv", encoding="utf-8") as fh:
            crime = {r["hcad_num"]: r for r in csv.DictReader(fh)}
        with open(PROCESSED / "site_lihtc.csv", encoding="utf-8") as fh:
            lihtc = {r["hcad_num"]: r for r in csv.DictReader(fh)}
        with open(PROCESSED / "site_daytime_population.csv", encoding="utf-8") as fh:
            daytime = {r["hcad_num"]: r for r in csv.DictReader(fh)}
        with open(PROCESSED / "site_food_access.csv", encoding="utf-8") as fh:
            food_access = {r["hcad_num"]: r for r in csv.DictReader(fh)}
        with open(PROCESSED / "site_overture_supplement.csv", encoding="utf-8") as fh:
            overture = {r["hcad_num"]: r for r in csv.DictReader(fh)}
        with open(PROCESSED / "site_hud_multifamily.csv", encoding="utf-8") as fh:
            multifamily = {r["hcad_num"]: r for r in csv.DictReader(fh)}
        with open(PROCESSED / "site_opportunity_zones.csv", encoding="utf-8") as fh:
            opp_zones = {r["hcad_num"]: r for r in csv.DictReader(fh)}

        hcad_nums = list(sites.keys())

        residential_demand_raw = []
        for h in hcad_nums:
            pop5 = float(trade[h]["pop_5min_drive"])
            mhi = trade[h]["trade_area_median_income"]
            fit = self.income_fit(float(mhi)) if mhi not in (None, "") else 0.5
            residential_demand_raw.append(pop5 * (0.4 + 0.6 * fit))
        lihtc_raw = [float(lihtc[h]["lihtc_unit_count_1mi"]) for h in hcad_nums]
        daytime_raw = [float(daytime[h]["daytime_workplace_pop_5min_drive"]) for h in hcad_nums]
        food_access_raw = [float(food_access[h]["pct_tract_pop_beyond_half_mi_from_food_retailer"]) for h in hcad_nums]
        multifamily_raw = [float(multifamily[h]["hud_multifamily_assisted_unit_count_1mi"]) for h in hcad_nums]
        opp_zone_raw = [1.0 if opp_zones[h]["in_opportunity_zone"] == "True" else 0.0 for h in hcad_nums]

        residential_demand_score = self.minmax(residential_demand_raw, True)
        lihtc_score = self.minmax(lihtc_raw, True)
        daytime_score = self.minmax(daytime_raw, True)
        food_access_score = self.minmax(food_access_raw, True)
        multifamily_score = self.minmax(multifamily_raw, True)
        opp_zone_score = [100.0 if f == 1.0 else 0.0 for f in opp_zone_raw]
        demand_score = [
            0.50 * residential_demand_score[i]
            + 0.12 * lihtc_score[i]
            + 0.12 * daytime_score[i]
            + 0.08 * food_access_score[i]
            + 0.10 * multifamily_score[i]
            + 0.08 * opp_zone_score[i]
            for i in range(len(hcad_nums))
        ]

        huff_raw = [float(trade[h]["huff_capture_pct"]) for h in hcad_nums]
        # Overture-corrected nearest-competitor distance where it found a real
        # competitor OSM missed (script 35); falls back to the OSM-only reading
        # for every other site, unchanged.
        competition_raw = [float(overture[h]["nearest_dollar_store_mi_incl_overture"]) for h in hcad_nums]
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
        crime_raw = [float(crime[h]["total_index_crime_count_12mo_0_5mi"]) for h in hcad_nums]

        huff_score = self.minmax(huff_raw, True)
        competition_score = self.minmax(competition_raw, True)
        traffic_score = self.minmax(traffic_raw, True)
        cost_score = self.minmax(cost_per_acre_raw, False)
        flood_score = [100.0 if f == 1.0 else 0.0 for f in flood_raw]
        crime_score = self.minmax(crime_raw, False)  # fewer real nearby incidents scores higher
        vacant_bonus = [10 if "Vacant" in sites[h]["site_type"] else 0 for h in hcad_nums]

        rows = []
        for i, h in enumerate(hcad_nums):
            cost_component = min(100.0, cost_score[i] + vacant_bonus[i])
            total = (
                0.22 * demand_score[i]
                + 0.18 * huff_score[i]
                + 0.13 * competition_score[i]
                + 0.13 * traffic_score[i]
                + 0.14 * cost_component
                + 0.10 * flood_score[i]
                + 0.10 * crime_score[i]
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
                    "nearest_dollar_store_mi_incl_overture": overture[h]["nearest_dollar_store_mi_incl_overture"],
                    "overture_new_competitors_found_1mi": overture[h]["overture_new_competitors_found_1mi"],
                    "nearest_family_dollar_mi_incl_overture": overture[h]["nearest_family_dollar_mi_incl_overture"],
                    "pop_5min_drive": trade[h]["pop_5min_drive"],
                    "pop_10min_drive": trade[h]["pop_10min_drive"],
                    "trade_area_median_income": trade[h]["trade_area_median_income"],
                    "huff_capture_pct": trade[h]["huff_capture_pct"],
                    "violent_crime_count_12mo_0_5mi": crime[h]["violent_crime_count_12mo_0_5mi"],
                    "property_crime_count_12mo_0_5mi": crime[h]["property_crime_count_12mo_0_5mi"],
                    "total_index_crime_count_12mo_0_5mi": crime[h]["total_index_crime_count_12mo_0_5mi"],
                    "lihtc_unit_count_1mi": lihtc[h]["lihtc_unit_count_1mi"],
                    "daytime_workplace_pop_5min_drive": daytime[h]["daytime_workplace_pop_5min_drive"],
                    "pct_tract_pop_beyond_half_mi_from_food_retailer": food_access[h]["pct_tract_pop_beyond_half_mi_from_food_retailer"],
                    "hud_multifamily_assisted_unit_count_1mi": multifamily[h]["hud_multifamily_assisted_unit_count_1mi"],
                    "in_opportunity_zone": opp_zones[h]["in_opportunity_zone"],
                    "residential_demand_subscore": round(residential_demand_score[i], 1),
                    "lihtc_subscore": round(lihtc_score[i], 1),
                    "daytime_pop_subscore": round(daytime_score[i], 1),
                    "food_access_subscore": round(food_access_score[i], 1),
                    "multifamily_subscore": round(multifamily_score[i], 1),
                    "opportunity_zone_subscore": round(opp_zone_score[i], 1),
                    "demand_score": round(demand_score[i], 1),
                    "huff_score": round(huff_score[i], 1),
                    "competition_score": round(competition_score[i], 1),
                    "traffic_score": round(traffic_score[i], 1),
                    "cost_feasibility_score": round(cost_component, 1),
                    "flood_score": round(flood_score[i], 1),
                    "crime_score": round(crime_score[i], 1),
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

        print(f"{'#':<5}{'ScoreRk':<8}{'Neighborhood':<14}{'Site':<40}{'Demand':>7}{'Huff':>6}{'Comp':>6}{'Traf':>6}{'Cost':>6}{'Flood':>6}{'Crime':>6}{'TOTAL':>7}  AADT>=8k?", file=sys.stderr)
        for i, r in enumerate(rows, 1):
            tag = " <- PRIMARY RECOMMENDATION" if r["primary_recommendation"] else ""
            print(
                f"{i:<5}{r['raw_score_rank']:<8}{r['neighborhood']:<14}{r['address'][:39]:<40}{r['demand_score']:>7}{r['huff_score']:>6}"
                f"{r['competition_score']:>6}{r['traffic_score']:>6}{r['cost_feasibility_score']:>6}{r['flood_score']:>6}{r['crime_score']:>6}{r['total_score']:>7}  "
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
