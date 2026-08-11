"""Step 12: Build the executive-facing interactive web map from the real
pipeline outputs -- every layer traces back to a data/processed/*.csv or
*.geojson file produced by scripts 01-11. Nothing in this map is invented.

Output: index.html (repo root, for GitHub Pages)
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import folium
from folium import plugins

from lib import PROCESSED, ROOT

MAP_BOUNDS = {"lat_min": 29.60, "lat_max": 29.73, "lon_min": -95.42, "lon_max": -95.28}


def in_bounds(lat: float, lon: float, pad: float = 0.02) -> bool:
    return (
        MAP_BOUNDS["lat_min"] - pad <= lat <= MAP_BOUNDS["lat_max"] + pad
        and MAP_BOUNDS["lon_min"] - pad <= lon <= MAP_BOUNDS["lon_max"] + pad
    )


def load_csv(name: str) -> list[dict]:
    with open(PROCESSED / name, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_json(name: str) -> dict:
    return json.loads((PROCESSED / name).read_text(encoding="utf-8"))


POPUP_CSS = """
<style>
  .exec-card { font-family: 'Segoe UI', Arial, sans-serif; width: 280px; padding: 6px 8px; }
  .exec-title { font-size: 14px; font-weight: 700; color: #1E3A8A; border-bottom: 2px solid #D97706; padding-bottom: 4px; margin-bottom: 6px; }
  .exec-metric { font-size: 12px; margin: 3px 0; color: #1E293B; display: flex; justify-content: space-between; }
  .exec-val { font-weight: 700; color: #0D9488; }
  .winner-tag { background-color: #10B981; color: white; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: 700; letter-spacing: .03em; }
  .rank-tag { background-color: #64748B; color: white; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: 700; }
  .comp-tag { background-color: #DC2626; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; }
  .anchor-tag { background-color: #2563EB; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 700; }
  .src-note { font-size: 10px; color: #64748B; margin-top: 6px; border-top: 1px solid #E2E8F0; padding-top: 4px; }
</style>
"""

TITLE_HTML = """
<div style="position: fixed; top: 12px; left: 60px; z-index: 9999; background: white;
            padding: 10px 16px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,.25);
            font-family: 'Segoe UI', Arial, sans-serif; max-width: 380px;">
  <div style="font-size: 15px; font-weight: 700; color: #1E3A8A;">Family Dollar &mdash; Houston Site Selection</div>
  <div style="font-size: 12px; color: #475569; margin-top: 2px;">Sunnyside / South Union submarket &middot; recommended site: <b>9104 Cullen Blvd</b></div>
</div>
"""

LEGEND_HTML = """
<div style="position: fixed; bottom: 24px; left: 12px; z-index: 9999; background: white;
            padding: 10px 14px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,.25);
            font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; line-height: 1.7; max-width: 250px;">
  <div style="font-weight:700; margin-bottom:4px;">Legend</div>
  <div><span style="color:#10B981; font-weight:700;">&#9733;</span> Recommended site (Site B)</div>
  <div><span style="color:#F59E0B; font-weight:700;">&#9679;</span> Other candidate sites</div>
  <div><span style="color:#DC2626; font-weight:700;">&#9679;</span> Existing dollar-store competitor</div>
  <div><span style="color:#2563EB; font-weight:700;">&#9679;</span> Grocery / big-box anchor</div>
  <div><span style="display:inline-block;width:10px;height:10px;background:#0D9488;opacity:.35;border:1px solid #0D9488;"></span> 5-min drive trade area</div>
  <div><span style="display:inline-block;width:10px;height:10px;background:#0D9488;opacity:.12;border:1px dashed #0D9488;"></span> 10-min drive trade area</div>
  <div style="margin-top:4px; color:#64748B;">Shading = tract opportunity (gap) score</div>
</div>
"""


def build_map() -> Path:
    output_path = ROOT / "index.html"

    scorecard = load_csv("scorecard.csv")
    sites = {r["hcad_num"]: r for r in load_csv("sites_enriched.csv")}
    trade = {r["hcad_num"]: r for r in load_csv("site_trade_areas.csv")}
    competitors = load_csv("competitors.csv")
    tracts = load_json("submarket_tracts.geojson")
    isochrone = load_json("isochrone_winner.json")

    winner = scorecard[0]
    center = [float(sites[winner["hcad_num"]]["lat"]), float(sites[winner["hcad_num"]]["lon"])]

    m = folium.Map(location=center, zoom_start=13, tiles=None, control_scale=True)
    folium.TileLayer(tiles="CartoDB positron", name="Base map", control=True).add_to(m)
    m.get_root().header.add_child(folium.Element(POPUP_CSS))
    m.get_root().html.add_child(folium.Element(TITLE_HTML))
    m.get_root().html.add_child(folium.Element(LEGEND_HTML))

    # --- Layer 1: submarket opportunity (gap score) choropleth -----------------
    gap_layer = folium.FeatureGroup(name="Submarket opportunity score (Census tracts)", show=True)
    scores = [float(f["properties"]["gap_score"]) for f in tracts["features"] if f["properties"]["gap_score"]]
    lo, hi = min(scores), max(scores)

    def color_for(score: float) -> str:
        t = (score - lo) / (hi - lo) if hi > lo else 0
        # light gold -> deep red ramp (higher gap score = more underserved = darker)
        r = 254
        g = int(237 - t * 170)
        b = int(160 - t * 150)
        return f"#{r:02x}{max(g,0):02x}{max(b,0):02x}"

    for f in tracts["features"]:
        p = f["properties"]
        if not p.get("gap_score"):
            continue
        score = float(p["gap_score"])
        pop = float(p["population"]) if p.get("population") else 0
        mhi = float(p["median_hh_income"]) if p.get("median_hh_income") else None
        pov = float(p["poverty_rate"]) * 100 if p.get("poverty_rate") else None
        tooltip = f"{p['name']}: gap score {score:.0f}"
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
            style_function=lambda _f, c=color_for(score): {"fillColor": c, "color": "#94a3b8", "weight": 0.6, "fillOpacity": 0.55},
            highlight_function=lambda _f: {"weight": 2, "color": "#1E3A8A"},
            tooltip=tooltip,
            popup=folium.Popup(popup, max_width=300),
        ).add_to(gap_layer)
    gap_layer.add_to(m)

    # --- Layer 2: competitors & anchors ----------------------------------------
    comp_layer = folium.FeatureGroup(name="Existing dollar-store competitors (OSM)", show=True)
    anchor_layer = folium.FeatureGroup(name="Grocery / big-box anchors (OSM)", show=True)
    for c in competitors:
        lat, lon = float(c["lat"]), float(c["lon"])
        if not in_bounds(lat, lon):
            continue
        if c["category"] == "dollar_store":
            folium.CircleMarker(
                location=[lat, lon], radius=6, color="#DC2626", fill=True, fill_color="#DC2626", fill_opacity=0.9,
                weight=1, tooltip=f"{c['name']} (existing competitor)",
                popup=f"<b>{c['name']}</b><br>Category: Existing dollar-store<br><span class='src-note'>Source: OpenStreetMap</span>",
            ).add_to(comp_layer)
        else:
            folium.CircleMarker(
                location=[lat, lon], radius=5, color="#2563EB", fill=True, fill_color="#2563EB", fill_opacity=0.85,
                weight=1, tooltip=f"{c['name']} (anchor)",
                popup=f"<b>{c['name']}</b><br>Category: Grocery/big-box anchor<br><span class='src-note'>Source: OpenStreetMap</span>",
            ).add_to(anchor_layer)
    comp_layer.add_to(m)
    anchor_layer.add_to(m)

    # --- Layer 3: candidate sites -----------------------------------------------
    site_layer = folium.FeatureGroup(name="Candidate sites", show=True)
    for i, row in enumerate(scorecard, start=1):
        h = row["hcad_num"]
        s = sites[h]
        t = trade[h]
        is_winner = i == 1
        rank_html = "<span class='winner-tag'>RECOMMENDED</span>" if is_winner else f"<span class='rank-tag'>RANK #{i}</span>"
        popup = f"""
        <div class="exec-card">
          {rank_html}
          <div class="exec-title" style="margin-top:6px;">{row['site_label'].split(' - ',1)[1]}</div>
          <div class="exec-metric"><span>Address</span><span class="exec-val">{s['address']}, Houston, TX</span></div>
          <div class="exec-metric"><span>Parcel (HCAD)</span><span class="exec-val">{s['acreage']} ac</span></div>
          <div class="exec-metric"><span>Site Type</span><span class="exec-val">{s['site_type']}</span></div>
          <div class="exec-metric"><span>Land Value (HCAD)</span><span class="exec-val">${float(s['land_value']):,.0f}</span></div>
          <div class="exec-metric"><span>AADT Traffic (TxDOT)</span><span class="exec-val">{int(float(s['aadt'])):,} vpd</span></div>
          <div class="exec-metric"><span>5-Min Drive Population</span><span class="exec-val">{int(float(t['pop_5min_drive'])):,}</span></div>
          <div class="exec-metric"><span>10-Min Drive Population</span><span class="exec-val">{int(float(t['pop_10min_drive'])):,}</span></div>
          <div class="exec-metric"><span>Nearest Competitor</span><span class="exec-val">{s['nearest_dollar_store_mi']} mi</span></div>
          <div class="exec-metric"><span>FEMA Flood Zone</span><span class="exec-val">{s['flood_zone']}</span></div>
          <div class="exec-metric"><span>Composite Score</span><span class="exec-val">{row['total_score']} / 100</span></div>
          <div class="src-note">Sources: HCAD parcels &middot; TxDOT AADT &middot; FEMA NFHL &middot; OSM &middot; OSRM drive times</div>
        </div>
        """
        if is_winner:
            icon = folium.Icon(color="green", icon="star", prefix="fa")
        else:
            icon = folium.Icon(color="orange", icon="shopping-cart", prefix="fa")
        folium.Marker(
            location=[float(s["lat"]), float(s["lon"])],
            popup=folium.Popup(popup, max_width=320),
            tooltip=("RECOMMENDED: " if is_winner else f"#{i}: ") + row["site_label"].split(" - ", 1)[1],
            icon=icon,
        ).add_to(site_layer)
    site_layer.add_to(m)

    # --- Layer 4: isochrones for the winning site --------------------------------
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

    folium.LayerControl(collapsed=False).add_to(m)
    plugins.Fullscreen(position="topright").add_to(m)

    m.save(output_path)
    return output_path


if __name__ == "__main__":
    path = build_map()
    print(f"Web map written to {path}")
