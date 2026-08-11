# Houston Family Dollar Site Selection

An end-to-end, reproducible GIS site-selection pipeline for a new Family Dollar location in
Houston, TX — built entirely from free, public, key-free data sources. Prepared as a Location
Intelligence / GIS Analyst case study.

**Recommendation:** 9104 Cullen Blvd, Houston, TX 77051 (Cullen Blvd & Reed Rd, Sunnyside / South
Union). See [`docs/results.md`](docs/results.md) for the full scorecard and reasoning, and
[`docs/methodology.md`](docs/methodology.md) for how the pipeline works.

**Interactive map:** [`index.html`](index.html) — open locally or view on GitHub Pages once
published.

## Data sources (all free, no API keys)

- US Census Bureau — TIGERweb (boundaries) + Census Reporter API (ACS 2024 5-yr demographics)
- OpenStreetMap / Overpass API — competitor & anchor retail locations, arterial road network
- Harris County Appraisal District (HCAD) — real parcel boundaries, land use, appraised value
- FEMA National Flood Hazard Layer (NFHL) — flood zone identification
- TxDOT — Annual Average Daily Traffic (AADT) counts
- OSRM — real drive-time routing over the OpenStreetMap road network

## Repository structure

- `scripts/` — the pipeline, run in numeric order (`01_...` through `12_...`); `lib.py` holds
  shared HTTP/geometry helpers
- `data/raw/` — cached raw API responses (so re-running the pipeline doesn't hammer public APIs)
- `data/processed/` — clean CSV/GeoJSON outputs consumed by later stages and the map
- `docs/` — methodology, results, and a presentation outline
- `index.html` — the generated interactive web map (repo root, for GitHub Pages)

## Running the pipeline

```bash
pip install -r requirements.txt

cd scripts
python 01_fetch_tracts.py            # Harris County tracts + ACS demographics
python 02_fetch_competitors.py       # existing dollar stores + anchors (OSM)
python 03_gap_analysis.py            # county-wide opportunity scoring
python 04_define_submarket.py        # lock in submarket geometry + AADT points
python 05_find_intersections.py      # real arterial intersections (OSM)
python 06_fetch_parcels.py           # real HCAD candidate parcels
python 07_fetch_blockgroup_demo.py   # block-group population for trade areas
python 08_enrich_sites.py            # FEMA flood, AADT, competitor distances per site
python 09_drive_times.py             # OSRM drive-time trade-area population
python 10_score_sites.py             # weighted scorecard + ranking
python 11_isochrone.py               # real drive-time isochrone for the winner
python 12_generate_map.py            # builds ../index.html
```

Each script caches its API responses under `data/raw/`, so re-running the pipeline after the first
time is fast and doesn't re-hit the public APIs. Delete the relevant cache file(s) to force a
refresh.
