# Kiến trúc

## High-level

```
┌──────────────────┐
│ Môi giới (web)   │  ── HTTPS ──┐
└──────────────────┘             │
                                 ▼
                       ┌─────────────────────┐
                       │  FastAPI (apps/api) │
                       │  ────────────────── │
                       │  /v1/auth           │
                       │  /v1/customers      │
                       │  /v1/ocr/sodo       │
                       │  /v1/reports        │
                       │  /v1/billing        │
                       └────────┬────────────┘
                                │
       ┌─────────────┬──────────┼──────────┬──────────────┐
       ▼             ▼          ▼          ▼              ▼
   PostgreSQL      Redis    Storage   Ontology pkg    VNPay/MoMo
   (encrypted    (RQ jobs) (S3 / FS) (pure-Python)   (HTTPS API)
    PII at rest)
```

## Tách lớp

- **`packages/ontology`** — Knowledge layer. Không phụ thuộc FastAPI, không
  phụ thuộc DB. Có thể publish thành standalone PyPI nếu muốn.
- **`apps/api`** — Application layer. Multi-tenant, multi-user. Wraps ontology
  thành endpoint REST.
- **`apps/web`** — Presentation layer. Stateless, gọi API bằng JWT.

## Data flow tạo báo cáo

```
1. POST /v1/customers
   {full_name, birth_date, gender, consent_given=true}
   → encrypt PII at rest, delete_after = now + 90 days

2. POST /v1/ocr/sodo (multipart)
   → OCR backend (mock | paddleocr) → extracted_data + confidence
   → persist LandTitle

3. PATCH /v1/ocr/sodo/{id}/direction {house_direction}
   → môi giới chốt hướng nhà sau khi xem ảnh sổ

4. POST /v1/reports
   {customer_id, land_title_id, purposes}
   → charge(tenant, 1 credit) (FOR UPDATE)
   → engine.build_report_payload()
     → cung_menh_from_birth_date()       # ontology
     → bat_trach_for_cung()              # ontology
     → match_house_direction()           # ontology
     → pick_good_days() × purpose        # ontology
   → render Jinja HTML → WeasyPrint PDF
   → upload Storage → URL signed
   → status=READY

5. GET /v1/reports/{id}/pdf
   → stream từ Storage
```

## Tách concerns trong code

| Module                                       | Trách nhiệm                               |
|----------------------------------------------|-------------------------------------------|
| `phongthuy_ontology.*`                       | Phong thủy rule (pure)                    |
| `phongthuy_bds.core.*`                       | Config, logging, security                 |
| `phongthuy_bds.db.*`                         | ORM models + session                      |
| `phongthuy_bds.schemas.*`                    | Pydantic DTOs                             |
| `phongthuy_bds.services.feng_shui.engine`    | Ontology adapter — gọi vào ontology      |
| `phongthuy_bds.services.ocr.*`               | OCR backends                              |
| `phongthuy_bds.services.report.*`            | HTML render + PDF + orchestration         |
| `phongthuy_bds.services.billing.*`           | Credits + VNPay/MoMo                      |
| `phongthuy_bds.services.storage`             | Local FS / S3 abstraction                 |
| `phongthuy_bds.api.v1.endpoints.*`           | FastAPI route handlers (thin)             |

## Multi-tenant model

Mọi bảng có `tenant_id` (FK → tenants). Mọi query filter theo `user.tenant_id`
trong endpoint handler. Không tin client gửi tenant_id; lấy từ JWT.

## Scaling notes

- **OCR sync ở v0**. Khi volume > 100 báo cáo/ngày, chuyển sang RQ worker
  (`redis://`). Đã có `rq` trong deps; chỉ cần thêm worker module và đổi endpoint
  từ sync → async (`status=ocr_running` → poll/webhook).
- **PDF generation** tương tự — WeasyPrint ~2-3s/báo cáo, chấp nhận sync ở MVP.
- **DB**. Mọi table có index `tenant_id`. JSONB cho `result_data`/`extracted_data`
  cho phép query gist nếu cần search trong tương lai.
