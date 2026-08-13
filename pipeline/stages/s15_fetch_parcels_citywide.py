"""Step 15 (generalizes the old scripts/06, which only searched Sunnyside):
Query real HCAD parcels around EVERY intersection found across all 10
Houston opportunity clusters (script 14), filter to realistic new-store
sites (vacant commercial land, or under-improved commercial land -- a
teardown/redevelopment opportunity), and shortlist up to 2 finalists per
cluster so the final scorecard compares real candidates spread across the
whole city, not one neighborhood.

Output:
  data/processed/candidate_parcels.csv  (every qualifying parcel found, all clusters)
  data/processed/site_shortlist.csv     (2 finalists per cluster, ~20 total)
"""
from __future__ import annotations

import csv
import json
import sys
import time
from collections import defaultdict

import requests

from ..clients import HcadClient
from ..core import PROCESSED, RAW, PipelineStage


class FetchParcelsCitywideStage(PipelineStage):
    id = "15"
    name = "fetch_parcels_citywide"
    description = "Query HCAD parcels around every citywide intersection and shortlist finalists per cluster"
    outputs = (
        PROCESSED / "candidate_parcels.csv",
        PROCESSED / "site_shortlist.csv",
    )

    FIELDS = (
        "HCAD_NUM,state_class,land_use,dscr,Acreage,land_sqft,land_value,bld_value,"
        "total_appraised_val,site_str_num,site_str_name,site_str_sfx,site_city,site_zip"
    )
    MAX_PER_CLUSTER = 2

    def __init__(self) -> None:
        self.hcad = HcadClient()

    @staticmethod
    def ring_centroid(rings: list) -> tuple[float, float]:
        pts = rings[0]
        lon = sum(p[0] for p in pts) / len(pts)
        lat = sum(p[1] for p in pts) / len(pts)
        return lat, lon

    def fetch_near(self, key: str, lat: float, lon: float, radius_m: int = 350) -> list[dict]:
        cache_path = RAW / f"hcad_{key}.json"
        if cache_path.exists():
            data = json.loads(cache_path.read_text(encoding="utf-8"))
        else:
            data = None
            for attempt in range(4):
                try:
                    resp = requests.get(
                        self.hcad.BASE_URL,
                        params={
                            "geometry": f"{lon},{lat}",
                            "geometryType": "esriGeometryPoint",
                            "inSR": "4326",
                            "distance": str(radius_m),
                            "units": "esriSRUnit_Meter",
                            "spatialRel": "esriSpatialRelIntersects",
                            "outFields": self.FIELDS,
                            "outSR": "4326",
                            "returnGeometry": "true",
                            "f": "json",
                        },
                        timeout=40,
                        verify=False,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        cache_path.write_text(resp.text, encoding="utf-8")
                        break
                except requests.RequestException as exc:
                    print(f"  {key}: request error {exc}, retrying...", file=sys.stderr)
                time.sleep(5)
            if data is None:
                return []

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
            # Filter out HOA common areas / drainage reserves / ROW slivers miscoded as
            # vacant commercial land in HCAD: real commercial land in Houston does not
            # appraise at a few hundred dollars per acre.
            if (land_value / acreage) < 15_000:
                continue
            rings = f.get("geometry", {}).get("rings")
            if not rings:
                continue
            clat, clon = self.ring_centroid(rings)
            addr = f"{int(a['site_str_num']) if a.get('site_str_num') else ''} {a.get('site_str_name') or ''} {a.get('site_str_sfx') or ''}".strip()
            out.append(
                {
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

    def run(self) -> None:
        with open(PROCESSED / "intersections.csv", encoding="utf-8") as fh:
            intersections = list(csv.DictReader(fh))

        by_cluster: dict[str, list[dict]] = defaultdict(list)
        seen_hcad_global: set[str] = set()  # a real parcel found near two overlapping cluster searches counts once

        for i, x in enumerate(intersections):
            key = f"{x['cluster_id']}_{i}"
            rows = self.fetch_near(key, float(x["lat"]), float(x["lon"]))
            new = 0
            for r in rows:
                if r["hcad_num"] in seen_hcad_global:
                    continue
                seen_hcad_global.add(r["hcad_num"])
                r["cluster_id"] = x["cluster_id"]
                r["neighborhood"] = x["neighborhood"]
                r["intersection"] = f"{x['road_a']} & {x['road_b']}"
                by_cluster[x["cluster_id"]].append(r)
                new += 1
            print(f"{key} ({x['neighborhood']}: {x['road_a']} & {x['road_b']}): +{new} new qualifying parcels", file=sys.stderr)

        all_rows = [r for rows in by_cluster.values() for r in rows]
        out_path = PROCESSED / "candidate_parcels.csv"
        fieldnames = [
            "cluster_id", "neighborhood", "intersection", "hcad_num", "state_class", "site_type", "acreage",
            "land_value", "bld_value", "total_appraised_val", "address", "city", "zip", "lat", "lon", "subdivision",
        ]
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"\nWrote {len(all_rows)} total qualifying parcels -> {out_path}", file=sys.stderr)

        shortlist = []
        for cluster_id, rows in by_cluster.items():
            rows.sort(key=lambda r: (0 if "Vacant" in r["site_type"] else 1, abs(r["acreage"] - 1.2)))
            shortlist.extend(rows[: self.MAX_PER_CLUSTER])

        shortlist_path = PROCESSED / "site_shortlist.csv"
        with open(shortlist_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(shortlist)
        print(f"Wrote {len(shortlist)} shortlisted finalists (up to {self.MAX_PER_CLUSTER}/cluster) -> {shortlist_path}", file=sys.stderr)
        for r in shortlist:
            print(f"  [{r['cluster_id']}] {r['address'] or r['intersection']} -- {r['site_type']}, {r['acreage']} ac, ${r['land_value']:,.0f}", file=sys.stderr)


if __name__ == "__main__":
    FetchParcelsCitywideStage().run()
