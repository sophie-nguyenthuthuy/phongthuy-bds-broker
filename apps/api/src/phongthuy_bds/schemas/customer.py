"""Pydantic schemas cho khách hàng."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from phongthuy_ontology import Gender


class CustomerCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    phone: str | None = Field(default=None, pattern=r"^(0|\+84)\d{9,10}$")
    birth_date: date
    gender: Gender
    consent_given: bool = Field(
        ...,
        description="Khách đã đồng ý cho phép xử lý DLCN (NĐ 13/2023/NĐ-CP)",
    )
    consent_doc_url: str | None = None

    def validate_consent(self) -> None:
        if not self.consent_given:
            raise ValueError("Phải có đồng thuận xử lý DLCN trước khi tạo hồ sơ KH")


class CustomerOut(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    full_name: str
    phone: str | None
    birth_date: date
    gender: Gender
    delete_after: date
    created_at: datetime

    model_config = {"from_attributes": True}
