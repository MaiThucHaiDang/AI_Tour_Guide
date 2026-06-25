from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from main import app
from core.database import get_db_session
from models.payment import Payment

client = TestClient(app, raise_server_exceptions=False)

def override_db():
    mock_session = AsyncMock()
    # Provide necessary mock behaviors for execute, scalar_one_or_none, etc.
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    yield mock_session

app.dependency_overrides[get_db_session] = override_db

def test_api_pay_01_food_items():
    response = client.get("/api/v1/payment/food-items")
    assert response.status_code in [200, 201]
    data = response.json()
    assert "items" in data

def test_api_pay_02_create_payment_ngo_mon():
    response = client.post(
        "/api/v1/payment/create",
        json={
            "location": "ngo_mon",
            "customer_name": "Nguyen Van A",
            "customer_email": "a@example.com",
            "customer_phone": "0123456789",
            "adult_count": 1,
            "children_paid_count": 1,
            "children_free_count": 0,
            "items": [{"key": "cafe_den", "quantity": 1}],
            "return_url": "http://localhost/return"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["paymentUrl"] is not None
    assert "vnp_SecureHash" in data["paymentUrl"]
    assert data["amount"] > 0

def test_api_pay_03_create_payment_dien_long_an():
    response = client.post(
        "/api/v1/payment/create",
        json={
            "location": "dien_long_an",
            "customer_name": "Nguyen Van A",
            "customer_email": "a@example.com",
            "customer_phone": "0123456789",
            "adult_count": 1,
            "children_paid_count": 1,
            "children_free_count": 0,
            "items": [],
            "return_url": "http://localhost/return"
        }
    )
    assert response.status_code == 201
    data = response.json()
    # Dien Long An doesn't charge children
    assert data["childrenPaidCount"] == 1
    # Check amount logic if known, or just expect success

def test_api_pay_04_create_payment_invalid_location():
    response = client.post(
        "/api/v1/payment/create",
        json={
            "location": "invalid_loc",
            "customer_name": "Nguyen Van A",
            "customer_email": "a@example.com",
            "customer_phone": "0123456789",
            "adult_count": 1,
            "children_paid_count": 0,
            "children_free_count": 0,
            "items": []
        }
    )
    assert response.status_code in (400, 422)

def test_api_pay_05_create_payment_adult_zero():
    response = client.post(
        "/api/v1/payment/create",
        json={
            "location": "ngo_mon",
            "customer_name": "Nguyen Van A",
            "customer_email": "a@example.com",
            "customer_phone": "0123456789",
            "adult_count": 0,
            "children_paid_count": 0,
            "children_free_count": 0,
            "items": []
        }
    )
    assert response.status_code == 422

def test_api_pay_06_create_payment_invalid_email():
    response = client.post(
        "/api/v1/payment/create",
        json={
            "location": "ngo_mon",
            "customer_name": "Nguyen Van A",
            "customer_email": "abc@.com",
            "customer_phone": "0123456789",
            "adult_count": 1,
            "children_paid_count": 0,
            "children_free_count": 0,
            "items": []
        }
    )
    assert response.status_code == 422

def test_api_pay_07_create_payment_unknown_food():
    response = client.post(
        "/api/v1/payment/create",
        json={
            "location": "ngo_mon",
            "customer_name": "Nguyen Van A",
            "customer_email": "a@example.com",
            "customer_phone": "0123456789",
            "adult_count": 1,
            "children_paid_count": 0,
            "children_free_count": 0,
            "items": [{"key": "unknown_food", "quantity": 1}]
        }
    )
    assert response.status_code == 422

def test_api_pay_08_return_missing_signature():
    response = client.get("/api/v1/payment/return?vnp_TxnRef=123")
    assert response.json()["success"] is False

def test_api_pay_09_return_invalid_signature():
    response = client.get("/api/v1/payment/return?vnp_TxnRef=123&vnp_SecureHash=fake")
    assert response.json()["success"] is False

@patch("services.payment.vnpay_service.verify_return_params", return_value=True)
def test_api_pay_10_return_order_not_found(mock_verify):
    # Default override db returns None for order
    response = client.get("/api/v1/payment/return?vnp_TxnRef=123&vnp_SecureHash=fake&vnp_ResponseCode=00")
    assert response.json()["success"] is False
    assert response.json()["message"] == "Order not found"

@patch("services.payment.vnpay_service.verify_return_params", return_value=True)
def test_api_pay_11_return_success(mock_verify):
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_order = Payment(order_code="123", status="pending")
    mock_result.scalar_one_or_none.return_value = mock_order
    mock_session.execute.return_value = mock_result
    
    app.dependency_overrides[get_db_session] = lambda: mock_session
    patcher = patch('core.database.async_session_factory')
    mock_factory = patcher.start()
    mock_factory.return_value.__aenter__.return_value = mock_session
    import atexit
    atexit.register(patcher.stop)
    response = client.get("/api/v1/payment/return?vnp_TxnRef=123&vnp_SecureHash=fake&vnp_ResponseCode=00")
    app.dependency_overrides[get_db_session] = override_db
    
    assert response.json()["success"] is True

def test_api_pay_12_ipn_invalid_signature():
    response = client.get("/api/v1/payment/ipn?vnp_TxnRef=123&vnp_SecureHash=fake")
    assert response.json()["RspCode"] == "97"

@patch("services.payment.vnpay_service.verify_return_params", return_value=True)
def test_api_pay_13_ipn_order_processed(mock_verify):
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_order = Payment(order_code="123", status="success")
    mock_result.scalar_one_or_none.return_value = mock_order
    mock_session.execute.return_value = mock_result
    
    app.dependency_overrides[get_db_session] = lambda: mock_session
    patcher = patch('core.database.async_session_factory')
    mock_factory = patcher.start()
    mock_factory.return_value.__aenter__.return_value = mock_session
    import atexit
    atexit.register(patcher.stop)
    response = client.get("/api/v1/payment/ipn?vnp_TxnRef=123&vnp_SecureHash=fake&vnp_ResponseCode=00")
    app.dependency_overrides[get_db_session] = override_db
    
    assert response.json()["RspCode"] == "02"

def test_api_pay_14_info_found():
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_order = Payment(
        id=1,
        order_code="123",
        amount=100000,
        location="ngo_mon",
        customer_name="A",
        customer_email="a@a.com",
        customer_phone="0123",
        adult_count=1,
        children_paid_count=0,
        children_free_count=0,
        items='[{"key": "cafe", "quantity": 1}]',
        status="success"
    )
    mock_result.scalar_one_or_none.return_value = mock_order
    mock_session.execute.return_value = mock_result
    
    app.dependency_overrides[get_db_session] = lambda: mock_session
    patcher = patch('core.database.async_session_factory')
    mock_factory = patcher.start()
    mock_factory.return_value.__aenter__.return_value = mock_session
    import atexit
    atexit.register(patcher.stop)
    response = client.get("/api/v1/payment/info/123")
    app.dependency_overrides[get_db_session] = override_db
    
    assert response.status_code in [200, 201]
    assert response.json()["payment"]["orderCode"] == "123"
    assert "items" in response.json()["payment"]

def test_api_pay_15_info_missing():
    response = client.get("/api/v1/payment/info/999")
    assert response.status_code in [404, 500]
