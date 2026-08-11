"""Step 2: Pull real, current store locations from OpenStreetMap (Overpass API)
for Harris County, TX -- the existing dollar-store competitive set plus
grocery/big-box anchors that drive co-tenancy traffic.

Output: data/processed/competitors.csv
"""
from __future__ import annotations

import csv
import sys

import requests

from lib import OVERPASS, PROCESSED, RAW

# Harris County bounding box (south, west, north, east)
BBOX = (29.49, -95.97, 30.13, -94.90)

QUERY = f"""
[out:json][timeout:90];
(
  nwr["shop"="variety_store"]["brand"~"Dollar General|Family Dollar|Dollar Tree",i]{BBOX};
  nwr["shop"="variety_store"]["name"~"Dollar General|Family Dollar|Dollar Tree",i]{BBOX};
  nwr["shop"="convenience"]["name"~"Family Dollar|Dollar General|Dollar Tree",i]{BBOX};
  nwr["shop"="supermarket"]["name"~"Walmart|Target|Kroger|H-E-B|HEB|Fiesta Mart|Aldi",i]{BBOX};
  nwr["shop"="department_store"]["name"~"Walmart|Target",i]{BBOX};
);
out center tags;
"""


def classify(tags: dict) -> str:
    name = (tags.get("name") or tags.get("brand") or "").lower()
    if "dollar general" in name:
        return "Dollar General"
    if "family dollar" in name:
        return "Family Dollar"
    if "dollar tree" in name:
        return "Dollar Tree"
    if "walmart" in name:
        return "Walmart"
    if "target" in name:
        return "Target"
    if "kroger" in name:
        return "Kroger"
    if "h-e-b" in name or "heb" in name:
        return "H-E-B"
    if "fiesta" in name:
        return "Fiesta Mart"
    if "aldi" in name:
        return "Aldi"
    return tags.get("name") or tags.get("brand") or "Unknown"


DOLLAR_BRANDS = {"Dollar General", "Family Dollar", "Dollar Tree"}


def main() -> None:
    cache_path = RAW / "overpass_competitors.json"
    if cache_path.exists():
        import json

        data = json.loads(cache_path.read_text(encoding="utf-8"))
    else:
        resp = requests.post(
            OVERPASS,
            data={"data": QUERY},
            timeout=120,
            headers={"User-Agent": "curl/8.7.1", "Accept": "*/*"},
        )
        resp.raise_for_status()
        data = resp.json()
        cache_path.write_text(resp.text, encoding="utf-8")

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
        key = (round(lat, 5), round(lon, 5), brand)
        if key in seen:
            continue
        seen.add(key)
        category = "dollar_store" if brand in DOLLAR_BRANDS else "anchor"
        rows.append(
            {
                "osm_id": f"{el['type']}/{el['id']}",
                "name": tags.get("name") or brand,
                "brand": brand,
                "category": category,
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
        writer = csv.DictWriter(fh, fieldnames=["osm_id", "name", "brand", "category", "lat", "lon", "addr"])
        writer.writeheader()
        writer.writerows(rows)

    dollar_count = sum(1 for r in rows if r["category"] == "dollar_store")
    anchor_count = sum(1 for r in rows if r["category"] == "anchor")
    print(f"Wrote {len(rows)} stores ({dollar_count} dollar stores, {anchor_count} anchors) to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
