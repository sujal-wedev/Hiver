"""
Milestone 5: Baseline Implementations for Intent Classification and Escalation.
Provides:
1. Trivial Baseline: Always predicts majority intent (order_status_delivery) and always escalates.
2. Simple Baseline: Keyword-rule intent classification + simple heuristic escalation.
"""

import re
from typing import Dict, Any
from src.taxonomy import Intent

class TrivialBaselineAgent:
    """Always predicts majority intent and always escalates every message."""
    def handle_message(self, text: str, thread_length: int = 1) -> Dict[str, Any]:
        return {
            "intent": Intent.ORDER_STATUS_DELIVERY.value,
            "confidence": 1.0,
            "reply": "Please reach out to AmazonHelp via direct message. ^AH",
            "decision": "escalate",
            "reason": "Trivial Baseline: Blanket escalation rule for all incoming messages.",
            "retrieved_context": "No retrieval context used in trivial baseline.",
            "hallucination_detected": False,
            "hallucination_flags": [],
            "model_type": "trivial_baseline"
        }

class SimpleBaselineAgent:
    """Keyword-matching intent classification and heuristic rule escalation."""
    def __init__(self):
        self.rules = [
            (r"\b(?:refund|return|return label|send back|drop off)\b", Intent.REFUND_RETURN.value),
            (r"\b(?:charge|billed|card|bank|double charged|payment|\$)\b", Intent.BILLING_DISPUTE.value),
            (r"\b(?:password|login|otp|locked|sign in|hacked)\b", Intent.ACCOUNT_ACCESS.value),
            (r"\b(?:broken|damaged|wrong item|defective|scratched|shattered)\b", Intent.PRODUCT_ISSUE.value),
            (r"\b(?:app|website|bug|500|cart|glitch)\b", Intent.APP_WEBSITE_BUG.value),
            (r"\b(?:cancel|cancellation|prime membership)\b", Intent.CANCELLATION.value),
            (r"\b(?:track|tracking|package|delivery|shipment|delayed|where is)\b", Intent.ORDER_STATUS_DELIVERY.value),
            (r"\b(?:worst|terrible|hate|useless|scam)\b", Intent.GENERAL_COMPLAINT_VENT.value),
        ]

    def classify_intent(self, text: str) -> str:
        text_lower = text.lower()
        for pattern, intent in self.rules:
            if re.search(pattern, text_lower):
                return intent
        return Intent.OTHER_UNCLEAR.value

    def handle_message(self, text: str, thread_length: int = 1) -> Dict[str, Any]:
        intent = self.classify_intent(text)
        text_lower = text.lower()

        should_escalate = False
        reason = "Auto-handled by simple keyword heuristic"

        if thread_length > 1:
            should_escalate = True
            reason = "Escalated: Multi-turn thread detected"
        elif any(k in text_lower for k in ["charge", "lawyer", "attorney", "sue", "refund", "dollar", "$"]):
            should_escalate = True
            reason = "Escalated: Financial or dispute keyword matched"

        decision = "escalate" if should_escalate else "auto_handle"

        return {
            "intent": intent,
            "confidence": 0.70,
            "reply": "Please send us a direct message with your account details so we can look into this for you. ^AH",
            "decision": decision,
            "reason": reason,
            "retrieved_context": "Keyword rule baseline - no semantic RAG retrieval.",
            "hallucination_detected": False,
            "hallucination_flags": [],
            "model_type": "simple_baseline"
        }

# Class Aliases for backwards compatibility
TrivialBaseline = TrivialBaselineAgent
SimpleBaseline = SimpleBaselineAgent
