"""Test bát trạch — đối chiếu Bát Trạch Minh Cảnh."""

import pytest

from phongthuy_ontology.bat_trach import (
    GOOD_QUALITIES,
    DirectionQuality,
    bat_trach_for_cung,
    direction_from_degrees,
    match_house_direction,
)
from phongthuy_ontology.cung_menh import Cung


class TestBatTrach:
    def test_all_8_cung_have_data(self) -> None:
        for c in Cung:
            dirs = bat_trach_for_cung(c)
            assert len(dirs) == 8

    def test_kham_sinh_khi_is_dong_nam(self) -> None:
        dirs = bat_trach_for_cung("Khảm")
        sinh_khi = next(d for d in dirs if d.quality == DirectionQuality.SINH_KHI)
        assert sinh_khi.direction == "Đông Nam"
        assert sinh_khi.is_good

    def test_can_sinh_khi_is_tay(self) -> None:
        dirs = bat_trach_for_cung("Càn")
        sinh_khi = next(d for d in dirs if d.quality == DirectionQuality.SINH_KHI)
        assert sinh_khi.direction == "Tây"

    def test_ly_tuyet_menh_is_tay_bac(self) -> None:
        dirs = bat_trach_for_cung("Ly")
        tuyet = next(d for d in dirs if d.quality == DirectionQuality.TUYET_MENH)
        assert tuyet.direction == "Tây Bắc"
        assert not tuyet.is_good

    def test_4_good_4_bad(self) -> None:
        for c in Cung:
            dirs = bat_trach_for_cung(c)
            good_count = sum(1 for d in dirs if d.is_good)
            assert good_count == 4
            for d in dirs:
                if d.quality in GOOD_QUALITIES:
                    assert d.is_good
                else:
                    assert not d.is_good


class TestMatchHouseDirection:
    def test_kham_likes_dong_nam(self) -> None:
        r = match_house_direction("Khảm", "Đông Nam")
        assert r.is_good
        assert r.quality == DirectionQuality.SINH_KHI

    def test_kham_dislikes_tay_nam(self) -> None:
        r = match_house_direction("Khảm", "Tây Nam")
        assert not r.is_good
        assert r.quality == DirectionQuality.TUYET_MENH

    def test_invalid_direction_raises(self) -> None:
        with pytest.raises(ValueError):
            match_house_direction("Khảm", "Đông Đông")


class TestDirectionFromDegrees:
    @pytest.mark.parametrize(
        "deg,expected",
        [
            (0, "Bắc"),
            (45, "Đông Bắc"),
            (90, "Đông"),
            (135, "Đông Nam"),
            (180, "Nam"),
            (225, "Tây Nam"),
            (270, "Tây"),
            (315, "Tây Bắc"),
            (359, "Bắc"),
            (360, "Bắc"),
            (720, "Bắc"),  # mod 360
        ],
    )
    def test_degrees_to_direction(self, deg: float, expected: str) -> None:
        assert direction_from_degrees(deg) == expected
