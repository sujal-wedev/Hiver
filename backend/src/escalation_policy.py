"""
Milestone 4: Deterministic, Inspectable Escalation Policy.
Evaluates explicit deterministic risk signals (intents, financial amounts, legal threats,
severe physical/safety damage, repeat contact, and low confidence) to produce an
explainable auto_handle vs. escalate decision with a plain-text justification string.
"""

import os
import sys
import re
from typing import Dict, Any, List

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.taxonomy import Intent

ESCALATE_PRONE_INTENTS = {
    Intent.BILLING_DISPUTE.value,
    Intent.ACCOUNT_ACCESS.value,
}

LEGAL_AND_REGULATORY_KEYWORDS = [
    r"\blawyer\b", r"\battorney\b", r"\bbbb\b", r"\bbetter business bureau\b",
    r"\bchargeback\b", r"\bpolice\b", r"\bsue\b", r"\blawsuit\b", r"\bsmall claims\b",
    r"\bfraud\b", r"\bftc\b", r"\blegal action\b"
]

SAFETY_AND_SEVERE_KEYWORDS = [
    r"\bshattered\b", r"\bbroken glass\b", r"\bexpired\b", r"\binjury\b",
    r"\bhazard\b", r"\bleaked\b", r"\bstolen\b", r"\bhacked\b", r"\bempty box\b",
    r"\bforged\b"
]

HIGH_FRUSTRATION_KEYWORDS = [
    r"\bhung up\b", r"\bsupervisor\b", r"\bmanager\b", r"\bunacceptable\b",
    r"\bworst customer service\b", r"\bdisgusting\b", r"\bscam\b", r"\bpathetic\b"
]

REPEAT_CONTACT_PATTERNS = [
    r"\b(?:3rd|4th|5th|third|fourth|fifth) time\b",
    r"\bcontacted (?:you|support|amazon) \d+ times\b",
    r"\bpromised.*(?:days|hours) ago\b",
    r"\balready (?:called|chatted|messaged)\b",
    r"\bmultiple times\b"
]

def evaluate_escalation_policy(
    text: str,
    intent: str,
    confidence: float = 0.85,
    thread_length: int = 1
) -> Dict[str, Any]:
    """
    Evaluates deterministic signals and outputs 'auto_handle' or 'escalate'
    along with an inspectable human-readable justification citing all fired signals.
    """
    text_lower = text.lower()
    fired_signals: List[str] = []

    if intent in ESCALATE_PRONE_INTENTS:
        fired_signals.append(f"High-risk intent category ('{intent}')")

    matched_legal = [k.replace(r"\b", "") for k in LEGAL_AND_REGULATORY_KEYWORDS if re.search(k, text_lower)]
    if matched_legal:
        fired_signals.append(f"Legal/Regulatory escalation keyword detected ({', '.join(matched_legal)})")

    dollar_matches = re.findall(r"\$\d+(?:\.\d{2})?", text)
    if dollar_matches:
        fired_signals.append(f"Monetary value involved ({', '.join(dollar_matches)})")

    matched_safety = [k.replace(r"\b", "") for k in SAFETY_AND_SEVERE_KEYWORDS if re.search(k, text_lower)]
    if matched_safety:
        fired_signals.append(f"Safety/Severe incident keyword detected ({', '.join(matched_safety)})")

    if thread_length > 1:
        fired_signals.append(f"Multi-turn repeat interaction (thread_length={thread_length})")
    matched_repeat = [p.replace(r"\b", "") for p in REPEAT_CONTACT_PATTERNS if re.search(p, text_lower)]
    if matched_repeat:
        fired_signals.append("Customer indicates prior unresolved contact attempts")

    matched_frustration = [k.replace(r"\b", "") for k in HIGH_FRUSTRATION_KEYWORDS if re.search(k, text_lower)]
    if matched_frustration:
        fired_signals.append(f"High-frustration / supervisor demand detected ({', '.join(matched_frustration)})")

    if confidence < 0.60:
        fired_signals.append(f"Low intent classification confidence ({confidence:.2f} < 0.60)")

    if fired_signals:
        decision = "escalate"
        reason = "Escalated due to: " + "; ".join(fired_signals)
    else:
        decision = "auto_handle"
        reason = "Auto-handled: Procedural/informational request with zero risk signals detected"

    return {
        "decision": decision,
        "reason": reason,
        "fired_signals": fired_signals,
        "signal_count": len(fired_signals)
    }
