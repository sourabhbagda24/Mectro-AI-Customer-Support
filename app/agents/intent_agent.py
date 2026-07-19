from typing import Optional, Literal
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from app.config import settings


Intent = Literal[
    "order_status",
    "refund_policy",
    "order_cancellation",
    "payment_issue",
    "shipping_information",
    "return_policy",
    "unknown",
]


class IntentResult(BaseModel):
    intent: Intent
    order_id: Optional[str] = None
    reasoning: str = Field(description="Short reason for the selected intent.")


prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """Classify the customer query into exactly one intent:
- order_status: order location or current status
- refund_policy: refund policy, process, or timeline
- order_cancellation: canceling an order or cancellation rules
- payment_issue: failed, pending, incorrect, or payment-method issues
- shipping_information: general shipping details, cost, or delivery time
- return_policy: returning a delivered product
- unknown: anything else

Extract any order ID such as ORD1001, #1234, or order number 5566.
Return null if no order ID is present.
Keep reasoning to one short sentence."""
    ),
    ("human", "{query}"),
])


llm = ChatGroq(
    api_key=settings.GROQ_API_KEY,
    model=settings.GROQ_MODEL,
    temperature=0,
)

chain = prompt | llm.with_structured_output(IntentResult)


def detect_intent(query: str) -> IntentResult:
    return chain.invoke({"query": query})