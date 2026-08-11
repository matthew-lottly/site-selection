# Presentation Outline

## Slide 1 — Executive Summary

- **Recommendation:** acquire the 0.66-acre vacant commercial parcel at **Cullen Blvd & Brookhaven
  St, Sunnyside, Houston, TX 77051** (HCAD 0430390000003).
- Core drivers: won a **citywide** comparison against 19 other real candidates in 9 other
  neighborhoods; verified 20,532 vpd on Cullen Blvd, clearing the 8,000 AADT minimum-traffic
  benchmark that its closest (higher raw-score) alternative fails; the **safest cannibalization
  profile of all 20 candidates** against Family Dollar's own existing network (43,688 net-new
  people, zero trade-area overlap); Zone X (minimal) flood risk; a real 40 mph posted speed limit
  in the ideal impulse-stop range.

## Slide 2 — Methodology and Data Pipeline

- Stage 1: County-wide macro gap screen — 1,115 Harris County Census tracts scored on demand
  (population × income fit × poverty) vs. supply (distance to nearest of 528 real stores, sorted
  into 5 categories: Family Dollar's own network, direct arch-rivals, sister banner, value grocery,
  big-box anchors).
- Stage 2: Real City of Houston boundary (not all of Harris County) used to scope 643 in-city
  tracts, clustered into **10 opportunity neighborhoods at least 2.75 miles apart** — not one
  submarket.
- Stage 3: Candidate discovery — real HCAD parcels at real arterial intersections, auto-discovered
  from OpenStreetMap (no hand-picked streets), across all 10 neighborhoods — 275 qualifying parcels,
  20-site citywide shortlist.
- Stage 4: Site enrichment — FEMA flood zone, TxDOT AADT traffic (verified by reverse-geocoding each
  station, freeway mainlane counts rejected), competitor distances by category, OSRM real drive-time
  trade-area population, and real micro-site operational detail (posted speed limits, co-tenant
  POIs, approximate lot dimensions from actual parcel geometry).
- Stage 5: Huff gravity market-capture model against real nearby **direct arch-rivals only**
  (Dollar General, Five Below — Dollar Tree excluded as Family Dollar's sister banner, not a
  competitor); a separate **cannibalization analysis** against existing Family Dollar stores
  (hard/soft buffers, real trade-area overlap %, net-new population reach — deliberately no revenue
  dollar figure, since no public sales data exists to calibrate one).
- Stage 6: Weighted scorecard (25% demand / 20% Huff capture / 15% competitive gap / 15% traffic /
  15% cost-feasibility / 10% flood risk) with the 8,000 AADT benchmark enforced as a **hard gate** on
  the primary recommendation, not just a soft-weighted factor.
- Stage 7: Real 90% confidence intervals for every city-wide headline statistic (population, income,
  poverty, foreign-born share, Spanish-at-home share, household size), computed with the Census
  Bureau's own ratio-MOE propagation formula.
- All data is public and free (US Census, OpenStreetMap, HCAD, FEMA, TxDOT, OSRM); no API keys
  required. Full source list, formulas, and every audit/validation check performed: see
  `docs/methodology.md` and `docs/data_validation.md`.

## Slide 3 — Trade Area, Competitive Landscape, and Cannibalization

- Real 5-minute and 10-minute OSRM drive-time isochrones (actual road network) around the
  recommended site: 43,688 people within 5 minutes; 258,423 within 10 minutes.
- Nearest direct arch-rival: 4.29 miles away. Huff model estimates 49.0% market-capture against
  real nearby arch-rivals — second-highest of any finalist that also clears the traffic benchmark.
- **Cannibalization:** 4.07 miles from the nearest existing Family Dollar, zero measured trade-area
  overlap, and the highest net-new population reach of all 20 candidates (43,688) — the safest site
  in the field on this dimension, not just a strong one.

## Slide 4 — Site-Level Evaluation

- Present the 20-site citywide scorecard (`docs/results.md`): the top raw score actually belongs to
  a different site 0.4 mi away (1023 Niagara St, also Sunnyside, 72.7 vs. 71.1) — but it carries only
  1,547 vehicles/day, below the 8,000 AADT industry minimum. Rather than let a 15%-weighted factor
  get averaged away, the benchmark is enforced as a hard gate: the recommendation is the
  highest-scoring site that *also* clears it, with the near-tied alternative kept visible as the
  natural fallback pending a traffic-engineering read.
- Every other neighborhood searched (Alief, Westchase, Gulfton, Braeswood, Denver Harbor, East
  Houston, Braeburn, Acres Homes, Central Southwest Houston) produced real candidates that scored
  lower — shown on the map so the VP can see the comparison, not just the winner.

## Slide 5 — Interactive Web Map & Analysis Dashboard

- `index.html` (Folium/Leaflet, hosted on GitHub Pages): real Houston city-limits boundary, citywide
  opportunity choropleth (643 tracts, amber→deep-red by opportunity score), all 20 candidate sites as
  clean numbered rank badges on a validated best (green) → worst (red) color ramp with the
  recommendation as a large gold-ringed star, and the real drive-time trade area for the recommended
  site.
- Competitors are split into 5 toggleable tiers, colored from a validated cool-hue palette
  (blue/violet/magenta/aqua) chosen to never be confused with the warm rank-ramp/choropleth colors
  sharing the map: **Family Dollar's own network** (always visible — the cannibalization check),
  **direct arch-rivals** (visible by default — the real competitive threat), then sister banner,
  value grocery, and big-box anchors as off-by-default context layers.
- A **bottom-drawer Analysis Dashboard** (toggle button, bottom of screen) gives the VP four tabs
  without leaving the map: the full **Scorecard**, the **Cannibalization** table, **Site Details**
  (speed limits, co-tenants, lot dimensions), and **Confidence Intervals** plus a condensed data
  validation summary.
- Basemap switcher offers light/dark/streets/satellite/terrain. Popup and legend text is set in dark,
  bold type for readability at a glance in a room.

---

## Note to the hiring team

Hi Hossein,

Attached is the completed Houston Family Dollar site-selection case study. I built an end-to-end,
reproducible pipeline in Python that pulls exclusively from free, public, key-free data sources —
US Census (via TIGERweb + Census Reporter, including real margins of error), OpenStreetMap/Overpass,
Harris County Appraisal District parcels, FEMA's flood layer, TxDOT traffic counts, and OSRM for real
drive-time routing, a Huff gravity market-capture model, and a cannibalization/trade-area-overlap
analysis against Family Dollar's own existing stores — to screen the entire county, scope the search
to Houston's real city boundary, source real candidate parcels from 10 different neighborhoods (not
just the first promising one), and rank them into a citywide recommendation.

I've also documented, in `docs/data_validation.md`, the specific checks I ran to make sure this
holds up — including three real bugs I found and fixed during the process (a mislabeled neighborhood,
a stale cached isochrone, and a dead field that had silently returned a placeholder value since
early in the build) — and I've been explicit throughout about where public data runs out (deed
restrictions, engineered ingress/egress, and any revenue forecast, none of which this analysis
claims to have verified).

- Methodology: `docs/methodology.md`
- Results & recommendation: `docs/results.md`
- Data validation & confidence intervals: `docs/data_validation.md`
- Interactive map + Analysis Dashboard: `index.html` (GitHub Pages link once published)

Happy to walk through any part of the pipeline or the scoring logic.

Best regards,
Matt
