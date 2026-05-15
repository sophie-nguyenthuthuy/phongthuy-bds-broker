"""Ngũ hành — 5 elements and their relationships."""

from __future__ import annotations

from enum import StrEnum


class NguHanh(StrEnum):
    KIM = "Kim"
    MOC = "Mộc"
    THUY = "Thủy"
    HOA = "Hỏa"
    THO = "Thổ"


# Tương sinh: A sinh B → A nuôi/hỗ trợ B.
# Kim sinh Thủy, Thủy sinh Mộc, Mộc sinh Hỏa, Hỏa sinh Thổ, Thổ sinh Kim.
TUONG_SINH: dict[NguHanh, NguHanh] = {
    NguHanh.KIM: NguHanh.THUY,
    NguHanh.THUY: NguHanh.MOC,
    NguHanh.MOC: NguHanh.HOA,
    NguHanh.HOA: NguHanh.THO,
    NguHanh.THO: NguHanh.KIM,
}

# Tương khắc: A khắc B → A áp chế B.
# Kim khắc Mộc, Mộc khắc Thổ, Thổ khắc Thủy, Thủy khắc Hỏa, Hỏa khắc Kim.
TUONG_KHAC: dict[NguHanh, NguHanh] = {
    NguHanh.KIM: NguHanh.MOC,
    NguHanh.MOC: NguHanh.THO,
    NguHanh.THO: NguHanh.THUY,
    NguHanh.THUY: NguHanh.HOA,
    NguHanh.HOA: NguHanh.KIM,
}

# Màu sắc đại diện ngũ hành — dùng cho gợi ý nội thất.
MAU_SAC: dict[NguHanh, tuple[str, ...]] = {
    NguHanh.KIM: ("Trắng", "Xám", "Ghi", "Bạc"),
    NguHanh.MOC: ("Xanh lá", "Xanh lục"),
    NguHanh.THUY: ("Đen", "Xanh dương", "Xanh nước biển"),
    NguHanh.HOA: ("Đỏ", "Hồng", "Tím", "Cam"),
    NguHanh.THO: ("Vàng", "Nâu đất", "Vàng nâu"),
}


def quan_he_ngu_hanh(a: NguHanh, b: NguHanh) -> str:
    """Trả về mối quan hệ giữa hai hành: 'tương sinh' | 'tương khắc' | 'bình hòa' | 'tương trợ'.

    - tương sinh: a sinh b (a nuôi b → tốt cho b).
    - bị sinh: b sinh a (a được b nuôi → tốt cho a).
    - tương khắc: a khắc b (a áp chế b → xấu cho b).
    - bị khắc: b khắc a (a bị b áp chế → xấu cho a).
    - tương trợ: a == b (cùng hành, hỗ trợ nhau).
    """
    if a == b:
        return "tương trợ"
    if TUONG_SINH[a] == b:
        return "tương sinh"
    if TUONG_SINH[b] == a:
        return "bị sinh"
    if TUONG_KHAC[a] == b:
        return "tương khắc"
    if TUONG_KHAC[b] == a:
        return "bị khắc"
    return "bình hòa"


def parse_element(nap_am_name: str) -> NguHanh:
    """Lấy hành (Kim/Mộc/Thủy/Hỏa/Thổ) từ tên nạp âm.

    Ví dụ: 'Hải Trung Kim' → NguHanh.KIM, 'Đại Lâm Mộc' → NguHanh.MOC.
    """
    last_word = nap_am_name.split()[-1]
    return NguHanh(last_word)
