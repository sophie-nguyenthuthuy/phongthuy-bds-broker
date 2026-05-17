"""Test engine: ráp ontology → payload báo cáo."""

from __future__ import annotations

from datetime import date

from phongthuy_bds.services.feng_shui.engine import build_report_payload
from phongthuy_ontology import Gender


class TestBuildReportPayload:
    def test_basic_payload(self) -> None:
        result = build_report_payload(
            birth_date=date(1990, 8, 15),
            gender=Gender.NAM,
            house_direction="Đông Nam",
            purposes=["nhap_trach"],
            good_day_window_start=date(2026, 6, 1),
            good_day_window_end=date(2026, 6, 30),
            good_day_top_k=3,
        )
        assert result.cung_menh.cung == "Khảm"
        assert result.cung_menh.nhom == "Đông tứ mệnh"
        assert len(result.bat_trach) == 8
        assert result.house_match is not None
        assert result.house_match.house_direction == "Đông Nam"
        assert result.house_match.is_good
        assert "nhap_trach" in result.good_days
        assert len(result.good_days["nhap_trach"]) <= 3

    def test_no_house_direction_means_no_match(self) -> None:
        result = build_report_payload(
            birth_date=date(1990, 8, 15),
            gender=Gender.NAM,
            house_direction=None,
            purposes=["nhap_trach"],
        )
        assert result.house_match is None

    def test_multiple_purposes(self) -> None:
        result = build_report_payload(
            birth_date=date(1985, 3, 20),
            gender=Gender.NAM,
            house_direction="Tây",
            purposes=["dong_tho", "nhap_trach", "khai_truong"],
            good_day_window_start=date(2026, 6, 1),
            good_day_window_end=date(2026, 8, 31),
        )
        assert set(result.good_days.keys()) == {"dong_tho", "nhap_trach", "khai_truong"}
