"""
Milestone 4: Grounded Reply Drafter with Hallucination Guardrails.
Uses prompts/reply_draft.txt and retrieved few-shot examples to draft
concise, brand-appropriate, grounded replies for AmazonHelp.
"""

import os
import re
import logging
from typing import Dict, Any, List, Optional

from src.llm_client import LLMClient

logger = logging.getLogger(__name__)

class ReplyDrafter:
    def __init__(self, prompt_template_path: str = "prompts/reply_draft.txt", llm_client: Optional[LLMClient] = None):
        self.prompt_template_path = prompt_template_path
        self.llm = llm_client or LLMClient()
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        if os.path.exists(self.prompt_template_path):
            with open(self.prompt_template_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            return (
                "You are an official Amazon customer support representative on Twitter (@AmazonHelp).\n"
                "Customer Message: \"{customer_message}\"\n"
                "Intent: \"{intent}\"\n"
                "Grounding Context: {retrieved_context}\n"
                "Draft a professional grounded Twitter reply:"
            )

    def check_hallucinations(self, draft_reply: str, customer_msg: str, retrieved_context: str) -> Dict[str, Any]:
        """
        Inspects drafted reply for fabricated entities not present in input or grounding context:
        - Invented Amazon Order IDs (format: 11X-XXXXXXX-XXXXXXX)
        - Invented Carrier Tracking IDs (format: TBAXXXXXXXXXXXX)
        - Fabricated dollar amounts ($XX.XX)
        """
        known_text = f"{customer_msg} {retrieved_context}"
        flagged_hallucinations = []

        # Check for order numbers
        reply_orders = set(re.findall(r"\b\d{3}-\d{7}-\d{7}\b", draft_reply))
        known_orders = set(re.findall(r"\b\d{3}-\d{7}-\d{7}\b", known_text))
        fabricated_orders = reply_orders - known_orders
        if fabricated_orders:
            flagged_hallucinations.append(f"Fabricated order ID(s): {', '.join(fabricated_orders)}")

        # Check for fabricated tracking numbers
        reply_trackings = set(re.findall(r"\bTBA\d{9,13}\b", draft_reply))
        known_trackings = set(re.findall(r"\bTBA\d{9,13}\b", known_text))
        fabricated_trackings = reply_trackings - known_trackings
        if fabricated_trackings:
            flagged_hallucinations.append(f"Fabricated tracking ID(s): {', '.join(fabricated_trackings)}")

        # Check for fabricated dollar figures
        reply_dollars = set(re.findall(r"\$\d+(?:\.\d{2})?", draft_reply))
        known_dollars = set(re.findall(r"\$\d+(?:\.\d{2})?", known_text))
        fabricated_dollars = reply_dollars - known_dollars
        if fabricated_dollars:
            flagged_hallucinations.append(f"Fabricated dollar amount(s): {', '.join(fabricated_dollars)}")

        has_hallucination = len(flagged_hallucinations) > 0
        sanitized_reply = draft_reply

        if has_hallucination:
            # Sanitize fabricated entities
            for order in fabricated_orders:
                sanitized_reply = sanitized_reply.replace(order, "your order details")
            for trk in fabricated_trackings:
                sanitized_reply = sanitized_reply.replace(trk, "your tracking number")
            for dol in fabricated_dollars:
                sanitized_reply = sanitized_reply.replace(dol, "the disputed amount")

        return {
            "has_hallucination": has_hallucination,
            "flags": flagged_hallucinations,
            "sanitized_reply": sanitized_reply
        }

    def draft_reply(self, customer_msg: str, intent: str, retrieved_context_str: str) -> Dict[str, Any]:
        prompt = self.prompt_template.format(
            customer_message=customer_msg,
            intent=intent,
            retrieved_context=retrieved_context_str
        )

        raw_reply = self.llm.generate(prompt, temperature=0.1, max_tokens=140).strip()
        # Clean enclosing quotes if any
        if raw_reply.startswith('"') and raw_reply.endswith('"'):
            raw_reply = raw_reply[1:-1].strip()

        # Enforce Twitter signature if missing
        if not any(raw_reply.endswith(sig) for sig in ["^AH", "^Amazon", "^Help", "^Helper"]):
            raw_reply = f"{raw_reply} ^AH"

        # Hallucination check
        guard_result = self.check_hallucinations(raw_reply, customer_msg, retrieved_context_str)

        return {
            "draft_reply": guard_result["sanitized_reply"],
            "raw_reply": raw_reply,
            "hallucination_detected": guard_result["has_hallucination"],
            "hallucination_flags": guard_result["flags"]
        }
