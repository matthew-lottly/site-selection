# Slide 4 of 12 - Data Sources and Validation Posture

## PASTE INTO SLIDE - TITLE

Why This Analysis Is Defensible

## PASTE INTO SLIDE - BODY

- Seven public sources, all free and keyless: US Census (TIGERweb + ACS), OpenStreetMap,
  Harris County Appraisal District, FEMA flood data, TxDOT traffic counts, and OSRM drive-time routing
- 528 real competitor and anchor locations pulled and categorized the way a site selector actually thinks about them
- Every number behind the recommended site was independently re-checked against the live source APIs, not just cached files
- 13 specific validation checks documented, including 6 real bugs that were found and fixed during the build
- One bug fix, caught by a self-imposed sensitivity-analysis stress test, changed the actual recommendation

## SPEAKER NOTES

Emphasize reproducibility and the anti-hallucination checks - this is what builds
executive trust quickly. The freeway-vs-frontage-road bug is the strongest proof
point: it shows the validation process catching something real, not just being
asserted. Full detail is in docs/data_validation.md if anyone wants to see it.
