---
name: chaos-takens-workflow
description: Reconstruct 3D Strange Attractors via Takens' Delay-Embedding Theorem, compute Rosenstein Lyapunov predictability horizons, and prove nonlinear X->Y causality via Sugihara CCM.
---
# Chaos Takens Manifold Nonlinear Dynamics Workflow
Whenever analyzing time series, server tail latencies, market spreads, or multi-column telemetry logs:
1. Call `chaos_takens_reconstruct` to compute the delay-coordinate shadow manifold `M_x`, Largest Lyapunov Exponent `lambda_1`, and predictability horizon `T_max`. Never extrapolate point forecasts past `T_max`.
2. Call `chaos_takens_ccm_causality` to compare linear Pearson correlation `r_XY` against nonlinear Sugihara CCM skill `rho(X -> Y)`.
3. Emit a standalone paragraph `::chaos-takens{lambda_1="..." horizon="..." regime="..."}` to mount the 3D phase-space attractor in Hermes Desktop.
