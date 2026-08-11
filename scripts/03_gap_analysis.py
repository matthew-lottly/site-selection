"""Step 3: Macro market screen. Score every Harris County tract on a
transparent demand-vs-supply "gap index" and surface the strongest
underserved cluster as the target submarket for site-level analysis.

Demand side (ACS 5-year, Census Reporter):
  - population
  - median household income, weighted toward the discount-retail core
    demographic band ($20k-$55k; dollar-store trade areas skew here)
  - poverty rate (higher poverty -> higher reliance on discount retail)

Supply side (OpenStreetMap, current):
  - straight-line distance from the tract centroid to the nearest existing
    small-box dollar-format store of ANY banner (Family Dollar, Dollar
    General, Dollar Tree) -- for this macro screen we care about overall
    dollar-format retail saturation, not yet which banner. The Family
    Dollar-specific cannibalization question is handled separately and more
    precisely at the site level in script 24.

Output: data/processed/tract_scores.csv (sorted, highest opportunity first)
"""
from __future__ import annotations

import csv
import sys

from lib import PROCESSED, haversine_miles

DOLLAR_FORMAT_CATEGORIES = {"family_dollar", "arch_rival", "sister_banner"}


def income_fit(mhi: float | None) -> float:
    if mhi is None:
        return 0.0
    if 20_000 <= mhi <= 55_000:
        return 1.0
    if mhi < 20_000:
        return max(0.0, mhi / 20_000)  # very low income = less stable trade area
    if mhi <= 80_000:
        return max(0.0, 1 - (mhi - 55_000) / 25_000)
    return 0.0


def main() -> None:
    with open(PROCESSED / "tracts.csv", encoding="utf-8") as fh:
        tracts = list(csv.DictReader(fh))

    with open(PROCESSED / "competitors.csv", encoding="utf-8") as fh:
        stores = list(csv.DictReader(fh))
    dollar_stores = [s for s in stores if s["category"] in DOLLAR_FORMAT_CATEGORIES]

    rows = []
    for t in tracts:
        lat, lon = float(t["lat"]), float(t["lon"])
        pop = float(t["population"] or 0)
        mhi = float(t["median_hh_income"]) if t["median_hh_income"] not in ("", "None", None) else None
        poverty_rate = float(t["poverty_rate"]) if t["poverty_rate"] not in ("", "None", None) else 0.0

        if not dollar_stores:
            nearest_dollar_mi = 99.0
        else:
            nearest_dollar_mi = min(haversine_miles(lat, lon, float(s["lat"]), float(s["lon"])) for s in dollar_stores)

        demand_index = pop * income_fit(mhi) * (1 + poverty_rate)
        competitive_gap_index = min(nearest_dollar_mi, 3.0) / 3.0
        gap_score = demand_index * competitive_gap_index

        rows.append(
            {
                **t,
                "population": pop,
                "median_hh_income": mhi,
                "poverty_rate": poverty_rate,
                "nearest_dollar_store_mi": round(nearest_dollar_mi, 2),
                "demand_index": round(demand_index, 1),
                "competitive_gap_index": round(competitive_gap_index, 3),
                "gap_score": round(gap_score, 1),
            }
        )

    rows.sort(key=lambda r: r["gap_score"], reverse=True)

    out_path = PROCESSED / "tract_scores.csv"
    fieldnames = [
        "geoid", "name", "lat", "lon", "aland_sqmi", "population", "median_hh_income",
        "poverty_rate", "nearest_dollar_store_mi",
        "demand_index", "competitive_gap_index", "gap_score",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r[k] for k in fieldnames})

    print(f"Wrote {len(rows)} scored tracts to {out_path}", file=sys.stderr)
    print("\nTop 30 opportunity tracts:", file=sys.stderr)
    print(f"{'GEOID':<13}{'Name':<28}{'Pop':>7}{'MHI':>9}{'Pov%':>7}{'NearFD(mi)':>11}{'GapScore':>10}", file=sys.stderr)
    for r in rows[:30]:
        mhi_s = f"{r['median_hh_income']:.0f}" if r["median_hh_income"] else "n/a"
        print(
            f"{r['geoid']:<13}{r['name'][:27]:<28}{r['population']:>7.0f}{mhi_s:>9}"
            f"{r['poverty_rate']*100:>6.1f}%{r['nearest_dollar_store_mi']:>11.2f}{r['gap_score']:>10.0f}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
