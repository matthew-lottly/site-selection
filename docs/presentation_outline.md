# Presentation Outline

## Slide 1 — Executive Summary

- **Recommendation:** acquire the 0.66-acre vacant commercial parcel at **Cullen Blvd & Brookhaven
  St, Sunnyside, Houston, TX 77051** (HCAD 0430390000003).
- Core drivers: won a **citywide** comparison against 19 other real candidates in 9 other
  neighborhoods; verified 20,532 vpd on Cullen Blvd; widest real competitive gap (4.07 mi) among
  finalists that also clear traffic and flood screens; highest Huff gravity-model market-capture
  rate (16.6%) of all 20 candidates; Zone X (minimal) flood risk.

## Slide 2 — Methodology and Data Pipeline

- Stage 1: County-wide macro gap screen — 1,115 Harris County Census tracts scored on demand
  (population × income fit × poverty) vs. supply (distance to nearest of 156 existing dollar
  stores).
- Stage 2: Real City of Houston boundary (not all of Harris County) used to scope 643 in-city
  tracts, clustered into **10 opportunity neighborhoods at least 2.75 miles apart** — not one
  submarket.
- Stage 3: Candidate discovery — real HCAD parcels at real arterial intersections, auto-discovered
  from OpenStreetMap (no hand-picked streets), across all 10 neighborhoods — 275 qualifying parcels,
  20-site citywide shortlist.
- Stage 4: Site enrichment — FEMA flood zone, TxDOT AADT traffic (verified by reverse-geocoding each
  station, freeway mainlane counts rejected), broadened OSM competitor distances (13 banners, 516
  locations), OSRM real drive-time trade-area population.
- Stage 5: Huff gravity market-capture model against real nearby direct dollar-store competitors
  (published typical prototype square footage, β = 2.0 distance decay).
- Stage 6: Weighted scorecard (25% demand / 20% Huff capture / 15% competitive gap / 15% traffic /
  15% cost-feasibility / 10% flood risk) → citywide ranking.
- All data is public and free (US Census, OpenStreetMap, HCAD, FEMA, TxDOT, OSRM); no API keys
  required. See `docs/methodology.md` for full source list and formulas.

## Slide 3 — Trade Area and Competitive Landscape

- Real 5-minute and 10-minute OSRM drive-time isochrones (actual road network) around the
  recommended site: 43,688 people within 5 minutes; 258,423 within 10 minutes.
- Nearest existing dollar-store competitor: 4.07 miles away — the widest qualifying gap of any
  finalist. Huff model estimates a 16.6% market-capture rate against real nearby direct competitors.

## Slide 4 — Site-Level Evaluation

- Present the 20-site citywide scorecard (`docs/results.md`): the top 2 finalists are both in
  Sunnyside, essentially tied (73.5 vs. 73.3) — but #2 fails the 8,000 AADT minimum-traffic
  benchmark (1,547 vpd), which is why #1 is the recommendation and #2 is the fallback pending a
  traffic-engineering read.
- Every other neighborhood searched (Alief, Westchase, Gulfton, Braeswood, Denver Harbor, East
  Houston, Braeburn, Acres Homes, Central Southwest Houston) produced real candidates that scored
  lower — shown on the map so the VP can see the comparison, not just the winner.

## Slide 5 — Interactive Web Map

- `index.html` (Folium/Leaflet, hosted on GitHub Pages): real Houston city-limits boundary, citywide
  opportunity choropleth (643 tracts, amber→deep-red by opportunity score), all 20 candidate sites as
  clean numbered rank badges on a best (green) → worst (red) color ramp with the recommendation as a
  large gold-ringed star, and the real drive-time trade area for the recommended site.
- Competitors are split into 4 toggleable tiers so the VP can isolate what matters most: **existing
  Family Dollar locations get their own dedicated layer** (the direct cannibalization check), then
  other dollar-store banners, then off-price/general merchandise and grocery/big-box anchors as
  lower-opacity context layers, on by request rather than by default.
- Basemap switcher offers light/dark/streets/satellite/terrain. Popup and legend text is set in dark,
  bold type for readability at a glance in a room.

---

## Note to the hiring team

Hi Hossein,

Attached is the completed Houston Family Dollar site-selection case study. I built an end-to-end,
reproducible pipeline in Python that pulls exclusively from free, public, key-free data sources —
US Census (via TIGERweb + Census Reporter), OpenStreetMap/Overpass, Harris County Appraisal
District parcels, FEMA's flood layer, TxDOT traffic counts, and OSRM for real drive-time routing and
a Huff gravity market-capture model — to screen the entire county, scope the search to Houston's
real city boundary, source real candidate parcels from 10 different neighborhoods (not just the
first promising one), and rank them into a citywide recommendation.

- Methodology: `docs/methodology.md`
- Results & recommendation: `docs/results.md`
- Interactive map: `index.html` (GitHub Pages link once published)

Happy to walk through any part of the pipeline or the scoring logic.

Best regards,
Matt
