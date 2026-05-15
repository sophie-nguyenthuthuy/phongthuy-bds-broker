"""Tín dụng (credits) — trừ khi tạo báo cáo, nạp qua VNPay/MoMo."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from phongthuy_bds.db.models import CreditTransaction, Tenant


class InsufficientCreditError(Exception):
    pass


def get_balance(db: Session, tenant_id: uuid.UUID) -> Decimal:
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise ValueError(f"Tenant {tenant_id} not found")
    return tenant.credit_balance


def charge(
    db: Session,
    tenant_id: uuid.UUID,
    amount: Decimal,
    *,
    kind: str = "report",
    reference: str | None = None,
) -> CreditTransaction:
    """Trừ credit. Throw `InsufficientCreditError` nếu hết tín dụng.

    Sử dụng SELECT … FOR UPDATE để tránh race condition khi hai báo cáo
    được tạo cùng lúc.
    """
    if amount <= 0:
        raise ValueError("amount phải > 0 cho 'charge'; dùng 'topup' để nạp")

    tenant = db.execute(
        select(Tenant).where(Tenant.id == tenant_id).with_for_update()
    ).scalar_one_or_none()
    if tenant is None:
        raise ValueError(f"Tenant {tenant_id} not found")
    if tenant.credit_balance < amount:
        raise InsufficientCreditError(
            f"Không đủ tín dụng — số dư {tenant.credit_balance}, cần {amount}"
        )

    tenant.credit_balance = tenant.credit_balance - amount
    tx = CreditTransaction(
        tenant_id=tenant.id,
        amount=-amount,
        balance_after=tenant.credit_balance,
        kind=kind,
        reference=reference,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def topup(
    db: Session,
    tenant_id: uuid.UUID,
    amount: Decimal,
    *,
    provider: str,
    reference: str,
    payment_data: dict | None = None,
) -> CreditTransaction:
    """Nạp credit từ payment gateway (VNPay/MoMo/ZaloPay)."""
    if amount <= 0:
        raise ValueError("amount phải > 0")

    tenant = db.execute(
        select(Tenant).where(Tenant.id == tenant_id).with_for_update()
    ).scalar_one_or_none()
    if tenant is None:
        raise ValueError(f"Tenant {tenant_id} not found")

    tenant.credit_balance = tenant.credit_balance + amount
    tx = CreditTransaction(
        tenant_id=tenant.id,
        amount=amount,
        balance_after=tenant.credit_balance,
        kind="topup",
        reference=reference,
        payment_provider=provider,
        payment_data=payment_data or {},
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx
