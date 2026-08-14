# Results & Recommendation - Houston Family Dollar Site Selection (Citywide)

See [`methodology.md`](methodology.md) for how every number below was produced,
[`data_validation.md`](data_validation.md) for the full source catalog, audit trail, and confidence
intervals, [`limitations_and_diligence.md`](limitations_and_diligence.md) for what a desk analysis
can't verify and the concrete next steps that close that gap, and `index.html` for the interactive
map (open the **Analysis Dashboard** panel from the header for the full scorecard, cannibalization
table, sensitivity analysis, and confidence intervals live - and the header's layer control for the
new HUD LIHTC, LEHD daytime-population, USDA food-access, and Overture-competitor layers, all real,
free, and off by default).

**Revision note:** this is the second real-data revision. The first added HPD crime data as a 7th
scoring factor (see `data_validation.md` §2 item 14). This revision adds four more real, free sources
found on a second, deliberately thorough pass checking for anything free this model had missed (§2
items 15-18): HUD LIHTC affordable-housing data, Census LEHD daytime/workplace population, the USDA
food-access ("food desert") share, and an Overture Maps cross-check of the OSM-sourced competitor
data. **The primary recommendation is unchanged** from the crime-data revision, and the sensitivity
check actually got *more* stable (5 of 6 scenarios agree, up from 4 of 6) - but the Overture check
surfaced a real, material correction worth reading below before anything else.

## Recommendation

> **Eldridge Parkway & Westhollow Parkway, Parkridge, Houston, TX** - a 1.0-acre vacant commercial
> parcel, HCAD account 0582970000612.

Selected from 20 real, HCAD-verified candidate parcels spanning 10 Houston neighborhoods. Full
citywide screening methodology (1,115 Harris County tracts scoped to 643 inside Houston city limits,
10 opportunity clusters, 275 qualifying parcels) is unchanged from prior revisions - see
`methodology.md`.

**Why this site, in seven points:**

1. **Highest verified traffic in the entire 20-site field.** 32,634 vehicles/day on Bellaire
   Boulevard (TxDOT 2025 AADT), comfortably above the 8,000 AADT minimum-viable benchmark.
2. **Lowest real crime exposure of any strong finalist.** 2 violent + 4 property real HPD Part I
   incidents within 0.5mi, trailing 12 months - a crime score of 96.6/100.
3. **Strongest Huff market-capture in the field.** 54.6% modeled capture against nearby direct
   arch-rivals.
4. **Real LIHTC affordable-housing proximity.** 3 real HUD LIHTC properties, 442 units, within 1
   mile - a real signal for concentration of Family Dollar's core low-income customer base, new to
   this revision.
5. **Real daytime workplace population.** 11,614 real jobs (Census LEHD) reachable within a 5-minute
   drive - a signal this model had zero visibility into before this revision, since every prior demand
   metric measured only residents, never workers passing through.
6. **Shovel-ready and low flood-risk.** Vacant commercial land, FEMA Zone X, $217,035 land value on a
   full 1.0-acre parcel - cost/feasibility score 93.2/100.
7. **More robust under reweighting than before.** Wins 5 of the 6 sensitivity scenarios tested
   (previously 4 of 6) - see below.

### A real correction the Overture cross-check surfaced, worth reading before anything else

The most consequential finding in this revision isn't about the winning site - it's about the
**previous #2, 6600 Stillwell St (Pecan Park)**. Cross-checking the OSM-sourced competitor data
against Overture Maps found **a real Dollar General ~0.14 miles away and a real Family Dollar ~0.24
miles away that OpenStreetMap had completely missed** (along with a Dollar Tree and a Ross Dress for
Less nearby). The OSM-only data had reported the nearest true competitor at 3.03 miles and the
nearest existing Family Dollar at 1.01 miles - both substantially wrong. With the correction, 6600
Stillwell St's competition score collapses (68.8 -> 1.4) and it falls from #2 to #5 in the ranking.
This is real, verified data, not a modeling choice - and it's exactly the kind of gap this project's
own documented OSM limitation (Ross Dress for Less undercounted citywide) predicted could exist
somewhere in the finalist set. See `data_validation.md` §2 item 18 for the full story, including why
only the nearest-competitor distance was corrected and not the Huff capture model (a disclosed scope
boundary, not an oversight).

**Practical implication for diligence:** if 6600 Stillwell St remains under consideration for any
reason, this correction should be independently re-verified on the ground before proceeding - real
competitor proximity this close would materially change that site's investment case.

### The two real trade-offs at the recommended site: cannibalization overlap and trade-area income

The recommended site's **cannibalization risk against Family Dollar's own existing network is High**:
1.48 miles from an existing FD, 70.6% trade-area overlap, 9,679 net-new population reach - the lowest
among the top finalists. Its trade-area median household income ($61,815) also sits above the
$20k-$55k core discount-retail band.

The #2 site - **Brookhaven St & Cullen Blvd, Sunnyside** (66.7 vs. 77.0) - has the best cannibalization
profile of the top tier (Low risk, 4.07 mi from the nearest existing FD, zero measured overlap, 43,688
net-new population reach) but a far worse real crime reading (60 violent + 68 property incidents
within 0.5mi vs. 2 violent + 4 property at the recommended site).

No finalist wins on every dimension - see the full scorecard below for the complete comparison.

### Sensitivity check: does the recommendation hold up under different weightings?

Re-aggregating the same real per-factor scores under 6 different, defensible weighting schemes
(`pipeline/stages/s28_sensitivity_analysis.py`, full table in the map's Scorecard tab) - the
recommendation is now **stable in 5 of 6 scenarios**, up from 4 of 6 in the prior revision. Notably,
it now also wins the **Demand-Heavy** scenario, which it lost before this revision's blended demand
composite (residential population + real LIHTC density + real daytime workplace population + real
food-access share) gave it credit for signals the old residential-only demand metric couldn't see:

| Scenario | Winner | Score | Same as base? |
| --- | --- | --- | --- |
| Base (documented) | Eldridge Pkwy & Westhollow Pkwy, Parkridge | 77.0 | - |
| Traffic-Heavy | Eldridge Pkwy & Westhollow Pkwy, Parkridge | 85.2 | Yes |
| Cost-Heavy | Eldridge Pkwy & Westhollow Pkwy, Parkridge | 81.2 | Yes |
| Competition-Heavy | Brookhaven St & Cullen Blvd, Sunnyside | 73.5 | No - 1023 Niagara St has the raw top score (74.6) but fails the AADT gate |
| Demand-Heavy | Eldridge Pkwy & Westhollow Pkwy, Parkridge | 69.4 | **Yes (new - previously lost this scenario)** |
| Crime-Heavy | Eldridge Pkwy & Westhollow Pkwy, Parkridge | 82.7 | Yes |

Reported honestly: it still loses the Competition-Heavy scenario, where raw distance-to-nearest-rival
dominates and the Sunnyside site's much larger competitive buffer wins outright.

## Top 5 of 20 citywide finalists

| Rank | Neighborhood | Site | Traffic (verified) | Crime (0.5mi, 12mo) | LIHTC units (1mi) | Daytime jobs (5min) | **Score** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **★ Recommended** | **Parkridge** | **Eldridge Pkwy & Westhollow Pkwy** | 32,634 vpd ✅ | 2 violent / 4 property | 442 | 11,614 | **77.0** |
| #2 | Sunnyside | Brookhaven St & Cullen Blvd | 20,532 vpd ✅ | 60 violent / 68 property | 221 | 10,041 | 66.7 |
| #3 | Sunnyside | 1023 Niagara St | 1,547 vpd ❌ | 57 violent / 63 property | 221 | 6,524 | 66.1 |
| #4 | Pecan Park | Broadway St & La Porte Fwy | 2,651 vpd ❌ | 13 violent / 31 property | 0 | 6,334 | 64.6 |
| #5 | Pecan Park | 6600 Stillwell St | 19,656 vpd ✅ | 24 violent / 62 property | 152 | 16,560 | 62.8 |

Full 20-site detail, every per-factor and per-sub-factor score, cannibalization math, real crime and
food-access data, and the sensitivity analysis is in `data/processed/scorecard.csv` and the map's
Analysis Dashboard.

## The four new real, free signals added this revision

- **HUD LIHTC affordable-housing properties** (`data/processed/site_lihtc.csv`,
  `lihtc_properties_detail.csv`) - real, geocoded, point-level federal database, queried within 1 mile
  of each finalist. Folded into the demand composite at 15% sub-weight (proxy for concentration of
  Family Dollar's core low-income customer base).
- **Census LEHD daytime/workplace population** (`site_daytime_population.csv`,
  `blockgroup_daytime_population.csv`) - real block-level job counts summed within each site's actual
  5-minute OSRM drive-time trade area (reusing already-cached routing, no new API calls). Folded into
  the demand composite at 15% sub-weight - a real signal this model had zero visibility into before.
- **USDA food-access share** (`site_food_access.csv`) - real, continuous "% of tract population beyond
  0.5mi from a SNAP-authorized food retailer," from the USDA's own Food Access Research Atlas. Folded
  into the demand composite at 10% sub-weight - directly on-topic for a dollar-store expansion thesis.
- **Overture Maps competitor cross-check** (`site_overture_supplement.csv`,
  `overture_new_competitors_detail.csv`) - found 54 real competitor locations across the 20 finalists
  that the OSM-sourced pull missed, corrected 8 of the 20 sites' nearest-competitor distance, and
  surfaced the material Stillwell correction above.

All four are also real, off-by-default layers on the interactive map (header layer control) so a
reviewer can inspect the raw points/polygons behind each signal, not just the aggregate score.

## Cannibalization: existing Family Dollar stores are network, not competition

Method unchanged from prior revisions (hard/soft distance buffers + real drive-time trade-area
overlap + net-new population reach) - see `methodology.md` Stage 5b. Full 20-site table in
`data/processed/cannibalization.csv` and the map's Cannibalization tab.

## Citywide context

- **10 opportunity neighborhoods screened**, **528 real OSM store locations** across 15 banners (plus
  54 additional real Overture-sourced finds not in OSM), **275 real HCAD parcels** qualified before
  narrowing to 20 finalists.
- **2,328,253 people** live inside the real Houston city boundary (Census ACS 2024 5-yr, 90% CI:
  2,328,057-2,328,449) - see `data_validation.md` §4 for the full confidence-interval table.
- **47,283 real HPD Part I crime incidents** loaded for the crime-risk screen.
- **18,459 Texas block groups' worth of real LEHD job data** loaded for the daytime-population signal.
- **6,884 Texas census tracts' worth of real USDA food-access data** loaded for the food-access signal.

## Suggested next steps for the VP

1. **Independently re-verify the Stillwell competitor correction on the ground** before that site is
   considered further for any reason (see above) - a real, material finding, not a modeling artifact.
2. **Make the trade-off call explicitly** between the recommended site's traffic/crime/demand strength
   and its cannibalization/income-band trade-offs versus the #2 Sunnyside site's cannibalization
   profile - see `limitations_and_diligence.md`.
3. Commission a formal traffic-engineering / ingress-egress study for the recommended site's
   Eldridge Parkway & Westhollow Parkway intersection.
4. Confirm zoning/permitting and utility availability with the City of Houston (no municipal zoning -
   see `data_validation.md` §5).
5. Title search to confirm no restrictive covenants - not covered by any public data source used here.
6. Site visit to confirm ground conditions, visibility, and ingress/egress geometry.
7. If the top sites fall through, 6600 Stillwell St's real corrected numbers (above) should factor
   heavily into whether it's still a viable fallback.
