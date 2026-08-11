"""Step 30: fetch FEMA NFHL flood-zone polygons for the Houston map.

This writes a GeoJSON overlay that the final map can toggle on/off. The layer
uses FEMA NFHL flood-hazard polygons (MapServer layer 28), clipped to the
Houston map extent so the web map stays responsive.
"""
from __future__ import annotations

import json
from pathlib import Path

import requests

from lib import FEMA_FLOOD, PROCESSED, RAW

OUT_PATH = PROCESSED / "houston_fema_flood.geojson"
RAW_CACHE = RAW / "houston_fema_flood_layer28.json"
QUERY_URL = f"{FEMA_FLOOD}/query"
def _coord_bounds(coords: object, state: list[float]) -> None:
    if isinstance(coords, (list, tuple)):
        if len(coords) == 2 and all(isinstance(v, (int, float)) for v in coords):
            lon, lat = float(coords[0]), float(coords[1])
            state[0] = min(state[0], lon)
            state[1] = min(state[1], lat)
            state[2] = max(state[2], lon)
            state[3] = max(state[3], lat)
            return
        for item in coords:
            _coord_bounds(item, state)


def load_houston_boundary() -> dict:
    boundary_path = PROCESSED / "houston_boundary.geojson"
    return json.loads(boundary_path.read_text(encoding="utf-8"))["features"][0]["geometry"]


def _geometry_envelope(geometry: dict) -> dict:
    bounds = [float("inf"), float("inf"), float("-inf"), float("-inf")]
    _coord_bounds(geometry.get("coordinates"), bounds)
    return {
        "xmin": bounds[0],
        "ymin": bounds[1],
        "xmax": bounds[2],
        "ymax": bounds[3],
        "spatialReference": {"wkid": 4326},
    }


def _query_object_ids(where_clause: str, geometry: dict | None = None) -> list[int]:
    params: dict[str, str] = {
        "where": where_clause,
        "returnIdsOnly": "true",
        "f": "json",
    }
    if geometry is not None:
        geometry_type = "esriGeometryEnvelope" if {"xmin", "ymin", "xmax", "ymax"}.issubset(geometry) else "esriGeometryPolygon"
        geometry_value = (
            f"{geometry['xmin']},{geometry['ymin']},{geometry['xmax']},{geometry['ymax']}"
            if geometry_type == "esriGeometryEnvelope"
            else json.dumps(geometry)
        )
        params.update(
            {
                "geometry": geometry_value,
                "geometryType": geometry_type,
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
            }
        )
    resp = requests.get(QUERY_URL, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return sorted(data.get("objectIds", []))


def _fetch_batch(object_ids: list[int]) -> list[dict]:
    resp = requests.get(
        QUERY_URL,
        params={
            "objectIds": ",".join(str(i) for i in object_ids),
            "outFields": "FLD_ZONE,ZONE_SUBTY,SFHA_TF,OBJECTID",
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "geojson",
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json().get("features", [])


def _fetch_by_where(where_clause: str) -> list[dict]:
    features: list[dict] = []
    offset = 0
    page_size = 200
    while True:
        resp = requests.get(
            QUERY_URL,
            params={
                "where": where_clause,
                "outFields": "FLD_ZONE,ZONE_SUBTY,SFHA_TF,OBJECTID",
                "returnGeometry": "true",
                "outSR": "4326",
                "resultOffset": str(offset),
                "resultRecordCount": str(page_size),
                "f": "geojson",
            },
            timeout=60,
        )
        resp.raise_for_status()
        batch = resp.json().get("features", [])
        features.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size
    return features


def query_flood_polygons() -> dict:
    boundary = load_houston_boundary()
    geometry = _geometry_envelope(boundary)

    object_ids = _query_object_ids("1=1", geometry)
    if not object_ids:
        object_ids = _query_object_ids("1=1", None)
    if not object_ids:
        features = _fetch_by_where("1=1")
        return {"type": "FeatureCollection", "features": features}

    features: list[dict] = []
    batch_size = 200
    for start in range(0, len(object_ids), batch_size):
        batch_ids = object_ids[start : start + batch_size]
        features.extend(_fetch_batch(batch_ids))

    return {"type": "FeatureCollection", "features": features}


def main() -> None:
    RAW_CACHE.write_text(json.dumps(query_flood_polygons()), encoding="utf-8")
    OUT_PATH.write_text(RAW_CACHE.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote FEMA flood polygons -> {OUT_PATH}")


if __name__ == "__main__":
    main()