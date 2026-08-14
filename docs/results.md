# Results & Recommendation - Houston Family Dollar Site Selection (Citywide)

See [`methodology.md`](methodology.md) for how every number below was produced,
[`data_validation.md`](data_validation.md) for the full source catalog, audit trail, and confidence
intervals, [`limitations_and_diligence.md`](limitations_and_diligence.md) for what a desk analysis
can't verify and the concrete next steps that close that gap, and `index.html` for the interactive
map (open the **Analysis Dashboard** panel from the header for the full scorecard, cannibalization
table, sensitivity analysis, and confidence intervals live).

**Revision note:** this recommendation reflects the addition of a real crime-risk factor (real HPD
NIBRS Part I violent/property incident data, added as a 7th scoring input - see §"Crime risk" below
and `data_validation.md` §2 item 14). Adding it changed the primary recommendation from the previous
revision (6600 Stillwell St, Pecan Park, which had a materially higher real crime reading nearby) to
the site below. Both sites remain real, strong, HCAD-verified candidates; the full comparison is in
the scorecard table further down.

## Recommendation

> **Eldridge Parkway & Westhollow Parkway, Parkridge, Houston, TX** - a 1.0-acre vacant commercial
> parcel, HCAD account 0582970000612.

Selected from 20 real, HCAD-verified candidate parcels spanning 10 Houston neighborhoods (Alief,
Westchase, Sunnyside, Gulfton, Braeswood, Denver Harbor, East Houston, Braeburn, Acres Homes, and
Central Southwest Houston) - the result of a citywide opportunity screen across all 1,115 Harris
County Census tracts, scoped to the 643 tracts actually inside Houston city limits.

**Why this site, in six points:**

1. **It clears the traffic benchmark with the highest verified reading of any finalist.** 32,634
   vehicles/day on **Bellaire Boulevard** (TxDOT 2025 AADT, reverse-geocoded and verified as a real
   arterial reading, not a freeway mainline) - comfortably above the 8,000 AADT industry minimum and
   the strongest traffic exposure in the entire 20-site field.
2. **It has the lowest real crime exposure of any strong finalist.** Just 2 violent and 4 property
   Part I incidents (real HPD NIBRS data) within 0.5 miles over the trailing 12 months - a crime
   score of 96.6/100, versus 41.8 for the previous recommendation (6600 Stillwell St, 24 violent + 62
   property incidents nearby) and 13.0 for the close Sunnyside finalist (60 violent + 68 property).
3. **Real Huff market-capture is the strongest in the field.** 54.6% modeled capture against nearby
   direct arch-rivals (Dollar General, Five Below).
4. **It is shovel-ready, low-cost, and low flood-risk.** Vacant commercial land (no demolition), FEMA
   Zone X (outside the mapped Special Flood Hazard Area), $217,035 land value on a full 1.0-acre
   parcel - a cost/feasibility score of 93.2/100.
5. **Trade-area demand is real but more modest than the #2 site.** 32,879 people within a real
   5-minute OSRM drive, 224,098 within 10 minutes, at a $61,815 trade-area median income - above the
   $20k-$55k core band, which is why its demand score (48.0/100) is the one factor that doesn't lead
   the field (see the trade-off below).
6. **It won under 4 of the 6 weighting scenarios tested**, including a dedicated Crime-Heavy scenario
   built specifically to stress-test how much the recommendation depends on the new crime factor (see
   the sensitivity section below).

### The two real trade-offs: cannibalization overlap and trade-area demand, reported honestly

This is the most important set of numbers to surface plainly, not smooth over. The recommended
site's **cannibalization risk against Family Dollar's own existing network is High**: it sits 1.48
miles from an existing Family Dollar, with 70.6% of its trade area already overlapping that store's,
for a net-new population reach of 9,679 - the lowest net-new reach among the top 5 finalists. Its
trade-area median household income ($61,815) also sits above Family Dollar's core $20k-$55k
discount-retail demand band, unlike the #2 and #3 sites below.

The very close #2 site - **6600 Stillwell St, Pecan Park** (76.1 vs. 78.5, a 2.4-point gap, and the
previous revision's recommendation) - has a stronger demand profile (44,339 five-minute-drive
population inside the core income band) but a materially worse real crime reading (86 total Part I
incidents within 0.5mi vs. 6) and the same High cannibalization risk via a hard 1.01-mile buffer to
an existing FD.

The #3 site - **Brookhaven St & Cullen Blvd, Sunnyside** (71.8) - has the best cannibalization profile
of the top 3 (Low risk, 4.07 mi from the nearest existing FD, zero measured overlap, 43,688 net-new
population reach, the highest of any finalist) but by far the worst real crime reading in the top
tier (128 total Part I incidents within 0.5mi, a crime score of 13.0/100).

None of the top 3 finalists wins on every dimension. All three numbers (crime, cannibalization,
demand) are real and computed the same way for every site (see `data/processed/scorecard.csv`,
`data/processed/site_crime_risk.csv`, and `data/processed/cannibalization.csv`); this isn't a data
quality issue, it's a genuine three-way strategic trade-off for the VP to weigh explicitly - see
`limitations_and_diligence.md`.

### Sensitivity check: does the recommendation hold up under different weightings?

Re-aggregating the same real per-factor scores under 6 different, defensible weighting schemes
(`pipeline/stages/s28_sensitivity_analysis.py`, full table in the map's Scorecard tab, including a
dedicated **Crime-Heavy** scenario built specifically to test how load-bearing the new crime factor
is) - the recommendation is **stable in 4 of 6 scenarios** (Base, Traffic-Heavy, Cost-Heavy,
Crime-Heavy) and never falls outside the top 3 in the other two:

| Scenario | Winner | Score | Same as base? |
| --- | --- | --- | --- |
| Base (documented) | Eldridge Pkwy & Westhollow Pkwy, Parkridge | 78.5 | - |
| Traffic-Heavy | Eldridge Pkwy & Westhollow Pkwy, Parkridge | 86.1 | Yes |
| Cost-Heavy | Eldridge Pkwy & Westhollow Pkwy, Parkridge | 82.4 | Yes |
| Competition-Heavy | Brookhaven St & Cullen Blvd, Sunnyside | 76.5 | No - Eldridge/Westhollow raw top score (77.2 at Broadway/La Porte) |
| Demand-Heavy | 7818 Hillcroft St, Braeburn | 76.3 | No - a lower-crime, high-demand site wins instead |
| Crime-Heavy | Eldridge Pkwy & Westhollow Pkwy, Parkridge | 83.8 | Yes |

Reported honestly: this is *not* the universal #1 under every possible weighting, including under a
Demand-Heavy scenario where raw trade-area population dominates. It is the top pick under the
documented base weights, wins decisively when crime is weighted even more heavily (Crime-Heavy
scenario, 83.8), and remains competitive under every alternative tested.

## Top 5 of 20 citywide finalists

| Rank | Neighborhood | Site | Traffic (verified) | Crime (0.5mi, 12mo) | Nearest Family Dollar | Cannibalization Risk | Net-New Pop. | **Score** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **★ Recommended** | **Parkridge** | **Eldridge Pkwy & Westhollow Pkwy** | 32,634 vpd ✅ ≥8k | 2 violent / 4 property | 1.48 mi | High (trade-area overlap) | 9,679 | **78.5** |
| #2 | Pecan Park | 6600 Stillwell St | 19,656 vpd ✅ ≥8k | 24 violent / 62 property | 1.01 mi | High (hard buffer) | 23,138 | 76.1 |
| #3 | Sunnyside | Brookhaven St & Cullen Blvd | 20,532 vpd ✅ ≥8k | 60 violent / 68 property | 4.07 mi | Low | 43,688 | 71.8 |
| #4 | Pecan Park | Broadway St & La Porte Fwy | 2,651 vpd ❌ &lt;8k | 13 violent / 31 property | 1.18 mi | High (hard buffer) | 12,909 | 69.7 |
| #5 | Central Southwest Houston | 4620 Fuqua St | 27,301 vpd ✅ ≥8k | 7 violent / 31 property | 1.49 mi | High (trade-area overlap) | 11,514 | 68.9 |

Full 20-site detail, every per-factor score, cannibalization math, real crime-incident counts,
micro-site operational data (speed limits, co-tenants, transit distance, approximate lot dimensions),
and the sensitivity analysis is in `data/processed/scorecard.csv`, `data/processed/site_crime_risk.csv`,
`data/processed/cannibalization.csv`, `data/processed/microsite_details.csv`,
`data/processed/sensitivity_analysis.csv`, and live in the map's Analysis Dashboard.

## Crime risk: a real 7th scoring factor

Real Houston Police Department NIBRS Part I violent (murder, rape, robbery, aggravated assault) and
property (burglary, larceny-theft, motor vehicle theft) incident counts within 0.5 miles of each
site, trailing 12 months (Aug 2025-Jul 2026), pulled directly from HPD's own public CSV exports - not
Houston's CKAN open-data catalog, which was checked in an earlier revision and genuinely has no
queryable crime dataset (see `data_validation.md` §2 items 11 and 14 for the full story of what was
missed the first time and how it was found). Weighted at 10%, the same weight as flood risk, since
both are real-world risk-mitigation factors that penalize a worse reading rather than reward a
better one. The spread across the 20 finalists is large and real: from 1 total incident (Site 20,
Inwood) to 147 (Site 8, Fondren Gardens) - see `data/processed/site_crime_risk.csv` for every site.

## Cannibalization: existing Family Dollar stores are network, not competition

Existing Family Dollar locations were tracked separately from competitors throughout - the real
question is how much of a new store's trade area a nearby existing FD store already serves, not
whether FD "competes with itself." Method: a hard buffer (<1.2 mi from an existing FD auto-flags High
risk), a real-drive-time trade-area overlap percentage against a 1.5-mile radius of the nearest
existing FD, and a **net-new population reach** figure (5-minute drive population minus the overlap)
as a real, computed stand-in for "how much of this is actually incremental" - deliberately not a
dollar figure, since no public store-level sales data exists to calibrate a revenue model (a number
without that grounding would be fabricated precision dressed up as insight).

As detailed above, all three top finalists carry real cannibalization exposure of some kind - the
clearest three-way trade-off in the whole finalist field, and the top item flagged for the VP's
judgment in `limitations_and_diligence.md`.

## Competitive landscape (recategorized to match how a real site selector thinks about it)

- **Family Dollar (61 existing locations)** - the company's own network, tracked for cannibalization
  above, not counted as competition.
- **Direct arch-rivals (56: Dollar General, Five Below)** - the real competitive threat; this is the
  set the Huff gravity model measures market capture against (54.6% for the recommended site).
- **Sister banner (61: Dollar Tree)** - same parent company (Dollar Tree, Inc.) as Family Dollar,
  tracked separately since modeling it as a competitive threat would misstate the real business
  relationship.
- **Value grocery (225: Aldi, Kroger, H-E-B, Fiesta Mart, Food Town, Save A Lot, and Houston-specific
  banners Joe V's Smart Shop and Mi Tienda)** - the extreme-value grocers Houston's low-income
  households split their budget with.
- **Big-box anchors (125: Walmart, Target, Burlington, Ross)** - general-merchandise price anchors
  and regional traffic generators, tracked for context but excluded from the Huff competitive set
  (different shopping mission, and their much larger square footage would mathematically swamp every
  candidate's modeled share to a non-discriminating near-zero regardless of where it actually sits -
  tested and confirmed before this design choice was made).

## Citywide context

- **10 opportunity neighborhoods screened**, chosen to be at least 2.75 miles apart so the search
  covered geographically distinct parts of the city, not one cluster of adjacent tracts.
- **528 real store locations** pulled from OpenStreetMap across 15 banners (see categorization
  above).
- **2,328,253 people** live inside the real Houston city boundary per the Census Bureau's own
  place-level 2024 ACS 5-year estimate (90% CI: 2,328,057-2,328,449) - independently close to the
  2,312,201 figure obtained by summing block-group populations inside the same boundary polygon, a
  useful cross-check that the city-limits filtering worked correctly. Full confidence-interval table
  for population, income, poverty, foreign-born share, Spanish-at-home share, household size,
  zero-vehicle household share, and renter-occupied share is in
  [`data_validation.md`](data_validation.md) and the map's Confidence Intervals dashboard tab.
- **275 real HCAD parcels** qualified as realistic new-store sites across all 10 neighborhoods before
  narrowing to the 20-site finalist shortlist.
- **47,283 real HPD Part I crime incidents** (violent + property, citywide) loaded for the trailing
  12-month crime-risk screen.

## Suggested next steps for the VP

1. **Make the three-way trade-off call explicitly.** No single finalist wins on crime, demand, and
   cannibalization simultaneously - decide which of the top 3 real, comparably strong candidates
   (lowest crime / highest traffic at Parkridge; strongest core-income-band demand at Pecan Park;
   lowest cannibalization risk at Sunnyside) best fits the portfolio's current risk tolerance. See
   `limitations_and_diligence.md` for this framed explicitly as a diligence decision point, not
   resolved unilaterally by the scoring model.
2. Commission a formal traffic-engineering / ingress-egress study for whichever site is selected -
   a desk analysis can verify real AADT and road identity but not driveway permit feasibility or
   median-break geometry (see `limitations_and_diligence.md`).
3. Confirm zoning/permitting and utility availability with the City of Houston; note Houston has no
   municipal zoning, so this runs through HCAD land-use codes, deed restrictions, and the city's
   parking/development code instead (see `data_validation.md` §5).
4. Title search to confirm no restrictive covenants - not covered by any public data source used
   here, and explicitly flagged as unverified in the Site Details dashboard tab.
5. Site visit to confirm ground conditions, visibility, and ingress/egress geometry (median breaks,
   turning movements) that public GIS data can't fully resolve.
6. If the top sites fall through, 4620 Fuqua St (Central Southwest Houston) is the #5 citywide
   finalist with a strong crime score (74.7) and the second-highest verified traffic reading (27,301
   vpd) among AADT-qualified sites.
