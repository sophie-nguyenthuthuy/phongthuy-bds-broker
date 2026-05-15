"""OCR sổ đỏ — extract trường theo TT 23/2014 và TT 10/2024.

Architecture:
  1. Phát hiện mẫu sổ (cũ vs mới) bằng heuristic: vị trí QR / màu logo.
  2. Chạy OCR (PaddleOCR cho mẫu cũ scan, có thể bypass cho mẫu mới có QR data).
  3. Bbox-based field extraction theo template.
  4. Confidence score per field; nếu < threshold thì cờ needs_review.

Cần dataset ~500 sổ đỏ ẩn danh để fine-tune. Hiện tại stub trả mock data
để toàn bộ pipeline chạy được end-to-end.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Protocol

from phongthuy_bds.core.config import get_settings
from phongthuy_bds.core.logging import get_logger
from phongthuy_bds.schemas.ocr import SoDoExtractedData

log = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class OcrResult:
    template_version: str
    extracted: SoDoExtractedData
    confidence: float
    raw_text: str
    needs_review: bool


class OcrBackend(Protocol):
    def extract(self, file_path: Path) -> OcrResult: ...


# ─── Backend: Mock (dev) ─────────────────────────────────────────
class MockBackend:
    """Trả dữ liệu giả lập — cho phép end-to-end pipeline chạy không cần OCR thật."""

    def extract(self, file_path: Path) -> OcrResult:
        log.info("ocr.mock.extract", file=str(file_path))
        return OcrResult(
            template_version="tt10_2024",
            extracted=SoDoExtractedData(
                nguoi_su_dung="Nguyễn Văn Demo",
                thua_dat_so="123",
                to_ban_do_so="45",
                dia_chi="Số 10, đường Lê Lợi, phường Bến Nghé, Quận 1, TP. HCM",
                dien_tich_m2=Decimal("78.50"),
                muc_dich_su_dung="ODT (Đất ở tại đô thị)",
                thoi_han_su_dung="Lâu dài",
                nguon_goc_su_dung="Nhà nước công nhận quyền sử dụng đất",
                so_seri="CT 123456",
                so_vao_so="CS-12345",
            ),
            confidence=0.92,
            raw_text="(mock OCR result)",
            needs_review=False,
        )


# ─── Backend: PaddleOCR ──────────────────────────────────────────
class PaddleBackend:
    """OCR thực tế. Cần optional extra `[ocr]` đã cài."""

    def __init__(self, lang: str = "vi") -> None:
        try:
            from paddleocr import PaddleOCR  # type: ignore[import-not-found]
        except ImportError as e:
            raise RuntimeError(
                "PaddleOCR chưa cài. Chạy `uv pip install '.[ocr]'`."
            ) from e
        self._ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)

    def extract(self, file_path: Path) -> OcrResult:
        log.info("ocr.paddle.extract", file=str(file_path))
        result = self._ocr.ocr(str(file_path), cls=True)
        lines: list[tuple[str, float]] = []
        for page in result:
            for box_info in page or []:
                _, (text, conf) = box_info
                lines.append((text, float(conf)))
        raw_text = "\n".join(t for t, _ in lines)
        avg_conf = sum(c for _, c in lines) / len(lines) if lines else 0.0

        # Phát hiện mẫu sổ.
        template_version = _detect_template(raw_text)
        # Trích xuất trường (regex/keyword-based; sau sẽ thay bằng bbox-based).
        extracted = _extract_fields(raw_text)

        return OcrResult(
            template_version=template_version,
            extracted=extracted,
            confidence=round(avg_conf, 3),
            raw_text=raw_text,
            needs_review=avg_conf < 0.85,
        )


def _detect_template(raw_text: str) -> str:
    """Phân biệt mẫu sổ đỏ TT 23/2014 vs TT 10/2024."""
    # TT 10/2024 mẫu mới: có dòng "Giấy chứng nhận quyền sử dụng đất, quyền sở hữu
    # tài sản gắn liền với đất" và có QR code dạng GLN VN.
    if "tài sản gắn liền với đất" in raw_text:
        return "tt10_2024"
    return "tt23_2014"


_THUA_RE = re.compile(r"[Tt]hửa\s+đất\s+số[:\s]+(\d+)")
_TO_BAN_DO_RE = re.compile(r"[Tt]ờ\s+bản\s+đồ\s+số[:\s]+(\d+)")
_DIEN_TICH_RE = re.compile(r"[Dd]iện\s+tích[:\s]+([\d.,]+)")
_SO_SERI_RE = re.compile(r"\b([A-Z]{2}\s?\d{6,})\b")
_MUC_DICH_RE = re.compile(r"[Mm]ục\s+đích\s+sử\s+dụng[:\s]+(.+?)(?:\n|$)")


def _extract_fields(raw_text: str) -> SoDoExtractedData:
    def _m(pat: re.Pattern[str]) -> str | None:
        m = pat.search(raw_text)
        return m.group(1).strip() if m else None

    def _dec(pat: re.Pattern[str]) -> Decimal | None:
        s = _m(pat)
        if not s:
            return None
        try:
            return Decimal(s.replace(",", ".").replace(" ", ""))
        except (ValueError, ArithmeticError):
            return None

    return SoDoExtractedData(
        thua_dat_so=_m(_THUA_RE),
        to_ban_do_so=_m(_TO_BAN_DO_RE),
        dien_tich_m2=_dec(_DIEN_TICH_RE),
        muc_dich_su_dung=_m(_MUC_DICH_RE),
        so_seri=_m(_SO_SERI_RE),
        # Các trường khác cần bbox-based template — chưa support trong v0.
    )


# ─── Factory ─────────────────────────────────────────────────────
def get_ocr_backend() -> OcrBackend:
    settings = get_settings()
    if settings.ocr_backend == "mock":
        return MockBackend()
    if settings.ocr_backend == "paddleocr":
        return PaddleBackend(lang=settings.paddleocr_lang)
    # google_vision có thể thêm sau.
    raise NotImplementedError(f"OCR backend {settings.ocr_backend!r} chưa hỗ trợ")
