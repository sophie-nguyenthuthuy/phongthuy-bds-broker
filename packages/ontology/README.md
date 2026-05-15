# phongthuy-ontology

Phong thủy được mã hóa thành **dữ liệu phiên bản hóa**, không phải hardcode.

## Vì sao tách thành package riêng?

Toàn bộ "tri thức nghiệp vụ" của hệ thống (cung mệnh, bát trạch, can chi, ngũ hành nạp âm, ngày Hoàng Đạo) ở đây.
Nếu sau này thầy phong thủy cần chỉnh — ví dụ đổi cách map cung mệnh cho người sinh sau 2024 (Cửu Vận) —
chỉ chỉnh YAML, không đụng vào API/web.

## API chính

```python
from datetime import date
from phongthuy_ontology import (
    cung_menh_from_birth,
    bat_trach_for_cung,
    can_chi_of_year,
    can_chi_of_day,
    pick_good_days,
    Gender,
)

# 1. Cung mệnh
result = cung_menh_from_birth(year=1990, gender=Gender.NAM)
# → CungMenhResult(cung="Càn", nhom="Tay Tu Menh", ngu_hanh="Kim", ...)

# 2. Bát trạch — 8 hướng cho cung Càn
trach = bat_trach_for_cung("Càn")
# → [Direction(name="Sinh Khí", direction="Tây", ...), ...]

# 3. Can chi năm sinh
cc = can_chi_of_year(1990)
# → CanChi(can="Canh", chi="Ngọ", nap_am="Lộ Bàng Thổ")

# 4. Ngày tốt động thổ trong tháng 6/2026
good = pick_good_days(
    chu_nha_year=1990,
    chu_nha_gender=Gender.NAM,
    purpose="dong_tho",      # dong_tho | nhap_trach | khai_truong
    from_date=date(2026, 6, 1),
    to_date=date(2026, 6, 30),
)
# → [GoodDay(date=2026-06-15, hoang_dao_than="Thanh Long", reasons=[...]), ...]
```

## Nguồn

- **Bát Trạch Minh Cảnh** (八宅明鏡, Cố Cảnh Hiên 顾镜轩, Thanh) — cơ sở 8 hướng/cung.
- **Hoàng Lịch Thông Thư** — Hoàng Đạo / Hắc Đạo 12 thần.
- **Lịch Vạn Niên** Hồ Ngọc Đức — chuyển đổi âm/dương lịch theo kinh tuyến 105°Đ.
- **Lạc Thư Cửu Cung** — mapping 1–9 → cung mệnh.

## Test

```bash
cd packages/ontology && uv run pytest -v
```

Test cases lấy từ các app phong thủy phổ biến (TuviSo, NgaytotXau, Lichviet) để đối chiếu.
