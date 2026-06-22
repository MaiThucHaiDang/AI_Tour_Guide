"""VNPay payment integration service (Sandbox)."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import unicodedata
import urllib.parse
import uuid
from datetime import datetime, timedelta

from core.config import settings


def _strip_vietnamese(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = re.sub(r"[\u0300-\u036f]", "", text)
    text = text.replace("đ", "d").replace("Đ", "D")
    return text


def _generate_order_code() -> str:
    """Generate a unique order code: VNP-YYYYMMDD-HHMMSS-XXXXXX."""
    now = datetime.now()
    date_part = now.strftime("%Y%m%d-%H%M%S")
    uid = uuid.uuid4().hex[:6].upper()
    return f"VNP-{date_part}-{uid}"


def _build_order_desc(location: str, adult: int, children_paid: int, children_free: int, items: list[dict]) -> str:
    parts = [f"Ve {location}"]
    if adult:
        parts.append(f"{adult} nguoi lon")
    if children_paid:
        parts.append(f"{children_paid} tre em co ve")
    if children_free:
        parts.append(f"{children_free} tre em mien phi")
    if items:
        item_strs = []
        for it in items:
            name = it.get("name_vi", it.get("key", ""))
            qty = it.get("quantity", 0)
            if qty:
                item_strs.append(f"{name}x{qty}")
        if item_strs:
            parts.append("+ " + ", ".join(item_strs))
    return " ".join(parts)


def create_payment_url(
    amount: int,
    order_code: str,
    order_desc: str,
    return_url: str | None = None,
    client_ip: str = "127.0.0.1",
) -> str:
    """Build the VNPay Sandbox payment URL for an order."""
    now = datetime.now()

    order_info = _strip_vietnamese(order_desc or f"Thanh toan {order_code}")
    order_info = re.sub(r"[^a-zA-Z0-9\s]", "", order_info)[:255]

    params: dict[str, str] = {
        "vnp_Version": "2.1.0",
        "vnp_Command": "pay",
        "vnp_TmnCode": settings.VNPAY_TMN_CODE,
        "vnp_Amount": str(amount * 100),
        "vnp_CurrCode": "VND",
        "vnp_TxnRef": order_code,
        "vnp_OrderInfo": order_info,
        "vnp_OrderType": "other",
        "vnp_Locale": "vn",
        "vnp_ReturnUrl": return_url or settings.VNPAY_RETURN_URL,
        "vnp_IpAddr": client_ip,
        "vnp_CreateDate": now.strftime("%Y%m%d%H%M%S"),
        "vnp_ExpireDate": (now + timedelta(minutes=15)).strftime("%Y%m%d%H%M%S"),
    }

    sorted_params = sorted(params.items())
    hash_data = "&".join(f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in sorted_params)

    secure_hash = hmac.new(
        settings.VNPAY_HASH_SECRET.encode("utf-8"),
        hash_data.encode("utf-8"),
        hashlib.sha512,
    ).hexdigest()

    return f"{settings.VNPAY_PAYMENT_URL}?{hash_data}&vnp_SecureHash={secure_hash}"


def verify_return_params(params: dict[str, str]) -> bool:
    """Verify VNPay return params signature."""
    secure_hash = params.get("vnp_SecureHash", "")
    if not secure_hash:
        return False

    to_verify = {
        k: v
        for k, v in params.items()
        if k.startswith("vnp_") and k not in ("vnp_SecureHash", "vnp_SecureHashType")
    }
    sorted_params = sorted(to_verify.items())
    hash_data = "&".join(f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in sorted_params)

    expected_hash = hmac.new(
        settings.VNPAY_HASH_SECRET.encode("utf-8"),
        hash_data.encode("utf-8"),
        hashlib.sha512,
    ).hexdigest()

    return expected_hash == secure_hash
