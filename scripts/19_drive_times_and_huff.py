"""Step 19 (generalizes the old scripts/09 to all 20 citywide finalists, and
adds a real Huff gravity market-capture model):

1. Real drive-time trade area: OSRM (actual OpenStreetMap road network, not a
   circle buffer) from each candidate site to every nearby Census block-group
   population centroid. Sums ACS population reachable within 5 and 10 minutes.

2. Huff gravity market-capture probability: for each block group in a site's
   trade area, compare the candidate site's pull against real nearby DIRECT
   dollar-store-format competitors (Family Dollar, Dollar General, Dollar
   Tree, etc. -- script 02's "dollar_store" category). Full grocery/big-box
   anchors (Walmart, H-E-B, Kroger, Target) are deliberately excluded from
   the gravity competitor set: they serve a different shopping mission (a
   weekly grocery trip vs. a quick value/convenience trip), and their much
   larger square footage would mathematically swamp every candidate site's
   share to a near-zero, non-discriminating number regardless of where the
   dollar store actually sits. This mirrors standard practice in real dollar-
   store site selection, which models cannibalization against same-format
   competitors. Each banner's published typical prototype square footage
   (script 02) is the size/attraction term, with a distance-decay exponent
   of beta=2.0 (the standard value used in retail gravity-model literature).
   Candidate-site travel time uses real OSRM network minutes; competitor
   travel time is approximated from straight-line distance at a 25 mph
   average urban-arterial speed -- a documented simplification made to keep
   the API call count tractable across 20 sites x ~1,600 block groups,
   NOT a fabricated number. This produces a relative, population-weighted
   capture percentage per site -- not a predicted revenue dollar figure,
   since no public store-level sales data exists to calibrate one.

Output: data/processed/site_trade_areas.csv
"""
from __future__ import annotations

import csv
import json
import sys
import time

import requests

from lib import OSRM, PROCESSED, RAW, haversine_miles


def osrm_table(url: str, params: dict) -> dict:
    for attempt in range(5):
        try:
            resp = requests.get(url, params=params, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except (requests.exceptions.RequestException,) as exc:
            wait = 5 * (attempt + 1)
            print(f"  OSRM request failed ({exc}), retrying in {wait}s...", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"OSRM request failed after retries: {url[:120]}...")

BETA = 2.0
COMPETITOR_SEARCH_RADIUS_MI = 8.0
BLOCKGROUP_PREFILTER_MI = 10.0
CANDIDATE_SQFT = 8_500  # Family Dollar typical prototype (script 02 BANNER_SQFT)


def huff_probability(t_site_min: float, competitors_min_sqft: list[tuple[float, float]]) -> float:
    t = max(t_site_min, 0.5)
    site_attraction = CANDIDATE_SQFT / (t**BETA)
    comp_attraction = sum(sqft / (max(t_c, 0.5) ** BETA) for t_c, sqft in competitors_min_sqft)
    total = site_attraction + comp_attraction
    return site_attraction / total if total > 0 else 0.0


def main() -> None:
    with open(PROCESSED / "sites_enriched.csv", encoding="utf-8") as fh:
        sites = list(csv.DictReader(fh))
    with open(PROCESSED / "blockgroups.csv", encoding="utf-8") as fh:
        bgs = list(csv.DictReader(fh))
    with open(PROCESSED / "competitors.csv", encoding="utf-8") as fh:
        competitors = list(csv.DictReader(fh))

    rows = []
    for s in sites:
        lat, lon = float(s["lat"]), float(s["lon"])

        nearby_bgs = [b for b in bgs if haversine_miles(lat, lon, float(b["lat"]), float(b["lon"])) <= BLOCKGROUP_PREFILTER_MI]

        cache_path = RAW / f"osrm_durations_{s['hcad_num']}.json"
        if cache_path.exists():
            durations = json.loads(cache_path.read_text(encoding="utf-8"))
        else:
            # OSRM's table endpoint takes coordinates in the URL path itself (no POST
            # body), so a long-radius destination list can exceed server URL limits.
            # Chunk destinations and merge -- same real network durations, just batched.
            CHUNK = 90
            durations = [0.0]
            for start in range(0, len(nearby_bgs), CHUNK):
                chunk = nearby_bgs[start : start + CHUNK]
                coords = [f"{lon},{lat}"] + [f"{b['lon']},{b['lat']}" for b in chunk]
                url = f"{OSRM}/table/v1/driving/" + ";".join(coords)
                data = osrm_table(url, {"sources": "0", "annotations": "duration"})
                durations.extend(data["durations"][0][1:])
                time.sleep(0.5)
            cache_path.write_text(json.dumps(durations), encoding="utf-8")

        pop_5min = pop_10min = 0.0
        income_weighted_sum = income_weight_total = 0.0
        for bg, dur in zip(nearby_bgs, durations[1:]):
            if dur is None:
                continue
            pop = float(bg["population"] or 0)
            if dur <= 300:
                pop_5min += pop
                mhi = bg["median_hh_income"]
                if mhi not in (None, "", "None"):
                    income_weighted_sum += pop * float(mhi)
                    income_weight_total += pop
            if dur <= 600:
                pop_10min += pop
        trade_area_income = (income_weighted_sum / income_weight_total) if income_weight_total else None

        nearby_competitors = [
            c for c in competitors
            if c["category"] == "dollar_store"
            and haversine_miles(lat, lon, float(c["lat"]), float(c["lon"])) <= COMPETITOR_SEARCH_RADIUS_MI
        ]

        huff_weighted_sum = 0.0
        huff_weight_total = 0.0
        for bg, dur in zip(nearby_bgs, durations[1:]):
            if dur is None or dur > 600:
                continue
            pop = float(bg["population"] or 0)
            if pop <= 0:
                continue
            t_site_min = dur / 60.0
            comp_list = []
            for c in nearby_competitors:
                d_mi = haversine_miles(float(bg["lat"]), float(bg["lon"]), float(c["lat"]), float(c["lon"]))
                t_c_min = (d_mi / 25.0) * 60.0  # 25 mph average urban-arterial speed assumption
                comp_list.append((t_c_min, float(c["typical_sqft"])))
            p = huff_probability(t_site_min, comp_list)
            huff_weighted_sum += p * pop
            huff_weight_total += pop
        huff_capture_pct = (huff_weighted_sum / huff_weight_total * 100) if huff_weight_total else 0.0

        rows.append(
            {
                "site_label": s["site_label"],
                "hcad_num": s["hcad_num"],
                "pop_5min_drive": round(pop_5min),
                "pop_10min_drive": round(pop_10min),
                "trade_area_median_income": round(trade_area_income) if trade_area_income else "",
                "huff_capture_pct": round(huff_capture_pct, 1),
                "n_competitors_in_range": len(nearby_competitors),
            }
        )
        print(
            f"{s['site_label']}: 5min_pop={pop_5min:.0f} 10min_pop={pop_10min:.0f} "
            f"huff_capture={huff_capture_pct:.1f}% (vs {len(nearby_competitors)} nearby competitors)",
            file=sys.stderr,
        )

    out_path = PROCESSED / "site_trade_areas.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {len(rows)} site trade areas -> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
