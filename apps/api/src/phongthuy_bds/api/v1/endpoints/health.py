"""Health + readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel
from sqlalchemy import text

from phongthuy_bds.api.deps import DbDep
from phongthuy_bds import __version__

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str


class ReadyResponse(BaseModel):
    status: str
    checks: dict[str, str]


@router.get("/healthz", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness — không kiểm tra dependencies."""
    return HealthResponse(status="ok", version=__version__)


@router.get(
    "/readyz",
    response_model=ReadyResponse,
    responses={503: {"model": ReadyResponse}},
)
def ready(db: DbDep, response_class: type | None = None) -> ReadyResponse:
    """Readiness — check DB."""
    checks: dict[str, str] = {}
    try:
        db.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as e:  # noqa: BLE001
        checks["db"] = f"fail: {e!s}"
    overall = "ok" if all(v == "ok" for v in checks.values()) else "fail"
    return ReadyResponse(status=overall, checks=checks)
