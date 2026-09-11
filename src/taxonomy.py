"""
Taxonomy of customer intents for AmazonHelp Twitter Support.
Frozen post-clustering as single source of truth for labeling, classification, and eval.
"""

from enum import Enum
from typing import Dict, List

class Intent(str, Enum):
    ORDER_STATUS_DELIVERY = "order_status_delivery"
    REFUND_RETURN = "refund_return"
    BILLING_DISPUTE = "billing_dispute"
    ACCOUNT_ACCESS = "account_access"
    PRODUCT_ISSUE = "product_issue"
    APP_WEBSITE_BUG = "app_website_bug"
    CANCELLATION = "cancellation"
    GENERAL_COMPLAINT_VENT = "general_complaint_vent"
    OTHER_UNCLEAR = "other_unclear"

INTENT_DEFINITIONS: Dict[str, str] = {
    Intent.ORDER_STATUS_DELIVERY.value: (
        "Customer asking where an order is, delivery delayed/missing, tracking confusion, "
        "carrier delivery attempts, marked delivered but package not received."
    ),
    Intent.REFUND_RETURN.value: (
        "Customer wants money back or wants to return an item; return window queries, "
        "refund not received, drop-off location or return label issues."
    ),
    Intent.BILLING_DISPUTE.value: (
        "Charged incorrectly, double-charged, unauthorized payment, Prime auto-renewal "
        "disputes, unexpected credit card charges."
    ),
    Intent.ACCOUNT_ACCESS.value: (
        "Locked out of Amazon account, OTP/2FA issues, password reset problems, "
        "account suspended or security hold."
    ),
    Intent.PRODUCT_ISSUE.value: (
        "Item arrived broken/damaged, wrong item or wrong size delivered, missing components, "
        "defective electronic device."
    ),
    Intent.APP_WEBSITE_BUG.value: (
        "Technical fault in the Amazon app or website, cart errors, checkout crashing, "
        "search filter malfunctioning, broken web pages."
    ),
    Intent.CANCELLATION.value: (
        "Customer wants to cancel an order before dispatch, cancel a subscription, "
        "or cancel Amazon Prime membership."
    ),
    Intent.GENERAL_COMPLAINT_VENT.value: (
        "Expressing general frustration, sarcasm, poor customer service vent with no "
        "actionable question or procedural resolution request."
    ),
    Intent.OTHER_UNCLEAR.value: (
        "Ambiguous message, fragmented text, foreign language without context, spam, "
        "or completely unrelated queries."
    ),
}

# Multi-intent priority resolution hierarchy (most urgent / risky first)
INTENT_PRIORITY_ORDER: List[str] = [
    Intent.BILLING_DISPUTE.value,
    Intent.ACCOUNT_ACCESS.value,
    Intent.PRODUCT_ISSUE.value,
    Intent.REFUND_RETURN.value,
    Intent.CANCELLATION.value,
    Intent.ORDER_STATUS_DELIVERY.value,
    Intent.APP_WEBSITE_BUG.value,
    Intent.GENERAL_COMPLAINT_VENT.value,
    Intent.OTHER_UNCLEAR.value,
]

ALL_INTENTS: List[str] = list(INTENT_DEFINITIONS.keys())

def get_taxonomy_prompt_string() -> str:
    """Formats the taxonomy definitions for injection into prompts."""
    lines = []
    for name, definition in INTENT_DEFINITIONS.items():
        lines.append(f"- `{name}`: {definition}")
    return "\n".join(lines)
