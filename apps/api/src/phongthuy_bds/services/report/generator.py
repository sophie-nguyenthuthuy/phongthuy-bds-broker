"""Báo cáo end-to-end: orchestrate engine + PDF + storage."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from phongthuy_bds.core.logging import get_logger
from phongthuy_bds.core.security import decrypt_pii
from phongthuy_bds.db.models import (
    Customer,
    LandTitle,
    Report,
    ReportStatus,
    Tenant,
)
from phongthuy_bds.services.feng_shui.engine import build_report_payload
from phongthuy_bds.services.report.pdf import render_html, render_pdf_bytes
from phongthuy_bds.services.storage import get_storage
from phongthuy_ontology import Gender

log = get_logger(__name__)


class ReportGenerationError(Exception):
    pass


def generate_report(db: Session, report_id: uuid.UUID) -> Report:
    """Chạy toàn bộ pipeline: tính phong thủy → render HTML → PDF → upload → cập nhật DB.

    Idempotent: gọi lại trên cùng report_id sẽ ghi đè PDF + result_data.
    Throw `ReportGenerationError` khi pipeline fail; caller chịu trách nhiệm
    set status FAILED.
    """
    report = db.get(Report, report_id)
    if report is None:
        raise ReportGenerationError(f"Không tìm thấy báo cáo {report_id}")

    customer = db.get(Customer, report.customer_id)
    land_title = db.get(LandTitle, report.land_title_id)
    tenant = db.get(Tenant, report.tenant_id)
    if customer is None or land_title is None or tenant is None:
        raise ReportGenerationError("Thiếu dữ liệu khách / sổ đỏ / tenant")

    report.status = ReportStatus.COMPUTING
    db.commit()

    try:
        birth_date_str = decrypt_pii(customer.birth_date_encrypted)
        from datetime import date as _date
        birth_date = _date.fromisoformat(birth_date_str)
        full_name = decrypt_pii(customer.full_name_encrypted)

        result = build_report_payload(
            birth_date=birth_date,
            gender=Gender(customer.gender),
            house_direction=land_title.house_direction,
            purposes=[str(p) for p in report.purposes],
            good_day_top_k=5,
        )

        # ── Render HTML ──
        html = render_html(
            tenant={"name": tenant.name, "tax_code": tenant.tax_code},
            customer={
                "full_name": full_name,
                "birth_date": birth_date,
                "gender_label": "Nam" if customer.gender == "nam" else "Nữ",
            },
            report={"id": str(report.id)},
            land_title={
                "address": land_title.address,
                "thua": land_title.extracted_data.get("thua_dat_so") or "—",
                "to_bd": land_title.extracted_data.get("to_ban_do_so") or "—",
                "area_m2": float(land_title.area_m2) if land_title.area_m2 else None,
                "house_direction": land_title.house_direction,
            },
            result=result.model_dump(),
        )

        # ── Render PDF ──
        pdf_bytes = render_pdf_bytes(html)

        # ── Upload ──
        storage = get_storage()
        key = f"reports/{tenant.id}/{report.id}.pdf"
        storage.put(key, pdf_bytes, content_type="application/pdf")

        report.result_data = result.model_dump(mode="json")
        report.pdf_storage_key = key
        report.status = ReportStatus.READY
        report.error_message = None
        db.commit()
        log.info("report.generated", report_id=str(report.id), key=key)

    except Exception as e:
        log.exception("report.failed", report_id=str(report.id))
        report.status = ReportStatus.FAILED
        report.error_message = str(e)[:500]
        db.commit()
        raise ReportGenerationError(str(e)) from e

    return report
