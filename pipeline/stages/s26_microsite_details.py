"""Step 26: Real micro-site operational details -- the things an experienced
retail real estate professional checks beyond the macro numbers. Each is
either pulled from a real source or explicitly flagged as NOT verifiable
from public data (never guessed):

  - Posted speed limit on the frontage road (OSM `maxspeed` tag, where
    tagged): dollar-store visibility/impulse-stop sweet spot is ~35-45 mph;
    55+ mph means drivers pass the entrance before they can safely turn in.
  - Real co-tenant traffic generators within 0.3 mi (OSM POIs: gas/fuel
    stations, laundromats, schools, post offices, pharmacies) -- the
    complementary-anchor detail a site selector cites for shared-trip traffic.
  - Real distance to the nearest public-transit stop (OSM `highway=bus_stop`
    / `public_transport=platform`, incl. Houston METRO) within 1 mile --
    dollar-store customers in urban corridors frequently walk or bus in for
    top-off trips, so transit proximity is a real demand signal.
  - Approximate parcel bounding dimensions computed from the REAL HCAD
    parcel polygon already fetched in script 15 (haversine edge lengths,
    not a survey) -- a rough gut-check on whether the lot is even
    plausibly large enough for a delivery-truck turning movement, not a
    certified engineering confirmation.

Explicitly NOT claimed, because no public API provides it and asserting a
confirmation would be a fabrication:
  - Deed restrictions / restrictive covenants (requires a title search)
  - Median-break / divided-highway ingress-egress geometry (requires a
    site plan or a levels-of-detail OSM tagging this pipeline doesn't rely on)
  - A verified, engineered 53-ft delivery-truck turning radius (requires a
    civil site plan)
  - Houston's specific parking-space requirement for a given parcel
    (the general municipal ratio is public and cited as CONTEXT in the
    docs, not computed here as a parcel-specific verified figure)

Output: data/processed/microsite_details.csv
"""
from __future__ import annotations

import csv
import json
import re
import sys
import time

import requests

from ..clients import OverpassClient
from ..core import PROCESSED, RAW, PipelineStage
from ..geometry import Geometry


class MicrositeDetailsStage(PipelineStage):
    id = "26"
    name = "microsite_details"
    description = "Real micro-site operational details: speed limit, co-tenants, transit proximity, parcel dimensions"
    outputs = (PROCESSED / "microsite_details.csv",)

    POI_TAGS = {
        "fuel": "Gas station",
        "school": "School",
        "post_office": "Post office",
        "pharmacy": "Pharmacy",
    }

    FUNCTIONAL_CLASS = {
        "motorway": "Limited-access freeway",
        "trunk": "Limited-access freeway",
        "primary": "Principal arterial",
        "secondary": "Minor arterial",
        "tertiary": "Collector / local connector",
    }

    def __init__(self) -> None:
        self.overpass = OverpassClient()

    def query_microsite(self, lat: float, lon: float) -> dict:
        # Not routed through OverpassClient.query() -- that wraps a single POST
        # attempt, and this call needs the original's 4-attempt retry-with-backoff
        # on any non-200 (Overpass rate-limits/504s under load), which the shared
        # client doesn't expose. Uses the client only for BASE_URL/HEADERS.
        q = f"""[out:json][timeout:40];
        (
          way["highway"~"^(primary|secondary|tertiary)$"](around:200,{lat},{lon});
          node["amenity"~"^(fuel|school|post_office|pharmacy)$"](around:500,{lat},{lon});
          node["shop"="laundry"](around:500,{lat},{lon});
          node["highway"="bus_stop"](around:1600,{lat},{lon});
          node["public_transport"="platform"](around:1600,{lat},{lon});
        );
        out center tags;"""
        for attempt in range(4):
            resp = requests.post(self.overpass.BASE_URL, data={"data": q}, timeout=60, headers=self.overpass.HEADERS)
            if resp.status_code == 200:
                return resp.json()
            time.sleep(8 * (attempt + 1))
        raise RuntimeError("Overpass failed after retries")

    @staticmethod
    def parcel_bounding_ft(hcad_num: str) -> tuple[float, float] | None:
        """Re-parse the HCAD parcel geometry already cached by script 15 to get
        approximate bounding-box dimensions (feet) for a real gut-check on lot
        size -- not a survey, and explicitly labeled as such downstream."""
        for cache_file in RAW.glob("hcad_*.json"):
            try:
                data = json.loads(cache_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            for feat in data.get("features", []):
                if feat["attributes"].get("HCAD_NUM") != hcad_num:
                    continue
                rings = feat.get("geometry", {}).get("rings")
                if not rings:
                    return None
                pts = rings[0]
                lons = [p[0] for p in pts]
                lats = [p[1] for p in pts]
                width_mi = Geometry.haversine_miles(min(lats), min(lons), min(lats), max(lons))
                height_mi = Geometry.haversine_miles(min(lats), min(lons), max(lats), min(lons))
                return round(width_mi * 5280), round(height_mi * 5280)
        return None

    def run(self) -> None:
        with open(PROCESSED / "sites_enriched.csv", encoding="utf-8") as fh:
            sites = list(csv.DictReader(fh))

        rows = []
        for s in sites:
            lat, lon = float(s["lat"]), float(s["lon"])
            cache_path = RAW / f"overpass_microsite_{s['hcad_num']}.json"
            if cache_path.exists():
                data = json.loads(cache_path.read_text(encoding="utf-8"))
            else:
                data = self.query_microsite(lat, lon)
                cache_path.write_text(json.dumps(data), encoding="utf-8")
                time.sleep(1.0)

            maxspeed = None
            road_class = "Not tagged in OSM"
            for el in data["elements"]:
                t = el.get("tags", {})
                if t.get("highway") and t.get("maxspeed"):
                    m = re.search(r"\d+", t["maxspeed"])
                    if m:
                        maxspeed = int(m.group())
                if t.get("highway") in self.FUNCTIONAL_CLASS:
                    road_class = self.FUNCTIONAL_CLASS[t["highway"]]

            pois = []
            for el in data["elements"]:
                t = el.get("tags", {})
                kind = self.POI_TAGS.get(t.get("amenity")) or ("Laundromat" if t.get("shop") == "laundry" else None)
                if not kind:
                    continue
                if el["type"] == "node":
                    plat, plon = el["lat"], el["lon"]
                else:
                    c = el.get("center")
                    if not c:
                        continue
                    plat, plon = c["lat"], c["lon"]
                dist = Geometry.haversine_miles(lat, lon, plat, plon)
                pois.append((dist, kind, t.get("name") or kind))
            pois.sort()
            co_tenant_count = sum(1 for dist, _kind, _name in pois if dist <= 0.3)
            co_tenants = "; ".join(f"{name} ({dist*5280:.0f} ft)" for dist, kind, name in pois[:3]) or "none found within 0.3 mi"

            transit_dists = []
            transit_within_500ft = 0
            for el in data["elements"]:
                t = el.get("tags", {})
                if t.get("highway") != "bus_stop" and t.get("public_transport") != "platform":
                    continue
                plat, plon = (el["lat"], el["lon"]) if el["type"] == "node" else (None, None)
                if plat is None:
                    continue
                dist_mi = Geometry.haversine_miles(lat, lon, plat, plon)
                transit_dists.append(dist_mi)
                if dist_mi <= (500 / 5280):
                    transit_within_500ft += 1
            nearest_transit_ft = round(min(transit_dists) * 5280) if transit_dists else None
            transit_note = f"{nearest_transit_ft:,} ft" if nearest_transit_ft else "none within 1 mi"

            bbox = self.parcel_bounding_ft(s["hcad_num"])
            lot_dims = f"~{bbox[0]} ft x {bbox[1]} ft (bounding box, not a survey)" if bbox else "not available"

            speed_note = (
                "sweet spot (35-45 mph) for impulse-stop visibility" if maxspeed and 35 <= maxspeed <= 45
                else ("fast road -- reduced impulse-stop visibility" if maxspeed and maxspeed >= 50
                      else ("slow/local road" if maxspeed else "not tagged in OSM"))
            )

            rows.append(
                {
                    "hcad_num": s["hcad_num"],
                    "site_label": s["site_label"],
                    "posted_speed_limit_mph": maxspeed if maxspeed else "not tagged in OSM",
                    "speed_assessment": speed_note,
                    "road_functional_class": road_class,
                    "co_tenant_count_0_3mi": co_tenant_count,
                    "nearby_co_tenants": co_tenants,
                    "bus_stops_within_500ft": transit_within_500ft,
                    "nearest_transit_stop": transit_note,
                    "approx_lot_dimensions": lot_dims,
                    "deed_restrictions": "NOT VERIFIED -- requires a title search, no public API covers this",
                    "median_ingress_egress": "NOT VERIFIED -- requires a site plan / civil engineering review",
                }
            )
            print(f"{s['site_label']}: speed={maxspeed or 'n/a'}mph ({speed_note}) | co-tenants: {co_tenants} | transit: {transit_note} | lot: {lot_dims}", file=sys.stderr)

        out_path = PROCESSED / "microsite_details.csv"
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nWrote {len(rows)} microsite detail records -> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    MicrositeDetailsStage().run()
