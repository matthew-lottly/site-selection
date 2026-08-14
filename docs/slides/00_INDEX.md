# Slide Deck - Build Instructions

Twelve slides, one file each (`01_recommendation.md` through `12_decision_ask.md`),
built to be assembled into Google Slides in about 15-20 minutes. Every number in
every file was checked directly against `data/processed/*.csv` - if you change the
underlying data and rerun the pipeline, regenerate the images
(`python -m pipeline.stages.s31_generate_slide_assets`) before reusing these files, since the
numbers would no longer match.

## How to build the deck

1. In Google Slides, create a new blank presentation, 16:9, one blank slide per file (12 total).
2. Open `01_recommendation.md` in a text or markdown editor.
3. Select and copy the text under "PASTE INTO SLIDE - TITLE", paste into the slide's title box.
4. Select and copy the text under "PASTE INTO SLIDE - BODY", paste into the slide's body text box.
   Google Slides pastes this as plain text - the "- " bullet lines will look fine as-is, or select
   the pasted text and click the bullet-list button to convert them to real bullets.
5. Drag the referenced PNG from `docs/slides/images/` onto the slide and place it per the file's
   "IMAGE" instructions.
6. Optional: copy the "SPEAKER NOTES" text into the Slides notes field (click below the slide).
7. Repeat for files 02 through 12, in order.

## Deck outline

| # | File | Title | Image |
| --- | ------ | ------- | ------- |
| 1 | `01_recommendation.md` | Houston Family Dollar Site Recommendation | `site_map.png` |
| 2 | `02_decision_summary.md` | Decision Summary | none |
| 3 | `03_scope_and_pipeline.md` | How the Recommendation Was Built | `pipeline_funnel.png` |
| 4 | `04_data_sources_validation.md` | Why This Analysis Is Defensible | none |
| 5 | `05_top_finalists.md` | Top 5 of 20 Citywide Finalists | `top5_scores.png` |
| 6 | `06_recommended_site_profile.md` | Why Brookhaven St & Cullen Blvd Wins | none |
| 7 | `07_key_tradeoff.md` | Weakest Crime Reading, Strongest Real Investment Signals | `key_tradeoff.png` |
| 8 | `08_robustness_check.md` | Sensitivity Analysis: Does the Pick Hold Up? | `sensitivity.png` |
| 9 | `09_confidence_intervals.md` | How Uncertain Are the Underlying Numbers? | `confidence_intervals.png` |
| 10 | `10_interactive_map.md` | What Leadership Can Inspect Live | your own screenshot(s) of `index.html` |
| 11 | `11_limitations_diligence.md` | What Must Be Verified Before Commitment | none |
| 12 | `12_decision_ask.md` | Decision and Next 30 Days | none |

## About the images

All six PNGs in `images/` are generated directly from the same
`data/processed/*.csv` and `houston_boundary.geojson` files the map and the
written docs use - none are mockups. They're built by
`pipeline/stages/s31_generate_slide_assets.py` (run it after any pipeline rerun to
refresh them) and colored from this project's own validated palette
(`pipeline/color.py`'s `ColorRamp.SEQUENTIAL_BLUE` / `ColorRamp.STATUS_RAMP`), so they match the web map's
symbology exactly: green + gold ring = recommended site, blue sequential ramp
= opportunity/magnitude, green-to-red = best-to-worst rank.

Slide 10 is the one exception - it needs a real screenshot of the live,
interactive `index.html`, which this script can't produce. See that file for
exactly what to capture.

## Presenter timing (15-18 minute version)

- Slides 1-2: 3 minutes
- Slides 3-4: 3 minutes
- Slides 5-8: 6 minutes
- Slides 9-10: 3 minutes
- Slides 11-12: 3 minutes

## Q&A backup points

- Why no revenue forecast? No public store-level sales data exists to calibrate a defensible dollar model;
  the named industry-standard fix is analog-store sales forecasting, which requires Family Dollar's own data.
- Why does the recommendation carry the field's worst crime score? Reported plainly rather than smoothed
  over - it's the real trade-off against a real Opportunity Zone designation and the largest nearby
  concentration of HUD-assisted housing of any finalist. See slide 7.
- Why trust the traffic number? Every AADT match was reverse-geocoded and verified to be a real
  arterial road, not a freeway mainline count - a bug in that exact check was found and fixed during
  the build (see `docs/data_validation.md` §2, item 10).
- Why did the recommendation change from an earlier revision? A fourth research pass found two more
  real, free federal data sources (Opportunity Zones, HUD Multifamily) that materially favor this site -
  a real result of the model getting more complete, not a tuning choice. See `docs/results.md`.
- Why is Dollar Tree counted as a competitor now? Dollar Tree sold Family Dollar to private equity and
  the two officially separated on 2025-07-08 - it's a real competitor now, not a "sister banner."

## Superseded files (removed)

Earlier drafts of this deck (`powerpoint_starter.md`, `powerpoint_slide_copy.md`,
`powerpoint_speaker_notes.md`, `presentation_outline.md`) covered the same ground in prose form under
a stale recommendation and have been removed - this `docs/slides/` folder is the current, paste-ready
version with real, regenerated chart images.
