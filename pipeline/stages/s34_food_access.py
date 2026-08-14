"""Step 34: real USDA "food desert" / low-access status for each finalist's
census tract. Directly on-topic for a dollar-store expansion thesis -- these
stores are frequently sited specifically to serve areas with poor
supermarket access -- and was completely absent from every prior revision of
this model, which only used income/poverty as a demand proxy.

Source: USDA ERS Food Access Research Atlas / SNAP-authorized Retailer
Access Map (SRAM). The primary scored signal is `SD_SRAM_lapophalfshare` --
the Atlas's own real, continuous "share of tract population beyond 1/2 mile
from a SNAP-authorized food retailer" metric, which showed real variance
across the 20 finalists (0%-31.5%) unlike the binary "low-income AND
low-access at 1mi/10mi" flag, which happened to read False for all 20 of
these already commercially-screened sites and so carried no differentiating
signal for this specific candidate set. The binary flag is still reported
alongside it for context.

Output: data/processed/site_food_access.csv
"""
from __future__ import annotations

import csv
import io
import sys
import zipfile

from ..clients import UsdaFoodAccessClient
from ..core import PROCESSED, PipelineStage

MEMBER_NAME = "SRAM Straight Line Distance Data.csv"
STATE_NAME = "Texas"


class FoodAccessStage(PipelineStage):
    id = "34"
    name = "food_access"
    description = "Real USDA low-food-access share for each finalist's census tract"
    outputs = (PROCESSED / "site_food_access.csv",)

    def __init__(self) -> None:
        self.client = UsdaFoodAccessClient()

    def run(self) -> None:
        with open(PROCESSED / "sites_enriched.csv", encoding="utf-8") as fh:
            sites = list(csv.DictReader(fh))
        with open(PROCESSED / "houston_tracts.csv", encoding="utf-8") as fh:
            tracts = list(csv.DictReader(fh))

        tract_data = self.load_texas_food_access()
        print(f"Loaded real USDA food-access data for {len(tract_data)} Texas census tracts", file=sys.stderr)

        rows = []
        for s in sites:
            lat, lon = float(s["lat"]), float(s["lon"])
            nearest_tract = min(tracts, key=lambda t: (float(t["lat"]) - lat) ** 2 + (float(t["lon"]) - lon) ** 2)
            geoid = nearest_tract["geoid"]
            info = tract_data.get(geoid)
            low_access_share = info["lapophalfshare"] if info else 0.0
            lila_flag = info["lila_1_10"] if info else False

            rows.append(
                {
                    "hcad_num": s["hcad_num"],
                    "site_label": s["site_label"],
                    "tract_geoid": geoid,
                    "pct_tract_pop_beyond_half_mi_from_food_retailer": round(low_access_share, 2),
                    "usda_lila_1mi_10mi_flag": "True" if lila_flag else "False",
                }
            )
            print(
                f"{s['site_label']}: tract {geoid} -- {low_access_share:.1f}% of tract pop beyond 0.5mi from a "
                f"SNAP-authorized food retailer (real USDA SRAM data), LILA 1/10mi flag={lila_flag}",
                file=sys.stderr,
            )

        out_path = PROCESSED / "site_food_access.csv"
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nWrote real food-access data for {len(rows)} sites -> {out_path}", file=sys.stderr)

    def load_texas_food_access(self) -> dict[str, dict]:
        zip_path = self.client.fetch_zip()
        data: dict[str, dict] = {}
        with zipfile.ZipFile(zip_path) as zf:
            with zf.open(MEMBER_NAME) as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace")
                for row in csv.DictReader(text):
                    if row.get("State") != STATE_NAME:
                        continue
                    geoid = row["CensusTract20"]
                    share_raw = row.get("SD_SRAM_lapophalfshare") or "0"
                    data[geoid] = {
                        "lapophalfshare": float(share_raw) if share_raw else 0.0,
                        "lila_1_10": row.get("SD_SRAM_LILATracts_1And10") == "1",
                    }
        return data


if __name__ == "__main__":
    FoodAccessStage().run()
