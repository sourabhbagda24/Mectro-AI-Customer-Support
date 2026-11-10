"""
Agent 2 — Database Agent (LLM tool-calling).

The Groq LLaMA 3.3 model is bound to the 5 tools and decides which one to
call. If the model makes no valid tool call (or the API fails), we fall back
to deterministic intent -> tool routing so the pipeline never breaks.
"""
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.config import settings
from app.tools import (
    TOOLS,
    TOOLS_BY_NAME,
    get_cancellation_policy,
    get_order_details,
    get_refund_policy,
    get_return_policy,
    get_shipping_policy,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the data-retrieval agent for Mectro customer support.
Call the single most relevant tool for the customer's intent.
- order_status / payment_issue -> get_order_details (needs the order ID)
- refund_policy -> get_refund_policy
- return_policy -> get_return_policy
- order_cancellation -> get_cancellation_policy
- shipping_information -> get_order_details if an order ID is given,
  otherwise get_shipping_policy
Never invent an order ID. If none is given for an order lookup, do not call a tool."""

llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_MODEL,
    temperature=0,
).bind_tools(TOOLS)


def _fallback(intent: str, order_id: str | None) -> str:
    """Deterministic routing used when the LLM does not call a tool."""
    if intent in {"order_status", "payment_issue"}:
        return get_order_details.invoke({"order_id": order_id or ""})
    if intent == "refund_policy":
        return get_refund_policy.invoke({})
    if intent == "return_policy":
        return get_return_policy.invoke({})
    if intent == "order_cancellation":
        return get_cancellation_policy.invoke({})
    if intent == "shipping_information":
        if order_id:
            return get_order_details.invoke({"order_id": order_id})
        return get_shipping_policy.invoke({})
    return "No relevant information found."


def retrieve_data(query: str, intent: str, order_id: str | None = None) -> str:
    if intent == "unknown":
        return "No relevant information found."

    try:
        ai_msg = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=f"Query: {query}\nIntent: {intent}\nOrder ID: {order_id}"
            ),
        ])
    except Exception:
        logger.exception("Tool-calling LLM failed, using fallback routing")
        return _fallback(intent, order_id)

    results = []
    for call in ai_msg.tool_calls:
        tool_fn = TOOLS_BY_NAME.get(call["name"])
        if tool_fn is None:
            continue
        logger.info("tool_call=%s args=%s", call["name"], call["args"])
        try:
            results.append(tool_fn.invoke(call["args"]))
        except Exception:
            logger.exception("Tool %s failed", call["name"])

    return "\n".join(results) if results else _fallback(intent, order_id)