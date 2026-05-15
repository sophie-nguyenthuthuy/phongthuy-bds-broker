# Phong Thủy BĐS — Plug-in chốt deal cho môi giới

> **Mục tiêu**: Môi giới BĐS nhập **sổ đỏ + ngày sinh khách** → trong 30 giây có ngay
> báo cáo phong thủy chuyên nghiệp: **hợp tuổi, hướng nhà, ngày tốt động thổ / nhập trạch**.
> Cây búa chốt deal của môi giới VN, hiện vẫn làm thủ công bằng lịch giấy.

[![CI](https://github.com/.../phongthuy-bds-broker/actions/workflows/ci.yml/badge.svg)](./.github/workflows/ci.yml)
[![License: BUSL-1.1](https://img.shields.io/badge/License-BUSL--1.1-blue.svg)](./LICENSE)

---

## Vì sao defensible?

Khác với các tool phong thủy generic của TQ port sang, repo này khác biệt ở 3 điểm:

1. **`packages/ontology`** — Phong thủy được mã hóa thành **dữ liệu phiên bản hóa**
   (YAML + Pydantic), không phải LLM hallucination. Mỗi cung mệnh, mỗi bộ hướng, mỗi
   ngày tốt đều **trace được về nguồn** (Hoàng Lịch Thông Thư, Bát Trạch Minh Cảnh).
2. **OCR sổ đỏ VN-canonical** — Trích xuất chính xác layout sổ đỏ theo **Luật Đất đai
   2024** và Thông tư 10/2024/TT-BTNMT: thửa số, tờ bản đồ, diện tích, mục đích sử dụng,
   thời hạn, địa chỉ thửa, người sử dụng đất. Không phải OCR generic.
3. **Plug-in API-first** — Tích hợp được vào CRM môi giới sẵn có (HomeService, Rever,
   Propzy-style) qua REST + webhook. Không bắt môi giới đổi workflow.

## Stack

| Layer       | Tech                                                          |
|-------------|---------------------------------------------------------------|
| API         | FastAPI (Python 3.12), uv, SQLAlchemy 2, Alembic              |
| Ontology    | YAML data + Pydantic v2 models + pure-Python queries          |
| OCR         | PaddleOCR (VN model) + bbox-based field extraction            |
| Lunar/CanChi| Pure Python lunar conversion (VN timezone, kinh tuyến 105°E)  |
| Web         | Next.js 14 (App Router) + TypeScript + Tailwind + shadcn/ui   |
| Báo cáo     | WeasyPrint → PDF tiếng Việt (font Be Vietnam Pro)             |
| DB          | PostgreSQL 16 + Redis 7 (job queue)                           |
| Auth        | JWT + multi-tenant (mỗi sàn môi giới = 1 tenant)              |
| Billing     | VNPay / MoMo / ZaloPay (mỗi báo cáo = 1 tín dụng)             |
| Infra       | Docker, docker-compose, GitHub Actions CI                     |

## Cấu trúc repo

```
apps/
  api/                 # FastAPI service — endpoint /v1/reports, /v1/ocr/sodo, /v1/auth
  web/                 # Next.js broker dashboard
packages/
  ontology/            # YAML phong thủy + Pydantic models (đây là core IP)
  sample-sodo/         # Mẫu sổ đỏ ẩn danh để test OCR (CC-BY-SA)
infra/
  docker/              # Dockerfile prod, nginx config
  k8s/                 # Helm chart placeholder
docs/
  architecture.md      # High-level diagram, data flow
  feng-shui-spec.md    # Đặc tả nguyên lý phong thủy đã encode
  legal-compliance.md  # Luật Đất đai 2024, NĐ 13/2023/NĐ-CP về DLCN
.github/workflows/     # CI: lint, type-check, test, build
```

## Quick start (developer)

```bash
# 1. Cài uv + pnpm
brew install uv pnpm

# 2. Khởi tạo môi trường
cp .env.example .env
make dev-up           # Docker Postgres + Redis
make db-migrate       # alembic upgrade head
make api-dev          # FastAPI ở :8000
make web-dev          # Next.js ở :3000

# 3. Chạy test
make test             # pytest + vitest
make lint             # ruff + mypy + eslint
```

Truy cập `http://localhost:3000/login` → đăng nhập bằng tài khoản demo trong
`scripts/seed_demo.py` → tạo báo cáo mới.

## Luồng nghiệp vụ chính

```
┌─────────────┐    ┌──────────────┐    ┌──────────────────┐    ┌──────────┐
│ Môi giới    │───▶│ Upload sổ đỏ │───▶│ OCR + xác minh   │───▶│ Báo cáo  │
│ Nhập ngày   │    │ (PDF/ảnh)    │    │ địa chỉ → hướng  │    │ PDF gửi  │
│ sinh khách  │    │              │    │ Tính cung mệnh   │    │ khách    │
└─────────────┘    └──────────────┘    │ Match bát trạch  │    └──────────┘
                                       │ Chọn ngày tốt    │
                                       └──────────────────┘
```

**Mỗi báo cáo tốn 1 tín dụng** (~ 20.000 VND wholesale, môi giới bán lại cho khách
~ 200.000–500.000 VND, hoặc tặng kèm để chốt deal).

## Tuân thủ pháp lý

- **NĐ 13/2023/NĐ-CP** về bảo vệ dữ liệu cá nhân: hồ sơ sổ đỏ + ngày sinh là DLCN
  nhạy cảm. Repo lưu encrypted-at-rest (AES-256), retention mặc định 90 ngày, có
  endpoint `DELETE /v1/customers/{id}` để KH yêu cầu xóa.
- **Luật Đất đai 2024** (hiệu lực 01/08/2024) — sổ đỏ mẫu mới có QR code; OCR
  module fallback đọc cả mẫu cũ (TT 23/2014) và mẫu mới (TT 10/2024).
- **Phong thủy ≠ tư vấn đầu tư** — báo cáo có disclaimer rõ ràng, không phải lời
  khuyên đầu tư BĐS và không thay thế tư vấn pháp lý/kỹ thuật.

## Roadmap

- [x] Ontology v0: 8 cung mệnh, bát trạch, can chi 60 năm, ngày Hoàng Đạo
- [x] API v1: `/reports`, `/ocr/sodo`, `/auth`, `/health`
- [x] PDF report generator tiếng Việt
- [ ] OCR sổ đỏ thực tế (đang stub — cần dataset 500+ mẫu ẩn danh)
- [ ] Tích hợp VNPay sandbox
- [ ] Webhook cho CRM bên thứ ba (Pancake, Misa, Bizfly)
- [ ] Mobile app (React Native) — phase 2

## License

BUSL-1.1 — xem [LICENSE](./LICENSE). Tóm tắt: code public để audit, nhưng
**không được dùng để chạy dịch vụ phong thủy thương mại cạnh tranh** trong 3 năm.
Sau đó tự động chuyển sang Apache 2.0.

## Liên hệ

PR welcome. Bug / feedback: mở issue.
