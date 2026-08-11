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


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 3958.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


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
