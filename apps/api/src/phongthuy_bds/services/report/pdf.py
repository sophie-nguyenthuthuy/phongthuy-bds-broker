"""Sinh PDF báo cáo từ template Jinja2 + WeasyPrint."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from phongthuy_bds.core.logging import get_logger

log = get_logger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "templates"

_jinja = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
)

PURPOSE_LABELS: dict[str, str] = {
    "dong_tho": "Ngày tốt động thổ",
    "dat_mong": "Ngày tốt đặt móng",
    "nhap_trach": "Ngày tốt nhập trạch (về nhà mới)",
    "khai_truong": "Ngày tốt khai trương",
}


def render_html(
    *,
    tenant: dict[str, Any],
    customer: dict[str, Any],
    report: dict[str, Any],
    land_title: dict[str, Any],
    result: dict[str, Any],
) -> str:
    """Render báo cáo thành HTML (Jinja2). Dễ test, không phụ thuộc WeasyPrint."""
    template = _jinja.get_template("report.html")
    return template.render(
        tenant=tenant,
        customer=customer,
        report=report,
        land_title=land_title,
        result=result,
        purpose_labels=PURPOSE_LABELS,
        generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
    )


def render_pdf_bytes(html: str, base_url: str | None = None) -> bytes:
    """HTML → PDF bytes. Lazy-import để test không cần weasyprint."""
    try:
        from weasyprint import HTML  # type: ignore[import-not-found]
    except ImportError as e:
        raise RuntimeError(
            "WeasyPrint chưa cài. Thường cài cùng base deps; check pyproject.toml."
        ) from e
    return HTML(string=html, base_url=base_url).write_pdf() or b""
