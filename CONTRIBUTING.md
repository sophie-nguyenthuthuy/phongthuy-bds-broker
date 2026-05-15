# Đóng góp

## Setup

```bash
# 1. Cài tooling
brew install uv pnpm docker

# 2. Clone + setup env
cp .env.example .env
make install
make dev-up
make db-migrate
make seed

# 3. Chạy
make api-dev   # :8000
make web-dev   # :3000
```

## Workflow

1. Mở issue mô tả bug / feature.
2. Branch theo convention `fix/<slug>` hoặc `feat/<slug>`.
3. Đảm bảo `make lint test` xanh trước khi mở PR.
4. PR template: mô tả thay đổi + checklist.

## Conventions

- **Tiếng Việt** trong docstring, comment, commit message, PR description.
- **Tiếng Anh** trong tên hàm/biến/class — để công cụ static analysis hoạt động.
- File path nội bộ luôn dùng UTF-8 chuẩn (có dấu) ở docs/yaml, ASCII ở filename
  (ví dụ `bat_trach.yaml`, không `bat_trạch.yaml`).
- Migration alembic: tên `YYYYMMDD_NNNN_<slug>.py`, autogenerate rồi review bằng tay.

## Nguyên tắc phong thủy

Khi thêm/sửa luật phong thủy:

1. Chỉnh **dữ liệu** (`packages/ontology/data/*.yaml`) trước, không hardcode Python.
2. Mỗi luật phải kèm **nguồn** (tên sách, tác giả, chương).
3. Mỗi luật mới phải có **test case** đối chiếu với app phong thủy phổ biến
   (Tuvixemboi, NgaytotXau, Lichviet).
4. Đưa vào `docs/feng-shui-spec.md`.

## Bảo mật

- **Không commit** `.env`, sổ đỏ thật, ngày sinh thật.
- Sổ đỏ trong `packages/sample-sodo/` phải ẩn danh hóa (xóa tên, số CCCD,
  số thửa thật) bằng tool dedicated, không phải copy thủ công.
- Báo cáo lỗ hổng bảo mật: gửi email riêng, **không mở issue public**.
