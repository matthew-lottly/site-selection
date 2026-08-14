# Methodology - Houston Family Dollar Site Selection (Citywide)

**Author:** Matthew Powers · **Prompt:** GIS Analyst case study, Location Intelligence team
**Scope:** Identify and recommend a new Family Dollar store site anywhere in the City of Houston,
TX market, using only free, public, open data and open-source tools, and communicate the
recommendation to a non-technical Real Estate VP.

Every figure in this analysis and on the accompanying web map (`index.html`) is pulled live from a
public API or dataset - nothing is fabricated or hand-typed, and every number attached to the
recommended site has been independently re-verified against the live source API (not just the
cached pipeline output) before being reported. The full pipeline is reproducible: run
`python run_pipeline.py` (see `README.md`). For the complete audit trail - every specific
check performed against hallucination or error, the real confidence intervals behind the headline
statistics, and what this analysis explicitly does not claim - see `docs/data_validation.md`.

**This is the citywide revision of the analysis.** An earlier draft screened Harris County broadly
but then only sourced and compared candidate parcels inside one neighborhood (Sunnyside). That was
a real gap: a "best site in Houston" claim needs candidates sourced from across the whole city, not
just the first promising area found. This version fixes that - see Stage 2 below.

## 1. Data sources (all free, all keyless)

| # | Source | What it provides | Access method |
| --- | -------- | ------------------- | ---------------- |
| 1 | US Census Bureau TIGERweb | Census tract & block group boundaries, and the real City of Houston incorporated-place boundary | ArcGIS REST (`tigerweb.geo.census.gov`) |
| 2 | Census Reporter API | ACS 2024 5-year estimates and margins of error: population, median household income, poverty status, foreign-born share, language spoken at home, household size | REST API (wraps Census Bureau ACS) |
| 3 | OpenStreetMap / Overpass API | Competitor & anchor retail locations (15 real banners found), arterial road network, posted speed limits, co-tenant POIs | Overpass QL |
| 4 | Harris County Appraisal District (HCAD) | Real parcel boundaries, acreage, land use class, land/building/appraised value, situs address | ArcGIS REST (`gis.hctx.net`) |
| 5 | FEMA National Flood Hazard Layer (NFHL) | Flood zone designation (X, AE, etc.) at a point | ArcGIS REST identify/query (`hazards.fema.gov`) |
| 6 | TxDOT | Annual Average Daily Traffic (AADT) counts, current (2025) | ArcGIS Online Feature Service |
| 7 | OSRM (Open Source Routing Machine) | Real drive times over the OpenStreetMap road network | Public routing API |
| 8 | Nominatim (OpenStreetMap) | Reverse geocoding - confirms each site's real neighborhood and verifies what road each traffic count and each parcel actually sits on | REST API |
| 9 | OpenStreetMap / Overpass API | Real transit stops (bus stops, transit platforms) near each finalist, for the micro-site operational detail | Overpass QL |
| 10 | Census Reporter API (ACS B25044, B25003) | Zero-vehicle household share and renter-occupied housing share, per tract and city-wide, with margins of error | REST API |
| 11 | Houston Police Department (`houstontx.gov`) | Real, point-level NIBRS Part I violent/property crime incidents (offense code, date, lat/lon), direct CSV export, for the crime-risk score | Direct CSV download (not the CKAN catalog - see below) |
| 12 | HUD LIHTC Database | Real, geocoded, point-level affordable-housing property locations and unit counts | ArcGIS REST (`egis.hud.gov`) |
| 13 | Census LEHD LODES (WAC) | Real block-level total job counts, for a real daytime/workplace-population demand signal | Direct CSV download (`lehd.ces.census.gov`) |
| 14 | USDA ERS Food Access Research Atlas (SNAP-authorized Retailer Access Map) | Real per-tract share of population beyond 0.5mi from a food retailer | Direct CSV download (`ers.usda.gov`) |
| 15 | Overture Maps Foundation Places | Real, open (CDLA Permissive 2.0), ML-deduped POI data, used to cross-check/backfill the OSM-sourced competitor pull | Public GeoParquet on S3, via the official `overturemaps` Python package |

No Census API key, Google Maps key, or paid GIS license was used or required.

## 2. Pipeline stages

### Stage 1 - Macro market screen (all of Harris County)

`pipeline/stages/s01_fetch_tracts.py`, `02_fetch_competitors.py`, `03_gap_analysis.py`

- Pulled **all 1,115 Census tracts in Harris County** with ACS 5-year population, median household
  income, and poverty rate.
- Pulled **every current store location relevant to the analysis** from OpenStreetMap across the
  county, categorized the way a real Family Dollar site selector thinks about them (see §Stage 5 -
  this is not just "dollar store vs. not"): **Family Dollar** (61 existing locations - the company's
  own network, not a competitor); **direct arch-rivals** Dollar General, Five Below, and Dollar Tree
  (117 - Dollar Tree included as a direct competitor since Family Dollar and Dollar Tree officially
  separated on 2025-07-08, see §Stage 5 for the full story); **value grocery** - Aldi, Kroger, H-E-B,
  Fiesta Mart, Food Town, Save A Lot, and two Houston-specific extreme-value banners, Joe V's Smart
  Shop (H-E-B) and Mi Tienda (Fiesta) (225); and **big-box anchors** Walmart, Target, Burlington, Ross
  (125) - **528 real stores in total**.
- Scored every tract with a transparent **opportunity ("gap") index**:

  ```text
  demand_index          = population × income_fit(median_HH_income) × (1 + poverty_rate)
  competitive_gap_index  = min(distance_to_nearest_dollar_store_mi, 3.0) / 3.0
  gap_score              = demand_index × competitive_gap_index
  ```

  `income_fit()` peaks (weight = 1.0) for tracts with median household income between $20k and $55k
  - the band that indexes most strongly to discount/value retail - tapering to zero outside roughly
  $0-$80k, so very low-income (unstable trade area) and affluent (better served by Target/Walmart)
  tracts are both discounted.

### Stage 2 - Citywide submarket scoping (the fix)

`pipeline/stages/s13_houston_scope_clusters.py`

- Pulled the **real City of Houston boundary** (TIGERweb Incorporated Places, GEOID 4835000) - a
  genuinely irregular polygon (100 rings, ~70,800 source vertices, reflecting Houston's real
  annexation-driven shape) - rather than using all of Harris County, which also contains separate
  incorporated cities (Pasadena, Baytown, Pearland, Katy) that are not "Houston, TX."
- Kept only the **643 of 1,115 Harris County tracts** whose centroid actually falls inside city
  limits.
- Rather than committing to the single highest-scoring tract cluster, grid-clustered the top-scoring
  tracts and kept the **10 strongest opportunity clusters at least 2.75 miles apart**, so the
  candidate search spans geographically distinct parts of the city instead of one neighborhood.
  Each cluster was reverse-geocoded to a real Houston neighborhood name: **Alief, Westchase,
  Sunnyside, Gulfton, Braeswood/Sunnyside corridor, Denver Harbor, East Houston, Braeburn, Acres
  Homes, and Central Southwest Houston.**

### Stage 3 - Candidate site identification, all 10 areas

`pipeline/stages/s14_find_intersections_citywide.py`, `15_fetch_parcels_citywide.py`

- For each of the 10 opportunity areas, auto-discovered that area's named primary/secondary
  arterial roads directly from OpenStreetMap (no hand-picked street lists) and found real
  intersections between them via spatial grid-bucketing - **100 real intersections across the city.**
- Queried **real HCAD parcels within ~350m of every intersection**, filtered to realistic new-store
  sites (vacant commercial land, or under-improved commercial land where the building is worth less
  than 60% of the land - a teardown/redevelopment opportunity), sized 0.4-4.0 acres.
- Screened out parcels appraising under $15,000/acre - these turned out to be HOA common areas,
  drainage reserves, and right-of-way slivers miscoded as vacant commercial land in HCAD, not real
  buildable sites (a data-quality check, not a business filter).
- This produced **275 real, addressed parcels** with actual HCAD account numbers. Kept the best 2
  per opportunity area (closest to a ~1.2-acre typical footprint, preferring shovel-ready vacant
  land) as the finalist shortlist - **20 real candidate sites spanning all 10 neighborhoods.**

### Stage 4 - Site enrichment

`pipeline/stages/s16_fetch_citywide_aadt.py`, `17_fetch_citywide_blockgroups.py`, `18_enrich_sites_citywide.py`

For each of the 20 finalists:

- **FEMA flood zone** at the exact parcel point (NFHL identify query).
- **Verified traffic count**: nearest TxDOT AADT station. TxDOT records roads by route number (e.g.
  `FM0865`), not local name, and a station can sit directly on a limited-access freeway a store could
  never have a driveway onto - so every match's coordinates were reverse-geocoded to a real street
  name, and any station whose name resolved to a freeway/tollway/loop was rejected in favor of the
  nearest genuine arterial station (falling back to a conservative citywide-minimum estimate, never
  the freeway's inflated count, for the 3 sites where no arterial station exists nearby).
- **Neighborhood identity**: each site's own coordinates were independently reverse-geocoded rather
  than inheriting its search cluster's label, since one cluster's search radius can span more than
  one named neighborhood.
- **Competitive distances**: straight-line distance to the nearest true arch-rival (Dollar General or
  Five Below), nearest value-grocery store, and nearest big-box anchor - tracked separately from
  distance to the nearest **existing Family Dollar**, which feeds the cannibalization analysis
  (Stage 5b) rather than the competitive-gap score, since it isn't competition.
- **Micro-site operational detail** (`pipeline/stages/s26_microsite_details.py`): posted speed limit on the
  frontage road (OSM `maxspeed` tag, where mapped - the 35-45 mph range is the sweet spot for
  discount-retail impulse-stop visibility); real nearby co-tenant traffic generators (gas stations,
  laundromats, schools, post offices, pharmacies) within 0.3 mi; real nearest public-transit stop
  (OSM bus stops and transit platforms, within 1 mile); and approximate parcel bounding dimensions
  computed from the real HCAD parcel polygon (haversine edge lengths - a gut-check on lot size, not a
  certified survey). Explicitly **not** claimed, because no public API covers it and asserting a
  confirmation would be fabrication: deed restrictions/restrictive covenants (requires a title
  search), median-break/divided-highway ingress-egress geometry, and an engineered 53-ft
  delivery-truck turning radius (both require a civil site plan). Full detail on these gaps and the
  concrete diligence steps that close them: `docs/limitations_and_diligence.md`.
- **Real drive-time trade area**: queried OSRM (actual road-network routing, not a circle buffer)
  from each site to every one of Houston's **1,603 Census block groups (2,312,201 people - matches
  Houston's real published population)** within a 10-mile prefilter, and summed ACS population
  reachable within a 5-minute and a 10-minute drive.

### Stage 5 - Huff gravity market-capture model

`pipeline/stages/s19_drive_times_and_huff.py`

For each site, estimated a relative market-capture percentage using the classic **Huff gravity
model**: for every block group in the site's drive-time trade area, the candidate's pull is compared
against every real nearby **direct arch-rival** (Dollar General, Five Below, and Dollar Tree - same
target demographic, footprint, and inventory mix as Family Dollar), using each banner's published
typical prototype square footage as the size/attraction term and a distance-decay exponent of β = 2.0
(the standard value in retail gravity-model literature):

```text
P(choose site j | block group i) = (Sⱼ / Dᵢⱼ^β) / Σₖ (Sₖ / Dᵢₖ^β)
```

**Dollar Tree is now included as a direct arch-rival - a real correction from earlier revisions of
this analysis.** Earlier revisions excluded Dollar Tree from the competitive set because it was
Family Dollar's *sister banner*, both owned by the same parent, Dollar Tree, Inc. That relationship
ended: Dollar Tree sold Family Dollar to private equity (Brigade Capital Management, Macellum Capital
Management, and Arkhouse Management), and the two officially separated on **2025-07-08** - Family
Dollar has been a standalone company since. Modeling Dollar Tree as unrelated network rather than a
real, same-format competitor would now misstate the actual business relationship, so this revision
folds it into the arch-rival competitive set. This is a real, verified, dated business fact (confirmed
via Dollar Tree's own investor-relations press releases and multiple trade-press sources), not a
judgment call - see `data_validation.md` §2 for the full audit trail and its effect on every site's
Huff capture percentage.

One remaining deliberate exclusion from the Huff competitive set, tested and confirmed before the
design choice was made:

- **Full grocery/big-box anchors** (Walmart, H-E-B, Kroger, Target) - they serve a different shopping
  mission (a weekly grocery trip vs. a quick value/convenience trip), and their much larger square
  footage mathematically swamps every candidate's share to a uniform near-zero number regardless of
  where the store actually sits.

This mirrors how real dollar-store site selection evaluates competitive threat: against same-format
rivals actually competing for the same trip, not the whole retail landscape.

Candidate-site travel time (`Dᵢⱼ`) uses real OSRM network minutes. Competitor travel time (`Dᵢₖ`) is
approximated from straight-line distance at a 25 mph average urban-arterial speed - a documented
simplification made to keep the API call count tractable across 20 sites × ~1,600 block groups, not
a fabricated number. **This produces a relative, population-weighted capture percentage per site -
not a predicted revenue dollar figure**, since no public store-level sales data exists to calibrate
one; a dollar forecast built without real sales data to ground it would itself be a fabricated
number, so this analysis deliberately stops at a defensible relative comparison instead.

### Stage 5b - Cannibalization analysis

`pipeline/stages/s24_cannibalization_analysis.py`

Existing Family Dollar stores are the company's own network, not competitors - the real question is
how much of a new store's trade area a nearby existing store already serves. A 3-step framework,
adapted to only use real, computable inputs:

1. **Hard/soft exclusion buffers** on straight-line distance to the nearest existing Family Dollar:
   under 1.2 mi auto-flags High risk (industry rule-of-thumb minimum spacing for a small-box
   format); over 2.5 mi auto-clears to Low risk; in between, the overlap calculation decides.
2. **Trade-area overlap %**: of the population inside the candidate's real 5-minute OSRM drive-time
   trade area, what share also sits within 1.5 miles (straight-line) of the nearest existing FD.
   Under 15% is Low risk, 15-30% is Moderate, over 30% is High. (This mixes a network-based candidate
   trade area with a straight-line existing-store trade area - a documented, disclosed asymmetry, not
   a hidden one: full network routing from all 1,603 block groups to every existing FD store would
   have multiplied the OSRM call count roughly 60x for a secondary metric.)
3. **Net-new population reach** = 5-minute drive population minus the overlap population. This is
   deliberately **not** a "net new sales $" figure - that would require a revenue model calibrated to
   real store-level sales data, which doesn't exist publicly. Reporting a dollar figure without that
   grounding would be a fabricated number dressed up as precise; net-new population reach answers the
   same underlying question (how much of this trade area is genuinely incremental) with a real,
   computed proxy instead.

### Stage 5c - Crime risk

`pipeline/stages/s30_crime_risk.py`

A real property/violent crime metric was investigated in an earlier revision and dropped as
unavailable - that check queried only Houston's open-data CKAN catalog (`data.houstontx.gov`,
`package_search`/`package_show`), which genuinely has no queryable crime dataset. That check missed a
separate, real source: **Houston Police Department's own site publishes point-level NIBRS incident
data as direct CSV downloads** (offense code, occurrence date, beat, and lat/lon), free and keyless,
back to 2009 - not through the CKAN API at all. This stage closes that gap:

- Downloaded the real 2025 and 2026 NIBRS Public View exports directly from HPD, filtered to the
  trailing 12 months (Aug 2025-Jul 2026, matching the most recent published refresh of the 2026 file).
- Classified offenses using the standard FBI UCR Part I "index crime" definition - the same standard
  used nationally for retail crime-risk screening, not an ad hoc one: **violent** = murder (09A), rape
  (11A-11D), robbery (120), aggravated assault (13A); **property** = burglary (220), larceny/theft
  (23A-23H), motor vehicle theft (240).
- Counted real incidents within a fixed 0.5-mile radius of each of the 20 finalists. Because the
  radius is identical for every site, raw incident counts are already an apples-to-apples comparison
  without a separate per-capita normalization step.
- Loaded **47,283 real qualifying incidents citywide** for the window; per-site counts range from 1
  (Site 20, Inwood) to 147 (Site 8, Fondren Gardens) - a large, real, differentiating spread. Full
  detail in `data/processed/site_crime_risk.csv`.

### Stage 5d - Second free-data pass: LIHTC, daytime population, food access, and an OSM cross-check

After adding real crime data, a deliberate second research pass checked (a) whether any of the paid
data categories this analysis would otherwise have to flag as unavailable actually have a free
alternative, and (b) whether any other obvious free dataset for retail site selection had been missed.
Four real, free, currently-live sources were found and added - full source-by-source verification and
what was checked and ruled out (Walk Score API, HUD USPS vacancy data, Texas Comptroller sales tax,
CDC SVI, FBI CDE) is in `data_validation.md` §2 items 15-18.

**Real HUD LIHTC affordable-housing proximity** (`pipeline/stages/s32_lihtc_properties.py`) - HUD's
Low-Income Housing Tax Credit Database is served as a public ArcGIS REST Feature Service, the same
access pattern already used for HCAD/FEMA/TxDOT. Queried within 1.0 mile of each finalist for real,
geocoded property records (project name, unit count). A real, free proxy for concentration of Family
Dollar's core low-income customer base near a candidate site.

**Real Census LEHD daytime/workplace population** (`pipeline/stages/s33_daytime_population.py`) -
every other demand signal in this pipeline measures *residents* reachable by drive time; this model
had zero visibility into the office/retail/industrial workforce that passes a site on a commute or
lunch break. Census LEHD LODES (the same public data behind the Census Bureau's own OnTheMap tool)
provides real, free, block-level total job counts. Downloaded Texas's real 2023 Workplace Area
Characteristics file, aggregated block-level job counts to block-group level (matching the block
group's first 12 GEOID digits), and summed real job counts within each finalist's already-cached real
OSRM 5-minute drive-time trade area (reusing script 19's cached durations - no new routing calls).

**Real USDA food-access share** (`pipeline/stages/s34_food_access.py`) - the USDA Economic Research
Service's Food Access Research Atlas (now distributed as part of the SNAP-authorized Retailer Access
Map, SRAM) publishes a real, continuous "share of tract population beyond 0.5 mile from a
SNAP-authorized food retailer" metric per census tract - directly on-topic for a dollar-store
expansion thesis, since these stores are frequently sited specifically to serve areas with poor
supermarket access, and this signal was completely absent from every prior revision. (The Atlas's
binary "low-income AND low-access" flag was checked first and found to read False for all 20
already-commercially-screened finalists - no differentiating signal for this specific candidate set -
so the continuous share metric was used instead; both are real Atlas fields, not a threshold invented
for this project.)

**Real Overture Maps competitor cross-check** (`pipeline/stages/s35_overture_supplement.py`) - this
project already documented a real OSM coverage gap (Ross Dress for Less undercounted citywide, see
`data_validation.md` §6). Overture Maps Places - free, open (CDLA Permissive 2.0), blending Meta,
Microsoft, TomTom, and ~200 other sources with ML-based dedup/QA - was queried within 1.0 mile of each
finalist and cross-checked against the existing OSM-sourced competitor list. Found **54 real
competitor locations across the 20 finalists that OSM had missed**, corrected the nearest-competitor
distance for 8 of the 20 sites, and surfaced one materially significant finding: a real Dollar General
and a real Family Dollar within a quarter mile of 6600 Stillwell St (the prior revision's #2 site) that
OSM's data had missed entirely - see `docs/results.md` for the full story. Scope, disclosed rather than
silently assumed: only the nearest-competitor-distance input to the scorecard is corrected this way;
the Huff market-capture model is not re-derived against Overture data (a larger change, out of scope
for this pass - Overture's major-chain coverage for arch-rivals specifically is already strong in OSM,
unlike the big-box-anchor gap this project originally found).

### Stage 6 - Weighted scorecard

`pipeline/stages/s20_score_sites_citywide.py`

Each metric was min-max normalized across the 20 finalists (0-100) and combined with documented
weights. The original 25/20/15/15/15/10 split was rebalanced to make room for the real crime-risk
factor above at the same 10% weight as flood risk - both are risk-mitigation factors that penalize a
worse reading rather than reward a better one - with the other five factors scaled down
proportionally rather than arbitrarily:

| Factor | Weight | Rationale |
| --- | --- | --- |
| Trade-area demand (blended composite, see below) | 22% | Rooftops within an easy drive, weighted toward the $20k-$55k core customer band, now also incorporating real LIHTC/daytime-population/food-access signals |
| Huff market-capture % | 18% | Comprehensive, distance- and size-weighted competitive pull against direct arch-rivals |
| Competitive white space (distance to nearest arch-rival, Overture-corrected) | 13% | Simple, exec-legible cross-check on the Huff score |
| Traffic & visibility (verified AADT) | 13% | Passive visibility drives real discount-retail traffic; freeway mainlane counts excluded |
| Site feasibility & cost (land value/acre, vacant-land bonus) | 14% | Lower acquisition cost and shovel-ready land reduce time-to-open |
| Flood risk (FEMA zone) | 10% | Any mapped Special Flood Hazard Area is heavily penalized |
| Crime risk (real HPD Part I incidents, 0.5mi, trailing 12mo) | 10% | More nearby violent/property incidents is penalized (Stage 5c) |

**Trade-area demand is itself a blended composite**, extended this revision to fold in the three new
demand-side signals from Stage 5d - the same pattern already used for `cost_feasibility_score`
(land-cost-per-acre blended with a vacant-land bonus into one line), so the top-level factor count
stays at seven rather than growing indefinitely, while every sub-component stays visible as its own
column in `scorecard.csv` for transparency:

| Demand sub-component | Sub-weight | Rationale |
| --- | --- | --- |
| Residential 5-min drive population × income fit (original signal) | 60% | Still the core, most directly relevant demand metric |
| Real LIHTC units within 1mi (Stage 5d) | 15% | Concentration of the core low-income customer base |
| Real LEHD daytime workplace population within 5-min drive (Stage 5d) | 15% | A signal this model had zero visibility into before this revision |
| Real USDA food-access share (Stage 5d) | 10% | On-topic "underserved area" signal for a dollar-store expansion thesis |

**Competitive white space also carries a real correction this revision**: the nearest-competitor
distance input is Overture-corrected where Stage 5d's cross-check found a real competitor OSM missed
(8 of 20 sites), rather than the raw OSM-only reading used in prior revisions.

**The 8,000 AADT industry rule-of-thumb minimum viable-traffic benchmark is enforced as a hard gate
on the primary recommendation, not just a soft-weighted factor.** The scoring script selects the
**primary recommendation** as the highest-scoring site that *also* clears the benchmark; a
higher-raw-score site that fails it stays visible in the scorecard (tagged) for transparency but is
not selectable as "the" recommendation. In the current run the top raw-scoring site also clears the
benchmark on its own - the gate's practical effect is excluding several lower-ranked, AADT-failing
sites (e.g. Broadway St & La Porte Fwy, 2,651 vpd, a real but low reading) from ever becoming the
recommendation regardless of how well they score on the other six factors - but earlier in this
project's development the gate did override the raw #1, which is exactly why it's implemented as a
hard rule rather than left to the weighted average. See `docs/results.md` for the current ranking, and
`docs/data_validation.md` §2 for how a related classification bug (freeway vs. frontage road in the
traffic-count matching) was found and fixed via the sensitivity analysis in Stage 8b below.

### Stage 7 - Trade-area visualization

`pipeline/stages/s21_fetch_houston_tract_geometry.py`, `pipeline/stages/s22_isochrone_winner.py`

Pulled tract polygon geometry for all 643 Houston-city tracts (simplified for file size with
Douglas-Peucker line simplification, ~9x fewer vertices, no change to the underlying values) so the
map's opportunity choropleth covers the whole city that was actually screened. Built a real 5-minute
/ 10-minute drive-time isochrone for the recommended site by querying OSRM along 16 compass bearings
at 8 candidate distances each, keeping the farthest point on each bearing still under the time
threshold - the actual reachable shape given the real road network, not a generic circle.

### Stage 8 - Extended demographics & confidence intervals

`pipeline/stages/s25_extended_demographics_and_ci.py`

Two things a first pass at this analysis was missing:

- **Real Houston-specific demographic nuance** the ACS already tracks: foreign-born share, Spanish
  spoken at home, and average household size, pulled for all 643 Houston tracts. Corridors like
  Gulfton, Alief, and East Houston have large immigrant, multi-generational-household populations -
  a real demand driver for Family Dollar's core categories (dry grocery, baby products, household
  essentials) that median-income screening alone doesn't capture.
- **Real 90% confidence intervals** for the city-wide headline statistics, using the Census Bureau's
  own place-level geography (not a sum of tracts) and its published ratio-MOE propagation formula for
  derived rates. Full table and formula in `docs/data_validation.md` §4 and the map's Confidence
  Intervals dashboard tab.

### Stage 8b - Vehicle access, housing tenure, and sensitivity analysis

`pipeline/stages/s27_vehicle_tenure_demographics.py`, `pipeline/stages/s28_sensitivity_analysis.py`

- **Zero-vehicle household share and renter-occupied housing share** (ACS B25044, B25003), pulled for
  all 643 Houston tracts plus a real city-wide 90% confidence interval, using the same ratio-MOE
  propagation formula as Stage 8. Both are real demand-relevant signals for a discount-retail format
  specifically: a zero-vehicle household depends more on walkable/visible neighborhood retail, and a
  renter-heavy tract skews toward exactly the household-budget profile Family Dollar's core
  categories serve. Surfaced in the map's tract popups and Confidence Intervals dashboard tab.
- **Multi-scenario sensitivity analysis**: re-aggregates the same already-normalized 0-100 per-factor
  subscores from Stage 6 under 6 different, defensible weighting schemes (Traffic-Heavy, Cost-Heavy,
  Competition-Heavy, Demand-Heavy, Crime-Heavy, plus the documented Base split), re-applying the same
  AADT gate to each. The Crime-Heavy scenario (30% weight on the Stage 5c crime score) was added
  specifically to stress-test how load-bearing the new crime factor is on the recommendation. No new
  data is fetched - this is a pure re-aggregation check on whether the recommendation is an artifact
  of the specific weights chosen, or holds up under alternative, equally defensible ones.
  Building this check is what surfaced the freeway/frontage-road classification bug documented in
  `docs/data_validation.md` §2 - an implausible score under one scenario traced back to a real error
  in Stage 4's traffic-count matching, which was then fixed and changed the actual recommendation.
  Results in `data/processed/sensitivity_analysis.csv` and the map's Scorecard tab.

### Stage 9 - Web map

`pipeline/stages/s22_isochrone_winner.py`, `pipeline/stages/s23_generate_map_citywide.py`

Built with Folium (Python) on top of Leaflet.js - 100% open source, no API key, deployable as a
static file to GitHub Pages. Layers: real Houston city-limits boundary (off by default for initial
map clarity); citywide opportunity choropleth (643 tracts, blue sequential ramp with fill opacity
scaled to score so low-opportunity tracts recede and high-opportunity ones stand out); competitors
split into 4 toggleable tiers matching the categorization in Stage 1 (Family Dollar always visible
for the cannibalization check; arch-rivals - now including Dollar Tree - visible by default; value
grocery and big-box anchors off by default as context layers) - colors were deliberately chosen from
a validated cool-hue set (blue/magenta/aqua) that remains visually distinct from the rank-badge color
ramp; all 20 candidate sites as clean numbered rank badges (white ring, small footprint) on a
validated best→worst color ramp, with the recommendation as a distinct gold-ringed star; the 10
opportunity areas searched; and the real drive-time trade area for the recommended site. A FEMA
NFHL flood-polygon layer is included as a toggleable off-by-default overlay for risk review and is
fetched live client-side from the FEMA API (instead of being stored as a large static repo artifact).
The live fetch is capped to a fixed area around the map center and gated behind a minimum zoom level
(with an on-map "zoom in" hint below that) - a full-city query was tested directly against the live
FEMA API and confirmed to exceed FEMA's own server-side transfer limit on the first page alone, so
citywide loading was never a viable design, not just a performance nicety.
Four more real, free, off-by-default layers from Stage 5d are also on the map: HUD LIHTC
affordable-housing properties, Census LEHD daytime workplace population (all Houston block groups),
USDA food-access share (the 20 finalist tracts), and the Overture-sourced competitors OSM's data
missed - each cited to its real source in its own popup, same as every other layer.
A basemap switcher offers 5 free tile providers (light, dark, streets, satellite, terrain). Every
marker popup cites its data source, set in dark, bold text for at-a-glance legibility.

**The legend (bottom-left) is dynamic**, not a static always-on-screen key: every section is tagged
to the exact real map layer it describes, and JavaScript listening to Leaflet's own
`overlayadd`/`overlayremove` events shows or hides that section live as the corresponding checkbox is
toggled in the layer control - so the legend only ever displays what's actually visible on the map,
for every layer, current and future, without a second source of truth to keep in sync by hand.

A **right-side Analysis Dashboard panel** (toggle button, top-right header) surfaces seven tabs built
live from the same CSVs referenced throughout this document: **Executive Checks**, the full 20-site
**Scorecard** (with the sensitivity analysis beneath it), the **Cannibalization** table, **Site
Details** (micro-site operational data including transit distance), **Confidence Intervals**
(including the vehicle-access and housing-tenure rates from Stage 8b), **Model Rigor**, and
**Sources & Validation** - a condensed version of the audit trail in `data_validation.md`.

## 3. Known limitations

- ACS 5-year estimates (2020-2024) carry real margins of error - see `docs/data_validation.md` §4 for
  the actual 90% confidence intervals on every headline statistic, computed with the Census Bureau's
  own methodology, rather than treating point estimates as exact.
- The Huff model's and cannibalization analysis's competitor-side travel time are straight-line/
  speed-assumption approximations, not full OSRM routing from every block group to every competitor
  (see Stages 5 and 5b) - a documented tractability trade-off, not a fabricated number.
- The isochrone is generated from 16 rays × 8 distances (128 points), which can miss small dead-end
  pockets or one-way-street effects; it is a strong approximation, not a parcel-precise flood-fill.
- Overpass/OSM competitor and road data reflect current OSM tagging completeness. It is generally
  strong in Houston but not exhaustive - e.g., Ross Dress for Less returned only 1 match despite
  operating more locations in Houston, almost certainly an OSM tagging gap rather than a real count.
  This revision partially closes the gap for the 20 finalists specifically: Stage 5d's Overture Maps
  cross-check found 54 real competitor locations OSM had missed nearby and corrected 8 sites' nearest-
  competitor distance - but full citywide OSM completeness (beyond the 20 finalists' immediate
  vicinity) is still not claimed.
- No revenue forecast is produced anywhere (see Stages 5 and 5b). The industry-standard technique for
  this - **analog-store sales forecasting**: profiling the candidate site, finding the retailer's own
  existing stores with the closest-matching trade-area/site profile, and forecasting from a weighted
  average of those analogs' real sales performance - requires Family Dollar's own store-level
  performance data, which no public source provides. Confirmed against current retail site-selection
  best-practice literature (see `docs/data_validation.md` §2) rather than assumed unavailable.
- Relatedly, this analysis's **scorecard weights are documented and defensible but judgment-based, not
  regression-calibrated against real historical store performance** - best practice for a mature
  retailer is to regress location attributes against actual store outcomes to find which factors
  really predict success for that specific brand and format. The same missing ingredient (real store
  performance data) blocks both the revenue forecast above and empirical weight calibration; without
  it, judgment-based weights informed by the source framework and stated explicitly (§Stage 6) are the
  correct fallback, not a hidden shortcut.
- **Distribution-center / logistics proximity was considered and correctly excluded**, not overlooked.
  Regional distribution centers typically serve a 250-350 mile radius (a single Dollar Tree Southwest
  DC covers ~700 stores across multiple states) - all 20 Houston finalists sit a few miles apart in
  the same metro and would be served by the same regional DC regardless of which one is chosen, so
  this factor cannot differentiate between them at this analysis's geographic scale.
- A real property/violent crime metric **is** produced (Stage 5c) - real HPD NIBRS Part I incident
  counts within 0.5mi of each site, trailing 12 months, weighted at 10% in the scorecard. An earlier
  revision checked only Houston's open-data CKAN catalog API (genuinely no queryable crime dataset
  there) and stopped, missing HPD's own direct CSV export; see `docs/data_validation.md` §2 for the
  full correction.
- Deed restrictions, median-break/ingress-egress geometry, and engineered truck-turning-radius
  confirmation are not covered by any public data source used here and are explicitly flagged as
  unverified (Stage 4, Site Details dashboard tab) rather than guessed.
- This is a desk-based screening exercise. A final go/no-go would still require a site visit, a
  title/zoning check, and formal traffic-engineering sign-off.

**Full audit trail:** every specific hallucination/error check actually performed on this analysis -
including bugs found and fixed during the process - is cataloged in `docs/data_validation.md` §2.
**Full diligence roadmap:** what a desk analysis can't verify and the concrete next steps that close
each gap, organized by whether it's a data-availability constraint or a structural boundary (title
search, engineering sign-off, site visit) - see `docs/limitations_and_diligence.md`.
