"""Cung mệnh (Bát Quái) từ năm sinh + giới tính.

Áp dụng quy tắc Lạc Thư Cửu Cung. Cung mệnh nằm trong 8 quẻ:
    Khảm, Khôn, Chấn, Tốn, Càn, Đoài, Cấn, Ly.
Hai nhóm:
    - Đông tứ mệnh: Khảm, Ly, Chấn, Tốn — hợp với 4 hướng Đông tứ.
    - Tây tứ mệnh: Càn, Khôn, Cấn, Đoài — hợp với 4 hướng Tây tứ.

Ghi chú: dùng năm âm lịch — nếu khách sinh trước Tết Nguyên Đán thì
trừ 1 năm so với năm dương. Hàm `cung_menh_from_birth_date` xử lý điều này.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from phongthuy_ontology.can_chi import can_chi_of_year
from phongthuy_ontology.lunar import solar_to_lunar
from phongthuy_ontology.ngu_hanh import NguHanh, parse_element


class Gender(StrEnum):
    NAM = "nam"
    NU = "nu"


class Cung(StrEnum):
    KHAM = "Khảm"
    KHON = "Khôn"
    CHAN = "Chấn"
    TON = "Tốn"
    CAN = "Càn"
    DOAI = "Đoài"
    CAN_TRAGRAM = "Cấn"  # NB: "Cấn" trùng spelling với họ Càn ASCII; dùng key riêng.
    LY = "Ly"


class Nhom(StrEnum):
    DONG = "Đông tứ mệnh"
    TAY = "Tây tứ mệnh"


# Lạc Thư số → cung (sau khi xử lý số 5).
LAC_THU_TO_CUNG: dict[int, Cung] = {
    1: Cung.KHAM,
    2: Cung.KHON,
    3: Cung.CHAN,
    4: Cung.TON,
    6: Cung.CAN,
    7: Cung.DOAI,
    8: Cung.CAN_TRAGRAM,
    9: Cung.LY,
}

NHOM_OF_CUNG: dict[Cung, Nhom] = {
    Cung.KHAM: Nhom.DONG,
    Cung.LY: Nhom.DONG,
    Cung.CHAN: Nhom.DONG,
    Cung.TON: Nhom.DONG,
    Cung.CAN: Nhom.TAY,
    Cung.KHON: Nhom.TAY,
    Cung.CAN_TRAGRAM: Nhom.TAY,
    Cung.DOAI: Nhom.TAY,
}

# Ngũ hành của 8 cung (theo Hậu Thiên Bát Quái).
NGU_HANH_OF_CUNG: dict[Cung, NguHanh] = {
    Cung.KHAM: NguHanh.THUY,
    Cung.LY: NguHanh.HOA,
    Cung.CHAN: NguHanh.MOC,
    Cung.TON: NguHanh.MOC,
    Cung.CAN: NguHanh.KIM,
    Cung.DOAI: NguHanh.KIM,
    Cung.CAN_TRAGRAM: NguHanh.THO,
    Cung.KHON: NguHanh.THO,
}


@dataclass(frozen=True, slots=True)
class CungMenhResult:
    cung: Cung
    nhom: Nhom
    ngu_hanh_cung: NguHanh
    ngu_hanh_nap_am: NguHanh
    lunar_year: int
    can_chi: str
    lac_thu_so: int
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, str | int | list[str]]:
        return {
            "cung": str(self.cung),
            "nhom": str(self.nhom),
            "ngu_hanh_cung": str(self.ngu_hanh_cung),
            "ngu_hanh_nap_am": str(self.ngu_hanh_nap_am),
            "lunar_year": self.lunar_year,
            "can_chi": self.can_chi,
            "lac_thu_so": self.lac_thu_so,
            "notes": list(self.notes),
        }


def _digit_sum_to_single(n: int) -> int:
    """Cộng dồn các chữ số đến khi còn 1 chữ số (1..9)."""
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


def _lac_thu_for_male(lunar_year: int) -> int:
    """Lạc Thư số nam giới.

    Sách Bát Trạch Minh Cảnh:
      - Thế kỷ 20 (1900–1999): (10 − tổng 2 chữ số cuối, rút gọn) mod 9, 0 → 9.
      - Thế kỷ 21 (2000–2099): (9 − tổng 2 chữ số cuối, rút gọn) mod 9, 0 → 9.
    """
    last_two = lunar_year % 100
    s = _digit_sum_to_single(last_two)
    base = 10 if lunar_year < 2000 else 9
    val = (base - s) % 9
    return 9 if val == 0 else val


def _lac_thu_for_female(lunar_year: int) -> int:
    """Lạc Thư số nữ giới.

    Sách Bát Trạch Minh Cảnh:
      - Thế kỷ 20: (5 + tổng 2 chữ số cuối, rút gọn) mod 9, 0 → 9.
      - Thế kỷ 21: (6 + tổng 2 chữ số cuối, rút gọn) mod 9, 0 → 9.
    """
    last_two = lunar_year % 100
    s = _digit_sum_to_single(last_two)
    base = 5 if lunar_year < 2000 else 6
    val = (base + s) % 9
    return 9 if val == 0 else val


def cung_menh_from_lunar_year(lunar_year: int, gender: Gender) -> CungMenhResult:
    """Tính cung mệnh từ năm âm lịch + giới tính."""
    n = (
        _lac_thu_for_male(lunar_year)
        if gender == Gender.NAM
        else _lac_thu_for_female(lunar_year)
    )

    notes: list[str] = []
    if n == 5:
        # Số 5 nhập trung cung, không có quẻ → quy ước: nam → Khôn (2), nữ → Cấn (8).
        if gender == Gender.NAM:
            n = 2
            notes.append("Lạc Thư số 5 → quy về Khôn (2) cho nam.")
        else:
            n = 8
            notes.append("Lạc Thư số 5 → quy về Cấn (8) cho nữ.")

    cung = LAC_THU_TO_CUNG[n]
    nhom = NHOM_OF_CUNG[cung]
    cc = can_chi_of_year(lunar_year)

    return CungMenhResult(
        cung=cung,
        nhom=nhom,
        ngu_hanh_cung=NGU_HANH_OF_CUNG[cung],
        ngu_hanh_nap_am=parse_element(cc.nap_am),
        lunar_year=lunar_year,
        can_chi=f"{cc.can} {cc.chi}",
        lac_thu_so=n,
        notes=tuple(notes),
    )


def cung_menh_from_birth(year: int, gender: Gender) -> CungMenhResult:
    """Tính cung mệnh từ năm dương lịch + giới tính.

    Nếu không biết ngày/tháng sinh chính xác, giả định khách sinh **sau Tết Nguyên Đán**
    nên năm âm lịch = năm dương. Để chính xác cho khách sinh tháng 1–2 dương lịch,
    dùng `cung_menh_from_birth_date(birth_date, gender)`.
    """
    return cung_menh_from_lunar_year(year, gender)


def cung_menh_from_birth_date(birth_date: date, gender: Gender) -> CungMenhResult:
    """Tính cung mệnh từ ngày sinh dương lịch chính xác.

    Quy đổi sang năm âm lịch trước khi tính (xử lý đúng trường hợp sinh trước Tết).
    """
    lunar = solar_to_lunar(birth_date.day, birth_date.month, birth_date.year)
    return cung_menh_from_lunar_year(lunar.year, gender)
