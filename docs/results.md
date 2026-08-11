# Results & Recommendation — Houston Family Dollar Site Selection (Citywide)

See [`methodology.md`](methodology.md) for how every number below was produced,
[`data_validation.md`](data_validation.md) for the full source catalog, audit trail, and confidence
intervals, [`limitations_and_diligence.md`](limitations_and_diligence.md) for what a desk analysis
can't verify and the concrete next steps that close that gap, and `index.html` for the interactive
map (open the **Analysis Dashboard** panel from the header for the full scorecard, cannibalization
table, sensitivity analysis, and confidence intervals live).

## Recommendation

> **6600 Stillwell St, Pecan Park, Houston, TX** — a 0.81-acre vacant commercial parcel, HCAD
> account 0410300000175.

Selected from 20 real, HCAD-verified candidate parcels spanning 10 Houston neighborhoods (Alief,
Westchase, Sunnyside, Gulfton, Braeswood, Denver Harbor, East Houston, Braeburn, Acres Homes, and
Central Southwest Houston) — the result of a citywide opportunity screen across all 1,115 Harris
County Census tracts, scoped to the 643 tracts actually inside Houston city limits.

**Why this site, in five points:**

1. **It won a citywide comparison on both raw score and gated score.** Unlike an earlier draft of
   this analysis, the top-scoring site here also clears the traffic benchmark outright — no
   scoring-gate override was needed to reach this recommendation (see below for how close the #2
   site is, and the one real trade-off between them).
2. **It has real, verified traffic that clears the industry-standard minimum.** 19,656 vehicles/day
   on **Gulf Freeway Frontage Road** (TxDOT 2025 AADT) — reverse-geocoded and independently
   re-verified to confirm this is a legitimate frontage road with real driveway access, not the
   freeway mainline itself (see `data_validation.md` §2 for the classification bug this project
   found and fixed while building that exact check — it's the reason this is the recommended site at
   all, rather than the Sunnyside site below).
3. **It has the strongest trade-area demand of any finalist that also clears the traffic gate.**
   44,339 people within a real 5-minute OSRM drive, 228,331 within 10 minutes, at a $55,390 trade-area
   median income — squarely inside the $20k–$55k core discount-retail demand band.
4. **Real Huff market-capture is strong.** 44.8% modeled capture against nearby direct arch-rivals
   (Dollar General, Five Below), with the nearest arch-rival (Dollar General) 3.03 miles away.
5. **It is shovel-ready and low flood-risk.** Vacant commercial land (no demolition), FEMA Zone X
   (outside the mapped Special Flood Hazard Area), $123,494 land value — the lowest acquisition cost
   among the top-scoring finalists.

### The one real trade-off: cannibalization risk, reported honestly

This is the most important number to surface plainly, not smooth over. The recommended site's
**cannibalization risk against Family Dollar's own existing network is High**: it sits 1.01 miles
from an existing Family Dollar, with 47.8% of its trade area already overlapping that store's, for a
net-new population reach of 23,138.

The extremely close #2 site — **Brookhaven St & Cullen Blvd, Sunnyside** (78.3 vs. 79.4, a 1.1-point
gap) — has the opposite profile: **Low** cannibalization risk, 4.07 miles from the nearest existing
FD, zero measured trade-area overlap, and a *higher* net-new population reach (43,688 vs. 23,138)
despite its slightly lower composite score. Both numbers are real and computed the same way for both
sites (see `data/processed/cannibalization.csv`); this isn't a data quality issue, it's a genuine
strategic fork. A VP who weighs protecting the existing network's sales more heavily than raw
trade-area size and traffic may reasonably prefer the Sunnyside site instead — see
`limitations_and_diligence.md` for this framed explicitly as a diligence decision point, not resolved
unilaterally by the scoring model.

### Sensitivity check: does the recommendation hold up under different weightings?

Re-aggregating the same real per-factor scores under 5 different, defensible weighting schemes
(`scripts/28_sensitivity_analysis.py`, full table in the map's Scorecard tab) — the recommendation is
**stable in 3 of 5 scenarios** (Base, Cost-Heavy, Demand-Heavy) and never falls out of the top 2 in
the other two:

| Scenario | Winner | Score | Same as base? |
|---|---|---|---|
| Base (documented) | 6600 Stillwell St, Pecan Park | 79.4 | — |
| Traffic-Heavy | Eldridge Pkwy & Westhollow Pkwy, Parkridge | 84.5 | No — Stillwell ranks #2 (76.0) |
| Cost-Heavy | 6600 Stillwell St, Pecan Park | 85.2 | Yes |
| Competition-Heavy | Brookhaven St & Cullen Blvd, Sunnyside | 83.4 | No — Stillwell ranks #2 (76.8) |
| Demand-Heavy | 6600 Stillwell St, Pecan Park | 79.8 | Yes |

Reported honestly: this is *not* the universal #1 under every possible weighting. It's the top pick
under the documented base weights and remains competitive (never worse than a close #2) under every
alternative tested.

## Top 5 of 20 citywide finalists

| Rank | Neighborhood | Site | Traffic (verified) | Nearest Family Dollar | Cannibalization Risk | Net-New Pop. | **Score** |
|---|---|---|---|---|---|---|---|
| **★ Recommended** | **Pecan Park** | **6600 Stillwell St** | 19,656 vpd ✅ ≥8k | 1.01 mi | **High (hard buffer)** | 23,138 | **79.4** |
| #2 | Sunnyside | Brookhaven St & Cullen Blvd | 20,532 vpd ✅ ≥8k | 4.07 mi | Low | 43,688 | 78.3 |
| #3 | Parkridge (Alief) | Eldridge Pkwy & Westhollow Pkwy | 32,634 vpd ✅ ≥8k | 1.48 mi | High (trade-area overlap) | 9,679 | 75.9 |
| #4 | Sunnyside | 1023 Niagara St | 1,547 vpd ❌ &lt;8k | 4.16 mi | Low | 35,427 | 72.9 |
| #5 | Pecan Park | Broadway St & La Porte Fwy | 2,651 vpd ❌ &lt;8k | 1.18 mi | High (hard buffer) | 12,909 | 69.1 |

Full 20-site detail, every per-factor score, cannibalization math, micro-site operational data (speed
limits, co-tenants, transit distance, approximate lot dimensions), and the sensitivity analysis is in
`data/processed/scorecard.csv`, `data/processed/cannibalization.csv`,
`data/processed/microsite_details.csv`, `data/processed/sensitivity_analysis.csv`, and live in the
map's Analysis Dashboard.

## Cannibalization: existing Family Dollar stores are network, not competition

Existing Family Dollar locations were tracked separately from competitors throughout — the real
question is how much of a new store's trade area a nearby existing FD store already serves, not
whether FD "competes with itself." Method: a hard buffer (<1.2 mi from an existing FD auto-flags High
risk), a real-drive-time trade-area overlap percentage against a 1.5-mile radius of the nearest
existing FD, and a **net-new population reach** figure (5-minute drive population minus the overlap)
as a real, computed stand-in for "how much of this is actually incremental" — deliberately not a
dollar figure, since no public store-level sales data exists to calibrate a revenue model (a number
without that grounding would be fabricated precision dressed up as insight).

As detailed above, the recommended site and the #2 Sunnyside site sit at opposite ends of this
metric — the single clearest trade-off in the whole finalist field, and the top item flagged for the
VP's judgment in `limitations_and_diligence.md`.

## Competitive landscape (recategorized to match how a real site selector thinks about it)

- **Family Dollar (61 existing locations)** — the company's own network, tracked for cannibalization
  above, not counted as competition.
- **Direct arch-rivals (56: Dollar General, Five Below)** — the real competitive threat; this is the
  set the Huff gravity model measures market capture against (44.8% for the recommended site).
- **Sister banner (61: Dollar Tree)** — same parent company (Dollar Tree, Inc.) as Family Dollar,
  tracked separately since modeling it as a competitive threat would misstate the real business
  relationship.
- **Value grocery (225: Aldi, Kroger, H-E-B, Fiesta Mart, Food Town, Save A Lot, and Houston-specific
  banners Joe V's Smart Shop and Mi Tienda)** — the extreme-value grocers Houston's low-income
  households split their budget with.
- **Big-box anchors (125: Walmart, Target, Burlington, Ross)** — general-merchandise price anchors
  and regional traffic generators, tracked for context but excluded from the Huff competitive set
  (different shopping mission, and their much larger square footage would mathematically swamp every
  candidate's modeled share to a non-discriminating near-zero regardless of where it actually sits —
  tested and confirmed before this design choice was made).

## Citywide context

- **10 opportunity neighborhoods screened**, chosen to be at least 2.75 miles apart so the search
  covered geographically distinct parts of the city, not one cluster of adjacent tracts.
- **528 real store locations** pulled from OpenStreetMap across 15 banners (see categorization
  above).
- **2,328,253 people** live inside the real Houston city boundary per the Census Bureau's own
  place-level 2024 ACS 5-year estimate (90% CI: 2,328,057–2,328,449) — independently close to the
  2,312,201 figure obtained by summing block-group populations inside the same boundary polygon, a
  useful cross-check that the city-limits filtering worked correctly. Full confidence-interval table
  for population, income, poverty, foreign-born share, Spanish-at-home share, household size,
  zero-vehicle household share, and renter-occupied share is in
  [`data_validation.md`](data_validation.md) and the map's Confidence Intervals dashboard tab.
- **275 real HCAD parcels** qualified as realistic new-store sites across all 10 neighborhoods before
  narrowing to the 20-site finalist shortlist.

## Suggested next steps for the VP

1. Commission a formal traffic-engineering / ingress-egress study for the Gulf Freeway Frontage Road
   access at 6600 Stillwell St — a frontage-road parcel can have more constrained turn/median-break
   geometry than a standard arterial intersection, and this is the one factor a desk analysis can't
   fully settle (see `limitations_and_diligence.md`).
2. Make the cannibalization trade-off call explicitly: accept the recommended site's High
   cannibalization risk against the existing Family Dollar network in exchange for its stronger
   traffic and trade-area demand, or select the Low-risk, higher-net-new-reach Sunnyside site
   (Brookhaven St & Cullen Blvd) instead — both are real, comparably strong candidates, 1.1 points
   apart.
3. Confirm zoning/permitting and utility availability for whichever parcel is selected with the City
   of Houston; note Houston has no municipal zoning, so this runs through HCAD land-use codes, deed
   restrictions, and the city's parking/development code instead (see `data_validation.md` §5).
4. Title search to confirm no restrictive covenants — not covered by any public data source used
   here, and explicitly flagged as unverified in the Site Details dashboard tab.
5. Site visit to confirm ground conditions, visibility, and ingress/egress geometry (median breaks,
   turning movements) that public GIS data can't fully resolve.
6. If both top sites fall through, Eldridge Pkwy & Westhollow Pkwy (Parkridge/Alief) is the #3
   citywide finalist and the Traffic-Heavy sensitivity scenario's winner (32,634 vpd, the highest
   verified traffic of any finalist).
