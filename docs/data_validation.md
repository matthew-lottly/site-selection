# Data Validation & Statistical Rigor - Houston Family Dollar Site Selection

This document exists to answer one question directly: **how do we know this analysis isn't making
things up?** It catalogs every data source, every number's provenance, every audit step actually
performed, the real confidence intervals behind the headline statistics, and - just as important -
what the analysis explicitly does *not* claim, because no public data supports it.

Companion documents: [`methodology.md`](methodology.md) (how the pipeline works, stage by stage),
[`results.md`](results.md) (the recommendation and scorecard), and
[`limitations_and_diligence.md`](limitations_and_diligence.md) (what a desk analysis can't verify,
and the concrete next steps that close that gap). The interactive map's **Analysis Dashboard** panel
(right side of `index.html`, opened from the header) surfaces the same scorecard, cannibalization
table, confidence intervals, sensitivity analysis, and this validation summary live, sourced from the
same CSV files referenced here.

## 1. Full source catalog

| Source | What it provides | Access | Cost / auth |
| --- | --- | --- | --- |
| US Census Bureau TIGERweb | Tract & block-group boundaries; the real City of Houston incorporated-place boundary | ArcGIS REST, `tigerweb.geo.census.gov` | Free, no key |
| Census Reporter API | ACS 2024 5-year estimates **and margins of error** for population, income, poverty, foreign-born status, language spoken at home, household size | REST API wrapping the Census Bureau ACS | Free, no key |
| OpenStreetMap / Overpass API | 528 real competitor/anchor locations across 15 banners; arterial road network; posted speed limits; co-tenant POIs (gas stations, laundromats, schools, post offices, pharmacies) | Overpass QL | Free, no key |
| Harris County Appraisal District (HCAD) | Real parcel boundaries, acreage, land-use class, land/building/appraised value, situs address | ArcGIS REST, `gis.hctx.net` | Free, no key |
| FEMA National Flood Hazard Layer (NFHL) | Flood zone designation at a point | ArcGIS REST identify, `hazards.fema.gov` | Free, no key |
| TxDOT | Annual Average Daily Traffic (AADT), 2025 counts | ArcGIS Online Feature Service | Free, no key |
| OSRM (Open Source Routing Machine) | Real drive times over the OpenStreetMap road network | Public routing API | Free, no key |
| Nominatim (OpenStreetMap) | Reverse geocoding - road identity, neighborhood identity | REST API | Free, no key, rate-limited to 1 req/sec (respected throughout) |
| OpenStreetMap / Overpass API | Real transit stops (bus stops, transit platforms) near each finalist | Overpass QL | Free, no key |
| Census Reporter API (ACS B25044, B25003) | Zero-vehicle household share and renter-occupied housing share, per tract and city-wide, with margins of error | REST API | Free, no key |
| Houston Police Department (`houstontx.gov`) | Real, point-level NIBRS Part I violent/property crime incidents (offense code, date, lat/lon) for the crime-risk score | Direct CSV download | Free, no key |
| HUD LIHTC Database | Real, geocoded, point-level affordable-housing properties (project name, unit counts) | ArcGIS REST, `egis.hud.gov` | Free, no key |
| Census LEHD LODES (WAC) | Real block-level total job counts, for a real daytime/workplace-population signal | Direct CSV download, `lehd.ces.census.gov` | Free, no key |
| USDA ERS Food Access Research Atlas (SRAM) | Real per-tract share of population beyond 0.5mi from a SNAP-authorized food retailer | Direct CSV download, `ers.usda.gov` | Free, no key |
| Overture Maps Foundation Places | Real, open, ML-deduped POI data used to cross-check the OSM-sourced competitor pull | Public GeoParquet on S3, via the `overturemaps` Python package | Free, open (CDLA Permissive 2.0), no key |

No Census API key, Google Maps key, or paid GIS/mobility-data license (SafeGraph, Placer.ai, Esri)
was used or is required to reproduce this analysis.

## 2. Specific hallucination/error checks actually performed

These are not generic assurances - each one is a concrete thing that was checked, and in several
cases, a real problem that was found and fixed - including one, #10 below, that changed the actual
recommendation.

1. **Live re-verification of the winning site.** After the pipeline produced its recommendation,
   the HCAD parcel record, FEMA flood zone, and TxDOT AADT count for that exact site were
   independently re-queried directly against the source APIs (not the pipeline's cached output) and
   matched, before the recommendation was finalized.
2. **AADT road identity verification.** TxDOT records traffic counts by route number (e.g.
   `FM0865`), not local street name. Every AADT match used in scoring was reverse-geocoded to a real
   street name to confirm identity (e.g., confirming `FM0865` really is Cullen Blvd). Stations whose
   coordinates resolved to a freeway or tollway - which a retail pad cannot legally have a driveway
   onto - were rejected in favor of the nearest genuine arterial-road reading, with a fallback flag
   for the 3 sites where no arterial station exists nearby (their traffic score uses a conservative
   citywide-minimum estimate, never the inflated freeway figure).
3. **Independent per-site neighborhood verification.** Each finalist's neighborhood name was
   reverse-geocoded from its own coordinates rather than inherited from the macro search cluster
   that found it. This mattered: one site (the current #2 finalist, Brookhaven St & Cullen Blvd) was
   initially mislabeled "Braeswood" because its search cluster's centroid sat in Braeswood, even
   though the specific parcel - subdivision "East Sunnyside Court" - is really in Sunnyside. Fixed by
   re-geocoding every site individually.
4. **HCAD data-quality filter.** Several parcels that queried as "vacant commercial land" (state
   class C1/C2) appraised at $900-$5,000 total for 0.4-2+ acres - economically impossible for real
   commercial land (that's a few cents per square foot). Inspection showed these were HOA common
   areas, drainage/detention easements, and right-of-way remnants miscoded in HCAD, not real
   buildable sites. Filtered out with a $15,000/acre floor.
5. **Cross-cluster duplicate check.** Two adjacent macro search areas can find the same real parcel
   near their shared border. Deduplicated globally by HCAD account number so no site is counted, or
   could win, twice.
6. **Stale-data bug caught by cross-checking.** After the analysis was rebuilt to search citywide
   instead of one neighborhood, the map's drive-time isochrone briefly still showed the *previous*
   draft's recommended site's shape rather than the new one's - a stale cache file the map script
   read without re-validating. Caught by checking the isochrone file's embedded site label against
   the live scorecard winner, and fixed by making the isochrone script always re-derive from the
   current scorecard's top row rather than trusting a cached file blindly.
7. **Dead-code / silently-broken field removed.** An early version of the macro gap-analysis script
   computed a "nearest anchor" distance for every tract that was always exactly 99.0 miles - a
   placeholder that was never real, caused by a category-name mismatch (`"anchor"` vs. the real
   category name), and had gone unnoticed because nothing downstream actually used the value. Found
   during this audit and removed rather than left in the output.
8. **AADT-benchmark scoring gate.** The weighted scorecard alone let a site with only 1,547 vehicles
   per day (a real, low reading) outscore the actual recommendation on raw points, because traffic
   is only 15% of the composite weight. Rather than let a soft-weighted average paper over a site
   that fails a real industry minimum-viable-traffic threshold (8,000 AADT), the scoring logic now
   explicitly gates the *primary recommendation* to the top-scoring site that also clears that
   threshold - the higher-raw-score, benchmark-failing site is kept visible in the scorecard for
   transparency, tagged, but is not selectable as "the" recommendation.
9. **No revenue dollar figure, anywhere.** Neither the Huff gravity model nor the cannibalization
   analysis produces a predicted-sales dollar amount. Family Dollar does not publish store-level
   sales data, so no model here is calibrated against real revenue - a dollar figure would be a
   fabricated number wearing a precise mask. Both analyses stop at real, computed, relative metrics
   instead (market-capture percentage; net-new population reach) that answer the same underlying
   business question without inventing a number.
10. **Freeway/frontage-road classification bug, found and fixed via the sensitivity analysis - the
    single most consequential check performed in this project.** Building the multi-scenario
    sensitivity analysis (`pipeline/stages/s28_sensitivity_analysis.py`) exposed an implausibly dominant score
    for one candidate under a Traffic-Heavy weighting, which traced back to a real bug: the
    freeway-name filter (`FREEWAY_PATTERN` in `pipeline/stages/s18_enrich_sites_citywide.py`) correctly
    rejected AADT stations whose reverse-geocoded name contained "Freeway," but it also needed to
    catch names like "East Loop North" (I-610's real east-side name), which slipped past the
    original pattern because it required "loop" plus a digit, not "loop" plus a direction word.
    Broadening the pattern to catch that case then over-corrected: it started also rejecting
    legitimate **frontage roads** literally named after the freeway they parallel (e.g. "Gulf Freeway
    Frontage Road" - a real street with real driveway access, common in Houston), silently replacing
    several sites' correct AADT readings with lower fallback values. Fixed with an explicit
    `is_true_freeway()` override that treats any name containing "frontage" as not a freeway,
    checked before the freeway-keyword pattern. **This fix changed the actual recommendation** - the
    corrected AADT for 6600 Stillwell St jumped from 2,980 to 19,656 (a real Gulf Freeway Frontage
    Road count, independently re-verified against TxDOT afterward as genuinely distinct from that
    corridor's ~193,000 freeway-mainline count nearby), moving it from a traffic-benchmark failure to
    the new top-scoring, benchmark-clearing site. Documented here rather than quietly folded into the
    final numbers because a validation process is only credible if it's shown catching something
    real, not just asserted.
11. **Property crime - initially checked via the wrong door, then found and added (see item 14).**
    An earlier revision checked `data.houstontx.gov`'s CKAN catalog directly (`package_search`,
    `package_show`) for a queryable crime dataset and found none: Houston's CKAN catalog genuinely
    only lists static HTML report pages, and a `police-transparency-hub` package exists there with
    zero attached resources. That check was real and its finding about the CKAN catalog specifically
    is still correct - but it stopped one door too early. See item 14 below for the real source that
    check missed, and `docs/methodology.md` Stage 5c for how it's now used.
12. **FEMA flood-layer transfer-limit bug, found and fixed.** The map's FEMA NFHL overlay
    (`pipeline/stages/s23_generate_map_citywide.py`) originally queried the live FEMA API for whatever the
    current map viewport was. Tested directly against the live API at the map's citywide starting
    view: the first 2,000-feature page alone returned ~25MB and FEMA reported
    `exceededTransferLimit: true`, with an unknown number of pages still remaining - so the layer
    never finished loading and appeared empty. Fixed by capping every query to a fixed small area
    around the map center (verified at ~5MB per request) and gating fetches behind a minimum zoom
    level, with an on-map hint below that level and a refetch on pan/zoom.
13. **Recommendation marker color was silently coupled to rank position, not the actual
    recommendation.** The winning site's marker color was computed from its raw score-rank position on
    the best-to-worst ramp, which only rendered green because the current #1 raw score happens to also
    be the primary recommendation. Since the scoring gate (`pipeline/stages/s20_score_sites_citywide.py`) can
    make the primary recommendation a site other than the raw #1 (see item 8 above), that coupling
    would have silently rendered the winner marker in whatever ramp color its rank happened to be
    the moment the raw #1 fails the AADT benchmark - contradicting the legend's fixed "gold-ringed
    star" promise. Fixed by making the winner's fill and ring color constants, independent of rank.
14. **Property crime - the real source that item 11's check missed, found and added.** Item 11's
    CKAN-catalog check was correct as far as it went, but it only checked one access path. Houston
    Police Department separately publishes real, point-level NIBRS Part I crime incident data (offense
    code, occurrence date, beat, and exact lat/lon) as direct CSV downloads on its own site
    (`houstontx.gov/police/cs/xls/NIBRSPublicView{year}.csv`), free, keyless, and current through the
    most recent monthly refresh - not through the CKAN API at all, so the earlier check never saw it.
    Verified directly (`curl -I`) that the file is live and downloadable before building anything on
    top of it. Added as `pipeline/stages/s30_crime_risk.py`: real violent (murder, rape, robbery,
    aggravated assault) and property (burglary, larceny-theft, motor vehicle theft) Part I incident
    counts within 0.5 miles of each finalist, trailing 12 months (Aug 2025-Jul 2026), loaded from
    **47,283 real qualifying incidents citywide**. Folded into the scorecard as a real 7th factor at
    10% weight (`docs/methodology.md` Stage 6), with the other weights rebalanced proportionally
    rather than arbitrarily. **This changed the actual recommendation**: the previous top site
    (6600 Stillwell St, Pecan Park) has a real, materially worse crime reading nearby (24 violent + 62
    property incidents within 0.5mi, crime score 41.8/100) than the new #1 (Eldridge Pkwy & Westhollow
    Pkwy, Parkridge - 2 violent + 4 property, crime score 96.6/100), which was enough to overtake it
    once a real risk factor previously missing from the model was added. Full before/after comparison
    in `docs/results.md`.
15. **Second free-data pass - re-checked every paid category for a free alternative, found one
    (Overture Maps), and found three other free datasets this model had never used.** Rather than
    finalize a list of "these require a paid license" for the outbound explanation without checking
    that assumption twice, every paid category considered (mobile foot-traffic data, consumer spending
    data, commercial real estate data, enterprise traffic data, commercial crime scoring, enhanced
    business-listings data) was re-researched for a live 2026 free tier or open alternative. Also
    checked and ruled out as genuinely not free/accessible enough to use: Google Places API and Yelp
    Fusion API (both ended meaningful free tiers in 2026), Walk Score API (free tier restricted to
    non-commercial consumer apps by its own terms), HUD's Aggregated USPS Vacant Address Data (access
    restricted to registered government/non-profit entities, not openly public), and Texas Comptroller
    local sales-tax data (published at city level only, too coarse for a per-site comparison).
16. **Real HUD LIHTC affordable-housing data - verified live before building on it.** Queried
    `egis.hud.gov/arcgis/rest/services/gotit/LIHTCProperties/MapServer/0` directly (`curl`) and
    confirmed a real, current Feature Service (1,762 Texas records at query time) before writing
    `pipeline/stages/s32_lihtc_properties.py`. Real unit counts within 1 mile of each finalist range
    from 0 to 1,189 - a genuine, differentiating signal.
17. **Real Census LEHD daytime-population data - verified live and reused already-cached routing.**
    Confirmed the Texas 2023 Workplace Area Characteristics file is live (`curl -I`) before building
    `pipeline/stages/s33_daytime_population.py`. Deliberately reused the OSRM drive-time durations
    already cached per site by script 19 rather than re-querying OSRM, since the same block-group
    prefilter and ordering script 19 and script 24 already rely on made this safe to do without a
    single new routing call. Real job counts within each finalist's 5-minute drive range from 44 to
    27,883 - a large, real, differentiating spread.
18. **Real USDA food-access data - the binary flag showed no variance for this specific candidate set,
    so the underlying continuous metric was used instead, and that decision is disclosed, not hidden.**
    The Atlas's standard "low-income AND low-access at 1mi urban/10mi rural" flag
    (`SD_SRAM_LILATracts_1And10`) read False for all 20 finalists - unsurprising, since these are
    already commercially-screened, arterial-adjacent intersections, but it meant the flag carried zero
    differentiating signal for this candidate set specifically. Checked several other real fields in
    the same Atlas file before choosing `SD_SRAM_lapophalfshare` (share of tract population beyond 0.5
    mile from a SNAP-authorized food retailer), which showed real variance (0%-31.5%) across the 20
    finalists. Both are real Atlas fields; neither threshold was invented for this project.
19. **Real Overture Maps competitor cross-check found a materially significant gap in the prior
    revision's #2 site.** Cross-checking `pipeline/stages/s35_overture_supplement.py`'s output against
    the OSM-sourced competitor data found a real Dollar General ~0.14 mi and a real Family Dollar
    ~0.24 mi from 6600 Stillwell St (the crime-revision's #2 finalist) that OSM had missed entirely -
    the OSM-only data had reported 3.03 mi and 1.01 mi respectively for those same two figures, both
    substantially wrong. Sanity-checked every one of the 54 total new finds across all 20 finalists by
    inspecting the matched brand names directly (`site_overture_supplement.csv`) before trusting the
    correction - all were exact, known chain names from the same brand list script 02 already
    classifies against, not generic substring false-positives. Folded into the scorecard's
    nearest-competitor-distance input (8 of 20 sites corrected); the Huff capture model was
    deliberately NOT re-derived against Overture data, a disclosed scope boundary (see
    `docs/methodology.md` Stage 5d), not an oversight.

## 3. Documented simplifications (disclosed, not hidden)

Every analysis makes modeling trade-offs to stay computationally tractable. The ones here are
disclosed explicitly rather than presented as more precise than they are:

- **Huff model competitor-side travel time** uses straight-line distance at an assumed 25 mph
  average urban-arterial speed, not full OSRM network routing from every block group to every
  competitor. Full routing would multiply the API call count roughly 60x for a secondary input to a
  relative comparison metric. The candidate site's own travel time - the one number that actually
  varies by which site wins - uses real OSRM network routing throughout.
- **Cannibalization trade-area overlap** uses a 1.5-mile straight-line radius around the nearest
  existing Family Dollar (rather than that store's own real drive-time isochrone) for the same
  tractability reason, mixed with the candidate's real OSRM 5-minute drive-time population.
- **Isochrone shape** is traced from 16 compass bearings × 8 candidate distances (128 sampled
  points), which can miss small dead-end pockets or one-way-street effects at that resolution - a
  strong approximation of the reachable area, not a parcel-precise flood-fill.
- **Approximate lot dimensions** (Site Details dashboard tab) are a bounding-box calculation from
  the real HCAD parcel polygon's vertices (haversine edge lengths), not a certified survey.

## 4. Real 90% confidence intervals

The Census Bureau publishes a margin of error (MOE) with every ACS estimate - it is not optional
supplementary information, it's how the Bureau itself expresses uncertainty in survey-based
estimates. This pipeline pulls and reports it rather than presenting point estimates as exact.

City-wide headline statistics (real Census place-level geography for Houston, GEOID 4835000 - not a
sum of tracts, which is the statistically correct way to get a valid city-wide margin of error):

| Statistic | Estimate | 90% MOE | 90% CI range | Source |
| --- | --- | --- | --- | --- |
| Population | 2,328,253 | ±196 | 2,328,057-2,328,449 | ACS 2024 5-yr B01003 |
| Median household income | $64,813 | ±$822 | $63,991-$65,635 | ACS 2024 5-yr B19013 |
| Poverty rate | 19.9% | ±0.4pp | 19.5%-20.3% | ACS 2024 5-yr B17001 (ratio MOE propagated) |
| Foreign-born share | 29.3% | ±0.4pp | 29.0%-29.7% | ACS 2024 5-yr B05002 (ratio MOE propagated) |
| Spanish spoken at home | 37.2% | ±0.4pp | 36.8%-37.6% | ACS 2024 5-yr C16001, population 5+ (ratio MOE propagated) |
| Average household size | 2.46 | ±0.01 | 2.45-2.47 | ACS 2024 5-yr B25010 |
| Zero-vehicle household share | 10.1% | ±0.3pp | 9.7%-10.4% | ACS 2024 5-yr B25044 (ratio MOE propagated) |
| Renter-occupied housing share | 57.9% | ±0.5pp | 57.4%-58.4% | ACS 2024 5-yr B25003 (ratio MOE propagated) |

For the three derived rates (poverty, foreign-born, Spanish-at-home), the MOE is **not** simply the
inputs' MOEs - it is propagated using the Census Bureau's own published formula for a proportion
`p = X/Y` (from *A Compass for Understanding and Using American Community Survey Data*, Appendix A):

```text
MOE_p = (1/Y) × sqrt(MOE_X² − p² × MOE_Y²)        [if the radicand is negative, use the + form instead]
```

Reproducible in `pipeline/stages/s25_extended_demographics_and_ci.py` (the first six rows) and
`pipeline/stages/s27_vehicle_tenure_demographics.py` (zero-vehicle and renter-occupied shares).

**A related, non-formal robustness check:** the 6-scenario sensitivity analysis
(`pipeline/stages/s28_sensitivity_analysis.py`) is a different kind of check than a statistical confidence
interval - it re-aggregates real per-factor scores under alternative, defensible weight vectors
rather than testing sampling uncertainty. The recommendation holds in 5 of 6 scenarios as of this
revision (up from 4 of 6 before the LIHTC/daytime-population/food-access signals were added, since
the old residential-only demand metric lost the Demand-Heavy scenario the new blended composite now
wins); full results in `docs/results.md` and the map's Scorecard tab.

**Sanity cross-check:** the citywide ACS place-level population (2,328,253) is independently close to
(within ~0.7%) the sum of ACS block-group populations whose centroid falls inside the same real city
boundary polygon (2,312,201, computed in `pipeline/stages/s17_fetch_citywide_blockgroups.py`) - two different
valid methods of estimating "Houston's population" landing within a fraction of a percent of each
other is a meaningful cross-check, not a coincidence to paper over. The residual gap is expected
(different geography vintage/methodology between a place boundary and summed block groups), not an
error.

### What does *not* carry a formal confidence interval

The **Opportunity (Gap) Score**, **Huff capture %**, and **Composite Score** are custom-built
indices this analysis constructed by combining several real inputs with judgment-based weights (e.g.
25% demand / 20% Huff capture / 15% competitive gap / 15% traffic / 15% cost / 10% flood in the
final scorecard). They are analytical tools for ranking real candidates against each other, not
Census-published population statistics - a formal statistical confidence interval does not apply to
a weighted composite the way it applies to a survey estimate, and presenting one would itself be a
fabricated precision claim. Only the raw ACS estimates in the table above carry a Census-computed
margin of error.

## 5. Houston-specific factors this analysis accounts for

- **No municipal zoning.** Houston is the only major US city without formal zoning ordinances; land
  use is instead governed by HCAD land-use codes, private deed restrictions, and the city's
  development/parking code. Practically: a site can be developed faster than in a zoned city, but a
  neighboring parcel's future use isn't zoning-guaranteed to stay compatible - worth a site visit,
  not something any public dataset can fully screen for. Houston's general off-street parking ratio
  (city code, roughly 1 space per 200-300 sq ft of retail - about 35-45 spaces for Family Dollar's
  ~8,500 sq ft prototype) is cited as informational context in the dashboard, not computed as a
  parcel-specific verified figure - a permitting check would confirm current code.
- **Flood risk.** Harris County's severe flood history (including Hurricane Harvey) is why every one
  of the 20 candidates was screened against FEMA's NFHL, with any mapped Special Flood Hazard Area
  heavily penalized in scoring (10% weight, near-zero score if inside a mapped zone).
- **Immigrant / Hispanic demographic corridors.** Real ACS variables for foreign-born share, Spanish
  spoken at home, and average household size were pulled for all 643 Houston tracts specifically
  because corridors like Gulfton, Alief, and East Houston have large immigrant, multi-generational
  households - a real, data-grounded demand driver for Family Dollar's core categories (dry grocery,
  baby products, household essentials) that median-income screening alone would miss. See the map's
  tract popups for block-level detail and the table above for the citywide figures.
- **Vehicle access and housing tenure.** Real ACS zero-vehicle household share and renter-occupied
  housing share were pulled for the same reason - a discount-retail format depends more on
  walkable/visible neighborhood presence in car-light tracts, and renter-heavy tracts skew toward the
  household-budget profile Family Dollar's core categories serve.
- **Real crime risk.** Real HPD NIBRS Part I violent/property incident counts within 0.5 mi of every
  finalist, trailing 12 months, weighted 10% in the scorecard - a genuine safety/loss-prevention
  signal for both employees and customers, and for shrink risk to the store itself (see §2, point 14).

## 6. What this analysis explicitly does not claim

Being clear about the boundary of what public data can support is itself part of not hallucinating:

- **No predicted revenue dollar figure**, anywhere (see §2, point 9).
- **A real property/violent crime metric IS produced** (see §2, point 14) - real HPD NIBRS Part I
  incident counts, not an estimate. What it does *not* claim: NIBRS incident data reflects
  *reported* crime only, not a survey of actual victimization (some crime goes unreported, and
  reporting rates can vary by neighborhood) - the same caveat that applies to any police-recorded
  crime statistic nationally, not specific to this analysis. It is also a snapshot of a trailing
  12-month window, not a long-run trend.
- **No verified deed-restriction / restrictive-covenant status** for any parcel - this requires a
  title search, which no public API provides. Flagged per-site in the Site Details dashboard tab
  rather than assumed clear.
- **No verified median-break / divided-highway ingress-egress geometry** - this requires a civil
  site plan, not public GIS data. Flagged, not guessed.
- **No engineered confirmation of 53-ft delivery-truck turning radius** - only a real, approximate
  parcel bounding-box size is reported (§3) as a directional gut-check, explicitly not a substitute
  for a civil site plan.
- **No claim of exhaustive OSM competitor coverage citywide**, though this revision closes the gap for
  the 20 finalists specifically. OpenStreetMap tagging completeness varies - Ross Dress for Less
  returned only 1 citywide match despite operating more Houston locations, almost certainly an OSM
  tagging gap rather than a real store count. §2 item 19's Overture Maps cross-check found 54 real
  competitor locations near the 20 finalists that OSM had missed (including a materially significant
  find near the prior revision's #2 site) and corrected 8 sites' scores accordingly - but that check
  only covered a 1-mile radius around each of the 20 finalists, not the full city, so citywide OSM
  completeness beyond that radius is still not claimed.
- **This is a desk-based screening exercise.** A final go/no-go still requires a site visit, a
  title/zoning check, and formal traffic-engineering sign-off - this analysis is built to make that
  final diligence faster and better-targeted, not to replace it. Full roadmap, organized by whether
  each gap is a data-availability constraint or a structural boundary (title search, engineering
  sign-off, site visit): [`limitations_and_diligence.md`](limitations_and_diligence.md).
