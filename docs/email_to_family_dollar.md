# Email to Family Dollar - Data Sources & Roadmap

Paste-ready email explaining which data this analysis used and why, which paid data was deliberately
left out (and why, backed by an actual check rather than assumption), and what would make the model
production-grade with Family Dollar's own data. Companion to `docs/results.md` (the recommendation),
`docs/methodology.md` (how the pipeline works), `docs/data_validation.md` (full audit trail), and
`docs/limitations_and_diligence.md` (diligence roadmap).

---

**Subject:** Houston Family Dollar Site Selection - Data Sources, What's Missing, and Why

Hi [Name],

Following up on the Houston site-selection case study with the detail I promised on data: what I
used, what I deliberately left out, and what would make this production-grade with your team's own
data behind it.

## What this analysis is built on

Everything in this analysis - every number on the map and in the scorecard - traces to a live, free,
public source. No proprietary vendor data, nothing hand-typed or estimated:

- **U.S. Census Bureau** (TIGERweb boundaries, ACS 5-year demographics with real margins of error,
  vehicle access, housing tenure, and the Population Estimates Program for a real multi-year growth
  trend)
- **OpenStreetMap**, cross-checked against **Overture Maps** (the open-data project backed by Meta,
  Microsoft, and TomTom) - real competitor and co-tenant locations, road network, transit stops
- **Harris County Appraisal District** - real parcel boundaries, land use, appraised value
- **FEMA** - flood zone designation at every candidate site
- **TxDOT** - real traffic counts, independently verified against the live source
- **OSRM** - real drive-time routing (not circle buffers) for trade areas and the Huff gravity model
- **Houston Police Department** - real, point-level crime incident data near each site
- **HUD** - real, geocoded LIHTC affordable-housing properties and HUD Multifamily (FHA-insured/
  assisted-housing) properties, two distinct federal programs, both geocoded from their real addresses
- **Census LEHD** - real daytime/workplace population, not just residents
- **USDA** - real food-access ("food desert") data, directly relevant to a dollar-store demand thesis
- **Federal Qualified Opportunity Zones** - real tract-level designation, verified by point-in-polygon
  intersection at each candidate site, not assumed from a tract-ID list

I deliberately went back and re-checked this list three times before finalizing it - once to make sure
I hadn't missed a free alternative to something I was about to ask you for, a second time specifically
against how professional retail site-selection teams actually build their criteria (GrowthFactor,
Buxton, Kalibrate, and similar industry guides), and a third time to make sure nothing else free and
relevant had been missed, which is what turned up the Opportunity Zone and HUD Multifamily sources
above. Both of those ended up materially changing the recommended site - a genuine result of the model
getting more complete, not a tuning choice; see `docs/results.md` for exactly what moved and why. The
second pass also caught something worth flagging directly: an earlier draft still modeled Dollar Tree
as Family Dollar's "sister banner" and excluded it from competitive scoring - accurate until Dollar
Tree sold Family Dollar to private equity and the two officially separated on July 8, 2025. That's
corrected now - Dollar Tree is scored as a real competitor, the same as Dollar General and Five Below -
and it meaningfully changed the competitive-capture numbers across every site, which is exactly the
kind of thing I'd rather catch and show you than leave quietly wrong.

## What I deliberately left out, and why

Five categories of data I did **not** use - each checked directly for a free alternative rather than
assumed unavailable, so this list reflects what's actually missing, not what I didn't get around to:

1. **Mobile location / foot-traffic data** (e.g., Placer.ai, SafeGraph) - no free, bulk-usable tier
   exists. This is the biggest gap: it would replace my *modeled* competitive capture with *measured*
   visitation, visit frequency, and where your customers actually come from.
2. **Consumer spending data by category** (e.g., Esri Business Analyst, Nielsen) - the closest free
   equivalent (BLS Consumer Expenditure Survey) is published at a regional level, too coarse to
   compare individual sites against each other.
3. **Commercial real estate data** (e.g., CoStar) - no free source of real asking rents or lease
   comps; I used county tax-assessed values instead, which understate real acquisition cost.
4. **Enterprise-grade traffic data** (e.g., StreetLight, INRIX) - TxDOT's public counts are the free
   ceiling; they're real but update less frequently and less granularly than paid vehicle-probe data.
5. **Commercial crime-risk scoring** (e.g., CAP Index) - I built a real substitute from Houston
   police incident data, but it's not the normalized, predictive product a paid service offers.

## What would make this production-grade: your own data

This is the part I want to be specific about, because "give us your sales data" undersells what's
actually missing. Two named, standard techniques in retail site selection are structurally blocked
without your data, not by any public dataset:

- **Analog-store sales forecasting** - profiling a candidate site and forecasting its performance from
  a weighted average of your own existing stores with the closest-matching trade-area and site
  profile. This is the industry-standard way retailers turn a site score into a real revenue number,
  and it requires your store-level sales data specifically, not just "more data."
- **Regression-calibrated scorecard weights** - right now my scorecard weights (25% demand, 20% Huff
  capture, etc.) are documented and defensible but judgment-based. Best practice is to regress your
  own historical store performance against site attributes to find which factors *actually* predict
  success for Family Dollar's format - again, something only your own outcome data can calibrate.

Beyond those two, your team's own data would sharpen almost everything else in the model:

- **Historical cannibalization data from past store openings** - real observed sales impact when a
  new store opened near an existing one, replacing my rule-of-thumb distance/overlap buffers with a
  calibrated elasticity curve.
- **Customer loyalty/app geolocation data** - a real, measured trade area instead of a modeled
  drive-time isochrone.
- **Internal site-criteria standards** - your own minimum parking, ingress/egress, and turning-radius
  requirements in place of the generic industry benchmarks I used.
- **Loss-prevention/shrink data by store** - a sharper, Family-Dollar-specific risk signal than
  citywide police crime statistics.

## What's already solid, for what it's worth

Not everything here is a gap. I checked the core methodology - drive-time trade areas (not crude
concentric rings), the Huff gravity competitive model, and the cannibalization framework - against
current industry guidance, and it already matches or exceeds standard practice. The free-data
ceiling is real, but it's not the weak part of this analysis.

Happy to walk through any of this live, or run the model again once any of the above becomes
available.

Best,
Matthew Powers
