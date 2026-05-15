"""Can Chi (Sexagenary cycle) — Thiên Can × Địa Chi = 60 năm.

Reference cycle anchor: năm Giáp Tý = 1984 (modern cycle start).
Day Can Chi anchor: JDN 2451910 = 11/01/2001 = ngày Giáp Tý.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from phongthuy_ontology.lunar import jdn_from_date

CAN: tuple[str, ...] = (
    "Giáp", "Ất", "Bính", "Đinh", "Mậu",
    "Kỷ", "Canh", "Tân", "Nhâm", "Quý",
)

CHI: tuple[str, ...] = (
    "Tý", "Sửu", "Dần", "Mão", "Thìn", "Tỵ",
    "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi",
)

CHI_ANIMAL: dict[str, str] = {
    "Tý": "Chuột", "Sửu": "Trâu", "Dần": "Hổ", "Mão": "Mèo",
    "Thìn": "Rồng", "Tỵ": "Rắn", "Ngọ": "Ngựa", "Mùi": "Dê",
    "Thân": "Khỉ", "Dậu": "Gà", "Tuất": "Chó", "Hợi": "Lợn",
}

# Lục xung — 6 cặp chi xung khắc nặng nhất.
CHI_XUNG: dict[str, str] = {
    "Tý": "Ngọ", "Ngọ": "Tý",
    "Sửu": "Mùi", "Mùi": "Sửu",
    "Dần": "Thân", "Thân": "Dần",
    "Mão": "Dậu", "Dậu": "Mão",
    "Thìn": "Tuất", "Tuất": "Thìn",
    "Tỵ": "Hợi", "Hợi": "Tỵ",
}

# Tam hình — 3 cặp/nhóm hình hại.
CHI_HINH: dict[str, tuple[str, ...]] = {
    "Tý": ("Mão",), "Mão": ("Tý",),
    "Dần": ("Tỵ", "Thân"), "Tỵ": ("Dần", "Thân"), "Thân": ("Dần", "Tỵ"),
    "Sửu": ("Tuất", "Mùi"), "Tuất": ("Sửu", "Mùi"), "Mùi": ("Sửu", "Tuất"),
    "Thìn": ("Thìn",), "Ngọ": ("Ngọ",), "Dậu": ("Dậu",), "Hợi": ("Hợi",),
}

# Lục hại — 6 cặp tương hại nhẹ.
CHI_HAI: dict[str, str] = {
    "Tý": "Mùi", "Mùi": "Tý",
    "Sửu": "Ngọ", "Ngọ": "Sửu",
    "Dần": "Tỵ", "Tỵ": "Dần",
    "Mão": "Thìn", "Thìn": "Mão",
    "Thân": "Hợi", "Hợi": "Thân",
    "Dậu": "Tuất", "Tuất": "Dậu",
}

# Nạp âm ngũ hành — 30 pair × 2 năm = 60 năm.
# Index by (can_index * 6 + chi_index // 2) doesn't work cleanly; use direct map by canchi pair.
# Source: Hoàng Lịch Thông Thư.
NAP_AM_TABLE: dict[tuple[str, str], str] = {
    ("Giáp", "Tý"): "Hải Trung Kim", ("Ất", "Sửu"): "Hải Trung Kim",
    ("Bính", "Dần"): "Lư Trung Hỏa", ("Đinh", "Mão"): "Lư Trung Hỏa",
    ("Mậu", "Thìn"): "Đại Lâm Mộc", ("Kỷ", "Tỵ"): "Đại Lâm Mộc",
    ("Canh", "Ngọ"): "Lộ Bàng Thổ", ("Tân", "Mùi"): "Lộ Bàng Thổ",
    ("Nhâm", "Thân"): "Kiếm Phong Kim", ("Quý", "Dậu"): "Kiếm Phong Kim",
    ("Giáp", "Tuất"): "Sơn Đầu Hỏa", ("Ất", "Hợi"): "Sơn Đầu Hỏa",
    ("Bính", "Tý"): "Giản Hạ Thủy", ("Đinh", "Sửu"): "Giản Hạ Thủy",
    ("Mậu", "Dần"): "Thành Đầu Thổ", ("Kỷ", "Mão"): "Thành Đầu Thổ",
    ("Canh", "Thìn"): "Bạch Lạp Kim", ("Tân", "Tỵ"): "Bạch Lạp Kim",
    ("Nhâm", "Ngọ"): "Dương Liễu Mộc", ("Quý", "Mùi"): "Dương Liễu Mộc",
    ("Giáp", "Thân"): "Tuyền Trung Thủy", ("Ất", "Dậu"): "Tuyền Trung Thủy",
    ("Bính", "Tuất"): "Ốc Thượng Thổ", ("Đinh", "Hợi"): "Ốc Thượng Thổ",
    ("Mậu", "Tý"): "Tích Lịch Hỏa", ("Kỷ", "Sửu"): "Tích Lịch Hỏa",
    ("Canh", "Dần"): "Tùng Bách Mộc", ("Tân", "Mão"): "Tùng Bách Mộc",
    ("Nhâm", "Thìn"): "Trường Lưu Thủy", ("Quý", "Tỵ"): "Trường Lưu Thủy",
    ("Giáp", "Ngọ"): "Sa Trung Kim", ("Ất", "Mùi"): "Sa Trung Kim",
    ("Bính", "Thân"): "Sơn Hạ Hỏa", ("Đinh", "Dậu"): "Sơn Hạ Hỏa",
    ("Mậu", "Tuất"): "Bình Địa Mộc", ("Kỷ", "Hợi"): "Bình Địa Mộc",
    ("Canh", "Tý"): "Bích Thượng Thổ", ("Tân", "Sửu"): "Bích Thượng Thổ",
    ("Nhâm", "Dần"): "Kim Bạch Kim", ("Quý", "Mão"): "Kim Bạch Kim",
    ("Giáp", "Thìn"): "Phú Đăng Hỏa", ("Ất", "Tỵ"): "Phú Đăng Hỏa",
    ("Bính", "Ngọ"): "Thiên Hà Thủy", ("Đinh", "Mùi"): "Thiên Hà Thủy",
    ("Mậu", "Thân"): "Đại Trạch Thổ", ("Kỷ", "Dậu"): "Đại Trạch Thổ",
    ("Canh", "Tuất"): "Thoa Xuyến Kim", ("Tân", "Hợi"): "Thoa Xuyến Kim",
    ("Nhâm", "Tý"): "Tang Đố Mộc", ("Quý", "Sửu"): "Tang Đố Mộc",
    ("Giáp", "Dần"): "Đại Khê Thủy", ("Ất", "Mão"): "Đại Khê Thủy",
    ("Bính", "Thìn"): "Sa Trung Thổ", ("Đinh", "Tỵ"): "Sa Trung Thổ",
    ("Mậu", "Ngọ"): "Thiên Thượng Hỏa", ("Kỷ", "Mùi"): "Thiên Thượng Hỏa",
    ("Canh", "Thân"): "Thạch Lựu Mộc", ("Tân", "Dậu"): "Thạch Lựu Mộc",
    ("Nhâm", "Tuất"): "Đại Hải Thủy", ("Quý", "Hợi"): "Đại Hải Thủy",
}

# Element of each nạp âm (lookup helper).
NAP_AM_ELEMENT: dict[str, str] = {
    name: name.split()[-1]
    for name in set(NAP_AM_TABLE.values())
}

# JDN of 11/01/2001 = Giáp Tý day. We anchor the day cycle here.
_DAY_ANCHOR_JDN = jdn_from_date(11, 1, 2001)
_DAY_ANCHOR_CAN = 0  # Giáp
_DAY_ANCHOR_CHI = 0  # Tý


@dataclass(frozen=True, slots=True)
class CanChi:
    """A Can-Chi pair, with its nạp âm element."""

    can: str
    chi: str
    nap_am: str

    @property
    def element(self) -> str:
        return NAP_AM_ELEMENT[self.nap_am]

    def __str__(self) -> str:
        return f"{self.can} {self.chi} ({self.nap_am})"


def can_chi_of_year(year: int) -> CanChi:
    """Can chi của năm âm lịch. Anchor: 1984 = Giáp Tý."""
    # 1984 → can_idx=0 (Giáp), chi_idx=0 (Tý). Year 4 BC would be Giáp Tý too;
    # using (year - 4) handles negative years cleanly.
    can_idx = (year - 4) % 10
    chi_idx = (year - 4) % 12
    return CanChi(
        can=CAN[can_idx],
        chi=CHI[chi_idx],
        nap_am=NAP_AM_TABLE[(CAN[can_idx], CHI[chi_idx])],
    )


def can_chi_of_day(d: date) -> CanChi:
    """Can chi của ngày dương lịch d."""
    jdn = jdn_from_date(d.day, d.month, d.year)
    delta = jdn - _DAY_ANCHOR_JDN
    can_idx = (_DAY_ANCHOR_CAN + delta) % 10
    chi_idx = (_DAY_ANCHOR_CHI + delta) % 12
    return CanChi(
        can=CAN[can_idx],
        chi=CHI[chi_idx],
        nap_am=NAP_AM_TABLE[(CAN[can_idx], CHI[chi_idx])],
    )


def can_chi_of_month(lunar_year: int, lunar_month: int) -> CanChi:
    """Can chi của tháng âm lịch.

    Chi của tháng cố định: tháng Giêng = Dần, tháng 2 = Mão, …, tháng 11 = Tý, tháng 12 = Sửu.
    Can của tháng dựa vào can của năm:
      Năm Giáp/Kỷ  → tháng Giêng Bính Dần
      Năm Ất/Canh  → tháng Giêng Mậu Dần
      Năm Bính/Tân → tháng Giêng Canh Dần
      Năm Đinh/Nhâm → tháng Giêng Nhâm Dần
      Năm Mậu/Quý  → tháng Giêng Giáp Dần
    """
    year_can = can_chi_of_year(lunar_year).can
    # Mapping năm-can → can của tháng Giêng (Dần).
    first_month_can_idx = {
        "Giáp": 2, "Kỷ": 2,         # Bính
        "Ất": 4, "Canh": 4,         # Mậu
        "Bính": 6, "Tân": 6,        # Canh
        "Đinh": 8, "Nhâm": 8,       # Nhâm
        "Mậu": 0, "Quý": 0,         # Giáp
    }[year_can]
    # Month offset: lunar month 1 → chi=Dần (index 2). Offset from tháng Giêng.
    offset = (lunar_month - 1)
    can_idx = (first_month_can_idx + offset) % 10
    chi_idx = (2 + offset) % 12  # 2 = Dần
    return CanChi(
        can=CAN[can_idx],
        chi=CHI[chi_idx],
        nap_am=NAP_AM_TABLE[(CAN[can_idx], CHI[chi_idx])],
    )


def nap_am(can: str, chi: str) -> str:
    """Lookup nạp âm cho một cặp can-chi."""
    return NAP_AM_TABLE[(can, chi)]


def is_xung(chi_a: str, chi_b: str) -> bool:
    """Hai chi có xung khắc trực tiếp (lục xung) không."""
    return CHI_XUNG.get(chi_a) == chi_b


def is_hai(chi_a: str, chi_b: str) -> bool:
    """Hai chi có tương hại không (lục hại)."""
    return CHI_HAI.get(chi_a) == chi_b


def is_hinh(chi_a: str, chi_b: str) -> bool:
    """Hai chi có hình nhau không (tam hình)."""
    return chi_b in CHI_HINH.get(chi_a, ())
