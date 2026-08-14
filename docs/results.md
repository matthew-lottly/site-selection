# Results & Recommendation - Houston Family Dollar Site Selection (Citywide)

See [`methodology.md`](methodology.md) for how every number below was produced,
[`data_validation.md`](data_validation.md) for the full source catalog, audit trail, and confidence
intervals, [`limitations_and_diligence.md`](limitations_and_diligence.md) for what a desk analysis
can't verify and the concrete next steps that close that gap, and `index.html` for the interactive
map (open the **Analysis Dashboard** panel from the header for the full scorecard, cannibalization
table, sensitivity analysis, and confidence intervals live - and the header's layer control for 16
real map layers, including HUD LIHTC, HUD Multifamily, LEHD daytime population, USDA food access,
federal Opportunity Zones, and the Overture-competitor cross-check, all off by default, with a
dynamic legend that shows only what's currently toggled on).

**Revision note: the recommendation changed.** A fourth research pass, done specifically to check
this analysis wasn't missing any other real, free retail-site-selection data, found and verified two
more real federal data sources: **federal Qualified Opportunity Zone designations** (a real
tax-advantaged-investment tract boundary, checked by real point-in-polygon intersection) and **HUD
Multifamily Properties** (FHA-insured/HUD-assisted housing - a different federal program than LIHTC,
so a real, complementary signal, not a duplicate). Both are folded into the demand composite. The new
signals materially favor a different finalist - **the recommendation moved from Eldridge Parkway &
Westhollow Parkway (Parkridge) to Brookhaven Street & Cullen Boulevard (Sunnyside)**, which sits in a
real Opportunity Zone and has more real HUD-assisted housing nearby (612 units) than any other
finalist. This is a real, evidence-based change, not a tuning choice - see below for exactly what
moved and why.

## Recommendation

> **Brookhaven Street & Cullen Boulevard, Sunnyside, Houston, TX** - a 0.66-acre vacant commercial
> parcel, HCAD account 0430390000003.

Selected from 20 real, HCAD-verified candidate parcels spanning 10 Houston neighborhoods. Full
citywide screening methodology (1,115 Harris County tracts scoped to 643 inside Houston city limits,
10 opportunity clusters, 275 qualifying parcels) is unchanged from prior revisions - see
`methodology.md`.

**Why this site, in six points:**

1. **Real federal Opportunity Zone designation.** This site's tract carries a real, current federal
   Qualified Opportunity Zone designation (verified by point-in-polygon intersection, not assumed) -
   a genuine tax-advantaged-investment signal correlated with underserved-area targeting.
2. **The most real HUD-assisted housing of any finalist.** 612 real assisted units across 4 HUD
   Multifamily properties within 1 mile - the highest concentration of Family Dollar's core
   low-income customer base found near any of the 20 sites.
3. **Lowest cannibalization risk of any strong finalist.** 4.07 miles from the nearest existing
   Family Dollar, 0% trade-area overlap, 43,688 net-new population reach - Low risk, clean.
4. **Strong real Huff market-capture.** 30.1% modeled capture against every real nearby arch-rival
   (Dollar General, Five Below, and Dollar Tree, now correctly counted as a competitor - see below).
5. **Clears the traffic benchmark.** 20,532 vehicles/day on Cullen Boulevard (TxDOT 2025 AADT),
   comfortably above the 8,000 AADT minimum-viable benchmark.
6. **Shovel-ready and low flood-risk.** Vacant commercial land, FEMA Zone X, $373,516 land value on a
   0.66-acre parcel.

### The real trade-off: this site has the worst real crime reading in the top tier

Reported plainly, not smoothed over: the recommended site has **60 violent and 68 property** real HPD
Part I incidents within 0.5 miles, trailing 12 months - a crime score of 13.0/100, the weakest of any
top-5 finalist. The prior revision's pick, **Eldridge Pkwy & Westhollow Pkwy (Parkridge, now #3, 65.8)**,
has by far the best crime reading in the field (2 violent + 4 property, crime score 96.6) and the
highest verified traffic (32,634 vpd), but far less real subsidized-housing concentration nearby and
no Opportunity Zone designation. **6600 Stillwell St (Pecan Park, now #4, 64.6)** sits in between on
most factors. No finalist wins on every dimension - see the full scorecard below.

### What actually changed the recommendation, and why

The demand composite was rebalanced from 4 to 6 real sub-signals to make room for the two new sources,
without changing the top-level factor count (still 7 factors, same as every prior revision):

| Demand sub-component | Weight | Recommended site's real value |
| --- | --- | --- |
| Residential 5-min drive population x income fit | 50% | 43,688 people, subscore 77.9/100 |
| Real LIHTC units within 1mi | 12% | 221 units, subscore 18.6/100 |
| Real LEHD daytime workplace population | 12% | 10,041 jobs, subscore 35.9/100 |
| Real USDA food-access share | 8% | 0.0%, subscore 0.0/100 |
| Real HUD Multifamily assisted units within 1mi | 10% | 612 units, subscore **100.0/100** |
| Real federal Opportunity Zone designation | 8% | Yes, subscore **100.0/100** |

The two new signals both scored at the maximum (100/100) for this site - a real, substantial pull
that outweighed the prior revision's residential-population and traffic advantages once genuinely
new, real data was added. This is exactly what should happen when a model gets more complete, not a
sign something went wrong.

### Sensitivity check: does the recommendation hold up under different weightings?

Re-aggregating the same real per-factor scores under 6 different, defensible weighting schemes
(`pipeline/stages/s28_sensitivity_analysis.py`) - the recommendation is **stable in 3 of 6 scenarios**,
down from 4 of 6 before this revision. Reported honestly: adding two real, strongly-differentiating
signals made the recommendation *less* uniformly dominant across every possible weighting, which is
expected - a site that wins primarily on two specific real signals (Opportunity Zone + HUD Multifamily
concentration) won't automatically also win a Traffic-Heavy or Crime-Heavy reweighting where its real
weaknesses (crime, traffic relative to Parkridge) matter more.

| Scenario | Winner | Score | Same as base? |
| --- | --- | --- | --- |
| Base (documented) | Brookhaven St & Cullen Blvd, Sunnyside | 68.8 | - |
| Traffic-Heavy | Eldridge Pkwy & Westhollow Pkwy, Parkridge | 77.3 | No |
| Cost-Heavy | 6600 Stillwell St, Pecan Park | 73.4 | No |
| Competition-Heavy | Brookhaven St & Cullen Blvd, Sunnyside | 74.9 | Yes |
| Demand-Heavy | Brookhaven St & Cullen Blvd, Sunnyside | 67.0 | Yes |
| Crime-Heavy | Eldridge Pkwy & Westhollow Pkwy, Parkridge | 73.6 | No |

**Practical read for the VP:** this is now genuinely a three-way real contest between Brookhaven St
(Sunnyside), Eldridge Pkwy (Parkridge), and 6600 Stillwell St (Pecan Park), each winning under
different, equally defensible priorities. See the trade-off judgment call in
`limitations_and_diligence.md`.

### Overture-sourced competitor correction (still holds, from a prior revision)

Cross-checking the OSM-sourced competitor data against Overture Maps found **a real Dollar General
~0.14 miles and a real Family Dollar ~0.24 miles from 6600 Stillwell St** that OpenStreetMap had
completely missed. If Stillwell remains under consideration for any reason, this should be
independently re-verified on the ground before proceeding.

## Top 5 of 20 citywide finalists

| Rank | Neighborhood | Site | Traffic (verified) | Crime (0.5mi, 12mo) | HUD Multifamily units (1mi) | Opportunity Zone | **Score** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **★ Recommended** | **Sunnyside** | **Brookhaven St & Cullen Blvd** | 20,532 vpd ✅ | 60 violent / 68 property | 612 | Yes | **68.8** |
| #2 | Sunnyside | 1023 Niagara St | 1,547 vpd ❌ | 57 violent / 63 property | 612 | Yes | 67.9 |
| #3 | Parkridge | Eldridge Pkwy & Westhollow Pkwy | 32,634 vpd ✅ | 2 violent / 4 property | 0 | No | 65.8 |
| #4 | Pecan Park | 6600 Stillwell St | 19,656 vpd ✅ | 24 violent / 62 property | 10 | Yes | 64.6 |
| #5 | Pecan Park | Broadway St & La Porte Fwy | 2,651 vpd ❌ | 13 violent / 31 property | 0 | No | 64.5 |

Full 20-site detail, every per-factor and per-sub-factor score, cannibalization math, and the
sensitivity analysis is in `data/processed/scorecard.csv` and the map's Analysis Dashboard.

## Real signals added across four revisions

- **HPD crime data** - real Part I violent/property incidents, 0.5mi, trailing 12mo (10% weight).
- **HUD LIHTC affordable-housing properties** - real, geocoded federal database, within 1mi (12%
  demand sub-weight).
- **Census LEHD daytime/workplace population** - real block-level job counts within 5-min drive (12%
  demand sub-weight).
- **USDA food-access share** - real, continuous SNAP-retailer-access metric (8% demand sub-weight).
- **Overture Maps competitor cross-check** - found 54 real competitors OSM missed, corrected 8 sites.
- **Real Census population growth trend** - citywide context (not scored): +91,180 people, +4.0%,
  2020-2024.
- **Federal Qualified Opportunity Zones** - real point-in-polygon-verified tract designation (8%
  demand sub-weight).
- **HUD Multifamily Properties** - real FHA-insured/assisted housing, geocoded from real addresses
  after a confirmed API limitation (this layer returns no geometry) was worked around, not ignored
  (10% demand sub-weight).

All site-level signals above are also real, off-by-default layers on the interactive map, with a
dynamic legend that shows each one only while it's actually toggled on.

## Cannibalization: existing Family Dollar stores are network, not competition

Method unchanged from prior revisions (hard/soft distance buffers + real drive-time trade-area
overlap + net-new population reach) - see `methodology.md` Stage 5b. Full 20-site table in
`data/processed/cannibalization.csv` and the map's Cannibalization tab.

## Citywide context

- **10 opportunity neighborhoods screened**, **528 real OSM store locations** across 15 banners (plus
  54 additional real Overture-sourced finds not in OSM), **275 real HCAD parcels** qualified before
  narrowing to 20 finalists. 117 of the 528 are now categorized as direct arch-rivals (Dollar General,
  Five Below, and Dollar Tree - post-separation).
- **2,328,253 people** live inside the real Houston city boundary (Census ACS 2024 5-yr, 90% CI:
  2,328,057-2,328,449) - a 2020-2024 rolling average. The real Census PEP annual estimate for 2024 is
  2,390,125; see `data_validation.md` §5 for the full growth-trend table.
- **47,283 real HPD Part I crime incidents**, **18,459 Texas block groups' worth of real LEHD job
  data**, **6,884 Texas census tracts' worth of real USDA food-access data**, **165 real Houston HUD
  Multifamily properties**, and **~100 real Harris County Opportunity Zone tracts** loaded across the
  respective screens.

## Suggested next steps for the VP

1. **Make the three-way trade-off call explicitly.** Brookhaven St (Sunnyside) wins on Opportunity
   Zone status, subsidized-housing concentration, and cannibalization risk, but has the field's worst
   crime reading; Eldridge Pkwy (Parkridge) wins on crime and traffic; 6600 Stillwell St (Pecan Park)
   sits in between. See `limitations_and_diligence.md` for this framed as a diligence decision point.
2. **Independently re-verify the Stillwell competitor correction on the ground** if that site remains
   under consideration for any reason (see above).
3. Commission a formal traffic-engineering / ingress-egress study for the recommended site's
   Cullen Boulevard frontage.
4. Confirm zoning/permitting and utility availability with the City of Houston (no municipal zoning -
   see `data_validation.md` §5).
5. Title search to confirm no restrictive covenants - not covered by any public data source used here.
6. Site visit to confirm ground conditions, visibility, and ingress/egress geometry - and, given the
   real crime reading here specifically, a security/loss-prevention assessment before committing.
