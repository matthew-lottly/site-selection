# Houston Family Dollar Site Selection

A reproducible, citywide GIS site-selection pipeline that recommends a new Family Dollar location in
Houston, TX, built entirely from free, public, key-free data. Prepared as a Location Intelligence /
GIS Analyst case study.

## Recommendation

**Brookhaven Street & Cullen Boulevard, Sunnyside, Houston, TX** - a 0.66-acre vacant commercial
parcel (HCAD account 0430390000003), selected from 20 real candidate sites across 10 Houston
neighborhoods. Score: 68.8/100.

- Sits in a real federal Qualified Opportunity Zone (verified by point-in-polygon check).
- Highest HUD-assisted-housing concentration of any finalist (612 units within 1 mile).
- Lowest cannibalization risk in the top tier (4.07 mi from the nearest existing Family Dollar, 0%
  trade-area overlap, 43,688 net-new population reach).
- 30.1% modeled Huff market-capture against nearby arch-rivals (Dollar General, Five Below, Dollar
  Tree - now a direct competitor since Family Dollar and Dollar Tree separated on 2025-07-08).
- Clears the 8,000 AADT traffic-viability gate (20,532 vpd on Cullen Blvd).
- FEMA Zone X (low flood risk), shovel-ready vacant land, $373,516 land value.

**The trade-off:** this site has the weakest crime reading of the top 5 finalists (60 violent / 68
property incidents within 0.5 mi, trailing 12 months). It's stable as the top choice in only 3 of 6
sensitivity-weighting scenarios - two other finalists (Eldridge Pkwy & Westhollow Pkwy in Parkridge,
and 6600 Stillwell St in Pecan Park) win under different, equally defensible priorities. See
[`docs/results.md`](docs/results.md) for the full scorecard and trade-off analysis.

**Interactive map:** [`index.html`](index.html) - a header bar plus a right-side **Analysis
Dashboard** panel (toggle in the header) with the full scorecard, sensitivity analysis,
cannibalization math, site-level detail, and confidence intervals, alongside an interactive map with
16 toggleable layers.

## Data sources (all free, no API keys)

- **US Census Bureau** - TIGERweb (tract/block-group boundaries, the real City of Houston boundary),
  ACS 2024 5-yr demographics via Census Reporter API (incl. margins of error, vehicle access, housing
  tenure), Population Estimates Program (citywide growth trend)
- **OpenStreetMap / Overpass API**, cross-checked against **Overture Maps** - 528+ competitor/anchor
  locations across 15 banners, arterial road network, posted speed limits, transit stops, co-tenant
  POIs
- **Harris County Appraisal District (HCAD)** - real parcel boundaries, land use, appraised value
- **FEMA National Flood Hazard Layer (NFHL)** - flood zone identification
- **TxDOT** - Annual Average Daily Traffic (AADT) counts, verified by reverse-geocoding each station
- **OSRM** - real drive-time routing over the OpenStreetMap road network, feeding a Huff gravity
  market-capture model and a cannibalization/trade-area-overlap analysis
- **Houston Police Department** - point-level NIBRS Part I violent/property crime incidents, for a
  per-site crime-risk score
- **HUD** - LIHTC affordable-housing properties and HUD Multifamily (FHA-insured/assisted housing),
  both geocoded from real addresses
- **Census LEHD LODES** - block-level job counts, for a daytime/workplace-population demand signal
- **USDA ERS Food Access Research Atlas** - per-tract food-access share
- **Federal Qualified Opportunity Zones** - tract-level designation, verified by point-in-polygon
  intersection against each finalist site

Full source-by-source detail, access methods, and verification checks:
[`docs/data_validation.md`](docs/data_validation.md).

## Methodology, in brief

1. **Macro screen** - score all 1,115 Harris County census tracts on a demand/competitive-gap index
   (`demand_index x competitive_gap_index`), then keep the 643 tracts inside the real Houston city
   boundary.
2. **Opportunity clustering** - group the strongest-scoring tracts into 10 geographically distinct
   opportunity areas (2.75+ mi apart), each mapped to a real named neighborhood.
3. **Candidate sourcing** - find real arterial intersections in each area, pull real HCAD parcels
   nearby, filter to realistic new-store sites (vacant or under-improved commercial land, 0.4-4.0
   acres), and keep the best 2 per area - 20 finalists total.
4. **Site enrichment** - FEMA flood zone, verified (non-freeway) AADT traffic count, competitive
   distances, real drive-time trade areas via OSRM, micro-site detail (speed limit, co-tenants,
   transit access, approximate lot dimensions).
5. **Competitive modeling** - a Huff gravity model estimates relative market-capture % against
   same-format arch-rivals (Dollar General, Five Below, Dollar Tree); a separate cannibalization
   analysis measures trade-area overlap and net-new population reach against Family Dollar's own
   existing stores.
6. **Additional demand/risk signals** - crime risk (HPD), LIHTC and HUD Multifamily housing
   proximity, LEHD daytime population, USDA food-access share, Opportunity Zone status.
7. **Weighted scorecard** - 7 top-level factors (demand composite, Huff capture, competitive white
   space, traffic, site cost/feasibility, flood risk, crime risk), each normalized 0-100 across the
   20 finalists, combined with documented weights. A hard AADT gate (8,000 vpd) excludes any
   otherwise-high-scoring site with unviable traffic from being the primary recommendation.
8. **Validation** - a 6-scenario sensitivity analysis re-weights the scorecard to test how robust the
   winner is; Moran's I and spatial cross-validation checks test the scoring model itself for spatial
   bias.

Full stage-by-stage detail: [`docs/methodology.md`](docs/methodology.md).

## Why these methods (and why not others)

Every figure traces to a live public API - no proprietary vendor data (SafeGraph, Placer.ai, CoStar,
Esri Business Analyst) and nothing hand-typed. The methods mirror how professional retail
site-selection teams actually structure a screen - drive-time trade areas (not circle buffers), a
gravity-model competitive read, a dedicated cannibalization check, and a hard viability gate - using
only free data. Deliberately **not** attempted: a store-level revenue forecast or regression-
calibrated scorecard weights, since both require the retailer's own historical sales data, which no
public source provides - inventing either would be a fabricated number dressed up as precision.
Instead, the model reports real, computed proxies (Huff capture %, net-new population reach) that
answer the same underlying questions without overstating what free data can support.

## Financial rationale & business use

**This pipeline exists to make diligence spend efficient, not to replace it.** Title searches,
traffic-engineering studies, and market studies are expensive per site and don't scale to dozens of
candidates. This analysis uses free data to narrow a citywide search (1,115 tracts -> 10 opportunity
areas -> 275 qualifying parcels -> 20 finalists -> 1 recommendation + 2 close alternates) before any
paid diligence dollars are spent, and only on the short list that survives.

**Business decisions this is built to support:**

- **Where to spend diligence budget next** - which 1-3 of 20 sites justify a title search, traffic
  study, and site visit, instead of funding that work blind or across all candidates.
- **Risk-adjusted prioritization** - trading off cannibalization, competitive exposure, traffic,
  flood risk, and crime risk against each other, rather than deciding on one factor alone (e.g.
  cheapest land or highest traffic).
- **Capital-gains tax strategy** - the recommended site's Opportunity Zone designation is a real,
  usable financial lever (capital gains deferral/reduction for QOZ-eligible investment structures),
  independent of the retail thesis.
- **Protecting existing-store sales** - the cannibalization framework exists specifically so a new
  store doesn't quietly cut into a nearby existing Family Dollar's sales.
- **Acquisition-cost negotiation anchor** - HCAD assessed land value ($373,516 for 0.66 acres at the
  recommended site) is a defensible floor for price negotiation (likely understates true market/lease
  cost, since it's a tax-assessed value, not an appraisal or lease comp).

**What this does not decide:** actual capital commitment. That requires closing the gaps below first
- this is the funnel into that process, not a substitute for it.

## Critique / known limitations

1. **No dollar revenue forecast** - no public data exists to calibrate one; the model stops at
   defensible proxy metrics instead of a fabricated sales number.
2. **Scorecard weights are judgment-based**, not regression-calibrated against real store outcomes.
3. **The recommendation is not robust to reweighting** - it wins in only 3 of 6 sensitivity scenarios;
   two other finalists win under different, equally defensible priorities.
4. **The winning site has the weakest crime reading of the top 5 finalists**, and crime is only 10%
   of the score - a real operational risk that a low weight may understate.
5. **Data vintage/consistency gaps** - Opportunity Zone polygons use 2010-vintage census tracts vs.
   2020-vintage tracts elsewhere; ACS 5-yr population (2.33M) vs. Census PEP annual estimate (2.39M)
   diverge by ~62k.
6. **Competitor travel time is approximated** (straight-line distance + a flat 25 mph), not full
   network routing, adding error to the competitive-capture metric specifically.
7. **Legal/physical diligence is unverified** - deed restrictions, ingress/egress geometry, turning
   radius, title. Houston has no municipal zoning, making deed restrictions a bigger-than-usual
   unknown.
8. **Crime, LIHTC, and food-access inputs are single-point-in-time snapshots**, not trends.
9. **No cost-of-capital framing** - no acquisition budget, lease-vs-buy comparison, or payback/IRR
   view ties the site score to expected financial return.
10. **Operational fragility** - the pipeline depends on several rate-limited public APIs (Overpass,
    Nominatim, OSRM) that can change or throttle without notice, with no automated test suite.

Full detail, plus the concrete next steps that close each gap:
[`docs/limitations_and_diligence.md`](docs/limitations_and_diligence.md).

## Repository structure

- `pipeline/` - the pipeline, as a class-based Python package:
  - `pipeline/core/` - `PipelineStage` (base class: `run()` + a default `validate()`), `ApiClient`
    (shared GET/POST + disk-cache behavior), `Pipeline` (orchestrator), and the `ROOT`/`RAW`/
    `PROCESSED` path constants.
  - `pipeline/clients/` - one client per data source (`TigerWebClient`, `CensusReporterClient`,
    `OverpassClient`, `HcadClient`, `FemaClient`, `TxDotClient`, `OsrmClient`, `HpdCrimeClient`,
    `HudLihtcClient`, `LehdClient`, `UsdaFoodAccessClient`, `OvertureClient`, `CensusPepClient`,
    `OpportunityZonesClient`, `HudMultifamilyClient`).
  - `pipeline/geometry.py` / `pipeline/color.py` - stateless helpers for distance/point-in-polygon/
    hull math and validated map color palettes.
  - `pipeline/stages/` - one `PipelineStage` subclass per pipeline step, each independently runnable.
- `run_pipeline.py` - CLI entry point: run every stage (`python run_pipeline.py`), a subset
  (`--only 01 02`), or list them (`--list`).
- `data/raw/` - cached raw API responses.
- `data/processed/` - clean CSV/GeoJSON outputs consumed by later stages and the map.
- `docs/` - `methodology.md` (how the pipeline works), `results.md` (full scorecard and
  recommendation reasoning), `data_validation.md` (source catalog, audit checks, confidence
  intervals), `limitations_and_diligence.md` (what a desk analysis can't verify and the next steps
  that close the gap), `email_to_family_dollar.md` (data-sources summary for a non-technical
  audience), and `docs/slides/` (a paste-ready leadership slide deck).
- `index.html` - the generated interactive web map (repo root, for GitHub Pages).

## Running the pipeline

```bash
pip install -r requirements.txt

python run_pipeline.py --list   # see every stage, in run order, with a one-line description
python run_pipeline.py          # run the whole pipeline end-to-end
```

Or run a specific stage or subset - useful when only one step's inputs changed:

```bash
python run_pipeline.py --only 20 23      # re-score sites and regenerate the map
python -m pipeline.stages.s01_fetch_tracts   # any stage is directly runnable on its own
```

### Run order and what each stage does

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
30  crime_risk                     HPD NIBRS Part I violent/property crime counts within 0.5mi of each finalist
32  lihtc_properties               HUD LIHTC affordable-housing unit counts within 1mi of each finalist
33  daytime_population             Census LEHD workplace/job counts within each finalist's 5-min drive trade area
34  food_access                    USDA food-access ("food desert") share for each finalist's census tract
35  overture_supplement            Overture Maps cross-check of the OSM-sourced competitor data
37  opportunity_zones              federal Opportunity Zone designation, verified by point-in-polygon intersection
38  hud_multifamily                HUD Multifamily assisted-housing unit counts within 1mi of each finalist
20  score_sites_citywide           weighted scorecard + AADT-benchmark gate + citywide ranking
21  fetch_houston_tract_geometry   tract polygons for the citywide choropleth
22  isochrone_winner               OSRM isochrone for the current #1 scorecard site
24  cannibalization_analysis       trade-area overlap vs. existing Family Dollar stores
25  extended_demographics_and_ci   foreign-born/Spanish/household-size + 90% confidence intervals
26  microsite_details              speed limits, co-tenants, transit distance, approx. lot dimensions
27  vehicle_tenure_demographics    zero-vehicle household share + renter-occupied share + CIs
28  sensitivity_analysis           6-scenario re-weighting robustness check on the scorecard
29  statistical_rigor              Moran's I residual test + spatial block cross-validation metrics
36  population_trend               Census PEP Houston population growth trend, 2020-2024 (citywide context)
23  generate_map_citywide          builds ../index.html + Analysis Dashboard (FEMA polygons load live in-map via NFHL API)

31  generate_slide_assets          optional: chart images for docs/slides/ (leadership deck), not required for the map or analysis
```

Numbering has gaps because superseded early-draft stages were removed rather than renumbered; stage
23 (map generation) depends on later stages' outputs, so `pipeline/stages/__init__.py` and
`run_pipeline.py` run it after them, not in numeric position. Each stage caches its API responses
under `data/raw/`, so re-running the pipeline after the first time is fast and doesn't re-hit public
APIs - delete the relevant cache file(s) to force a refresh.
