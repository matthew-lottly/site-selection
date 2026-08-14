"""HUD Multifamily Properties -- real, point-level, FHA-insured/HUD-assisted
multifamily housing (apartments, senior housing, assisted living), served as
a public ArcGIS REST Feature Service (same pattern as HudLihtcClient). A
different federal program than LIHTC (FHA mortgage insurance/project-based
assistance vs. tax credits), so its property universe is real and genuinely
complementary, not a duplicate.

This layer's `/query` endpoint declares point geometry but returns
`"geometry": null` for every feature regardless of `returnGeometry` -- a
real, confirmed API limitation (verified directly against the live service
with `f=geojson`, not assumed), not a bug in how it's queried here: the
server-side spatial filter still works correctly (an envelope query returns
only the real properties inside it), it just won't hand back coordinates.
Real street addresses (STD_ADDR/STD_CITY/STD_ST/STD_ZIP5) ARE returned, so
this client also exposes a Nominatim forward-geocode helper (same
rate-limited, cached pattern already used for reverse geocoding in script
18) to recover real coordinates from the real address, rather than
approximating or dropping the source."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import requests

from ..core.api_client import ApiClient
from ..core.paths import RAW


class HudMultifamilyClient(ApiClient):
    BASE_URL = "https://egis.hud.gov/arcgis/rest/services/gotit/MultifamilyProperties/MapServer/0/query"
    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    GEOCODE_HEADERS = {"User-Agent": "houston-site-selection-study/1.0"}

    def query(self, params: dict, cache_name: str) -> dict:
        return self.get_json(self.BASE_URL, params, cache_name)

    def geocode_address(self, address: str, city: str, state: str, zip5: str, cache_dir: Path = RAW) -> tuple[float, float] | None:
        """Real forward geocode of a HUD property's real street address via
        Nominatim, cached to disk so a property near multiple finalists is
        only ever looked up once, and rate-limited to Nominatim's 1 req/sec
        policy (respected the same way script 18 already does)."""
        key = f"{address}, {city}, {state} {zip5}".strip()
        # Python's built-in hash() is randomized per-process (PYTHONHASHSEED), which
        # would silently defeat this cache across runs -- use a stable digest instead.
        key_digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
        cache_path = cache_dir / f"nominatim_forward_{key_digest}.json"
        if cache_path.exists():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            return (cached["lat"], cached["lon"]) if cached else None

        resp = requests.get(
            self.NOMINATIM_URL,
            params={"q": key, "format": "json", "limit": 1, "countrycodes": "us"},
            headers=self.GEOCODE_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        results = resp.json()
        time.sleep(1.05)

        if not results:
            cache_path.write_text("null", encoding="utf-8")
            return None
        lat, lon = float(results[0]["lat"]), float(results[0]["lon"])
        cache_path.write_text(json.dumps({"lat": lat, "lon": lon}), encoding="utf-8")
        return lat, lon
