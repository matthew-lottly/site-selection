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

from lib import PROCESSED, ROOT, SEQUENTIAL_BLUE, STATUS_RAMP, ramp_color

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
  .exec-metric { font-size: 12px; margin: 3px 0; color: #1E293B; display: flex; justify-content: space-between; gap: 8px; }
  .exec-val { font-weight: 700; color: #0D9488; text-align: right; }
  .winner-tag { background-color: #0ca30c; color: white; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: 700; letter-spacing: .03em; }
  .rank-tag { color: white; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: 700; }
  .src-note { font-size: 10px; color: #64748B; margin-top: 6px; border-top: 1px solid #E2E8F0; padding-top: 4px; }
  .warn-note { font-size: 11px; color: #92400E; background: #FEF3C7; padding: 4px 6px; border-radius: 4px; margin-top: 4px; }
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
    return f"""
<div style="position: fixed; bottom: 20px; left: 12px; z-index: 9999; background: white;
            padding: 14px 16px; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,.28);
            font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; max-width: 268px;">
  <div style="font-weight:700; font-size:13px; color:#1E3A8A; margin-bottom:10px;">Legend</div>

  <div style="font-weight:700; color:#334155; font-size:11px; text-transform:uppercase; letter-spacing:.04em; margin-bottom:6px;">Candidate sites (by score)</div>
  <div style="height:10px; border-radius:5px; margin-bottom:3px; background:{rank_ramp_css};"></div>
  <div style="display:flex; justify-content:space-between; color:#64748B; font-size:10.5px; margin-bottom:10px;">
    <span>Best (Rank 1)</span><span>Worst (Rank 20)</span>
  </div>
  <div style="display:flex; align-items:center; gap:6px; margin-bottom:10px;">
    <span style="color:#0ca30c; font-size:16px; line-height:1;">&#9733;</span>
    <span style="color:#334155;">Recommended site</span>
  </div>

  <div style="border-top:1px solid #E2E8F0; margin:10px 0;"></div>
  <div style="font-weight:700; color:#334155; font-size:11px; text-transform:uppercase; letter-spacing:.04em; margin-bottom:6px;">Competitors</div>
  <div style="display:flex; align-items:center; gap:7px; margin-bottom:4px;"><span style="width:10px; height:10px; border-radius:50%; background:#DC2626; display:inline-block;"></span><span style="color:#334155;">Direct dollar-store</span></div>
  <div style="display:flex; align-items:center; gap:7px; margin-bottom:4px;"><span style="width:10px; height:10px; border-radius:50%; background:#7C3AED; display:inline-block;"></span><span style="color:#334155;">Off-price / general merch.</span></div>
  <div style="display:flex; align-items:center; gap:7px; margin-bottom:10px;"><span style="width:10px; height:10px; border-radius:50%; background:#2563EB; display:inline-block;"></span><span style="color:#334155;">Grocery / big-box anchor</span></div>

  <div style="border-top:1px solid #E2E8F0; margin:10px 0;"></div>
  <div style="font-weight:700; color:#334155; font-size:11px; text-transform:uppercase; letter-spacing:.04em; margin-bottom:6px;">Trade area (recommended site)</div>
  <div style="display:flex; align-items:center; gap:7px; margin-bottom:4px;"><span style="width:14px; height:10px; background:#0D9488; opacity:.35; border:1px solid #0D9488; display:inline-block;"></span><span style="color:#334155;">5-min drive (OSRM)</span></div>
  <div style="display:flex; align-items:center; gap:7px; margin-bottom:10px;"><span style="width:14px; height:10px; background:#0D9488; opacity:.12; border:1px dashed #0D9488; display:inline-block;"></span><span style="color:#334155;">10-min drive (OSRM)</span></div>

  <div style="border-top:1px solid #E2E8F0; margin:10px 0;"></div>
  <div style="font-weight:700; color:#334155; font-size:11px; text-transform:uppercase; letter-spacing:.04em; margin-bottom:6px;">Opportunity score</div>
  <div style="height:10px; border-radius:5px; margin-bottom:3px; background:linear-gradient(90deg,{','.join(SEQUENTIAL_BLUE)});"></div>
  <div style="display:flex; justify-content:space-between; color:#64748B; font-size:10.5px;">
    <span>Lower (served)</span><span>Higher (underserved)</span>
  </div>
</div>
"""


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
        color = ramp_color(t, SEQUENTIAL_BLUE)
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
            style_function=lambda _f, c=color: {"fillColor": c, "color": "#94a3b8", "weight": 0.4, "fillOpacity": 0.6},
            highlight_function=lambda _f: {"weight": 2, "color": "#1E3A8A"},
            tooltip=f"{p['name']}: opportunity score {score:.0f}",
            popup=folium.Popup(popup, max_width=300),
        ).add_to(gap_layer)
    gap_layer.add_to(m)

    # --- Layer: competitors, split by tier ---------------------------------------
    dollar_layer = folium.FeatureGroup(name="Direct dollar-store competitors (OSM)", show=True)
    offprice_layer = folium.FeatureGroup(name="Off-price / general merchandise (OSM)", show=False)
    anchor_layer = folium.FeatureGroup(name="Grocery / big-box anchors (OSM)", show=False)
    layer_by_category = {"dollar_store": (dollar_layer, "#DC2626"), "offprice": (offprice_layer, "#7C3AED"), "grocery_anchor": (anchor_layer, "#2563EB")}

    for c in competitors:
        lat, lon = float(c["lat"]), float(c["lon"])
        if not (MAP_BOUNDS["lat_min"] <= lat <= MAP_BOUNDS["lat_max"] and MAP_BOUNDS["lon_min"] <= lon <= MAP_BOUNDS["lon_max"]):
            continue
        layer, color = layer_by_category.get(c["category"], (anchor_layer, "#2563EB"))
        folium.CircleMarker(
            location=[lat, lon], radius=5, color=color, fill=True, fill_color=color, fill_opacity=0.85, weight=1,
            tooltip=f"{c['name']} ({c['brand']})",
            popup=f"<b>{c['name']}</b><br>Brand: {c['brand']}<br>Typical size: {int(c['typical_sqft']):,} sq ft<br><span class='src-note'>Source: OpenStreetMap</span>",
        ).add_to(layer)
    dollar_layer.add_to(m)
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
        if is_winner:
            icon = folium.Icon(color="green", icon="star", prefix="fa")
        else:
            icon = plugins.BeautifyIcon(
                icon="shopping-cart", icon_shape="marker", background_color=rank_color,
                border_color="#334155", text_color="white", inner_icon_style="font-size:12px;padding-top:2px;",
            )
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
