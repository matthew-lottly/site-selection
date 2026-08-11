"""Step 24: Real cannibalization-risk analysis against Family Dollar's own
existing network -- existing FD stores are not competitors, they're the
company's own coverage, and the question is how much of a new store's trade
area a nearby existing store already serves.

Method (3-step framework, adapted to only use real, computable inputs):

1. Hard/soft exclusion buffers on straight-line distance to the nearest
   existing Family Dollar:
     < 1.2 mi  -> High risk, automatic (industry rule-of-thumb minimum
                  spacing for a small-box discount format)
     1.2-2.5 mi -> depends on the overlap calculation below
     > 2.5 mi  -> Low risk, automatic

2. Trade-area overlap %: of the population inside the candidate site's REAL
   5-minute OSRM drive-time trade area (script 19's cached durations), what
   share also sits within 1.5 miles (straight-line) of the nearest existing
   Family Dollar. This mixes a network-based candidate trade area with a
   straight-line existing-store trade area -- an intentional, documented
   asymmetry (we have real routing for the candidate but did not re-run
   full network routing from 1,603 block groups to every existing FD store,
   which would multiply the OSRM call count ~60x for a secondary metric);
   flagged here and in the validation doc, not hidden.
     < 15% overlap -> Low risk
     15-30% overlap -> Moderate risk
     > 30% overlap -> High risk

3. NOT computed: a "net new sales $" figure. The source framework calls for
   Candidate Site Projected Sales minus Diverted Sales -- both require a
   calibrated revenue model, and no public store-level sales data exists to
   build one (see docs/methodology.md Stage 5 for the same reasoning applied
   to the Huff model). Reporting a dollar figure here would be a fabricated
   number dressed up as precise. Instead we report a real, computed proxy:
   Net New Population Reach = 5-min drive population MINUS the population
   already inside the overlap with the nearest existing Family Dollar. It
   answers the same underlying question (how much of this trade area is
   genuinely incremental) without inventing a number.

Output: data/processed/cannibalization.csv
"""
from __future__ import annotations

import csv
import json
import sys

from lib import PROCESSED, RAW, haversine_miles

HARD_BUFFER_HIGH_MI = 1.2
HARD_BUFFER_CLEAR_MI = 2.5
OVERLAP_RADIUS_MI = 1.5
OVERLAP_LOW_PCT = 15.0
OVERLAP_HIGH_PCT = 30.0


def risk_category(nearest_fd_mi: float, overlap_pct: float) -> str:
    if nearest_fd_mi < HARD_BUFFER_HIGH_MI:
        return "High (hard buffer: existing FD < 1.2 mi)"
    if nearest_fd_mi > HARD_BUFFER_CLEAR_MI and overlap_pct < OVERLAP_LOW_PCT:
        return "Low"
    if overlap_pct > OVERLAP_HIGH_PCT:
        return "High (trade-area overlap)"
    if overlap_pct >= OVERLAP_LOW_PCT:
        return "Moderate"
    return "Low"


def main() -> None:
    with open(PROCESSED / "sites_enriched.csv", encoding="utf-8") as fh:
        sites = list(csv.DictReader(fh))
    with open(PROCESSED / "site_trade_areas.csv", encoding="utf-8") as fh:
        trade = {r["hcad_num"]: r for r in csv.DictReader(fh)}
    with open(PROCESSED / "competitors.csv", encoding="utf-8") as fh:
        competitors = list(csv.DictReader(fh))
    with open(PROCESSED / "blockgroups.csv", encoding="utf-8") as fh:
        bgs = list(csv.DictReader(fh))
    family_dollar = [c for c in competitors if c["category"] == "family_dollar"]

    rows = []
    for s in sites:
        lat, lon = float(s["lat"]), float(s["lon"])
        hcad = s["hcad_num"]
        nearest_fd = min(family_dollar, key=lambda x: haversine_miles(lat, lon, float(x["lat"]), float(x["lon"])))
        nearest_fd_mi = haversine_miles(lat, lon, float(nearest_fd["lat"]), float(nearest_fd["lon"]))

        durations_path = RAW / f"osrm_durations_{hcad}.json"
        durations = json.loads(durations_path.read_text(encoding="utf-8"))
        nearby_bgs = [b for b in bgs if haversine_miles(lat, lon, float(b["lat"]), float(b["lon"])) <= 10.0]

        pop_5min = 0.0
        overlap_pop = 0.0
        for bg, dur in zip(nearby_bgs, durations[1:]):
            if dur is None or dur > 300:
                continue
            pop = float(bg["population"] or 0)
            pop_5min += pop
            d_to_fd = haversine_miles(float(bg["lat"]), float(bg["lon"]), float(nearest_fd["lat"]), float(nearest_fd["lon"]))
            if d_to_fd <= OVERLAP_RADIUS_MI:
                overlap_pop += pop

        overlap_pct = (overlap_pop / pop_5min * 100) if pop_5min else 0.0
        net_new_pop = pop_5min - overlap_pop
        risk = risk_category(nearest_fd_mi, overlap_pct)

        rows.append(
            {
                "site_label": s["site_label"],
                "hcad_num": hcad,
                "nearest_family_dollar": nearest_fd["name"],
                "nearest_family_dollar_mi": round(nearest_fd_mi, 2),
                "hard_buffer_flag": "High risk (<1.2mi)" if nearest_fd_mi < HARD_BUFFER_HIGH_MI else ("Clear (>2.5mi)" if nearest_fd_mi > HARD_BUFFER_CLEAR_MI else "Soft buffer, check overlap"),
                "pop_5min_drive": round(pop_5min),
                "overlap_pop_within_1_5mi_of_fd": round(overlap_pop),
                "overlap_pct": round(overlap_pct, 1),
                "net_new_population_reach": round(net_new_pop),
                "cannibalization_risk": risk,
            }
        )
        print(
            f"{s['site_label']}: nearest FD {nearest_fd_mi:.2f}mi | overlap {overlap_pct:.1f}% "
            f"| net-new pop reach {net_new_pop:,.0f} | risk: {risk}",
            file=sys.stderr,
        )

    out_path = PROCESSED / "cannibalization.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {len(rows)} cannibalization assessments -> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
