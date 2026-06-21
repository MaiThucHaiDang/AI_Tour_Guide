"""VNPay ticket payment API router."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.observability import increment
from models.payment import Payment
from schemas.payment import (
    FOOD_ITEMS,
    LOCATION_PRICES,
    FoodItemsResponse,
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaymentInfo,
    PaymentInfoResponse,
    PaymentReturnResponse,
)
from services.payment.vnpay_service import (
    _build_order_desc,
    _generate_order_code,
    create_payment_url,
    verify_return_params,
)

router = APIRouter(prefix="/api/v1/payment", tags=["Payment"])
_LOGGER = logging.getLogger(__name__)


async def _update_order_from_vnpay(order: Payment, params: dict) -> None:
    """Apply VNPay response params to an order."""
    order.vnpay_response_code = params.get("vnp_ResponseCode", "")
    order.vnpay_transaction_no = params.get("vnp_TransactionNo", "")
    order.vnpay_bank_code = params.get("vnp_BankCode", "")
    order.vnpay_pay_date = params.get("vnp_PayDate", "")
    order.updated_at = datetime.now(timezone.utc)

    response_code = params.get("vnp_ResponseCode", "")
    if response_code == "00":
        order.status = "success"
        increment("payment.success")
    else:
        order.status = "failed"
        increment("payment.failed")


@router.get("/food-items", response_model=FoodItemsResponse)
async def get_food_items() -> FoodItemsResponse:
    """Return available food & drink items with prices."""
    return FoodItemsResponse(items=FOOD_ITEMS)


@router.post("/create", response_model=PaymentCreateResponse, status_code=201)
async def create_payment(
    request: Request,
    body: PaymentCreateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> PaymentCreateResponse:
    """Create a ticket payment order and return the VNPay Sandbox payment URL."""
    unit_price = LOCATION_PRICES.get(body.location)
    if unit_price is None:
        raise HTTPException(status_code=400, detail="Invalid location selected.")

    total_amount = body.calc_total()
    order_code = _generate_order_code()
    items_json = json.dumps([it.model_dump() for it in body.items], ensure_ascii=False)

    order = Payment(
        order_code=order_code,
        amount=total_amount,
        location=body.location,
        customer_name=body.customer_name,
        customer_email=body.customer_email,
        customer_phone=body.customer_phone,
        adult_count=body.adult_count,
        children_paid_count=body.children_paid_count,
        children_free_count=body.children_free_count,
        items=items_json,
        status="pending",
    )
    db.add(order)
    await db.flush()
    await db.commit()

    items_for_desc = []
    for it in body.items:
        info = FOOD_ITEMS.get(it.key)
        if info:
            items_for_desc.append({"key": it.key, "name_vi": info["name_vi"], "quantity": it.quantity})

    order_desc = _build_order_desc(body.location, body.adult_count, body.children_paid_count, body.children_free_count, items_for_desc)

    client_ip = request.client.host if request.client else "127.0.0.1"
    payment_url = create_payment_url(
        amount=total_amount,
        order_code=order.order_code,
        order_desc=order_desc,
        client_ip=client_ip,
    )

    increment("payment.order_created")
    _LOGGER.info("Payment order %s created for %s, amount=%d", order.order_code, body.location, total_amount)

    return PaymentCreateResponse(
        paymentUrl=payment_url,
        orderCode=order.order_code,
        amount=total_amount,
        location=body.location,
        adultCount=body.adult_count,
        childrenPaidCount=body.children_paid_count,
        childrenFreeCount=body.children_free_count,
    )


@router.get("/return")
async def payment_return(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> PaymentReturnResponse:
    """Handle VNPay return URL after user completes payment on Sandbox."""
    params = dict(request.query_params)

    if not params.get("vnp_SecureHash"):
        return PaymentReturnResponse(
            success=False,
            message="Missing signature",
            orderCode="",
            status="failed",
        )

    order_code = params.get("vnp_TxnRef", "")

    if not verify_return_params(params):
        _LOGGER.warning("Invalid VNPay signature for order %s", order_code)
        return PaymentReturnResponse(
            success=False,
            message="Invalid signature",
            orderCode=order_code,
            status="failed",
        )

    stmt = select(Payment).where(Payment.order_code == order_code)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if order is None:
        _LOGGER.warning("Order %s not found in VNPay return", order_code)
        return PaymentReturnResponse(
            success=False,
            message="Order not found",
            orderCode=order_code,
            status="failed",
        )

    response_code = params.get("vnp_ResponseCode", "")
    await _update_order_from_vnpay(order, params)
    await db.flush()
    await db.commit()

    _LOGGER.info(
        "Payment return for order %s, code=%s, status=%s",
        order_code, response_code, order.status,
    )
    return PaymentReturnResponse(
        success=response_code == "00",
        message="Payment successful" if response_code == "00" else f"Payment failed (code: {response_code})",
        orderCode=order_code,
        status=order.status,
    )


@router.get("/ipn")
async def payment_ipn(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Handle VNPay IPN (server-to-server) callback."""
    params = dict(request.query_params)
    order_code = params.get("vnp_TxnRef", "")
    response_code = params.get("vnp_ResponseCode", "")

    if not params.get("vnp_SecureHash"):
        _LOGGER.warning("IPN missing signature for order %s", order_code)
        return {"RspCode": "97", "Message": "Invalid signature"}

    if not verify_return_params(params):
        _LOGGER.warning("IPN invalid signature for order %s", order_code)
        return {"RspCode": "97", "Message": "Invalid signature"}

    stmt = select(Payment).where(Payment.order_code == order_code)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if order is None:
        _LOGGER.warning("IPN order not found: %s", order_code)
        return {"RspCode": "01", "Message": "Order not found"}

    if order.status != "pending":
        _LOGGER.info("IPN order %s already processed (status=%s)", order_code, order.status)
        return {"RspCode": "02", "Message": "Order already confirmed"}

    await _update_order_from_vnpay(order, params)
    await db.flush()
    await db.commit()

    if response_code == "00":
        _LOGGER.info("IPN confirmed success for order %s", order_code)
        return {"RspCode": "00", "Message": "Confirm success"}
    else:
        _LOGGER.info("IPN confirmed failed for order %s, code=%s", order_code, response_code)
        return {"RspCode": "00", "Message": "Confirm success"}


@router.get("/info/{order_code}", response_model=PaymentInfoResponse)
async def get_payment_info(
    order_code: str,
    db: AsyncSession = Depends(get_db_session),
) -> PaymentInfoResponse:
    """Get payment order information by order code."""
    stmt = select(Payment).where(Payment.order_code == order_code)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    increment("payment.info_queried")
    items_data = json.loads(order.items) if order.items else []
    return PaymentInfoResponse(
        payment=PaymentInfo(
            id=order.id,
            orderCode=order.order_code,
            amount=order.amount,
            location=order.location,
            customerName=order.customer_name,
            customerEmail=order.customer_email,
            customerPhone=order.customer_phone,
            adultCount=order.adult_count,
            childrenPaidCount=order.children_paid_count,
            childrenFreeCount=order.children_free_count,
            items=items_data,
            status=order.status,
            vnpay_response_code=order.vnpay_response_code,
            vnpay_transaction_no=order.vnpay_transaction_no,
            vnpay_bank_code=order.vnpay_bank_code,
            created_at=order.created_at,
        )
    )
