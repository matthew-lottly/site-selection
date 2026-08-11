# Methodology — Houston Family Dollar Site Selection

**Author:** Matthew Powers · **Prompt:** GIS Analyst case study, Location Intelligence team
**Scope:** Identify and recommend a new Family Dollar store site in the Houston, TX market, using
only free, public, open data and open-source tools, and communicate the recommendation to a
non-technical Real Estate VP.

Every figure in this analysis and on the accompanying web map (`index.html`) is pulled live from a
public API or dataset — nothing is fabricated or hand-typed. The full pipeline is reproducible: run
`scripts/01_fetch_tracts.py` through `scripts/12_generate_map.py` in order (see `README.md`).

## 1. Data sources (all free, all keyless)

| # | Source | What it provides | Access method |
|---|--------|-------------------|----------------|
| 1 | US Census Bureau TIGERweb | Census tract & block group boundaries | ArcGIS REST (`tigerweb.geo.census.gov`) |
| 2 | Census Reporter API | ACS 2024 5-year estimates: population, median household income, poverty status, SNAP receipt | REST API (wraps Census Bureau ACS) |
| 3 | OpenStreetMap / Overpass API | Existing Family Dollar / Dollar General / Dollar Tree locations; grocery & big-box anchors; named arterial roads | Overpass QL |
| 4 | Harris County Appraisal District (HCAD) | Real parcel boundaries, acreage, land use class, land/building/appraised value, situs address | ArcGIS REST (`gis.hctx.net`) |
| 5 | FEMA National Flood Hazard Layer (NFHL) | Flood zone designation (X, AE, etc.) at a point | ArcGIS REST identify/query (`hazards.fema.gov`) |
| 6 | TxDOT Annual Average Daily Traffic (AADT) | Real, current (2025) traffic counts on state-monitored roads | ArcGIS Online Feature Service |
| 7 | OSRM (Open Source Routing Machine) | Real drive times over the OpenStreetMap road network | Public routing API |
| 8 | Nominatim (OpenStreetMap) | Reverse geocoding, used to confirm neighborhood identity and to confirm TxDOT route-number-to-street mappings (e.g., FM 865 = Cullen Blvd) | REST API |

No Census API key, Google Maps key, or paid GIS license was used or required.

## 2. Pipeline stages

### Stage 1 — Macro market screen (county-wide)
`scripts/01_fetch_tracts.py`, `02_fetch_competitors.py`, `03_gap_analysis.py`

- Pulled **all 1,115 Census tracts in Harris County** with ACS 5-year population, median household
  income, and poverty rate.
- Pulled **every current Family Dollar, Dollar General, and Dollar Tree location in Harris County**
  from OpenStreetMap (154 stores found), plus 289 grocery/big-box anchors (Walmart, Target, Kroger,
  H-E-B, Aldi, Fiesta Mart) for co-tenancy context.
- Scored every tract with a transparent **opportunity ("gap") index**:

  ```
  demand_index         = population × income_fit(median_HH_income) × (1 + poverty_rate)
  competitive_gap_index = min(distance_to_nearest_dollar_store_mi, 3.0) / 3.0
  gap_score             = demand_index × competitive_gap_index
  ```

  `income_fit()` peaks (weight = 1.0) for tracts with median household income between $20k and $55k
  — the demographic band that indexes most strongly to discount/value retail — and tapers to zero
  outside roughly $0–$80k, so very low-income (unstable trade area) and affluent (better served by
  Target/Walmart) tracts are both discounted.
- Grouped the top-scoring tracts geographically (grid clustering) rather than picking single tracts
  in isolation, because a real trade area spans several adjoining tracts.

### Stage 2 — Submarket selection
`scripts/04_define_submarket.py`

The single strongest, most defensible cluster was a ~3×3 mile corridor in **Sunnyside / South
Union**, South Houston (confirmed by reverse-geocoding the cluster centroid). Four of the top ten
county-wide tract clusters sit inside this corridor, and it contains **zero existing Family Dollar,
Dollar General, or Dollar Tree locations** — verified directly against the OSM competitor pull, not
inferred. Sunnyside is also a long-documented, real Houston neighborhood (a City of Houston
Complete Communities target area), not a statistical artifact of the scoring formula.

Submarket stats (79 Census tracts, ACS 2024 5-yr):
- Population: **283,962**
- Average median household income: **$60,670** (tract average; large variance within the corridor)
- Average poverty rate: **24.6%**

Pulled real tract and block-group polygon geometry for the submarket (for the map choropleth and
population-weighted trade-area calculations) and every TxDOT AADT count station inside it (76
stations, 2025 counts).

### Stage 3 — Candidate site identification
`scripts/05_find_intersections.py`, `06_fetch_parcels.py`

Rather than guessing candidate addresses, the pipeline found **real intersections** of Sunnyside's
named arterials (Cullen Blvd, Martin Luther King Jr Blvd, Scott St, Old Spanish Trail, Reed Rd,
Mykawa Rd) by pulling their OSM way geometry and computing where different roads' vertices come
within ~185 ft of each other — the same corner-lot logic a site selector uses when scanning a road
atlas. This produced 6 real intersections.

At each intersection, queried **HCAD parcels within ~350m** and filtered to realistic new-store
sites:
- `state_class` C1/C2 ("vacant land tract") — shovel-ready land, **or**
- `state_class` F1 ("commercial, improved") where building value is under 60% of land value — a
  teardown/redevelopment opportunity
- 0.4–4.0 acres (a freestanding ~8,000–10,000 sq ft discount-store pad is typically 0.75–1.5 acres;
  the range was left wide enough to catch smaller infill lots realistic for a dense urban corridor)

This produced 29 real, addressed parcels with actual HCAD account numbers, appraised values, and
acreage. One representative site was selected per intersection (5 of the 6 intersections had
qualifying parcels) to build the finalist shortlist — **Sites A through E**.

### Stage 4 — Site enrichment
`scripts/07_fetch_blockgroup_demo.py`, `08_enrich_sites.py`, `09_drive_times.py`

For each of the 5 finalist sites:
- **FEMA flood zone** at the exact parcel point (NFHL identify query).
- **Traffic count**: nearest TxDOT AADT station on the road the site fronts. TxDOT records roads by
  route number (e.g., `FM0865`), not local name, so each match was verified by reverse-geocoding the
  station coordinates (confirmed `FM0865` = Cullen Blvd, `UA0090` = Old Spanish Trail). For two
  sites the nearest labeled station was ~0.8 mi away on an unnamed local segment — reported as
  corridor-representative rather than exact-frontage traffic.
- **Competitive distance**: straight-line distance to the nearest existing dollar-store competitor
  and nearest grocery/big-box anchor (OSM).
- **Real drive-time trade area**: queried OSRM (actual road-network routing, not a circle buffer) for
  driving duration from each site to all 170 block-group population centroids in the submarket, and
  summed ACS population reachable within a 5-minute and a 10-minute drive.
- **Trade-area income fit**: population-weighted median household income of the block groups inside
  each site's 5-minute drive area.

### Stage 5 — Weighted scorecard
`scripts/10_score_sites.py`

Each metric was min-max normalized across the 5 finalists (0–100) and combined with weights chosen
to reflect what actually drives a discount-retail site decision, and documented so the weighting can
be challenged:

| Factor | Weight | Rationale |
|---|---|---|
| Trade-area demand (5-min drive population × income fit) | 30% | Rooftops within an easy drive, weighted toward the $20k–$55k core customer band |
| Competitive white space (distance to nearest existing dollar store) | 25% | Avoids cannibalizing an existing FD/DG/DT and confirms an underserved gap |
| Traffic & visibility (AADT) | 20% | Passive visibility drives a meaningful share of discount-retail traffic |
| Site feasibility & cost (land value/acre, vacant-land bonus) | 15% | Lower acquisition cost and shovel-ready (vacant) land reduce time-to-open |
| Flood risk (FEMA zone) | 10% | Any mapped Special Flood Hazard Area is heavily penalized (insurance cost, build risk) |

### Stage 6 — Trade-area visualization
`scripts/11_isochrone.py`

Built a real 5-minute / 10-minute drive-time isochrone for the recommended site by querying OSRM
along 16 compass bearings at 8 candidate distances each (a single batched request), keeping the
farthest point on each bearing still under the time threshold. This traces the actual reachable
shape given the real road network, rather than a generic circle.

### Stage 7 — Web map
`scripts/12_generate_map.py`

Built with Folium (Python) on top of Leaflet.js and CartoDB Positron basemap tiles — 100% open
source, no API key, deployable as a static file to GitHub Pages. Layers: submarket opportunity
choropleth, competitors, anchors, 5 candidate sites (winner highlighted), and the real drive-time
trade area for the recommended site. Every marker popup cites its data source.

## 3. Known limitations

- ACS 5-year estimates (2020–2024) carry margins of error, especially at the block-group level;
  they are directional, not survey-grade for a single block.
- TxDOT AADT stations are not present on every residential block; two of the five finalist sites
  are matched to a same-corridor count ~0.8 mi away rather than an exact-frontage count.
- The isochrone is generated from 16 rays × 8 distances (128 points), which can miss small dead-end
  pockets or one-way-street effects; it is a strong approximation, not a parcel-precise flood-fill.
- Overpass/OSM competitor and road data reflect current OSM tagging completeness, which is generally
  strong in Houston but not guaranteed exhaustive (e.g., a very recently opened or closed store may
  lag).
- This is a desk-based screening exercise. A final go/no-go would still require a site visit,
  a title/zoning check, and formal traffic-engineering sign-off.
