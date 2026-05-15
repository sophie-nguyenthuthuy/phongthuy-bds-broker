"""VNPay sandbox integration.

Theo `https://sandbox.vnpayment.vn/apis/docs/thanh-toan-pay/`.
"""

from __future__ import annotations

import hashlib
import hmac
import urllib.parse
from datetime import datetime
from decimal import Decimal

from phongthuy_bds.core.config import get_settings


def build_payment_url(
    *,
    order_id: str,
    amount_vnd: Decimal,
    order_info: str,
    ip_address: str,
    locale: str = "vn",
    bank_code: str | None = None,
) -> str:
    """Xây URL redirect VNPay payment.

    Args:
        amount_vnd: Số tiền VND (VNPay yêu cầu nhân 100, đã handle bên dưới).
    """
    settings = get_settings()
    if not settings.vnpay_tmn_code:
        raise RuntimeError("VNPAY_TMN_CODE chưa cấu hình")

    vnp = {
        "vnp_Version": "2.1.0",
        "vnp_Command": "pay",
        "vnp_TmnCode": settings.vnpay_tmn_code,
        "vnp_Amount": str(int(amount_vnd * 100)),
        "vnp_CurrCode": "VND",
        "vnp_TxnRef": order_id,
        "vnp_OrderInfo": order_info,
        "vnp_OrderType": "other",
        "vnp_Locale": locale,
        "vnp_ReturnUrl": settings.vnpay_return_url,
        "vnp_IpAddr": ip_address,
        "vnp_CreateDate": datetime.now().strftime("%Y%m%d%H%M%S"),
    }
    if bank_code:
        vnp["vnp_BankCode"] = bank_code

    # Sort + sign.
    sorted_pairs = sorted(vnp.items())
    query = urllib.parse.urlencode(sorted_pairs, quote_via=urllib.parse.quote_plus)
    sig = hmac.new(
        settings.vnpay_hash_secret.get_secret_value().encode("utf-8"),
        query.encode("utf-8"),
        hashlib.sha512,
    ).hexdigest()
    return f"{settings.vnpay_api_url}?{query}&vnp_SecureHash={sig}"


def verify_return(params: dict[str, str]) -> bool:
    """Verify VNPay callback signature."""
    settings = get_settings()
    received_sig = params.pop("vnp_SecureHash", "")
    params.pop("vnp_SecureHashType", None)
    sorted_pairs = sorted(params.items())
    query = urllib.parse.urlencode(sorted_pairs, quote_via=urllib.parse.quote_plus)
    expected = hmac.new(
        settings.vnpay_hash_secret.get_secret_value().encode("utf-8"),
        query.encode("utf-8"),
        hashlib.sha512,
    ).hexdigest()
    return hmac.compare_digest(received_sig.lower(), expected.lower())
