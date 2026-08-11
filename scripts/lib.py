"""Shared helpers for the Houston Family Dollar site-selection pipeline.

Every function in this module talks to a real, public, key-free data source:

- TIGERweb (Census Bureau)      -- tract / block group boundaries
- Census Reporter API           -- ACS 5-year demographic estimates
- Overpass API (OpenStreetMap)  -- competitor & anchor store locations
- HCAD ArcGIS REST              -- Harris County Appraisal District parcels
- FEMA NFHL ArcGIS REST         -- flood zone identify
- TxDOT AADT FeatureServer      -- annual average daily traffic counts
- OSRM demo router              -- real street-network drive times

No API keys are required for any of these endpoints.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RAW.mkdir(parents=True, exist_ok=True)
PROCESSED.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "curl/8.7.1", "Accept": "*/*"}

TIGERWEB = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer"
CENSUS_REPORTER = "https://api.censusreporter.org/1.0/data/show/latest"
OVERPASS = "https://overpass-api.de/api/interpreter"
HCAD_PARCELS = "https://www.gis.hctx.net/arcgis/rest/services/HCAD/Parcels/MapServer/0/query"
FEMA_FLOOD = "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"
TXDOT_AADT = "https://services.arcgis.com/KTcxiTD9dsQw4r7Z/arcgis/rest/services/TxDOT_AADT_Annuals_(Public_View)/FeatureServer/0/query"
OSRM = "https://router.project-osrm.org"

HARRIS_STATE_FIPS = "48"
HARRIS_COUNTY_FIPS = "201"


def cached_get(url: str, params: dict, cache_name: str, verify: bool = True, timeout: int = 30) -> dict:
    """GET with disk caching so repeated pipeline runs don't hammer public APIs."""
    cache_path = RAW / f"{cache_name}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text(encoding="utf-8"))

    resp = requests.get(url, params=params, headers=HEADERS, timeout=timeout, verify=verify)
    resp.raise_for_status()
    data = resp.json()
    cache_path.write_text(json.dumps(data), encoding="utf-8")
    time.sleep(0.2)
    return data


# Validated palettes (dataviz skill, references/palette.md)
SEQUENTIAL_BLUE = [  # magnitude ramp, light->dark: for the tract opportunity-score choropleth
    "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b",
]
SEQUENTIAL_ORANGE = [  # magnitude ramp, light->dark: alternate choropleth hue (categorical slot 2)
    "#fde3d3", "#fbc9a3", "#f5a56a", "#eb6834", "#c94f20", "#a13d16", "#7a2d0f",
]
STATUS_RAMP = [  # ordered good->critical: for "best to worst ranked" site symbology
    "#0ca30c", "#fab219", "#ec835a", "#d03b3b",
]
# Competitor-tier colors: deliberately all cool hues (blue/violet/magenta/aqua),
# never green/yellow/orange/red, so they never get confused with the warm
# STATUS_RAMP (candidate-site rank) or SEQUENTIAL_ORANGE (choropleth) markers
# sharing the same map. Validated distinct via the dataviz skill's
# validate_palette.js (light mode, all-pairs): PASS on lightness/chroma/normal-
# vision floors, WARN (not FAIL) on CVD separation -- acceptable per the skill's
# own rule because every one of these colors also carries a text legend/tooltip
# label (the required secondary encoding for a 6-8 ΔE pair).
COMPETITOR_COLORS = {
    "family_dollar": "#2a78d6",    # blue -- own network, not a competitor
    "arch_rival": "#e87ba4",       # magenta -- the real competitive threat
    "sister_banner": "#4a3aa7",    # violet -- same parent company, different format
    "value_grocery": "#1baf7a",    # aqua -- extreme-value grocery competition
    "big_box_anchor": "#57534e",   # muted stone -- lowest priority, context only
}


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(rgb: tuple[float, float, float]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, round(c))) for c in rgb))


def ramp_color(t: float, stops: list[str]) -> str:
    """t in [0,1] -> interpolated hex color across an ordered list of hex stops."""
    t = max(0.0, min(1.0, t))
    n = len(stops) - 1
    pos = t * n
    i = min(int(pos), n - 1)
    frac = pos - i
    c0, c1 = _hex_to_rgb(stops[i]), _hex_to_rgb(stops[i + 1])
    return _rgb_to_hex(tuple(c0[k] + (c1[k] - c0[k]) * frac for k in range(3)))


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def ring_bbox(ring: list) -> tuple[float, float, float, float]:
    lons = [p[0] for p in ring]
    lats = [p[1] for p in ring]
    return min(lons), min(lats), max(lons), max(lats)


def point_in_rings_fast(lat: float, lon: float, rings: list, bboxes: list) -> bool:
    """Ray-casting point-in-polygon with a per-ring bbox short-circuit --
    needed for Houston's real city boundary (100 rings, ~70,800 vertices)."""
    inside = False
    for ring, (minx, miny, maxx, maxy) in zip(rings, bboxes):
        if not (minx <= lon <= maxx and miny <= lat <= maxy):
            continue
        n = len(ring)
        j = n - 1
        ring_inside = False
        for i in range(n):
            xi, yi = ring[i][0], ring[i][1]
            xj, yj = ring[j][0], ring[j][1]
            if ((yi > lat) != (yj > lat)) and (lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-15) + xi):
                ring_inside = not ring_inside
            j = i
        if ring_inside:
            inside = not inside
    return inside


def simplify_ring(points: list[list[float]], tolerance: float) -> list[list[float]]:
    """Douglas-Peucker line simplification for a single ring of [lon, lat] points.
    Used only to shrink display-map file size; source data is untouched."""
    if len(points) <= 4:
        return points

    def perpendicular_distance(pt, start, end):
        if start == end:
            return math.hypot(pt[0] - start[0], pt[1] - start[1])
        x, y = pt
        x1, y1 = start
        x2, y2 = end
        num = abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1)
        den = math.hypot(y2 - y1, x2 - x1)
        return num / den if den else 0.0

    def rdp(pts):
        if len(pts) <= 2:
            return pts
        start, end = pts[0], pts[-1]
        max_dist, max_idx = 0.0, 0
        for i in range(1, len(pts) - 1):
            d = perpendicular_distance(pts[i], start, end)
            if d > max_dist:
                max_dist, max_idx = d, i
        if max_dist > tolerance:
            left = rdp(pts[: max_idx + 1])
            right = rdp(pts[max_idx:])
            return left[:-1] + right
        return [start, end]

    simplified = rdp(points)
    if simplified[0] != simplified[-1]:
        simplified.append(simplified[0])
    return simplified if len(simplified) >= 4 else points


def point_in_polygon(lat: float, lon: float, rings: list[list[list[float]]]) -> bool:
    """Ray-casting point-in-polygon test against an Esri-style rings geometry
    (list of [lon, lat] rings; first ring outer, rest holes)."""
    inside = False
    for ring in rings:
        n = len(ring)
        j = n - 1
        ring_inside = False
        for i in range(n):
            xi, yi = ring[i][0], ring[i][1]
            xj, yj = ring[j][0], ring[j][1]
            if ((yi > lat) != (yj > lat)) and (
                lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-15) + xi
            ):
                ring_inside = not ring_inside
            j = i
        if ring_inside:
            inside = not inside
    return inside


def convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Andrew's monotone-chain convex hull. points = [(lon, lat), ...]."""
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list[tuple[float, float]] = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper: list[tuple[float, float]] = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]
