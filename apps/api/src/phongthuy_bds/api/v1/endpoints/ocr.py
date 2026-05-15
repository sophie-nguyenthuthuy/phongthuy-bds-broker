"""OCR endpoints — upload sổ đỏ → extract trường."""

from __future__ import annotations

import tempfile
import uuid
from decimal import Decimal
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from phongthuy_bds.api.deps import CurrentUser, DbDep
from phongthuy_bds.db.models import LandTitle
from phongthuy_bds.schemas.ocr import HouseDirectionUpdate, OcrSoDoResponse
from phongthuy_bds.services.ocr.so_do import get_ocr_backend
from phongthuy_bds.services.storage import get_storage

router = APIRouter(prefix="/ocr", tags=["ocr"])

ALLOWED_MIME: frozenset[str] = frozenset({
    "image/jpeg", "image/png", "image/webp", "application/pdf",
})
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/sodo", response_model=OcrSoDoResponse, status_code=status.HTTP_201_CREATED)
async def ocr_so_do(
    db: DbDep,
    user: CurrentUser,
    file: UploadFile = File(..., description="Ảnh hoặc PDF sổ đỏ (≤10MB)"),
) -> OcrSoDoResponse:
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Định dạng không hỗ trợ: {file.content_type}",
        )

    contents = await file.read()
    if len(contents) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File lớn quá ({len(contents)} bytes), tối đa {MAX_SIZE_BYTES}",
        )

    # Lưu raw upload.
    storage = get_storage()
    upload_key = f"uploads/sodo/{user.tenant_id}/{uuid.uuid4()}-{file.filename}"
    storage.put(upload_key, contents, content_type=file.content_type or "application/octet-stream")

    # OCR sync trong v0; chuyển sang RQ worker khi có volume.
    with tempfile.NamedTemporaryFile(
        suffix=Path(file.filename or "upload").suffix, delete=False,
    ) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    try:
        backend = get_ocr_backend()
        result = backend.extract(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    # Persist LandTitle.
    lt = LandTitle(
        tenant_id=user.tenant_id,
        upload_storage_key=upload_key,
        template_version=result.template_version,
        so_seri=result.extracted.so_seri,
        so_vao_so=result.extracted.so_vao_so,
        extracted_data=result.extracted.model_dump(mode="json"),
        confidence=Decimal(str(result.confidence)),
        address=result.extracted.dia_chi,
        area_m2=result.extracted.dien_tich_m2,
    )
    db.add(lt)
    db.commit()
    db.refresh(lt)

    return OcrSoDoResponse(
        land_title_id=lt.id,
        template_version=result.template_version,
        extracted=result.extracted,
        confidence=result.confidence,
        needs_review=result.needs_review,
        created_at=lt.created_at,
    )


@router.patch("/sodo/{land_title_id}/direction", response_model=OcrSoDoResponse)
def set_house_direction(
    land_title_id: uuid.UUID,
    req: HouseDirectionUpdate,
    db: DbDep,
    user: CurrentUser,
) -> OcrSoDoResponse:
    """Môi giới chốt hướng nhà sau khi OCR (do OCR không suy ra được tọa-hướng)."""
    lt = db.get(LandTitle, land_title_id)
    if lt is None or lt.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    lt.house_direction = req.house_direction
    db.commit()
    db.refresh(lt)
    from phongthuy_bds.schemas.ocr import SoDoExtractedData
    return OcrSoDoResponse(
        land_title_id=lt.id,
        template_version=lt.template_version,
        extracted=SoDoExtractedData.model_validate(lt.extracted_data),
        confidence=float(lt.confidence),
        needs_review=float(lt.confidence) < 0.85,
        created_at=lt.created_at,
    )
