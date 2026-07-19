import json
from langchain_core.tools import tool
from app import database as db


def _policy(policy_type: str, name: str) -> str:
    row = db.fetch_policy(policy_type)
    return json.dumps(row) if row else f"No {name} policy found."


@tool
def get_refund_policy() -> str:
    """Get the refund policy."""
    return _policy("refund_policy", "refund")


@tool
def get_return_policy() -> str:
    """Get the return policy."""
    return _policy("return_policy", "return")


@tool
def get_cancellation_policy() -> str:
    """Get the cancellation policy."""
    return _policy("cancellation_policy", "cancellation")


@tool
def get_shipping_policy() -> str:
    """Get the general shipping policy."""
    return _policy("shipping_policy", "shipping")


@tool
def get_order_details(order_id: str) -> str:
    """Get details for a specific order."""
    if not order_id:
        return "No order ID was provided."

    row = db.fetch_order(order_id)

    return (
        json.dumps(row, default=str)
        if row
        else f"No order found with order_id={order_id}."
    )