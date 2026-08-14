# Slide 4 of 12 - Data Sources and Validation Posture

## PASTE INTO SLIDE - TITLE

Why This Analysis Is Defensible

## PASTE INTO SLIDE - BODY

- 18 public data feeds, all free and keyless: Census (TIGERweb, ACS, population estimates), OpenStreetMap
  and Overture Maps, HCAD, FEMA, TxDOT, OSRM, HPD crime, HUD LIHTC and Multifamily, Census LEHD, USDA, Opportunity Zones
- 528 real competitor/anchor locations (plus 54 more found by an independent Overture cross-check), categorized
  the way a site selector actually thinks about them - including Dollar Tree, a direct competitor since its
  July 2025 separation from Family Dollar
- Every number behind the recommended site was independently re-checked against the live source APIs, not just cached files
- 26 specific validation checks documented across four research passes, including real bugs found and fixed
  along the way - not just asserted, demonstrated
- Two bugs changed the actual recommendation: an early freeway-vs-frontage-road traffic misclassification,
  and (this round) a HUD API returning no geometry, fixed with real address geocoding rather than dropped

## SPEAKER NOTES

Emphasize reproducibility and the anti-hallucination checks - this is what builds
executive trust quickly. The freeway-vs-frontage-road bug and the HUD geocoding fix are
the strongest proof points: they show the validation process catching something real, not
just being asserted. Full detail is in docs/data_validation.md if anyone wants to see it.
