"""Step 25: Two things the analysis was missing --

1. Houston-specific demographic nuance the ACS already tracks but the
   pipeline hadn't pulled: % foreign-born, % Spanish spoken at home, and
   average household size, for all 643 Houston tracts. Houston corridors
   like Gulfton, Alief, and East Houston have large immigrant populations
   and larger, multi-generational households -- real demand drivers for
   dry grocery, baby products, and household essentials (Family Dollar's
   core categories) that median-income screening alone doesn't capture.

2. Real 90% confidence intervals (the ACS margin of error, "MOE") for the
   city-wide headline statistics, computed the way the Census Bureau's own
   methodology computes them -- not just point estimates presented as exact.
   For a derived ratio (poverty rate, foreign-born rate, Spanish-at-home
   rate), the MOE is NOT simply the input MOEs -- it's propagated with the
   Census Bureau's published ratio-MOE formula:

     MOE_p = (1/Y) * sqrt(MOE_X^2 - p^2 * MOE_Y^2)      [if radicand >= 0]
     MOE_p = (1/Y) * sqrt(MOE_X^2 + p^2 * MOE_Y^2)      [fallback otherwise]

   where p = X/Y. Source: US Census Bureau, "A Compass for Understanding
   and Using American Community Survey Data," Appendix A.

Output: data/processed/tract_extended_demographics.csv  (per-tract, for map popups)
        data/processed/city_confidence_intervals.csv     (city-wide headline stats + 90% CI)
"""
from __future__ import annotations

import csv
import math
import sys
import time

import requests

from lib import CENSUS_REPORTER, PROCESSED

TABLES = "B01003,B19013,B17001,B05002,C16001,B25010"


def ratio_moe(x: float, moe_x: float, y: float, moe_y: float) -> float:
    if y == 0:
        return 0.0
    p = x / y
    radicand = moe_x**2 - (p**2) * (moe_y**2)
    if radicand < 0:
        radicand = moe_x**2 + (p**2) * (moe_y**2)
    return math.sqrt(radicand) / y


def fetch(geo_ids: str, release: str = "acs2024_5yr") -> dict:
    resp = requests.get(
        f"{CENSUS_REPORTER}".replace("/show/latest", f"/show/{release}"),
        params={"table_ids": TABLES, "geo_ids": geo_ids},
        headers={"User-Agent": "curl/8.7.1"},
        timeout=40,
    )
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    # ---- Part 1: city-wide confidence intervals (real Census place-level geography,
    # not a sum of tracts -- the correct way to get a valid city-wide estimate + MOE) ----
    city = fetch("16000US4835000")
    d = city["data"]["16000US4835000"]
    pop_est, pop_moe = d["B01003"]["estimate"]["B01003001"], d["B01003"]["error"]["B01003001"]
    mhi_est, mhi_moe = d["B19013"]["estimate"]["B19013001"], d["B19013"]["error"]["B19013001"]
    pov_tot_est, pov_tot_moe = d["B17001"]["estimate"]["B17001001"], d["B17001"]["error"]["B17001001"]
    pov_below_est, pov_below_moe = d["B17001"]["estimate"]["B17001002"], d["B17001"]["error"]["B17001002"]
    fb_tot_est, fb_tot_moe = d["B05002"]["estimate"]["B05002001"], d["B05002"]["error"]["B05002001"]
    fb_est, fb_moe = d["B05002"]["estimate"]["B05002013"], d["B05002"]["error"]["B05002013"]
    lang_tot_est, lang_tot_moe = d["C16001"]["estimate"]["C16001001"], d["C16001"]["error"]["C16001001"]
    span_est, span_moe = d["C16001"]["estimate"]["C16001003"], d["C16001"]["error"]["C16001003"]
    hh_est, hh_moe = d["B25010"]["estimate"]["B25010001"], d["B25010"]["error"]["B25010001"]

    poverty_rate = pov_below_est / pov_tot_est
    poverty_rate_moe = ratio_moe(pov_below_est, pov_below_moe, pov_tot_est, pov_tot_moe)
    fb_rate = fb_est / fb_tot_est
    fb_rate_moe = ratio_moe(fb_est, fb_moe, fb_tot_est, fb_tot_moe)
    span_rate = span_est / lang_tot_est
    span_rate_moe = ratio_moe(span_est, span_moe, lang_tot_est, lang_tot_moe)

    ci_rows = [
        {"statistic": "Population", "estimate": f"{pop_est:,.0f}", "moe_90pct": f"±{pop_moe:,.0f}",
         "ci_90pct_low": f"{pop_est - pop_moe:,.0f}", "ci_90pct_high": f"{pop_est + pop_moe:,.0f}", "source": "ACS 2024 5-yr B01003"},
        {"statistic": "Median household income", "estimate": f"${mhi_est:,.0f}", "moe_90pct": f"±${mhi_moe:,.0f}",
         "ci_90pct_low": f"${mhi_est - mhi_moe:,.0f}", "ci_90pct_high": f"${mhi_est + mhi_moe:,.0f}", "source": "ACS 2024 5-yr B19013"},
        {"statistic": "Poverty rate", "estimate": f"{poverty_rate*100:.1f}%", "moe_90pct": f"±{poverty_rate_moe*100:.1f}pp",
         "ci_90pct_low": f"{(poverty_rate-poverty_rate_moe)*100:.1f}%", "ci_90pct_high": f"{(poverty_rate+poverty_rate_moe)*100:.1f}%", "source": "ACS 2024 5-yr B17001 (ratio MOE propagated)"},
        {"statistic": "Foreign-born share", "estimate": f"{fb_rate*100:.1f}%", "moe_90pct": f"±{fb_rate_moe*100:.1f}pp",
         "ci_90pct_low": f"{(fb_rate-fb_rate_moe)*100:.1f}%", "ci_90pct_high": f"{(fb_rate+fb_rate_moe)*100:.1f}%", "source": "ACS 2024 5-yr B05002 (ratio MOE propagated)"},
        {"statistic": "Spanish spoken at home", "estimate": f"{span_rate*100:.1f}%", "moe_90pct": f"±{span_rate_moe*100:.1f}pp",
         "ci_90pct_low": f"{(span_rate-span_rate_moe)*100:.1f}%", "ci_90pct_high": f"{(span_rate+span_rate_moe)*100:.1f}%", "source": "ACS 2024 5-yr C16001, population 5+ (ratio MOE propagated)"},
        {"statistic": "Average household size", "estimate": f"{hh_est:.2f}", "moe_90pct": f"±{hh_moe:.2f}",
         "ci_90pct_low": f"{hh_est - hh_moe:.2f}", "ci_90pct_high": f"{hh_est + hh_moe:.2f}", "source": "ACS 2024 5-yr B25010"},
    ]
    ci_path = PROCESSED / "city_confidence_intervals.csv"
    with open(ci_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(ci_rows[0].keys()))
        writer.writeheader()
        writer.writerows(ci_rows)
    print(f"Wrote city-wide confidence intervals -> {ci_path}", file=sys.stderr)
    for r in ci_rows:
        print(f"  {r['statistic']}: {r['estimate']} (90% CI: {r['ci_90pct_low']} to {r['ci_90pct_high']})", file=sys.stderr)

    # ---- Part 2: per-tract extended demographics for the 643 Houston tracts ----
    with open(PROCESSED / "houston_tracts.csv", encoding="utf-8") as fh:
        tracts = list(csv.DictReader(fh))

    cache_path = PROCESSED / "_extended_demo_cache.csv"
    demo: dict[str, dict] = {}
    if cache_path.exists():
        with open(cache_path, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                demo[row["geoid"]] = row
    else:
        geoids = [t["geoid"] for t in tracts]
        batch_size = 30
        for i in range(0, len(geoids), batch_size):
            batch = geoids[i : i + batch_size]
            ids = ",".join(f"14000US{g}" for g in batch)
            result = fetch(ids)["data"]
            for full_geoid, tables in result.items():
                g = full_geoid.replace("14000US", "")
                try:
                    fb_t = tables["B05002"]["estimate"]["B05002001"]
                    fb = tables["B05002"]["estimate"]["B05002013"]
                    lang_t = tables["C16001"]["estimate"]["C16001001"]
                    span = tables["C16001"]["estimate"]["C16001003"]
                    hh = tables["B25010"]["estimate"]["B25010001"]
                except (KeyError, TypeError):
                    continue
                demo[g] = {
                    "foreign_born_rate": (fb / fb_t) if fb_t else None,
                    "spanish_at_home_rate": (span / lang_t) if lang_t else None,
                    "avg_household_size": hh,
                }
            print(f"  fetched extended demographics {i + len(batch)}/{len(geoids)}", file=sys.stderr)
            time.sleep(0.3)
        with open(cache_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["geoid", "foreign_born_rate", "spanish_at_home_rate", "avg_household_size"])
            writer.writeheader()
            for g, d2 in demo.items():
                writer.writerow({"geoid": g, **d2})

    out_path = PROCESSED / "tract_extended_demographics.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["geoid", "foreign_born_rate", "spanish_at_home_rate", "avg_household_size"])
        writer.writeheader()
        for t in tracts:
            d3 = demo.get(t["geoid"], {})
            writer.writerow({"geoid": t["geoid"], **d3})
    print(f"Wrote {len(tracts)} tract extended demographics -> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
