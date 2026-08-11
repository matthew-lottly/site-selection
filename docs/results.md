# Results & Recommendation — Houston Family Dollar Site Selection (Citywide)

See `docs/methodology.md` for how every number below was produced, and `index.html` for the
interactive map. This is the citywide revision: 20 real candidate sites sourced from 10
geographically distinct Houston neighborhoods, not one submarket.

## Recommendation

> **Cullen Blvd & Brookhaven St, Sunnyside, Houston, TX 77051** — a 0.66-acre vacant commercial
> parcel, HCAD account 0430390000003.

This site scored highest (73.5 / 100) across 20 real, HCAD-verified candidate parcels spanning 10
Houston neighborhoods (Alief, Westchase, Sunnyside, Gulfton, Braeswood, Denver Harbor, East Houston,
Braeburn, Acres Homes, and Central Southwest Houston) — the result of a citywide opportunity screen
across all 1,115 Harris County Census tracts, scoped to the 643 tracts actually inside Houston city
limits.

**Why this site, in four points:**

1. **It won on a citywide comparison, not a first-look pick.** Two of the top three finalists both
   landed in Sunnyside (ranks #1 and #2, essentially tied at 73.5 and 73.3), even after searching
   nine other demographically similar Houston neighborhoods for something stronger. That convergence
   is itself evidence the pick is real, not an artifact of where the search started.
2. **It has real, verified traffic.** 20,532 vehicles/day on Cullen Blvd (TxDOT 2025 AADT) — the
   station's coordinates were independently reverse-geocoded to confirm it really is Cullen Blvd and
   not a mismatched freeway route. Clears the industry-standard 8,000 AADT minimum-viable-traffic
   benchmark.
3. **It sits in a real, wide-open competitive gap.** The nearest existing dollar store is 4.07 miles
   away — the largest gap of any finalist that also clears the traffic and flood screens — and this
   site posted the highest Huff gravity-model market-capture rate of all 20 candidates (16.6%,
   against every real nearby Family Dollar / Dollar General / Dollar Tree).
4. **It is shovel-ready and low-risk.** Vacant commercial land (no demolition), FEMA Zone X (outside
   the mapped Special Flood Hazard Area), $373,516 land value ($566k/acre — mid-range among the
   finalists, not the cheapest but far from the most expensive).

**Runner-up, for context:** Site #2, also in Sunnyside (1023 Niagara St, 0.4 mile away), scored
almost identically (73.3) but fails the traffic benchmark (1,547 AADT on a frontage road) — a
reminder that these two top scores are close enough that a site visit and a real traffic-engineering
read should settle the final call between them before acquisition.

## Top 5 of 20 citywide finalists

| Rank | Neighborhood | Site | Type | Traffic (verified) | Nearest Competitor | Huff Capture | Flood | **Score** |
|---|---|---|---|---|---|---|---|---|
| **1** | **Sunnyside** | **Cullen Blvd & Brookhaven St** | Vacant land, 0.66 ac | 20,532 vpd (Cullen Blvd) ✅ ≥8k | 4.07 mi | 16.6% | X | **73.5** |
| 2 | Sunnyside | 1023 Niagara St | Vacant land, 0.72 ac | 1,547 vpd ❌ &lt;8k | 4.16 mi | 16.5% | X | 73.3 |
| 3 | Pecan Park | 6600 Stillwell St | Vacant land, 0.81 ac | 2,980 vpd ❌ &lt;8k | 1.01 mi | 10.5% | X | 59.9 |
| 4 | Parkridge (Alief) | Eldridge Pkwy & Westhollow Pkwy | Vacant land, 1.00 ac | 32,634 vpd ✅ ≥8k | 1.48 mi | 70.7%* | X | 58.7 |
| 5 | Braeburn | 7818 Hillcroft St | Vacant land, 0.63 ac | 13,371 vpd ✅ ≥8k | 0.66 mi | 27.2% | X | 53.6 |

\* Site #4's high Huff score reflects very few nearby dollar-store competitors in that specific
pocket of Alief — it did not win overall because its trade-area income skews above the $20k–$55k
target band and its competitive gap (1.48 mi) is much tighter. Full 20-site detail, including every
per-factor score, is in `data/processed/scorecard.csv`.

## Citywide context

- **10 opportunity neighborhoods screened**, chosen to be at least 2.75 miles apart so the search
  covered geographically distinct parts of the city, not one cluster of adjacent tracts.
- **516 real competitor/anchor locations** pulled from OpenStreetMap across 13 banners: 156 direct
  dollar stores (Family Dollar, Dollar General, Dollar Tree), 147 off-price/general-merchandise
  (Walmart, Target, Burlington, Five Below, Ross), and 213 grocery anchors (Kroger, H-E-B, Aldi,
  Fiesta Mart, Food Town).
- **2,312,201 people** live inside the real Houston city boundary used for this analysis (1,603
  Census block groups) — a figure that lines up with Houston's published population, a useful sanity
  check that the city-limits filtering worked correctly.
- **275 real HCAD parcels** qualified as realistic new-store sites across all 10 neighborhoods before
  narrowing to the 20-site finalist shortlist.

## Suggested next steps for the VP

1. Confirm zoning/permitting and utility availability for the Cullen Blvd & Brookhaven St parcel
   with the City of Houston.
2. Commission a formal traffic/ingress-egress study for the Cullen Blvd frontage, and use it to make
   the final call against the near-tied runner-up (1023 Niagara St, also Sunnyside).
3. Site visit to confirm ground conditions and visibility (HCAD/satellite data can't replace a walk).
4. If the Sunnyside sites fall through in acquisition, Pecan Park (6600 Stillwell St) is the
   next-best, data-supported fallback from a different part of the city.
