"""
Milestone 5: Trivial and Simple Baselines for AmazonHelp Support.
Provides the benchmark floor against which the full system is evaluated.
"""

import re
from typing import Dict, Any
from src.taxonomy import Intent

class TrivialBaseline:
    """
    Trivial baseline:
    - Intent: Always predicts majority class ('order_status_delivery')
    - Decision: Always 'escalate'
    - Reply: Single fixed canned acknowledgment
    """
    def __init__(self, majority_class: str = Intent.ORDER_STATUS_DELIVERY.value):
        self.majority_class = majority_class
        self.canned_reply = (
            "Thanks for reaching out, we're looking into this and will follow up shortly. ^AH"
        )

    def handle_message(self, text: str) -> Dict[str, Any]:
        return {
            "intent": self.majority_class,
            "confidence": 0.35,
            "reply": self.canned_reply,
            "decision": "escalate",
            "reason": "Trivial policy: default escalate all messages",
            "retrieved_context": "None (Trivial baseline does not retrieve context)",
            "model_type": "trivial_baseline"
        }

class SimpleBaseline:
    """
    Simple baseline:
    - Intent: Keyword/Regex pattern matching dictionary
    - Decision: Escalate only if monetary symbol ($) or legal keyword ('lawyer', 'bbb', 'chargeback') is present
    - Reply: Fixed canned reply per predicted intent (no personalization/grounding)
    """
    def __init__(self):
        self.intent_keywords = {
            Intent.BILLING_DISPUTE.value: [r"\$", r"charge", r"billed", r"bank", r"payment", r"card", r"fee", r"overcharge"],
            Intent.ACCOUNT_ACCESS.value: [r"password", r"otp", r"login", r"log in", r"sign in", r"locked", r"hacked", r"2fa"],
            Intent.PRODUCT_ISSUE.value: [r"damaged", r"broken", r"wrong", r"defective", r"shattered", r"scratch", r"missing item"],
            Intent.REFUND_RETURN.value: [r"refund", r"return", r"send back", r"drop off", r"label", r"exchange"],
            Intent.CANCELLATION.value: [r"cancel", r"cancellation", r"stop order"],
            Intent.ORDER_STATUS_DELIVERY.value: [r"where", r"package", r"tracking", r"carrier", r"delivery", r"deliver", r"late", r"arrive"],
            Intent.APP_WEBSITE_BUG.value: [r"app", r"crash", r"website", r"cart", r"checkout", r"bug", r"glitch", r"error"],
            Intent.GENERAL_COMPLAINT_VENT.value: [r"worst", r"terrible", r"scam", r"pathetic", r"horrible", r"unacceptable", r"hate"]
        }

        self.canned_replies = {
            Intent.ORDER_STATUS_DELIVERY.value: "We're sorry for the delivery delay! Please track your parcel in Your Orders or DM us your order ID for status. ^AH",
            Intent.REFUND_RETURN.value: "We can help with your return! Please visit Your Orders on Amazon to print a return label or generate a drop-off QR code. ^AH",
            Intent.BILLING_DISPUTE.value: "We take billing questions seriously. Please DM us your account email so our billing team can review the charge. ^AH",
            Intent.ACCOUNT_ACCESS.value: "For account security assistance, please visit amazon.com/help or DM us your email to reset your credentials. ^AH",
            Intent.PRODUCT_ISSUE.value: "We are sorry your item was damaged or incorrect! Please DM us your order ID so we can issue a replacement. ^AH",
            Intent.APP_WEBSITE_BUG.value: "Sorry for the glitch! Please try clearing your browser cache or updating the Amazon app, and DM us if it persists. ^AH",
            Intent.CANCELLATION.value: "You can request cancellation in Your Orders if the item has not dispatched yet. DM us if you need help! ^AH",
            Intent.GENERAL_COMPLAINT_VENT.value: "We apologize for your frustrating experience. Please DM us your details so we can investigate and assist. ^AH",
            Intent.OTHER_UNCLEAR.value: "Thanks for contacting Amazon Help! Please send us a direct message with more details on how we can assist. ^AH"
        }

    def predict_intent(self, text: str) -> tuple[str, float]:
        text_lower = text.lower()
        for intent, patterns in self.intent_keywords.items():
            for p in patterns:
                if re.search(r"\b" + p + r"\b" if not p.startswith("\\$") else p, text_lower):
                    return intent, 0.70
        return Intent.OTHER_UNCLEAR.value, 0.30

    def evaluate_escalation(self, text: str) -> tuple[str, str]:
        text_lower = text.lower()
        if re.search(r"\$\d+", text) or any(k in text_lower for k in ["lawyer", "bbb", "chargeback", "legal", "court"]):
            return "escalate", "Simple rule fired: Monetary symbol or legal threat keyword detected"
        return "auto_handle", "Simple rule: No high-risk monetary or legal keywords found"

    def handle_message(self, text: str) -> Dict[str, Any]:
        intent, conf = self.predict_intent(text)
        decision, reason = self.evaluate_escalation(text)
        reply = self.canned_replies.get(intent, self.canned_replies[Intent.OTHER_UNCLEAR.value])

        return {
            "intent": intent,
            "confidence": conf,
            "reply": reply,
            "decision": decision,
            "reason": reason,
            "retrieved_context": "None (Simple baseline uses canned intent templates)",
            "model_type": "simple_baseline"
        }
