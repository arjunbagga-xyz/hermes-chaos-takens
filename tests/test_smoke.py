"""Smoke tests for chaos-takens."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import handle_takens_reconstruct, handle_takens_ccm_causality


def _logistic_series(n=160, r=3.99, x0=0.21):
    xs = []
    x = x0
    for _ in range(n):
        x = r * x * (1.0 - x)
        xs.append(x)
    return xs


def test_manifest_exists():
    assert True


def test_reconstruct_real_series():
    series = _logistic_series()
    r = handle_takens_reconstruct({"series": series})
    assert r["status"] == "ok"
    assert r["dynamical_regime"] == "CHAOTIC_STRANGE_ATTRACTOR"
    assert r["largest_lyapunov_exponent"] > 0.015
    assert r["predictability_horizon_steps"] > 0


def test_reconstruct_no_series_errors():
    r = handle_takens_reconstruct({})
    assert r["status"] == "error"
    assert "required" in r["error"]


def test_ccm_real_series():
    x = _logistic_series()
    y = [0.5 * v + 0.1 for v in x]  # y driven by x
    r = handle_takens_ccm_causality({"series_x": x, "series_y": y})
    assert r["status"] == "ok"
    assert r["causal_direction"] in ("X_CAUSES_Y", "BIDIRECTIONAL_COUPLING")


def test_ccm_no_series_errors():
    r = handle_takens_ccm_causality({})
    assert r["status"] == "error"
    assert "required" in r["error"]


def test_tool_wrapper_returns_json_str():
    src = (Path(__file__).resolve().parent.parent / "__init__.py").read_text()
    assert "_reconstruct_tool" in src and "_ccm_tool" in src
    assert "json.dumps(handle_takens_reconstruct" in src
    assert "json.dumps(handle_takens_ccm_causality" in src

