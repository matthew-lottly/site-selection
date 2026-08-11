# Methodology — Houston Family Dollar Site Selection (Citywide)

**Author:** Matthew Powers · **Prompt:** GIS Analyst case study, Location Intelligence team
**Scope:** Identify and recommend a new Family Dollar store site anywhere in the City of Houston,
TX market, using only free, public, open data and open-source tools, and communicate the
recommendation to a non-technical Real Estate VP.

Every figure in this analysis and on the accompanying web map (`index.html`) is pulled live from a
public API or dataset — nothing is fabricated or hand-typed, and every number attached to the
recommended site has been independently re-verified against the live source API (not just the
cached pipeline output) before being reported. The full pipeline is reproducible: run the numbered
scripts in `scripts/` in order (see `README.md`).

**This is the citywide revision of the analysis.** An earlier draft screened Harris County broadly
but then only sourced and compared candidate parcels inside one neighborhood (Sunnyside). That was
a real gap: a "best site in Houston" claim needs candidates sourced from across the whole city, not
just the first promising area found. This version fixes that — see Stage 2 below.

## 1. Data sources (all free, all keyless)

| # | Source | What it provides | Access method |
|---|--------|-------------------|----------------|
| 1 | US Census Bureau TIGERweb | Census tract & block group boundaries, and the real City of Houston incorporated-place boundary | ArcGIS REST (`tigerweb.geo.census.gov`) |
| 2 | Census Reporter API | ACS 2024 5-year estimates: population, median household income, poverty status | REST API (wraps Census Bureau ACS) |
| 3 | OpenStreetMap / Overpass API | Competitor & anchor retail locations (13 real banners found), arterial road network | Overpass QL |
| 4 | Harris County Appraisal District (HCAD) | Real parcel boundaries, acreage, land use class, land/building/appraised value, situs address | ArcGIS REST (`gis.hctx.net`) |
| 5 | FEMA National Flood Hazard Layer (NFHL) | Flood zone designation (X, AE, etc.) at a point | ArcGIS REST identify/query (`hazards.fema.gov`) |
| 6 | TxDOT | Annual Average Daily Traffic (AADT) counts, current (2025) | ArcGIS Online Feature Service |
| 7 | OSRM (Open Source Routing Machine) | Real drive times over the OpenStreetMap road network | Public routing API |
| 8 | Nominatim (OpenStreetMap) | Reverse geocoding — confirms each site's real neighborhood and verifies what road each traffic count and each parcel actually sits on | REST API |

No Census API key, Google Maps key, or paid GIS license was used or required.

## 2. Pipeline stages

### Stage 1 — Macro market screen (all of Harris County)
`scripts/01_fetch_tracts.py`, `02_fetch_competitors.py`, `03_gap_analysis.py`

- Pulled **all 1,115 Census tracts in Harris County** with ACS 5-year population, median household
  income, and poverty rate.
- Pulled **every current dollar-store, off-price/general-merchandise, and grocery/big-box location**
  from OpenStreetMap across the county: Family Dollar, Dollar General, Dollar Tree (direct
  competitors, 156 found); Walmart, Target, Burlington, Five Below, Ross (off-price/general
  merchandise, 147 found); Kroger, H-E-B, Aldi, Fiesta Mart, Food Town (grocery anchors, 213 found)
  — 516 real stores in total.
- Scored every tract with a transparent **opportunity ("gap") index**:

  ```
  demand_index          = population × income_fit(median_HH_income) × (1 + poverty_rate)
  competitive_gap_index  = min(distance_to_nearest_dollar_store_mi, 3.0) / 3.0
  gap_score              = demand_index × competitive_gap_index
  ```

  `income_fit()` peaks (weight = 1.0) for tracts with median household income between $20k and $55k
  — the band that indexes most strongly to discount/value retail — tapering to zero outside roughly
  $0–$80k, so very low-income (unstable trade area) and affluent (better served by Target/Walmart)
  tracts are both discounted.

### Stage 2 — Citywide submarket scoping (the fix)
`scripts/13_houston_scope_clusters.py`

- Pulled the **real City of Houston boundary** (TIGERweb Incorporated Places, GEOID 4835000) — a
  genuinely irregular polygon (100 rings, ~70,800 source vertices, reflecting Houston's real
  annexation-driven shape) — rather than using all of Harris County, which also contains separate
  incorporated cities (Pasadena, Baytown, Pearland, Katy) that are not "Houston, TX."
- Kept only the **643 of 1,115 Harris County tracts** whose centroid actually falls inside city
  limits.
- Rather than committing to the single highest-scoring tract cluster, grid-clustered the top-scoring
  tracts and kept the **10 strongest opportunity clusters at least 2.75 miles apart**, so the
  candidate search spans geographically distinct parts of the city instead of one neighborhood.
  Each cluster was reverse-geocoded to a real Houston neighborhood name: **Alief, Westchase,
  Sunnyside, Gulfton, Braeswood/Sunnyside corridor, Denver Harbor, East Houston, Braeburn, Acres
  Homes, and Central Southwest Houston.**

### Stage 3 — Candidate site identification, all 10 areas
`scripts/14_find_intersections_citywide.py`, `15_fetch_parcels_citywide.py`

- For each of the 10 opportunity areas, auto-discovered that area's named primary/secondary
  arterial roads directly from OpenStreetMap (no hand-picked street lists) and found real
  intersections between them via spatial grid-bucketing — **100 real intersections across the city.**
- Queried **real HCAD parcels within ~350m of every intersection**, filtered to realistic new-store
  sites (vacant commercial land, or under-improved commercial land where the building is worth less
  than 60% of the land — a teardown/redevelopment opportunity), sized 0.4–4.0 acres.
- Screened out parcels appraising under $15,000/acre — these turned out to be HOA common areas,
  drainage reserves, and right-of-way slivers miscoded as vacant commercial land in HCAD, not real
  buildable sites (a data-quality check, not a business filter).
- This produced **275 real, addressed parcels** with actual HCAD account numbers. Kept the best 2
  per opportunity area (closest to a ~1.2-acre typical footprint, preferring shovel-ready vacant
  land) as the finalist shortlist — **20 real candidate sites spanning all 10 neighborhoods.**

### Stage 4 — Site enrichment
`scripts/16_fetch_citywide_aadt.py`, `17_fetch_citywide_blockgroups.py`, `18_enrich_sites_citywide.py`

For each of the 20 finalists:
- **FEMA flood zone** at the exact parcel point (NFHL identify query).
- **Verified traffic count**: nearest TxDOT AADT station. TxDOT records roads by route number (e.g.
  `FM0865`), not local name, and a station can sit directly on a limited-access freeway a store could
  never have a driveway onto — so every match's coordinates were reverse-geocoded to a real street
  name, and any station whose name resolved to a freeway/tollway/loop was rejected in favor of the
  nearest genuine arterial station (falling back to a conservative citywide-minimum estimate, never
  the freeway's inflated count, for the 3 sites where no arterial station exists nearby).
- **Neighborhood identity**: each site's own coordinates were independently reverse-geocoded rather
  than inheriting its search cluster's label, since one cluster's search radius can span more than
  one named neighborhood.
- **Competitive distances**: straight-line distance to the nearest direct dollar-store competitor,
  nearest off-price/general-merchandise store, and nearest grocery/big-box anchor.
- **Real drive-time trade area**: queried OSRM (actual road-network routing, not a circle buffer)
  from each site to every one of Houston's **1,603 Census block groups (2,312,201 people — matches
  Houston's real published population)** within a 10-mile prefilter, and summed ACS population
  reachable within a 5-minute and a 10-minute drive.

### Stage 5 — Huff gravity market-capture model
`scripts/19_drive_times_and_huff.py`

For each site, estimated a relative market-capture percentage using the classic **Huff gravity
model**: for every block group in the site's drive-time trade area, the candidate's pull is compared
against every real nearby **direct dollar-store competitor** (Family Dollar, Dollar General, Dollar
Tree), using each banner's published typical prototype square footage as the size/attraction term
and a distance-decay exponent of β = 2.0 (the standard value in retail gravity-model literature):

```
P(choose site j | block group i) = (Sⱼ / Dᵢⱼ^β) / Σₖ (Sₖ / Dᵢₖ^β)
```

Full grocery/big-box anchors (Walmart, H-E-B, Kroger, Target) were deliberately **excluded** from
the competitive set: they serve a different shopping mission (a weekly grocery trip vs. a quick
value/convenience trip), and their much larger square footage mathematically swamps every
candidate's share to a uniform near-zero number regardless of where the store actually sits — that
was tested and confirmed before this design choice was made. This mirrors how real dollar-store
site selection evaluates cannibalization: against same-format competitors, not the whole retail
landscape.

Candidate-site travel time (`Dᵢⱼ`) uses real OSRM network minutes. Competitor travel time (`Dᵢₖ`) is
approximated from straight-line distance at a 25 mph average urban-arterial speed — a documented
simplification made to keep the API call count tractable across 20 sites × ~1,600 block groups, not
a fabricated number. **This produces a relative, population-weighted capture percentage per site —
not a predicted revenue dollar figure**, since no public store-level sales data exists to calibrate
one; a dollar forecast built without real sales data to ground it would itself be a fabricated
number, so this analysis deliberately stops at a defensible relative comparison instead.

### Stage 6 — Weighted scorecard
`scripts/20_score_sites_citywide.py`

Each metric was min-max normalized across the 20 finalists (0–100) and combined with documented
weights:

| Factor | Weight | Rationale |
|---|---|---|
| Trade-area demand (5-min drive population × income fit) | 25% | Rooftops within an easy drive, weighted toward the $20k–$55k core customer band |
| Huff market-capture % | 20% | Comprehensive, distance- and size-weighted competitive pull against direct competitors |
| Competitive white space (distance to nearest dollar store) | 15% | Simple, exec-legible cross-check on the Huff score; avoids cannibalization |
| Traffic & visibility (verified AADT) | 15% | Passive visibility drives real discount-retail traffic; freeway mainlane counts excluded |
| Site feasibility & cost (land value/acre, vacant-land bonus) | 15% | Lower acquisition cost and shovel-ready land reduce time-to-open |
| Flood risk (FEMA zone) | 10% | Any mapped Special Flood Hazard Area is heavily penalized |

An industry rule-of-thumb **8,000 AADT minimum viable-traffic benchmark** is also flagged per site
(pass/fail column in the scorecard) so a reviewer can see at a glance which finalists clear it,
independent of the weighted score.

### Stage 7 — Trade-area visualization
`scripts/21_fetch_houston_tract_geometry.py`, existing isochrone logic

Built a real 5-minute / 10-minute drive-time isochrone for the recommended site by querying OSRM
along 16 compass bearings at 8 candidate distances each, keeping the farthest point on each bearing
still under the time threshold — the actual reachable shape given the real road network, not a
generic circle. Pulled tract polygon geometry for all 643 Houston-city tracts (simplified for file
size with Douglas-Peucker line simplification, ~9x fewer vertices, no change to the underlying
values) so the map's opportunity choropleth covers the whole city that was actually screened.

### Stage 8 — Web map
`scripts/22_generate_map_citywide.py`

Built with Folium (Python) on top of Leaflet.js — 100% open source, no API key, deployable as a
static file to GitHub Pages. Layers: real Houston city-limits boundary, citywide opportunity
choropleth (643 tracts), competitors split into 3 toggleable tiers, all 20 candidate sites on a
validated best→worst color ramp (green→red), the 10 opportunity areas searched, and the real
drive-time trade area for the recommended site. A basemap switcher offers 5 free tile providers
(light, dark, streets, satellite, terrain). Every marker popup cites its data source.

## 3. Known limitations

- ACS 5-year estimates (2020–2024) carry margins of error, especially at the block-group level;
  they are directional, not survey-grade for a single block.
- The Huff model's competitor-side travel time is a straight-line/speed-assumption approximation,
  not full OSRM routing from every block group to every competitor (see Stage 5) — a documented
  tractability trade-off, not a fabricated number.
- The isochrone is generated from 16 rays × 8 distances (128 points), which can miss small dead-end
  pockets or one-way-street effects; it is a strong approximation, not a parcel-precise flood-fill.
- Overpass/OSM competitor and road data reflect current OSM tagging completeness. It is generally
  strong in Houston but not exhaustive — e.g., Ross Dress for Less returned only 1 match despite
  operating more locations in Houston, almost certainly an OSM tagging gap rather than a real count;
  reported as-is rather than patched with an estimate.
- No revenue forecast is produced (see Stage 5) — no public store-level sales data exists to
  calibrate one.
- This is a desk-based screening exercise. A final go/no-go would still require a site visit, a
  title/zoning check, and formal traffic-engineering sign-off.
