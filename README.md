# chaos-takens

**Chaos & Causal Manifold Reconstructor for Hermes Agent.**

Standard LLM data analysis treats 1D time series (server latencies, financial spreads, geophysical telemetry) with naive linear regressions or moving averages—failing completely on coupled nonlinear dynamical systems. `chaos-takens` brings **Takens' Delay-Embedding Theorem (1981)**, **Rosenstein's Largest Lyapunov Exponent ($\lambda_1$)**, and **Sugihara's Convergent Cross Mapping (CCM, 2012)** into Hermes:

1. **Phase-Space Manifold Reconstruction (`chaos_takens_reconstruct`)**: Embeds a 1D scalar series $x(t)$ into an $m$-dimensional shadow manifold $\mathbf{x}(t) = [x(t), x(t-\tau), \dots, x(t-(m-1)\tau)]^\top$ using average mutual information (AMI) to select $\tau$.
2. **Largest Lyapunov Exponent ($\lambda_1$) & Predictability Horizon ($T_{\max}$)**: Uses `scipy.spatial.cKDTree` with a Theiler exclusion window to measure exponential trajectory divergence $d_j(i) \approx C_j e^{\lambda_1 (i\Delta t)}$. When $\lambda_1 > 0$, the system is mathematically chaotic and point forecasts beyond $T_{\max} = \frac{1}{\lambda_1}\ln(\frac{\varepsilon_{\max}}{\varepsilon_0})$ are provably meaningless!
3. **Sugihara Convergent Cross Mapping (`chaos_takens_ccm_causality`)**: Distinguishes true directional dynamical coupling ($X \to Y$ vs $Y \to X$) from spurious correlation by testing whether the shadow manifold $\mathcal{M}_Y$ cross-maps $X(t)$ with monotonically increasing skill $\rho(L)$ as library length $L$ grows.
