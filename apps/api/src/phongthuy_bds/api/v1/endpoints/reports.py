"""Report endpoints — create / get / download PDF."""

from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select

from phongthuy_bds.api.deps import CurrentUser, DbDep
from phongthuy_bds.db.models import Customer, LandTitle, Report, ReportStatus
from phongthuy_bds.schemas.report import CreateReportRequest, ReportOut
from phongthuy_bds.services.billing.credits import InsufficientCreditError, charge
from phongthuy_bds.services.report.generator import (
    ReportGenerationError,
    generate_report,
)
from phongthuy_bds.services.storage import get_storage

router = APIRouter(prefix="/reports", tags=["reports"])

CREDIT_PER_REPORT = Decimal("1")


def _to_out(r: Report) -> ReportOut:
    storage = get_storage()
    return ReportOut(
        id=r.id,
        tenant_id=r.tenant_id,
        customer_id=r.customer_id,
        land_title_id=r.land_title_id,
        status=r.status,
        purposes=[p for p in r.purposes],  # noqa: C416
        result_data=r.result_data or {},
        pdf_url=storage.url_for(r.pdf_storage_key) if r.pdf_storage_key else None,
        credit_cost=r.credit_cost,
        created_at=r.created_at,
        error_message=r.error_message,
    )


@router.post("", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def create_report(
    req: CreateReportRequest, db: DbDep, user: CurrentUser,
) -> ReportOut:
    customer = db.get(Customer, req.customer_id)
    land_title = db.get(LandTitle, req.land_title_id)
    if customer is None or customer.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Customer không tồn tại",
        )
    if land_title is None or land_title.tenant_id != user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sổ đỏ không tồn tại",
        )
    if not land_title.house_direction:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cần chốt hướng nhà (PATCH /v1/ocr/sodo/{id}/direction) trước",
        )

    # Trừ credit (transactional, FOR UPDATE).
    try:
        charge(
            db, user.tenant_id, CREDIT_PER_REPORT,
            kind="report", reference=f"report-pending-{customer.id}",
        )
    except InsufficientCreditError as e:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(e),
        ) from e

    report = Report(
        tenant_id=user.tenant_id,
        customer_id=customer.id,
        land_title_id=land_title.id,
        created_by_id=user.id,
        purposes=[p.value for p in req.purposes],
        credit_cost=CREDIT_PER_REPORT,
        status=ReportStatus.PENDING,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # Sync generate in v0. Move to RQ worker when latency hurts.
    try:
        generate_report(db, report.id)
    except ReportGenerationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tạo báo cáo thất bại: {e}",
        ) from e
    db.refresh(report)
    return _to_out(report)


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: uuid.UUID, db: DbDep, user: CurrentUser) -> ReportOut:
    r = db.get(Report, report_id)
    if r is None or r.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return _to_out(r)


@router.get("", response_model=list[ReportOut])
def list_reports(db: DbDep, user: CurrentUser, limit: int = 50) -> list[ReportOut]:
    rows = db.execute(
        select(Report)
        .where(Report.tenant_id == user.tenant_id)
        .order_by(Report.created_at.desc())
        .limit(limit)
    ).scalars().all()
    return [_to_out(r) for r in rows]


@router.get("/{report_id}/pdf", responses={200: {"content": {"application/pdf": {}}}})
def download_pdf(report_id: uuid.UUID, db: DbDep, user: CurrentUser) -> Response:
    r = db.get(Report, report_id)
    if r is None or r.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if not r.pdf_storage_key:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="PDF chưa sẵn sàng",
        )
    pdf = get_storage().get(r.pdf_storage_key)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="bao-cao-phongthuy-{r.id}.pdf"',
        },
    )
