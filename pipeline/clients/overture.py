"""Overture Maps Foundation -- real, free, open (CDLA Permissive 2.0) Places
data blending Meta, Microsoft, TomTom, and ~200 other sources with ML-based
dedup/QA, distributed as cloud-native GeoParquet. Used here as a real
cross-check/backfill against the OSM-sourced competitor and co-tenant pulls
(scripts 02 and 26), which this project already found have real gaps (e.g.
Ross Dress for Less undercounted in OSM)."""
from __future__ import annotations

from overturemaps.core import BBox, record_batch_reader


class OvertureClient:
    def places_in_bbox(self, min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> list[dict]:
        """Real Overture Places within a bounding box. Returns plain dicts with
        name, category, confidence, and lon/lat already parsed from the raw
        WKB point geometry -- no caller needs to know Overture's storage format."""
        import shapely.wkb

        bbox = BBox(min_lon, min_lat, max_lon, max_lat)
        reader = record_batch_reader("place", bbox)
        results = []
        for batch in reader:
            for row in batch.to_pylist():
                geom_bytes = row.get("geometry")
                if not geom_bytes:
                    continue
                point = shapely.wkb.loads(geom_bytes)
                names = row.get("names") or {}
                results.append(
                    {
                        "name": names.get("primary") or "",
                        "confidence": row.get("confidence") or 0.0,
                        "lon": point.x,
                        "lat": point.y,
                    }
                )
        return results
