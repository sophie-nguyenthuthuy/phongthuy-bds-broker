"""Test chọn ngày tốt."""

from datetime import date

import pytest

from phongthuy_ontology.cung_menh import Gender
from phongthuy_ontology.ngay_tot import (
    HOANG_DAO_THAN,
    Purpose,
    evaluate_day,
    pick_good_days,
)


class TestEvaluateDay:
    def test_returns_a_result(self) -> None:
        r = evaluate_day(date(2026, 6, 15), 1990, Gender.NAM, Purpose.NHAP_TRACH)
        assert r.solar_date == date(2026, 6, 15)
        assert r.can_chi_day  # non-empty
        assert r.hoang_dao_than

    def test_tam_nuong_day_penalized(self) -> None:
        # Quét 1 năm tìm ngày âm là Tam Nương rồi check.
        d = date(2026, 1, 1)
        while True:
            r = evaluate_day(d, 1990, Gender.NAM, Purpose.NHAP_TRACH)
            if r.lunar_day == 7:
                assert any("Tam Nương" in x for x in r.reasons_bad)
                break
            d = d.replace(day=d.day + 1) if d.day < 28 else d.replace(day=1, month=d.month + 1)
            if d.month > 3:
                pytest.fail("Không tìm thấy ngày Tam Nương trong Q1/2026")


class TestPickGoodDays:
    def test_returns_sorted_by_score(self) -> None:
        days = pick_good_days(
            chu_nha_year=1990,
            chu_nha_gender=Gender.NAM,
            purpose=Purpose.NHAP_TRACH,
            from_date=date(2026, 6, 1),
            to_date=date(2026, 6, 30),
            only_recommended=False,
        )
        assert len(days) > 0
        # Đã sắp giảm dần theo điểm.
        for a, b in zip(days, days[1:]):
            assert a.score >= b.score

    def test_top_k(self) -> None:
        days = pick_good_days(
            chu_nha_year=1990,
            chu_nha_gender=Gender.NAM,
            purpose=Purpose.NHAP_TRACH,
            from_date=date(2026, 1, 1),
            to_date=date(2026, 12, 31),
            top_k=5,
        )
        assert len(days) <= 5

    def test_only_recommended_filters(self) -> None:
        days = pick_good_days(
            chu_nha_year=1990,
            chu_nha_gender=Gender.NAM,
            purpose=Purpose.DONG_THO,
            from_date=date(2026, 1, 1),
            to_date=date(2026, 3, 31),
            only_recommended=True,
        )
        for d in days:
            assert d.is_recommended
            assert d.score > 0

    def test_xung_day_excluded(self) -> None:
        # 1990 = Canh Ngọ → chi Ngọ → xung Tý → ngày chi Tý phải bị loại
        # (hoặc ít nhất not recommended).
        days = pick_good_days(
            chu_nha_year=1990,
            chu_nha_gender=Gender.NAM,
            purpose=Purpose.NHAP_TRACH,
            from_date=date(2026, 1, 1),
            to_date=date(2026, 12, 31),
            only_recommended=True,
        )
        for d in days:
            assert "Tý" not in d.can_chi_day or "Tý" == d.can_chi_day.split()[0]  # Tý có thể là Can-prefix? Không, Tý chỉ là chi.

    def test_invalid_date_range_raises(self) -> None:
        with pytest.raises(ValueError):
            pick_good_days(
                chu_nha_year=1990,
                chu_nha_gender=Gender.NAM,
                purpose=Purpose.NHAP_TRACH,
                from_date=date(2026, 6, 30),
                to_date=date(2026, 6, 1),
            )


class TestHoangDao:
    def test_six_lucky_six_unlucky(self) -> None:
        assert len(HOANG_DAO_THAN) == 6
