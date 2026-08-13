"""Geometry helpers shared across pipeline stages: distance, point-in-polygon
tests, line simplification, and convex hulls over plain lon/lat coordinates.
Stateless by design -- grouped as staticmethods for a single, discoverable
import surface rather than scattered module-level functions.
"""
from __future__ import annotations

import math


class Geometry:
    @staticmethod
    def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 3958.8
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
        return 2 * r * math.asin(math.sqrt(a))

    @staticmethod
    def ring_bbox(ring: list) -> tuple[float, float, float, float]:
        lons = [p[0] for p in ring]
        lats = [p[1] for p in ring]
        return min(lons), min(lats), max(lons), max(lats)

    @classmethod
    def point_in_rings_fast(cls, lat: float, lon: float, rings: list, bboxes: list) -> bool:
        """Ray-casting point-in-polygon with a per-ring bbox short-circuit --
        needed for Houston's real city boundary (100 rings, ~70,800 vertices)."""
        inside = False
        for ring, (minx, miny, maxx, maxy) in zip(rings, bboxes):
            if not (minx <= lon <= maxx and miny <= lat <= maxy):
                continue
            n = len(ring)
            j = n - 1
            ring_inside = False
            for i in range(n):
                xi, yi = ring[i][0], ring[i][1]
                xj, yj = ring[j][0], ring[j][1]
                if ((yi > lat) != (yj > lat)) and (lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-15) + xi):
                    ring_inside = not ring_inside
                j = i
            if ring_inside:
                inside = not inside
        return inside

    @staticmethod
    def simplify_ring(points: list[list[float]], tolerance: float) -> list[list[float]]:
        """Douglas-Peucker line simplification for a single ring of [lon, lat] points.
        Used only to shrink display-map file size; source data is untouched."""
        if len(points) <= 4:
            return points

        def perpendicular_distance(pt, start, end):
            if start == end:
                return math.hypot(pt[0] - start[0], pt[1] - start[1])
            x, y = pt
            x1, y1 = start
            x2, y2 = end
            num = abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1)
            den = math.hypot(y2 - y1, x2 - x1)
            return num / den if den else 0.0

        def rdp(pts):
            if len(pts) <= 2:
                return pts
            start, end = pts[0], pts[-1]
            max_dist, max_idx = 0.0, 0
            for i in range(1, len(pts) - 1):
                d = perpendicular_distance(pts[i], start, end)
                if d > max_dist:
                    max_dist, max_idx = d, i
            if max_dist > tolerance:
                left = rdp(pts[: max_idx + 1])
                right = rdp(pts[max_idx:])
                return left[:-1] + right
            return [start, end]

        simplified = rdp(points)
        if simplified[0] != simplified[-1]:
            simplified.append(simplified[0])
        return simplified if len(simplified) >= 4 else points

    @staticmethod
    def point_in_polygon(lat: float, lon: float, rings: list[list[list[float]]]) -> bool:
        """Ray-casting point-in-polygon test against an Esri-style rings geometry
        (list of [lon, lat] rings; first ring outer, rest holes)."""
        inside = False
        for ring in rings:
            n = len(ring)
            j = n - 1
            ring_inside = False
            for i in range(n):
                xi, yi = ring[i][0], ring[i][1]
                xj, yj = ring[j][0], ring[j][1]
                if ((yi > lat) != (yj > lat)) and (
                    lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-15) + xi
                ):
                    ring_inside = not ring_inside
                j = i
            if ring_inside:
                inside = not inside
        return inside

    @staticmethod
    def convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
        """Andrew's monotone-chain convex hull. points = [(lon, lat), ...]."""
        pts = sorted(set(points))
        if len(pts) <= 2:
            return pts

        def cross(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

        lower: list[tuple[float, float]] = []
        for p in pts:
            while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
                lower.pop()
            lower.append(p)
        upper: list[tuple[float, float]] = []
        for p in reversed(pts):
            while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
                upper.pop()
            upper.append(p)
        return lower[:-1] + upper[:-1]
