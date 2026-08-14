"""Step 35: real cross-check of the OSM-sourced competitor pull (script 02)
against Overture Maps Places (free, open, ML-deduped, blending Meta +
Microsoft + TomTom + ~200 other sources) within 1.0 mile of each of the 20
citywide finalists. This project already found and documented a real OSM
coverage gap (Ross Dress for Less undercounted citywide) -- this stage
checks whether that kind of gap affects the specific finalist set actually
being scored, and if it does, feeds a corrected nearest-competitor distance
into script 20's competition_score rather than leaving a known-possible blind
spot unchecked.

Scope, disclosed rather than silently assumed: only the *nearest-competitor
distance* input to the scorecard is corrected here. The Huff market-capture
model (script 19) is NOT re-run against Overture-sourced data -- that would
require re-deriving the full block-group gravity calculation, and Overture's
brand-name coverage for major national chains (the arch-rivals the Huff model
actually competes against) is already strong in OSM; the documented gap this
project found was specifically a big-box anchor, not an arch-rival.

A second real finding surfaced by this check, reported but NOT auto-corrected
in this revision: Overture also found real, OSM-missed **existing Family
Dollar** locations near several finalists -- directly relevant to
cannibalization risk (script 24), not competitive threat. Folding this into
the cannibalization trade-area-overlap calculation would require reworking
script 24's population-overlap logic, a larger change out of scope here;
reported as `nearest_family_dollar_mi_incl_overture` for transparency so a
reviewer can see where the existing cannibalization numbers might be
understated, without silently changing them.

Output: data/processed/site_overture_supplement.csv
"""
from __future__ import annotations

import csv
import json
import sys

from .s02_fetch_competitors import FetchCompetitorsStage
from ..clients import OvertureClient
from ..core import PROCESSED, RAW, PipelineStage
from ..geometry import Geometry

RADIUS_MI = 1.0
MIN_CONFIDENCE = 0.6
DEDUPE_RADIUS_MI = 0.15  # a match this close to an existing OSM competitor of the same brand is the same real store


class OvertureSupplementStage(PipelineStage):
    id = "35"
    name = "overture_supplement"
    description = "Real Overture Maps cross-check of OSM-sourced competitor data within 1.0mi of each finalist"
    outputs = (PROCESSED / "site_overture_supplement.csv", PROCESSED / "overture_new_competitors_detail.csv")

    def __init__(self) -> None:
        self.client = OvertureClient()

    def run(self) -> None:
        with open(PROCESSED / "sites_enriched.csv", encoding="utf-8") as fh:
            sites = list(csv.DictReader(fh))
        with open(PROCESSED / "competitors.csv", encoding="utf-8") as fh:
            existing = list(csv.DictReader(fh))
        true_competitors = [c for c in existing if c["category"] in ("arch_rival", "sister_banner")]

        rows = []
        detail_rows = []
        for s in sites:
            lat, lon = float(s["lat"]), float(s["lon"])
            hcad = s["hcad_num"]
            places = self.query_cached(lat, lon, hcad)

            new_finds = []
            for p in places:
                if p["confidence"] < MIN_CONFIDENCE or not p["name"]:
                    continue
                brand = FetchCompetitorsStage.classify({"name": p["name"]})
                if brand == "Unknown" or brand not in FetchCompetitorsStage.BANNER_SQFT:
                    continue
                dist_mi = Geometry.haversine_miles(lat, lon, p["lat"], p["lon"])
                if dist_mi > RADIUS_MI:
                    continue
                already_known = any(
                    c["brand"] == brand and Geometry.haversine_miles(p["lat"], p["lon"], float(c["lat"]), float(c["lon"])) <= DEDUPE_RADIUS_MI
                    for c in existing
                )
                if already_known:
                    continue
                new_finds.append({"brand": brand, "name": p["name"], "lat": p["lat"], "lon": p["lon"], "dist_mi": dist_mi})
                detail_rows.append({"hcad_num": hcad, "brand": brand, "name": p["name"], "lat": p["lat"], "lon": p["lon"]})

            existing_nearest_mi = float(s["nearest_dollar_store_mi"])
            new_true_competitor_dists = [f["dist_mi"] for f in new_finds if f["brand"] in ("Dollar General", "Five Below", "Dollar Tree")]
            corrected_nearest_mi = min([existing_nearest_mi] + new_true_competitor_dists)

            existing_nearest_fd_mi = float(s["nearest_family_dollar_mi"])
            new_fd_dists = [f["dist_mi"] for f in new_finds if f["brand"] == "Family Dollar"]
            corrected_nearest_fd_mi = min([existing_nearest_fd_mi] + new_fd_dists)

            rows.append(
                {
                    "hcad_num": hcad,
                    "site_label": s["site_label"],
                    "overture_new_competitors_found_1mi": len(new_finds),
                    "overture_new_competitor_brands": "; ".join(sorted({f["brand"] for f in new_finds})) or "none",
                    "nearest_dollar_store_mi_osm_only": round(existing_nearest_mi, 2),
                    "nearest_dollar_store_mi_incl_overture": round(corrected_nearest_mi, 2),
                    "nearest_family_dollar_mi_osm_only": round(existing_nearest_fd_mi, 2),
                    "nearest_family_dollar_mi_incl_overture": round(corrected_nearest_fd_mi, 2),
                }
            )
            flag = " -- OSM undercounted, corrected" if corrected_nearest_mi < existing_nearest_mi - 0.01 else ""
            print(
                f"{s['site_label']}: {len(new_finds)} real Overture-sourced competitor(s) not in OSM within 1mi{flag}",
                file=sys.stderr,
            )

        out_path = PROCESSED / "site_overture_supplement.csv"
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        detail_path = PROCESSED / "overture_new_competitors_detail.csv"
        with open(detail_path, "w", newline="", encoding="utf-8") as fh:
            fieldnames = ["hcad_num", "brand", "name", "lat", "lon"]
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(detail_rows)

        total_new = sum(r["overture_new_competitors_found_1mi"] for r in rows)
        print(f"\n{total_new} real competitor(s) found by Overture but missed by OSM across all 20 finalists -> {out_path}", file=sys.stderr)
        print(f"Wrote {len(detail_rows)} individual Overture-sourced competitor points -> {detail_path}", file=sys.stderr)

    def query_cached(self, lat: float, lon: float, hcad: str) -> list[dict]:
        cache_path = RAW / f"overture_places_{hcad}.json"
        if cache_path.exists():
            return json.loads(cache_path.read_text(encoding="utf-8"))
        pad_lat = RADIUS_MI / 69.0
        pad_lon = RADIUS_MI / 60.0
        places = self.client.places_in_bbox(lon - pad_lon, lat - pad_lat, lon + pad_lon, lat + pad_lat)
        cache_path.write_text(json.dumps(places), encoding="utf-8")
        return places


if __name__ == "__main__":
    OvertureSupplementStage().run()
