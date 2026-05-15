"""Chọn ngày tốt động thổ / nhập trạch / khai trương.

Logic chính:
1. Với mỗi ngày dương trong khoảng [from_date, to_date]:
   - Tính can-chi ngày + can-chi tháng âm + ngày âm trong tháng.
   - Áp dụng Hoàng Đạo / Hắc Đạo theo 12 thần.
   - Loại Tam Nương (mùng 3, 7, 13, 18, 22, 27 âm).
   - Loại Nguyệt Kỵ (mùng 5, 14, 23 âm).
   - Loại ngày xung trực tiếp với chi tuổi chủ nhà (lục xung).
   - Loại ngày Sát Chủ / Thụ Tử / Trùng Tang theo bảng tháng âm.
2. Cộng điểm các yếu tố tốt, trừ điểm các yếu tố xấu.
3. Trả về danh sách ngày sắp theo điểm.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import StrEnum

from phongthuy_ontology.can_chi import (
    CHI,
    CHI_XUNG,
    CanChi,
    can_chi_of_day,
    can_chi_of_month,
    can_chi_of_year,
    is_hai,
    is_hinh,
)
from phongthuy_ontology.cung_menh import Gender
from phongthuy_ontology.lunar import solar_to_lunar


class Purpose(StrEnum):
    DONG_THO = "dong_tho"          # Động thổ — khởi công xây dựng
    NHAP_TRACH = "nhap_trach"      # Nhập trạch — về nhà mới
    KHAI_TRUONG = "khai_truong"    # Khai trương cửa hàng
    DAT_MONG = "dat_mong"          # Đặt móng (≈ động thổ nhưng nghiêm hơn)


# 12 Hoàng Đạo / Hắc Đạo thần.
THAN_NAMES: tuple[str, ...] = (
    "Thanh Long", "Minh Đường", "Thiên Hình", "Chu Tước",
    "Kim Quỹ", "Bảo Quang", "Bạch Hổ", "Ngọc Đường",
    "Thiên Lao", "Huyền Vũ", "Tư Mệnh", "Câu Trận",
)
HOANG_DAO_THAN: frozenset[str] = frozenset({
    "Thanh Long", "Minh Đường", "Kim Quỹ", "Bảo Quang",
    "Ngọc Đường", "Tư Mệnh",
})

# Khởi vị trí Thanh Long theo chi của tháng âm.
THANH_LONG_START_BY_MONTH_CHI: dict[str, str] = {
    "Dần": "Tý", "Thân": "Tý",
    "Mão": "Dần", "Dậu": "Dần",
    "Thìn": "Thìn", "Tuất": "Thìn",
    "Tỵ": "Ngọ", "Hợi": "Ngọ",
    "Ngọ": "Thân", "Tý": "Thân",
    "Mùi": "Tuất", "Sửu": "Tuất",
}

# Sát Chủ — tháng âm → chi ngày cần tránh khi xây dựng.
SAT_CHU_THANG: dict[int, str] = {
    1: "Tỵ", 2: "Tý", 3: "Mùi", 4: "Mão",
    5: "Thân", 6: "Tuất", 7: "Hợi", 8: "Sửu",
    9: "Ngọ", 10: "Dậu", 11: "Dần", 12: "Thìn",
}

# Thụ Tử — tháng âm → chi ngày cần tránh tuyệt đối (không động thổ, không khai trương).
THU_TU_THANG: dict[int, str] = {
    1: "Tuất", 2: "Thìn", 3: "Hợi", 4: "Tỵ",
    5: "Tý", 6: "Ngọ", 7: "Sửu", 8: "Mùi",
    9: "Dần", 10: "Thân", 11: "Mão", 12: "Dậu",
}

# Trùng Tang — tránh nhập trạch.
TRUNG_TANG_THANG: dict[int, str] = {
    1: "Giáp", 2: "Ất", 3: "Mậu", 4: "Bính", 5: "Đinh", 6: "Kỷ",
    7: "Canh", 8: "Tân", 9: "Mậu", 10: "Nhâm", 11: "Quý", 12: "Kỷ",
}

TAM_NUONG_DAYS: frozenset[int] = frozenset({3, 7, 13, 18, 22, 27})
NGUYET_KY_DAYS: frozenset[int] = frozenset({5, 14, 23})


@dataclass(frozen=True, slots=True)
class GoodDay:
    solar_date: date
    lunar_day: int
    lunar_month: int
    lunar_year: int
    can_chi_day: str
    hoang_dao_than: str
    is_hoang_dao: bool
    score: int
    reasons_good: tuple[str, ...] = field(default_factory=tuple)
    reasons_bad: tuple[str, ...] = field(default_factory=tuple)
    is_recommended: bool = True

    def to_dict(self) -> dict[str, str | int | bool | list[str]]:
        return {
            "solar_date": self.solar_date.isoformat(),
            "lunar_date": f"{self.lunar_day:02d}/{self.lunar_month:02d}/{self.lunar_year}",
            "can_chi_day": self.can_chi_day,
            "hoang_dao_than": self.hoang_dao_than,
            "is_hoang_dao": self.is_hoang_dao,
            "score": self.score,
            "reasons_good": list(self.reasons_good),
            "reasons_bad": list(self.reasons_bad),
            "is_recommended": self.is_recommended,
        }


def _than_for_day(month_chi: str, day_chi: str) -> str:
    """12 thần Hoàng Đạo của ngày, dựa vào chi tháng + chi ngày."""
    start_chi = THANH_LONG_START_BY_MONTH_CHI[month_chi]
    start_idx = CHI.index(start_chi)
    day_idx = CHI.index(day_chi)
    offset = (day_idx - start_idx) % 12
    return THAN_NAMES[offset]


def evaluate_day(
    solar_date: date,
    chu_nha_year: int,
    chu_nha_gender: Gender,
    purpose: Purpose,
) -> GoodDay:
    """Đánh giá một ngày cho mục đích cụ thể, trả về điểm và lý do."""
    lunar = solar_to_lunar(solar_date.day, solar_date.month, solar_date.year)
    day_cc: CanChi = can_chi_of_day(solar_date)
    month_cc: CanChi = can_chi_of_month(lunar.year, lunar.month)
    chu_nha_cc: CanChi = can_chi_of_year(chu_nha_year)

    than = _than_for_day(month_cc.chi, day_cc.chi)
    is_hoang_dao = than in HOANG_DAO_THAN

    score = 0
    good: list[str] = []
    bad: list[str] = []

    # ─── Hoàng Đạo / Hắc Đạo ─────────────────────────────────────
    if is_hoang_dao:
        score += 20
        good.append(f"Ngày Hoàng Đạo — sao {than}")
    else:
        score -= 10
        bad.append(f"Ngày Hắc Đạo — sao {than}")

    # ─── Tam Nương / Nguyệt Kỵ ───────────────────────────────────
    if lunar.day in TAM_NUONG_DAYS:
        score -= 30
        bad.append(f"Tam Nương — mùng {lunar.day} âm lịch")
    if lunar.day in NGUYET_KY_DAYS:
        score -= 20
        bad.append(f"Nguyệt Kỵ — mùng {lunar.day} âm lịch")

    # ─── Xung khắc tuổi chủ nhà ──────────────────────────────────
    if CHI_XUNG.get(day_cc.chi) == chu_nha_cc.chi:
        score -= 50
        bad.append(
            f"Lục xung — chi ngày {day_cc.chi} xung chi tuổi chủ nhà {chu_nha_cc.chi}"
        )
    elif is_hai(day_cc.chi, chu_nha_cc.chi):
        score -= 15
        bad.append(f"Lục hại — chi ngày {day_cc.chi} hại chi tuổi chủ nhà")
    elif is_hinh(day_cc.chi, chu_nha_cc.chi) and day_cc.chi != chu_nha_cc.chi:
        score -= 10
        bad.append(f"Tam hình — chi ngày {day_cc.chi} hình chi tuổi chủ nhà")
    elif day_cc.chi == chu_nha_cc.chi:
        # Ngày trùng chi với chủ nhà — thường có thể chấp nhận, "ngày của mình".
        score += 5
        good.append(f"Ngày {day_cc.chi} — trùng chi tuổi chủ nhà, hợp")

    # ─── Sát Chủ / Thụ Tử ────────────────────────────────────────
    if purpose in {Purpose.DONG_THO, Purpose.DAT_MONG}:
        if SAT_CHU_THANG.get(lunar.month) == day_cc.chi:
            score -= 40
            bad.append(f"Sát Chủ tháng {lunar.month} — kỵ động thổ")
    if THU_TU_THANG.get(lunar.month) == day_cc.chi:
        score -= 60
        bad.append(f"Thụ Tử tháng {lunar.month} — kỵ tuyệt đối")

    # ─── Trùng tang (riêng cho nhập trạch) ───────────────────────
    if purpose == Purpose.NHAP_TRACH:
        if TRUNG_TANG_THANG.get(lunar.month) == day_cc.can:
            score -= 30
            bad.append(f"Trùng tang tháng {lunar.month} — can {day_cc.can} kỵ nhập trạch")

    # ─── Cuối tuần (gợi ý mềm) ──────────────────────────────────
    if solar_date.weekday() in (5, 6) and purpose == Purpose.KHAI_TRUONG:
        score += 5
        good.append("Cuối tuần — thuận tiện đón khách khai trương")

    _ = chu_nha_gender  # reserved cho luật phân biệt nam/nữ trong tương lai

    is_recommended = score > 0 and not any("Lục xung" in r or "Thụ Tử" in r for r in bad)

    return GoodDay(
        solar_date=solar_date,
        lunar_day=lunar.day,
        lunar_month=lunar.month,
        lunar_year=lunar.year,
        can_chi_day=f"{day_cc.can} {day_cc.chi}",
        hoang_dao_than=than,
        is_hoang_dao=is_hoang_dao,
        score=score,
        reasons_good=tuple(good),
        reasons_bad=tuple(bad),
        is_recommended=is_recommended,
    )


def pick_good_days(
    chu_nha_year: int,
    chu_nha_gender: Gender,
    purpose: Purpose | str,
    from_date: date,
    to_date: date,
    top_k: int | None = None,
    only_recommended: bool = True,
) -> list[GoodDay]:
    """Quét khoảng ngày và chọn các ngày tốt nhất.

    Args:
        chu_nha_year: Năm sinh dương lịch của chủ nhà (sẽ dùng để tính can chi tuổi).
        chu_nha_gender: Giới tính chủ nhà.
        purpose: Mục đích — động thổ, nhập trạch, khai trương.
        from_date / to_date: Khoảng ngày dương lịch cần quét (inclusive).
        top_k: Nếu set, chỉ trả về top K ngày điểm cao nhất.
        only_recommended: True thì chỉ giữ ngày `is_recommended=True`.
    """
    if isinstance(purpose, str):
        purpose = Purpose(purpose)
    if from_date > to_date:
        raise ValueError("from_date phải <= to_date")

    days: list[GoodDay] = []
    d = from_date
    while d <= to_date:
        day = evaluate_day(d, chu_nha_year, chu_nha_gender, purpose)
        if not only_recommended or day.is_recommended:
            days.append(day)
        d += timedelta(days=1)

    days.sort(key=lambda x: x.score, reverse=True)
    if top_k is not None:
        days = days[:top_k]
    return days
