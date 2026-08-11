# PowerPoint Starter Pack

Use this file as your working build sheet while creating the deck in PowerPoint.

## Recommended deck structure (12 slides)

1. Title + one-line recommendation
2. Executive decision summary
3. Business question and scope
4. Data sources and validation posture
5. Method pipeline (county -> city -> parcel)
6. Top 5 finalists and score comparison
7. Recommended site profile (6600 Stillwell St)
8. Cannibalization trade-off (recommended vs #2)
9. Sensitivity analysis and robustness
10. Map walkthrough (layers and dashboard)
11. Risks, limits, and diligence roadmap
12. Decision ask and next 30-day plan

## Build instructions in PowerPoint

1. Create a new 16:9 deck.
2. Add a simple slide master with one accent color family (blue) and neutral grays.
3. Use section headers at slides 1, 5, 10, and 12.
4. Keep each slide to one headline and three supporting bullets max.
5. Place one data visual per slide (table, map, or chart), not multiple competing visuals.
6. Keep consistent footer: "Houston Family Dollar Site Selection | Date | Confidential".

## Visual assets to export from this repo

- Map hero screenshot from `index.html` (default view + top candidate marker)
- FEMA overlay screenshot from `index.html` with flood layer toggled on
- Scorecard table from `data/processed/scorecard.csv`
- Cannibalization comparison from `data/processed/cannibalization.csv`
- Sensitivity table from `data/processed/sensitivity_analysis.csv`
- Confidence intervals summary from `data/processed/houston_demographics_ci.csv` and `data/processed/houston_vehicle_tenure_ci.csv`

## Slide-level objective checklist

- Slide 1 answers: what is recommended?
- Slide 2 answers: why should leadership trust this recommendation?
- Slide 6 answers: how much better is #1 than alternatives?
- Slide 8 answers: what is the key trade-off and decision fork?
- Slide 11 answers: what remains unverified before committing capital?
- Slide 12 answers: what decision is needed now?

## Presenter timing target (15-18 minute version)

- Slides 1-2: 3 minutes
- Slides 3-5: 4 minutes
- Slides 6-9: 6 minutes
- Slides 10-12: 4 minutes

## Optional appendix slides

- Full 20-site scorecard
- Moran's I and spatial CV outputs
- Source-by-source data provenance table
- Definitions (Huff, AADT gate, overlap %, net-new population)
