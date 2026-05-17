"""Billing endpoints — balance, top-up via VNPay, transaction history."""

from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from phongthuy_bds.api.deps import CurrentUser, DbDep, require_role
from phongthuy_bds.db.models import CreditTransaction
from phongthuy_bds.services.billing.credits import get_balance, topup
from phongthuy_bds.services.billing.vnpay import build_payment_url, verify_return

router = APIRouter(prefix="/billing", tags=["billing"])


class BalanceOut(BaseModel):
    tenant_id: uuid.UUID
    credit_balance: Decimal


class TopupRequest(BaseModel):
    amount_vnd: Decimal = Field(ge=10_000, le=100_000_000)
    provider: str = Field(default="vnpay", pattern="^(vnpay|momo|zalopay)$")
    bank_code: str | None = None


class TopupResponse(BaseModel):
    order_id: str
    payment_url: str


class TransactionOut(BaseModel):
    id: uuid.UUID
    amount: Decimal
    balance_after: Decimal
    kind: str
    reference: str | None
    payment_provider: str | None

    model_config = {"from_attributes": True}


@router.get("/balance", response_model=BalanceOut)
def balance(db: DbDep, user: CurrentUser) -> BalanceOut:
    return BalanceOut(
        tenant_id=user.tenant_id,
        credit_balance=get_balance(db, user.tenant_id),
    )


@router.post(
    "/topup",
    response_model=TopupResponse,
    dependencies=[Depends(require_role("owner", "admin"))],
)
def create_topup(
    req: TopupRequest, request: Request, user: CurrentUser,
) -> TopupResponse:
    if req.provider != "vnpay":
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Cổng {req.provider} sẽ hỗ trợ sau",
        )

    order_id = f"TOPUP-{user.tenant_id}-{uuid.uuid4().hex[:8]}"
    url = build_payment_url(
        order_id=order_id,
        amount_vnd=req.amount_vnd,
        order_info=f"Nap credit phong thuy BDS — {user.tenant_id}",
        ip_address=request.client.host if request.client else "127.0.0.1",
        bank_code=req.bank_code,
    )
    return TopupResponse(order_id=order_id, payment_url=url)


@router.post("/vnpay/return")
def vnpay_return(request: Request, db: DbDep) -> dict[str, str]:
    """Callback từ VNPay sau khi user thanh toán xong.

    Verify signature → topup credit cho tenant.
    """
    params = dict(request.query_params)
    if not verify_return(params):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Sai chữ ký VNPay",
        )
    if params.get("vnp_ResponseCode") != "00":
        return {"status": "failed", "code": params.get("vnp_ResponseCode", "")}

    order_id = params.get("vnp_TxnRef", "")
    # order_id = "TOPUP-{tenant_id}-{xxx}"
    parts = order_id.split("-")
    if len(parts) < 3 or parts[0] != "TOPUP":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Order ID không hợp lệ",
        )
    tenant_id = uuid.UUID(parts[1])

    amount = Decimal(params.get("vnp_Amount", "0")) / Decimal("100")

    # Idempotency: ensure we don't double-topup on duplicate callbacks.
    existing = db.execute(
        select(CreditTransaction).where(CreditTransaction.reference == order_id)
    ).scalar_one_or_none()
    if existing is not None:
        return {"status": "already_processed", "order_id": order_id}

    topup(
        db, tenant_id, amount,
        provider="vnpay", reference=order_id, payment_data=params,
    )
    return {"status": "success", "order_id": order_id}


@router.get("/transactions", response_model=list[TransactionOut])
def list_transactions(
    db: DbDep, user: CurrentUser, limit: int = 50,
) -> list[TransactionOut]:
    rows = db.execute(
        select(CreditTransaction)
        .where(CreditTransaction.tenant_id == user.tenant_id)
        .order_by(CreditTransaction.created_at.desc())
        .limit(limit)
    ).scalars().all()
    return [TransactionOut.model_validate(r) for r in rows]
