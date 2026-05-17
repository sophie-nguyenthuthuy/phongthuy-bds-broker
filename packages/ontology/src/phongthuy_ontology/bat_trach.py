"""Bát Trạch — match cung mệnh với hướng nhà.

Đọc dữ liệu từ `data/bat_trach.yaml` để có thể chỉnh sửa mà không đụng code.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from phongthuy_ontology.cung_menh import Cung

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "bat_trach.yaml"

DIRECTION_DEG: dict[str, tuple[float, float]] = {
    "Bắc":        (337.5, 22.5),
    "Đông Bắc":   (22.5, 67.5),
    "Đông":       (67.5, 112.5),
    "Đông Nam":   (112.5, 157.5),
    "Nam":        (157.5, 202.5),
    "Tây Nam":    (202.5, 247.5),
    "Tây":        (247.5, 292.5),
    "Tây Bắc":    (292.5, 337.5),
}


class DirectionQuality(StrEnum):
    SINH_KHI = "Sinh Khí"
    THIEN_Y = "Thiên Y"
    DIEN_NIEN = "Diên Niên"
    PHUC_VI = "Phục Vị"
    TUYET_MENH = "Tuyệt Mệnh"
    NGU_QUY = "Ngũ Quỷ"
    LUC_SAT = "Lục Sát"
    HOA_HAI = "Họa Hại"


# Mô tả ngắn của 8 sao bát trạch — dùng cho báo cáo.
QUALITY_DESCRIPTION: dict[DirectionQuality, str] = {
    DirectionQuality.SINH_KHI:
        "Hướng tốt nhất — tài lộc, công danh, vận khí thịnh. Ưu tiên cửa chính, cửa hàng.",
    DirectionQuality.THIEN_Y:
        "Hướng sức khỏe — trường thọ, ít bệnh tật. Đặt bếp, phòng ngủ chủ nhân.",
    DirectionQuality.DIEN_NIEN:
        "Hướng tình duyên, hòa thuận gia đình — hợp phòng ngủ vợ chồng, phòng khách.",
    DirectionQuality.PHUC_VI:
        "Hướng bình ổn — phù hợp bàn thờ, phòng học, văn phòng làm việc cá nhân.",
    DirectionQuality.TUYET_MENH:
        "Hướng xấu nặng — tránh tuyệt đối làm cửa chính, giường ngủ chủ nhân.",
    DirectionQuality.NGU_QUY:
        "Hướng hao tài, kiện tụng — tránh đặt két sắt, phòng kinh doanh.",
    DirectionQuality.LUC_SAT:
        "Hướng thị phi, tranh cãi — tránh đặt phòng họp, phòng khách chính.",
    DirectionQuality.HOA_HAI:
        "Hướng ốm đau, hao tài nhẹ — tránh phòng ngủ chính, bếp.",
}

GOOD_QUALITIES: frozenset[DirectionQuality] = frozenset({
    DirectionQuality.SINH_KHI,
    DirectionQuality.THIEN_Y,
    DirectionQuality.DIEN_NIEN,
    DirectionQuality.PHUC_VI,
})


@dataclass(frozen=True, slots=True)
class Direction:
    quality: DirectionQuality
    direction: str
    description: str
    is_good: bool

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "quality": str(self.quality),
            "direction": self.direction,
            "description": self.description,
            "is_good": self.is_good,
        }


@lru_cache(maxsize=1)
def _load_data() -> dict[str, Any]:
    with DATA_PATH.open(encoding="utf-8") as fp:
        return yaml.safe_load(fp)


def bat_trach_for_cung(cung: str | Cung) -> list[Direction]:
    """8 hướng của một cung mệnh, theo thứ tự tốt trước → xấu sau."""
    cung_name = str(cung)
    data = _load_data()
    entry = data.get(cung_name)
    if entry is None:
        raise KeyError(f"Không có dữ liệu bát trạch cho cung {cung_name!r}")

    result: list[Direction] = []
    for quality_name, dir_name in entry["huong_tot"].items():
        q = DirectionQuality(quality_name)
        result.append(Direction(
            quality=q,
            direction=dir_name,
            description=QUALITY_DESCRIPTION[q],
            is_good=True,
        ))
    for quality_name, dir_name in entry["huong_xau"].items():
        q = DirectionQuality(quality_name)
        result.append(Direction(
            quality=q,
            direction=dir_name,
            description=QUALITY_DESCRIPTION[q],
            is_good=False,
        ))
    return result


def match_house_direction(cung: str | Cung, house_direction: str) -> Direction:
    """Đánh giá một hướng nhà cụ thể (Bắc/Nam/…) cho cung mệnh đã cho.

    `house_direction` là hướng cửa chính nhà (toạ-hướng truyền thống lấy theo hướng cửa chính).
    """
    if house_direction not in DIRECTION_DEG:
        raise ValueError(
            f"Hướng không hợp lệ: {house_direction!r}. "
            f"Phải là một trong {list(DIRECTION_DEG)}."
        )
    for direction in bat_trach_for_cung(cung):
        if direction.direction == house_direction:
            return direction
    raise RuntimeError(
        f"Không tìm thấy hướng {house_direction} cho cung {cung} — dữ liệu YAML không đầy đủ."
    )


def direction_from_degrees(deg: float) -> str:
    """Quy đổi độ la bàn (0–360, 0=Bắc, theo chiều kim đồng hồ) sang tên hướng VN."""
    deg = deg % 360
    if deg >= 337.5 or deg < 22.5:
        return "Bắc"
    for name, (lo, hi) in DIRECTION_DEG.items():
        if name == "Bắc":
            continue
        if lo <= deg < hi:
            return name
    return "Bắc"
