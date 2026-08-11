# Data Validation & Statistical Rigor — Houston Family Dollar Site Selection

This document exists to answer one question directly: **how do we know this analysis isn't making
things up?** It catalogs every data source, every number's provenance, every audit step actually
performed, the real confidence intervals behind the headline statistics, and — just as important —
what the analysis explicitly does *not* claim, because no public data supports it.

Companion documents: [`methodology.md`](methodology.md) (how the pipeline works, stage by stage) and
[`results.md`](results.md) (the recommendation and scorecard). The interactive map's **Analysis
Dashboard** drawer (bottom of `index.html`) surfaces the same scorecard, cannibalization table,
confidence intervals, and this validation summary live, sourced from the same CSV files referenced
here.

## 1. Full source catalog

| Source | What it provides | Access | Cost / auth |
|---|---|---|---|
| US Census Bureau TIGERweb | Tract & block-group boundaries; the real City of Houston incorporated-place boundary | ArcGIS REST, `tigerweb.geo.census.gov` | Free, no key |
| Census Reporter API | ACS 2024 5-year estimates **and margins of error** for population, income, poverty, foreign-born status, language spoken at home, household size | REST API wrapping the Census Bureau ACS | Free, no key |
| OpenStreetMap / Overpass API | 528 real competitor/anchor locations across 15 banners; arterial road network; posted speed limits; co-tenant POIs (gas stations, laundromats, schools, post offices, pharmacies) | Overpass QL | Free, no key |
| Harris County Appraisal District (HCAD) | Real parcel boundaries, acreage, land-use class, land/building/appraised value, situs address | ArcGIS REST, `gis.hctx.net` | Free, no key |
| FEMA National Flood Hazard Layer (NFHL) | Flood zone designation at a point | ArcGIS REST identify, `hazards.fema.gov` | Free, no key |
| TxDOT | Annual Average Daily Traffic (AADT), 2025 counts | ArcGIS Online Feature Service | Free, no key |
| OSRM (Open Source Routing Machine) | Real drive times over the OpenStreetMap road network | Public routing API | Free, no key |
| Nominatim (OpenStreetMap) | Reverse geocoding — road identity, neighborhood identity | REST API | Free, no key, rate-limited to 1 req/sec (respected throughout) |

No Census API key, Google Maps key, or paid GIS/mobility-data license (SafeGraph, Placer.ai, Esri)
was used or is required to reproduce this analysis.

## 2. Specific hallucination/error checks actually performed

These are not generic assurances — each one is a concrete thing that was checked, and in three
cases, a real problem that was found and fixed.

1. **Live re-verification of the winning site.** After the pipeline produced its recommendation,
   the HCAD parcel record, FEMA flood zone, and TxDOT AADT count for that exact site were
   independently re-queried directly against the source APIs (not the pipeline's cached output) and
   matched, before the recommendation was finalized.
2. **AADT road identity verification.** TxDOT records traffic counts by route number (e.g.
   `FM0865`), not local street name. Every AADT match used in scoring was reverse-geocoded to a real
   street name to confirm identity (e.g., confirming `FM0865` really is Cullen Blvd). Stations whose
   coordinates resolved to a freeway or tollway — which a retail pad cannot legally have a driveway
   onto — were rejected in favor of the nearest genuine arterial-road reading, with a fallback flag
   for the 3 sites where no arterial station exists nearby (their traffic score uses a conservative
   citywide-minimum estimate, never the inflated freeway figure).
3. **Independent per-site neighborhood verification.** Each finalist's neighborhood name was
   reverse-geocoded from its own coordinates rather than inherited from the macro search cluster
   that found it. This mattered: one site (now the recommended one) was initially mislabeled
   "Braeswood" because its search cluster's centroid sat in Braeswood, even though the specific
   parcel — on Cullen Blvd, subdivision "East Sunnyside Court" — is really in Sunnyside. Fixed by
   re-geocoding every site individually.
4. **HCAD data-quality filter.** Several parcels that queried as "vacant commercial land" (state
   class C1/C2) appraised at $900–$5,000 total for 0.4–2+ acres — economically impossible for real
   commercial land (that's a few cents per square foot). Inspection showed these were HOA common
   areas, drainage/detention easements, and right-of-way remnants miscoded in HCAD, not real
   buildable sites. Filtered out with a $15,000/acre floor.
5. **Cross-cluster duplicate check.** Two adjacent macro search areas can find the same real parcel
   near their shared border. Deduplicated globally by HCAD account number so no site is counted, or
   could win, twice.
6. **Stale-data bug caught by cross-checking.** After the analysis was rebuilt to search citywide
   instead of one neighborhood, the map's drive-time isochrone briefly still showed the *previous*
   draft's recommended site's shape rather than the new one's — a stale cache file the map script
   read without re-validating. Caught by checking the isochrone file's embedded site label against
   the live scorecard winner, and fixed by making the isochrone script always re-derive from the
   current scorecard's top row rather than trusting a cached file blindly.
7. **Dead-code / silently-broken field removed.** An early version of the macro gap-analysis script
   computed a "nearest anchor" distance for every tract that was always exactly 99.0 miles — a
   placeholder that was never real, caused by a category-name mismatch (`"anchor"` vs. the real
   category name), and had gone unnoticed because nothing downstream actually used the value. Found
   during this audit and removed rather than left in the output.
8. **AADT-benchmark scoring gate.** The weighted scorecard alone let a site with only 1,547 vehicles
   per day (a real, low reading) outscore the actual recommendation on raw points, because traffic
   is only 15% of the composite weight. Rather than let a soft-weighted average paper over a site
   that fails a real industry minimum-viable-traffic threshold (8,000 AADT), the scoring logic now
   explicitly gates the *primary recommendation* to the top-scoring site that also clears that
   threshold — the higher-raw-score, benchmark-failing site is kept visible in the scorecard for
   transparency, tagged, but is not selectable as "the" recommendation.
9. **No revenue dollar figure, anywhere.** Neither the Huff gravity model nor the cannibalization
   analysis produces a predicted-sales dollar amount. Family Dollar does not publish store-level
   sales data, so no model here is calibrated against real revenue — a dollar figure would be a
   fabricated number wearing a precise mask. Both analyses stop at real, computed, relative metrics
   instead (market-capture percentage; net-new population reach) that answer the same underlying
   business question without inventing a number.

## 3. Documented simplifications (disclosed, not hidden)

Every analysis makes modeling trade-offs to stay computationally tractable. The ones here are
disclosed explicitly rather than presented as more precise than they are:

- **Huff model competitor-side travel time** uses straight-line distance at an assumed 25 mph
  average urban-arterial speed, not full OSRM network routing from every block group to every
  competitor. Full routing would multiply the API call count roughly 60x for a secondary input to a
  relative comparison metric. The candidate site's own travel time — the one number that actually
  varies by which site wins — uses real OSRM network routing throughout.
- **Cannibalization trade-area overlap** uses a 1.5-mile straight-line radius around the nearest
  existing Family Dollar (rather than that store's own real drive-time isochrone) for the same
  tractability reason, mixed with the candidate's real OSRM 5-minute drive-time population.
- **Isochrone shape** is traced from 16 compass bearings × 8 candidate distances (128 sampled
  points), which can miss small dead-end pockets or one-way-street effects at that resolution — a
  strong approximation of the reachable area, not a parcel-precise flood-fill.
- **Approximate lot dimensions** (Site Details dashboard tab) are a bounding-box calculation from
  the real HCAD parcel polygon's vertices (haversine edge lengths), not a certified survey.

## 4. Real 90% confidence intervals

The Census Bureau publishes a margin of error (MOE) with every ACS estimate — it is not optional
supplementary information, it's how the Bureau itself expresses uncertainty in survey-based
estimates. This pipeline pulls and reports it rather than presenting point estimates as exact.

City-wide headline statistics (real Census place-level geography for Houston, GEOID 4835000 — not a
sum of tracts, which is the statistically correct way to get a valid city-wide margin of error):

| Statistic | Estimate | 90% MOE | 90% CI range | Source |
|---|---|---|---|---|
| Population | 2,328,253 | ±196 | 2,328,057 – 2,328,449 | ACS 2024 5-yr B01003 |
| Median household income | $64,813 | ±$822 | $63,991 – $65,635 | ACS 2024 5-yr B19013 |
| Poverty rate | 19.9% | ±0.4pp | 19.5% – 20.3% | ACS 2024 5-yr B17001 (ratio MOE propagated) |
| Foreign-born share | 29.3% | ±0.4pp | 29.0% – 29.7% | ACS 2024 5-yr B05002 (ratio MOE propagated) |
| Spanish spoken at home | 37.2% | ±0.4pp | 36.8% – 37.6% | ACS 2024 5-yr C16001, population 5+ (ratio MOE propagated) |
| Average household size | 2.46 | ±0.01 | 2.45 – 2.47 | ACS 2024 5-yr B25010 |

For the three derived rates (poverty, foreign-born, Spanish-at-home), the MOE is **not** simply the
inputs' MOEs — it is propagated using the Census Bureau's own published formula for a proportion
`p = X/Y` (from *A Compass for Understanding and Using American Community Survey Data*, Appendix A):

```
MOE_p = (1/Y) × sqrt(MOE_X² − p² × MOE_Y²)        [if the radicand is negative, use the + form instead]
```

Reproducible in `scripts/25_extended_demographics_and_ci.py`.

**Sanity cross-check:** the citywide ACS place-level population (2,328,253) is independently close to
(within ~0.7%) the sum of ACS block-group populations whose centroid falls inside the same real city
boundary polygon (2,312,201, computed in `scripts/17_fetch_citywide_blockgroups.py`) — two different
valid methods of estimating "Houston's population" landing within a fraction of a percent of each
other is a meaningful cross-check, not a coincidence to paper over. The residual gap is expected
(different geography vintage/methodology between a place boundary and summed block groups), not an
error.

### What does *not* carry a formal confidence interval

The **Opportunity (Gap) Score**, **Huff capture %**, and **Composite Score** are custom-built
indices this analysis constructed by combining several real inputs with judgment-based weights (e.g.
25% demand / 20% Huff capture / 15% competitive gap / 15% traffic / 15% cost / 10% flood in the
final scorecard). They are analytical tools for ranking real candidates against each other, not
Census-published population statistics — a formal statistical confidence interval does not apply to
a weighted composite the way it applies to a survey estimate, and presenting one would itself be a
fabricated precision claim. Only the raw ACS estimates in the table above carry a Census-computed
margin of error.

## 5. Houston-specific factors this analysis accounts for

- **No municipal zoning.** Houston is the only major US city without formal zoning ordinances; land
  use is instead governed by HCAD land-use codes, private deed restrictions, and the city's
  development/parking code. Practically: a site can be developed faster than in a zoned city, but a
  neighboring parcel's future use isn't zoning-guaranteed to stay compatible — worth a site visit,
  not something any public dataset can fully screen for. Houston's general off-street parking ratio
  (city code, roughly 1 space per 200–300 sq ft of retail — about 35–45 spaces for Family Dollar's
  ~8,500 sq ft prototype) is cited as informational context in the dashboard, not computed as a
  parcel-specific verified figure — a permitting check would confirm current code.
- **Flood risk.** Harris County's severe flood history (including Hurricane Harvey) is why every one
  of the 20 candidates was screened against FEMA's NFHL, with any mapped Special Flood Hazard Area
  heavily penalized in scoring (10% weight, near-zero score if inside a mapped zone).
- **Immigrant / Hispanic demographic corridors.** Real ACS variables for foreign-born share, Spanish
  spoken at home, and average household size were pulled for all 643 Houston tracts specifically
  because corridors like Gulfton, Alief, and East Houston have large immigrant, multi-generational
  households — a real, data-grounded demand driver for Family Dollar's core categories (dry grocery,
  baby products, household essentials) that median-income screening alone would miss. See the map's
  tract popups for block-level detail and the table above for the citywide figures.

## 6. What this analysis explicitly does not claim

Being clear about the boundary of what public data can support is itself part of not hallucinating:

- **No predicted revenue dollar figure**, anywhere (see §2, point 9).
- **No verified deed-restriction / restrictive-covenant status** for any parcel — this requires a
  title search, which no public API provides. Flagged per-site in the Site Details dashboard tab
  rather than assumed clear.
- **No verified median-break / divided-highway ingress-egress geometry** — this requires a civil
  site plan, not public GIS data. Flagged, not guessed.
- **No engineered confirmation of 53-ft delivery-truck turning radius** — only a real, approximate
  parcel bounding-box size is reported (§3) as a directional gut-check, explicitly not a substitute
  for a civil site plan.
- **No claim of exhaustive OSM competitor coverage.** OpenStreetMap tagging completeness varies; for
  example, Ross Dress for Less returned only 1 match despite operating more Houston locations,
  almost certainly an OSM tagging gap rather than a real store count. Reported as pulled, not patched
  with an estimate.
- **This is a desk-based screening exercise.** A final go/no-go still requires a site visit, a
  title/zoning check, and formal traffic-engineering sign-off — this analysis is built to make that
  final diligence faster and better-targeted, not to replace it.
