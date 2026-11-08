"""FastAPI web router for chaos-takens phase-space and CCM inspection."""

from __future__ import annotations

from fastapi import APIRouter

from ..engine import LAST_TAKENS_CACHE, handle_takens_reconstruct

router = APIRouter()


@router.get("/status")
def get_takens_status() -> dict:
    latest = LAST_TAKENS_CACHE.get("latest")
    if not latest:
        latest = handle_takens_reconstruct({})
    return {
        "plugin": "chaos-takens",
        "status": "active",
        "latest_reconstruction": latest,
    }
