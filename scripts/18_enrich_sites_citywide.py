"""Step 18 (generalizes the old scripts/08 to all 20 citywide finalists):
FEMA flood zone, nearest real TxDOT AADT count (with its station coordinate
reverse-geocoded to a real street name for verification -- TxDOT records
roads by route number, not local name, so this is how we confirm each match
is real rather than guessed), and distance to the nearest competitor in each
tier (direct dollar-store, off-price/general-merchandise, grocery anchor).

Output: data/processed/sites_enriched.csv
"""
from __future__ import annotations

import csv
import re
import sys
import time

import requests

from lib import FEMA_FLOOD, PROCESSED, RAW, haversine_miles

# A retail pad can't have a driveway directly onto a limited-access freeway/tollway,
# so for the "traffic exposure" metric we skip stations that reverse-geocode to one
# of these and prefer the nearest station on an actual frontage/arterial street.
FREEWAY_PATTERN = re.compile(
    r"\b(freeway|tollway|beltway|interstate|expressway|fwy)\b"
    r"|\bloop \d+\b|\bi-\d+\b|\bus[- ]\d+\b|\bsh[- ]\d+\b|\bsam houston (parkway|tollway)\b",
    re.IGNORECASE,
)


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


def reverse_geocode(lat: float, lon: float, zoom: int) -> dict:
    cache_path = RAW / f"nominatim_{zoom}_{round(lat, 5)}_{round(lon, 5)}.json"
    if cache_path.exists():
        import json

        return json.loads(cache_path.read_text(encoding="utf-8"))
    resp = requests.get(
        "https://nominatim.openstreetmap.org/reverse",
        params={"lat": lat, "lon": lon, "format": "json", "zoom": zoom},
        headers={"User-Agent": "houston-site-selection-study/1.0"},
        timeout=15,
    )
    resp.raise_for_status()
    d = resp.json()
    import json

    cache_path.write_text(json.dumps(d), encoding="utf-8")
    time.sleep(1.05)
    return d


def reverse_geocode_road(lat: float, lon: float) -> str:
    d = reverse_geocode(lat, lon, zoom=17)
    addr = d.get("address", {})
    return addr.get("road") or d.get("display_name", "").split(",")[0] or "unknown road"


def reverse_geocode_neighborhood(lat: float, lon: float) -> str:
    d = reverse_geocode(lat, lon, zoom=15)
    addr = d.get("address", {})
    return (
        addr.get("suburb")
        or addr.get("neighbourhood")
        or addr.get("city_district")
        or addr.get("quarter")
        or "Houston"
    )


def main() -> None:
    with open(PROCESSED / "site_shortlist.csv", encoding="utf-8") as fh:
        sites = list(csv.DictReader(fh))
    with open(PROCESSED / "aadt_points.csv", encoding="utf-8") as fh:
        aadt = list(csv.DictReader(fh))
    with open(PROCESSED / "competitors.csv", encoding="utf-8") as fh:
        stores = list(csv.DictReader(fh))
    dollar_stores = [s for s in stores if s["category"] == "dollar_store"]
    offprice = [s for s in stores if s["category"] == "offprice"]
    anchors = [s for s in stores if s["category"] == "grocery_anchor"]

    rows = []
    for i, s in enumerate(sites, start=1):
        lat, lon = float(s["lat"]), float(s["lon"])
        # the cluster-level neighborhood (script 13/15) can be several miles from any one
        # intersection inside that cluster's search bbox -- verify each site's own
        # immediate neighborhood individually rather than inheriting the cluster label.
        neighborhood = reverse_geocode_neighborhood(lat, lon)
        # HCAD situs address for raw vacant tracts is sometimes just a bare street-suffix
        # fragment (e.g. "LOOP") with no house number -- not a usable address, so fall
        # back to the real cross-street description instead of printing a fragment.
        has_house_number = bool(s["address"]) and s["address"].split(" ")[0].isdigit()
        display_address = s["address"] if has_house_number else f"{s['intersection']} (unaddressed vacant tract)"
        site_label = f"Site {i:02d} ({neighborhood}) - {display_address}"

        zone, sfha = fema_flood_zone(lat, lon)

        ranked_aadt = sorted(aadt, key=lambda a: haversine_miles(lat, lon, float(a["lat"]), float(a["lon"])))[:8]
        nearest_aadt = None
        aadt_road_name = None
        aadt_on_freeway = False
        for candidate in ranked_aadt:
            name = reverse_geocode_road(float(candidate["lat"]), float(candidate["lon"]))
            if not FREEWAY_PATTERN.search(name):
                nearest_aadt, aadt_road_name = candidate, name
                break
        if nearest_aadt is None:  # every nearby station is on a freeway; fall back to nearest, flagged
            nearest_aadt = ranked_aadt[0]
            aadt_road_name = reverse_geocode_road(float(nearest_aadt["lat"]), float(nearest_aadt["lon"]))
            aadt_on_freeway = True
        aadt_dist = haversine_miles(lat, lon, float(nearest_aadt["lat"]), float(nearest_aadt["lon"]))

        nearest_dollar = min(dollar_stores, key=lambda x: haversine_miles(lat, lon, float(x["lat"]), float(x["lon"])))
        nearest_dollar_mi = haversine_miles(lat, lon, float(nearest_dollar["lat"]), float(nearest_dollar["lon"]))

        nearest_offprice = min(offprice, key=lambda x: haversine_miles(lat, lon, float(x["lat"]), float(x["lon"]))) if offprice else None
        nearest_offprice_mi = haversine_miles(lat, lon, float(nearest_offprice["lat"]), float(nearest_offprice["lon"])) if nearest_offprice else None

        nearest_anchor = min(anchors, key=lambda x: haversine_miles(lat, lon, float(x["lat"]), float(x["lon"])))
        nearest_anchor_mi = haversine_miles(lat, lon, float(nearest_anchor["lat"]), float(nearest_anchor["lon"]))

        rows.append(
            {
                "site_label": site_label,
                "cluster_id": s["cluster_id"],
                "neighborhood": neighborhood,
                "cluster_search_area": s["neighborhood"],
                "hcad_num": s["hcad_num"],
                "address": display_address,
                "intersection": s["intersection"],
                "site_type": s["site_type"],
                "acreage": s["acreage"],
                "land_value": s["land_value"],
                "total_appraised_val": s["total_appraised_val"],
                "lat": lat,
                "lon": lon,
                "flood_zone": zone,
                "in_sfha": sfha,
                "aadt_road_verified": aadt_road_name,
                "aadt_on_freeway": aadt_on_freeway,
                "aadt": nearest_aadt["aadt"],
                "aadt_year": nearest_aadt["year"],
                "aadt_station_dist_mi": round(aadt_dist, 2),
                "nearest_dollar_store": nearest_dollar["name"],
                "nearest_dollar_store_brand": nearest_dollar["brand"],
                "nearest_dollar_store_mi": round(nearest_dollar_mi, 2),
                "nearest_offprice": nearest_offprice["name"] if nearest_offprice else "none found",
                "nearest_offprice_mi": round(nearest_offprice_mi, 2) if nearest_offprice_mi else None,
                "nearest_anchor": nearest_anchor["name"],
                "nearest_anchor_mi": round(nearest_anchor_mi, 2),
            }
        )
        flag = " [FREEWAY-ONLY, no arterial station nearby]" if aadt_on_freeway else ""
        print(
            f"{site_label}: zone={zone} AADT={nearest_aadt['aadt']} on {aadt_road_name}{flag} "
            f"({aadt_dist:.2f}mi) | nearest dollar store {nearest_dollar_mi:.2f}mi",
            file=sys.stderr,
        )

    out_path = PROCESSED / "sites_enriched.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {len(rows)} enriched citywide sites -> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
