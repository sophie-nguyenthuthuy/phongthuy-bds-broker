"""Pydantic schemas cho OCR sổ đỏ."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class SoDoExtractedData(BaseModel):
    """Trường rút từ sổ đỏ — theo TT 10/2024/TT-BTNMT (mẫu mới) hoặc TT 23/2014.

    Không phải mọi trường đều có ở mọi sổ — set None khi OCR không xác định được.
    """
    nguoi_su_dung: str | None = Field(
        None, description="Người sử dụng đất / chủ sở hữu — ẩn danh khi log",
    )
    thua_dat_so: str | None = Field(None, description="Thửa đất số")
    to_ban_do_so: str | None = Field(None, description="Tờ bản đồ số")
    dia_chi: str | None = Field(None, description="Địa chỉ thửa đất")
    dien_tich_m2: Decimal | None = Field(None, description="Diện tích m²")
    muc_dich_su_dung: str | None = Field(
        None,
        description="ONT/ODT/CLN/… mã loại đất theo Luật Đất đai 2024 Phụ lục 01",
    )
    thoi_han_su_dung: str | None = Field(None, description="Thời hạn sử dụng")
    nguon_goc_su_dung: str | None = Field(None, description="Nguồn gốc sử dụng đất")
    so_seri: str | None = Field(None, description="Số seri sổ (CT/AB/…)")
    so_vao_so: str | None = Field(None, description="Số vào sổ cấp giấy")


class OcrSoDoResponse(BaseModel):
    land_title_id: uuid.UUID
    template_version: str = Field(
        description="tt23_2014 (mẫu cũ) | tt10_2024 (mẫu mới)",
    )
    extracted: SoDoExtractedData
    confidence: float = Field(ge=0, le=1)
    needs_review: bool = Field(
        description="True nếu confidence thấp — yêu cầu môi giới xác nhận thủ công",
    )
    created_at: datetime


class HouseDirectionUpdate(BaseModel):
    """Môi giới chốt hướng nhà sau khi OCR (vì OCR không suy ra được tọa-hướng)."""
    house_direction: str = Field(
        pattern=r"^(Bắc|Nam|Đông|Tây|Đông Bắc|Đông Nam|Tây Bắc|Tây Nam)$",
    )
