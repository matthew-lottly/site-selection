# Houston Family Dollar Site Selection

An end-to-end, reproducible, **citywide** GIS site-selection pipeline for a new Family Dollar
location in Houston, TX - built entirely from free, public, key-free data sources. Prepared as a
Location Intelligence / GIS Analyst case study.

**Recommendation:** Eldridge Parkway & Westhollow Parkway, Parkridge, Houston, TX - selected from 20
real candidate sites spanning 10 Houston neighborhoods. See [`docs/results.md`](docs/results.md) for the full
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
- Houston Police Department - real, point-level NIBRS Part I violent/property crime incidents,
  direct CSV export, for a real per-site crime-risk score

An earlier revision checked Houston's open-data CKAN catalog for crime data and found it genuinely
unavailable there. That check missed a separate, real source: HPD's own site publishes point-level
incident data as direct CSV downloads. See `docs/data_validation.md` §2 (item 14) for the full story
and `docs/methodology.md` Stage 5c for how it's used.

## Repository structure

- `pipeline/` - the pipeline, as a class-based Python package:
  - `pipeline/core/` - `PipelineStage` (the abstract base every stage subclasses: `run()` +
    a default `validate()` that confirms declared outputs exist), `ApiClient` (shared GET/POST +
    disk-cache behavior), `Pipeline` (the orchestrator that runs stages in order), and the
    `ROOT`/`RAW`/`PROCESSED` path constants.
  - `pipeline/clients/` - one `ApiClient` subclass per data source (`TigerWebClient`,
    `CensusReporterClient`, `OverpassClient`, `HcadClient`, `FemaClient`, `TxDotClient`,
    `OsrmClient`), each just enough to express that source's request shape and caching needs.
  - `pipeline/geometry.py` / `pipeline/color.py` - `Geometry` and `ColorRamp`: stateless helper
    classes for distance/point-in-polygon/hull math and the validated map color palettes.
  - `pipeline/stages/` - one `PipelineStage` subclass per pipeline step (`s01_fetch_tracts.py`,
    `s02_fetch_competitors.py`, ... `s31_generate_slide_assets.py`), each independently runnable.
    Numbering has a gap (03 → 13): stages 04-12 were an earlier single-neighborhood draft, superseded
    by the citywide versions and removed rather than left to confuse a rerun. Stage 30 originally
    fetched a static, citywide FEMA flood-polygon file, superseded by the live in-map FEMA fetch in
    stage 23 and removed - the number was later reused for the real HPD crime-risk stage.
- `run_pipeline.py` - CLI entry point: runs every stage in order (`python run_pipeline.py`), a
  subset (`--only 01 02`), or just lists them (`--list`).
- `data/raw/` - cached raw API responses (so re-running the pipeline doesn't hammer public APIs)
- `data/processed/` - clean CSV/GeoJSON outputs consumed by later stages and the map
- `docs/` - methodology, results, data validation, limitations & diligence roadmap, and a
  presentation outline, plus PowerPoint build assets (`powerpoint_starter.md`,
  `powerpoint_slide_copy.md`, `powerpoint_speaker_notes.md`)
- `docs/slides/` - a paste-ready, 12-file leadership slide deck (one markdown file per slide, real
  chart images included) - see `docs/slides/00_INDEX.md` for how to build it in Google Slides
- `index.html` - the generated interactive web map (repo root, for GitHub Pages)

## Running the pipeline

```bash
pip install -r requirements.txt

python run_pipeline.py --list   # see every stage, in run order, with a one-line description
python run_pipeline.py          # run the whole pipeline end-to-end
```

Or run (or re-run) a specific stage or subset, either through the CLI or as a standalone module -
useful when only one step's inputs changed:

```bash
python run_pipeline.py --only 20 23      # re-score sites and regenerate the map
python -m pipeline.stages.s01_fetch_tracts   # any stage is directly runnable on its own
```

Run order and what each stage does:

```text
01  fetch_tracts                   all 1,115 Harris County tracts + ACS demographics
02  fetch_competitors              528 store locations across 15 banners, categorized (OSM)
03  gap_analysis                   county-wide opportunity scoring

13  houston_scope_clusters         real Houston boundary; 10 spread-out opportunity areas
14  find_intersections_citywide    real arterial intersections in all 10 areas (OSM)
15  fetch_parcels_citywide         real HCAD candidate parcels, 20-site citywide shortlist
16  fetch_citywide_aadt            every TxDOT AADT station in Houston (1,687)
17  fetch_citywide_blockgroups     every Census block group in Houston (1,603)
18  enrich_sites_citywide          FEMA flood, verified AADT, competitor distances
19  drive_times_and_huff           OSRM drive-time trade areas + Huff gravity model
30  crime_risk                     real HPD NIBRS Part I violent/property crime counts within 0.5mi of each finalist
20  score_sites_citywide           weighted scorecard + AADT-benchmark gate + citywide ranking
21  fetch_houston_tract_geometry   tract polygons for the citywide choropleth
22  isochrone_winner               real OSRM isochrone for the CURRENT #1 scorecard site
24  cannibalization_analysis       real trade-area overlap vs. existing Family Dollar stores
25  extended_demographics_and_ci   foreign-born/Spanish/household-size + 90% confidence intervals
26  microsite_details              real speed limits, co-tenants, transit distance, approx. lot dimensions
27  vehicle_tenure_demographics    zero-vehicle household share + renter-occupied share + CIs
28  sensitivity_analysis           6-scenario re-weighting robustness check on the scorecard
29  statistical_rigor              Moran's I residual test + spatial block cross-validation metrics
23  generate_map_citywide          builds ../index.html + Analysis Dashboard (FEMA polygons load live in-map via NFHL API)

31  generate_slide_assets          optional: real chart images for docs/slides/ (leadership deck), not required for the map or analysis
```

(Stage 23 depends on stages 24-29's outputs, so `pipeline/stages/__init__.py` registers it near the
end - it runs there rather than in numeric position. Stage 30 (crime risk) similarly runs right after
19, before scoring, since stage 20 consumes its output - both are slotted into `ALL_STAGES` at the
point they actually need to run, not in numeric order; `run_pipeline.py` follows that same order.)

Each stage caches its API responses under `data/raw/`, so re-running the pipeline after the first
time is fast and doesn't re-hit the public APIs. Delete the relevant cache file(s) to force a
refresh.
