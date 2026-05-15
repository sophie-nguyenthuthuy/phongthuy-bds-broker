"""Test chuyển đổi âm/dương lịch — đối chiếu với Lịch Vạn Niên Hồ Ngọc Đức."""

import pytest

from phongthuy_ontology.lunar import lunar_to_solar, solar_to_lunar


class TestSolarToLunar:
    @pytest.mark.parametrize(
        "solar,expected_lunar",
        [
            # Tết Nguyên Đán những năm gần đây — đối chiếu lịch in.
            ((10, 2, 2024), (1, 1, 2024)),    # Tết Giáp Thìn
            ((29, 1, 2025), (1, 1, 2025)),    # Tết Ất Tỵ
            ((17, 2, 2026), (1, 1, 2026)),    # Tết Bính Ngọ
            ((1, 1, 2026), (13, 11, 2025)),
        ],
    )
    def test_known_dates(
        self, solar: tuple[int, int, int], expected_lunar: tuple[int, int, int],
    ) -> None:
        d, m, y = solar
        lunar = solar_to_lunar(d, m, y)
        assert (lunar.day, lunar.month, lunar.year) == expected_lunar


class TestLunarToSolar:
    def test_tet_2024_round_trip(self) -> None:
        dd, mm, yy = lunar_to_solar(1, 1, 2024)
        assert (dd, mm, yy) == (10, 2, 2024)

    def test_round_trip_random_dates(self) -> None:
        # Round-trip solar → lunar → solar phải giữ nguyên.
        for dd, mm, yy in [(15, 6, 2024), (1, 9, 2025), (20, 12, 2026)]:
            lunar = solar_to_lunar(dd, mm, yy)
            back = lunar_to_solar(lunar.day, lunar.month, lunar.year, lunar.is_leap)
            assert back == (dd, mm, yy)
