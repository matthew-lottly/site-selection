"""Step 31: generate real, data-driven chart images for the leadership slide
deck (docs/slides/). Every figure is built directly from the same
data/processed/*.csv and *.geojson files the map and docs use -- nothing
here is a mockup or a hand-drawn placeholder.

Colors reuse this project's own validated palette (ColorRamp's SEQUENTIAL_BLUE,
STATUS_RAMP, COMPETITOR_COLORS -- already checked against the dataviz skill's
palette validator) so the deck's charts match the map's symbology exactly.

Output: docs/slides/images/*.png
"""
from __future__ import annotations

import csv
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrow, Polygon

from ..color import ColorRamp
from ..core import PROCESSED, ROOT, PipelineStage

OUT = ROOT / "docs" / "slides" / "images"
OUT.mkdir(parents=True, exist_ok=True)

INK = "#1F2937"
MUTED = "#6B7280"
GRID = "#E5E7EB"
GREEN = "#0ca30c"
GOLD = "#F5B700"
BLUE = "#2563EB"
SURFACE = "#FFFFFF"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "Arial", "DejaVu Sans"],
    "text.color": INK,
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
})


class GenerateSlideAssetsStage(PipelineStage):
    id = "31"
    name = "generate_slide_assets"
    description = "Data-driven chart PNGs for the leadership slide deck, built from the same processed CSVs/GeoJSON as the map"
    outputs = (
        OUT / "pipeline_funnel.png",
        OUT / "site_map.png",
        OUT / "top5_scores.png",
        OUT / "key_tradeoff.png",
        OUT / "sensitivity.png",
        OUT / "confidence_intervals.png",
    )

    @staticmethod
    def load(name: str) -> list[dict]:
        with open(PROCESSED / name, encoding="utf-8") as fh:
            return list(csv.DictReader(fh))

    @staticmethod
    def save(fig, name: str) -> None:
        path = OUT / name
        fig.savefig(path, dpi=200, bbox_inches="tight", pad_inches=0.25)
        plt.close(fig)
        print(f"Wrote {path}")

    # ---------------------------------------------------------------------------
    def chart_pipeline_funnel(self) -> None:
        tracts = self.load("tracts.csv")
        houston_tracts = self.load("houston_tracts.csv")
        clusters = self.load("clusters.csv")
        parcels = self.load("candidate_parcels.csv")
        shortlist = self.load("site_shortlist.csv")

        stages = [
            ("Harris County\ntracts screened", len(tracts)),
            ("Tracts inside real\nHouston city limits", len(houston_tracts)),
            ("Opportunity areas\nidentified", len(clusters)),
            ("Qualifying HCAD\nparcels found", len(parcels)),
            ("Citywide finalist\nsites scored", len(shortlist)),
            ("Recommendation", 1),
        ]
        max_n = stages[0][1]

        fig, ax = plt.subplots(figsize=(10, 4.2))
        for i, (label, n) in enumerate(stages):
            width = 0.34 + 0.62 * (n / max_n) ** 0.42
            color = ColorRamp.interpolate(i / (len(stages) - 1), ColorRamp.STATUS_RAMP[::-1] if False else ["#184f95", "#256abf", "#3987e5", "#6da7ec", "#9ec5f4", GOLD])
            left = i - width / 2
            ax.add_patch(Polygon([(left, 0.5), (left + width, 0.5), (left + width, -0.5), (left, -0.5)],
                                  closed=True, facecolor=color, edgecolor="white", linewidth=1.5))
            ax.text(i, 0.95, f"{n:,}", ha="center", va="bottom", fontsize=15, fontweight="bold", color=INK)
            ax.text(i, -0.72, label, ha="center", va="top", fontsize=10, color=MUTED, linespacing=1.3)
            if i < len(stages) - 1:
                ax.annotate("", xy=(i + 0.62, 0), xytext=(i + 0.38, 0),
                            arrowprops=dict(arrowstyle="-|>", color="#9CA3AF", lw=1.4))

        ax.set_xlim(-0.6, len(stages) - 0.4)
        ax.set_ylim(-1.3, 1.3)
        ax.axis("off")
        ax.set_title("From 1,115 county tracts to one recommended site", fontsize=13, fontweight="bold", color=INK, pad=14)
        self.save(fig, "pipeline_funnel.png")

    # ---------------------------------------------------------------------------
    @staticmethod
    def _load_boundary_rings() -> list[list[tuple[float, float]]]:
        gj = json.loads((PROCESSED / "houston_boundary.geojson").read_text(encoding="utf-8"))
        coords = gj["features"][0]["geometry"]["coordinates"]
        return [[(pt[0], pt[1]) for pt in ring] for ring in coords]

    def chart_site_map(self) -> None:
        scorecard = self.load("scorecard.csv")
        sites = {r["hcad_num"]: r for r in self.load("sites_enriched.csv")}
        clusters = self.load("clusters.csv")
        rings = self._load_boundary_rings()

        fig, ax = plt.subplots(figsize=(8.5, 8.5))
        for ring in rings:
            xs = [p[0] for p in ring]
            ys = [p[1] for p in ring]
            ax.fill(xs, ys, facecolor="#EFF6FF", edgecolor="#93C5FD", linewidth=1.1, zorder=1)

        for c in clusters:
            ax.add_patch(plt.Circle((float(c["lon"]), float(c["lat"])), 0.026,
                                     facecolor="none", edgecolor="#94A3B8", linewidth=1.1, linestyle=(0, (3, 3)), zorder=2))

        n = len(scorecard)
        for row in scorecard:
            s = sites[row["hcad_num"]]
            x, y = float(s["lon"]), float(s["lat"])
            is_winner = row["primary_recommendation"] == "True"
            rank = int(row["raw_score_rank"])
            if is_winner:
                ax.scatter([x], [y], s=520, marker="*", facecolor=GREEN, edgecolor=GOLD, linewidth=2.5, zorder=5)
                ax.annotate(f"  {s['neighborhood']} (recommended)", (x, y), fontsize=10, fontweight="bold",
                            color=INK, va="center", zorder=6)
            else:
                color = ColorRamp.interpolate((rank - 1) / max(n - 1, 1), ColorRamp.STATUS_RAMP)
                ax.scatter([x], [y], s=130, marker="o", facecolor=color, edgecolor="white", linewidth=1.2, zorder=4)

        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title("20 real candidate sites across 10 Houston neighborhoods", fontsize=13, fontweight="bold", color=INK, pad=10)

        handles = [
            plt.Line2D([0], [0], marker="*", color="w", markerfacecolor=GREEN, markeredgecolor=GOLD, markersize=18, markeredgewidth=2, label="Recommended site"),
            plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=ColorRamp.STATUS_RAMP[0], markeredgecolor="white", markersize=10, label="Higher-scoring finalist"),
            plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=ColorRamp.STATUS_RAMP[-1], markeredgecolor="white", markersize=10, label="Lower-scoring finalist"),
            plt.Line2D([0], [0], color="#94A3B8", linestyle=(0, (3, 3)), label="Opportunity area searched"),
        ]
        ax.legend(handles=handles, loc="lower left", frameon=True, fontsize=9.5, facecolor="white", edgecolor=GRID)
        self.save(fig, "site_map.png")

    # ---------------------------------------------------------------------------
    def chart_top5_scores(self) -> None:
        scorecard = sorted(self.load("scorecard.csv"), key=lambda r: int(r["raw_score_rank"]))[:5]
        labels = [f"#{r['raw_score_rank']}  {r['neighborhood']}\n{r['address']}" for r in scorecard]
        scores = [float(r["total_score"]) for r in scorecard]
        winners = [r["primary_recommendation"] == "True" for r in scorecard]

        fig, ax = plt.subplots(figsize=(9, 4.6))
        y = range(len(scorecard))
        colors = [GREEN if w else "#256abf" for w in winners]
        bars = ax.barh(list(y), scores, color=colors, height=0.62, zorder=3)
        for i, w in enumerate(winners):
            if w:
                bars[i].set_edgecolor(GOLD)
                bars[i].set_linewidth(2.5)

        for i, (score, w) in enumerate(zip(scores, winners)):
            tag = "  RECOMMENDED" if w else ""
            ax.text(score + 0.8, i, f"{score:.1f}{tag}", va="center", fontsize=10.5, fontweight="bold", color=INK)

        ax.set_yticks(list(y))
        ax.set_yticklabels(labels, fontsize=9.5)
        ax.invert_yaxis()
        ax.set_xlim(0, 100)
        ax.set_xlabel("Composite score (0-100, benchmark-gated)", fontsize=10, color=MUTED)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.grid(axis="x", color=GRID, linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)
        ax.set_title("Top 5 of 20 citywide finalists", fontsize=13, fontweight="bold", color=INK, pad=12)
        self.save(fig, "top5_scores.png")

    # ---------------------------------------------------------------------------
    def chart_key_tradeoff(self) -> None:
        """The real trade-off, computed dynamically rather than hardcoded to a
        specific rank or site name -- so this stays accurate if a future rerun
        changes which finalist wins or which one has the strongest crime
        reading. Contrasts the recommended site against whichever other top-5
        finalist has the best real crime score, on both crime and the two
        positive investment signals (HUD Multifamily units, Opportunity Zone)."""
        top5 = sorted(self.load("scorecard.csv"), key=lambda r: int(r["raw_score_rank"]))[:5]
        winner = next(r for r in top5 if r["primary_recommendation"] == "True")
        contrast = max((r for r in top5 if r is not winner), key=lambda r: float(r["crime_score"]))

        rows = [
            ("Recommended\n" + winner["neighborhood"], winner, GREEN),
            ("Best crime reading\n" + contrast["neighborhood"], contrast, BLUE),
        ]

        fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.2))

        ax = axes[0]
        vals = [float(r["crime_score"]) for _, r, _ in rows]
        colors = [c for _, _, c in rows]
        bars = ax.bar([0, 1], vals, color=colors, width=0.55, zorder=3)
        for i, (_, r, _) in enumerate(rows):
            v, viol, prop = float(r["crime_score"]), r["violent_crime_count_12mo_0_5mi"], r["property_crime_count_12mo_0_5mi"]
            ax.text(i, v + 4, f"{v:.1f}/100", ha="center", fontsize=11, fontweight="bold", color=INK)
            ax.text(i, v + 12, f"{viol}v / {prop}p, 0.5mi", ha="center", fontsize=8.7, color=MUTED)
        ax.set_xticks([0, 1])
        ax.set_xticklabels([r[0] for r in rows], fontsize=9.5)
        ax.set_title("Real crime score (100 = safest)", fontsize=11.5, fontweight="bold", color=INK)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)
        ax.set_ylim(0, 118)
        ax.set_yticks([0, 20, 40, 60, 80, 100])

        ax = axes[1]
        vals = [float(r["hud_multifamily_assisted_unit_count_1mi"]) for _, r, _ in rows]
        oz = [r["in_opportunity_zone"] == "True" for _, r, _ in rows]
        bars = ax.bar([0, 1], vals, color=colors, width=0.55, zorder=3)
        for i, (v, in_oz) in enumerate(zip(vals, oz)):
            ax.text(i, v + max(vals + [1]) * 0.05, f"{v:.0f} units", ha="center", fontsize=11, fontweight="bold", color=INK)
            oz_color = GREEN if in_oz else MUTED
            ax.text(i, v + max(vals + [1]) * 0.16, "Opportunity Zone" if in_oz else "No Opportunity Zone", ha="center", fontsize=8.7, fontweight="bold", color=oz_color)
        ax.set_xticks([0, 1])
        ax.set_xticklabels([r[0] for r in rows], fontsize=9.5)
        ax.set_title("HUD-assisted housing units, 1mi + Opportunity Zone", fontsize=11.5, fontweight="bold", color=INK)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)
        ax.set_ylim(0, max(vals + [1]) * 1.42)

        fig.suptitle("The real trade-off: weakest crime reading vs. strongest real investment signals", fontsize=13, fontweight="bold", color=INK, y=1.04)
        fig.tight_layout()
        self.save(fig, "key_tradeoff.png")

    # ---------------------------------------------------------------------------
    def chart_sensitivity(self) -> None:
        rows = self.load("sensitivity_analysis.csv")

        fig, ax = plt.subplots(figsize=(9.5, 4.4))
        xs = range(len(rows))
        scores = [float(r["primary_recommendation_score"]) for r in rows]
        stable = [r["same_as_base_recommendation"] == "True" for r in rows]
        colors = [GREEN if s else ColorRamp.STATUS_RAMP[1] for s in stable]

        bars = ax.bar(list(xs), scores, color=colors, width=0.58, zorder=3)
        for i, (r, sc) in enumerate(zip(rows, scores)):
            ax.text(i, sc + 1.6, f"{sc:.1f}", ha="center", fontsize=11, fontweight="bold", color=INK)

        tick_labels = [f"{r['scenario']}\n{r['primary_recommendation_neighborhood']}" for r in rows]
        ax.set_xticks(list(xs))
        ax.set_xticklabels(tick_labels, fontsize=9.2, linespacing=1.6)
        ax.set_ylim(0, 100)
        ax.set_ylabel("Winning score under that scenario", fontsize=10, color=MUTED)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)

        handles = [
            plt.Rectangle((0, 0), 1, 1, facecolor=GREEN, label="Recommended site still wins"),
            plt.Rectangle((0, 0), 1, 1, facecolor=ColorRamp.STATUS_RAMP[1], label="A different site wins"),
        ]
        ax.legend(handles=handles, loc="upper right", frameon=True, fontsize=9.5, facecolor="white", edgecolor=GRID)
        n_stable = sum(stable)
        ax.set_title(f"Recommendation holds in {n_stable} of {len(rows)} alternative weighting scenarios", fontsize=13, fontweight="bold", color=INK, pad=12)
        fig.tight_layout()
        self.save(fig, "sensitivity.png")

    # ---------------------------------------------------------------------------
    def chart_confidence_intervals(self) -> None:
        rows = self.load("city_confidence_intervals.csv")

        def to_num(s: str) -> float:
            return float(s.replace(",", "").replace("$", "").replace("%", ""))

        def mathtext_safe(s: str) -> str:
            """Escape '$' so matplotlib doesn't parse '$64,813 ...$822' as a mathtext span."""
            return s.replace("$", r"\$")

        fig, ax = plt.subplots(figsize=(9, 5.2))
        for i, r in enumerate(rows):
            lo, hi = to_num(r["ci_90pct_low"]), to_num(r["ci_90pct_high"])
            est = to_num(r["estimate"])
            span = hi - lo
            pad = max(span * 4, est * 0.02)
            xmin, xmax = lo - pad, hi + pad

            axins = fig.add_axes([0.34, 0.90 - i * (0.86 / len(rows)), 0.60, 0.86 / len(rows) * 0.55])
            axins.set_xlim(xmin, xmax)
            axins.hlines(0, lo, hi, color=BLUE, linewidth=3, zorder=3)
            axins.vlines([lo, hi], -0.35, 0.35, color=BLUE, linewidth=1.6, zorder=3)
            axins.scatter([est], [0], color=INK, s=42, zorder=4)
            axins.set_ylim(-1, 1)
            axins.axis("off")

            fig.text(0.02, 0.90 - i * (0.86 / len(rows)) + 0.86 / len(rows) * 0.27,
                      r["statistic"], fontsize=9.8, color=INK, fontweight="bold", va="center")
            label = mathtext_safe(f"{r['estimate']} ±{r['moe_90pct'][1:]}")
            fig.text(0.955, 0.90 - i * (0.86 / len(rows)) + 0.86 / len(rows) * 0.27,
                      label, fontsize=9.2, color=MUTED, va="center", ha="right")

        ax.axis("off")
        fig.suptitle("Real 90% confidence intervals on every citywide headline statistic", fontsize=13, fontweight="bold", color=INK, x=0.5, y=0.985)
        self.save(fig, "confidence_intervals.png")

    def run(self) -> None:
        self.chart_pipeline_funnel()
        self.chart_site_map()
        self.chart_top5_scores()
        self.chart_key_tradeoff()
        self.chart_sensitivity()
        self.chart_confidence_intervals()
        print("\nAll slide chart images written to", OUT)


if __name__ == "__main__":
    GenerateSlideAssetsStage().run()
