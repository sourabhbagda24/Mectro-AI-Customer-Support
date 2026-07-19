import logging

from app.agents.intent_agent import detect_intent
from app.agents.sql_agent import retrieve_data
from app.agents.response_agent import generate_response
from app import database as db


logger = logging.getLogger(__name__)


def run_support_pipeline(query: str, persist_log: bool = True) -> dict:
    intent = detect_intent(query)

    logger.info(
        "intent=%s order_id=%s",
        intent.intent,
        intent.order_id,
    )

    data = retrieve_data(
        query=query,
        intent=intent.intent,
        order_id=intent.order_id,
    )

    response = generate_response(
        query=query,
        intent=intent.intent,
        retrieved_data=data,
    )

    if persist_log:
        try:
            db.log_interaction(
                customer_query=query,
                intent=intent.intent,
                order_id=intent.order_id,
                retrieved_data=data,
                final_response=response,
            )
        except Exception:
            logger.exception("Failed to save support log")

    return {
        "customer_query": query,
        "detected_intent": intent.intent,
        "intent_reasoning": intent.reasoning,
        "order_id": intent.order_id,
        "retrieved_data": data,
        "final_response": response,
    }