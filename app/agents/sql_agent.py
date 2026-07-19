from app.tools import (
    get_order_details,
    get_refund_policy,
    get_return_policy,
    get_cancellation_policy,
    get_shipping_policy,
)


def retrieve_data(
    query: str,
    intent: str,
    order_id: str | None = None,
) -> str:

    if intent in {"order_status", "payment_issue"}:
        return get_order_details.invoke({
            "order_id": order_id or ""
        })

    if intent == "refund_policy":
        return get_refund_policy.invoke({})

    if intent == "return_policy":
        return get_return_policy.invoke({})

    if intent == "order_cancellation":
        return get_cancellation_policy.invoke({})

    if intent == "shipping_information":
        if order_id:
            return get_order_details.invoke({
                "order_id": order_id
            })
        return get_shipping_policy.invoke({})

    return "No relevant information found."