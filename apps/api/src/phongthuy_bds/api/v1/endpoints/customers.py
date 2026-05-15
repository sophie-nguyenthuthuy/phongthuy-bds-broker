"""Customer endpoints — tạo / xem / xóa hồ sơ khách hàng (DLCN).

Tuân thủ NĐ 13/2023/NĐ-CP:
- Yêu cầu `consent_given=True` khi tạo (kèm timestamp + doc URL nếu có).
- Field tên + ngày sinh + SĐT lưu encrypted at rest.
- Retention 90 ngày mặc định; có endpoint DELETE để KH yêu cầu xóa.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from phongthuy_bds.api.deps import CurrentUser, DbDep
from phongthuy_bds.core.config import get_settings
from phongthuy_bds.core.security import decrypt_pii, encrypt_pii
from phongthuy_bds.db.models import Customer
from phongthuy_bds.schemas.customer import CustomerCreate, CustomerOut

router = APIRouter(prefix="/customers", tags=["customers"])


def _to_out(c: Customer) -> CustomerOut:
    return CustomerOut(
        id=c.id,
        tenant_id=c.tenant_id,
        full_name=decrypt_pii(c.full_name_encrypted),
        phone=decrypt_pii(c.phone_encrypted) if c.phone_encrypted else None,
        birth_date=date.fromisoformat(decrypt_pii(c.birth_date_encrypted)),
        gender=c.gender,  # type: ignore[arg-type]
        delete_after=c.delete_after,
        created_at=c.created_at,
    )


@router.post("", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
def create_customer(req: CustomerCreate, db: DbDep, user: CurrentUser) -> CustomerOut:
    if not req.consent_given:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cần đồng thuận DLCN theo NĐ 13/2023/NĐ-CP trước khi lưu hồ sơ",
        )
    retention = get_settings().dlcn_retention_days
    now = datetime.now(UTC)
    c = Customer(
        tenant_id=user.tenant_id,
        full_name_encrypted=encrypt_pii(req.full_name),
        phone_encrypted=encrypt_pii(req.phone) if req.phone else None,
        birth_date_encrypted=encrypt_pii(req.birth_date.isoformat()),
        gender=req.gender.value,
        consent_given_at=now,
        consent_doc_url=req.consent_doc_url,
        delete_after=now.date() + timedelta(days=retention),
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return _to_out(c)


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: uuid.UUID, db: DbDep, user: CurrentUser) -> CustomerOut:
    c = db.get(Customer, customer_id)
    if c is None or c.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return _to_out(c)


@router.get("", response_model=list[CustomerOut])
def list_customers(db: DbDep, user: CurrentUser, limit: int = 50) -> list[CustomerOut]:
    rows = db.execute(
        select(Customer)
        .where(Customer.tenant_id == user.tenant_id)
        .order_by(Customer.created_at.desc())
        .limit(limit)
    ).scalars().all()
    return [_to_out(c) for c in rows]


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: uuid.UUID, db: DbDep, user: CurrentUser) -> None:
    """Xóa hồ sơ theo yêu cầu KH (NĐ 13 Điều 16 — quyền xóa DLCN).

    Xóa cứng (hard-delete) thay vì soft-delete, để đảm bảo không còn DLCN trên hệ thống.
    Báo cáo đã tạo từ KH này có FK CASCADE → tự xóa luôn.
    """
    c = db.get(Customer, customer_id)
    if c is None or c.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    db.delete(c)
    db.commit()
