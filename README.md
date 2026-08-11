# Houston Family Dollar Site Selection

An end-to-end, reproducible, **citywide** GIS site-selection pipeline for a new Family Dollar
location in Houston, TX - built entirely from free, public, key-free data sources. Prepared as a
Location Intelligence / GIS Analyst case study.

**Recommendation:** 6600 Stillwell St, Pecan Park, Houston, TX - selected from 20 real candidate
sites spanning 10 Houston neighborhoods. See [`docs/results.md`](docs/results.md) for the full
scorecard, reasoning, and the one real trade-off (cannibalization risk vs. the close #2 finalist),
[`docs/methodology.md`](docs/methodology.md) for how the pipeline works,
[`docs/data_validation.md`](docs/data_validation.md) for the full source catalog, every audit check
performed (including a bug the sensitivity analysis caught that changed the recommendation), and
real 90% confidence intervals, and
[`docs/limitations_and_diligence.md`](docs/limitations_and_diligence.md) for what a desk analysis
can't verify and the concrete next steps that close that gap.

**Interactive map:** [`index.html`](index.html) - open locally or view on GitHub Pages once
published. App-shell layout: a header bar up top and a right-side **Analysis Dashboard** panel
(toggle button in the header) with the full scorecard, sensitivity analysis, cannibalization math,
site-level operational detail, and confidence intervals - the map stays visible and interactive
alongside it.

## Data sources (all free, no API keys)

- US Census Bureau - TIGERweb (tract/block-group boundaries + the real City of Houston boundary) +
  Census Reporter API (ACS 2024 5-yr demographics, incl. margins of error, vehicle access, and
  housing tenure)
- OpenStreetMap / Overpass API - 528 competitor/anchor locations across 15 banners, arterial road
  network, posted speed limits, transit stops, co-tenant POIs
- Harris County Appraisal District (HCAD) - real parcel boundaries, land use, appraised value
- FEMA National Flood Hazard Layer (NFHL) - flood zone identification
- TxDOT - Annual Average Daily Traffic (AADT) counts, verified by reverse-geocoding each station
- OSRM - real drive-time routing over the OpenStreetMap road network, a real Huff gravity
  market-capture model, and a real cannibalization/trade-area-overlap analysis

Property crime was investigated as a candidate metric and confirmed unavailable as a free, queryable
dataset for Houston - documented as a real limitation rather than estimated. See
`docs/limitations_and_diligence.md`.

## Repository structure

- `scripts/` - the pipeline, run in numeric order; `lib.py` holds shared HTTP/geometry/color
  helpers. Numbering has a gap (03 → 13): scripts 04–12 were an earlier single-neighborhood draft,
  superseded by the citywide versions and removed rather than left to confuse a rerun.
- `data/raw/` - cached raw API responses (so re-running the pipeline doesn't hammer public APIs)
- `data/processed/` - clean CSV/GeoJSON outputs consumed by later stages and the map
- `docs/` - methodology, results, data validation, limitations & diligence roadmap, and a
  presentation outline, plus PowerPoint build assets (`powerpoint_starter.md`,
  `powerpoint_slide_copy.md`, `powerpoint_speaker_notes.md`)
- `index.html` - the generated interactive web map (repo root, for GitHub Pages)

## Running the pipeline

```bash
pip install -r requirements.txt

cd scripts
python 01_fetch_tracts.py                  # all 1,115 Harris County tracts + ACS demographics
python 02_fetch_competitors.py              # 528 store locations across 15 banners, categorized (OSM)
python 03_gap_analysis.py                   # county-wide opportunity scoring

python 13_houston_scope_clusters.py         # real Houston boundary; 10 spread-out opportunity areas
python 14_find_intersections_citywide.py    # real arterial intersections in all 10 areas (OSM)
python 15_fetch_parcels_citywide.py         # real HCAD candidate parcels, 20-site citywide shortlist
python 16_fetch_citywide_aadt.py            # every TxDOT AADT station in Houston (1,687)
python 17_fetch_citywide_blockgroups.py     # every Census block group in Houston (1,603)
python 18_enrich_sites_citywide.py          # FEMA flood, verified AADT, competitor distances
python 19_drive_times_and_huff.py           # OSRM drive-time trade areas + Huff gravity model
python 20_score_sites_citywide.py           # weighted scorecard + AADT-benchmark gate + citywide ranking
python 21_fetch_houston_tract_geometry.py   # tract polygons for the citywide choropleth
python 22_isochrone_winner.py               # real OSRM isochrone for the CURRENT #1 scorecard site
python 24_cannibalization_analysis.py       # real trade-area overlap vs. existing Family Dollar stores
python 25_extended_demographics_and_ci.py   # foreign-born/Spanish/household-size + 90% confidence intervals
python 26_microsite_details.py              # real speed limits, co-tenants, transit distance, approx. lot dimensions
python 27_vehicle_tenure_demographics.py    # zero-vehicle household share + renter-occupied share + CIs
python 28_sensitivity_analysis.py           # 5-scenario re-weighting robustness check on the scorecard
python 29_statistical_rigor.py              # Moran's I residual test + spatial block cross-validation metrics
python 23_generate_map_citywide.py          # builds ../index.html + Analysis Dashboard (FEMA polygons load live in-map via NFHL API)
```

Each script caches its API responses under `data/raw/`, so re-running the pipeline after the first
time is fast and doesn't re-hit the public APIs. Delete the relevant cache file(s) to force a
refresh.
