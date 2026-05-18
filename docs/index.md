# Phong Thủy BĐS — Tài liệu

> Plug-in chốt deal cho môi giới bất động sản Việt Nam. Nhập **sổ đỏ + ngày
> sinh khách** → trong 30 giây có ngay báo cáo phong thủy chuyên nghiệp:
> hợp tuổi, hướng nhà, ngày tốt động thổ / nhập trạch.

[:material-source-repository: Repo trên GitHub](https://github.com/sophie-nguyenthuthuy/phongthuy-bds-broker){ .md-button }
[:material-rocket-launch: Quickstart](#quickstart){ .md-button .md-button--primary }

## Bộ tài liệu

<div class="grid cards" markdown>

- :material-sitemap: __[Kiến trúc](architecture.md)__

    Sơ đồ dòng dữ liệu, tách lớp, multi-tenant model, ghi chú scaling.

- :material-book-open-variant: __[Đặc tả phong thủy](feng-shui-spec.md)__

    Công thức cung mệnh, bát trạch, can chi, ngày tốt — kèm nguồn từ Bát
    Trạch Minh Cảnh + Hoàng Lịch Thông Thư.

- :material-scale-balance: __[Tuân thủ pháp lý](legal-compliance.md)__

    NĐ 13/2023/NĐ-CP (DLCN), Luật Đất đai 2024, TT 23/2014 vs TT 10/2024
    (sổ đỏ), disclaimer.

- :material-account-group: __[Đóng góp](contributing.md)__

    Setup dev, convention, nguyên tắc thêm/sửa luật phong thủy, báo cáo lỗ
    hổng bảo mật.

</div>

## Vì sao defensible? { #defensible }

Khác với các tool phong thủy generic của Trung Quốc port sang, repo này khác
biệt ở 3 điểm:

1. **Ontology phiên bản hóa** — Phong thủy được mã hóa thành YAML +
   Pydantic, không phải LLM hallucination. Mỗi cung mệnh, mỗi bộ hướng,
   mỗi ngày tốt đều **trace được về nguồn** (Hoàng Lịch Thông Thư, Bát
   Trạch Minh Cảnh).
2. **OCR sổ đỏ VN-canonical** — Trích xuất chính xác layout sổ đỏ theo
   **Luật Đất đai 2024** và TT 10/2024/TT-BTNMT: thửa, tờ bản đồ, diện
   tích, mục đích sử dụng, thời hạn, người sử dụng đất. Không phải OCR
   generic.
3. **Plug-in API-first** — Tích hợp được vào CRM môi giới sẵn có
   (HomeService, Rever, Propzy-style) qua REST + webhook. Không bắt môi
   giới đổi workflow.

## Quickstart { #quickstart }

```bash
git clone https://github.com/sophie-nguyenthuthuy/phongthuy-bds-broker
cd phongthuy-bds-broker
cp .env.example .env

make install
make dev-up           # Postgres + Redis
make db-migrate
make seed             # demo tenant + owner / broker
make api-dev          # :8000
make web-dev          # :3000
```

Đăng nhập demo: `owner@demo.local` / `changeme123`.

## Smoke test ontology

```python
from datetime import date
from phongthuy_ontology import (
    cung_menh_from_birth_date, bat_trach_for_cung,
    pick_good_days, Gender, Purpose,
)

# 1990 nam → cung Khảm (Đông tứ mệnh)
r = cung_menh_from_birth_date(date(1990, 8, 15), Gender.NAM)
print(r.cung, r.nhom, r.can_chi)  # Khảm Đông tứ mệnh Canh Ngọ

# 8 hướng theo bát trạch
for d in bat_trach_for_cung(r.cung):
    print(d.quality, d.direction, "✓" if d.is_good else "✗")

# Top 3 ngày nhập trạch tháng 6/2026
days = pick_good_days(
    chu_nha_year=1990, chu_nha_gender=Gender.NAM,
    purpose=Purpose.NHAP_TRACH,
    from_date=date(2026, 6, 1), to_date=date(2026, 6, 30),
    top_k=3,
)
for d in days:
    print(d.solar_date, d.can_chi_day, d.hoang_dao_than, d.score)
```

## Disclaimer

Báo cáo phong thủy mang tính tham khảo văn hóa Việt Nam, **không phải tư
vấn đầu tư bất động sản, pháp lý hay kỹ thuật xây dựng**. Quý khách nên
kết hợp với ý kiến chuyên gia chuyên ngành trước khi ra quyết định.

Dữ liệu cá nhân được xử lý theo NĐ 13/2023/NĐ-CP. Xem
[Tuân thủ pháp lý](legal-compliance.md) để biết chi tiết.
