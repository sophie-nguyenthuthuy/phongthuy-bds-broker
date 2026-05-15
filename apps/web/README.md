# phongthuy-bds-web

Next.js 14 (App Router) — broker dashboard.

## Pages

| Route                  | Mô tả                                                      |
|------------------------|------------------------------------------------------------|
| `/`                    | Landing — pitch + 3-step CTA                              |
| `/login`               | Đăng nhập                                                  |
| `/register`            | Đăng ký sàn mới                                            |
| `/dashboard`           | Danh sách báo cáo, số dư tín dụng                          |
| `/reports/new`         | Wizard 4 bước: khách → sổ đỏ → hướng → mục đích           |
| `/reports/[id]`        | Xem chi tiết + tải PDF                                     |

## Stack

- Next.js 14 App Router + TypeScript strict
- Tailwind CSS + ad-hoc components (no shadcn dependency)
- Axios + interceptor (auto-attach JWT, auto-redirect /login on 401)
- `Be Vietnam Pro` font (Google Fonts)

## Dev

```bash
pnpm install
pnpm dev
```

Yêu cầu API chạy tại `NEXT_PUBLIC_API_URL` (mặc định `http://localhost:8000`).
