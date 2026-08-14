"""Step 2: Pull real, current store locations from OpenStreetMap (Overpass API)
across the FULL City of Houston footprint, categorized the way a Family
Dollar site selector actually thinks about them -- not just "dollar store
vs. not":

  - family_dollar   existing Family Dollar locations. NOT a competitor --
                     this is the company's own network. Relevant for
                     cannibalization risk, not competitive threat (script 24).
  - arch_rival      Dollar General, Five Below, Dollar Tree: same target
                     demographic, footprint, and inventory mix. The real
                     competitive threat. Dollar Tree was Family Dollar's
                     "sister banner" under a shared parent (Dollar Tree, Inc.)
                     through 2024, but Dollar Tree sold Family Dollar to
                     private equity (Brigade Capital Management, Macellum
                     Capital Management, Arkhouse Management) and the two
                     officially separated on July 8, 2025 -- Family Dollar is
                     now a standalone company, so Dollar Tree is a real,
                     same-format competitor, not a related banner.
  - value_grocery    Extreme-value grocers Houston's low-income households
                     split their budget with, incl. two Houston-specific
                     banners: H-E-B's Joe V's Smart Shop and Fiesta's Mi
                     Tienda, alongside Aldi, Save A Lot, Fiesta Mart, Food
                     Town, Kroger, and H-E-B.
  - big_box_anchor   Walmart, Target, Burlington, Ross: general-merchandise
                     price anchors and regional traffic generators.

Output: data/processed/competitors.csv
"""
from __future__ import annotations

import csv
import sys
import time

import requests

from ..clients import OverpassClient
from ..core import PROCESSED, RAW, PipelineStage


class FetchCompetitorsStage(PipelineStage):
    id = "02"
    name = "fetch_competitors"
    description = "OSM competitor & anchor store locations across the full City of Houston (Overpass API)"
    outputs = (PROCESSED / "competitors.csv",)

    # Generous Harris County bounding box (south, west, north, east) -- filtered
    # down to true Houston city limits later in the pipeline via houston_boundary.geojson
    BBOX = (29.49, -95.97, 30.13, -94.90)

    NAME_PATTERN = (
        "Dollar General|Family Dollar|Dollar Tree|99 Cents Only|Fred's|Variety Wholesalers|"
        "Walmart|Target|Big Lots|Five Below|Ross Dress for Less|Ross Stores|Burlington|"
        "Kroger|H-E-B|HEB|Fiesta Mart|Aldi|Food Town|Save A Lot|Save-A-Lot|"
        "Joe V's|Joe Vs|Mi Tienda"
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
    # proxy for the Huff gravity model in script 19 -- NOT a per-store measurement,
    # since HCAD/OSM don't publish individual competitor floor-plate sizes.
    BANNER_SQFT = {
        "Family Dollar": 8_500,
        "Dollar General": 7_400,
        "Five Below": 8_500,
        "Dollar Tree": 9_000,
        "Aldi": 17_000,
        "Save A Lot": 16_000,
        "Joe V's Smart Shop": 30_000,
        "Mi Tienda": 40_000,
        "Fiesta Mart": 50_000,
        "Food Town": 40_000,
        "Kroger": 55_000,
        "H-E-B": 90_000,
        "Walmart": 100_000,  # blended Supercenter/Neighborhood Market typical
        "Target": 125_000,
        "Burlington": 65_000,
        "Ross Dress for Less": 28_000,
    }

    BRAND_CATEGORY = {
        "Family Dollar": "family_dollar",
        "Dollar General": "arch_rival",
        "Five Below": "arch_rival",
        "Dollar Tree": "arch_rival",
        "Aldi": "value_grocery",
        "Save A Lot": "value_grocery",
        "Joe V's Smart Shop": "value_grocery",
        "Mi Tienda": "value_grocery",
        "Fiesta Mart": "value_grocery",
        "Food Town": "value_grocery",
        "Kroger": "value_grocery",
        "H-E-B": "value_grocery",
        "Walmart": "big_box_anchor",
        "Target": "big_box_anchor",
        "Burlington": "big_box_anchor",
        "Ross Dress for Less": "big_box_anchor",
    }

    def __init__(self) -> None:
        self.overpass = OverpassClient()

    @staticmethod
    def classify(tags: dict) -> str:
        name = (tags.get("name") or tags.get("brand") or "").lower()
        checks = [
            ("dollar general", "Dollar General"), ("family dollar", "Family Dollar"), ("dollar tree", "Dollar Tree"),
            ("walmart", "Walmart"), ("target", "Target"), ("five below", "Five Below"),
            ("ross dress for less", "Ross Dress for Less"), ("ross stores", "Ross Dress for Less"),
            ("burlington", "Burlington"), ("kroger", "Kroger"), ("h-e-b", "H-E-B"), ("heb", "H-E-B"),
            ("joe v", "Joe V's Smart Shop"), ("mi tienda", "Mi Tienda"),
            ("fiesta mart", "Fiesta Mart"), ("aldi", "Aldi"), ("food town", "Food Town"),
            ("save a lot", "Save A Lot"), ("save-a-lot", "Save A Lot"),
        ]
        for needle, brand in checks:
            if needle in name:
                return brand
        return tags.get("name") or tags.get("brand") or "Unknown"

    def run(self) -> None:
        cache_path = RAW / "overpass_competitors.json"
        if cache_path.exists():
            import json

            data = json.loads(cache_path.read_text(encoding="utf-8"))
        else:
            data = None
            for attempt in range(5):
                resp = requests.post(
                    self.overpass.BASE_URL,
                    data={"data": self.QUERY},
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
            brand = self.classify(tags)
            if brand == "Unknown" or brand not in self.BANNER_SQFT:
                continue
            key = (round(lat, 5), round(lon, 5), brand)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "osm_id": f"{el['type']}/{el['id']}",
                    "name": tags.get("name") or brand,
                    "brand": brand,
                    "category": self.BRAND_CATEGORY[brand],
                    "typical_sqft": self.BANNER_SQFT[brand],
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
        cat_counts = Counter(r["category"] for r in rows)
        print(f"Wrote {len(rows)} stores to {out_path}", file=sys.stderr)
        print(f"By category: {dict(cat_counts)}", file=sys.stderr)
        for brand, n in counts.most_common():
            print(f"  {brand}: {n}", file=sys.stderr)


if __name__ == "__main__":
    FetchCompetitorsStage().run()
