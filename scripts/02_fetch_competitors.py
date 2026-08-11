"""Step 2: Pull real, current store locations from OpenStreetMap (Overpass API)
across the FULL City of Houston footprint -- the direct dollar-store
competitive set, off-price/general-merchandise chains, and grocery anchors
that drive co-tenancy traffic and factor into the Huff gravity model
(script 15).

Output: data/processed/competitors.csv
"""
from __future__ import annotations

import csv
import sys
import time

import requests

from lib import OVERPASS, PROCESSED, RAW

# Generous Harris County bounding box (south, west, north, east) -- filtered
# down to true Houston city limits later in the pipeline via houston_boundary.geojson
BBOX = (29.49, -95.97, 30.13, -94.90)

NAME_PATTERN = (
    "Dollar General|Family Dollar|Dollar Tree|99 Cents Only|Fred's|Variety Wholesalers|"
    "Walmart|Target|Big Lots|Five Below|Ross Dress for Less|Ross Stores|Burlington|"
    "Kroger|H-E-B|HEB|Fiesta Mart|Aldi|Food Town|Save A Lot|Save-A-Lot"
)

QUERY = f"""
[out:json][timeout:120];
(
  nwr["shop"~"variety_store|convenience|department_store|supermarket|discount"]["brand"~"{NAME_PATTERN}",i]{BBOX};
  nwr["shop"~"variety_store|convenience|department_store|supermarket|discount"]["name"~"{NAME_PATTERN}",i]{BBOX};
);
out center tags;
"""

# Real, published typical prototype square footage by banner (company fact
# sheets / commercial real estate literature). Used only as a size/attraction
# proxy for the Huff gravity model in script 15 -- NOT a per-store measurement,
# since HCAD/OSM don't publish individual competitor floor-plate sizes.
BANNER_SQFT = {
    "Family Dollar": 8_500,
    "Dollar General": 7_400,
    "Dollar Tree": 9_000,
    "99 Cents Only": 25_000,
    "Fred's": 15_000,
    "Variety Wholesalers": 15_000,
    "Walmart": 100_000,  # blended Supercenter/Neighborhood Market typical
    "Target": 125_000,
    "Big Lots": 30_000,
    "Five Below": 8_500,
    "Ross Dress for Less": 28_000,
    "Burlington": 65_000,
    "Kroger": 55_000,
    "H-E-B": 90_000,
    "Fiesta Mart": 50_000,
    "Aldi": 17_000,
    "Food Town": 40_000,
    "Save A Lot": 16_000,
}

DOLLAR_BRANDS = {"Dollar General", "Family Dollar", "Dollar Tree", "99 Cents Only", "Fred's", "Variety Wholesalers"}
OFFPRICE_BRANDS = {"Big Lots", "Five Below", "Ross Dress for Less", "Burlington", "Target"}
# Walmart is both a direct discount-retail competitor AND a grocery/general-merch anchor;
# category "anchor" for map grouping, but included in the Huff competitor set either way.


def classify(tags: dict) -> str:
    name = (tags.get("name") or tags.get("brand") or "").lower()
    checks = [
        ("dollar general", "Dollar General"), ("family dollar", "Family Dollar"), ("dollar tree", "Dollar Tree"),
        ("99 cents only", "99 Cents Only"), ("fred's", "Fred's"), ("variety wholesalers", "Variety Wholesalers"),
        ("walmart", "Walmart"), ("target", "Target"), ("big lots", "Big Lots"), ("five below", "Five Below"),
        ("ross dress for less", "Ross Dress for Less"), ("ross stores", "Ross Dress for Less"),
        ("burlington", "Burlington"), ("kroger", "Kroger"), ("h-e-b", "H-E-B"), ("heb", "H-E-B"),
        ("fiesta mart", "Fiesta Mart"), ("aldi", "Aldi"), ("food town", "Food Town"),
        ("save a lot", "Save A Lot"), ("save-a-lot", "Save A Lot"),
    ]
    for needle, brand in checks:
        if needle in name:
            return brand
    return tags.get("name") or tags.get("brand") or "Unknown"


def category_for(brand: str) -> str:
    if brand in DOLLAR_BRANDS:
        return "dollar_store"
    if brand in OFFPRICE_BRANDS:
        return "offprice"
    return "grocery_anchor"


def main() -> None:
    cache_path = RAW / "overpass_competitors.json"
    if cache_path.exists():
        import json

        data = json.loads(cache_path.read_text(encoding="utf-8"))
    else:
        data = None
        for attempt in range(5):
            resp = requests.post(
                OVERPASS,
                data={"data": QUERY},
                timeout=150,
                headers={"User-Agent": "curl/8.7.1", "Accept": "*/*"},
            )
            if resp.status_code == 200:
                data = resp.json()
                cache_path.write_text(resp.text, encoding="utf-8")
                break
            if resp.status_code in (429, 504):
                wait = 15 * (attempt + 1)
                print(f"Overpass {resp.status_code}, retrying in {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            resp.raise_for_status()
        if data is None:
            raise RuntimeError("Overpass failed after retries")

    rows = []
    seen = set()
    for el in data["elements"]:
        tags = el.get("tags", {})
        if el["type"] == "node":
            lat, lon = el["lat"], el["lon"]
        else:
            center = el.get("center")
            if not center:
                continue
            lat, lon = center["lat"], center["lon"]
        brand = classify(tags)
        if brand == "Unknown" or brand not in BANNER_SQFT:
            continue
        key = (round(lat, 5), round(lon, 5), brand)
        if key in seen:
            continue
        seen.add(key)
        category = category_for(brand)
        rows.append(
            {
                "osm_id": f"{el['type']}/{el['id']}",
                "name": tags.get("name") or brand,
                "brand": brand,
                "category": category,
                "typical_sqft": BANNER_SQFT[brand],
                "lat": lat,
                "lon": lon,
                "addr": ", ".join(
                    filter(
                        None,
                        [tags.get("addr:housenumber", "") + " " + tags.get("addr:street", "") if tags.get("addr:street") else None, tags.get("addr:city")],
                    )
                ),
            }
        )

    out_path = PROCESSED / "competitors.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["osm_id", "name", "brand", "category", "typical_sqft", "lat", "lon", "addr"])
        writer.writeheader()
        writer.writerows(rows)

    from collections import Counter

    counts = Counter(r["brand"] for r in rows)
    print(f"Wrote {len(rows)} stores to {out_path}", file=sys.stderr)
    for brand, n in counts.most_common():
        print(f"  {brand}: {n}", file=sys.stderr)


if __name__ == "__main__":
    main()
