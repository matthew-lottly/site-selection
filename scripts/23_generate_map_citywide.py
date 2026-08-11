"""Step 23 (supersedes scripts/12_generate_map.py): build the executive-facing
interactive web map from the citywide pipeline outputs. Every layer and every
dashboard number traces back to a data/processed/*.csv or *.geojson file
produced by scripts 01-25.

Symbology:
  - candidate sites: numbered rank badges on a validated best->worst ramp
  - competitors: 5 categories (Family Dollar / arch-rival / sister banner /
    value grocery / big-box), all cool hues, validated distinct from each
    other and from the warm rank-ramp/choropleth colors sharing the map
  - choropleth: amber->deep-red sequential ramp, opacity scaled to score
  - a bottom-drawer dashboard: Scorecard / Cannibalization / Confidence
    Intervals / Data Sources & Validation tabs
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import folium
from folium import plugins

from lib import COMPETITOR_COLORS, PROCESSED, ROOT, SEQUENTIAL_ORANGE, STATUS_RAMP, ramp_color

MAP_BOUNDS = {"lat_min": 29.52, "lat_max": 30.11, "lon_min": -95.79, "lon_max": -95.01}

COMPETITOR_LABELS = {
    "family_dollar": "Family Dollar (existing -- not a competitor)",
    "arch_rival": "Direct arch-rival (Dollar General, Five Below)",
    "sister_banner": "Sister banner (Dollar Tree)",
    "value_grocery": "Value grocery (Aldi, Joe V's, Mi Tienda, Fiesta, etc.)",
    "big_box_anchor": "Big-box anchor (Walmart, Target, etc.)",
}


def load_csv(name: str) -> list[dict]:
    with open(PROCESSED / name, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_json(name: str) -> dict:
    return json.loads((PROCESSED / name).read_text(encoding="utf-8"))


POPUP_CSS = """
<style>
  .exec-card { font-family: 'Segoe UI', Arial, sans-serif; width: 300px; padding: 6px 8px; }
  .exec-title { font-size: 14px; font-weight: 700; color: #1E3A8A; border-bottom: 2px solid #D97706; padding-bottom: 4px; margin-bottom: 6px; }
  .exec-metric { font-size: 12px; margin: 4px 0; color: #1F2937; font-weight: 700; display: flex; justify-content: space-between; gap: 8px; }
  .exec-metric span:first-child { color: #374151; font-weight: 600; }
  .exec-val { font-weight: 700; color: #1F2937; text-align: right; }
  .winner-tag { background-color: #0ca30c; color: white; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: 700; letter-spacing: .03em; }
  .rank-tag { color: white; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: 700; }
  .src-note { font-size: 10px; color: #64748B; margin-top: 6px; border-top: 1px solid #E2E8F0; padding-top: 4px; font-weight: 400; }
  .warn-note { font-size: 11px; color: #92400E; background: #FEF3C7; padding: 4px 6px; border-radius: 4px; margin-top: 4px; font-weight: 600; }
  .good-note { font-size: 11px; color: #14532D; background: #DCFCE7; padding: 4px 6px; border-radius: 4px; margin-top: 4px; font-weight: 600; }
</style>
"""

TITLE_HTML = """
<div style="position: fixed; top: 12px; left: 60px; z-index: 9999; background: white;
            padding: 10px 16px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,.25);
            font-family: 'Segoe UI', Arial, sans-serif; max-width: 400px;">
  <div style="font-size: 15px; font-weight: 700; color: #1E3A8A;">Family Dollar &mdash; Houston Site Selection</div>
  <div style="font-size: 12px; color: #475569; margin-top: 2px;">Citywide screen &middot; 10 neighborhoods &middot; 20 real candidate sites</div>
  <div style="font-size: 12px; color: #0D9488; margin-top: 2px; font-weight: 600;">Recommended: Cullen Blvd &amp; Brookhaven St, Sunnyside</div>
</div>
"""


def build_legend_html(rank_ramp_css: str) -> str:
    section_head = "font-weight:700; color:#1F2937; font-size:11px; text-transform:uppercase; letter-spacing:.04em; margin-bottom:7px;"
    row_text = "color:#374151; font-weight:600;"

    def dot(color: str, label: str) -> str:
        return (
            f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:5px;">'
            f'<span style="width:11px; height:11px; border-radius:50%; background:{color}; border:1.5px solid #fff; '
            f'box-shadow:0 0 0 .5px {color}; display:inline-block; flex-shrink:0;"></span>'
            f'<span style="{row_text}">{label}</span></div>'
        )

    competitor_rows = "".join(
        dot(COMPETITOR_COLORS[k], v.split(" (")[0]) for k, v in COMPETITOR_LABELS.items()
    )

    return f"""
<div style="position: fixed; bottom: 20px; left: 12px; z-index: 9999; background: white;
            padding: 14px 16px; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,.28);
            font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; max-width: 272px;">
  <div style="font-weight:700; font-size:13px; color:#1E3A8A; margin-bottom:12px;">Legend</div>

  <div style="{section_head}">Candidate sites (by score)</div>
  <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
    <div style="width:22px; height:22px; border-radius:50%; background:#0ca30c; border:2px solid #fff; box-shadow:0 1px 3px rgba(0,0,0,.35); flex-shrink:0; display:flex; align-items:center; justify-content:center; color:#fff; font-size:12px;">&#9733;</div>
    <span style="{row_text}">Recommended site</span>
  </div>
  <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
    <div style="width:18px; height:18px; border-radius:50%; background:#d03b3b; border:2px solid #fff; box-shadow:0 1px 3px rgba(0,0,0,.35); flex-shrink:0;"></div>
    <span style="{row_text}">Other candidate sites, numbered by rank</span>
  </div>
  <div style="height:9px; border-radius:5px; margin-bottom:3px; background:{rank_ramp_css};"></div>
  <div style="display:flex; justify-content:space-between; color:#6B7280; font-size:10.5px; margin-bottom:12px; font-weight:600;">
    <span>Best</span><span>Worst</span>
  </div>

  <div style="border-top:1px solid #E5E7EB; margin:10px 0;"></div>
  <div style="{section_head}">Competitors</div>
  {competitor_rows}

  <div style="border-top:1px solid #E5E7EB; margin:10px 0;"></div>
  <div style="{section_head}">Trade area (recommended site)</div>
  <div style="display:flex; align-items:center; gap:8px; margin-bottom:5px;"><span style="width:16px; height:11px; background:#0D9488; opacity:.4; border:1px solid #0D9488; display:inline-block; flex-shrink:0;"></span><span style="{row_text}">5-min drive (OSRM)</span></div>
  <div style="display:flex; align-items:center; gap:8px; margin-bottom:12px;"><span style="width:16px; height:11px; background:#0D9488; opacity:.14; border:1px dashed #0D9488; display:inline-block; flex-shrink:0;"></span><span style="{row_text}">10-min drive (OSRM)</span></div>

  <div style="border-top:1px solid #E5E7EB; margin:10px 0;"></div>
  <div style="{section_head}">Opportunity score</div>
  <div style="height:9px; border-radius:5px; margin-bottom:3px; background:linear-gradient(90deg,{','.join(SEQUENTIAL_ORANGE)});"></div>
  <div style="display:flex; justify-content:space-between; color:#6B7280; font-size:10.5px; font-weight:600;">
    <span>Lower (served)</span><span>Higher (underserved)</span>
  </div>

  <div style="border-top:1px solid #E5E7EB; margin:10px 0;"></div>
  <div style="color:#6B7280; font-size:10.5px;">Full scorecard, cannibalization math, confidence
  intervals, and data-source audit trail: open the <b>Analysis Dashboard</b> drawer (bottom of screen).</div>
</div>
"""


def rank_badge_icon(rank: int, color: str, is_winner: bool) -> folium.DivIcon:
    """A clean circular rank badge instead of a busy icon-in-a-pin marker --
    gives the 20 candidate sites clear visual priority over the competitor
    dots and the choropleth without competing icon shapes."""
    if is_winner:
        size = 36
        html = f"""
        <div style="width:{size}px; height:{size}px; border-radius:50%; background:{color};
                    border:3px solid #ffffff; box-shadow:0 0 0 2.5px {color}, 0 3px 8px rgba(0,0,0,.45);
                    display:flex; align-items:center; justify-content:center;
                    color:#ffffff; font-size:17px; font-family:'Segoe UI',Arial,sans-serif;">&#9733;</div>
        """
    else:
        size = 24
        html = f"""
        <div style="width:{size}px; height:{size}px; border-radius:50%; background:{color};
                    border:2px solid #ffffff; box-shadow:0 1px 4px rgba(0,0,0,.4);
                    display:flex; align-items:center; justify-content:center;
                    color:#ffffff; font-weight:700; font-size:11px; font-family:'Segoe UI',Arial,sans-serif;">{rank}</div>
        """
    return folium.DivIcon(html=html, icon_size=(size, size), icon_anchor=(size // 2, size // 2))


# --------------------------------------------------------------------------
# Bottom-drawer dashboard
# --------------------------------------------------------------------------

def _risk_badge(risk: str) -> str:
    color = "#0ca30c" if risk == "Low" else ("#fab219" if risk == "Moderate" else "#d03b3b")
    label = risk.split(" (")[0]
    return f'<span style="background:{color}; color:white; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:700;">{label}</span>'


def build_scorecard_table(scorecard: list[dict]) -> str:
    rows_html = []
    for r in scorecard:
        is_primary = r["primary_recommendation"] == "True"
        aadt_ok = r["meets_8000_aadt_benchmark"] == "True"
        row_style = "background:#F0FDF4; font-weight:700;" if is_primary else ""
        badge = '<span style="background:#0ca30c;color:#fff;padding:2px 7px;border-radius:10px;font-size:10px;font-weight:700;">RECOMMENDED</span>' if is_primary else f"#{r['raw_score_rank']}"
        aadt_badge = '<span style="color:#0ca30c;font-weight:700;">&#10003;</span>' if aadt_ok else '<span style="color:#d03b3b;font-weight:700;">&#10007;</span>'
        rows_html.append(f"""
        <tr style="{row_style} border-bottom:1px solid #E5E7EB;">
          <td style="padding:6px 8px;">{badge}</td>
          <td style="padding:6px 8px;">{r['neighborhood']}</td>
          <td style="padding:6px 8px; max-width:220px;">{r['address']}</td>
          <td style="padding:6px 8px; text-align:right;">{r['total_score']}</td>
          <td style="padding:6px 8px; text-align:right;">{r['demand_score']}</td>
          <td style="padding:6px 8px; text-align:right;">{r['huff_score']}</td>
          <td style="padding:6px 8px; text-align:right;">{r['competition_score']}</td>
          <td style="padding:6px 8px; text-align:right;">{r['traffic_score']}</td>
          <td style="padding:6px 8px; text-align:right;">{r['cost_feasibility_score']}</td>
          <td style="padding:6px 8px; text-align:right;">{r['flood_score']}</td>
          <td style="padding:6px 8px; text-align:center;">{aadt_badge}</td>
        </tr>""")
    return f"""
    <p style="color:#374151; font-size:12.5px; margin:0 0 10px;">All 20 real citywide candidates, ranked by weighted score
    (25% demand, 20% Huff capture, 15% competitive gap, 15% traffic, 15% cost/feasibility, 10% flood risk).
    The <b>primary recommendation</b> is the highest-scoring site that also clears the 8,000 AADT minimum-traffic
    benchmark (&#10003; column) -- a higher raw score that fails the benchmark is shown but not selected. Full detail: <code>data/processed/scorecard.csv</code>.</p>
    <div style="overflow-x:auto;">
    <table style="border-collapse:collapse; width:100%; font-size:12px; color:#1F2937;">
      <thead><tr style="background:#F3F4F6; text-align:left; border-bottom:2px solid #D1D5DB;">
        <th style="padding:6px 8px;">Rank</th><th style="padding:6px 8px;">Neighborhood</th><th style="padding:6px 8px;">Site</th>
        <th style="padding:6px 8px; text-align:right;">Total</th><th style="padding:6px 8px; text-align:right;">Demand</th>
        <th style="padding:6px 8px; text-align:right;">Huff</th><th style="padding:6px 8px; text-align:right;">Comp.</th>
        <th style="padding:6px 8px; text-align:right;">Traffic</th><th style="padding:6px 8px; text-align:right;">Cost</th>
        <th style="padding:6px 8px; text-align:right;">Flood</th><th style="padding:6px 8px; text-align:center;">&ge;8k AADT</th>
      </tr></thead>
      <tbody>{"".join(rows_html)}</tbody>
    </table>
    </div>
    """


def build_cannibalization_table(cannibalization: list[dict]) -> str:
    rows_html = []
    for r in cannibalization:
        rows_html.append(f"""
        <tr style="border-bottom:1px solid #E5E7EB;">
          <td style="padding:6px 8px;">{r['site_label'].split(') - ')[0]})</td>
          <td style="padding:6px 8px; text-align:right;">{r['nearest_family_dollar_mi']} mi</td>
          <td style="padding:6px 8px;">{r['hard_buffer_flag']}</td>
          <td style="padding:6px 8px; text-align:right;">{r['overlap_pct']}%</td>
          <td style="padding:6px 8px; text-align:right;">{int(float(r['net_new_population_reach'])):,}</td>
          <td style="padding:6px 8px; text-align:center;">{_risk_badge(r['cannibalization_risk'])}</td>
        </tr>""")
    return f"""
    <p style="color:#374151; font-size:12.5px; margin:0 0 6px;">Existing Family Dollar stores are the company's own
    network, not competitors -- this measures how much of each candidate's real trade area a nearby existing store
    already serves. <b>Hard buffer:</b> &lt;1.2 mi from an existing FD auto-flags High risk. <b>Overlap %:</b> share of
    the candidate's real 5-minute OSRM drive-time population also within 1.5 mi (straight-line) of the nearest
    existing FD. <b>Net-new population reach</b> = 5-min drive population minus that overlap -- a real, computed
    proxy for incremental reach.</p>
    <p style="color:#92400E; background:#FEF3C7; font-size:11.5px; padding:6px 8px; border-radius:6px; margin:0 0 10px;">
    We deliberately do NOT report a "net new sales $" figure here. That requires a revenue model calibrated to real
    store-level sales data, which does not exist publicly -- a dollar figure without one would be a fabricated number
    dressed up as precise. See the Data Validation tab.</p>
    <div style="overflow-x:auto;">
    <table style="border-collapse:collapse; width:100%; font-size:12px; color:#1F2937;">
      <thead><tr style="background:#F3F4F6; text-align:left; border-bottom:2px solid #D1D5DB;">
        <th style="padding:6px 8px;">Site</th><th style="padding:6px 8px; text-align:right;">Nearest FD</th>
        <th style="padding:6px 8px;">Hard buffer</th><th style="padding:6px 8px; text-align:right;">Overlap %</th>
        <th style="padding:6px 8px; text-align:right;">Net-new pop. reach</th><th style="padding:6px 8px; text-align:center;">Risk</th>
      </tr></thead>
      <tbody>{"".join(rows_html)}</tbody>
    </table>
    </div>
    """


def build_microsite_table(microsite: list[dict]) -> str:
    rows_html = "".join(f"""
        <tr style="border-bottom:1px solid #E5E7EB;">
          <td style="padding:6px 8px;">{r['site_label'].split(') - ')[0]})</td>
          <td style="padding:6px 8px; text-align:right;">{r['posted_speed_limit_mph']}</td>
          <td style="padding:6px 8px;">{r['speed_assessment']}</td>
          <td style="padding:6px 8px;">{r['nearby_co_tenants']}</td>
          <td style="padding:6px 8px;">{r['approx_lot_dimensions']}</td>
        </tr>""" for r in microsite)
    return f"""
    <p style="color:#374151; font-size:12.5px; margin:0 0 6px;">Operational detail beyond the macro numbers.
    Speed limit is OSM's tagged posted limit on the frontage road where mapped; dollar-store visibility/impulse-stop
    traffic works best at 35-45 mph. Co-tenants are real nearby POIs (gas stations, laundromats, schools, post
    offices, pharmacies) within 0.3 mi that generate shared neighborhood trips. Lot dimensions are an approximate
    bounding box computed from the real HCAD parcel polygon (haversine edge lengths) -- a gut-check on whether the
    lot is plausibly large enough, not a certified survey.</p>
    <p style="color:#92400E; background:#FEF3C7; font-size:11.5px; padding:6px 8px; border-radius:6px; margin:0 0 10px;">
    <b>Not verifiable from any public data source</b> (flagged rather than guessed): deed restrictions / restrictive
    covenants (requires a title search), median-break / divided-highway ingress-egress geometry, and an engineered
    53-ft delivery-truck turning radius (both require a civil site plan). Houston has no municipal zoning -- the
    general off-street parking ratio (city code, roughly 1 space per 200-300 sq ft of retail) is cited as
    informational context in the Data Validation tab, not computed as a parcel-specific verified figure.</p>
    <div style="overflow-x:auto;">
    <table style="border-collapse:collapse; width:100%; font-size:12px; color:#1F2937;">
      <thead><tr style="background:#F3F4F6; text-align:left; border-bottom:2px solid #D1D5DB;">
        <th style="padding:6px 8px;">Site</th><th style="padding:6px 8px; text-align:right;">Speed limit</th>
        <th style="padding:6px 8px;">Assessment</th><th style="padding:6px 8px;">Nearby co-tenants</th>
        <th style="padding:6px 8px;">Approx. lot dimensions</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    </div>
    """


def build_ci_table(ci_rows: list[dict]) -> str:
    rows_html = "".join(f"""
        <tr style="border-bottom:1px solid #E5E7EB;">
          <td style="padding:7px 8px; font-weight:700;">{r['statistic']}</td>
          <td style="padding:7px 8px; text-align:right;">{r['estimate']}</td>
          <td style="padding:7px 8px; text-align:right;">{r['moe_90pct']}</td>
          <td style="padding:7px 8px; text-align:right;">{r['ci_90pct_low']} &ndash; {r['ci_90pct_high']}</td>
          <td style="padding:7px 8px; color:#6B7280; font-size:11px;">{r['source']}</td>
        </tr>""" for r in ci_rows)
    return f"""
    <p style="color:#374151; font-size:12.5px; margin:0 0 10px;">Real 90% confidence intervals for Houston
    city-wide (not a sum of tracts -- the Census Bureau's own place-level geography and margin of error) headline
    statistics, computed with the Census Bureau's published ratio-MOE propagation formula for the derived rates
    (poverty, foreign-born, Spanish-at-home): MOE<sub>p</sub> = (1/Y)&times;&radic;(MOE<sub>X</sub>&sup2; &minus; p&sup2;&times;MOE<sub>Y</sub>&sup2;).</p>
    <div style="overflow-x:auto;">
    <table style="border-collapse:collapse; width:100%; font-size:12px; color:#1F2937;">
      <thead><tr style="background:#F3F4F6; text-align:left; border-bottom:2px solid #D1D5DB;">
        <th style="padding:7px 8px;">Statistic</th><th style="padding:7px 8px; text-align:right;">Estimate</th>
        <th style="padding:7px 8px; text-align:right;">90% MOE</th><th style="padding:7px 8px; text-align:right;">90% CI range</th>
        <th style="padding:7px 8px;">Source</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    </div>
    <p style="color:#92400E; background:#FEF3C7; font-size:11.5px; padding:8px 10px; border-radius:6px; margin-top:12px;">
    <b>What does NOT have a formal confidence interval:</b> the Opportunity (Gap) Score, Huff capture %, and
    Composite Score are custom-built indices combining several inputs with judgment-based weights -- they are
    analytical tools, not Census-published population statistics, so a formal statistical confidence interval
    does not apply to them. Only the raw ACS estimates above (population, income, poverty, foreign-born, language,
    household size) carry a Census-computed margin of error.</p>
    """


def build_validation_html() -> str:
    return """
    <div style="font-size:12.5px; color:#1F2937; line-height:1.65;">
    <p><b>Every data point on this map traces to a live, free, public API</b> -- no proprietary vendor data
    (SafeGraph, Placer.ai, Esri) and no invented numbers. Full source catalog and methodology:
    <code>docs/methodology.md</code> and <code>docs/data_validation.md</code> in the repository.</p>

    <p style="font-weight:700; margin-bottom:4px;">Sources (all free, all keyless)</p>
    <ul style="margin-top:0; padding-left:18px;">
      <li>US Census Bureau -- TIGERweb (boundaries) + Census Reporter API (ACS 2024 5-yr demographics, incl. margins of error)</li>
      <li>OpenStreetMap / Overpass API -- 528 real competitor/anchor locations across 15 banners, arterial road network</li>
      <li>Harris County Appraisal District (HCAD) -- real parcel boundaries, land use, appraised value</li>
      <li>FEMA National Flood Hazard Layer (NFHL) -- flood zone identification</li>
      <li>TxDOT -- Annual Average Daily Traffic (AADT), verified by reverse-geocoding each station</li>
      <li>OSRM -- real drive-time routing + Huff gravity market-capture model</li>
      <li>Nominatim (OpenStreetMap) -- reverse geocoding for site/neighborhood/road verification</li>
    </ul>

    <p style="font-weight:700; margin-bottom:4px;">Specific checks performed against hallucination / error</p>
    <ul style="margin-top:0; padding-left:18px;">
      <li>The winning site's HCAD record, FEMA flood zone, and TxDOT AADT count were independently re-queried
      live against the source APIs (not just the cached pipeline output) and matched.</li>
      <li>TxDOT records roads by route number, not name -- every AADT match was reverse-geocoded to a real street,
      and stations that resolved to a freeway/tollway (no legal driveway access) were rejected in favor of the
      nearest genuine arterial reading.</li>
      <li>Each site's neighborhood was independently reverse-geocoded rather than inherited from its search
      cluster, after finding a case where the two disagreed.</li>
      <li>Parcels appraising under $15,000/acre were screened out -- found to be HOA common areas and drainage
      easements miscoded as vacant commercial land in HCAD, not real buildable sites.</li>
      <li>A duplicate real parcel found by two overlapping search areas is counted once, not twice.</li>
      <li>A stale isochrone bug (map briefly showed an earlier draft's winning site's drive-time shape after the
      recommendation changed) was caught by cross-checking the file's embedded site label against the live
      scorecard, and fixed.</li>
      <li>A dead/broken "nearest anchor" field (always returned a constant placeholder due to a category-name
      mismatch, silently, since it fed no downstream calculation) was found during this audit and removed.</li>
      <li>The Huff model and cannibalization analysis stop at a relative capture percentage / population-overlap
      metric -- no revenue dollar figure is produced anywhere, because no public store-level sales data exists
      to calibrate one, and a number without that grounding would be fabricated precision.</li>
      <li>Documented, non-fabricated simplifications (kept for transparency, not hidden): the Huff model's
      competitor-side travel time is straight-line/speed-estimated rather than fully OSRM-routed (network
      routing from every block group to every competitor would multiply API calls ~60x for a secondary input);
      the cannibalization overlap radius (1.5 mi straight-line) is a documented proxy for the same reason.</li>
    </ul>

    <p style="font-weight:700; margin-bottom:4px;">Houston-specific factors accounted for</p>
    <ul style="margin-top:0; padding-left:18px;">
      <li><b>No municipal zoning:</b> Houston is the only major US city without formal zoning ordinances; land use
      is governed by HCAD land-use codes, private deed restrictions, and the city's development/parking code
      instead. This means a site can be developed faster, but it also means a neighboring parcel's use isn't
      zoning-guaranteed to stay compatible -- a real-world caveat worth a site visit, not something a public
      dataset can fully screen for. Houston's general off-street parking ratio (city code, roughly 1 space per
      200-300 sq ft of retail -- about 35-45 spaces for Family Dollar's ~8,500 sq ft prototype) is cited here as
      informational context only; it is not verified per parcel and a permitting check would confirm current code.</li>
      <li><b>Flood risk:</b> Harris County's severe flood history (incl. Hurricane Harvey) is why every candidate
      was screened against FEMA's NFHL and any Special Flood Hazard Area is heavily penalized in scoring.</li>
      <li><b>Immigrant / Hispanic demographic corridors:</b> real ACS variables for foreign-born share, Spanish
      spoken at home, and average household size were pulled for all 643 Houston tracts specifically because
      corridors like Gulfton, Alief, and East Houston have large immigrant, multi-generational-household
      populations that are real demand drivers for Family Dollar's core categories (see the Confidence Intervals
      tab for the citywide figures, and tract popups on the map for local detail).</li>
    </ul>
    </div>
    """


def build_dashboard_html(scorecard: list[dict], cannibalization: list[dict], ci_rows: list[dict], microsite: list[dict]) -> str:
    return f"""
<style>
  #dash-toggle {{ position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); z-index: 10001;
                  background: #1E3A8A; color: white; border: none; padding: 10px 22px; border-radius: 10px 10px 0 0;
                  font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; font-weight: 700; cursor: pointer;
                  box-shadow: 0 -2px 10px rgba(0,0,0,.3); }}
  #dash-toggle:hover {{ background: #1E40AF; }}
  #dash-drawer {{ position: fixed; left: 0; right: 0; bottom: -68vh; height: 68vh; background: white; z-index: 10000;
                  box-shadow: 0 -6px 24px rgba(0,0,0,.35); transition: bottom .32s ease; display: flex; flex-direction: column;
                  font-family: 'Segoe UI', Arial, sans-serif; border-top: 3px solid #1E3A8A; }}
  #dash-drawer.open {{ bottom: 0; }}
  #dash-tabs {{ display: flex; gap: 4px; padding: 10px 14px 0; background: #F8FAFC; border-bottom: 1px solid #E5E7EB; flex-shrink: 0; }}
  .dash-tab-btn {{ padding: 8px 16px; border: none; background: transparent; font-size: 12.5px; font-weight: 700;
                    color: #64748B; cursor: pointer; border-radius: 6px 6px 0 0; }}
  .dash-tab-btn.active {{ background: white; color: #1E3A8A; border: 1px solid #E5E7EB; border-bottom: 1px solid white; margin-bottom: -1px; }}
  .dash-body {{ overflow-y: auto; padding: 16px 20px; flex: 1; }}
  .dash-tab-content {{ display: none; }}
  .dash-tab-content.active {{ display: block; }}
</style>
<button id="dash-toggle" onclick="fdToggleDash()">&#128202; Analysis Dashboard &#9650;</button>
<div id="dash-drawer">
  <div id="dash-tabs">
    <button class="dash-tab-btn active" id="tabbtn-scorecard" onclick="fdShowTab('scorecard')">Scorecard (20 sites)</button>
    <button class="dash-tab-btn" id="tabbtn-cannibalization" onclick="fdShowTab('cannibalization')">Cannibalization</button>
    <button class="dash-tab-btn" id="tabbtn-microsite" onclick="fdShowTab('microsite')">Site Details</button>
    <button class="dash-tab-btn" id="tabbtn-ci" onclick="fdShowTab('ci')">Confidence Intervals</button>
    <button class="dash-tab-btn" id="tabbtn-validation" onclick="fdShowTab('validation')">Data Sources &amp; Validation</button>
  </div>
  <div class="dash-body">
    <div class="dash-tab-content active" id="tab-scorecard">{build_scorecard_table(scorecard)}</div>
    <div class="dash-tab-content" id="tab-cannibalization">{build_cannibalization_table(cannibalization)}</div>
    <div class="dash-tab-content" id="tab-microsite">{build_microsite_table(microsite)}</div>
    <div class="dash-tab-content" id="tab-ci">{build_ci_table(ci_rows)}</div>
    <div class="dash-tab-content" id="tab-validation">{build_validation_html()}</div>
  </div>
</div>
<script>
  function fdToggleDash() {{
    var d = document.getElementById('dash-drawer');
    var btn = document.getElementById('dash-toggle');
    var open = d.classList.toggle('open');
    btn.innerHTML = open ? '&#128202; Analysis Dashboard &#9660;' : '&#128202; Analysis Dashboard &#9650;';
  }}
  function fdShowTab(name) {{
    document.querySelectorAll('.dash-tab-content').forEach(function(el) {{ el.classList.remove('active'); }});
    document.querySelectorAll('.dash-tab-btn').forEach(function(el) {{ el.classList.remove('active'); }});
    document.getElementById('tab-' + name).classList.add('active');
    document.getElementById('tabbtn-' + name).classList.add('active');
  }}
</script>
"""


def build_map() -> Path:
    output_path = ROOT / "index.html"

    scorecard = load_csv("scorecard.csv")
    sites = {r["hcad_num"]: r for r in load_csv("sites_enriched.csv")}
    trade = {r["hcad_num"]: r for r in load_csv("site_trade_areas.csv")}
    cannibalization = {r["hcad_num"]: r for r in load_csv("cannibalization.csv")}
    microsite = {r["hcad_num"]: r for r in load_csv("microsite_details.csv")}
    ci_rows = load_csv("city_confidence_intervals.csv")
    extended_demo = {r["geoid"]: r for r in load_csv("tract_extended_demographics.csv")}
    competitors = load_csv("competitors.csv")
    tracts = load_json("houston_tracts.geojson")
    boundary = load_json("houston_boundary.geojson")
    isochrone = load_json("isochrone_winner.json")

    m = folium.Map(location=[29.79, -95.45], zoom_start=11, tiles=None, control_scale=True)

    # --- Basemap switcher: several free/open tile providers ---------------------
    # Only the first should be active on load; Leaflet renders whichever base
    # TileLayer was added last if more than one defaults to show=True.
    folium.TileLayer(tiles="CartoDB positron", name="Light (CartoDB Positron)", control=True, show=True).add_to(m)
    folium.TileLayer(tiles="CartoDB dark_matter", name="Dark (CartoDB Dark Matter)", control=True, show=False).add_to(m)
    folium.TileLayer(tiles="OpenStreetMap", name="Streets (OpenStreetMap)", control=True, show=False).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri, Maxar, Earthstar Geographics",
        name="Satellite (Esri World Imagery)",
        control=True,
        show=False,
    ).add_to(m)
    folium.TileLayer(
        tiles="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
        attr="Map data: OpenStreetMap contributors, SRTM | Map style: OpenTopoMap (CC-BY-SA)",
        name="Terrain (OpenTopoMap)",
        control=True,
        show=False,
    ).add_to(m)

    m.get_root().header.add_child(folium.Element(POPUP_CSS))
    m.get_root().html.add_child(folium.Element(TITLE_HTML))

    # --- Layer: Houston city limits (real boundary, for scale/context) ----------
    boundary_layer = folium.FeatureGroup(name="Houston city limits", show=True)
    folium.GeoJson(
        boundary,
        style_function=lambda _f: {"fillOpacity": 0, "color": "#1E3A8A", "weight": 2.5, "dashArray": "6,4"},
        tooltip="City of Houston boundary (TIGERweb)",
    ).add_to(boundary_layer)
    boundary_layer.add_to(m)

    # --- Layer: citywide opportunity (gap score) choropleth ---------------------
    gap_layer = folium.FeatureGroup(name="Opportunity score, all Houston tracts (643)", show=True)
    scores = [float(f["properties"]["gap_score"]) for f in tracts["features"] if f["properties"].get("gap_score")]
    lo, hi = min(scores), max(scores)

    for f in tracts["features"]:
        p = f["properties"]
        if not p.get("gap_score"):
            continue
        score = float(p["gap_score"])
        t = (score - lo) / (hi - lo) if hi > lo else 0
        color = ramp_color(t, SEQUENTIAL_ORANGE)
        fill_opacity = 0.12 + 0.5 * t
        pop = float(p["population"]) if p.get("population") else 0
        mhi = float(p["median_hh_income"]) if p.get("median_hh_income") else None
        pov = float(p["poverty_rate"]) * 100 if p.get("poverty_rate") else None
        ext = extended_demo.get(p["geoid"], {})
        fb = float(ext["foreign_born_rate"]) * 100 if ext.get("foreign_born_rate") not in (None, "") else None
        span = float(ext["spanish_at_home_rate"]) * 100 if ext.get("spanish_at_home_rate") not in (None, "") else None
        hh = float(ext["avg_household_size"]) if ext.get("avg_household_size") not in (None, "") else None
        popup = (
            f"<div class='exec-card'><div class='exec-title'>{p['name']}</div>"
            f"<div class='exec-metric'><span>Population</span><span class='exec-val'>{pop:,.0f}</span></div>"
            f"<div class='exec-metric'><span>Median HH Income</span><span class='exec-val'>{'$'+format(mhi, ',.0f') if mhi else 'n/a'}</span></div>"
            f"<div class='exec-metric'><span>Poverty Rate</span><span class='exec-val'>{pov:.1f}%</span></div>"
            f"<div class='exec-metric'><span>Foreign-Born Share</span><span class='exec-val'>{f'{fb:.1f}%' if fb is not None else 'n/a'}</span></div>"
            f"<div class='exec-metric'><span>Spanish Spoken at Home</span><span class='exec-val'>{f'{span:.1f}%' if span is not None else 'n/a'}</span></div>"
            f"<div class='exec-metric'><span>Avg. Household Size</span><span class='exec-val'>{f'{hh:.2f}' if hh is not None else 'n/a'}</span></div>"
            f"<div class='exec-metric'><span>Nearest Dollar-Format Store</span><span class='exec-val'>{p['nearest_dollar_store_mi']} mi</span></div>"
            f"<div class='exec-metric'><span>Opportunity (Gap) Score</span><span class='exec-val'>{score:.0f}</span></div>"
            f"<div class='src-note'>Source: US Census ACS 2024 5-yr (Census Reporter API) &middot; OSM competitor pull</div></div>"
        )
        folium.GeoJson(
            f,
            style_function=lambda _f, c=color, o=fill_opacity: {"fillColor": c, "color": "#c2996b", "weight": 0.3, "fillOpacity": o},
            highlight_function=lambda _f: {"weight": 2, "color": "#7a2d0f"},
            tooltip=f"{p['name']}: opportunity score {score:.0f}",
            popup=folium.Popup(popup, max_width=300),
        ).add_to(gap_layer)
    gap_layer.add_to(m)

    # --- Layer: competitors, 5 categories -----------------------------------------
    # Family Dollar gets its own always-on layer: existing FD locations are the
    # company's own network (cannibalization question), not a competitive threat,
    # and that distinction is the single most important competitor fact here.
    category_layers = {
        "family_dollar": folium.FeatureGroup(name="Family Dollar (existing)", show=True),
        "arch_rival": folium.FeatureGroup(name="Direct arch-rivals (Dollar General, Five Below)", show=True),
        "sister_banner": folium.FeatureGroup(name="Sister banner (Dollar Tree)", show=False),
        "value_grocery": folium.FeatureGroup(name="Value grocery (Aldi, Joe V's, Fiesta, etc.)", show=False),
        "big_box_anchor": folium.FeatureGroup(name="Big-box anchors (Walmart, Target, etc.)", show=False),
    }

    for c in competitors:
        lat, lon = float(c["lat"]), float(c["lon"])
        if not (MAP_BOUNDS["lat_min"] <= lat <= MAP_BOUNDS["lat_max"] and MAP_BOUNDS["lon_min"] <= lon <= MAP_BOUNDS["lon_max"]):
            continue
        layer = category_layers.get(c["category"])
        color = COMPETITOR_COLORS.get(c["category"], "#57534e")
        if layer is None:
            continue
        # smaller + more transparent than the candidate-site markers, with a thin white
        # ring instead of a saturated border, so these read as context, not the focus
        folium.CircleMarker(
            location=[lat, lon], radius=4.5, color="#ffffff", fill=True, fill_color=color,
            fill_opacity=0.68, weight=0.75, opacity=0.9,
            tooltip=f"{c['name']} ({c['brand']})",
            popup=f"<b style='color:#1F2937;'>{c['name']}</b><br><span style='color:#374151;'>Brand: {c['brand']}<br>Category: {COMPETITOR_LABELS[c['category']]}<br>Typical size: {int(c['typical_sqft']):,} sq ft</span><br><span class='src-note'>Source: OpenStreetMap</span>",
        ).add_to(layer)
    for layer in category_layers.values():
        layer.add_to(m)

    # --- Layer: 10 opportunity clusters searched (context) -----------------------
    clusters = load_csv("clusters.csv")
    cluster_layer = folium.FeatureGroup(name="Opportunity areas searched (10 neighborhoods)", show=False)
    for c in clusters:
        folium.Circle(
            location=[float(c["lat"]), float(c["lon"])],
            radius=1800,
            color="#94A3B8",
            weight=1.5,
            dash_array="3,4",
            fill=False,
            tooltip=f"{c['neighborhood']} opportunity cluster (gap score {round(float(c['score'])):,})",
        ).add_to(cluster_layer)
    cluster_layer.add_to(m)

    # --- Layer: 20 candidate sites, rank color ramp -------------------------------
    site_layer = folium.FeatureGroup(name="Candidate sites (20, all Houston)", show=True)
    n = len(scorecard)
    winner_latlon = None
    for i, row in enumerate(scorecard, start=1):
        h = row["hcad_num"]
        s = sites[h]
        t = trade[h]
        canib = cannibalization[h]
        micro = microsite[h]
        is_winner = row["primary_recommendation"] == "True"
        if is_winner:
            winner_latlon = [float(s["lat"]), float(s["lon"])]
        rank_color = ramp_color((int(row["raw_score_rank"]) - 1) / max(n - 1, 1), STATUS_RAMP)
        rank_html = "<span class='winner-tag'>PRIMARY RECOMMENDATION</span>" if is_winner else f"<span class='rank-tag' style='background:{rank_color};'>SCORE RANK {row['raw_score_rank']} / {n}</span>"
        freeway_note = (
            "<div class='warn-note'>Nearest labeled TxDOT station sits on a limited-access freeway with no arterial "
            "count nearby; traffic score uses a conservative fallback, not this freeway figure.</div>"
            if s["aadt_on_freeway"] == "True" else ""
        )
        flood_note = "<div class='warn-note'>Falls inside a FEMA Special Flood Hazard Area.</div>" if s["in_sfha"] == "T" else ""
        aadt_note = "" if row["meets_8000_aadt_benchmark"] == "True" else "<div class='warn-note'>Below the 8,000 AADT minimum-traffic benchmark -- not eligible as the primary recommendation regardless of score.</div>"
        canib_note = ""
        if canib["cannibalization_risk"].startswith("Low"):
            canib_note = f"<div class='good-note'>Low cannibalization risk vs. existing Family Dollar ({canib['nearest_family_dollar_mi']} mi, {canib['overlap_pct']}% trade-area overlap).</div>"
        elif canib["cannibalization_risk"].startswith("High"):
            canib_note = f"<div class='warn-note'>High cannibalization risk vs. existing Family Dollar ({canib['nearest_family_dollar_mi']} mi, {canib['overlap_pct']}% trade-area overlap).</div>"
        popup = f"""
        <div class="exec-card">
          {rank_html}
          <div class="exec-title" style="margin-top:6px;">{s['neighborhood']}: {s['address']}</div>
          <div class="exec-metric"><span>Parcel (HCAD)</span><span class="exec-val">{s['acreage']} ac, {s['site_type']}</span></div>
          <div class="exec-metric"><span>Land Value (HCAD)</span><span class="exec-val">${float(s['land_value']):,.0f}</span></div>
          <div class="exec-metric"><span>Traffic (verified road)</span><span class="exec-val">{int(float(s['aadt'])):,} vpd on {s['aadt_road_verified']}</span></div>
          <div class="exec-metric"><span>5-Min Drive Population</span><span class="exec-val">{int(float(t['pop_5min_drive'])):,}</span></div>
          <div class="exec-metric"><span>10-Min Drive Population</span><span class="exec-val">{int(float(t['pop_10min_drive'])):,}</span></div>
          <div class="exec-metric"><span>Trade-Area Median Income</span><span class="exec-val">{'$'+format(float(t['trade_area_median_income']), ',.0f') if t['trade_area_median_income'] else 'n/a'}</span></div>
          <div class="exec-metric"><span>Huff Capture (vs. arch-rivals)</span><span class="exec-val">{t['huff_capture_pct']}%</span></div>
          <div class="exec-metric"><span>Nearest Arch-Rival</span><span class="exec-val">{s['nearest_dollar_store_mi']} mi</span></div>
          <div class="exec-metric"><span>Nearest Family Dollar</span><span class="exec-val">{s['nearest_family_dollar_mi']} mi</span></div>
          <div class="exec-metric"><span>FEMA Flood Zone</span><span class="exec-val">{s['flood_zone']}</span></div>
          <div class="exec-metric"><span>Posted Speed Limit</span><span class="exec-val">{micro['posted_speed_limit_mph']} mph</span></div>
          <div class="exec-metric"><span>Nearby Co-Tenants</span><span class="exec-val" style="text-align:right; font-weight:600;">{micro['nearby_co_tenants']}</span></div>
          <div class="exec-metric"><span>Composite Score</span><span class="exec-val">{row['total_score']} / 100</span></div>
          {aadt_note}{freeway_note}{flood_note}{canib_note}
          <div class="src-note">Sources: HCAD parcels &middot; TxDOT AADT (Nominatim-verified) &middot; FEMA NFHL &middot; OSM &middot; OSRM drive times &middot; Huff gravity model. Full detail in the Analysis Dashboard.</div>
        </div>
        """
        icon = rank_badge_icon(int(row["raw_score_rank"]), rank_color, is_winner)
        folium.Marker(
            location=[float(s["lat"]), float(s["lon"])],
            popup=folium.Popup(popup, max_width=340),
            tooltip=("RECOMMENDED: " if is_winner else f"Score rank #{row['raw_score_rank']}: ") + f"{s['neighborhood']} - {s['address']}",
            icon=icon,
        ).add_to(site_layer)
    site_layer.add_to(m)

    # --- Layer: isochrones for the winning site --------------------------------
    iso_layer = folium.FeatureGroup(name="Drive-time trade area (recommended site, OSRM)", show=True)
    folium.GeoJson(
        isochrone["isochrones"]["10min"],
        style_function=lambda _f: {"fillColor": "#0D9488", "color": "#0D9488", "weight": 1.5, "dashArray": "4,4", "fillOpacity": 0.10},
        tooltip="10-minute drive trade area (OSRM network routing)",
    ).add_to(iso_layer)
    folium.GeoJson(
        isochrone["isochrones"]["5min"],
        style_function=lambda _f: {"fillColor": "#0D9488", "color": "#0D9488", "weight": 2, "fillOpacity": 0.30},
        tooltip="5-minute drive trade area (OSRM network routing)",
    ).add_to(iso_layer)
    iso_layer.add_to(m)

    rank_ramp_css = "linear-gradient(90deg," + ",".join(STATUS_RAMP) + ")"
    m.get_root().html.add_child(folium.Element(build_legend_html(rank_ramp_css)))
    m.get_root().html.add_child(folium.Element(build_dashboard_html(scorecard, load_csv("cannibalization.csv"), ci_rows, load_csv("microsite_details.csv"))))

    folium.LayerControl(collapsed=False).add_to(m)
    plugins.Fullscreen(position="topright").add_to(m)
    m.fit_bounds([[29.60, -95.65], [29.98, -95.20]])

    m.save(output_path)
    return output_path


if __name__ == "__main__":
    path = build_map()
    print(f"Web map written to {path}")
