"""Step 28: Multi-scenario sensitivity analysis -- does the recommendation
hold up under different, defensible weighting schemes, or is it an artifact
of the specific 22/18/13/13/14/10/10 split chosen in script 20?

Re-weights the SAME already-normalized 0-100 per-factor subscores computed
in script 20 (demand, Huff capture, competitive gap, traffic, cost/
feasibility, flood risk, crime risk) under 5 scenarios, and re-applies the
same 8,000-AADT primary-recommendation gate to each. No new data is fetched
-- this is a pure re-aggregation check on real, already-computed scores.

Output: data/processed/sensitivity_analysis.csv
"""
from __future__ import annotations

import csv
import sys

from ..core import PROCESSED, PipelineStage


class SensitivityAnalysisStage(PipelineStage):
    id = "28"
    name = "sensitivity_analysis"
    description = "Re-weighted scorecard sensitivity check across 5 alternative weighting scenarios"
    outputs = (PROCESSED / "sensitivity_analysis.csv",)

    # Each scenario's weights sum to 100. "Base" is script 20's documented split.
    SCENARIOS = {
        "Base (documented)":       {"demand": 22, "huff": 18, "competition": 13, "traffic": 13, "cost": 14, "flood": 10, "crime": 10},
        "Traffic-Heavy":           {"demand": 13, "huff": 13, "competition": 9,  "traffic": 35, "cost": 12, "flood": 9,  "crime": 9},
        "Cost-Heavy":              {"demand": 17, "huff": 13, "competition": 9,  "traffic": 9,  "cost": 35, "flood": 8,  "crime": 9},
        "Competition-Heavy":       {"demand": 13, "huff": 27, "competition": 27, "traffic": 9,  "cost": 9,  "flood": 5,  "crime": 10},
        "Demand-Heavy":            {"demand": 40, "huff": 13, "competition": 9,  "traffic": 9,  "cost": 9,  "flood": 10, "crime": 10},
        "Crime-Heavy":             {"demand": 15, "huff": 15, "competition": 10, "traffic": 10, "cost": 10, "flood": 10, "crime": 30},
    }

    FACTOR_COLUMN = {
        "demand": "demand_score", "huff": "huff_score", "competition": "competition_score",
        "traffic": "traffic_score", "cost": "cost_feasibility_score", "flood": "flood_score",
        "crime": "crime_score",
    }

    def run(self) -> None:
        with open(PROCESSED / "scorecard.csv", encoding="utf-8") as fh:
            sites = list(csv.DictReader(fh))

        results = []
        for scenario_name, weights in self.SCENARIOS.items():
            assert sum(weights.values()) == 100, f"{scenario_name} weights don't sum to 100"
            scored = []
            for s in sites:
                total = sum((w / 100.0) * float(s[self.FACTOR_COLUMN[factor]]) for factor, w in weights.items())
                scored.append((total, s))
            scored.sort(key=lambda x: -x[0])

            qualified = [(t, s) for t, s in scored if s["meets_8000_aadt_benchmark"] == "True"]
            winner_score, winner = qualified[0] if qualified else scored[0]
            raw_top_score, raw_top = scored[0]

            results.append(
                {
                    "scenario": scenario_name,
                    "weights": ", ".join(f"{k}={v}%" for k, v in weights.items()),
                    "primary_recommendation": winner["address"],
                    "primary_recommendation_neighborhood": winner["neighborhood"],
                    "primary_recommendation_score": round(winner_score, 1),
                    "raw_top_score_site": raw_top["address"],
                    "raw_top_score_value": round(raw_top_score, 1),
                    "same_as_base_recommendation": winner["hcad_num"] == sites[0]["hcad_num"],
                }
            )

        out_path = PROCESSED / "sensitivity_analysis.csv"
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(results[0].keys()))
            writer.writeheader()
            writer.writerows(results)

        print(f"Base primary recommendation: {sites[0]['address']} ({sites[0]['neighborhood']})\n", file=sys.stderr)
        print(f"{'Scenario':<22}{'Primary recommendation':<45}{'Score':>7}  Same as base?", file=sys.stderr)
        for r in results:
            print(f"{r['scenario']:<22}{r['primary_recommendation']:<45}{r['primary_recommendation_score']:>7}  {'YES' if r['same_as_base_recommendation'] else 'NO -- differs'}", file=sys.stderr)

        stable = all(r["same_as_base_recommendation"] for r in results)
        print(f"\n{'STABLE' if stable else 'NOT STABLE'} across all {len(results)} weighting scenarios tested.", file=sys.stderr)
        print(f"Wrote {out_path}", file=sys.stderr)


if __name__ == "__main__":
    SensitivityAnalysisStage().run()
