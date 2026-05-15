"""Engine phong thủy — wrap ontology thành business-level service.

Service này là điểm duy nhất nơi backend gọi vào ontology, để dễ thay đổi nguồn
dữ liệu sau này (vd đổi sang ontology v2 mà không phải sửa endpoint).
"""

from __future__ import annotations

from datetime import date, timedelta

from phongthuy_ontology import (
    Gender,
    Purpose,
    bat_trach_for_cung,
    cung_menh_from_birth_date,
    match_house_direction,
    pick_good_days,
)

from phongthuy_bds.schemas.report import (
    CungMenhBlock,
    DirectionBlock,
    GoodDayBlock,
    HouseMatchBlock,
    ReportResultData,
)


GOOD_QUALITY_ADVICE: dict[str, str] = {
    "Sinh Khí": "Hướng tốt nhất cho khách. Phù hợp đặt cửa chính/cửa hàng.",
    "Thiên Y": "Hướng tốt cho sức khỏe gia đình. Phù hợp bếp/phòng ngủ chủ nhân.",
    "Diên Niên": "Hướng hợp tình duyên, hòa thuận. Phù hợp phòng ngủ vợ chồng.",
    "Phục Vị": "Hướng bình ổn, phù hợp bàn thờ, phòng học, phòng làm việc.",
}

BAD_QUALITY_ADVICE: dict[str, str] = {
    "Tuyệt Mệnh": (
        "Hướng xấu nặng nhất — nên thương lượng giảm giá hoặc tư vấn KH tìm "
        "bất động sản khác. Nếu KH vẫn quyết mua, đề xuất hóa giải bằng "
        "chuyển hướng cửa chính / dùng gương bát quái / cây cảnh."
    ),
    "Ngũ Quỷ": (
        "Hướng kỵ hao tài, kiện tụng — nếu khách dùng làm nhà ở thì cần hóa giải. "
        "Tránh tuyệt đối nếu khách mua làm cửa hàng/văn phòng."
    ),
    "Lục Sát": "Hướng thị phi, hóa giải bằng treo chuông gió / đá phong thủy.",
    "Họa Hại": "Hướng xấu nhẹ — chấp nhận được nếu điều chỉnh nội thất phù hợp.",
}


def build_report_payload(
    *,
    birth_date: date,
    gender: Gender,
    house_direction: str | None,
    purposes: list[str],
    good_day_window_start: date | None = None,
    good_day_window_end: date | None = None,
    good_day_top_k: int = 5,
) -> ReportResultData:
    """Sinh toàn bộ payload báo cáo phong thủy."""

    # ─── 1. Cung mệnh ───────────────────────────────────────────
    cm = cung_menh_from_birth_date(birth_date, gender)
    cung_menh_block = CungMenhBlock(
        cung=str(cm.cung),
        nhom=str(cm.nhom),
        ngu_hanh_cung=str(cm.ngu_hanh_cung),
        ngu_hanh_nap_am=str(cm.ngu_hanh_nap_am),
        can_chi=cm.can_chi,
        lunar_year=cm.lunar_year,
        lac_thu_so=cm.lac_thu_so,
        notes=list(cm.notes),
    )

    # ─── 2. Bát trạch — 8 hướng ──────────────────────────────────
    bat_trach = bat_trach_for_cung(cm.cung)
    bat_trach_blocks = [
        DirectionBlock(
            quality=str(d.quality),
            direction=d.direction,
            description=d.description,
            is_good=d.is_good,
        )
        for d in bat_trach
    ]

    # ─── 3. Match hướng nhà thực tế (nếu có) ─────────────────────
    house_match_block: HouseMatchBlock | None = None
    if house_direction:
        m = match_house_direction(cm.cung, house_direction)
        advice = (
            GOOD_QUALITY_ADVICE.get(str(m.quality)) if m.is_good
            else BAD_QUALITY_ADVICE.get(str(m.quality), "")
        )
        house_match_block = HouseMatchBlock(
            house_direction=m.direction,
            matched_quality=str(m.quality),
            is_good=m.is_good,
            advice=advice or m.description,
        )

    # ─── 4. Chọn ngày tốt ───────────────────────────────────────
    today = date.today()
    window_start = good_day_window_start or today
    window_end = good_day_window_end or (today + timedelta(days=90))

    good_days_by_purpose: dict[str, list[GoodDayBlock]] = {}
    for p in purposes:
        days = pick_good_days(
            chu_nha_year=birth_date.year,
            chu_nha_gender=gender,
            purpose=Purpose(p),
            from_date=window_start,
            to_date=window_end,
            top_k=good_day_top_k,
            only_recommended=True,
        )
        good_days_by_purpose[p] = [
            GoodDayBlock(
                solar_date=d.solar_date,
                lunar_date=f"{d.lunar_day:02d}/{d.lunar_month:02d}/{d.lunar_year}",
                can_chi_day=d.can_chi_day,
                hoang_dao_than=d.hoang_dao_than,
                is_hoang_dao=d.is_hoang_dao,
                score=d.score,
                reasons_good=list(d.reasons_good),
                reasons_bad=list(d.reasons_bad),
                is_recommended=d.is_recommended,
            )
            for d in days
        ]

    return ReportResultData(
        cung_menh=cung_menh_block,
        bat_trach=bat_trach_blocks,
        house_match=house_match_block,
        good_days=good_days_by_purpose,
    )
