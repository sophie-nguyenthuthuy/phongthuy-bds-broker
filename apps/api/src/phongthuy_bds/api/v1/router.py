"""API v1 router — gom tất cả endpoint modules."""

from fastapi import APIRouter

from phongthuy_bds.api.v1.endpoints import (
    auth,
    billing,
    customers,
    health,
    ocr,
    reports,
)

api_router = APIRouter(prefix="/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(customers.router)
api_router.include_router(ocr.router)
api_router.include_router(reports.router)
api_router.include_router(billing.router)
