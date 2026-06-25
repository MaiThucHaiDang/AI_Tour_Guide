import pytest
import urllib.parse
from pydantic import ValidationError

from schemas.payment import (
    ItemSelection,
    PaymentCreateRequest,
    PaymentInfo,
)
from services.payment.vnpay_service import (
    _strip_vietnamese,
    _generate_order_code,
    _build_order_desc,
    create_payment_url,
    verify_return_params,
)

def test_item_selection_quantity_bounds():
    ItemSelection(key="nuoc_suoi", quantity=1)
    ItemSelection(key="nuoc_suoi", quantity=50)
    
    with pytest.raises(ValidationError):
        ItemSelection(key="nuoc_suoi", quantity=-1)
        
    with pytest.raises(ValidationError):
        ItemSelection(key="nuoc_suoi", quantity=51)

def test_payment_request_rejects_unknown_location():
    with pytest.raises(ValidationError):
        PaymentCreateRequest(
            location="Unknown Place",
            customerName="A",
            customerEmail="a@b.com",
            customerPhone="0123456789"
        )

def test_payment_request_rejects_bad_phone():
    # Valid
    PaymentCreateRequest(
        location="Ngọ Môn", customerName="A", customerEmail="a@b.com", customerPhone="0123456789"
    )
    
    with pytest.raises(ValidationError, match="Invalid phone number"):
        PaymentCreateRequest(
            location="Ngọ Môn", customerName="A", customerEmail="a@b.com", customerPhone="123" # too short
        )
        
    with pytest.raises(ValidationError, match="Invalid phone number"):
        PaymentCreateRequest(
            location="Ngọ Môn", customerName="A", customerEmail="a@b.com", customerPhone="not a number"
        )

def test_calc_total_ngo_mon_adult_child_food():
    req = PaymentCreateRequest(
        location="Ngọ Môn",
        customerName="A",
        customerEmail="a@b.com",
        customerPhone="0123456789",
        adultCount=2,  # 2 * 200k = 400k
        childrenPaidCount=1,  # 1 * 40k = 40k
        items=[ItemSelection(key="nuoc_suoi", quantity=2)]  # 2 * 10k = 20k
    )
    assert req.calc_total() == 460000

def test_calc_total_dien_long_an_ignores_paid_child_ticket():
    req = PaymentCreateRequest(
        location="Điện Long An",
        customerName="A",
        customerEmail="a@b.com",
        customerPhone="0123456789",
        adultCount=2,  # 2 * 50k = 100k
        childrenPaidCount=5,  # Ignored because Điện Long An doesn't charge children
        items=[]
    )
    assert req.calc_total() == 100000

def test_payment_info_parse_items_json_string_and_bad_json():
    # Parse from string
    info1 = PaymentInfo(
        id=1, orderCode="O1", amount=100, location="Ngọ Môn", customerName="A",
        customerEmail="A", customerPhone="0123456789", adultCount=1, childrenPaidCount=0,
        childrenFreeCount=0, status="pending", createdAt="2026-01-01T00:00:00Z",
        items='[{"key": "nuoc_suoi", "quantity": 2}]'
    )
    assert len(info1.items) == 1
    assert info1.items[0].key == "nuoc_suoi"

    # Parse bad json
    info2 = PaymentInfo(
        id=1, orderCode="O1", amount=100, location="Ngọ Môn", customerName="A",
        customerEmail="A", customerPhone="0123456789", adultCount=1, childrenPaidCount=0,
        childrenFreeCount=0, status="pending", createdAt="2026-01-01T00:00:00Z",
        items='[bad json'
    )
    assert info2.items == []

def test_strip_vietnamese_removes_diacritics_and_d():
    assert _strip_vietnamese("Đường đi đèo Hải Vân") == "Duong di deo Hai Van"

def test_generate_order_code_format_and_uniqueness():
    code1 = _generate_order_code()
    code2 = _generate_order_code()
    assert code1.startswith("VNP-")
    assert len(code1) > 10
    assert code1 != code2

def test_build_order_desc_includes_ticket_and_items():
    desc = _build_order_desc("Ngọ Môn", 2, 1, 0, [{"name_vi": "Nước suối", "quantity": 2}])
    assert "Ve Ngọ Môn" in desc
    assert "2 nguoi lon" in desc
    assert "1 tre em co ve" in desc
    assert "Nước suốix2" in desc

def test_create_payment_url_amount_x100_and_signature(monkeypatch):
    monkeypatch.setattr("core.config.settings.VNPAY_TMN_CODE", "TESTCODE")
    monkeypatch.setattr("core.config.settings.VNPAY_HASH_SECRET", "TESTSECRET")
    monkeypatch.setattr("core.config.settings.VNPAY_PAYMENT_URL", "http://pay")
    
    url = create_payment_url(100000, "VNP-123", "Ve Hue")
    assert "vnp_Amount=10000000" in url # 100k * 100
    assert "vnp_TxnRef=VNP-123" in url
    assert "vnp_SecureHash=" in url

def test_verify_return_params_rejects_missing_or_tampered_hash(monkeypatch):
    monkeypatch.setattr("core.config.settings.VNPAY_HASH_SECRET", "TESTSECRET")
    
    # Missing hash
    assert verify_return_params({"vnp_Amount": "100"}) is False
    
    # Tampered hash
    assert verify_return_params({"vnp_Amount": "100", "vnp_SecureHash": "fakehash"}) is False

def test_payment_request_should_reject_bad_email():
    # Valid
    PaymentCreateRequest(
        location="Ngọ Môn", customerName="A", customerEmail="valid@email.com", customerPhone="0123456789"
    )
    
    # Invalid
    with pytest.raises(ValidationError):
        PaymentCreateRequest(
            location="Ngọ Môn", customerName="A", customerEmail="bad_email", customerPhone="0123456789"
        )

def test_calc_total_should_reject_unknown_food_key():
    with pytest.raises(ValidationError, match="Invalid food item"):
        PaymentCreateRequest(
            location="Ngọ Môn", 
            customerName="A", 
            customerEmail="a@b.com", 
            customerPhone="0123456789",
            items=[ItemSelection(key="unknown_item", quantity=1)]
        )

def test_create_payment_url_strips_special_chars_in_order_info(monkeypatch):
    monkeypatch.setattr("core.config.settings.VNPAY_TMN_CODE", "TESTCODE")
    monkeypatch.setattr("core.config.settings.VNPAY_HASH_SECRET", "TESTSECRET")
    monkeypatch.setattr("core.config.settings.VNPAY_PAYMENT_URL", "http://pay")
    
    url = create_payment_url(100000, "VNP-123", "Thanh toán cho Nguyễn Văn A @#$!! 123")
    parsed_url = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    
    order_info = query_params.get("vnp_OrderInfo", [""])[0]
    # Expect "Thanh toan cho Nguyen Van A  123" without special characters
    assert "@" not in order_info
    assert "#" not in order_info
    assert "$" not in order_info
    assert "!" not in order_info
    assert order_info == "Thanh toan cho Nguyen Van A  123"

def test_verify_return_params_valid_signature(monkeypatch):
    monkeypatch.setattr("core.config.settings.VNPAY_HASH_SECRET", "TESTSECRET")
    
    params = {
        "vnp_Amount": "10000",
        "vnp_Command": "pay",
        "vnp_OrderInfo": "Test",
        "vnp_SecureHashType": "SHA512"
    }
    
    import hashlib
    import hmac
    
    hash_data = "vnp_Amount=10000&vnp_Command=pay&vnp_OrderInfo=Test"
    secure_hash = hmac.new(
        "TESTSECRET".encode("utf-8"),
        hash_data.encode("utf-8"),
        hashlib.sha512,
    ).hexdigest()
    
    params["vnp_SecureHash"] = secure_hash
    
    assert verify_return_params(params) is True

def test_verify_return_params_edge_cases(monkeypatch):
    monkeypatch.setattr("core.config.settings.VNPAY_HASH_SECRET", "TESTSECRET")
    import hashlib
    import hmac
    
    # 1. Ignore non-vnp_ params
    params1 = {
        "vnp_Amount": "10000",
        "vnp_Command": "pay",
        "other_param": "ignore_me"
    }
    hash_data1 = "vnp_Amount=10000&vnp_Command=pay"
    params1["vnp_SecureHash"] = hmac.new(
        "TESTSECRET".encode("utf-8"), hash_data1.encode("utf-8"), hashlib.sha512
    ).hexdigest()
    assert verify_return_params(params1) is True
    
    # 2. Empty string value for vnp_ param
    params2 = {
        "vnp_Amount": "10000",
        "vnp_BankCode": ""
    }
    hash_data2 = "vnp_Amount=10000&vnp_BankCode="
    params2["vnp_SecureHash"] = hmac.new(
        "TESTSECRET".encode("utf-8"), hash_data2.encode("utf-8"), hashlib.sha512
    ).hexdigest()
    assert verify_return_params(params2) is True
    
    # 3. Different cases or URL encoded values (like space encoded as +)
    # the function uses urllib.parse.quote_plus which handles spaces as +
    # So if vnp_OrderInfo="Test spaces", hash data should be "vnp_OrderInfo=Test+spaces"
    params3 = {
        "vnp_OrderInfo": "Test spaces"
    }
    hash_data3 = "vnp_OrderInfo=Test+spaces"
    params3["vnp_SecureHash"] = hmac.new(
        "TESTSECRET".encode("utf-8"), hash_data3.encode("utf-8"), hashlib.sha512
    ).hexdigest()
    assert verify_return_params(params3) is True
