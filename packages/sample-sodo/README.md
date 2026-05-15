# Mẫu sổ đỏ ẩn danh (test fixtures)

Để training + test OCR, cần dataset sổ đỏ thật **đã ẩn danh**.

## Cách ẩn danh hóa

Trước khi commit vào repo, dùng tool nội bộ (sẽ implement ở phase 2):

1. **Tên người đứng tên** → "Nguyễn Văn A", "Trần Thị B", …
2. **Số CCCD** → mask `0XXXXXXX9012`
3. **Số thửa** → giữ nguyên format nhưng đổi sang số fake
4. **Địa chỉ chi tiết** → giữ phường/xã, đổi số nhà + tên đường
5. **QR code** → blur

License của mẫu: **CC-BY-SA 4.0** — môi giới sàn nào upload mẫu chia sẻ phải
đồng ý cho dùng open dataset.

## Trạng thái hiện tại

v0: trống — đang thu thập. Liên hệ team data nếu có nguồn sổ đỏ đã ẩn danh hợp pháp.

## Format đề xuất

```
packages/sample-sodo/
├── tt23_2014/
│   ├── ONT_TPHCM/
│   │   ├── 001.pdf
│   │   └── 001.labels.json     # ground-truth fields
│   └── ODT_HaNoi/
└── tt10_2024/
    └── ...
```

File `*.labels.json` schema:
```json
{
  "template_version": "tt23_2014",
  "fields": {
    "nguoi_su_dung": "Nguyễn Văn A",
    "thua_dat_so": "123",
    ...
  },
  "bbox": {
    "nguoi_su_dung": [120, 340, 580, 380],
    ...
  }
}
```
