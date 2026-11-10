"""Pydantic models for tool inputs/outputs and the API contract."""
from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

PolicyType = Literal[
    "refund_policy",
    "return_policy",
    "cancellation_policy",
    "shipping_policy",
]


class OrderLookupInput(BaseModel):
    """Validated input for the order lookup tool."""

    order_id: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Order ID such as ORD1001.",
    )

    @field_validator("order_id")
    @classmethod
    def normalise(cls, v: str) -> str:
        return v.strip().lstrip("#").upper()


class OrderDetails(BaseModel):
    """Validated output of the order lookup tool."""

    order_id: str
    customer_name: str
    order_status: str
    payment_status: str
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    expected_delivery: Optional[date] = None
    order_amount: Decimal


class PolicyRecord(BaseModel):
    """Validated output of the policy tools."""

    policy_type: PolicyType
    title: str
    content: str