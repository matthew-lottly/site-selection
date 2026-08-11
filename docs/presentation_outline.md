# Presentation Outline

## Slide 1 — Executive Summary
- **Recommendation:** acquire the 0.46-acre vacant commercial parcel at **9104 Cullen Blvd, Houston,
  TX 77051** (Cullen Blvd & Reed Rd, Sunnyside / South Union).
- Core drivers: verified zero-competitor gap, highest confirmed traffic count among finalists
  (18,429 vpd on Cullen Blvd), lowest land cost per acre, on-target trade-area income ($41,648
  median HH income vs. Family Dollar's ~$20k–$55k core band), Zone X (minimal) flood risk.

## Slide 2 — Methodology and Data Pipeline
- Stage 1: County-wide macro gap screen — 1,115 Harris County Census tracts scored on demand
  (population × income fit × poverty) vs. supply (distance to nearest existing dollar store).
- Stage 2: Submarket lock-in — Sunnyside / South Union, the strongest underserved cluster, verified
  to have zero existing Family Dollar / Dollar General / Dollar Tree locations.
- Stage 3: Candidate discovery — real HCAD parcels at real arterial intersections (Cullen Blvd, MLK
  Jr Blvd, Scott St, Reed Rd, Old Spanish Trail), filtered to vacant/under-improved commercial land.
- Stage 4: Site enrichment — FEMA flood zone, TxDOT AADT traffic, OSM competitor distances, OSRM
  real drive-time trade-area population.
- Stage 5: Weighted scorecard (30% demand / 25% competitive gap / 20% traffic / 15% cost-feasibility
  / 10% flood risk) → ranked recommendation.
- All data is public and free (US Census, OpenStreetMap, HCAD, FEMA, TxDOT); no API keys required.
  See `docs/methodology.md` for full source list and formulas.

## Slide 3 — Trade Area and Competitive Landscape
- Show the real 5-minute and 10-minute OSRM drive-time isochrones (actual road network, not a
  circle buffer) around the recommended site.
- 29,755 people within a 5-minute drive; 141,724 within 10 minutes.
- Nearest existing dollar-store competitor: 3.22 miles away. Nearest anchor retail (Walmart, Aldi,
  H-E-B): all on the corridor's northern edge, over a mile out — supports a standalone location.

## Slide 4 — Site-Level Evaluation
- Present the 5-site scorecard (`docs/results.md`): income fit, traffic, population, parcel size,
  competition, land cost, and flood risk side by side, with the Site B vs. Site D trade-off called
  out explicitly (Site D draws more raw population but at nearly double the land cost per acre and
  an above-target trade-area income).

## Slide 5 — Interactive Web Map
- `index.html` (Folium/Leaflet, hosted on GitHub Pages): submarket opportunity choropleth, all
  competitor and anchor locations, all 5 candidate sites with full data-backed popups, and the real
  drive-time trade area for the recommended site.

---

## Note to the hiring team

Hi Hossein,

Attached is the completed Houston Family Dollar site-selection case study. I built an end-to-end,
reproducible pipeline in Python (`scripts/01`–`12`) that pulls exclusively from free, public,
key-free data sources — US Census (via TIGERweb + Census Reporter), OpenStreetMap/Overpass, Harris
County Appraisal District parcels, FEMA's flood layer, TxDOT traffic counts, and OSRM for real
drive-time routing — to screen the entire county, lock in an underserved submarket (Sunnyside /
South Union), source real candidate parcels, and rank them into a recommendation.

- Methodology: `docs/methodology.md`
- Results & recommendation: `docs/results.md`
- Interactive map: `index.html` (GitHub Pages link once published)

Happy to walk through any part of the pipeline or the scoring logic.

Best regards,
Matt
