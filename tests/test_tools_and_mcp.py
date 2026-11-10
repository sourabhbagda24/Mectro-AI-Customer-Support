import asyncio
import json
import os
from datetime import date
from decimal import Decimal

os.environ.setdefault("GROQ_API_KEY", "test-key")

from app import database as db  # noqa: E402

ORDER = {
    "order_id": "ORD1001", "customer_name": "Aditi Sharma",
    "order_status": "Shipped", "payment_status": "Paid",
    "tracking_number": "TRK1", "carrier": "BlueDart",
    "expected_delivery": date(2026, 8, 1), "order_amount": Decimal("99.50"),
}
POLICY = {"policy_type": "refund_policy", "title": "Refunds", "content": "7 days."}


def test_order_tool_validates_and_normalises(monkeypatch):
    from app.tools import get_order_details
    monkeypatch.setattr(db, "fetch_order", lambda oid: ORDER if oid == "ORD1001" else None)
    out = json.loads(get_order_details.invoke({"order_id": " #ord1001 "}))
    assert out["order_id"] == "ORD1001" and out["order_status"] == "Shipped"
    assert "No order found" in get_order_details.invoke({"order_id": "ORD9"})


def test_policy_tool(monkeypatch):
    from app.tools import get_refund_policy
    monkeypatch.setattr(db, "fetch_policy", lambda t: POLICY)
    assert json.loads(get_refund_policy.invoke({}))["title"] == "Refunds"


def test_five_tools_registered():
    from app.tools import TOOLS
    assert len(TOOLS) == 5


def test_agent_falls_back_when_llm_makes_no_tool_call(monkeypatch):
    from app.agents import sql_agent

    class FakeLLM:
        def invoke(self, _):
            class M:
                tool_calls = []
            return M()

    monkeypatch.setattr(sql_agent, "llm", FakeLLM())
    monkeypatch.setattr(db, "fetch_policy", lambda t: POLICY)
    out = sql_agent.retrieve_data("refund?", "refund_policy")
    assert "Refunds" in out


def test_agent_executes_llm_tool_call(monkeypatch):
    from app.agents import sql_agent

    class FakeLLM:
        def invoke(self, _):
            class M:
                tool_calls = [{"name": "get_order_details", "args": {"order_id": "ORD1001"}, "id": "1"}]
            return M()

    monkeypatch.setattr(sql_agent, "llm", FakeLLM())
    monkeypatch.setattr(db, "fetch_order", lambda oid: ORDER)
    assert "Aditi Sharma" in sql_agent.retrieve_data("where is it", "order_status", "ORD1001")


def test_mcp_server_exposes_five_tools():
    from app.mcp_server import mcp
    tools = asyncio.run(mcp.get_tools())
    assert set(tools) == {
        "get_order_details", "get_refund_policy", "get_return_policy",
        "get_cancellation_policy", "get_shipping_policy",
    }


def test_api_app_imports():
    from app.main import app
    assert any(r.path == "/api/support/query" for r in app.routes)