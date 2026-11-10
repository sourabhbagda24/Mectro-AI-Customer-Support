"""
FastMCP server exposing the support tools over the Model Context Protocol.

Any MCP client (Claude Desktop, Cursor, custom agents) can call the same 5
database tools the internal Database Agent uses.

Run (stdio, for Claude Desktop):   python -m app.mcp_server
Run (HTTP/SSE):                    python -m app.mcp_server --http
"""
import json
import sys

from fastmcp import FastMCP

from app import database as db
from app.schemas import OrderDetails, OrderLookupInput, PolicyRecord

mcp = FastMCP("Mectro Support Tools")


def _policy(policy_type: str) -> dict:
    row = db.fetch_policy(policy_type)
    if not row:
        return {"error": f"No {policy_type} found."}
    return json.loads(PolicyRecord(**row).model_dump_json())


@mcp.tool()
def get_order_details(order_id: str) -> dict:
    """Get status, payment, tracking and delivery details for one order."""
    order_id = OrderLookupInput(order_id=order_id).order_id
    row = db.fetch_order(order_id)
    if not row:
        return {"error": f"No order found with order_id={order_id}."}
    return json.loads(OrderDetails(**row).model_dump_json())


@mcp.tool()
def get_refund_policy() -> dict:
    """Get the refund policy."""
    return _policy("refund_policy")


@mcp.tool()
def get_return_policy() -> dict:
    """Get the return policy."""
    return _policy("return_policy")


@mcp.tool()
def get_cancellation_policy() -> dict:
    """Get the cancellation policy."""
    return _policy("cancellation_policy")


@mcp.tool()
def get_shipping_policy() -> dict:
    """Get the shipping policy."""
    return _policy("shipping_policy")


if __name__ == "__main__":
    if "--http" in sys.argv:
        mcp.run(transport="sse", host="127.0.0.1", port=8001)
    else:
        mcp.run()