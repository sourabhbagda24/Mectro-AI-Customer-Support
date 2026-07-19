from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from app.config import settings


_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine

    if _engine is None:
        _engine = create_engine(
            settings.sqlalchemy_uri,
            pool_pre_ping=True,
        )

    return _engine


POLICIES = {
    "refund_policy",
    "return_policy",
    "cancellation_policy",
    "shipping_policy",
}


def fetch_policy(policy_type: str) -> dict | None:
    if policy_type not in POLICIES:
        return None

    with get_engine().connect() as conn:
        row = conn.execute(
            text("""
                SELECT policy_type, title, content
                FROM policies
                WHERE policy_type = :type
                LIMIT 1
            """),
            {"type": policy_type},
        ).mappings().first()

    return dict(row) if row else None


def fetch_order(order_id: str) -> dict | None:
    if not order_id:
        return None

    with get_engine().connect() as conn:
        row = conn.execute(
            text("""
                SELECT order_id, customer_name, order_status,
                       payment_status, tracking_number, carrier,
                       expected_delivery, order_amount
                FROM orders
                WHERE UPPER(order_id) = UPPER(:id)
                LIMIT 1
            """),
            {"id": order_id},
        ).mappings().first()

    return dict(row) if row else None


def log_interaction(
    customer_query: str,
    intent: str,
    order_id: str | None,
    retrieved_data: str,
    final_response: str,
) -> None:
    with get_engine().begin() as conn:
        conn.execute(
            text("""
                INSERT INTO support_logs
                (customer_query, detected_intent, order_id,
                 retrieved_data, final_response)
                VALUES (:query, :intent, :order_id, :data, :response)
            """),
            {
                "query": customer_query,
                "intent": intent,
                "order_id": order_id,
                "data": retrieved_data,
                "response": final_response,
            },
        )