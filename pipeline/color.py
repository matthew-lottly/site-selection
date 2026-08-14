"""Validated map color palettes (dataviz skill, references/palette.md) and the
ramp-interpolation helper used to symbolize choropleths and rank badges.
"""
from __future__ import annotations


class ColorRamp:
    # magnitude ramp, light->dark: tract opportunity-score choropleth
    SEQUENTIAL_BLUE = [
        "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b",
    ]
    # magnitude ramp, light->dark: alternate choropleth hue (categorical slot 2)
    SEQUENTIAL_ORANGE = [
        "#fde3d3", "#fbc9a3", "#f5a56a", "#eb6834", "#c94f20", "#a13d16", "#7a2d0f",
    ]
    # ordered good->critical: "best to worst ranked" site symbology
    STATUS_RAMP = ["#0ca30c", "#fab219", "#ec835a", "#d03b3b"]

    # Competitor-tier colors: deliberately all cool hues (blue/violet/magenta/aqua),
    # never green/yellow/orange/red, so they never get confused with the warm
    # STATUS_RAMP (candidate-site rank) or SEQUENTIAL_ORANGE (choropleth) markers
    # sharing the same map. Validated distinct via the dataviz skill's
    # validate_palette.js (light mode, all-pairs): PASS on lightness/chroma/normal-
    # vision floors, WARN (not FAIL) on CVD separation -- acceptable per the skill's
    # own rule because every one of these colors also carries a text legend/tooltip
    # label (the required secondary encoding for a 6-8 dE pair).
    COMPETITOR_COLORS = {
        "family_dollar": "#2a78d6",    # blue -- own network, not a competitor
        "arch_rival": "#e87ba4",       # magenta -- the real competitive threat (Dollar General, Five Below, Dollar Tree)
        "value_grocery": "#1baf7a",    # aqua -- extreme-value grocery competition
        "big_box_anchor": "#57534e",   # muted stone -- lowest priority, context only
    }

    @staticmethod
    def _hex_to_rgb(h: str) -> tuple[int, int, int]:
        h = h.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    @staticmethod
    def _rgb_to_hex(rgb: tuple[float, float, float]) -> str:
        return "#{:02x}{:02x}{:02x}".format(*(max(0, min(255, round(c))) for c in rgb))

    @classmethod
    def interpolate(cls, t: float, stops: list[str]) -> str:
        """t in [0,1] -> interpolated hex color across an ordered list of hex stops."""
        t = max(0.0, min(1.0, t))
        n = len(stops) - 1
        pos = t * n
        i = min(int(pos), n - 1)
        frac = pos - i
        c0, c1 = cls._hex_to_rgb(stops[i]), cls._hex_to_rgb(stops[i + 1])
        return cls._rgb_to_hex(tuple(c0[k] + (c1[k] - c0[k]) * frac for k in range(3)))
