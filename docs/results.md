# Results & Recommendation — Houston Family Dollar Site Selection (Citywide)

See [`methodology.md`](methodology.md) for how every number below was produced,
[`data_validation.md`](data_validation.md) for the full source catalog, audit trail, and confidence
intervals, and `index.html` for the interactive map (open the **Analysis Dashboard** drawer at the
bottom for the full scorecard, cannibalization table, and confidence intervals live).

## Recommendation

> **Cullen Blvd & Brookhaven St, Sunnyside, Houston, TX 77051** — a 0.66-acre vacant commercial
> parcel, HCAD account 0430390000003.

Selected from 20 real, HCAD-verified candidate parcels spanning 10 Houston neighborhoods (Alief,
Westchase, Sunnyside, Gulfton, Braeswood, Denver Harbor, East Houston, Braeburn, Acres Homes, and
Central Southwest Houston) — the result of a citywide opportunity screen across all 1,115 Harris
County Census tracts, scoped to the 643 tracts actually inside Houston city limits.

**Why this site, in five points:**

1. **It won a citywide comparison, not a first-look pick.** Two of the top three finalists both
   landed in Sunnyside, even after searching nine other demographically similar Houston
   neighborhoods for something stronger. That convergence is itself evidence the pick is real, not
   an artifact of where the search started.
2. **It has real, verified traffic that clears the industry-standard minimum.** 20,532 vehicles/day
   on Cullen Blvd (TxDOT 2025 AADT) — the station's coordinates were independently reverse-geocoded
   to confirm it really is Cullen Blvd, not a mismatched freeway route. This is the deciding factor
   against the near-tied alternative below.
3. **It is the safest site in the whole field on cannibalization.** 4.07 miles from the nearest
   existing Family Dollar, zero real trade-area overlap, and the **highest net-new population reach
   of any of the 20 candidates (43,688 people)** — meaning essentially none of its 5-minute drive-time
   trade area is already served by an existing FD store. See §Cannibalization below.
4. **Real operational detail checks out.** A posted 40 mph speed limit on Cullen Blvd (OSM-tagged) —
   squarely in the 35–45 mph "impulse-stop visibility" range that works for a discount-retail
   format — and two real gas stations within 650 feet as shared-trip co-tenants.
5. **It is shovel-ready and low-risk otherwise.** Vacant commercial land (no demolition), FEMA Zone X
   (outside the mapped Special Flood Hazard Area), $373,516 land value ($566k/acre — mid-range among
   the finalists).

### The near-tie, and why the recommendation isn't the top raw score

The single highest **raw weighted score** among all 20 candidates actually belongs to a different
site 0.4 miles away — **1023 Niagara St, also Sunnyside** (72.7 vs. 71.1) — driven by a slightly
larger competitive gap and Huff share. But that site carries only **1,547 vehicles/day** on its
frontage road, well under the 8,000 AADT industry rule-of-thumb minimum for a discount-retail pad to
get real drive-by visibility. Rather than let a 15%-weighted traffic factor get averaged away by a
strong score everywhere else, the scoring logic applies the AADT benchmark as a hard gate on the
**primary recommendation**: the highest-scoring site that also clears it. 1023 Niagara St remains
visible in the scorecard (and is the natural fallback if a traffic-engineering review of Cullen Blvd
turns up a problem), but is not selected as the recommendation on that basis.

## Top 5 of 20 citywide finalists

| Rank | Neighborhood | Site | Traffic (verified) | Nearest Family Dollar | Cannibalization Risk | Net-New Pop. | **Score** |
|---|---|---|---|---|---|---|---|
| **★ Recommended** | **Sunnyside** | **Cullen Blvd & Brookhaven St** | 20,532 vpd ✅ ≥8k | 4.07 mi | **Low** | **43,688** | **71.1** |
| Raw #1 | Sunnyside | 1023 Niagara St | 1,547 vpd ❌ &lt;8k | 4.16 mi | Low | 35,427 | 72.7 |
| Raw #3 | Pecan Park | 6600 Stillwell St | 2,980 vpd ❌ &lt;8k | 1.01 mi | High (hard buffer) | 23,138 | 70.7 |
| Raw #4 | Pecan Park | Broadway St & La Porte Fwy | 2,651 vpd ❌ &lt;8k | 1.18 mi | High (hard buffer) | 12,909 | 68.5 |
| Raw #5 | Parkridge (Alief) | Eldridge Pkwy & Westhollow Pkwy | 32,634 vpd ✅ ≥8k | 1.48 mi | High (trade-area overlap) | 9,679 | 64.4 |

Full 20-site detail, every per-factor score, cannibalization math, and micro-site operational data
(speed limits, co-tenants, approximate lot dimensions) is in `data/processed/scorecard.csv`,
`data/processed/cannibalization.csv`, `data/processed/microsite_details.csv`, and live in the map's
Analysis Dashboard.

## Cannibalization: existing Family Dollar stores are network, not competition

Existing Family Dollar locations were tracked separately from competitors throughout — the real
question is how much of a new store's trade area a nearby existing FD store already serves, not
whether FD "competes with itself." Method: a hard buffer (<1.2 mi from an existing FD auto-flags
High risk), a real-drive-time trade-area overlap percentage against a 1.5-mile radius of the nearest
existing FD, and a **net-new population reach** figure (5-minute drive population minus the overlap)
as a real, computed stand-in for "how much of this is actually incremental" — deliberately not a
dollar figure, since no public store-level sales data exists to calibrate a revenue model (a number
without that grounding would be fabricated precision dressed up as insight).

The recommended site and its raw-score competitor (1023 Niagara St) are the only two of the 20
candidates with genuinely **Low** cannibalization risk and zero measured trade-area overlap — every
other finalist sits close enough to an existing FD that a meaningful share of its trade area is
already served. Among the two Low-risk options, the recommended site reaches **8,261 more net-new
people** (43,688 vs. 35,427).

## Competitive landscape (recategorized to match how a real site selector thinks about it)

- **Family Dollar (61 existing locations)** — the company's own network, tracked for cannibalization
  above, not counted as competition.
- **Direct arch-rivals (56: Dollar General, Five Below)** — the real competitive threat; this is the
  set the Huff gravity model measures market capture against (49.0% for the recommended site — the
  second-highest of all 20 candidates among sites that also clear the traffic benchmark).
- **Sister banner (61: Dollar Tree)** — same parent company (Dollar Tree, Inc.) as Family Dollar,
  tracked separately since modeling it as a competitive threat would misstate the real business
  relationship.
- **Value grocery (225: Aldi, Kroger, H-E-B, Fiesta Mart, Food Town, Save A Lot, and Houston-specific
  banners Joe V's Smart Shop and Mi Tienda)** — the extreme-value grocers Houston's low-income
  households split their budget with.
- **Big-box anchors (125: Walmart, Target, Burlington, Ross)** — general-merchandise price anchors
  and regional traffic generators, tracked for context but excluded from the Huff competitive set
  (different shopping mission, and their much larger square footage would mathematically swamp every
  candidate's modeled share to a non-discriminating near-zero regardless of where it actually sits —
  tested and confirmed before this design choice was made).

## Citywide context

- **10 opportunity neighborhoods screened**, chosen to be at least 2.75 miles apart so the search
  covered geographically distinct parts of the city, not one cluster of adjacent tracts.
- **528 real store locations** pulled from OpenStreetMap across 15 banners (see categorization
  above).
- **2,328,253 people** live inside the real Houston city boundary per the Census Bureau's own
  place-level 2024 ACS 5-year estimate (90% CI: 2,328,057–2,328,449) — independently close to the
  2,312,201 figure obtained by summing block-group populations inside the same boundary polygon, a
  useful cross-check that the city-limits filtering worked correctly. Full confidence-interval table
  for population, income, poverty, foreign-born share, Spanish-at-home share, and household size is
  in [`data_validation.md`](data_validation.md) and the map's Confidence Intervals dashboard tab.
- **275 real HCAD parcels** qualified as realistic new-store sites across all 10 neighborhoods before
  narrowing to the 20-site finalist shortlist.

## Suggested next steps for the VP

1. Commission a formal traffic-engineering / ingress-egress study for the Cullen Blvd frontage —
   this is the one factor a desk analysis can't fully settle, and it's the deciding factor here.
2. Confirm zoning/permitting and utility availability for the Cullen Blvd & Brookhaven St parcel
   with the City of Houston; note Houston has no municipal zoning, so this runs through HCAD
   land-use codes, deed restrictions, and the city's parking/development code instead (see
   `data_validation.md` §5).
3. Title search to confirm no restrictive covenants — not covered by any public data source used
   here, and explicitly flagged as unverified in the Site Details dashboard tab.
4. Site visit to confirm ground conditions, visibility, and ingress/egress geometry (median breaks,
   turning movements) that public GIS data can't fully resolve.
5. If Cullen Blvd falls through, 1023 Niagara St (also Sunnyside, same Low cannibalization profile)
   is the natural fallback pending its own traffic reading; Pecan Park (6600 Stillwell St) is the
   next-best option from a different part of the city.
