"""chaos-takens: Chaos & Causal Manifold Reconstructor with Time-Series Auto-Trigger."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    from .engine import (
        LAST_TAKENS_CACHE,
        TAKENS_CCM_SCHEMA,
        TAKENS_RECONSTRUCT_SCHEMA,
        handle_takens_ccm_causality,
        handle_takens_reconstruct,
    )
except (ImportError, ValueError):
    from engine import (
        LAST_TAKENS_CACHE,
        TAKENS_CCM_SCHEMA,
        TAKENS_RECONSTRUCT_SCHEMA,
        handle_takens_ccm_causality,
        handle_takens_reconstruct,
    )


def pre_llm_call_hook(
    session_id: Union[str, Dict[str, Any]] = "",
    user_message: str = "",
    **kwargs: Any,
) -> Optional[Dict[str, Any]]:
    payload_dict = session_id if isinstance(session_id, dict) else None
    user_text = (
        str(payload_dict.get("user_message", "") or payload_dict.get("prompt", ""))
        if payload_dict is not None
        else str(user_message or kwargs.get("prompt", ""))
    ).lower()

    if not any(k in user_text for k in ("forecast", "predict", "time series", "timeseries", "latency", "jitter", "causal", "correlation", ".csv", "stability", "nic")):
        return payload_dict if payload_dict is not None else None

    rec_raw = handle_takens_reconstruct({})
    ccm_raw = handle_takens_ccm_causality({})
    rec = json.loads(rec_raw) if isinstance(rec_raw, str) else rec_raw
    ccm = json.loads(ccm_raw) if isinstance(ccm_raw, str) else ccm_raw

    ribbon = (
        f"[TAKENS_MANIFOLD | lambda_1={rec['largest_lyapunov_exponent']:+.4f} ({rec['dynamical_regime']}) | "
        f"Max_Valid_Forecast_Horizon={rec['predictability_horizon_steps']} steps | "
        f"CCM_Causal={ccm['causal_direction']} (rho={ccm['terminal_rho_x_causes_y']} vs Linear_r={ccm['linear_pearson_r']})]"
    )
    if payload_dict is not None:
        existing = str(payload_dict.get("injected_context", ""))
        payload_dict["injected_context"] = (existing + chr(10) + ribbon).strip()
        payload_dict["context"] = ribbon
        payload_dict["chaos_takens_analysis"] = {"attractor": rec, "ccm": ccm}
        return payload_dict
    return {"context": ribbon, "chaos_takens_analysis": {"attractor": rec, "ccm": ccm}}


def post_llm_call_hook(
    session_id: Union[str, Dict[str, Any]] = "",
    **kwargs: Any,
) -> Optional[Dict[str, Any]]:
    if isinstance(session_id, dict):
        latest = LAST_TAKENS_CACHE.get("latest")
        if latest and "transcript_directive" in latest:
            session_id.setdefault("directives", []).append(latest["transcript_directive"])
        return session_id
    return None


def register(ctx) -> None:
    ctx.register_tool(
        name="chaos_takens_reconstruct",
        toolset="chaos_takens",
        schema=TAKENS_RECONSTRUCT_SCHEMA,
        handler=handle_takens_reconstruct,
        is_async=False,
        emoji="🌀",
    )
    ctx.register_tool(
        name="chaos_takens_ccm_causality",
        toolset="chaos_takens",
        schema=TAKENS_CCM_SCHEMA,
        handler=handle_takens_ccm_causality,
        is_async=False,
        emoji="🔗",
    )
    ctx.register_hook("pre_llm_call", pre_llm_call_hook)
    ctx.register_hook("post_llm_call", post_llm_call_hook)

    skills_dir = Path(__file__).parent / "skills"
    if hasattr(ctx, "register_skill") and skills_dir.exists():
        for child in sorted(skills_dir.iterdir()):
            skill_md = child / "SKILL.md"
            if child.is_dir() and skill_md.exists():
                ctx.register_skill(child.name, skill_md)
