"""Step 22 (supersedes scripts/12_generate_map.py): build the executive-facing
interactive web map from the citywide pipeline outputs. Every layer traces
back to a data/processed/*.csv or *.geojson file produced by scripts 01-21.

Adds, per user feedback on the first citywide draft:
  - candidate-site symbology on a validated best->worst color ramp (rank, not
    just a single "winner" color)
  - a basemap switcher (multiple free/open tile providers)
  - a full City of Houston choropleth + boundary, not one neighborhood
  - a reorganized, better-spaced legend
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import folium
from folium import plugins

from lib import PROCESSED, ROOT, SEQUENTIAL_ORANGE, STATUS_RAMP, ramp_color

MAP_BOUNDS = {"lat_min": 29.52, "lat_max": 30.11, "lon_min": -95.79, "lon_max": -95.01}


def load_csv(name: str) -> list[dict]:
    with open(PROCESSED / name, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_json(name: str) -> dict:
    return json.loads((PROCESSED / name).read_text(encoding="utf-8"))


POPUP_CSS = """
<style>
  .exec-card { font-family: 'Segoe UI', Arial, sans-serif; width: 290px; padding: 6px 8px; }
  .exec-title { font-size: 14px; font-weight: 700; color: #1E3A8A; border-bottom: 2px solid #D97706; padding-bottom: 4px; margin-bottom: 6px; }
  .exec-metric { font-size: 12px; margin: 4px 0; color: #1F2937; font-weight: 700; display: flex; justify-content: space-between; gap: 8px; }
  .exec-metric span:first-child { color: #374151; font-weight: 600; }
  .exec-val { font-weight: 700; color: #1F2937; text-align: right; }
  .winner-tag { background-color: #0ca30c; color: white; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: 700; letter-spacing: .03em; }
  .rank-tag { color: white; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: 700; }
  .src-note { font-size: 10px; color: #64748B; margin-top: 6px; border-top: 1px solid #E2E8F0; padding-top: 4px; font-weight: 400; }
  .warn-note { font-size: 11px; color: #92400E; background: #FEF3C7; padding: 4px 6px; border-radius: 4px; margin-top: 4px; font-weight: 600; }
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
    return f"""
<div style="position: fixed; bottom: 20px; left: 12px; z-index: 9999; background: white;
            padding: 14px 16px; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,.28);
            font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; max-width: 272px;">
  <div style="font-weight:700; font-size:13px; color:#1E3A8A; margin-bottom:12px;">Legend</div>

  <div style="{section_head}">Candidate sites (by score)</div>
  <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
    <div style="width:22px; height:22px; border-radius:50%; background:#0ca30c; border:2px solid #fff; box-shadow:0 1px 3px rgba(0,0,0,.35); flex-shrink:0; display:flex; align-items:center; justify-content:center; color:#fff; font-size:12px;">&#9733;</div>
    <span style="{row_text}">Recommended site (Rank 1)</span>
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
  <div style="display:flex; align-items:center; gap:8px; margin-bottom:5px;"><span style="width:11px; height:11px; border-radius:50%; background:#DC2626; border:1.5px solid #fff; box-shadow:0 0 0 .5px #DC2626; display:inline-block; flex-shrink:0;"></span><span style="{row_text}">Family Dollar (existing)</span></div>
  <div style="display:flex; align-items:center; gap:8px; margin-bottom:5px;"><span style="width:11px; height:11px; border-radius:50%; background:#DB2777; border:1.5px solid #fff; box-shadow:0 0 0 .5px #DB2777; display:inline-block; flex-shrink:0;"></span><span style="{row_text}">Other dollar stores</span></div>
  <div style="display:flex; align-items:center; gap:8px; margin-bottom:5px;"><span style="width:11px; height:11px; border-radius:50%; background:#7C3AED; border:1.5px solid #fff; box-shadow:0 0 0 .5px #7C3AED; display:inline-block; flex-shrink:0;"></span><span style="{row_text}">Off-price / general merch.</span></div>
  <div style="display:flex; align-items:center; gap:8px; margin-bottom:12px;"><span style="width:11px; height:11px; border-radius:50%; background:#2563EB; border:1.5px solid #fff; box-shadow:0 0 0 .5px #2563EB; display:inline-block; flex-shrink:0;"></span><span style="{row_text}">Grocery / big-box anchor</span></div>

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


def build_map() -> Path:
    output_path = ROOT / "index.html"

    scorecard = load_csv("scorecard.csv")
    sites = {r["hcad_num"]: r for r in load_csv("sites_enriched.csv")}
    trade = {r["hcad_num"]: r for r in load_csv("site_trade_areas.csv")}
    competitors = load_csv("competitors.csv")
    tracts = load_json("houston_tracts.geojson")
    boundary = load_json("houston_boundary.geojson")
    isochrone = load_json("isochrone_winner.json")

    winner = scorecard[0]
    center = [float(sites[winner["hcad_num"]]["lat"]), float(sites[winner["hcad_num"]]["lon"])]

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
        # let low-opportunity tracts recede and high-opportunity tracts stand out,
        # instead of one flat fill weight across all 643 polygons
        fill_opacity = 0.12 + 0.5 * t
        pop = float(p["population"]) if p.get("population") else 0
        mhi = float(p["median_hh_income"]) if p.get("median_hh_income") else None
        pov = float(p["poverty_rate"]) * 100 if p.get("poverty_rate") else None
        popup = (
            f"<div class='exec-card'><div class='exec-title'>{p['name']}</div>"
            f"<div class='exec-metric'><span>Population</span><span class='exec-val'>{pop:,.0f}</span></div>"
            f"<div class='exec-metric'><span>Median HH Income</span><span class='exec-val'>{'$'+format(mhi, ',.0f') if mhi else 'n/a'}</span></div>"
            f"<div class='exec-metric'><span>Poverty Rate</span><span class='exec-val'>{pov:.1f}%</span></div>"
            f"<div class='exec-metric'><span>Nearest Dollar Store</span><span class='exec-val'>{p['nearest_dollar_store_mi']} mi</span></div>"
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

    # --- Layer: competitors, split by tier -- Family Dollar gets its own layer -----
    # since this analysis is FOR Family Dollar: existing FD locations (cannibalization
    # check) are the single most important competitor fact on the map, so they get
    # their own toggle and color rather than being buried in "dollar stores" broadly.
    fd_layer = folium.FeatureGroup(name="Family Dollar (existing)", show=True)
    other_dollar_layer = folium.FeatureGroup(name="Other dollar stores (DG, Dollar Tree, etc.)", show=True)
    offprice_layer = folium.FeatureGroup(name="Off-price / general merchandise (OSM)", show=False)
    anchor_layer = folium.FeatureGroup(name="Grocery / big-box anchors (OSM)", show=False)

    COMPETITOR_STYLE = {
        "family_dollar": (fd_layer, "#DC2626"),
        "other_dollar": (other_dollar_layer, "#DB2777"),
        "offprice": (offprice_layer, "#7C3AED"),
        "grocery_anchor": (anchor_layer, "#2563EB"),
    }

    for c in competitors:
        lat, lon = float(c["lat"]), float(c["lon"])
        if not (MAP_BOUNDS["lat_min"] <= lat <= MAP_BOUNDS["lat_max"] and MAP_BOUNDS["lon_min"] <= lon <= MAP_BOUNDS["lon_max"]):
            continue
        if c["category"] == "dollar_store":
            key = "family_dollar" if c["brand"] == "Family Dollar" else "other_dollar"
        else:
            key = c["category"]
        layer, color = COMPETITOR_STYLE.get(key, (anchor_layer, "#2563EB"))
        # smaller + more transparent than the candidate-site markers, with a thin white
        # ring instead of a saturated border, so these read as context, not the focus
        folium.CircleMarker(
            location=[lat, lon], radius=4.5, color="#ffffff", fill=True, fill_color=color,
            fill_opacity=0.62, weight=0.75, opacity=0.9,
            tooltip=f"{c['name']} ({c['brand']})",
            popup=f"<b style='color:#1F2937;'>{c['name']}</b><br><span style='color:#374151;'>Brand: {c['brand']}<br>Typical size: {int(c['typical_sqft']):,} sq ft</span><br><span class='src-note'>Source: OpenStreetMap</span>",
        ).add_to(layer)
    fd_layer.add_to(m)
    other_dollar_layer.add_to(m)
    offprice_layer.add_to(m)
    anchor_layer.add_to(m)

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
            tooltip=f"{c['neighborhood']} opportunity cluster (rank {c['cluster_id']}, gap score {round(float(c['score'])):,})",
        ).add_to(cluster_layer)
    cluster_layer.add_to(m)

    # --- Layer: 20 candidate sites, rank color ramp -------------------------------
    site_layer = folium.FeatureGroup(name="Candidate sites (20, all Houston)", show=True)
    n = len(scorecard)
    for i, row in enumerate(scorecard, start=1):
        h = row["hcad_num"]
        s = sites[h]
        t = trade[h]
        is_winner = i == 1
        rank_color = ramp_color((i - 1) / max(n - 1, 1), STATUS_RAMP)
        rank_html = "<span class='winner-tag'>RECOMMENDED &middot; RANK 1</span>" if is_winner else f"<span class='rank-tag' style='background:{rank_color};'>RANK {i} / {n}</span>"
        freeway_note = (
            "<div class='warn-note'>Nearest labeled TxDOT station sits on a limited-access freeway with no arterial "
            "count nearby; traffic score uses a conservative fallback, not this freeway figure.</div>"
            if s["aadt_on_freeway"] == "True" else ""
        )
        flood_note = "<div class='warn-note'>Falls inside a FEMA Special Flood Hazard Area.</div>" if s["in_sfha"] == "T" else ""
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
          <div class="exec-metric"><span>Huff Capture (vs. dollar stores)</span><span class="exec-val">{t['huff_capture_pct']}%</span></div>
          <div class="exec-metric"><span>Nearest Competitor</span><span class="exec-val">{s['nearest_dollar_store_mi']} mi ({s['nearest_dollar_store']})</span></div>
          <div class="exec-metric"><span>FEMA Flood Zone</span><span class="exec-val">{s['flood_zone']}</span></div>
          <div class="exec-metric"><span>Composite Score</span><span class="exec-val">{row['total_score']} / 100</span></div>
          {freeway_note}{flood_note}
          <div class="src-note">Sources: HCAD parcels &middot; TxDOT AADT (Nominatim-verified) &middot; FEMA NFHL &middot; OSM &middot; OSRM drive times &middot; Huff gravity model</div>
        </div>
        """
        icon = rank_badge_icon(i, rank_color, is_winner)
        folium.Marker(
            location=[float(s["lat"]), float(s["lon"])],
            popup=folium.Popup(popup, max_width=330),
            tooltip=("RECOMMENDED: " if is_winner else f"#{i}: ") + f"{s['neighborhood']} - {s['address']}",
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

    folium.LayerControl(collapsed=False).add_to(m)
    plugins.Fullscreen(position="topright").add_to(m)
    m.fit_bounds([[29.60, -95.65], [29.98, -95.20]])

    m.save(output_path)
    return output_path


if __name__ == "__main__":
    path = build_map()
    print(f"Web map written to {path}")
