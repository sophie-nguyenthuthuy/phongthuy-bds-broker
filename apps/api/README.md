# phongthuy-bds (API)

FastAPI backend cho plug-in chốt deal môi giới BĐS.

## Endpoint chính

| Method | Path                                        | Mô tả                            |
|--------|---------------------------------------------|----------------------------------|
| POST   | `/v1/auth/register`                         | Tạo sàn môi giới + tài khoản owner |
| POST   | `/v1/auth/login`                            | Đăng nhập                        |
| GET    | `/v1/auth/me`                               | Profile user hiện tại            |
| POST   | `/v1/customers`                             | Tạo khách (cần consent DLCN)     |
| GET    | `/v1/customers`                             | Danh sách khách                  |
| DELETE | `/v1/customers/{id}`                        | Xóa khách (NĐ 13 Điều 16)        |
| POST   | `/v1/ocr/sodo`                              | Upload + OCR sổ đỏ               |
| PATCH  | `/v1/ocr/sodo/{id}/direction`               | Chốt hướng nhà                   |
| POST   | `/v1/reports`                               | Tạo báo cáo (trừ 1 credit)       |
| GET    | `/v1/reports/{id}`                          | Chi tiết báo cáo                 |
| GET    | `/v1/reports/{id}/pdf`                      | Tải PDF                          |
| GET    | `/v1/billing/balance`                       | Số dư tín dụng                   |
| POST   | `/v1/billing/topup`                         | Nạp credit (VNPay)               |
| POST   | `/v1/billing/vnpay/return`                  | Callback VNPay                   |
| GET    | `/v1/healthz` / `/v1/readyz`                | Health / readiness               |

OpenAPI docs: `http://localhost:8000/docs`.

## Dev

```bash
uv sync --all-packages
make dev-up                      # Postgres + Redis
make db-migrate
make seed                        # tạo demo tenant + user
make api-dev
```

Login demo: `owner@demo.local` / `changeme123`.

## Test

```bash
uv run pytest -v                 # unit
uv run pytest -m integration     # integration (cần docker)
```
