"""Step 16: Pull every real TxDOT AADT (2025) traffic-count station inside
the actual City of Houston envelope -- citywide, not just one submarket.
Paginates automatically if the result set exceeds the service's page size.

Output: data/processed/aadt_points.csv
"""
from __future__ import annotations

import csv
import json
import sys

from ..clients import TxDotClient
from ..core import PROCESSED, RAW, PipelineStage


class FetchCitywideAadtStage(PipelineStage):
    id = "16"
    name = "fetch_citywide_aadt"
    description = "Citywide TxDOT AADT (2025) traffic-count stations inside the Houston envelope"
    outputs = (PROCESSED / "aadt_points.csv",)

    # Houston city bounding envelope (from the real TIGERweb boundary, script 13)
    ENVELOPE = {"xmin": -95.79, "ymin": 29.52, "xmax": -95.01, "ymax": 30.11}

    def __init__(self) -> None:
        self.txdot = TxDotClient()

    def run(self) -> None:
        cache_path = RAW / "txdot_aadt_citywide.json"
        if cache_path.exists():
            all_features = json.loads(cache_path.read_text(encoding="utf-8"))
        else:
            all_features = []
            offset = 0
            page = 2000
            while True:
                data = self.txdot._request(
                    self.txdot.BASE_URL,
                    {
                        "geometry": f"{self.ENVELOPE['xmin']},{self.ENVELOPE['ymin']},{self.ENVELOPE['xmax']},{self.ENVELOPE['ymax']}",
                        "geometryType": "esriGeometryEnvelope",
                        "inSR": "4326",
                        "spatialRel": "esriSpatialRelIntersects",
                        "outFields": "TRFC_STATN_ID,AADT_RPT_YEAR,AADT_RPT_QTY,ON_ROAD,LATITUDE,LONGITUDE,ACTIVE",
                        "returnGeometry": "false",
                        "resultOffset": str(offset),
                        "resultRecordCount": str(page),
                        "f": "json",
                    },
                    timeout=40,
                )
                feats = data.get("features", [])
                all_features.extend(feats)
                print(f"  fetched {len(all_features)} AADT stations so far...", file=sys.stderr)
                if not data.get("exceededTransferLimit") or not feats:
                    break
                offset += page
            cache_path.write_text(json.dumps(all_features), encoding="utf-8")

        rows = []
        for f in all_features:
            a = f["attributes"]
            rows.append(
                {
                    "station_id": a["TRFC_STATN_ID"],
                    "year": a["AADT_RPT_YEAR"],
                    "aadt": a["AADT_RPT_QTY"],
                    "road": a["ON_ROAD"],
                    "lat": a["LATITUDE"],
                    "lon": a["LONGITUDE"],
                    "active": a["ACTIVE"],
                }
            )
        with open(PROCESSED / "aadt_points.csv", "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["station_id", "year", "aadt", "road", "lat", "lon", "active"])
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote {len(rows)} citywide TxDOT AADT stations -> {PROCESSED / 'aadt_points.csv'}", file=sys.stderr)


if __name__ == "__main__":
    FetchCitywideAadtStage().run()
