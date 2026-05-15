# Đặc tả nguyên lý phong thủy đã encode

Tài liệu này mô tả **chính xác công thức** mà repo đang chạy. Khi thầy phong
thủy bảo "tôi không đồng ý chỗ này", đến đây để chỉnh.

## 1. Cung mệnh

Đầu vào: năm âm lịch (`lunar_year`) + giới tính.

### Quy tắc rút gọn Lạc Thư

Lấy **2 chữ số cuối** của năm âm lịch, cộng dồn các chữ số đến khi còn 1 chữ
số (1–9). Ví dụ: 1990 → `9 + 0 = 9`; 1985 → `8 + 5 = 13 → 1 + 3 = 4`.

### Nam giới

| Sinh trước 2000     | Sinh từ 2000        |
|---------------------|---------------------|
| `(10 − s) mod 9`    | `(9 − s) mod 9`     |
| `0 → 9`             | `0 → 9`             |
| Nếu kết quả `= 5`: quy về 2 (Khôn)                       |

### Nữ giới

| Sinh trước 2000     | Sinh từ 2000        |
|---------------------|---------------------|
| `(5 + s) mod 9`     | `(6 + s) mod 9`     |
| `0 → 9`             | `0 → 9`             |
| Nếu kết quả `= 5`: quy về 8 (Cấn)                        |

### Lạc Thư số → Cung

| Số | Cung   | Hậu Thiên     | Ngũ hành | Nhóm           |
|----|--------|---------------|----------|----------------|
| 1  | Khảm   | Bắc           | Thủy     | Đông tứ mệnh   |
| 2  | Khôn   | Tây Nam       | Thổ      | Tây tứ mệnh    |
| 3  | Chấn   | Đông          | Mộc      | Đông tứ mệnh   |
| 4  | Tốn    | Đông Nam      | Mộc      | Đông tứ mệnh   |
| 6  | Càn    | Tây Bắc       | Kim      | Tây tứ mệnh    |
| 7  | Đoài   | Tây           | Kim      | Tây tứ mệnh    |
| 8  | Cấn    | Đông Bắc      | Thổ      | Tây tứ mệnh    |
| 9  | Ly     | Nam           | Hỏa      | Đông tứ mệnh   |

### Lưu ý quan trọng

- Năm âm lịch ≠ năm dương lịch nếu sinh trước Tết Nguyên Đán. Repo có hàm
  `cung_menh_from_birth_date(date, gender)` xử lý đúng việc này (chuyển âm
  trước rồi mới áp công thức).
- Có nhiều phái phong thủy với công thức khác (Đông Phương Sóc, Mai Hoa Dịch
  Số, Tử Vi…). Repo dùng **Bát Trạch Minh Cảnh** vì phổ biến nhất trong
  thực hành chọn nhà ở VN.

## 2. Bát trạch — 8 hướng

Mỗi cung có 4 hướng tốt + 4 hướng xấu, gồm 8 sao:

| Sao            | Tính chất                       | Mức độ          |
|----------------|---------------------------------|-----------------|
| Sinh Khí       | Tài lộc, công danh              | Tốt nhất        |
| Thiên Y        | Sức khỏe, trường thọ            | Rất tốt         |
| Diên Niên      | Tình duyên, hòa thuận           | Tốt             |
| Phục Vị        | Bình ổn, học hành               | Tốt (chính vị)  |
| Họa Hại        | Ốm đau nhẹ, hao tài nhẹ         | Xấu nhẹ         |
| Lục Sát        | Tranh cãi, thị phi              | Xấu vừa         |
| Ngũ Quỷ        | Hao tài, kiện tụng              | Xấu nặng        |
| Tuyệt Mệnh     | Tổn mạng                        | Xấu nhất        |

Mapping cụ thể cho từng cung: xem [packages/ontology/data/bat_trach.yaml](../packages/ontology/data/bat_trach.yaml).

Nguồn: **Bát Trạch Minh Cảnh** (八宅明鏡), Cố Cảnh Hiên 顾镜轩, đời Thanh.

## 3. Can Chi & Nạp âm

- **10 thiên can**: Giáp, Ất, Bính, Đinh, Mậu, Kỷ, Canh, Tân, Nhâm, Quý.
- **12 địa chi**: Tý, Sửu, Dần, Mão, Thìn, Tỵ, Ngọ, Mùi, Thân, Dậu, Tuất, Hợi.
- **Chu kỳ 60 năm**: kết hợp (chỉ kết hợp Can lẻ với Chi lẻ — như Giáp Tý, Ất
  Sửu — không có Giáp Sửu).

Anchor: **1984 = Giáp Tý** (đầu chu kỳ hiện đại).

### Ngày Can-Chi

Anchor: **11/01/2001 = ngày Giáp Tý**. Mỗi ngày dương lịch trượt 1 vị trí can
+ 1 vị trí chi.

### Nạp âm

30 cặp nạp âm tương ứng với 60 cặp can-chi (cứ 2 cặp can-chi có cùng nạp âm).
Mỗi nạp âm thuộc 1 trong 5 hành. Ví dụ:
- Giáp Tý + Ất Sửu = **Hải Trung Kim** (Kim trong biển)
- Canh Ngọ + Tân Mùi = **Lộ Bàng Thổ** (đất ven đường)

Bảng đầy đủ: [can_chi.py NAP_AM_TABLE](../packages/ontology/src/phongthuy_ontology/can_chi.py).

## 4. Lục xung / Lục hại / Tam hình

### Lục xung (xung khắc trực tiếp — nặng nhất)

```
Tý ↔ Ngọ, Sửu ↔ Mùi, Dần ↔ Thân,
Mão ↔ Dậu, Thìn ↔ Tuất, Tỵ ↔ Hợi
```

### Lục hại

```
Tý ↔ Mùi, Sửu ↔ Ngọ, Dần ↔ Tỵ,
Mão ↔ Thìn, Thân ↔ Hợi, Dậu ↔ Tuất
```

### Tam hình

```
Dần - Tỵ - Thân (vô ân)
Sửu - Tuất - Mùi (vô lễ)
Tý - Mão (tương hình)
Thìn, Ngọ, Dậu, Hợi (tự hình)
```

## 5. Chọn ngày tốt

Cho mỗi ngày dương lịch:

1. Tính **can-chi ngày** từ JDN.
2. Tính **can-chi tháng âm** từ năm âm.
3. **Hoàng Đạo / Hắc Đạo**: dựa vào chi tháng, xác định vị trí Thanh Long;
   12 thần (6 lành + 6 dữ) trượt theo chi ngày.
4. **Tam Nương**: mùng 3, 7, 13, 18, 22, 27 âm → trừ điểm.
5. **Nguyệt Kỵ**: mùng 5, 14, 23 âm → trừ điểm nhẹ.
6. **Sát Chủ / Thụ Tử** theo tháng âm — bảng tra cố định.
7. **Lục xung tuổi chủ nhà** → loại tuyệt đối nếu `chi_ngày XUNG chi_tuổi`.
8. **Trùng Tang** (chỉ áp dụng cho nhập trạch) — theo can ngày × tháng.

### Hệ số điểm (tổng đại)

| Yếu tố                    | Điểm   |
|---------------------------|--------|
| Hoàng Đạo                 | +20    |
| Hắc Đạo                   | −10    |
| Tam Nương                 | −30    |
| Nguyệt Kỵ                 | −20    |
| Lục xung tuổi chủ nhà     | −50    |
| Lục hại tuổi chủ nhà      | −15    |
| Tam hình                  | −10    |
| Ngày trùng chi chủ nhà    | +5     |
| Sát Chủ (đông thổ)        | −40    |
| Thụ Tử                    | −60    |
| Trùng Tang (nhập trạch)   | −30    |

Ngày được khuyến nghị (`is_recommended=True`) nếu `score > 0` và không có
yếu tố loại tuyệt đối (lục xung, Thụ Tử).

Hệ số ở đây là **kinh nghiệm** — có thể chỉnh trong `ngay_tot.py`. Khi thầy
phong thủy yêu cầu tinh chỉnh, sửa magic numbers ở đây.
