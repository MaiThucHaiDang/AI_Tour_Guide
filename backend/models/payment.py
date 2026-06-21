"""SQLAlchemy ORM model for ticket payment orders."""

from __future__ import annotations
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    adult_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    children_paid_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    children_free_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    vnpay_txn_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vnpay_response_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    vnpay_transaction_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    vnpay_bank_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    vnpay_pay_date: Mapped[str | None] = mapped_column(String(30), nullable=True)
    vnpay_secure_hash: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
