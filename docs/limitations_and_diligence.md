# Limitations & Diligence Roadmap - Houston Family Dollar Site Selection

This document exists to draw an honest line: **what this desk-based analysis can prove from public
data, and what it explicitly cannot** - plus the concrete next steps that close that gap before a
real acquisition decision. It complements [`data_validation.md`](data_validation.md) (which
documents checks performed and errors caught during the build) rather than repeating it - read that
one for the audit trail, this one for what happens *after* the desk screen ends.

## Executive summary

Every number in this analysis traces to a live, free, public API - no proprietary vendor data
(SafeGraph, Placer.ai, Esri Business Analyst) and nothing hand-typed or estimated. That is a real
strength over a purely qualitative site walk. It is not, by itself, a substitute for the physical,
legal, and engineering diligence a real estate acquisition requires before signing anything. The two
categories below distinguish *why* each remaining gap exists - a genuinely unavailable free dataset
(Category A) versus a question that structurally requires a human on the ground or a licensed
professional's sign-off, not just a better API (Category B) - because the fix for each is different.

## Category A - Free/public-data constraints

Real gaps caused by what free, public data does and doesn't cover today. If a paid data source
(license, subscription) became available, several of these would close without changing the
methodology at all.

| Limitation | Why it exists | How this analysis handled it |
| --- | --- | --- |
| **No predicted revenue / sales dollar figure** | Family Dollar does not publish store-level sales data, and no free public source does either. A revenue model without real sales data to calibrate it would be a fabricated number wearing a precise mask. | Both the Huff model and the cannibalization analysis stop at real, computed relative metrics instead - market-capture percentage and net-new population reach - that answer the same underlying business question without inventing a dollar figure. |
| **Crime data reflects reported incidents only** | HPD's NIBRS export (now used as a real 7th scoring factor - see below) is police-recorded crime, not a victimization survey. Some crime goes unreported, and reporting rates can vary by neighborhood - a limitation of any police-recorded crime statistic nationally, not specific to this analysis. It is also a trailing-12-month snapshot, not a multi-year trend. | Reported as real incident counts (violent/property, within 0.5mi, trailing 12mo), not smoothed into a longer trend or reweighted for suspected under-reporting - the raw, real number is more defensible than a guessed correction. |
| **Competitor travel time in the Huff model and cannibalization overlap is straight-line distance + a 25 mph average-speed assumption, not full OSRM network routing** | Full routing from every one of ~1,600 block groups to every one of 56 arch-rivals (and every existing FD store) would multiply the OSRM call count roughly 60x for a *secondary* input to a relative comparison metric. | Disclosed as a tractability trade-off, not hidden. The candidate site's own travel time - the number that actually varies by which site wins - uses real OSRM network routing throughout, not an approximation. |
| **Drive-time isochrone is a 128-point approximation (16 bearings × 8 distances), not a parcel-precise flood-fill** | A true flood-fill would require routing to every node on the OSM road network from every candidate - computationally possible but far beyond what a desk screen needs to rank 20 sites. | Documented explicitly as a strong approximation; can miss small dead-end pockets or one-way-street effects at the margins of the shape. |
| **OSM competitor coverage is not exhaustive** | OpenStreetMap tagging completeness varies by brand and area. Ross Dress for Less returned only 1 Houston match despite operating more locations - almost certainly an OSM tagging gap, not a real store count. | Reported as pulled, not patched with an estimated count. Flagged explicitly rather than presented as complete. |
| **ACS 5-year estimates carry real margins of error** | The Census Bureau's American Community Survey is a sample, not a full count - every estimate has statistical uncertainty by design. | Pulled and reported the real 90% confidence interval for every headline statistic (population, income, poverty, foreign-born share, Spanish-at-home share, household size, zero-vehicle household share, renter-occupied share), using the Bureau's own ratio-MOE propagation formula for derived rates rather than presenting point estimates as exact. Full table in `data_validation.md` §4. |

## Category B - Boundaries a desk-based GIS analysis cannot cross

These aren't missing datasets - they're questions that structurally require a person (a title
examiner, a civil engineer, a site visit) rather than a better API, no matter how much public data
improves.

| Limitation | Why it exists | How this analysis handled it |
| --- | --- | --- |
| **Deed restrictions / restrictive covenants** | Houston has no municipal zoning - land use is instead governed partly by private deed restrictions recorded against a specific parcel, which requires a title search to surface. No public GIS layer exposes them. | Flagged per-site in the map's Site Details dashboard tab as `NOT VERIFIED - requires a title search`, rather than assumed clear. |
| **Ingress/egress geometry** (median breaks, left-turn lane availability, driveway permit feasibility) | This requires a civil site plan and often a TxDOT/City of Houston driveway permit review, not a GIS query. | Flagged as `NOT VERIFIED - requires a site plan / civil engineering review` rather than guessed from road centerline data. |
| **Engineered delivery-truck turning radius** (a 53-ft trailer needs a confirmed real geometric radius, not an eyeballed one) | Same reason - this is a civil-engineering sign-off, not a public dataset. | Only a real, approximate parcel bounding-box size (from actual HCAD parcel polygon vertices, haversine edge lengths) is reported, explicitly labeled as a directional gut-check, not a substitute for a civil site plan. |
| **Approximate lot dimensions are a bounding box, not a survey** | The HCAD parcel polygon is the real, public shape record, but a bounding box of an irregular polygon isn't the same as a certified plat survey. | Labeled `(bounding box, not a survey)` everywhere it's shown, including in the map's Site Details tab. |
| **On-the-ground conditions** (visibility from the road at eye level, existing curb cuts, utility pole placement, vegetation/sightline obstructions, current site cleanliness/encroachment) | No free public dataset substitutes for standing on the parcel. | Not claimed. This is the first item on the diligence roadmap below. |

## Why the recommendation itself needs one specific extra check

The recommended site - **Eldridge Parkway & Westhollow Parkway, Parkridge** - has its verified AADT
(32,634, the highest of any finalist) attributed to **Bellaire Boulevard**, a real arterial a short
distance from the parcel's exact intersection (the AADT station sits 0.97 mi away, the closest
genuine arterial reading available - see `data_validation.md` §2 for how every AADT match across all
20 finalists is reverse-geocoded and screened for freeway-mainline contamination). The parcel itself
sits on Eldridge Parkway/Westhollow Parkway, classified from OSM tags as a collector/local connector,
not the arterial the traffic count is drawn from - confirming the driveway/ingress geometry actually
available at this specific intersection, not just the nearby arterial's traffic volume, is the single
highest-value diligence item for this site. See the roadmap's traffic-engineering step below.

The scorecard also shows a real, three-way trade-off worth surfacing directly rather than smoothing
over: the recommended site's cannibalization risk against Family Dollar's own existing network is
**High** (1.48 mi from an existing FD, 70.6% trade-area overlap, the lowest net-new population reach
of the top 5 finalists at 9,679) and its trade-area median income ($61,815) sits above the $20k-$55k
core demand band, in exchange for by far the lowest real crime reading in the top tier (2 violent + 4
property Part I incidents within 0.5mi, vs. 24+62 at the #2 site and 60+68 at the #3 site) and the
strongest traffic and Huff capture of any finalist. None of the top 3 finalists wins on every
dimension - see `docs/results.md` for the full comparison. A VP weighing real crime exposure most
heavily gets this recommendation; one weighing store-network cannibalization or core-income-band
demand most heavily may reasonably prefer the #2 (6600 Stillwell St) or #3 (Brookhaven St & Cullen
Blvd, Sunnyside) site instead. That judgment call is exactly what this document exists to make
possible, not obscure.

## Diligence roadmap: from desk screen to acquisition decision

```text
 THIS ANALYSIS                  NEXT STEPS (not yet performed)
┌────────────────┐   ┌──────────────┐   ┌───────────────┐   ┌──────────────────┐   ┌─────────────┐
│  Desk-based     │──▶│  Site visit  │──▶│ Title search  │──▶│ Traffic/ingress-  │──▶│  Utility &  │
│  citywide GIS   │   │  (visibility,│   │ & deed-       │   │ egress engineering│   │  permitting │
│  screen         │   │  curb cuts,  │   │ restriction   │   │ study (confirm    │   │  check with │
│  (this repo)    │   │  conditions) │   │ review        │   │ real driveway     │   │  City of    │
│                 │   │              │   │               │   │ access/geometry)  │   │  Houston    │
└────────────────┘   └──────────────┘   └───────────────┘   └──────────────────┘   └─────────────┘
                                                                                            │
                                                                                            ▼
                                                                                   ┌──────────────┐
                                                                                   │ Go / no-go & │
                                                                                   │ LOI decision │
                                                                                   └──────────────┘
```

1. **Site visit.** Confirm real-world visibility, existing curb cuts, sightlines, utility placement,
   and general parcel condition - none of which any public GIS dataset covers.
2. **Title search.** Surface any recorded deed restrictions or restrictive covenants against HCAD
   parcel 0582970000612 - required because Houston's lack of municipal zoning shifts more of the
   land-use-compatibility question onto private deed restrictions than in a zoned city.
3. **Traffic-engineering / ingress-egress review** at the Eldridge Parkway & Westhollow Parkway
   intersection - confirm real driveway permit feasibility and turn-lane geometry at this specific
   collector-road intersection, and that the 32,634 AADT reading (drawn from the nearest verified
   arterial station, 0.97 mi away on Bellaire Boulevard) is a fair proxy for actual frontage traffic
   at this exact parcel.
4. **Utility availability and permitting check** with the City of Houston - water/sewer/electric
   service confirmation and a parking-code review (Houston's general off-street ratio is roughly 1
   space per 200-300 sq ft of retail, cited as informational context, not a parcel-verified figure).
5. **Three-way trade-off judgment call.** Weigh the recommended site's lowest-in-field crime exposure
   and strongest traffic/Huff capture against its High cannibalization risk and above-core-band trade
   income, versus the #2 site's (6600 Stillwell St) stronger core-income demand and #3 site's
   (Brookhaven St & Cullen Blvd, Sunnyside) Low cannibalization risk (see above) - a real strategic
   trade-off for the VP to make explicitly, not one this analysis resolves on its behalf.

## This isn't a one-time disclaimer - it held up under its own audit

The rigor claim above isn't just asserted: building the multi-scenario **sensitivity analysis**
(re-aggregating the same real per-factor scores under 6 different, defensible weighting schemes -
see the map's Scorecard tab and `data/processed/sensitivity_analysis.csv`) surfaced an implausible
score for one candidate, which traced back to a real bug in the freeway-vs-frontage-road
classification regex. Fixing it changed the actual recommendation. That fix, and the live
re-verification performed on the corrected winner afterward, is documented in full in
`data_validation.md` §2 - included there, and referenced here, specifically because a diligence
document that only lists limitations found *before* the pipeline finished, and never one caught by
checking its own output, would be less credible, not more.
