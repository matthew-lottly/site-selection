"""Step 8: Enrich the 5-site shortlist with real, per-site attributes:
  - FEMA National Flood Hazard Layer flood zone (identify at the parcel point)
  - Nearest TxDOT AADT count on the road the site actually fronts
  - Distance to the nearest existing dollar-store competitor (OSM)
  - Distance to the nearest grocery/big-box anchor (OSM, co-tenancy signal)

Output: data/processed/sites_enriched.csv
"""
from __future__ import annotations

import csv
import sys

import requests

from lib import FEMA_FLOOD, PROCESSED, RAW, haversine_miles

SHORTLIST_HCAD = {
    "0410070160182": {"site_label": "Site A - Cullen Blvd @ Griggs Rd / Old Spanish Trail"},
    "0730510120001": {"site_label": "Site B - 9104 Cullen Blvd @ Reed Rd"},
    "0470560000010": {"site_label": "Site C - 8707 MLK Jr Blvd @ Reed Rd"},
    "0410070080062": {"site_label": "Site D - 3839 Griggs Rd @ Scott St / Old Spanish Trail"},
    "0771850040007": {"site_label": "Site E - 9229 Martell St @ Scott St / Reed Rd"},
}

# which named road each site fronts, for AADT matching
SITE_ROAD = {
    "0410070160182": "CULLEN",
    "0730510120001": "CULLEN",
    "0470560000010": "REED",
    "0410070080062": "GRIGGS",
    "0771850040007": "REED",
}


def fema_flood_zone(lat: float, lon: float) -> tuple[str, str]:
    resp = requests.get(
        FEMA_FLOOD,
        params={
            "geometry": f"{lon},{lat}",
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "FLD_ZONE,ZONE_SUBTY,SFHA_TF",
            "returnGeometry": "false",
            "f": "json",
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    feats = data.get("features", [])
    if not feats:
        return "X (unmapped/outside detailed study area)", "F"
    a = feats[0]["attributes"]
    return a.get("FLD_ZONE", "X"), a.get("SFHA_TF", "F")


def main() -> None:
    with open(PROCESSED / "candidate_parcels.csv", encoding="utf-8") as fh:
        parcels = {r["hcad_num"]: r for r in csv.DictReader(fh)}

    with open(PROCESSED / "aadt_points.csv", encoding="utf-8") as fh:
        aadt = list(csv.DictReader(fh))

    with open(PROCESSED / "competitors.csv", encoding="utf-8") as fh:
        stores = list(csv.DictReader(fh))
    dollar_stores = [s for s in stores if s["category"] == "dollar_store"]
    anchors = [s for s in stores if s["category"] == "anchor"]

    rows = []
    for hcad_num, meta in SHORTLIST_HCAD.items():
        p = parcels[hcad_num]
        lat, lon = float(p["lat"]), float(p["lon"])

        zone, sfha = fema_flood_zone(lat, lon)

        road_key = SITE_ROAD[hcad_num]
        on_road = [a for a in aadt if road_key in a["road"].upper()]
        pool = on_road if on_road else aadt
        nearest_aadt = min(pool, key=lambda a: haversine_miles(lat, lon, float(a["lat"]), float(a["lon"])))
        aadt_dist = haversine_miles(lat, lon, float(nearest_aadt["lat"]), float(nearest_aadt["lon"]))

        nearest_dollar = min(dollar_stores, key=lambda s: haversine_miles(lat, lon, float(s["lat"]), float(s["lon"])))
        nearest_dollar_mi = haversine_miles(lat, lon, float(nearest_dollar["lat"]), float(nearest_dollar["lon"]))

        nearest_anchor = min(anchors, key=lambda s: haversine_miles(lat, lon, float(s["lat"]), float(s["lon"])))
        nearest_anchor_mi = haversine_miles(lat, lon, float(nearest_anchor["lat"]), float(nearest_anchor["lon"]))

        rows.append(
            {
                "site_label": meta["site_label"],
                "hcad_num": hcad_num,
                "address": p["address"] or f"{p['intersection']} (unaddressed tract)",
                "intersection": p["intersection"],
                "site_type": p["site_type"],
                "acreage": p["acreage"],
                "land_value": p["land_value"],
                "total_appraised_val": p["total_appraised_val"],
                "lat": lat,
                "lon": lon,
                "flood_zone": zone,
                "in_sfha": sfha,
                "aadt_road": nearest_aadt["road"],
                "aadt": nearest_aadt["aadt"],
                "aadt_year": nearest_aadt["year"],
                "aadt_station_dist_mi": round(aadt_dist, 2),
                "nearest_dollar_store": nearest_dollar["name"],
                "nearest_dollar_store_mi": round(nearest_dollar_mi, 2),
                "nearest_anchor": nearest_anchor["name"],
                "nearest_anchor_mi": round(nearest_anchor_mi, 2),
            }
        )
        print(f"{meta['site_label']}: zone={zone} AADT={nearest_aadt['aadt']} ({nearest_aadt['road']}) nearest_dollar={nearest_dollar_mi:.2f}mi", file=sys.stderr)

    out_path = PROCESSED / "sites_enriched.csv"
    fieldnames = list(rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {len(rows)} enriched sites -> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
