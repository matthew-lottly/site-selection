"""Step 29: publish statistical-rigor metrics required for executive review.

Outputs:
  - data/processed/statistical_rigor.csv
  - data/processed/statistical_rigor_folds.csv

Metrics included:
  - Global Moran's I on residuals from a tract-level OLS model of gap_score
  - Permutation p-value for Moran's I (2-sided)
  - Spatial block cross-validation (grid-block holdouts): RMSE and R^2
  - In-sample OLS RMSE and R^2 for context
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import requests

from lib import HEADERS, OSRM, PROCESSED, RAW, haversine_miles


def load_rows(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def osrm_drive_minutes(site_lat: float, site_lon: float, target_lat: float, target_lon: float, cache_key: str) -> float | None:
    safe_key = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in cache_key)
    cache_path = RAW / f"osrm_competitor_{safe_key}.json"
    if cache_path.exists():
        data = json.loads(cache_path.read_text(encoding="utf-8"))
    else:
        url = f"{OSRM}/route/v1/driving/{site_lon:.6f},{site_lat:.6f};{target_lon:.6f},{target_lat:.6f}"
        resp = requests.get(url, params={"overview": "false"}, headers=HEADERS, timeout=25)
        if resp.status_code != 200:
            return None
        data = resp.json()
        cache_path.write_text(json.dumps(data), encoding="utf-8")

    routes = data.get("routes") or []
    if not routes:
        return None
    secs = routes[0].get("duration")
    if secs is None:
        return None
    return float(secs) / 60.0


def fit_ols(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    return beta


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    sse = float(np.sum((y_true - y_pred) ** 2))
    sst = float(np.sum((y_true - np.mean(y_true)) ** 2))
    if sst == 0:
        return 0.0
    return 1.0 - (sse / sst)


def build_knn_weights(coords: np.ndarray, k: int = 8) -> np.ndarray:
    n = len(coords)
    weights = np.zeros((n, n), dtype=float)
    for i in range(n):
        dlat = coords[:, 0] - coords[i, 0]
        dlon = coords[:, 1] - coords[i, 1]
        dist2 = dlat * dlat + dlon * dlon
        order = np.argsort(dist2)
        neighbors = [idx for idx in order if idx != i][:k]
        weights[i, neighbors] = 1.0
    return weights


def morans_i(values: np.ndarray, weights: np.ndarray) -> float:
    z = values - np.mean(values)
    n = len(z)
    w_sum = float(np.sum(weights))
    if w_sum == 0:
        return 0.0
    num = float(z @ weights @ z)
    den = float(np.sum(z * z))
    if den == 0:
        return 0.0
    return (n / w_sum) * (num / den)


def permutation_pvalue(values: np.ndarray, weights: np.ndarray, observed: float, n_perm: int = 199) -> float:
    rng = np.random.default_rng(42)
    extreme = 0
    for _ in range(n_perm):
        perm = rng.permutation(values)
        score = morans_i(perm, weights)
        if abs(score) >= abs(observed):
            extreme += 1
    return (extreme + 1) / (n_perm + 1)


def spatial_blocks(lat: np.ndarray, lon: np.ndarray, n_bins: int = 4) -> np.ndarray:
    lat_edges = np.linspace(float(np.min(lat)), float(np.max(lat)), n_bins + 1)
    lon_edges = np.linspace(float(np.min(lon)), float(np.max(lon)), n_bins + 1)
    lat_idx = np.clip(np.digitize(lat, lat_edges[1:-1], right=False), 0, n_bins - 1)
    lon_idx = np.clip(np.digitize(lon, lon_edges[1:-1], right=False), 0, n_bins - 1)
    return lat_idx * n_bins + lon_idx


def main() -> None:
    rows = load_rows(PROCESSED / "houston_tracts.csv")

    x_data = []
    y_data = []
    lat = []
    lon = []

    for r in rows:
        try:
            pop = float(r["population"])
            mhi = float(r["median_hh_income"])
            pov = float(r["poverty_rate"])
            nearest = float(r["nearest_dollar_store_mi"])
            area = float(r["aland_sqmi"])
            gap = float(r["gap_score"])
            if area <= 0:
                continue
        except (TypeError, ValueError, KeyError):
            continue

        density = pop / area
        # Spatial trend terms capture broad geographic structure so residual
        # clustering reflects less omitted spatial signal.
        lat0 = float(r["lat"]) - 29.75
        lon0 = float(r["lon"]) + 95.40
        x_data.append([
            1.0,
            np.log1p(pop),
            np.log1p(max(mhi, 0.0)),
            pov,
            nearest,
            np.log1p(density),
            lat0,
            lon0,
            lat0 * lat0,
            lon0 * lon0,
            lat0 * lon0,
        ])
        y_data.append(gap)
        lat.append(float(r["lat"]))
        lon.append(float(r["lon"]))

    x = np.asarray(x_data, dtype=float)
    y = np.asarray(y_data, dtype=float)
    lat_arr = np.asarray(lat, dtype=float)
    lon_arr = np.asarray(lon, dtype=float)

    beta = fit_ols(x, y)
    y_hat = x @ beta
    residuals = y - y_hat

    ins_rmse = rmse(y, y_hat)
    ins_r2 = r2(y, y_hat)

    coords = np.column_stack([lat_arr, lon_arr])
    w = build_knn_weights(coords, k=8)
    i_obs = morans_i(residuals, w)
    i_expected = -1.0 / (len(residuals) - 1)
    i_p = permutation_pvalue(residuals, w, i_obs, n_perm=199)

    block_ids = spatial_blocks(lat_arr, lon_arr, n_bins=4)
    unique_blocks = sorted(set(int(v) for v in block_ids.tolist()))

    fold_rows: list[dict] = []
    rmse_vals = []
    r2_vals = []

    for block in unique_blocks:
        test_mask = block_ids == block
        train_mask = ~test_mask
        n_test = int(np.sum(test_mask))
        n_train = int(np.sum(train_mask))

        if n_test < 8 or n_train < 80:
            continue

        beta_fold = fit_ols(x[train_mask], y[train_mask])
        pred = x[test_mask] @ beta_fold
        y_test = y[test_mask]

        fold_rmse = rmse(y_test, pred)
        fold_r2 = r2(y_test, pred)
        rmse_vals.append(fold_rmse)
        r2_vals.append(fold_r2)

        fold_rows.append(
            {
                "block_id": str(block),
                "n_test": str(n_test),
                "rmse": f"{fold_rmse:.3f}",
                "r2": f"{fold_r2:.3f}",
            }
        )

    if not rmse_vals:
        raise RuntimeError("Spatial CV produced no valid folds; adjust fold thresholds.")

    cv_rmse_mean = float(np.mean(rmse_vals))
    cv_rmse_std = float(np.std(rmse_vals))
    cv_r2_mean = float(np.mean(r2_vals))
    cv_r2_std = float(np.std(r2_vals))

    scorecard = load_rows(PROCESSED / "scorecard.csv")
    sites = {r["hcad_num"]: r for r in load_rows(PROCESSED / "sites_enriched.csv")}
    competitors = load_rows(PROCESSED / "competitors.csv")
    winner = next(r for r in scorecard if r.get("primary_recommendation") == "True")
    winner_site = sites[winner["hcad_num"]]
    wlat = float(winner_site["lat"])
    wlon = float(winner_site["lon"])

    arch = [c for c in competitors if c.get("category") == "arch_rival"]
    nearest_arch = min(
        arch,
        key=lambda c: haversine_miles(wlat, wlon, float(c["lat"]), float(c["lon"])),
    )
    nearest_arch_mi = haversine_miles(wlat, wlon, float(nearest_arch["lat"]), float(nearest_arch["lon"]))
    nearest_arch_drive_min = osrm_drive_minutes(
        wlat,
        wlon,
        float(nearest_arch["lat"]),
        float(nearest_arch["lon"]),
        f"{winner['hcad_num']}_{nearest_arch.get('osm_id', 'rival')}",
    )

    summary = [
        {
            "metric": "moran_i_residuals",
            "value": f"{i_obs:.4f}",
            "benchmark": "Near 0.0",
            "status": "Pass" if abs(i_obs) <= 0.10 else "Watch",
            "notes": "Global Moran's I on tract-model residuals using 8-nearest-neighbor weights.",
        },
        {
            "metric": "moran_i_expected",
            "value": f"{i_expected:.4f}",
            "benchmark": "Approx. null expectation",
            "status": "Info",
            "notes": "Expected Moran's I under spatial randomness.",
        },
        {
            "metric": "moran_i_permutation_pvalue",
            "value": f"{i_p:.4f}",
            "benchmark": ">= 0.05 preferred",
            "status": "Pass" if i_p >= 0.05 else "Watch",
            "notes": "Two-sided permutation p-value (199 permutations, fixed seed).",
        },
        {
            "metric": "spatial_block_cv_rmse_mean",
            "value": f"{cv_rmse_mean:.3f}",
            "benchmark": "Lower is better",
            "status": "Info",
            "notes": "Leave-one-spatial-block-out RMSE across valid folds.",
        },
        {
            "metric": "spatial_block_cv_r2_mean",
            "value": f"{cv_r2_mean:.3f}",
            "benchmark": "> 0 preferred",
            "status": "Pass" if cv_r2_mean > 0 else "Watch",
            "notes": "Leave-one-spatial-block-out R^2 across valid folds.",
        },
        {
            "metric": "spatial_block_cv_r2_std",
            "value": f"{cv_r2_std:.3f}",
            "benchmark": "Lower is more stable",
            "status": "Info",
            "notes": "Fold-to-fold variability in out-of-sample R^2.",
        },
        {
            "metric": "spatial_block_cv_n_folds",
            "value": str(len(rmse_vals)),
            "benchmark": ">= 6 preferred",
            "status": "Pass" if len(rmse_vals) >= 6 else "Watch",
            "notes": "Number of spatial holdout folds used.",
        },
        {
            "metric": "ols_in_sample_rmse",
            "value": f"{ins_rmse:.3f}",
            "benchmark": "Context only",
            "status": "Info",
            "notes": "In-sample fit for the tract-level OLS model.",
        },
        {
            "metric": "ols_in_sample_r2",
            "value": f"{ins_r2:.3f}",
            "benchmark": "Context only",
            "status": "Info",
            "notes": "In-sample R^2 for the tract-level OLS model.",
        },
        {
            "metric": "winner_nearest_arch_rival_distance_mi",
            "value": f"{nearest_arch_mi:.2f}",
            "benchmark": "> 1.5 mi preferred",
            "status": "Pass" if nearest_arch_mi > 1.5 else "Watch",
            "notes": f"Winner's nearest direct arch-rival ({nearest_arch.get('name', 'arch-rival')}).",
        },
        {
            "metric": "winner_nearest_arch_rival_drive_time_min",
            "value": f"{nearest_arch_drive_min:.1f}" if nearest_arch_drive_min is not None else "n/a",
            "benchmark": "> 5 min preferred",
            "status": "Pass" if nearest_arch_drive_min is not None and nearest_arch_drive_min > 5 else ("Watch" if nearest_arch_drive_min is not None else "Info"),
            "notes": "Winner-to-nearest-arch-rival OSRM network drive time.",
        },
    ]

    summary_path = PROCESSED / "statistical_rigor.csv"
    with open(summary_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)

    fold_path = PROCESSED / "statistical_rigor_folds.csv"
    with open(fold_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["block_id", "n_test", "rmse", "r2"])
        writer.writeheader()
        writer.writerows(fold_rows)

    print(f"Wrote {summary_path}")
    print(f"Wrote {fold_path}")


if __name__ == "__main__":
    main()
