"""
The 5 tool-calling functions used by the Database Agent.

Each tool is a LangChain @tool. Inputs are validated with Pydantic
(`args_schema`) and DB rows are validated into Pydantic models before being
returned, so the LLM only ever sees well-formed data.
"""
from pydantic import ValidationError
from langchain_core.tools import tool

from app import database as db
from app.schemas import OrderDetails, OrderLookupInput, PolicyRecord


def _policy(policy_type: str, name: str) -> str:
    row = db.fetch_policy(policy_type)
    if not row:
        return f"No {name} policy found."
    return PolicyRecord(**row).model_dump_json()


@tool
def get_refund_policy() -> str:
    """Get the refund policy (process, eligibility, timelines)."""
    return _policy("refund_policy", "refund")


@tool
def get_return_policy() -> str:
    """Get the return policy for delivered products."""
    return _policy("return_policy", "return")


@tool
def get_cancellation_policy() -> str:
    """Get the order cancellation policy."""
    return _policy("cancellation_policy", "cancellation")


@tool
def get_shipping_policy() -> str:
    """Get the general shipping policy (cost, delivery times)."""
    return _policy("shipping_policy", "shipping")


@tool(args_schema=OrderLookupInput)
def get_order_details(order_id: str) -> str:
    """Get status, payment, tracking and delivery details for one order."""
    try:
        order_id = OrderLookupInput(order_id=order_id).order_id
    except ValidationError:
        return "No order ID was provided."

    row = db.fetch_order(order_id)
    if not row:
        return f"No order found with order_id={order_id}."
    return OrderDetails(**row).model_dump_json()


TOOLS = [
    get_order_details,
    get_refund_policy,
    get_return_policy,
    get_cancellation_policy,
    get_shipping_policy,
]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}