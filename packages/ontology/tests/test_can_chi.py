"""Test can-chi của năm và ngày — đối chiếu với lịch vạn niên VN."""

from datetime import date

import pytest

from phongthuy_ontology.can_chi import (
    CHI_XUNG,
    can_chi_of_day,
    can_chi_of_month,
    can_chi_of_year,
    is_hai,
    is_hinh,
    is_xung,
    nap_am,
)


class TestCanChiYear:
    @pytest.mark.parametrize(
        "year,expected_can,expected_chi",
        [
            (1984, "Giáp", "Tý"),     # mốc đầu chu kỳ 60 năm hiện đại
            (1990, "Canh", "Ngọ"),
            (1995, "Ất", "Hợi"),
            (2000, "Canh", "Thìn"),
            (2024, "Giáp", "Thìn"),
            (2026, "Bính", "Ngọ"),
            (1985, "Ất", "Sửu"),
        ],
    )
    def test_year_can_chi(self, year: int, expected_can: str, expected_chi: str) -> None:
        cc = can_chi_of_year(year)
        assert cc.can == expected_can
        assert cc.chi == expected_chi

    def test_nap_am_examples(self) -> None:
        # Đối chiếu các cặp nổi tiếng.
        assert nap_am("Giáp", "Tý") == "Hải Trung Kim"
        assert nap_am("Canh", "Ngọ") == "Lộ Bàng Thổ"
        assert nap_am("Mậu", "Thìn") == "Đại Lâm Mộc"

    def test_60_year_cycle(self) -> None:
        # Sau 60 năm phải lặp lại.
        a = can_chi_of_year(1984)
        b = can_chi_of_year(2044)
        assert (a.can, a.chi) == (b.can, b.chi)


class TestCanChiDay:
    def test_anchor_day(self) -> None:
        """11/01/2001 = ngày Giáp Tý — neo của chu kỳ."""
        cc = can_chi_of_day(date(2001, 1, 11))
        assert cc.can == "Giáp"
        assert cc.chi == "Tý"

    def test_day_60_cycle(self) -> None:
        """Sau đúng 60 ngày phải lặp lại can-chi."""
        from datetime import timedelta
        a = can_chi_of_day(date(2026, 1, 1))
        b = can_chi_of_day(date(2026, 1, 1) + timedelta(days=60))
        assert (a.can, a.chi) == (b.can, b.chi)

    def test_consecutive_days_advance(self) -> None:
        d1 = can_chi_of_day(date(2001, 1, 11))  # Giáp Tý
        d2 = can_chi_of_day(date(2001, 1, 12))  # Ất Sửu
        assert d2.can == "Ất"
        assert d2.chi == "Sửu"


class TestCanChiMonth:
    def test_first_month_of_giap_year(self) -> None:
        """Năm Giáp → tháng Giêng (Dần) là Bính Dần."""
        cc = can_chi_of_month(2024, 1)  # 2024 = Giáp Thìn
        assert cc.can == "Bính"
        assert cc.chi == "Dần"

    def test_month_chi_progression(self) -> None:
        """Tháng âm 1=Dần, 2=Mão, ..., 11=Tý, 12=Sửu."""
        expected = ["Dần", "Mão", "Thìn", "Tỵ", "Ngọ", "Mùi",
                    "Thân", "Dậu", "Tuất", "Hợi", "Tý", "Sửu"]
        for m, chi in enumerate(expected, start=1):
            assert can_chi_of_month(2024, m).chi == chi


class TestXungHaiHinh:
    def test_luc_xung(self) -> None:
        assert is_xung("Tý", "Ngọ")
        assert is_xung("Ngọ", "Tý")
        assert not is_xung("Tý", "Sửu")
        assert CHI_XUNG["Dần"] == "Thân"

    def test_luc_hai(self) -> None:
        assert is_hai("Tý", "Mùi")
        assert not is_hai("Tý", "Sửu")

    def test_tam_hinh(self) -> None:
        assert is_hinh("Dần", "Tỵ")
        assert is_hinh("Tỵ", "Thân")
        assert is_hinh("Dần", "Thân")
