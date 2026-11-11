"""FastAPI web router for chaos-takens phase-space and CCM inspection."""

from __future__ import annotations

from fastapi import APIRouter

from ..engine import LAST_TAKENS_CACHE

router = APIRouter()


@router.get("/status")
def get_takens_status() -> dict:
    latest = LAST_TAKENS_CACHE.get("latest")
    if not latest:
        return {
            "plugin": "chaos-takens",
            "status": "idle",
            "message": "No reconstruction run yet. Use chaos_takens_reconstruct with a real series.",
        }
    return {
        "plugin": "chaos-takens",
        "status": "active",
        "latest_reconstruction": latest,
    }
