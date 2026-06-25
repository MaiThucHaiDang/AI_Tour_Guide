"""Pydantic schemas for VNPay ticket payment."""

from __future__ import annotations
import json
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, EmailStr

ALLOWED_LOCATIONS = ["Ngọ Môn", "Điện Long An"]

NgocMonPricing = dict(adult=200_000, children_paid=40_000)
DienLongAnPricing = dict(adult=50_000, children_paid=None)

LOCATION_PRICES: dict[str, dict] = {
    "Ngọ Môn": NgocMonPricing,
    "Điện Long An": DienLongAnPricing,
}

FOOD_ITEMS: dict[str, dict[str, Any]] = {
    "nuoc_suoi": {"name_vi": "Nước suối", "name_en": "Water", "price": 10000, "image": "/assets/images/nuocsuoi.jpg"},
    "nuoc_ngot": {"name_vi": "Nước ngọt", "name_en": "Soft drink", "price": 15000, "image": "/assets/images/nuocngot.jpg"},
    "ca_phe": {"name_vi": "Cà phê", "name_en": "Coffee", "price": 20000, "image": "/assets/images/caphe.jpg"},
    "tra_da": {"name_vi": "Trà đá", "name_en": "Iced tea", "price": 5000, "image": "/assets/images/trada.jpg"},
    "banh_mi": {"name_vi": "Bánh mì", "name_en": "Bread", "price": 25000, "image": "/assets/images/banhmi.jpg"},
    "banh_trang": {"name_vi": "Bánh tráng trộn", "name_en": "Rice paper mix", "price": 15000, "image": "/assets/images/banhtrangtron.jpg"},
    "bong_ngo": {"name_vi": "Bỏng ngô", "name_en": "Popcorn", "price": 10000, "image": "/assets/images/bongngo.jpg"},
    "kem": {"name_vi": "Kem", "name_en": "Ice cream", "price": 15000, "image": "/assets/images/kem.jpg"},
}


class ItemSelection(BaseModel):
    key: str
    quantity: int = Field(default=1, ge=0, le=50)


class PaymentCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    location: str = Field(min_length=1, max_length=100)
    customer_name: str = Field(min_length=1, max_length=255, alias="customerName")
    customer_email: EmailStr = Field(alias="customerEmail")
    customer_phone: str = Field(min_length=1, max_length=20, alias="customerPhone")
    adult_count: int = Field(default=1, ge=1, le=100, alias="adultCount")
    children_paid_count: int = Field(default=0, ge=0, le=100, alias="childrenPaidCount")
    children_free_count: int = Field(default=0, ge=0, le=100, alias="childrenFreeCount")
    items: list[ItemSelection] = Field(default_factory=list)
    return_url: str | None = Field(default=None, alias="returnUrl")

    @field_validator("location")
    @classmethod
    def validate_location(cls, value: str) -> str:
        if value not in ALLOWED_LOCATIONS:
            raise ValueError(f"Location must be one of: {', '.join(ALLOWED_LOCATIONS)}")
        return value

    @field_validator("customer_phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned.isdigit() or len(cleaned) < 9 or len(cleaned) > 15:
            raise ValueError("Invalid phone number")
        return cleaned
        
    @field_validator("items")
    @classmethod
    def validate_items(cls, value: list[ItemSelection]) -> list[ItemSelection]:
        for it in value:
            if it.key not in FOOD_ITEMS:
                raise ValueError(f"Invalid food item: {it.key}")
        return value

    def calc_total(self) -> int:
        prices = LOCATION_PRICES.get(self.location, {})
        ticket_total = self.adult_count * prices.get("adult", 0)
        if prices.get("children_paid"):
            ticket_total += self.children_paid_count * prices["children_paid"]
        items_total = sum(
            FOOD_ITEMS[it.key]["price"] * it.quantity
            for it in self.items
        )
        return ticket_total + items_total


class PaymentCreateResponse(BaseModel):
    success: bool = True
    payment_url: str = Field(alias="paymentUrl")
    order_code: str = Field(alias="orderCode")
    amount: int
    location: str
    adult_count: int = Field(alias="adultCount")
    children_paid_count: int = Field(alias="childrenPaidCount")
    children_free_count: int = Field(alias="childrenFreeCount")


class PaymentInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    order_code: str = Field(alias="orderCode")
    amount: int
    location: str
    customer_name: str = Field(alias="customerName")
    customer_email: str = Field(alias="customerEmail")
    customer_phone: str = Field(alias="customerPhone")
    adult_count: int = Field(alias="adultCount")
    children_paid_count: int = Field(alias="childrenPaidCount")
    children_free_count: int = Field(alias="childrenFreeCount")
    items: list[ItemSelection] | None = None
    status: str
    vnpay_txn_ref: str | None = Field(default=None, alias="vnpayTxnRef")
    vnpay_response_code: str | None = Field(default=None, alias="vnpayResponseCode")
    vnpay_transaction_no: str | None = Field(default=None, alias="vnpayTransactionNo")
    vnpay_bank_code: str | None = Field(default=None, alias="vnpayBankCode")
    created_at: datetime = Field(alias="createdAt")

    @field_validator("items", mode="before")
    @classmethod
    def parse_items(cls, value: Any) -> Any:
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return []
        return value


class PaymentInfoResponse(BaseModel):
    success: bool = True
    payment: PaymentInfo


class PaymentReturnResponse(BaseModel):
    success: bool
    message: str
    order_code: str = Field(alias="orderCode")
    status: str


class FoodItemsResponse(BaseModel):
    success: bool = True
    items: dict[str, dict[str, Any]]
