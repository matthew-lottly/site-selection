# Presentation Outline

## Slide 1 — Executive Summary

- **Recommendation:** acquire the 0.81-acre vacant commercial parcel at **6600 Stillwell St, Pecan
  Park, Houston, TX** (HCAD 0410300000175).
- Core drivers: won a **citywide** comparison against 19 other real candidates in 9 other
  neighborhoods, on both raw score and the traffic-benchmark-gated score; verified 19,656 vpd on Gulf
  Freeway Frontage Road, clearing the 8,000 AADT minimum-traffic benchmark; the strongest trade-area
  demand of any benchmark-clearing finalist (44,339 people within a real 5-minute drive); Zone X
  (minimal) flood risk; stable under 3 of 5 alternative scoring-weight scenarios tested.
- **One trade-off, reported plainly, not smoothed over:** this site's cannibalization risk against
  Family Dollar's own existing network is High (1.01 mi from an existing FD). The extremely close #2
  site (Cullen Blvd & Brookhaven St, Sunnyside — 78.3 vs. 79.4) has a Low-risk, higher-net-new-reach
  profile instead. Both are real, comparably strong candidates — see Slide 4.

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
  station, freeway mainline counts rejected, legitimate frontage roads retained), competitor
  distances by category, OSRM real drive-time trade-area population, and real micro-site operational
  detail (posted speed limits, co-tenant POIs, transit stop distance, approximate lot dimensions from
  actual parcel geometry).
- Stage 5: Huff gravity market-capture model against real nearby **direct arch-rivals only**
  (Dollar General, Five Below — Dollar Tree excluded as Family Dollar's sister banner, not a
  competitor); a separate **cannibalization analysis** against existing Family Dollar stores
  (hard/soft buffers, real trade-area overlap %, net-new population reach — deliberately no revenue
  dollar figure, since no public sales data exists to calibrate one).
- Stage 6: Weighted scorecard (25% demand / 20% Huff capture / 15% competitive gap / 15% traffic /
  15% cost-feasibility / 10% flood risk) with the 8,000 AADT benchmark enforced as a **hard gate** on
  the primary recommendation, not just a soft-weighted factor.
- Stage 7: Trade-area visualization — tract choropleth across the 643 in-city tracts and the real
  OSRM 5-minute / 10-minute isochrone for the recommended site.
- Stage 8: Extended demographics & confidence intervals — real Houston-specific ACS context plus
  citywide 90% confidence intervals for population, income, poverty, foreign-born share,
  Spanish-at-home share, and household size.
- Stage 8b: Vehicle access, housing tenure, and sensitivity analysis — zero-vehicle share,
  renter-occupied share, and the 5-scenario score re-aggregation check that caught a real
  freeway-vs.-frontage-road traffic classification bug and changed the actual recommendation; see
  `docs/data_validation.md` §2.
- Stage 9: Web map and dashboard — Folium/Leaflet delivery of the scorecard, cannibalization,
  confidence intervals, and validation tabs for an executive audience.
- All data is public and free (US Census, OpenStreetMap, HCAD, FEMA, TxDOT, OSRM); no API keys
  required. Full source list, formulas, and every audit/validation check performed: see
  `docs/methodology.md` and `docs/data_validation.md`.

## Slide 3 — Trade Area, Competitive Landscape, and Cannibalization

- Real 5-minute and 10-minute OSRM drive-time isochrones (actual road network) around the
  recommended site: 44,339 people within 5 minutes; 228,331 within 10 minutes.
- Nearest direct arch-rival (Dollar General): 3.03 miles away. Huff model estimates 44.8%
  market-capture against real nearby arch-rivals.
- **Cannibalization (the one real trade-off):** 1.01 miles from the nearest existing Family Dollar,
  47.8% measured trade-area overlap — a High cannibalization risk, reported plainly. The #2 finalist
  (Cullen Blvd & Brookhaven St, Sunnyside) is the opposite: 4.07 mi from the nearest FD, zero overlap,
  and a higher net-new population reach (43,688 vs. 23,138) despite scoring 1.1 points lower overall.
  Framed for the VP as an explicit decision point in `docs/limitations_and_diligence.md`, not
  resolved unilaterally by the scoring model.

## Slide 4 — Site-Level Evaluation

- Present the 20-site citywide scorecard (`docs/results.md`): the recommended site is both the top
  raw score and the top benchmark-gated score — no override was needed this time, unlike an earlier
  build of this pipeline (see Slide 2's sensitivity-analysis note for the bug that changed which site
  that is).
- The multi-scenario sensitivity analysis shows the recommendation holds under 3 of 5 alternative
  weightings (Base, Cost-Heavy, Demand-Heavy) and is never worse than a close #2 under the other two
  (Traffic-Heavy favors Eldridge Pkwy/Parkridge; Competition-Heavy favors the Sunnyside #2 site) —
  reported honestly rather than presented as universally dominant.
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
- A **right-side Analysis Dashboard panel** (toggle button in the top header bar) gives the VP seven
  tabs without leaving the map: **Executive Checks** (benchmark pass/watch/fail table for macro,
  micro, competition, and physical risk indicators), the full **Scorecard** (with sensitivity
  analysis beneath it), the **Cannibalization** table, **Site Details** (speed limits, road class,
  co-tenant count, transit access, lot dimensions), **Confidence Intervals**, **Model Rigor**
  (Moran's I residual test + spatial block CV), and **Sources &amp; Validation**. The map stays visible
  and interactive alongside the open panel.
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

I've also documented, in `docs/data_validation.md`, the specific checks I ran to make sure this holds
up — including a bug I found and fixed via a self-imposed sensitivity-analysis stress test that
actually changed the final recommendation (a freeway-vs-frontage-road traffic-count classification
error), plus a mislabeled neighborhood, a stale cached isochrone, and a dead field that had silently
returned a placeholder value since early in the build — and I've been explicit throughout about where
public data runs out (deed restrictions, engineered ingress/egress, property crime, and any revenue
forecast, none of which this analysis claims to have verified; see
`docs/limitations_and_diligence.md` for the concrete diligence steps that would close each gap).

- Methodology: `docs/methodology.md`
- Results & recommendation: `docs/results.md`
- Data validation & confidence intervals: `docs/data_validation.md`
- Limitations & diligence roadmap: `docs/limitations_and_diligence.md`
- Interactive map + Analysis Dashboard: `index.html` (GitHub Pages link once published)

Happy to walk through any part of the pipeline or the scoring logic.

Best regards,
Matt
