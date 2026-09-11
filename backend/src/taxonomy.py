"""
Intent Taxonomy Definitions & Standardized Prompt Formatters for AmazonHelp.
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

INTENT_DESCRIPTIONS: Dict[str, str] = {
    Intent.ORDER_STATUS_DELIVERY.value: "Inquiries regarding package tracking, shipment status, delayed delivery, lost in transit, or delivered-not-received.",
    Intent.REFUND_RETURN.value: "Requests to return an item, check return label status, check refund status, or ask about return policies.",
    Intent.BILLING_DISPUTE.value: "Disputes over unexpected charges, double billing, unauthorized transactions, or payment processing errors.",
    Intent.ACCOUNT_ACCESS.value: "Issues logging into account, 2FA code failures, password reset problems, or account suspension/lockout.",
    Intent.PRODUCT_ISSUE.value: "Reports of damaged, broken, defective, missing parts, or incorrect items received.",
    Intent.APP_WEBSITE_BUG.value: "Technical issues with Amazon app or website, checkout HTTP 500 errors, cart glitches, or search bugs.",
    Intent.CANCELLATION.value: "Requests to cancel an order before dispatch or cancel Prime subscription membership.",
    Intent.GENERAL_COMPLAINT_VENT.value: "Expressions of anger, frustration, or dissatisfaction with service quality without a specific actionable request.",
    Intent.OTHER_UNCLEAR.value: "Vague, ambiguous, incomplete, or off-topic customer messages that require clarification."
}

ALL_INTENTS: List[str] = list(INTENT_DESCRIPTIONS.keys())

def get_taxonomy_prompt_string() -> str:
    """Formats the intent taxonomy into a concise prompt block for LLMs."""
    lines = []
    for intent, desc in INTENT_DESCRIPTIONS.items():
        lines.append(f"- `{intent}`: {desc}")
    return "\n".join(lines)
