"""Step 6: Pull real Harris County Appraisal District (HCAD) parcels around
each candidate arterial intersection identified in script 05, and shortlist
realistic new-store sites: vacant commercial land (state_class C1/C2) or
under-improved commercial parcels (state_class F1 with a low building-to-land
value ratio, i.e. a teardown/redevelopment opportunity), sized roughly like a
freestanding discount-store pad (0.4-4 acres).

Output: data/processed/candidate_parcels.csv (full shortlist, all intersections)
"""
from __future__ import annotations

import csv
import sys

import requests

from lib import HCAD_PARCELS, PROCESSED, RAW

FIELDS = (
    "HCAD_NUM,state_class,land_use,dscr,Acreage,land_sqft,land_value,bld_value,"
    "total_appraised_val,site_str_num,site_str_name,site_str_sfx,site_city,site_zip"
)


def ring_centroid(rings: list) -> tuple[float, float]:
    pts = rings[0]
    lon = sum(p[0] for p in pts) / len(pts)
    lat = sum(p[1] for p in pts) / len(pts)
    return lat, lon


def fetch_near(label: str, lat: float, lon: float, radius_m: int = 350) -> list[dict]:
    cache_path = RAW / f"hcad_{label.replace(' ', '_').replace('/', '-')}.json"
    if cache_path.exists():
        import json

        data = json.loads(cache_path.read_text(encoding="utf-8"))
    else:
        resp = requests.get(
            HCAD_PARCELS,
            params={
                "geometry": f"{lon},{lat}",
                "geometryType": "esriGeometryPoint",
                "inSR": "4326",
                "distance": str(radius_m),
                "units": "esriSRUnit_Meter",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": FIELDS,
                "outSR": "4326",
                "returnGeometry": "true",
                "f": "json",
            },
            timeout=40,
            verify=False,
        )
        resp.raise_for_status()
        data = resp.json()
        cache_path.write_text(resp.text, encoding="utf-8")

    out = []
    for f in data.get("features", []):
        a = f["attributes"]
        acreage = a.get("Acreage")
        try:
            acreage = float(acreage) if acreage is not None else (float(a.get("land_sqft") or 0) / 43_560)
        except (TypeError, ValueError):
            continue
        if not (0.4 <= acreage <= 4.0):
            continue
        state_class = a.get("state_class")
        land_value = float(a.get("land_value") or 0)
        bld_value = float(a.get("bld_value") or 0)
        appraised = float(a.get("total_appraised_val") or 0)
        if state_class in ("C1", "C2"):
            site_type = "Vacant commercial land"
        elif state_class == "F1" and land_value > 0 and bld_value / max(land_value, 1) < 0.6:
            site_type = "Under-improved commercial (redevelopment)"
        else:
            continue
        rings = f.get("geometry", {}).get("rings")
        if not rings:
            continue
        clat, clon = ring_centroid(rings)
        addr = f"{int(a['site_str_num']) if a.get('site_str_num') else ''} {a.get('site_str_name') or ''} {a.get('site_str_sfx') or ''}".strip()
        out.append(
            {
                "intersection": label,
                "hcad_num": a.get("HCAD_NUM"),
                "state_class": state_class,
                "site_type": site_type,
                "acreage": round(acreage, 2),
                "land_value": land_value,
                "bld_value": bld_value,
                "total_appraised_val": appraised,
                "address": addr,
                "city": a.get("site_city"),
                "zip": a.get("site_zip"),
                "lat": round(clat, 6),
                "lon": round(clon, 6),
                "subdivision": a.get("dscr"),
            }
        )
    return out


def main() -> None:
    with open(PROCESSED / "intersections.csv", encoding="utf-8") as fh:
        intersections = list(csv.DictReader(fh))

    all_rows = []
    for x in intersections:
        label = f"{x['road_a']} & {x['road_b']}"
        rows = fetch_near(label, float(x["lat"]), float(x["lon"]))
        rows.sort(key=lambda r: abs(r["acreage"] - 1.2))  # prefer pads close to a typical ~1.2-acre FD footprint
        print(f"{label}: {len(rows)} candidate parcels", file=sys.stderr)
        all_rows.extend(rows)

    out_path = PROCESSED / "candidate_parcels.csv"
    fieldnames = [
        "intersection", "hcad_num", "state_class", "site_type", "acreage", "land_value",
        "bld_value", "total_appraised_val", "address", "city", "zip", "lat", "lon", "subdivision",
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"\nWrote {len(all_rows)} candidate parcels total -> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
