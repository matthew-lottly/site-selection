# Limitations & Diligence Roadmap — Houston Family Dollar Site Selection

This document exists to draw an honest line: **what this desk-based analysis can prove from public
data, and what it explicitly cannot** — plus the concrete next steps that close that gap before a
real acquisition decision. It complements [`data_validation.md`](data_validation.md) (which
documents checks performed and errors caught during the build) rather than repeating it — read that
one for the audit trail, this one for what happens *after* the desk screen ends.

## Executive summary

Every number in this analysis traces to a live, free, public API — no proprietary vendor data
(SafeGraph, Placer.ai, Esri Business Analyst) and nothing hand-typed or estimated. That is a real
strength over a purely qualitative site walk. It is not, by itself, a substitute for the physical,
legal, and engineering diligence a real estate acquisition requires before signing anything. The two
categories below distinguish *why* each remaining gap exists — a genuinely unavailable free dataset
(Category A) versus a question that structurally requires a human on the ground or a licensed
professional's sign-off, not just a better API (Category B) — because the fix for each is different.

## Category A — Free/public-data constraints

Real gaps caused by what free, public data does and doesn't cover today. If a paid data source
(license, subscription) became available, several of these would close without changing the
methodology at all.

| Limitation | Why it exists | How this analysis handled it |
|---|---|---|
| **No predicted revenue / sales dollar figure** | Family Dollar does not publish store-level sales data, and no free public source does either. A revenue model without real sales data to calibrate it would be a fabricated number wearing a precise mask. | Both the Huff model and the cannibalization analysis stop at real, computed relative metrics instead — market-capture percentage and net-new population reach — that answer the same underlying business question without inventing a dollar figure. |
| **No property/violent crime metric** | Houston's open data portal (`data.houstontx.gov`) was checked directly via its CKAN catalog API (`package_search`, `package_show`) — it has no queryable crime dataset or downloadable incident feed, only static HTML report pages, and a `police-transparency-hub` package with zero attached resources. | Investigated as a candidate 6th metric, then explicitly dropped rather than scraped or estimated — scraping an unstable HTML format or interpolating a number would reintroduce exactly the kind of fabrication this project is built to avoid. Reported here as a real, checked-for data-availability gap, not a silent omission. |
| **Competitor travel time in the Huff model and cannibalization overlap is straight-line distance + a 25 mph average-speed assumption, not full OSRM network routing** | Full routing from every one of ~1,600 block groups to every one of 56 arch-rivals (and every existing FD store) would multiply the OSRM call count roughly 60x for a *secondary* input to a relative comparison metric. | Disclosed as a tractability trade-off, not hidden. The candidate site's own travel time — the number that actually varies by which site wins — uses real OSRM network routing throughout, not an approximation. |
| **Drive-time isochrone is a 128-point approximation (16 bearings × 8 distances), not a parcel-precise flood-fill** | A true flood-fill would require routing to every node on the OSM road network from every candidate — computationally possible but far beyond what a desk screen needs to rank 20 sites. | Documented explicitly as a strong approximation; can miss small dead-end pockets or one-way-street effects at the margins of the shape. |
| **OSM competitor coverage is not exhaustive** | OpenStreetMap tagging completeness varies by brand and area. Ross Dress for Less returned only 1 Houston match despite operating more locations — almost certainly an OSM tagging gap, not a real store count. | Reported as pulled, not patched with an estimated count. Flagged explicitly rather than presented as complete. |
| **ACS 5-year estimates carry real margins of error** | The Census Bureau's American Community Survey is a sample, not a full count — every estimate has statistical uncertainty by design. | Pulled and reported the real 90% confidence interval for every headline statistic (population, income, poverty, foreign-born share, Spanish-at-home share, household size, zero-vehicle household share, renter-occupied share), using the Bureau's own ratio-MOE propagation formula for derived rates rather than presenting point estimates as exact. Full table in `data_validation.md` §4. |

## Category B — Boundaries a desk-based GIS analysis cannot cross

These aren't missing datasets — they're questions that structurally require a person (a title
examiner, a civil engineer, a site visit) rather than a better API, no matter how much public data
improves.

| Limitation | Why it exists | How this analysis handled it |
|---|---|---|
| **Deed restrictions / restrictive covenants** | Houston has no municipal zoning — land use is instead governed partly by private deed restrictions recorded against a specific parcel, which requires a title search to surface. No public GIS layer exposes them. | Flagged per-site in the map's Site Details dashboard tab as `NOT VERIFIED — requires a title search`, rather than assumed clear. |
| **Ingress/egress geometry** (median breaks, left-turn lane availability, driveway permit feasibility) | This requires a civil site plan and often a TxDOT/City of Houston driveway permit review, not a GIS query. | Flagged as `NOT VERIFIED — requires a site plan / civil engineering review` rather than guessed from road centerline data. |
| **Engineered delivery-truck turning radius** (a 53-ft trailer needs a confirmed real geometric radius, not an eyeballed one) | Same reason — this is a civil-engineering sign-off, not a public dataset. | Only a real, approximate parcel bounding-box size (from actual HCAD parcel polygon vertices, haversine edge lengths) is reported, explicitly labeled as a directional gut-check, not a substitute for a civil site plan. |
| **Approximate lot dimensions are a bounding box, not a survey** | The HCAD parcel polygon is the real, public shape record, but a bounding box of an irregular polygon isn't the same as a certified plat survey. | Labeled `(bounding box, not a survey)` everywhere it's shown, including in the map's Site Details tab. |
| **On-the-ground conditions** (visibility from the road at eye level, existing curb cuts, utility pole placement, vegetation/sightline obstructions, current site cleanliness/encroachment) | No free public dataset substitutes for standing on the parcel. | Not claimed. This is the first item on the diligence roadmap below. |

## Why the recommendation itself needs one specific extra check

The recommended site — **6600 Stillwell St, Pecan Park** — sits on a road TxDOT's traffic count
resolves to **Gulf Freeway Frontage Road** (verified AADT 19,656, reverse-geocoded independently to
confirm it is genuinely a frontage road with legal driveway access, not the Gulf Freeway mainline
itself — see `data_validation.md` §2 for the frontage-road classification bug this project found and
fixed while building that exact check). A frontage-road parcel's ingress/egress can still be more
constrained than a standard arterial intersection (one-way frontage-road traffic flow, limited
U-turn/median-break points back toward the freeway), which is precisely the kind of geometry
Category B above says a desk analysis can't resolve. **This is the single highest-value diligence
item for this specific site** — see the roadmap's traffic-engineering step below.

The scorecard also shows a real trade-off worth surfacing directly rather than smoothing over: the
recommended site's cannibalization risk against Family Dollar's own existing network is **High**
(1.01 mi from an existing FD, 47.8% trade-area overlap), while the very-close #2 site (Cullen Blvd &
Brookhaven St, Sunnyside — 78.3 vs. 79.4, a 1.1-point gap) has a **Low** cannibalization profile and
a higher net-new population reach (43,688 vs. 23,138). Both are real, computed numbers, not
smoothed into a single "winner" narrative — see `docs/results.md` for the full comparison. A VP
weighing store-network cannibalization heavily may reasonably prefer the #2 site instead; that
judgment call is exactly what this document exists to make possible, not obscure.

## Diligence roadmap: from desk screen to acquisition decision

```
 THIS ANALYSIS                  NEXT STEPS (not yet performed)
┌────────────────┐   ┌──────────────┐   ┌───────────────┐   ┌──────────────────┐   ┌─────────────┐
│  Desk-based     │──▶│  Site visit  │──▶│ Title search  │──▶│ Traffic/ingress-  │──▶│  Utility &  │
│  citywide GIS   │   │  (visibility,│   │ & deed-       │   │ egress engineering│   │  permitting │
│  screen         │   │  curb cuts,  │   │ restriction   │   │ study (esp. the   │   │  check with │
│  (this repo)    │   │  conditions) │   │ review        │   │ Gulf Fwy frontage │   │  City of    │
│                 │   │              │   │               │   │ road access)      │   │  Houston    │
└────────────────┘   └──────────────┘   └───────────────┘   └──────────────────┘   └─────────────┘
                                                                                            │
                                                                                            ▼
                                                                                   ┌──────────────┐
                                                                                   │ Go / no-go & │
                                                                                   │ LOI decision │
                                                                                   └──────────────┘
```

1. **Site visit.** Confirm real-world visibility, existing curb cuts, sightlines, utility placement,
   and general parcel condition — none of which any public GIS dataset covers.
2. **Title search.** Surface any recorded deed restrictions or restrictive covenants against HCAD
   parcel 0410300000175 — required because Houston's lack of municipal zoning shifts more of the
   land-use-compatibility question onto private deed restrictions than in a zoned city.
3. **Traffic-engineering / ingress-egress review**, specifically evaluating access from Gulf Freeway
   Frontage Road — confirm real driveway permit feasibility, median-break/turn-lane geometry, and
   that the 19,656 AADT reading genuinely reflects frontage-road (not freeway-adjacent-but-different)
   traffic exposure for a retail pad at this exact parcel.
4. **Utility availability and permitting check** with the City of Houston — water/sewer/electric
   service confirmation and a parking-code review (Houston's general off-street ratio is roughly 1
   space per 200–300 sq ft of retail, cited as informational context, not a parcel-verified figure).
5. **Cannibalization judgment call.** Weigh the recommended site's High cannibalization risk against
   its stronger raw score and traffic reading versus the #2 site's Low-risk, higher-net-new-reach
   profile (see above) — a real strategic trade-off for the VP to make explicitly, not one this
   analysis resolves on its behalf.

## This isn't a one-time disclaimer — it held up under its own audit

The rigor claim above isn't just asserted: building the multi-scenario **sensitivity analysis**
(re-aggregating the same real per-factor scores under 5 different, defensible weighting schemes —
see the map's Scorecard tab and `data/processed/sensitivity_analysis.csv`) surfaced an implausible
score for one candidate, which traced back to a real bug in the freeway-vs-frontage-road
classification regex. Fixing it changed the actual recommendation. That fix, and the live
re-verification performed on the corrected winner afterward, is documented in full in
`data_validation.md` §2 — included there, and referenced here, specifically because a diligence
document that only lists limitations found *before* the pipeline finished, and never one caught by
checking its own output, would be less credible, not more.
