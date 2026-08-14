# Houston Family Dollar Site Selection

An end-to-end, reproducible, **citywide** GIS site-selection pipeline for a new Family Dollar
location in Houston, TX - built entirely from free, public, key-free data sources. Prepared as a
Location Intelligence / GIS Analyst case study.

**Recommendation:** Brookhaven Street & Cullen Boulevard, Sunnyside, Houston, TX - selected from 20
real candidate sites spanning 10 Houston neighborhoods. Dollar Tree is modeled as a direct competitor
(not a "sister banner") since Family Dollar and Dollar Tree officially separated on 2025-07-08. See
[`docs/results.md`](docs/results.md) for the full scorecard, reasoning, and the real trade-offs (this
site's real Opportunity Zone status and subsidized-housing concentration vs. its weaker crime reading,
and how it compares to the two other real, close finalists) - including a materially significant real
correction found along the way, [`docs/methodology.md`](docs/methodology.md) for how the pipeline works,
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
- HUD LIHTC Database - real, geocoded affordable-housing properties (ArcGIS REST)
- Census LEHD LODES - real block-level job counts, for a real daytime/workplace-population signal
- USDA ERS Food Access Research Atlas (SRAM) - real per-tract food-access share
- Overture Maps Foundation Places - free, open (CDLA Permissive 2.0) POI data, cross-checked against
  the OSM-sourced competitor pull
- Census Population Estimates Program (PEP) - real annual City of Houston population estimates,
  2020-2024, direct CSV release (the PEP's own REST API now requires a key, so this uses the Bureau's
  keyless direct file instead) - citywide growth-trend context
- Federal Qualified Opportunity Zones (ArcGIS REST) - real tract-level designation, verified by
  point-in-polygon intersection against each finalist site
- HUD Multifamily Properties (ArcGIS REST) - real FHA-insured/HUD-assisted housing properties,
  geocoded from their real street addresses within 1 mile of each finalist

An earlier revision checked Houston's open-data CKAN catalog for crime data and found it genuinely
unavailable there. That check missed a separate, real source: HPD's own site publishes point-level
incident data as direct CSV downloads. See `docs/data_validation.md` §2 (item 14) for the full story
and `docs/methodology.md` Stage 5c for how it's used. A deliberate second free-data pass then re-checked
every other paid-vendor category for a free alternative and added four more sources - see
`docs/data_validation.md` §2 (items 15-19) and `docs/methodology.md` Stage 5d. A third pass reclassified
Dollar Tree as a real competitor (a corporate-separation fact, not a data addition), checked retail
site-selection best practice against the model's methodology, and added the real population-growth-trend
context above - see `docs/data_validation.md` §2 (items 20-22). A fourth pass specifically re-checked
for any remaining free retail-site-selection data and added two more real federal sources - Opportunity
Zones and HUD Multifamily Properties - see `docs/data_validation.md` §2 (items 23-26) and
`docs/methodology.md` Stage 5e.

## Repository structure

- `pipeline/` - the pipeline, as a class-based Python package:
  - `pipeline/core/` - `PipelineStage` (the abstract base every stage subclasses: `run()` +
    a default `validate()` that confirms declared outputs exist), `ApiClient` (shared GET/POST +
    disk-cache behavior), `Pipeline` (the orchestrator that runs stages in order), and the
    `ROOT`/`RAW`/`PROCESSED` path constants.
  - `pipeline/clients/` - one `ApiClient` subclass (or equivalent lightweight client) per data source
    (`TigerWebClient`, `CensusReporterClient`, `OverpassClient`, `HcadClient`, `FemaClient`,
    `TxDotClient`, `OsrmClient`, `HpdCrimeClient`, `HudLihtcClient`, `LehdClient`,
    `UsdaFoodAccessClient`, `OvertureClient`, `CensusPepClient`, `OpportunityZonesClient`,
    `HudMultifamilyClient`), each just enough to express that source's request shape and caching needs.
  - `pipeline/geometry.py` / `pipeline/color.py` - `Geometry` and `ColorRamp`: stateless helper
    classes for distance/point-in-polygon/hull math and the validated map color palettes.
  - `pipeline/stages/` - one `PipelineStage` subclass per pipeline step (`s01_fetch_tracts.py`,
    `s02_fetch_competitors.py`, ... `s38_hud_multifamily.py`), each independently runnable.
    Numbering has a gap (03 → 13): stages 04-12 were an earlier single-neighborhood draft, superseded
    by the citywide versions and removed rather than left to confuse a rerun. Stage 30 originally
    fetched a static, citywide FEMA flood-polygon file, superseded by the live in-map FEMA fetch in
    stage 23 and removed - the number was later reused for the real HPD crime-risk stage. Stages 32-35
    (LIHTC, daytime population, food access, Overture cross-check) were added in a second free-data
    pass after crime data; stage 36 (population growth trend) in a third pass alongside the Dollar
    Tree recategorization and a best-practice methodology review; stages 37-38 (Opportunity Zones,
    HUD Multifamily) in a fourth pass specifically re-checking for any remaining free retail-site-
    selection data.
- `run_pipeline.py` - CLI entry point: runs every stage in order (`python run_pipeline.py`), a
  subset (`--only 01 02`), or just lists them (`--list`).
- `data/raw/` - cached raw API responses (so re-running the pipeline doesn't hammer public APIs)
- `data/processed/` - clean CSV/GeoJSON outputs consumed by later stages and the map
- `docs/` - methodology, results, data validation, limitations & diligence roadmap, and an email
  deliverable summarizing data sources and next steps for a non-technical audience
  (`email_to_family_dollar.md`)
- `docs/slides/` - a paste-ready, 12-file leadership slide deck (one markdown file per slide, real
  chart images included) - see `docs/slides/00_INDEX.md` for how to build it in Google Slides. This is
  the current deck; an earlier PowerPoint-oriented draft covering the same ground in prose form was
  removed once this became the paste-ready version.
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
32  lihtc_properties                real HUD LIHTC affordable-housing unit counts within 1mi of each finalist
33  daytime_population              real Census LEHD workplace/job counts within each finalist's 5-min drive trade area
34  food_access                     real USDA food-access ("food desert") share for each finalist's census tract
35  overture_supplement             real Overture Maps cross-check of the OSM-sourced competitor data
37  opportunity_zones               real federal Opportunity Zone designation, verified by point-in-polygon intersection
38  hud_multifamily                 real HUD Multifamily assisted-housing unit counts within 1mi of each finalist
20  score_sites_citywide           weighted scorecard + AADT-benchmark gate + citywide ranking
21  fetch_houston_tract_geometry   tract polygons for the citywide choropleth
22  isochrone_winner               real OSRM isochrone for the CURRENT #1 scorecard site
24  cannibalization_analysis       real trade-area overlap vs. existing Family Dollar stores
25  extended_demographics_and_ci   foreign-born/Spanish/household-size + 90% confidence intervals
26  microsite_details              real speed limits, co-tenants, transit distance, approx. lot dimensions
27  vehicle_tenure_demographics    zero-vehicle household share + renter-occupied share + CIs
28  sensitivity_analysis           6-scenario re-weighting robustness check on the scorecard
29  statistical_rigor              Moran's I residual test + spatial block cross-validation metrics
36  population_trend                real Census PEP Houston population growth trend, 2020-2024 (citywide context)
23  generate_map_citywide          builds ../index.html + Analysis Dashboard (FEMA polygons load live in-map via NFHL API)

31  generate_slide_assets          optional: real chart images for docs/slides/ (leadership deck), not required for the map or analysis
```

(Stage 23 depends on stages 24-29 and 36's outputs, so `pipeline/stages/__init__.py` registers it near
the end - it runs there rather than in numeric position. Stages 30, 32-35, and 37-38 (crime risk,
LIHTC, daytime population, food access, Overture cross-check, Opportunity Zones, HUD Multifamily)
similarly run right after 19, before scoring, since stage 20 consumes their outputs - all are slotted
into `ALL_STAGES` at the point they actually need to run, not in numeric order; `run_pipeline.py`
follows that same order.)

Each stage caches its API responses under `data/raw/`, so re-running the pipeline after the first
time is fast and doesn't re-hit the public APIs. Delete the relevant cache file(s) to force a
refresh.
