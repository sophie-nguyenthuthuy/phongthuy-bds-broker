# Tuân thủ pháp lý

## 1. NĐ 13/2023/NĐ-CP — Bảo vệ dữ liệu cá nhân

Áp dụng từ **01/07/2023**. Repo xử lý 3 loại DLCN:

| Trường            | Loại                            | Biện pháp                              |
|-------------------|---------------------------------|----------------------------------------|
| Họ tên khách      | DLCN cơ bản (Đ.2 k.1)           | Encrypt Fernet at rest                 |
| Ngày sinh         | DLCN cơ bản                     | Encrypt Fernet at rest                 |
| SĐT               | DLCN cơ bản                     | Encrypt Fernet at rest                 |
| Người đứng tên sổ | DLCN cơ bản (trong sổ đỏ)       | Lưu trong `extracted_data` JSON, ẩn ở log |

### Cam kết của hệ thống

- **Điều 11 — Quyền của chủ thể dữ liệu**: Endpoint `DELETE /v1/customers/{id}`
  xóa cứng hồ sơ + cascade xóa báo cáo. Không có soft-delete.
- **Điều 17 — Sự đồng ý**: Field `consent_given_at` lưu timestamp đồng thuận;
  field `consent_doc_url` lưu URL văn bản (PDF chữ ký) nếu môi giới tải lên.
- **Điều 21 — Lưu trữ và bảo vệ**: Tất cả PII encrypt Fernet (AES-128-CBC + HMAC),
  khóa nằm trong env không commit code.
- **Điều 27 — Thời hạn lưu trữ**: Mặc định 90 ngày
  (`DLCN_RETENTION_DAYS`). Cron job (chưa implement v0) sẽ xóa records có
  `delete_after < CURRENT_DATE`.

### Chưa làm trong v0

- DPIA (Data Protection Impact Assessment) — cần làm trước khi đi prod.
- Notify Bộ Công an về xử lý DLCN khi hoạt động thực tế (Đ.43).
- Audit log truy cập DLCN (Đ.21 k.2 đ).

## 2. Luật Đất đai 2024

Hiệu lực **01/08/2024**. Tác động chính:

- **Mẫu sổ đỏ mới** theo TT 10/2024/TT-BTNMT — có QR code, gộp đất + tài sản
  trên đất vào 1 giấy. Module OCR phải nhận biết cả mẫu cũ (TT 23/2014) lẫn
  mẫu mới.
- **Mã loại đất** thay đổi (Phụ lục 01 Luật mới): ODT/CLN/ONT/… Hệ thống
  chỉ trích xuất mã, không phán đoán hợp pháp.

## 3. Disclaimer trên báo cáo

Mọi PDF phát hành đều chứa câu disclaimer cố định:

> Báo cáo phong thủy mang tính tham khảo văn hóa Việt Nam, không phải tư vấn
> đầu tư bất động sản, pháp lý hay kỹ thuật xây dựng. Quý khách nên kết hợp
> với ý kiến chuyên gia chuyên ngành trước khi ra quyết định mua/bán/xây dựng.

## 4. Thuế

- Tín dụng môi giới nạp = doanh thu chịu VAT 10% (dịch vụ).
- Mỗi giao dịch tạo `CreditTransaction` ghi `reference` (mã đơn VNPay) → đủ
  audit trail cho hóa đơn điện tử (TT 78/2021/TT-BTC + NĐ 123/2020/NĐ-CP).
- Tích hợp eInvoice (Misa, Viettel, Bkav…) là **roadmap phase 2** — không
  trong v0.

## 5. Bảo mật

- JWT secret 32+ ký tự, không commit.
- Bcrypt cho password (default).
- CORS whitelist từ env, không `*` trong prod.
- Rate-limiting **chưa làm** trong v0 — cần thêm `slowapi` trước khi public.
