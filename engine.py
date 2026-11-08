"""Takens delay-coordinate embedding, Rosenstein Largest Lyapunov Exponent, and Sugihara CCM engine."""

from __future__ import annotations

import json
import math
from typing import Any, Dict, List, Optional

import numpy as np
from scipy.spatial import cKDTree

try:
    from hermes_cli.plugin_events import emit_plugin_event
except ImportError:
    def emit_plugin_event(plugin_name: str, event_type: str, payload: Dict[str, Any]) -> None:
        pass


LAST_TAKENS_CACHE: Dict[str, Any] = {}


def delay_embed(series: np.ndarray, m: int, tau: int) -> np.ndarray:
    """Construct Takens delay-coordinate matrix M_x of shape (N - (m-1)*tau, m)."""
    x = np.asarray(series, dtype=float).ravel()
    n = len(x)
    n_vecs = n - (m - 1) * tau
    if n_vecs <= m + 2:
        raise ValueError(f"Time series length {n} is too short for m={m}, tau={tau}")
    indices = np.arange(n_vecs)[:, None] + np.arange(m)[None, :] * tau
    return x[indices]


def select_optimal_tau_ami(series: np.ndarray, max_tau: int = 15, n_bins: int = 12) -> int:
    """Select first local minimum of Average Mutual Information I(tau) for delay embedding."""
    x = np.asarray(series, dtype=float).ravel()
    if len(x) < 32:
        return 1
    prev_mi = float("inf")
    for tau in range(1, min(max_tau, len(x) // 4) + 1):
        x0 = x[:-tau]
        x1 = x[tau:]
        hist_2d, _, _ = np.histogram2d(x0, x1, bins=n_bins)
        pxy = hist_2d / np.sum(hist_2d)
        px = np.sum(pxy, axis=1, keepdims=True)
        py = np.sum(pxy, axis=0, keepdims=True)
        nz = pxy > 0
        mi = float(np.sum(pxy[nz] * np.log(pxy[nz] / (px @ py)[nz])))
        if mi > prev_mi:
            return max(1, tau - 1)
        prev_mi = mi
    return 2


def rosenstein_largest_lyapunov(
    manifold: np.ndarray, dt: float = 1.0, theiler_window: int = 4, max_steps: int = 12
) -> Dict[str, float]:
    """
    Estimate the Largest Lyapunov Exponent lambda_1 via Rosenstein's algorithm (1993):
    1. Locate nearest neighbor j^ for each state i on the reconstructed manifold M_x
       subject to temporal separation |i - j^| > theiler_window.
    2. Track mean logarithmic divergence y(k) = <ln ||x_{i+k} - x_{j^+k}||_2> over k = 1..max_steps.
    3. Estimate lambda_1 as the least-squares slope of y(k) vs k*dt.
    """
    n_pts = len(manifold)
    k_steps = min(max_steps, max(4, n_pts // 5))
    usable = n_pts - k_steps
    if usable <= theiler_window + 2:
        theiler_window = 1

    tree = cKDTree(manifold[:usable])
    # Query k neighbors and pick the first outside the Theiler window
    dists, idxs = tree.query(manifold[:usable], k=min(usable, 2 * theiler_window + 6))

    nn_indices = np.full(usable, -1, dtype=int)
    initial_seps: List[float] = []
    for i in range(usable):
        row_idxs = np.atleast_1d(idxs[i])
        row_dists = np.atleast_1d(dists[i])
        for cand_idx, cand_d in zip(row_idxs, row_dists):
            if abs(int(cand_idx) - i) > theiler_window and cand_d > 1e-12:
                nn_indices[i] = int(cand_idx)
                initial_seps.append(float(cand_d))
                break

    valid_i = np.where(nn_indices >= 0)[0]
    if len(valid_i) < 4:
        return {"lambda_1": 0.0, "predictability_horizon_steps": float("inf")}

    mean_log_div = np.zeros(k_steps, dtype=float)
    for k in range(k_steps):
        p1 = manifold[valid_i + k]
        p2 = manifold[nn_indices[valid_i] + k]
        sep = np.linalg.norm(p1 - p2, axis=1)
        mean_log_div[k] = float(np.mean(np.log(np.maximum(sep, 1e-12))))

    t_axis = np.arange(k_steps, dtype=float) * float(dt)
    slope, _ = np.polyfit(t_axis, mean_log_div, 1)
    lambda_1 = float(slope)

    manifold_diameter = float(np.max(np.ptp(manifold, axis=0)))
    eps_0 = float(np.median(initial_seps)) if initial_seps else 1e-2
    if lambda_1 > 1e-4:
        t_max = (1.0 / lambda_1) * math.log(max(1.5, manifold_diameter / max(eps_0, 1e-6)))
    else:
        t_max = float("inf")

    return {
        "lambda_1": round(lambda_1, 5),
        "predictability_horizon_steps": round(t_max, 2) if math.isfinite(t_max) else 9999.0,
    }


def handle_takens_reconstruct(args: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
    """
    Reconstruct the phase-space shadow manifold of a 1D time series using Takens' Theorem,
    compute the Rosenstein Largest Lyapunov Exponent lambda_1, and classify the dynamical regime.
    """
    raw_series = args.get("series")
    if not raw_series:
        # Default: Chaotic logistic map r=3.99 trajectory if none provided
        x_val = 0.21
        raw_series = []
        for _ in range(160):
            x_val = 3.99 * x_val * (1.0 - x_val)
            raw_series.append(x_val)

    series = np.asarray(raw_series, dtype=float).ravel()
    m = int(args.get("embedding_dim", 3))
    tau_arg = args.get("tau")
    tau = int(tau_arg) if tau_arg is not None else select_optimal_tau_ami(series)
    dt = float(args.get("dt", 1.0))

    manifold = delay_embed(series, m=m, tau=tau)
    lyap = rosenstein_largest_lyapunov(manifold, dt=dt)
    lam1 = lyap["lambda_1"]

    if lam1 > 0.015:
        regime = "CHAOTIC_STRANGE_ATTRACTOR"
    elif lam1 < -0.015:
        regime = "DISSIPATIVE_STABLE_FIXED_POINT"
    else:
        regime = "QUASI_PERIODIC_LIMIT_CYCLE"

    # Project 2D phase portrait coordinates (x(t), x(t-tau)) for inline SVG card
    pts_2d = [[round(float(row[0]), 3), round(float(row[1]), 3)] for row in manifold[:28]]

    result = {
        "status": "ok",
        "series_length": len(series),
        "embedding_dimension_m": m,
        "optimal_delay_tau": tau,
        "manifold_points": len(manifold),
        "largest_lyapunov_exponent": lam1,
        "predictability_horizon_steps": lyap["predictability_horizon_steps"],
        "dynamical_regime": regime,
        "phase_portrait_2d": pts_2d,
        "transcript_directive": "::chaos-takens " + json.dumps({"regime": regime, "lambda_1": lam1, "horizon": lyap["predictability_horizon_steps"], "m": m, "tau": tau, "pts": pts_2d[:16]}),
    }
    LAST_TAKENS_CACHE["latest"] = result
    emit_plugin_event("chaos-takens", "manifold_reconstructed", result)
    return result


def _ccm_cross_map_skill(source_x: np.ndarray, target_y: np.ndarray, m: int, tau: int, lib_len: int) -> float:
    """
    Sugihara Convergent Cross Mapping (CCM):
    Use simplex projection weights on shadow manifold M_Y (of library length lib_len)
    to reconstruct X(t). If X causally drives Y (X -> Y), M_Y contains X's dynamical
    footprint and cross-map skill rho(X, X^|M_Y) converges upward with lib_len.
    """
    my = delay_embed(target_y, m=m, tau=tau)
    x_aligned = source_x[(m - 1) * tau :]
    n_total = len(my)
    L = min(lib_len, n_total)
    my_lib = my[:L]
    x_lib = x_aligned[:L]

    tree = cKDTree(my_lib)
    k_nn = min(m + 2, L)
    dists, idxs = tree.query(my_lib, k=k_nn)

    x_hat = np.zeros(L, dtype=float)
    for i in range(L):
        # Exclude self (index 0 in query result)
        d_neighbors = dists[i, 1:]
        idx_neighbors = idxs[i, 1:]
        d_min = max(float(d_neighbors[0]), 1e-12)
        weights = np.exp(-d_neighbors / d_min)
        w_sum = float(np.sum(weights))
        if w_sum > 1e-12:
            weights = weights / w_sum
        else:
            weights = np.ones_like(weights) / len(weights)
        x_hat[i] = float(np.dot(weights, x_lib[idx_neighbors]))

    if np.std(x_lib) < 1e-12 or np.std(x_hat) < 1e-12:
        return 0.0
    corr = float(np.corrcoef(x_lib, x_hat)[0, 1])
    return max(0.0, corr)


def handle_takens_ccm_causality(args: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
    """
    Run Sugihara Convergent Cross Mapping (CCM) between time series X and Y across
    increasing library sizes L to test true nonlinear dynamical causation (X -> Y vs Y -> X).
    """
    x_raw = args.get("series_x")
    y_raw = args.get("series_y")

    if not x_raw or not y_raw:
        # Coupled nonlinear system where X drives Y unidirectionally (X -> Y), beta_yx > 0, beta_xy = 0
        n_pts = 160
        x_arr = np.zeros(n_pts)
        y_arr = np.zeros(n_pts)
        x_arr[0], y_arr[0] = 0.2, 0.4
        for t in range(n_pts - 1):
            x_arr[t + 1] = x_arr[t] * (3.8 - 3.8 * x_arr[t])
            y_arr[t + 1] = y_arr[t] * (3.5 - 3.5 * y_arr[t] - 0.35 * x_arr[t])
    else:
        x_arr = np.asarray(x_raw, dtype=float).ravel()
        y_arr = np.asarray(y_raw, dtype=float).ravel()

    m = int(args.get("embedding_dim", 3))
    tau = int(args.get("tau", 1))
    n_eff = len(x_arr) - (m - 1) * tau
    lib_sizes = [max(m + 6, int(n_eff * frac)) for frac in (0.25, 0.50, 0.75, 1.0)]

    # Cross-mapping X from M_Y tests whether X causally drives Y (X -> Y)
    skill_x_causes_y = [round(_ccm_cross_map_skill(x_arr, y_arr, m, tau, L), 4) for L in lib_sizes]
    # Cross-mapping Y from M_X tests whether Y causally drives X (Y -> X)
    skill_y_causes_x = [round(_ccm_cross_map_skill(y_arr, x_arr, m, tau, L), 4) for L in lib_sizes]

    rho_xy = skill_x_causes_y[-1]
    rho_yx = skill_y_causes_x[-1]
    conv_xy = skill_x_causes_y[-1] - skill_x_causes_y[0]
    conv_yx = skill_y_causes_x[-1] - skill_y_causes_x[0]

    if rho_xy > 0.55 and (rho_xy - rho_yx) > 0.15:
        direction = "X_CAUSES_Y"
    elif rho_yx > 0.55 and (rho_yx - rho_xy) > 0.15:
        direction = "Y_CAUSES_X"
    elif rho_xy > 0.55 and rho_yx > 0.55:
        direction = "BIDIRECTIONAL_COUPLING"
    else:
        direction = "NO_DYNAMICAL_CAUSATION"

    return {
        "status": "ok",
        "linear_pearson_r": round(float(np.corrcoef(x_arr[:len(y_arr)], y_arr[:len(x_arr)])[0, 1]), 4),
        "nonlinear_vs_linear_advantage": round(float(rho_xy - abs(np.corrcoef(x_arr[:len(y_arr)], y_arr[:len(x_arr)])[0, 1])), 4),
        "causal_direction": direction,
        "library_sizes": lib_sizes,
        "ccm_skill_x_causes_y": skill_x_causes_y,
        "ccm_skill_y_causes_x": skill_y_causes_x,
        "terminal_rho_x_causes_y": rho_xy,
        "terminal_rho_y_causes_x": rho_yx,
        "convergence_gain_x_causes_y": round(conv_xy, 4),
        "convergence_gain_y_causes_x": round(conv_yx, 4),
    }


TAKENS_RECONSTRUCT_SCHEMA: Dict[str, Any] = {
    "name": "chaos_takens_reconstruct",
    "description": (
        "Embed a 1D time series into an m-dimensional shadow manifold via Takens' Delay-Embedding Theorem, "
        "compute the Rosenstein Largest Lyapunov Exponent lambda_1, and derive the exact predictability horizon T_max."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "series": {
                "type": "array",
                "items": {"type": "number"},
                "description": "1D scalar time series observations.",
            },
            "embedding_dim": {"type": "integer", "description": "Embedding dimension m (default 3)."},
            "tau": {"type": "integer", "description": "Optional time delay tau (auto-selected via AMI if omitted)."},
        },
    },
}

TAKENS_CCM_SCHEMA: Dict[str, Any] = {
    "name": "chaos_takens_ccm_causality",
    "description": (
        "Test nonlinear directional causality (X -> Y vs Y -> X) between two coupled time series using "
        "Sugihara Convergent Cross Mapping (CCM) on reconstructed shadow manifolds."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "series_x": {"type": "array", "items": {"type": "number"}, "description": "Time series X."},
            "series_y": {"type": "array", "items": {"type": "number"}, "description": "Time series Y."},
            "embedding_dim": {"type": "integer", "description": "Embedding dimension m (default 3)."},
            "tau": {"type": "integer", "description": "Lag step tau (default 1)."},
        },
    },
}


def _ensure_json_str(res: Any) -> str:
    if isinstance(res, str):
        return res
    return json.dumps(res)
