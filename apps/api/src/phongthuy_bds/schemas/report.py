"""Pydantic schemas cho báo cáo phong thủy."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from phongthuy_bds.db.models import Purpose, ReportStatus


class CreateReportRequest(BaseModel):
    customer_id: uuid.UUID
    land_title_id: uuid.UUID
    purposes: list[Purpose] = Field(
        default_factory=lambda: [Purpose.NHAP_TRACH],
        min_length=1,
    )
    good_day_window_start: date | None = Field(
        default=None,
        description="Mặc định: hôm nay",
    )
    good_day_window_end: date | None = Field(
        default=None,
        description="Mặc định: hôm nay + 90 ngày",
    )
    good_day_top_k: int = Field(default=5, ge=1, le=30)


class CungMenhBlock(BaseModel):
    cung: str
    nhom: str
    ngu_hanh_cung: str
    ngu_hanh_nap_am: str
    can_chi: str
    lunar_year: int
    lac_thu_so: int
    notes: list[str] = []


class DirectionBlock(BaseModel):
    quality: str
    direction: str
    description: str
    is_good: bool


class HouseMatchBlock(BaseModel):
    """Đánh giá hợp tuổi cho hướng nhà thực tế từ sổ đỏ."""
    house_direction: str
    matched_quality: str
    is_good: bool
    advice: str


class GoodDayBlock(BaseModel):
    solar_date: date
    lunar_date: str
    can_chi_day: str
    hoang_dao_than: str
    is_hoang_dao: bool
    score: int
    reasons_good: list[str]
    reasons_bad: list[str]
    is_recommended: bool


class ReportResultData(BaseModel):
    cung_menh: CungMenhBlock
    bat_trach: list[DirectionBlock]
    house_match: HouseMatchBlock | None = None
    good_days: dict[str, list[GoodDayBlock]] = Field(
        default_factory=dict,
        description="Map từ purpose → danh sách ngày tốt",
    )
    disclaimer: str = (
        "Báo cáo phong thủy mang tính tham khảo văn hóa, không thay thế tư vấn "
        "đầu tư BĐS hay pháp lý."
    )


class ReportOut(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    land_title_id: uuid.UUID
    status: ReportStatus
    purposes: list[Purpose]
    result_data: dict[str, Any]
    pdf_url: str | None = None
    credit_cost: Decimal
    created_at: datetime
    error_message: str | None = None

    model_config = {"from_attributes": True}
