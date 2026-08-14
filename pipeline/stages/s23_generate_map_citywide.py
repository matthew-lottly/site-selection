"""Step 23 (supersedes scripts/12_generate_map.py): build the executive-facing
interactive web map from the citywide pipeline outputs. Every layer and every
dashboard number traces back to a data/processed/*.csv or *.geojson file
produced by scripts 01-25.

Symbology:
  - candidate sites: numbered rank badges on a validated best->worst ramp
  - competitors: 4 categories (Family Dollar / arch-rival, now including
    Dollar Tree since its 2025-07-08 separation from Family Dollar / value
    grocery / big-box), all cool hues, validated distinct from each other and
    from the warm rank-ramp/choropleth colors sharing the map
  - choropleth: blue sequential ramp, opacity scaled to score
  - a right-side sliding dashboard panel: Scorecard / Cannibalization / Confidence
    Intervals / Data Sources & Validation tabs
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
import math

import folium
from folium import plugins

from ..color import ColorRamp
from ..core import PROCESSED, ROOT, PipelineStage


class GenerateMapStage(PipelineStage):
    id = "23"
    name = "generate_map_citywide"
    description = (
        "Executive-facing citywide interactive web map (index.html) -- candidate site "
        "rankings, competitor layers, opportunity choropleth, and the Analysis Dashboard"
    )
    outputs = (ROOT / "index.html",)

    MAP_BOUNDS = {"lat_min": 29.52, "lat_max": 30.11, "lon_min": -95.79, "lon_max": -95.01}

    # Single source of truth for each competitor tier's map-layer name: used both as the
    # folium.FeatureGroup `name=` (what Leaflet's layer control shows and what its
    # overlayadd/overlayremove events report back) and as the legend row label, so the
    # two can never drift out of sync with each other.
    COMPETITOR_LABELS = {
        "family_dollar": "Family Dollar (existing -- not a competitor)",
        "arch_rival": "Direct arch-rival (Dollar General, Five Below, Dollar Tree)",
        "value_grocery": "Value grocery (Aldi, Joe V's, Mi Tienda, Fiesta, etc.)",
        "big_box_anchor": "Big-box anchor (Walmart, Target, etc.)",
    }
    COMPETITOR_LAYER_SHOW = {
        "family_dollar": True,
        "arch_rival": True,
        "value_grocery": False,
        "big_box_anchor": False,
    }


    @staticmethod
    def load_csv(name: str) -> list[dict]:
        with open(PROCESSED / name, encoding="utf-8") as fh:
            return list(csv.DictReader(fh))


    @staticmethod
    def load_json(name: str) -> dict:
        return json.loads((PROCESSED / name).read_text(encoding="utf-8"))


    PAGE_CHROME_CSS = """
<style>
  .exec-card { font-family: 'Segoe UI', Arial, sans-serif; width: 300px; padding: 6px 8px; }
  .exec-title { font-size: 14px; font-weight: 700; color: #0F172A; border-bottom: 2px solid #93C5FD; padding-bottom: 4px; margin-bottom: 6px; }
  .exec-metric { font-size: 12px; margin: 4px 0; color: #1F2937; font-weight: 700; display: flex; justify-content: space-between; gap: 8px; }
  .exec-metric span:first-child { color: #374151; font-weight: 600; }
  .exec-val { font-weight: 700; color: #1F2937; text-align: right; }
  .winner-tag { background-color: #0ca30c; color: white; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: 700; letter-spacing: .03em; }
  .rank-tag { color: white; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: 700; }
  .src-note { font-size: 10px; color: #64748B; margin-top: 6px; border-top: 1px solid #E2E8F0; padding-top: 4px; font-weight: 400; }
  .warn-note { font-size: 11px; color: #92400E; background: #FEF3C7; padding: 4px 6px; border-radius: 4px; margin-top: 4px; font-weight: 600; }
  .good-note { font-size: 11px; color: #14532D; background: #DCFCE7; padding: 4px 6px; border-radius: 4px; margin-top: 4px; font-weight: 600; }

  /* App-shell layout: a real top header bar, the map fills the rest, a right
     panel slides over it. Chrome IDs below are targeted by print CSS too. */
  html, body { overflow: hidden; }
  /* The map renders full-bleed under the fixed header (that's fine -- the header
     just overlays it). The generated Leaflet map div's id is a random per-build
     hash though, so instead of trying to resize the map container itself (which
     silently no-ops if the id guess is wrong), push Leaflet's own control-anchor
     classes down below the header -- this is what actually determines where the
     zoom/layer-control panel renders, regardless of the map div's real id. */
  .leaflet-top { top: 70px !important; }
  #app-header { position: fixed; top: 0; left: 0; right: 0; height: 60px; z-index: 9999;
                background: linear-gradient(180deg, #F8FAFC 0%, #EEF2FF 100%);
                border-bottom: 1px solid #CBD5E1; box-shadow: 0 2px 14px rgba(15,23,42,.12); font-family: 'Segoe UI', Arial, sans-serif;
                display: flex; align-items: center; justify-content: space-between; padding: 0 18px; box-sizing: border-box; }
  #app-header .title-block { display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; min-width: 0; }
  #app-header .title-main { font-size: 16px; font-weight: 800; color: #0F172A; white-space: nowrap; letter-spacing: .01em; }
  #app-header .title-sub { font-size: 12px; color: #475569; white-space: nowrap; }
  #app-header .title-rec { font-size: 12px; color: #1D4ED8; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
                           background: #DBEAFE; border: 1px solid #BFDBFE; padding: 4px 10px; border-radius: 999px; }
  #dash-toggle { flex-shrink: 0; background: linear-gradient(135deg, #1D4ED8 0%, #0F766E 100%); color: #F8FAFC; border: none;
                 padding: 10px 18px; border-radius: 10px; font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px;
                 font-weight: 800; cursor: pointer; white-space: nowrap; box-shadow: 0 4px 10px rgba(29,78,216,.24); }
  #dash-toggle:hover { filter: brightness(1.06); }
  #dash-toggle:active { transform: translateY(1px); }

  /* Prevent the browser's default focus-outline rectangle from appearing
     around clicked map shapes (looked like a stray "boundary box" artifact) */
  .leaflet-interactive:focus, path:focus, svg:focus { outline: none !important; }

  #dash-drawer { position: fixed; top: 60px; right: -600px; bottom: 0; width: 580px; max-width: 96vw;
                 background: #F8FAFC; z-index: 10000; box-shadow: -10px 0 28px rgba(15,23,42,.28);
                 transition: right .30s ease; display: flex; flex-direction: column;
                 border-left: 2px solid #1E3A8A; font-family: 'Segoe UI', Arial, sans-serif; }
  #dash-drawer.open { right: 0; }
  #dash-titlebar { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px;
                   padding: 14px 14px 10px; background: linear-gradient(180deg, #EEF2FF 0%, #F8FAFC 80%);
                   border-bottom: 1px solid #E5E7EB; flex-shrink: 0; }
  #dash-title-main { color: #1E3A8A; font-size: 15px; font-weight: 800; letter-spacing: .01em; }
  #dash-title-sub { color: #475569; font-size: 11.5px; margin-top: 3px; }
  #dash-tabs-row { padding: 10px 12px 10px; border-bottom: 1px solid #E2E8F0; background: #FFFFFF; flex-shrink: 0; }
  #dash-tabs { display: flex; gap: 6px; overflow-x: auto; padding-bottom: 2px; }
  #dash-tabs::-webkit-scrollbar { height: 6px; }
  #dash-tabs::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 99px; }
  .dash-tab-btn { padding: 7px 11px; border: 1px solid #D1D5DB; background: #FFFFFF; font-size: 11.5px; font-weight: 700;
                  color: #475569; cursor: pointer; border-radius: 999px; white-space: nowrap; }
  .dash-tab-btn:hover { background: #F8FAFC; border-color: #94A3B8; }
  .dash-tab-btn.active { background: #1E3A8A; color: #FFFFFF; border-color: #1E3A8A; }
  #dash-close { background: #DBEAFE; border: 1px solid #93C5FD; font-size: 16px; color: #1D4ED8; cursor: pointer;
                width: 30px; height: 30px; border-radius: 8px; flex-shrink: 0; box-shadow: 0 2px 6px rgba(29,78,216,.10); }
  #dash-close:hover { background: #BFDBFE; }
  .dash-body { overflow-y: auto; padding: 14px 14px 24px; flex: 1; }
  .dash-body p { line-height: 1.45; }
  .dash-body table { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; overflow: hidden; }
  .dash-body thead tr { background: #F1F5F9 !important; }
  .dash-body th { color: #334155; font-size: 11.5px; letter-spacing: .01em; }
  .dash-body td { background: #FFFFFF; }
  .dash-tab-content { display: none; }
  .dash-tab-content.active { display: block; }

  @media (max-width: 900px) {
    #dash-drawer { width: 100vw; max-width: 100vw; right: -100vw; }
    #dash-title-main { font-size: 14px; }
    #dash-title-sub { font-size: 11px; }
    .dash-body { padding: 12px; }
  }

  @media print {
    @page { size: landscape; margin: 10mm; }
    html, body { overflow: visible !important; height: auto !important; }
    .folium-map { position: relative !important; height: 700px !important; }
    .leaflet-top { top: 10px !important; }
    #app-header { position: relative !important; }
    #dash-toggle, .leaflet-control-zoom, .leaflet-control-fullscreen { display: none !important; }
    #dash-drawer:not(.open) { display: none !important; }
    #dash-drawer.open { position: relative !important; top: 0 !important; right: auto !important;
                         width: 100% !important; max-width: 100% !important; height: auto !important;
                         box-shadow: none !important; border-left: none !important; border-top: 3px solid #1E3A8A !important;
                         margin-top: 16px; page-break-before: always; }
    .dash-body { max-height: none !important; overflow: visible !important; }
  }
</style>
"""

    @staticmethod
    def build_header_html(winner_address: str, winner_neighborhood: str) -> str:
        # Built from the live scorecard winner every run -- a hardcoded site name
        # here is exactly the kind of stale-cache bug this project caught and
        # fixed once already (see docs/data_validation.md); never repeat it.
        return f"""
<div id="app-header">
  <div class="title-block">
    <span class="title-main">Family Dollar - Houston Site Selection</span>
    <span class="title-sub">Citywide screen &middot; 10 neighborhoods &middot; 20 real candidate sites</span>
    <span class="title-rec">Recommended: {winner_address}, {winner_neighborhood}</span>
  </div>
  <button id="dash-toggle" onclick="fdToggleDash()">&#128202; Analysis Dashboard</button>
</div>
"""


    def build_legend_html(self, opportunity_ramp_css: str) -> str:
        """A dynamic legend: every section/row that corresponds to a real, toggleable
        folium.FeatureGroup is wrapped in a `data-legend-layer="<exact FeatureGroup
        name>"` container, with its initial display matching that layer's actual
        default `show=` value. `build_dynamic_legend_script` (JS, injected separately)
        listens for Leaflet's overlayadd/overlayremove events and shows/hides the
        matching container live, so the legend always reflects exactly what's
        currently visible on the map -- nothing shown that isn't on, nothing hidden
        that is. The section header/divider chrome stays static; only the data rows
        underneath toggle, so turning every row in a section off leaves a clean
        (if momentarily empty) header rather than the whole legend jumping around.
        """
        section_head = "font-weight:700; color:#1F2937; font-size:11px; text-transform:uppercase; letter-spacing:.04em; margin-bottom:7px;"
        row_text = "color:#374151; font-weight:600;"

        def layer_row(layer_name: str, show_default: bool, inner_html: str) -> str:
            display = "block" if show_default else "none"
            safe_name = layer_name.replace('"', "&quot;")
            return f'<div data-legend-layer="{safe_name}" style="display:{display};">{inner_html}</div>'

        def dot(color: str, label: str) -> str:
            return (
                f'<div style="display:flex; align-items:center; gap:8px; margin-bottom:5px;">'
                f'<span style="width:11px; height:11px; border-radius:50%; background:{color}; border:1.5px solid #fff; '
                f'box-shadow:0 0 0 .5px {color}; display:inline-block; flex-shrink:0;"></span>'
                f'<span style="{row_text}">{label}</span></div>'
            )

        family_dollar_row = layer_row(
            self.COMPETITOR_LABELS["family_dollar"],
            self.COMPETITOR_LAYER_SHOW["family_dollar"],
            dot("#2a78d6", "Family Dollar (existing network)"),
        )
        competitor_rows = "".join(
            layer_row(v, self.COMPETITOR_LAYER_SHOW[k], dot(ColorRamp.COMPETITOR_COLORS[k], v.split(" (")[0]))
            for k, v in self.COMPETITOR_LABELS.items()
            if k != "family_dollar"
        )

        def ramp_dot(color: str) -> str:
            return (
                f'<span style="width:14px; height:14px; border-radius:50%; background:{color}; '
                f'border:2px solid #fff; box-shadow:0 1px 3px rgba(0,0,0,.35); flex-shrink:0;"></span>'
            )

        # Same color function the real rank-badge markers use (ramp_color over ColorRamp.STATUS_RAMP) -- a row of
        # points, not a solid bar, since candidate sites are points on the map, not a filled area.
        RANK_RAMP_DOTS = 7
        rank_dots = "".join(
            ramp_dot(ColorRamp.interpolate(i / (RANK_RAMP_DOTS - 1), ColorRamp.STATUS_RAMP)) for i in range(RANK_RAMP_DOTS)
        )

        candidate_sites_content = layer_row(
            "Candidate sites (20, all Houston)",
            True,
            f"""
  <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
    <div style="width:22px; height:22px; border-radius:50%; background:#0ca30c; border:2px solid #fff; box-shadow:0 0 0 2px #F5B700, 0 1px 3px rgba(0,0,0,.35); flex-shrink:0; display:flex; align-items:center; justify-content:center; color:#fff; font-size:12px;">&#9733;</div>
    <span style="{row_text}">Recommended site</span>
  </div>
  <div style="margin-bottom:6px;">
    <span style="{row_text}">Other candidate sites, numbered by rank</span>
  </div>
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:3px;">
    {rank_dots}
  </div>
  <div style="display:flex; justify-content:space-between; color:#6B7280; font-size:10.5px; margin-bottom:12px; font-weight:600;">
    <span>Best</span><span>Worst</span>
  </div>""",
        )

        trade_area_content = layer_row(
            "Drive-time trade area (recommended site, OSRM)",
            True,
            f"""
  <div style="display:flex; align-items:center; gap:8px; margin-bottom:5px;"><span style="width:16px; height:11px; background:#0D9488; opacity:.4; border:1px solid #0D9488; display:inline-block; flex-shrink:0;"></span><span style="{row_text}">5-min drive (OSRM)</span></div>
  <div style="display:flex; align-items:center; gap:8px; margin-bottom:12px;"><span style="width:16px; height:11px; background:#0D9488; opacity:.14; border:1px dashed #0D9488; display:inline-block; flex-shrink:0;"></span><span style="{row_text}">10-min drive (OSRM)</span></div>""",
        )

        opportunity_content = layer_row(
            "Opportunity score, all Houston tracts (643)",
            True,
            f"""
  <div style="height:9px; border-radius:5px; margin-bottom:3px; background:{opportunity_ramp_css};"></div>
  <div style="display:flex; justify-content:space-between; color:#6B7280; font-size:10.5px; font-weight:600;">
    <span>Lower (served)</span><span>Higher (underserved)</span>
  </div>""",
        )

        flood_content = layer_row(
            "FEMA flood zones (NFHL, live API, off by default)",
            False,
            f"""
  <div style="display:flex; align-items:center; gap:8px; margin-bottom:5px;"><span style="width:16px; height:11px; background:#93C5FD; opacity:.6; border:1px solid #2563EB; display:inline-block; flex-shrink:0;"></span><span style="{row_text}">FEMA NFHL polygons</span></div>
  <div style="color:#6B7280; font-size:10.5px; margin-bottom:2px;">Zoom in on a site once toggled on (loads live from FEMA per-area to stay fast). SFHA zones are darker blue.</div>""",
        )

        boundary_content = layer_row(
            "Houston city limits", False,
            dot("#1E3A8A", "City boundary (TIGERweb, dashed outline)"),
        )
        clusters_content = layer_row(
            "Opportunity areas searched (10 neighborhoods)", False,
            dot("#94A3B8", "Opportunity cluster search radius"),
        )
        lihtc_content = layer_row(
            "HUD LIHTC affordable-housing properties (free, off by default)", False,
            dot("#0f766e", "Real HUD LIHTC property (unit count in popup)"),
        )
        food_access_ramp_css = "linear-gradient(90deg," + ",".join(ColorRamp.SEQUENTIAL_ORANGE) + ")"
        daytime_content = layer_row(
            "Daytime workplace population, all Houston block groups (free, off by default)", False,
            f"""
  <div style="height:9px; border-radius:5px; margin-bottom:3px; background:{food_access_ramp_css};"></div>
  <div style="display:flex; justify-content:space-between; color:#6B7280; font-size:10.5px; font-weight:600;">
    <span>Fewer real jobs</span><span>More real jobs</span>
  </div>""",
        )
        food_access_content = layer_row(
            "Food access share, finalist tracts (USDA, free, off by default)", False,
            f"""
  <div style="height:9px; border-radius:5px; margin-bottom:3px; background:{food_access_ramp_css};"></div>
  <div style="display:flex; justify-content:space-between; color:#6B7280; font-size:10.5px; font-weight:600;">
    <span>Lower share</span><span>Higher share beyond 0.5mi</span>
  </div>""",
        )
        overture_content = layer_row(
            "Competitors found by Overture, missed by OSM (free, off by default)", False,
            dot("#b45309", "Real competitor OSM's data missed"),
        )
        multifamily_content = layer_row(
            "HUD Multifamily assisted-housing properties (free, off by default)", False,
            dot("#7c3aed", "Real HUD Multifamily property (assisted units in popup)"),
        )
        opp_zone_content = layer_row(
            "Federal Opportunity Zones, finalist tracts (free, off by default)", False,
            dot("#fbbf24", "Finalist site in a real federal Qualified Opportunity Zone"),
        )

        return f"""
<div style="position: fixed; bottom: 20px; left: 12px; z-index: 9999; background: white;
            padding: 14px 16px; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,.28);
            font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; max-width: 272px; max-height: 80vh; overflow-y: auto;">
  <div style="font-weight:700; font-size:13px; color:#1E3A8A; margin-bottom:12px;">Legend</div>
  <div style="color:#6B7280; font-size:10px; margin-bottom:10px;">Updates live as you toggle layers in the layer control (top-right of the map).</div>

  <div style="{section_head}">Candidate sites (by score)</div>
  {candidate_sites_content}

  <div style="border-top:1px solid #E5E7EB; margin:10px 0;"></div>
  <div style="{section_head}">Competitors</div>
  {family_dollar_row}
  {competitor_rows}

  <div style="border-top:1px solid #E5E7EB; margin:10px 0;"></div>
  <div style="{section_head}">Trade area (recommended site)</div>
  {trade_area_content}

  <div style="border-top:1px solid #E5E7EB; margin:10px 0;"></div>
  <div style="{section_head}">Opportunity score</div>
  {opportunity_content}

  <div style="border-top:1px solid #E5E7EB; margin:10px 0;"></div>
  <div style="{section_head}">Flood zones</div>
  {flood_content}

  <div style="border-top:1px solid #E5E7EB; margin:10px 0;"></div>
  <div style="{section_head}">Affordable housing (HUD LIHTC)</div>
  {lihtc_content}

  <div style="border-top:1px solid #E5E7EB; margin:10px 0;"></div>
  <div style="{section_head}">Assisted housing (HUD Multifamily)</div>
  {multifamily_content}

  <div style="border-top:1px solid #E5E7EB; margin:10px 0;"></div>
  <div style="{section_head}">Daytime population (Census LEHD)</div>
  {daytime_content}

  <div style="border-top:1px solid #E5E7EB; margin:10px 0;"></div>
  <div style="{section_head}">Food access (USDA)</div>
  {food_access_content}

  <div style="border-top:1px solid #E5E7EB; margin:10px 0;"></div>
  <div style="{section_head}">Federal Opportunity Zones</div>
  {opp_zone_content}

  <div style="border-top:1px solid #E5E7EB; margin:10px 0;"></div>
  <div style="{section_head}">Overture competitor cross-check</div>
  {overture_content}

  <div style="border-top:1px solid #E5E7EB; margin:10px 0;"></div>
  <div style="{section_head}">Boundaries & search areas</div>
  {boundary_content}
  {clusters_content}

  <div style="border-top:1px solid #E5E7EB; margin:10px 0;"></div>
  <div style="color:#6B7280; font-size:10.5px;">Full scorecard, cannibalization math, confidence
  intervals, and data-source audit trail: open the <b>Analysis Dashboard</b> panel (top-right button).</div>
</div>
"""


    WINNER_FILL = "#0ca30c"  # fixed -- must never depend on rank-ramp position (see rank_badge_icon)
    WINNER_RING = "#F5B700"  # gold ring called out in README/legend as the recommendation's marker


    def rank_badge_icon(self, rank: int, color: str, is_winner: bool) -> folium.DivIcon:
        """A clean circular rank badge instead of a busy icon-in-a-pin marker --
    gives the 20 candidate sites clear visual priority over the competitor
    dots and the choropleth without competing icon shapes.

    The winner's fill/ring are fixed constants, not `color` (the rank-ramp
    color for its raw_score_rank) -- the scoring gate means the primary
    recommendation is not always raw_score_rank #1 (a higher-raw-score site
    that fails the AADT benchmark stays ranked above it but isn't
    selectable), so tying the winner's marker color to rank position would
    silently render it in whatever ramp color that rank happens to be
    instead of the distinct gold-ringed star the legend promises.
    """
        if is_winner:
            size = 36
            html = f"""
        <div style="width:{size}px; height:{size}px; border-radius:50%; background:{self.WINNER_FILL};
                    border:3px solid #ffffff; box-shadow:0 0 0 2.5px {self.WINNER_RING}, 0 3px 8px rgba(0,0,0,.45);
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


    @staticmethod
    def family_dollar_icon() -> folium.DivIcon:
        html = """
    <div style="width:30px; height:30px; border-radius:50%; background:#2a78d6; border:3px solid #ffffff;
          box-shadow:0 0 0 2px #1d4f91, 0 3px 8px rgba(0,0,0,.45); display:flex; align-items:center;
          justify-content:center; color:#ffffff; font-size:11px; font-weight:800; font-family:'Segoe UI',Arial,sans-serif;">
      FD
    </div>
    """
        return folium.DivIcon(html=html, icon_size=(30, 30), icon_anchor=(15, 15))


    @staticmethod
    def competitor_dot_icon(color: str) -> folium.DivIcon:
        html = f"""
    <div style="width:14px; height:14px; border-radius:50%; background:{color}; border:2px solid #ffffff;
          box-shadow:0 1px 3px rgba(0,0,0,.28);"></div>
    """
        return folium.DivIcon(html=html, icon_size=(14, 14), icon_anchor=(7, 7))



    @staticmethod
    def fema_zone_style(feature: dict) -> dict:
        zone = str(feature.get("properties", {}).get("FLD_ZONE", "X") or "X").upper().strip()
        if zone.startswith(("VE", "V")):
            return {"fillColor": "#1D4ED8", "color": "#1E3A8A", "weight": 0.8, "fillOpacity": 0.42, "opacity": 0.65}
        if zone.startswith(("A", "AE", "AH", "AO")):
            return {"fillColor": "#60A5FA", "color": "#2563EB", "weight": 0.7, "fillOpacity": 0.28, "opacity": 0.55}
        if zone.startswith("X"):
            return {"fillColor": "#BFDBFE", "color": "#3B82F6", "weight": 0.55, "fillOpacity": 0.16, "opacity": 0.45}
        if zone.startswith("D"):
            return {"fillColor": "#C7D2FE", "color": "#6366F1", "weight": 0.65, "fillOpacity": 0.20, "opacity": 0.5}
        return {"fillColor": "#93C5FD", "color": "#1D4ED8", "weight": 0.6, "fillOpacity": 0.22, "opacity": 0.5}


    @staticmethod
    def build_fema_frontend_loader_script(map_name: str, layer_name: str) -> str:
        """Load FEMA NFHL polygons on-demand in the browser so large geometry
    payloads are not stored in repository outputs.

    NFHL polygons are dense enough that a full-city envelope query blows
    past FEMA's own server-side transfer limit (verified directly against
    the live API: the citywide view's bounding box returns 'exceededTransferLimit'
    on the *first* 2,000-feature page alone, ~25MB, with an unknown number of
    pages still remaining) -- so a naive "fetch whatever the current map
    bounds are" approach silently fails or never finishes, which is exactly
    why the layer previously appeared empty. Fixed by (1) capping every query
    to a fixed-size envelope around the map center regardless of zoom, so no
    single request can ever approach the transfer limit, and (2) gating
    fetches behind a minimum zoom level with an on-map hint, since "all flood
    zones in Houston at once" is never a useful rendering at citywide scale.

    This is visualization-only. Analysis scoring still uses the existing
    pipeline outputs generated by enrichment scripts.
    """
        return f"""
(function() {{
  const mapVarName = '{map_name}';
  const layerVarName = '{layer_name}';
  const queryUrl = 'https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query';
  const MIN_ZOOM = 12;          // below this, a full-viewport query risks/exceeds FEMA's transfer limit
  const HALF_WIDTH_DEG = 0.035; // ~3.5mi fetch box centered on the map, regardless of zoom/pan -- keeps every request small and fast
  const MOVE_DEBOUNCE_MS = 450;

  let femaLoading = false;
  let femaGeoLayer = null;   // the currently-rendered L.geoJSON layer, replaced (not accumulated) on each refetch
  let moveTimer = null;
  let hintEl = null;

  function femaStyle(feature) {{
    const zone = String(((feature.properties || {{}}).FLD_ZONE || 'X')).toUpperCase().trim();
    if (zone.startsWith('VE') || zone.startsWith('V')) return {{ fillColor: '#1D4ED8', color: '#1E3A8A', weight: 0.8, fillOpacity: 0.42, opacity: 0.65 }};
    if (zone.startsWith('A')) return {{ fillColor: '#60A5FA', color: '#2563EB', weight: 0.7, fillOpacity: 0.28, opacity: 0.55 }};
    if (zone.startsWith('X')) return {{ fillColor: '#BFDBFE', color: '#3B82F6', weight: 0.55, fillOpacity: 0.16, opacity: 0.45 }};
    if (zone.startsWith('D')) return {{ fillColor: '#C7D2FE', color: '#6366F1', weight: 0.65, fillOpacity: 0.20, opacity: 0.5 }};
    return {{ fillColor: '#93C5FD', color: '#1D4ED8', weight: 0.6, fillOpacity: 0.22, opacity: 0.5 }};
  }}

  function onEachFemaFeature(feature, layer) {{
    const p = feature.properties || {{}};
    const zone = String(p.FLD_ZONE || 'X').toUpperCase().trim();
    const subtype = p.ZONE_SUBTY || 'n/a';
    const sfha = p.SFHA_TF || 'n/a';
    layer.bindTooltip('FEMA flood zone ' + zone + (subtype !== 'n/a' ? (' / ' + subtype) : ''));
    layer.bindPopup(
      "<div class='exec-card'><div class='exec-title'>FEMA NFHL Flood Zone</div>" +
      "<div class='exec-metric'><span>Zone</span><span class='exec-val'>" + zone + "</span></div>" +
      "<div class='exec-metric'><span>Subtype</span><span class='exec-val'>" + subtype + "</span></div>" +
      "<div class='exec-metric'><span>SFHA</span><span class='exec-val'>" + sfha + "</span></div>" +
      "<div class='src-note'>Source: FEMA NFHL MapServer layer 28 (live API)</div></div>",
      {{ maxWidth: 300 }}
    );
  }}

  function ensureHint(mapRef) {{
    if (hintEl) return hintEl;
    hintEl = L.control({{ position: 'bottomleft' }});
    hintEl.onAdd = function() {{
      const div = L.DomUtil.create('div');
      div.style.cssText = 'background:#1E3A8A; color:#fff; font:600 12px/1.3 "Segoe UI",Arial,sans-serif; ' +
        'padding:7px 11px; border-radius:7px; box-shadow:0 2px 8px rgba(0,0,0,.3); margin-bottom:14px;';
      div.innerText = 'Zoom in to load FEMA flood zones for this area';
      return div;
    }};
    return hintEl;
  }}

  function showHint(mapRef) {{ ensureHint(mapRef).addTo(mapRef); }}
  function hideHint(mapRef) {{ if (hintEl) mapRef.removeControl(hintEl); }}

  async function loadFemaFromApi(mapRef, femaLayerRef) {{
    if (femaLoading) return;
    if (mapRef.getZoom() < MIN_ZOOM) {{ showHint(mapRef); return; }}
    hideHint(mapRef);
    femaLoading = true;

    try {{
      const c = mapRef.getCenter();
      const envelope = [c.lng - HALF_WIDTH_DEG, c.lat - HALF_WIDTH_DEG, c.lng + HALF_WIDTH_DEG, c.lat + HALF_WIDTH_DEG].join(',');
      const params = new URLSearchParams({{
        where: '1=1',
        geometry: envelope,
        geometryType: 'esriGeometryEnvelope',
        inSR: '4326',
        spatialRel: 'esriSpatialRelIntersects',
        outFields: 'FLD_ZONE,ZONE_SUBTY,SFHA_TF,OBJECTID',
        returnGeometry: 'true',
        outSR: '4326',
        resultRecordCount: '2000',
        f: 'geojson',
      }});

      const resp = await fetch(queryUrl + '?' + params.toString());
      if (!resp.ok) throw new Error('FEMA query failed with status ' + resp.status);
      const data = await resp.json();
      const features = (data && data.features) ? data.features : [];

      if (femaGeoLayer) {{ femaLayerRef.removeLayer(femaGeoLayer); }}
      femaGeoLayer = L.geoJSON({{ type: 'FeatureCollection', features: features }}, {{
        style: femaStyle,
        onEachFeature: onEachFemaFeature,
      }});
      femaGeoLayer.addTo(femaLayerRef);
    }} catch (err) {{
      console.warn('Unable to load FEMA flood polygons from live API:', err);
    }} finally {{
      femaLoading = false;
    }}
  }}

  function scheduleReload(mapRef, femaLayerRef) {{
    if (moveTimer) clearTimeout(moveTimer);
    moveTimer = setTimeout(function() {{ loadFemaFromApi(mapRef, femaLayerRef); }}, MOVE_DEBOUNCE_MS);
  }}

  function bindWhenReady() {{
    const mapRef = window[mapVarName];
    const femaLayerRef = window[layerVarName];
    if (!mapRef || !femaLayerRef) {{
      setTimeout(bindWhenReady, 40);
      return;
    }}

    mapRef.on('overlayadd', function(ev) {{
      if (ev.layer === femaLayerRef) loadFemaFromApi(mapRef, femaLayerRef);
    }});
    mapRef.on('overlayremove', function(ev) {{
      if (ev.layer === femaLayerRef) hideHint(mapRef);
    }});
    mapRef.on('moveend', function() {{
      if (mapRef.hasLayer(femaLayerRef)) scheduleReload(mapRef, femaLayerRef);
    }});

    if (mapRef.hasLayer(femaLayerRef)) loadFemaFromApi(mapRef, femaLayerRef);
  }}

  bindWhenReady();
}})();
"""

    @staticmethod
    def build_dynamic_legend_script(map_name: str) -> str:
        """Keep the legend (build_legend_html) in sync with which layers are actually
    toggled on, live. Leaflet's built-in layer control fires 'overlayadd'/
    'overlayremove' on the map itself whenever a checkbox changes, with
    `e.name` equal to the exact string passed to that FeatureGroup's `name=`
    -- the same string build_legend_html tags each legend section with via
    `data-legend-layer`. No per-layer wiring needed here: this listens once,
    generically, for every current and future layer, as long as the legend
    section's data attribute matches that layer's real name exactly.

    Same "poll until the folium-generated map variable exists" pattern as
    build_fema_frontend_loader_script, since this script can run before
    folium's own map-initialization script has executed.
    """
        return f"""
(function() {{
  const mapVarName = '{map_name}';

  function cssEscape(s) {{
    return (window.CSS && CSS.escape) ? CSS.escape(s) : s.replace(/["\\\\]/g, '\\\\$&');
  }}

  function setLegendLayerVisible(name, visible) {{
    document.querySelectorAll('[data-legend-layer="' + cssEscape(name) + '"]').forEach(function(el) {{
      el.style.display = visible ? 'block' : 'none';
    }});
  }}

  function bindWhenReady() {{
    const mapRef = window[mapVarName];
    if (!mapRef) {{
      setTimeout(bindWhenReady, 40);
      return;
    }}
    mapRef.on('overlayadd', function(ev) {{ setLegendLayerVisible(ev.name, true); }});
    mapRef.on('overlayremove', function(ev) {{ setLegendLayerVisible(ev.name, false); }});
  }}

  bindWhenReady();
}})();
"""


    # --------------------------------------------------------------------------
    # Bottom-drawer dashboard
    # --------------------------------------------------------------------------

    @staticmethod
    def _risk_badge(risk: str) -> str:
        color = "#0ca30c" if risk == "Low" else ("#fab219" if risk == "Moderate" else "#d03b3b")
        label = risk.split(" (")[0]
        return f'<span style="background:{color}; color:white; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:700;">{label}</span>'


    @staticmethod
    def _parse_float(value: str | float | int | None) -> float | None:
        if value is None:
            return None
        if isinstance(value, (float, int)):
            return float(value)
        s = str(value).strip()
        if not s:
            return None
        filtered = "".join(ch for ch in s if ch.isdigit() or ch in ".-")
        if filtered in {"", ".", "-", "-."}:
            return None
        try:
            return float(filtered)
        except ValueError:
            return None


    @staticmethod
    def _status_chip(status: str) -> str:
        palette = {
            "Pass": ("#14532D", "#DCFCE7"),
            "Watch": ("#92400E", "#FEF3C7"),
            "Fail": ("#7F1D1D", "#FEE2E2"),
            "Gap": ("#0F172A", "#E2E8F0"),
            "Info": ("#334155", "#E2E8F0"),
        }
        fg, bg = palette.get(status, ("#334155", "#E2E8F0"))
        return f'<span style="color:{fg}; background:{bg}; padding:2px 8px; border-radius:10px; font-size:11px; font-weight:700;">{status}</span>'


    @staticmethod
    def _polygon_area_sqmi(geom: dict) -> float | None:
        geometry = geom.get("geometry") if geom.get("type") == "Feature" else geom
        if not geometry:
            return None

        def ring_area_sqmi(ring: list[list[float]]) -> float:
            if len(ring) < 4:
                return 0.0
            lon0 = sum(pt[0] for pt in ring) / len(ring)
            lat0 = sum(pt[1] for pt in ring) / len(ring)
            cos_lat = math.cos(math.radians(lat0))
            pts = [((pt[0] - lon0) * cos_lat * 69.172, (pt[1] - lat0) * 69.0) for pt in ring]
            s = 0.0
            for i in range(len(pts) - 1):
                x1, y1 = pts[i]
                x2, y2 = pts[i + 1]
                s += (x1 * y2) - (x2 * y1)
            return abs(s) * 0.5

        gtype = geometry.get("type")
        if gtype == "Polygon":
            rings = geometry.get("coordinates", [])
            if not rings:
                return None
            outer = ring_area_sqmi(rings[0])
            holes = sum(ring_area_sqmi(r) for r in rings[1:])
            return max(0.0, outer - holes)
        if gtype == "MultiPolygon":
            total = 0.0
            for poly in geometry.get("coordinates", []):
                if not poly:
                    continue
                outer = ring_area_sqmi(poly[0])
                holes = sum(ring_area_sqmi(r) for r in poly[1:])
                total += max(0.0, outer - holes)
            return total
        return None


    def build_executive_indicator_table(
        self,
        scorecard: list[dict],
        sites: dict[str, dict],
        trade: dict[str, dict],
        cannibalization: dict[str, dict],
        microsite: dict[str, dict],
        ci_rows: list[dict],
        isochrone: dict,
        houston_tracts: list[dict],
        county_tracts: list[dict],
        ext_demo: dict[str, dict],
        rigor_rows: list[dict],
        crime: dict[str, dict],
    ) -> str:
        winner = next((r for r in scorecard if r.get("primary_recommendation") == "True"), scorecard[0])
        h = winner["hcad_num"]
        site = sites[h]
        tr = trade[h]
        can = cannibalization[h]
        micro = microsite[h]

        city_ci = {r["statistic"]: r for r in ci_rows}
        rigor = {r["metric"]: r for r in rigor_rows}
        county_idx = {r["geoid"]: r for r in county_tracts}

        wlat, wlon = float(site["lat"]), float(site["lon"])
        nearest_tract = min(
            houston_tracts,
            key=lambda r: (float(r["lat"]) - wlat) ** 2 + (float(r["lon"]) - wlon) ** 2,
        )
        geoid = nearest_tract["geoid"]
        ext = ext_demo.get(geoid, {})
        county_row = county_idx.get(geoid, {})

        pop_5 = self._parse_float(tr.get("pop_5min_drive")) or 0.0
        hhi_5 = self._parse_float(tr.get("trade_area_median_income"))
        poverty_proxy = (self._parse_float(nearest_tract.get("poverty_rate")) or 0.0) * 100
        snap_proxy = (self._parse_float(county_row.get("snap_rate")) or 0.0) * 100
        zero_vehicle = (self._parse_float(ext.get("zero_vehicle_rate")) or 0.0) * 100
        renter = (self._parse_float(ext.get("renter_occupied_rate")) or 0.0) * 100
        foreign_born = (self._parse_float(ext.get("foreign_born_rate")) or 0.0) * 100
        spanish_home = (self._parse_float(ext.get("spanish_at_home_rate")) or 0.0) * 100

        iso_area = self._polygon_area_sqmi(isochrone.get("isochrones", {}).get("5min", {}))
        density_5 = (pop_5 / iso_area) if iso_area and iso_area > 0 else None

        city_poverty = self._parse_float(city_ci.get("Poverty rate", {}).get("estimate")) or 0.0
        city_zero_vehicle = self._parse_float(city_ci.get("Zero-vehicle household share", {}).get("estimate")) or 0.0
        city_renter = self._parse_float(city_ci.get("Renter-occupied housing share", {}).get("estimate")) or 0.0
        city_foreign = self._parse_float(city_ci.get("Foreign-born share", {}).get("estimate")) or 0.0
        city_spanish = self._parse_float(city_ci.get("Spanish spoken at home", {}).get("estimate")) or 0.0

        aadt = self._parse_float(site.get("aadt")) or 0.0
        speed = self._parse_float(micro.get("posted_speed_limit_mph"))
        bus_500 = int(self._parse_float(micro.get("bus_stops_within_500ft")) or 0)
        cotenants_03 = int(self._parse_float(micro.get("co_tenant_count_0_3mi")) or 0)

        nearest_arch_mi = self._parse_float(rigor.get("winner_nearest_arch_rival_distance_mi", {}).get("value"))
        nearest_arch_drive_min = self._parse_float(rigor.get("winner_nearest_arch_rival_drive_time_min", {}).get("value"))
        nearest_fd_mi = self._parse_float(can.get("nearest_family_dollar_mi")) or 0.0
        overlap_pct = self._parse_float(can.get("overlap_pct")) or 0.0
        net_new = int(self._parse_float(can.get("net_new_population_reach")) or 0.0)

        flood_zone = site.get("flood_zone", "n/a")
        acreage = self._parse_float(site.get("acreage")) or 0.0
        land_value = self._parse_float(site.get("land_value")) or 0.0
        value_per_acre = (land_value / acreage) if acreage > 0 else None

        crime_row = crime.get(h, {})
        violent_crime = int(self._parse_float(crime_row.get("violent_crime_count_12mo_0_5mi")) or 0)
        property_crime = int(self._parse_float(crime_row.get("property_crime_count_12mo_0_5mi")) or 0)
        total_crime = int(self._parse_float(crime_row.get("total_index_crime_count_12mo_0_5mi")) or 0)

        rows = [
            ("Macro demand", "5-min trade-area median HHI", f"${hhi_5:,.0f}" if hhi_5 else "n/a", "$20k-$55k", "Pass" if hhi_5 is not None and 20000 <= hhi_5 <= 55000 else "Watch"),
            ("Macro demand", "SNAP household share (nearest tract proxy)", f"{snap_proxy:.1f}%", "> 18%", "Pass" if snap_proxy > 18 else "Watch"),
            ("Macro demand", "Poverty rate (nearest tract proxy)", f"{poverty_proxy:.1f}%", f"> city avg ({city_poverty:.1f}%)", "Pass" if poverty_proxy > city_poverty else "Watch"),
            ("Macro demand", "5-min drive population", f"{int(pop_5):,}", "10,000-25,000+", "Pass" if pop_5 >= 10000 else "Fail"),
            ("Macro demand", "5-min drive population density", f"{density_5:,.0f}/sq mi" if density_5 else "n/a", "> 2,500/sq mi", "Pass" if density_5 is not None and density_5 > 2500 else ("Watch" if density_5 is not None else "Gap")),
            ("Macro demand", "Zero-vehicle household share", f"{zero_vehicle:.1f}%", f"> city avg ({city_zero_vehicle:.1f}%)", "Pass" if zero_vehicle > city_zero_vehicle else "Watch"),
            ("Macro demand", "Renter-occupied housing share", f"{renter:.1f}%", f"> city avg ({city_renter:.1f}%)", "Pass" if renter > city_renter else "Watch"),
            ("Macro demand", "Foreign-born share", f"{foreign_born:.1f}%", f"> city avg ({city_foreign:.1f}%)", "Pass" if foreign_born > city_foreign else "Watch"),
            ("Macro demand", "Spanish spoken at home", f"{spanish_home:.1f}%", f"> city avg ({city_spanish:.1f}%)", "Pass" if spanish_home > city_spanish else "Watch"),
            ("Micro accessibility", "Verified AADT", f"{int(aadt):,} vpd", ">= 8,000", "Pass" if aadt >= 8000 else "Fail"),
            ("Micro accessibility", "Posted speed limit", f"{int(speed)} mph" if speed is not None else "n/a", "35-45 mph", "Pass" if speed is not None and 35 <= speed <= 45 else ("Watch" if speed is not None else "Gap")),
            ("Micro accessibility", "Road functional class", micro.get("road_functional_class", "n/a"), "Arterial/frontage preferred", "Pass" if "freeway" not in micro.get("road_functional_class", "").lower() else "Watch"),
            ("Micro accessibility", "Bus stops within 500 ft", str(bus_500), ">= 1 preferred", "Pass" if bus_500 >= 1 else "Watch"),
            ("Micro accessibility", "Co-tenancy generators within 0.3 mi", str(cotenants_03), ">= 2 preferred", "Pass" if cotenants_03 >= 2 else "Watch"),
            ("Competition/network", "Nearest direct arch-rival (straight-line)", f"{nearest_arch_mi:.2f} mi" if nearest_arch_mi is not None else "n/a", "> 1.5 mi", "Pass" if nearest_arch_mi is not None and nearest_arch_mi > 1.5 else ("Watch" if nearest_arch_mi is not None else "Gap")),
            ("Competition/network", "Nearest direct arch-rival (OSRM drive)", f"{nearest_arch_drive_min:.1f} min" if nearest_arch_drive_min is not None else "n/a", "> 5 min", "Pass" if nearest_arch_drive_min is not None and nearest_arch_drive_min > 5 else ("Watch" if nearest_arch_drive_min is not None else "Gap")),
            ("Competition/network", "Huff gravity capture", f"{tr.get('huff_capture_pct', 'n/a')}%", "Higher is better", "Info"),
            ("Competition/network", "Nearest existing Family Dollar", f"{nearest_fd_mi:.2f} mi", "> 1.2 mi hard buffer", "Pass" if nearest_fd_mi >= 1.2 else "Fail"),
            ("Competition/network", "Trade-area overlap with existing FD", f"{overlap_pct:.1f}%", "< 15% target", "Pass" if overlap_pct < 15 else ("Watch" if overlap_pct < 30 else "Fail")),
            ("Competition/network", "Net-new population reach", f"{net_new:,}", "Higher is better", "Info"),
            ("Physical/risk/cost", "FEMA flood zone", flood_zone, "Zone X preferred", "Pass" if str(flood_zone).upper().startswith("X") else "Fail"),
            ("Physical/risk/cost", "Parcel size", f"{acreage:.2f} acres", "1.0-2.5 acres", "Pass" if 1.0 <= acreage <= 2.5 else ("Watch" if 0.5 <= acreage < 1.0 else "Fail")),
            ("Physical/risk/cost", "Appraised land value", f"${land_value:,.0f}", "Feasibility input", "Info"),
            ("Physical/risk/cost", "Appraised land value per acre", f"${value_per_acre:,.0f}/acre" if value_per_acre else "n/a", "Feasibility screening", "Info"),
            ("Physical/risk/cost", "Violent crime incidents (real HPD Part I, 0.5mi, trailing 12mo)", str(violent_crime), "Lower is better", "Info"),
            ("Physical/risk/cost", "Property crime incidents (real HPD Part I, 0.5mi, trailing 12mo)", str(property_crime), "Lower is better", "Info"),
            ("Physical/risk/cost", "Total index crime incidents (0.5mi, trailing 12mo)", str(total_crime), "Lower is better", "Info"),
        ]

        body_rows = "".join(
            f"<tr style='border-bottom:1px solid #E5E7EB;'>"
            f"<td style='padding:6px 8px;'>{d}</td>"
            f"<td style='padding:6px 8px; font-weight:700;'>{i}</td>"
            f"<td style='padding:6px 8px; text-align:right;'>{v}</td>"
            f"<td style='padding:6px 8px;'>{b}</td>"
            f"<td style='padding:6px 8px; text-align:center;'>{self._status_chip(s)}</td>"
            f"</tr>"
            for d, i, v, b, s in rows
        )

        return f"""
    <p style='color:#374151; font-size:12.5px; margin:0 0 10px;'>Executive checklist for the current primary recommendation. Macro demographic rates use the nearest tract as a local proxy and are paired with city-wide ACS confidence-interval baselines.</p>
    <div style='overflow-x:auto;'>
      <table style='border-collapse:collapse; width:100%; font-size:12px; color:#1F2937;'>
      <thead><tr style='background:#F3F4F6; text-align:left; border-bottom:2px solid #D1D5DB;'>
        <th style='padding:6px 8px;'>Domain</th><th style='padding:6px 8px;'>Indicator</th><th style='padding:6px 8px; text-align:right;'>Current value</th>
        <th style='padding:6px 8px;'>Benchmark</th><th style='padding:6px 8px; text-align:center;'>Status</th>
      </tr></thead>
      <tbody>{body_rows}</tbody>
      </table>
    </div>
    """


    def build_rigor_table(self, rigor_rows: list[dict], sensitivity: list[dict]) -> str:
        if not rigor_rows:
            return "<p style='color:#92400E;'>Statistical rigor outputs are missing. Run pipeline stage 29 (statistical_rigor) and regenerate the map.</p>"

        display_order = [
            "moran_i_residuals",
            "moran_i_expected",
            "moran_i_permutation_pvalue",
            "spatial_block_cv_rmse_mean",
            "spatial_block_cv_r2_mean",
            "spatial_block_cv_r2_std",
            "spatial_block_cv_n_folds",
            "ols_in_sample_rmse",
            "ols_in_sample_r2",
        ]
        idx = {r["metric"]: r for r in rigor_rows}
        rows = [idx[m] for m in display_order if m in idx]

        n_stable = sum(1 for r in sensitivity if r.get("same_as_base_recommendation") == "True")
        row_html = "".join(
            f"<tr style='border-bottom:1px solid #E5E7EB;'>"
            f"<td style='padding:6px 8px; font-weight:700;'>{r['metric']}</td>"
            f"<td style='padding:6px 8px; text-align:right;'>{r['value']}</td>"
            f"<td style='padding:6px 8px;'>{r['benchmark']}</td>"
            f"<td style='padding:6px 8px; text-align:center;'>{self._status_chip(r['status'])}</td>"
            f"<td style='padding:6px 8px; color:#475569; font-size:11px;'>{r['notes']}</td>"
            f"</tr>"
            for r in rows
        )

        return f"""
    <p style='color:#374151; font-size:12.5px; margin:0 0 10px;'>Rigor outputs combine ACS uncertainty reporting, spatial autocorrelation diagnostics, and out-of-sample spatial block validation to reduce leakage and overconfidence.</p>
    <div style='overflow-x:auto;'>
      <table style='border-collapse:collapse; width:100%; font-size:12px; color:#1F2937;'>
      <thead><tr style='background:#F3F4F6; text-align:left; border-bottom:2px solid #D1D5DB;'>
        <th style='padding:6px 8px;'>Metric</th><th style='padding:6px 8px; text-align:right;'>Value</th>
        <th style='padding:6px 8px;'>Benchmark</th><th style='padding:6px 8px; text-align:center;'>Status</th><th style='padding:6px 8px;'>Notes</th>
      </tr></thead>
      <tbody>{row_html}</tbody>
      </table>
    </div>
    <p style='color:#374151; font-size:12px; margin-top:12px;'><b>Census ratio MOE formula used:</b> MOE<sub>p</sub> = (1/Y) × sqrt(MOE<sub>X</sub><sup>2</sup> - p<sup>2</sup> × MOE<sub>Y</sub><sup>2</sup>) with Census fallback to the + form when needed.</p>
    <p style='color:#374151; font-size:12px; margin-top:6px;'><b>Ranking stability:</b> {n_stable} of {len(sensitivity)} sensitivity scenarios retain the same primary recommendation.</p>
    """


    @staticmethod
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
          <td style="padding:6px 8px; text-align:right;">{r['crime_score']}</td>
          <td style="padding:6px 8px; text-align:center;">{aadt_badge}</td>
        </tr>""")
        return f"""
    <p style="color:#374151; font-size:12.5px; margin:0 0 10px;">All 20 real citywide candidates, ranked by weighted score
    (22% demand, 18% Huff capture, 13% competitive gap, 13% traffic, 14% cost/feasibility, 10% flood risk, 10% crime risk).
    The <b>primary recommendation</b> is the highest-scoring site that also clears the 8,000 AADT minimum-traffic
    benchmark (&#10003; column) -- a higher raw score that fails the benchmark is shown but not selected. Full detail: <code>data/processed/scorecard.csv</code>.</p>
    <div style="overflow-x:auto;">
    <table style="border-collapse:collapse; width:100%; font-size:12px; color:#1F2937;">
      <thead><tr style="background:#F3F4F6; text-align:left; border-bottom:2px solid #D1D5DB;">
        <th style="padding:6px 8px;">Rank</th><th style="padding:6px 8px;">Neighborhood</th><th style="padding:6px 8px;">Site</th>
        <th style="padding:6px 8px; text-align:right;">Total</th><th style="padding:6px 8px; text-align:right;">Demand</th>
        <th style="padding:6px 8px; text-align:right;">Huff</th><th style="padding:6px 8px; text-align:right;">Comp.</th>
        <th style="padding:6px 8px; text-align:right;">Traffic</th><th style="padding:6px 8px; text-align:right;">Cost</th>
        <th style="padding:6px 8px; text-align:right;">Flood</th><th style="padding:6px 8px; text-align:right;">Crime</th>
        <th style="padding:6px 8px; text-align:center;">&ge;8k AADT</th>
      </tr></thead>
      <tbody>{"".join(rows_html)}</tbody>
    </table>
    </div>
    """


    @staticmethod
    def build_sensitivity_table(sensitivity: list[dict]) -> str:
        base_site = sensitivity[0]["primary_recommendation"]
        n_stable = sum(1 for r in sensitivity if r["same_as_base_recommendation"] == "True")
        rows_html = "".join(f"""
        <tr style="border-bottom:1px solid #E5E7EB; {'background:#F0FDF4;' if r['same_as_base_recommendation']=='True' else ''}">
          <td style="padding:6px 8px; font-weight:700;">{r['scenario']}</td>
          <td style="padding:6px 8px; color:#6B7280; font-size:11px;">{r['weights']}</td>
          <td style="padding:6px 8px;">{r['primary_recommendation']}</td>
          <td style="padding:6px 8px; text-align:right;">{r['primary_recommendation_score']}</td>
          <td style="padding:6px 8px; text-align:center;">{'<span style="color:#0ca30c;font-weight:700;">&#10003; same</span>' if r['same_as_base_recommendation']=='True' else '<span style="color:#d03b3b;font-weight:700;">&#10007; differs</span>'}</td>
        </tr>""" for r in sensitivity)
        return f"""
    <div style="border-top:2px solid #E5E7EB; margin-top:18px; padding-top:14px;">
    <div style="font-weight:700; color:#1F2937; font-size:13px; margin-bottom:6px;">Sensitivity analysis: does the recommendation hold under different weights?</div>
    <p style="color:#374151; font-size:12.5px; margin:0 0 10px;">The same real, already-computed per-factor scores (script 20), re-aggregated under
    5 different weighting philosophies -- a re-aggregation check, not new data. <b>{base_site}</b> is the primary recommendation in
    {n_stable} of {len(sensitivity)} scenarios tested, including the documented base case, and never finishes worse than #2 among all 20 real candidates
    in the scenarios where it isn't #1. It is <i>not</i> universally #1 under every possible weighting -- honestly reported, not smoothed over: a
    traffic-maximizing or competition-maximizing philosophy can favor a different real site, which is an expected, real trade-off between site
    selection philosophies, not an error.</p>
    <div style="overflow-x:auto;">
    <table style="border-collapse:collapse; width:100%; font-size:12px; color:#1F2937;">
      <thead><tr style="background:#F3F4F6; text-align:left; border-bottom:2px solid #D1D5DB;">
        <th style="padding:6px 8px;">Scenario</th><th style="padding:6px 8px;">Weights</th><th style="padding:6px 8px;">Winner</th>
        <th style="padding:6px 8px; text-align:right;">Score</th><th style="padding:6px 8px; text-align:center;">vs. base case</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    </div>
    </div>
    """


    def build_cannibalization_table(self, cannibalization: list[dict]) -> str:
        rows_html = []
        for r in cannibalization:
            rows_html.append(f"""
        <tr style="border-bottom:1px solid #E5E7EB;">
          <td style="padding:6px 8px;">{r['site_label'].split(') - ')[0]})</td>
          <td style="padding:6px 8px; text-align:right;">{r['nearest_family_dollar_mi']} mi</td>
          <td style="padding:6px 8px;">{r['hard_buffer_flag']}</td>
          <td style="padding:6px 8px; text-align:right;">{r['overlap_pct']}%</td>
          <td style="padding:6px 8px; text-align:right;">{int(float(r['net_new_population_reach'])):,}</td>
          <td style="padding:6px 8px; text-align:center;">{self._risk_badge(r['cannibalization_risk'])}</td>
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


    @staticmethod
    def build_microsite_table(microsite: list[dict]) -> str:
        rows_html = "".join(f"""
        <tr style="border-bottom:1px solid #E5E7EB;">
          <td style="padding:6px 8px;">{r['site_label'].split(') - ')[0]})</td>
          <td style="padding:6px 8px; text-align:right;">{r['posted_speed_limit_mph']}</td>
          <td style="padding:6px 8px;">{r['speed_assessment']}</td>
          <td style="padding:6px 8px;">{r['nearby_co_tenants']}</td>
          <td style="padding:6px 8px;">{r['nearest_transit_stop']}</td>
          <td style="padding:6px 8px;">{r['approx_lot_dimensions']}</td>
        </tr>""" for r in microsite)
        return f"""
    <p style="color:#374151; font-size:12.5px; margin:0 0 6px;">Operational detail beyond the macro numbers.
    Speed limit is OSM's tagged posted limit on the frontage road where mapped; dollar-store visibility/impulse-stop
    traffic works best at 35-45 mph. Co-tenants are real nearby POIs (gas stations, laundromats, schools, post
    offices, pharmacies) within 0.3 mi that generate shared neighborhood trips. Transit stop is the real nearest
    OSM-mapped bus stop/platform within 1 mile -- dollar-store customers in urban corridors frequently walk or bus
    in for top-off trips. Lot dimensions are an approximate bounding box computed from the real HCAD parcel polygon
    (haversine edge lengths) -- a gut-check on whether the lot is plausibly large enough, not a certified survey.</p>
    <p style="color:#92400E; background:#FEF3C7; font-size:11.5px; padding:6px 8px; border-radius:6px; margin:0 0 10px;">
    <b>Not verifiable from any public data source</b> (flagged rather than guessed): deed restrictions / restrictive
    covenants (requires a title search), median-break / divided-highway ingress-egress geometry, and an engineered
    53-ft delivery-truck turning radius (requires a civil site plan). Houston has no municipal zoning -- the
    general off-street parking ratio (city code, roughly 1 space per 200-300 sq ft of retail) is cited as
    informational context in the Data Validation tab, not computed as a parcel-specific verified figure. Real
    property/violent crime risk (HPD NIBRS Part I incidents, 0.5mi, trailing 12mo) IS now covered -- see the
    Executive Checks and Scorecard tabs.</p>
    <div style="overflow-x:auto;">
    <table style="border-collapse:collapse; width:100%; font-size:12px; color:#1F2937;">
      <thead><tr style="background:#F3F4F6; text-align:left; border-bottom:2px solid #D1D5DB;">
        <th style="padding:6px 8px;">Site</th><th style="padding:6px 8px; text-align:right;">Speed limit</th>
        <th style="padding:6px 8px;">Assessment</th><th style="padding:6px 8px;">Nearby co-tenants</th>
        <th style="padding:6px 8px;">Nearest transit</th><th style="padding:6px 8px;">Approx. lot dimensions</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    </div>
    """


    @staticmethod
    def build_ci_table(ci_rows: list[dict]) -> str:
        rows_html = "".join(f"""
        <tr style="border-bottom:1px solid #E5E7EB;">
          <td style="padding:7px 8px; font-weight:700;">{r['statistic']}</td>
          <td style="padding:7px 8px; text-align:right;">{r['estimate']}</td>
          <td style="padding:7px 8px; text-align:right;">{r['moe_90pct']}</td>
          <td style="padding:7px 8px; text-align:right;">{r['ci_90pct_low']}-{r['ci_90pct_high']}</td>
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


    @staticmethod
    def build_validation_html() -> str:
        return """
    <div style="font-size:12.5px; color:#1F2937; line-height:1.65;">
    <p><b>Every data point on this map traces to a live, free, public API</b> -- no proprietary vendor data
    (SafeGraph, Placer.ai, Esri) and no invented numbers. Full source catalog and methodology:
    <code>docs/methodology.md</code> and <code>docs/data_validation.md</code> in the repository.</p>

    <p style="font-weight:700; margin-bottom:4px;">Sources (all free, all keyless)</p>
    <ul style="margin-top:0; padding-left:18px;">
      <li>US Census Bureau -- TIGERweb (boundaries) + Census Reporter API (ACS 2024 5-yr demographics, incl.
      margins of error, vehicle access, and housing tenure)</li>
      <li>OpenStreetMap / Overpass API -- 528 real competitor/anchor locations across 15 banners, arterial road
      network, posted speed limits, transit stops, co-tenant POIs</li>
      <li>Harris County Appraisal District (HCAD) -- real parcel boundaries, land use, appraised value</li>
      <li>FEMA National Flood Hazard Layer (NFHL) -- flood zone identification</li>
      <li>TxDOT -- Annual Average Daily Traffic (AADT), verified by reverse-geocoding each station</li>
      <li>OSRM -- real drive-time routing + Huff gravity market-capture model</li>
      <li>Nominatim (OpenStreetMap) -- reverse geocoding for site/neighborhood/road verification</li>
      <li>Houston Police Department -- real point-level NIBRS Part I violent/property crime incident exports
      (direct CSV download from houstontx.gov, not the CKAN catalog), trailing 12 months within 0.5mi of each site</li>
      <li>HUD LIHTC Database -- real, geocoded affordable-housing properties within 1mi of each site (ArcGIS REST)</li>
      <li>Census LEHD LODES -- real block-level workplace/job counts, real daytime population signal within each
      site's 5-minute drive trade area</li>
      <li>USDA ERS Food Access Research Atlas (SNAP-authorized Retailer Access Map) -- real per-tract share of
      population beyond 0.5mi from a food retailer</li>
      <li>Overture Maps Places -- free, open (CDLA Permissive 2.0), ML-deduped POI data blending Meta/Microsoft/
      TomTom/~200 other sources, used as a real cross-check against the OSM-sourced competitor pull</li>
      <li>Census Population Estimates Program (PEP) -- real annual City of Houston population estimates,
      2020-2024, direct CSV release (keyless, since the PEP's own REST API now requires a registered key) --
      citywide growth-trend context, not a per-site scored factor</li>
      <li>Federal Qualified Opportunity Zones (CDFI Fund / Treasury, via ArcGIS) -- real federal
      tax-advantaged-investment tract designations, checked by real point-in-polygon intersection</li>
      <li>HUD Multifamily Properties -- real, FHA-insured/HUD-assisted apartment and senior-housing
      properties, a different federal program than LIHTC (mortgage insurance/project-based assistance,
      not tax credits)</li>
    </ul>

    <p style="font-weight:700; margin-bottom:4px;">Specific checks performed against hallucination / error</p>
    <ul style="margin-top:0; padding-left:18px;">
      <li><b>A second free-data pass, run specifically to check nothing obvious and free was missed before
      finalizing which data sources genuinely require a paid license:</b> re-checked every paid category (mobile
      foot-traffic data, consumer spending data, commercial real estate data, enterprise traffic data, commercial
      crime scoring, enhanced business-listings data) for a free alternative, and found one real one (Overture
      Maps, added above) plus three other real free datasets this model had never used (HUD LIHTC, Census LEHD,
      USDA Food Access) -- each verified live and added as a real signal rather than assumed available.</li>
      <li><b>A sensitivity analysis (re-aggregating the same real scores under 6 different weighting schemes,
      Scorecard tab) exposed a real bug that changed the actual recommendation:</b> the freeway-name filter
      correctly rejected station names containing "Freeway," but a legitimate frontage road sharing that name
      (e.g. "Gulf Freeway Frontage Road" -- a real street with real driveway access, common in Houston retail)
      was being wrongly rejected too, understating several sites' true traffic. Fixed by excluding any name
      containing "frontage" from the freeway check, since frontage/access roads have real driveway access even
      when named after the freeway they parallel. Re-verified live against TxDOT afterward: the corrected
      19,656 AADT reading is a real frontage-road-specific count, distinct from that corridor's ~193,000
      freeway-mainline count nearby -- both real, different roads, same route number.</li>
      <li>The winning site's HCAD record, FEMA flood zone, and TxDOT AADT count were independently re-queried
      live against the source APIs (not just the cached pipeline output) and matched.</li>
      <li>TxDOT records roads by route number, not name -- every AADT match was reverse-geocoded to a real street,
      and stations that resolved to a freeway/tollway mainline (no legal driveway access) were rejected in favor
      of the nearest genuine arterial or frontage-road reading.</li>
      <li>Each site's neighborhood was independently reverse-geocoded rather than inherited from its search
      cluster, after finding a case where the two disagreed.</li>
      <li><b>Property/violent crime risk was re-investigated and a real source found.</b> The original check
      queried only Houston's open-data CKAN catalog (data.houstontx.gov, <code>package_search</code>/
      <code>package_show</code>), which genuinely has no queryable crime dataset. That check missed that HPD's
      own site separately publishes real, point-level NIBRS Part I incident data (offense code, date, lat/lon) as
      direct CSV downloads, free and keyless, back to 2009. Added as a real 7th scoring factor (10% weight):
      violent + property incident counts within 0.5mi of each site, trailing 12 months, classified using the
      standard FBI UCR Part I definition (murder, rape, robbery, aggravated assault = violent; burglary,
      larceny-theft, motor vehicle theft = property) -- not scraped or estimated, and not the same thing as the
      CKAN catalog that was checked before.</li>
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
      <li>This FEMA overlay itself was a caught bug: an earlier version queried the live FEMA API for the
      full current map view, which was tested directly against the API and confirmed to exceed FEMA's own
      transfer limit on the first page alone (~25MB, more pages remaining) -- so the layer never finished
      loading. Fixed by capping every request to a fixed area around the map center and requiring a minimum
      zoom level, refetching as you pan.</li>
      <li>The recommended site's marker color was originally computed from its raw score-rank position on the
      best-to-worst ramp, which only rendered green because the current #1 raw score also happens to be the
      primary recommendation -- a coincidence, not a guarantee, since the AADT gate can make the primary
      recommendation a different site than the raw #1. Fixed so the winner's color and gold ring are fixed
      constants, independent of rank.</li>
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


    def build_dashboard_html(
      self,
      scorecard: list[dict],
      cannibalization: list[dict],
      ci_rows: list[dict],
      microsite: list[dict],
      sensitivity: list[dict],
      sites: dict[str, dict],
      trade: dict[str, dict],
      canib_map: dict[str, dict],
      micro_map: dict[str, dict],
      isochrone: dict,
      houston_tracts: list[dict],
      county_tracts: list[dict],
      ext_demo: dict[str, dict],
      rigor_rows: list[dict],
      crime_map: dict[str, dict],
    ) -> str:
        return f"""
<div id="dash-drawer">
  <div id="dash-titlebar">
    <div>
      <div id="dash-title-main">Analysis Dashboard</div>
      <div id="dash-title-sub">Executive-ready metrics, model checks, and audit traceability</div>
    </div>
    <button id="dash-close" onclick="fdToggleDash()" title="Close">&#10005;</button>
  </div>
  <div id="dash-tabs-row">
    <div id="dash-tabs">
      <button class="dash-tab-btn active" id="tabbtn-exec" onclick="fdShowTab('exec')">Executive Checks</button>
      <button class="dash-tab-btn" id="tabbtn-scorecard" onclick="fdShowTab('scorecard')">Scorecard</button>
      <button class="dash-tab-btn" id="tabbtn-cannibalization" onclick="fdShowTab('cannibalization')">Cannibalization</button>
      <button class="dash-tab-btn" id="tabbtn-microsite" onclick="fdShowTab('microsite')">Site Details</button>
      <button class="dash-tab-btn" id="tabbtn-ci" onclick="fdShowTab('ci')">Confidence Intervals</button>
      <button class="dash-tab-btn" id="tabbtn-rigor" onclick="fdShowTab('rigor')">Model Rigor</button>
      <button class="dash-tab-btn" id="tabbtn-validation" onclick="fdShowTab('validation')">Sources &amp; Validation</button>
    </div>
  </div>
  <div class="dash-body">
    <div class="dash-tab-content active" id="tab-exec">{self.build_executive_indicator_table(scorecard, sites, trade, canib_map, micro_map, ci_rows, isochrone, houston_tracts, county_tracts, ext_demo, rigor_rows, crime_map)}</div>
    <div class="dash-tab-content" id="tab-scorecard">{self.build_scorecard_table(scorecard)}{self.build_sensitivity_table(sensitivity)}</div>
    <div class="dash-tab-content" id="tab-cannibalization">{self.build_cannibalization_table(cannibalization)}</div>
    <div class="dash-tab-content" id="tab-microsite">{self.build_microsite_table(microsite)}</div>
    <div class="dash-tab-content" id="tab-ci">{self.build_ci_table(ci_rows)}</div>
    <div class="dash-tab-content" id="tab-rigor">{self.build_rigor_table(rigor_rows, sensitivity)}</div>
    <div class="dash-tab-content" id="tab-validation">{self.build_validation_html()}</div>
  </div>
</div>
<script>
  function fdToggleDash() {{
    document.getElementById('dash-drawer').classList.toggle('open');
  }}
  function fdShowTab(name) {{
    document.querySelectorAll('.dash-tab-content').forEach(function(el) {{ el.classList.remove('active'); }});
    document.querySelectorAll('.dash-tab-btn').forEach(function(el) {{ el.classList.remove('active'); }});
    document.getElementById('tab-' + name).classList.add('active');
    document.getElementById('tabbtn-' + name).classList.add('active');
  }}
</script>
"""


    def run(self) -> Path:
        output_path = ROOT / "index.html"

        scorecard = self.load_csv("scorecard.csv")
        sites = {r["hcad_num"]: r for r in self.load_csv("sites_enriched.csv")}
        trade = {r["hcad_num"]: r for r in self.load_csv("site_trade_areas.csv")}
        cannibalization = {r["hcad_num"]: r for r in self.load_csv("cannibalization.csv")}
        microsite = {r["hcad_num"]: r for r in self.load_csv("microsite_details.csv")}
        crime_map = {r["hcad_num"]: r for r in self.load_csv("site_crime_risk.csv")}
        ci_rows = self.load_csv("city_confidence_intervals.csv")
        extended_demo = {r["geoid"]: r for r in self.load_csv("tract_extended_demographics.csv")}
        houston_tracts = self.load_csv("houston_tracts.csv")
        county_tracts = self.load_csv("tracts.csv")
        competitors = self.load_csv("competitors.csv")
        rigor_rows = self.load_csv("statistical_rigor.csv") if (PROCESSED / "statistical_rigor.csv").exists() else []
        tracts = self.load_json("houston_tracts.geojson")
        boundary = self.load_json("houston_boundary.geojson")
        isochrone = self.load_json("isochrone_winner.json")

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

        m.get_root().header.add_child(folium.Element(self.PAGE_CHROME_CSS))
        m.get_root().html.add_child(folium.Element(self.build_header_html(scorecard[0]["address"], scorecard[0]["neighborhood"])))

        # --- Layer: Houston city limits (real boundary, for scale/context) ----------
        boundary_layer = folium.FeatureGroup(name="Houston city limits", show=False)
        folium.GeoJson(
            boundary,
            style_function=lambda _f: {"fillOpacity": 0, "color": "#1E3A8A", "weight": 2.5, "dashArray": "6,4"},
            tooltip="City of Houston boundary (TIGERweb)",
        ).add_to(boundary_layer)
        boundary_layer.add_to(m)

        # --- Layer: FEMA flood-zone polygons (NFHL, off by default) -----------------
        flood_layer = folium.FeatureGroup(name="FEMA flood zones (NFHL, live API, off by default)", show=False)
        flood_layer.add_to(m)

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
            color = ColorRamp.interpolate(t, ColorRamp.SEQUENTIAL_BLUE)
            fill_opacity = 0.12 + 0.5 * t
            pop = float(p["population"]) if p.get("population") else 0
            mhi = float(p["median_hh_income"]) if p.get("median_hh_income") else None
            pov = float(p["poverty_rate"]) * 100 if p.get("poverty_rate") else None
            ext = extended_demo.get(p["geoid"], {})
            fb = float(ext["foreign_born_rate"]) * 100 if ext.get("foreign_born_rate") not in (None, "") else None
            span = float(ext["spanish_at_home_rate"]) * 100 if ext.get("spanish_at_home_rate") not in (None, "") else None
            hh = float(ext["avg_household_size"]) if ext.get("avg_household_size") not in (None, "") else None
            zv = float(ext["zero_vehicle_rate"]) * 100 if ext.get("zero_vehicle_rate") not in (None, "") else None
            rent = float(ext["renter_occupied_rate"]) * 100 if ext.get("renter_occupied_rate") not in (None, "") else None
            popup = (
                f"<div class='exec-card'><div class='exec-title'>{p['name']}</div>"
                f"<div class='exec-metric'><span>Population</span><span class='exec-val'>{pop:,.0f}</span></div>"
                f"<div class='exec-metric'><span>Median HH Income</span><span class='exec-val'>{'$'+format(mhi, ',.0f') if mhi else 'n/a'}</span></div>"
                f"<div class='exec-metric'><span>Poverty Rate</span><span class='exec-val'>{pov:.1f}%</span></div>"
                f"<div class='exec-metric'><span>Foreign-Born Share</span><span class='exec-val'>{f'{fb:.1f}%' if fb is not None else 'n/a'}</span></div>"
                f"<div class='exec-metric'><span>Spanish Spoken at Home</span><span class='exec-val'>{f'{span:.1f}%' if span is not None else 'n/a'}</span></div>"
                f"<div class='exec-metric'><span>Avg. Household Size</span><span class='exec-val'>{f'{hh:.2f}' if hh is not None else 'n/a'}</span></div>"
                f"<div class='exec-metric'><span>Zero-Vehicle Households</span><span class='exec-val'>{f'{zv:.1f}%' if zv is not None else 'n/a'}</span></div>"
                f"<div class='exec-metric'><span>Renter-Occupied Housing</span><span class='exec-val'>{f'{rent:.1f}%' if rent is not None else 'n/a'}</span></div>"
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

        # --- Layer: competitors, 4 categories -----------------------------------------
        # Family Dollar gets its own always-on layer: existing FD locations are the
        # company's own network (cannibalization question), not a competitive threat,
        # and that distinction is the single most important competitor fact here.
        # Dollar Tree is grouped into arch-rivals, not a separate "sister banner" tier --
        # Family Dollar and Dollar Tree officially separated on 2025-07-08 (Dollar Tree
        # sold Family Dollar to private equity), so Dollar Tree is now a real, same-format
        # competitor rather than a same-parent-company banner.
        category_layers = {
            k: folium.FeatureGroup(name=v, show=self.COMPETITOR_LAYER_SHOW[k])
            for k, v in self.COMPETITOR_LABELS.items()
        }

        for c in competitors:
            lat, lon = float(c["lat"]), float(c["lon"])
            if not (self.MAP_BOUNDS["lat_min"] <= lat <= self.MAP_BOUNDS["lat_max"] and self.MAP_BOUNDS["lon_min"] <= lon <= self.MAP_BOUNDS["lon_max"]):
                continue
            layer = category_layers.get(c["category"])
            color = ColorRamp.COMPETITOR_COLORS.get(c["category"], "#57534e")
            if layer is None:
                continue
            if c["category"] == "family_dollar":
              folium.Marker(
                location=[lat, lon],
                popup=f"<b style='color:#1F2937;'>Existing Family Dollar</b><br><span style='color:#374151;'>Brand: {c['brand']}<br>Category: {self.COMPETITOR_LABELS[c['category']]}<br>Typical size: {int(c['typical_sqft']):,} sq ft</span><br><span class='src-note'>Source: OpenStreetMap</span>",
                tooltip=f"Family Dollar existing network: {c['name']}",
                icon=self.family_dollar_icon(),
              ).add_to(layer)
            else:
              # smaller + more transparent than the candidate-site markers, with a thin white
              # ring instead of a saturated border, so these read as context, not the focus
              folium.Marker(
                location=[lat, lon],
                popup=f"<b style='color:#1F2937;'>{c['name']}</b><br><span style='color:#374151;'>Brand: {c['brand']}<br>Category: {self.COMPETITOR_LABELS[c['category']]}<br>Typical size: {int(c['typical_sqft']):,} sq ft</span><br><span class='src-note'>Source: OpenStreetMap</span>",
                tooltip=f"{c['name']} ({c['brand']})",
                icon=self.competitor_dot_icon(color),
              ).add_to(layer)
        for layer in category_layers.values():
            layer.add_to(m)

        # --- Layer: real HUD LIHTC affordable-housing properties (free, off by default) ---
        lihtc_layer = folium.FeatureGroup(name="HUD LIHTC affordable-housing properties (free, off by default)", show=False)
        seen_lihtc = set()
        for p in self.load_csv("lihtc_properties_detail.csv"):
            key = (p["name"], round(float(p["lat"]), 5), round(float(p["lon"]), 5))
            if key in seen_lihtc:
                continue
            seen_lihtc.add(key)
            folium.Marker(
                location=[float(p["lat"]), float(p["lon"])],
                popup=f"<b style='color:#1F2937;'>{p['name']}</b><br><span style='color:#374151;'>{p['units']} units</span><br><span class='src-note'>Source: HUD LIHTC Database</span>",
                tooltip=f"LIHTC: {p['name']} ({p['units']} units)",
                icon=self.competitor_dot_icon("#0f766e"),
            ).add_to(lihtc_layer)
        lihtc_layer.add_to(m)

        # --- Layer: real HUD Multifamily (FHA-insured/assisted) properties (free, off by default) ---
        multifamily_layer = folium.FeatureGroup(name="HUD Multifamily assisted-housing properties (free, off by default)", show=False)
        seen_multifamily = set()
        for p in self.load_csv("hud_multifamily_detail.csv"):
            key = (p["name"], round(float(p["lat"]), 5), round(float(p["lon"]), 5))
            if key in seen_multifamily:
                continue
            seen_multifamily.add(key)
            folium.Marker(
                location=[float(p["lat"]), float(p["lon"])],
                popup=f"<b style='color:#1F2937;'>{p['name']}</b><br><span style='color:#374151;'>{p['assisted_units']} assisted units</span><br><span class='src-note'>Source: HUD Multifamily Properties (FHA-insured/assisted)</span>",
                tooltip=f"HUD Multifamily: {p['name']} ({p['assisted_units']} assisted units)",
                icon=self.competitor_dot_icon("#7c3aed"),
            ).add_to(multifamily_layer)
        multifamily_layer.add_to(m)

        # --- Layer: real federal Qualified Opportunity Zone tracts, finalists only (free, off by default) ---
        opp_zone_layer = folium.FeatureGroup(name="Federal Opportunity Zones, finalist tracts (free, off by default)", show=False)
        opp_zone_rows = self.load_csv("site_opportunity_zones.csv")
        oz_by_hcad = {r["hcad_num"]: r for r in opp_zone_rows}
        for h, s in sites.items():
            r = oz_by_hcad.get(h)
            if not r or r["in_opportunity_zone"] != "True":
                continue
            folium.CircleMarker(
                location=[float(s["lat"]), float(s["lon"])],
                radius=14,
                color="#b45309",
                fill=True,
                fill_color="#fbbf24",
                fill_opacity=0.25,
                weight=2,
                dash_array="4,3",
                tooltip=f"{s['site_label']}: sits in a real federal Qualified Opportunity Zone",
                popup=f"<b style='color:#1F2937;'>Qualified Opportunity Zone</b><br><span style='color:#374151;'>{s['site_label']}</span><br><span class='src-note'>Source: CDFI Fund / Federal_User_Community ArcGIS feature service</span>",
            ).add_to(opp_zone_layer)
        opp_zone_layer.add_to(m)

        # --- Layer: real LEHD daytime workplace population (free, off by default) --------
        daytime_layer = folium.FeatureGroup(name="Daytime workplace population, all Houston block groups (free, off by default)", show=False)
        bg_daytime = self.load_csv("blockgroup_daytime_population.csv")
        job_counts = [float(b["daytime_jobs"]) for b in bg_daytime if float(b["daytime_jobs"]) > 0]
        j_hi = max(job_counts) if job_counts else 1.0
        for b in bg_daytime:
            jobs = float(b["daytime_jobs"])
            if jobs <= 0:
                continue
            t = min(1.0, jobs / j_hi)
            color = ColorRamp.interpolate(t, ColorRamp.SEQUENTIAL_ORANGE)
            folium.CircleMarker(
                location=[float(b["lat"]), float(b["lon"])],
                radius=2 + 8 * t,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.65,
                weight=0.5,
                tooltip=f"{int(jobs):,} real jobs (LEHD block group {b['geoid']})",
                popup=f"<b style='color:#1F2937;'>Daytime workplace population</b><br><span style='color:#374151;'>{int(jobs):,} jobs</span><br><span class='src-note'>Source: Census LEHD LODES (block group {b['geoid']})</span>",
            ).add_to(daytime_layer)
        daytime_layer.add_to(m)

        # --- Layer: real USDA food-access share, finalist tracts (free, off by default) ---
        food_access_layer = folium.FeatureGroup(name="Food access share, finalist tracts (USDA, free, off by default)", show=False)
        tract_by_geoid = {f["properties"]["geoid"]: f for f in tracts["features"]}
        food_access_rows = self.load_csv("site_food_access.csv")
        fa_shares = [float(r["pct_tract_pop_beyond_half_mi_from_food_retailer"]) for r in food_access_rows]
        fa_hi = max(fa_shares) if fa_shares else 1.0
        seen_fa_tracts = set()
        for r in food_access_rows:
            geoid = r["tract_geoid"]
            if geoid in seen_fa_tracts:
                continue
            seen_fa_tracts.add(geoid)
            feat = tract_by_geoid.get(geoid)
            if feat is None:
                continue
            share = float(r["pct_tract_pop_beyond_half_mi_from_food_retailer"])
            t = (share / fa_hi) if fa_hi > 0 else 0.0
            color = ColorRamp.interpolate(t, ColorRamp.SEQUENTIAL_ORANGE)
            folium.GeoJson(
                feat,
                style_function=lambda _f, c=color: {"fillColor": c, "color": "#7a2d0f", "weight": 1, "fillOpacity": 0.35},
                highlight_function=lambda _f: {"weight": 2, "color": "#7a2d0f"},
                tooltip=f"Tract {geoid}: {share:.1f}% of population beyond 0.5mi from a SNAP-authorized food retailer",
                popup=f"<b style='color:#1F2937;'>Tract {geoid}</b><br><span style='color:#374151;'>{share:.1f}% of tract population beyond 0.5mi from a SNAP-authorized food retailer</span><br><span class='src-note'>Source: USDA ERS Food Access Research Atlas (SRAM)</span>",
            ).add_to(food_access_layer)
        food_access_layer.add_to(m)

        # --- Layer: real Overture-sourced competitors OSM missed (free, off by default) ---
        overture_layer = folium.FeatureGroup(name="Competitors found by Overture, missed by OSM (free, off by default)", show=False)
        seen_overture = set()
        for p in self.load_csv("overture_new_competitors_detail.csv"):
            key = (p["name"], round(float(p["lat"]), 5), round(float(p["lon"]), 5))
            if key in seen_overture:
                continue
            seen_overture.add(key)
            folium.Marker(
                location=[float(p["lat"]), float(p["lon"])],
                popup=f"<b style='color:#1F2937;'>{p['name']}</b><br><span style='color:#374151;'>Brand: {p['brand']}<br>Found by Overture Maps, not present in the OSM competitor pull</span><br><span class='src-note'>Source: Overture Maps Places</span>",
                tooltip=f"{p['name']} ({p['brand']}) -- Overture-only find",
                icon=self.competitor_dot_icon("#b45309"),
            ).add_to(overture_layer)
        overture_layer.add_to(m)

        # --- Layer: 10 opportunity clusters searched (context) -----------------------
        clusters = self.load_csv("clusters.csv")
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
            rank_color = ColorRamp.interpolate((int(row["raw_score_rank"]) - 1) / max(n - 1, 1), ColorRamp.STATUS_RAMP)
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
          <div class="exec-metric"><span>Road Class</span><span class="exec-val">{micro.get('road_functional_class', 'n/a')}</span></div>
          <div class="exec-metric"><span>Bus Stops (500 ft)</span><span class="exec-val">{micro.get('bus_stops_within_500ft', 'n/a')}</span></div>
          <div class="exec-metric"><span>Co-Tenants (0.3 mi)</span><span class="exec-val">{micro.get('co_tenant_count_0_3mi', 'n/a')}</span></div>
          <div class="exec-metric"><span>Nearby Co-Tenants</span><span class="exec-val" style="text-align:right; font-weight:600;">{micro['nearby_co_tenants']}</span></div>
          <div class="exec-metric"><span>Nearest Transit Stop</span><span class="exec-val">{micro['nearest_transit_stop']}</span></div>
          <div class="exec-metric"><span>Composite Score</span><span class="exec-val">{row['total_score']} / 100</span></div>
          {aadt_note}{freeway_note}{flood_note}{canib_note}
          <div class="src-note">Sources: HCAD parcels &middot; TxDOT AADT (Nominatim-verified) &middot; FEMA NFHL &middot; OSM &middot; OSRM drive times &middot; Huff gravity model. Full detail in the Analysis Dashboard.</div>
        </div>
        """
            icon = self.rank_badge_icon(int(row["raw_score_rank"]), rank_color, is_winner)
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

        opportunity_ramp_css = "linear-gradient(90deg," + ",".join(ColorRamp.SEQUENTIAL_BLUE) + ")"
        m.get_root().html.add_child(folium.Element(self.build_legend_html(opportunity_ramp_css)))
        m.get_root().html.add_child(folium.Element(self.build_dashboard_html(
          scorecard,
          self.load_csv("cannibalization.csv"),
          ci_rows,
          self.load_csv("microsite_details.csv"),
          self.load_csv("sensitivity_analysis.csv"),
          sites,
          trade,
          cannibalization,
          microsite,
          isochrone,
          houston_tracts,
          county_tracts,
          extended_demo,
          rigor_rows,
          crime_map,
        )))

        folium.LayerControl(collapsed=False).add_to(m)
        m.get_root().script.add_child(folium.Element(self.build_fema_frontend_loader_script(m.get_name(), flood_layer.get_name())))
        m.get_root().script.add_child(folium.Element(self.build_dynamic_legend_script(m.get_name())))
        plugins.Fullscreen(position="topright").add_to(m)
        m.fit_bounds([[29.60, -95.65], [29.98, -95.20]])

        m.save(output_path)
        return output_path

if __name__ == "__main__":
    GenerateMapStage().run()
