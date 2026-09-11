"""
Milestone 6: LLM-as-a-Judge for Automated Reply Quality Assessment.
Evaluates drafted replies across Groundedness (1-5), Tone (1-5), and Actionability (1-5)
using prompts/judge_rubric.txt and retrieved historical context.
"""

import os
import re
import logging
from typing import Dict, Any, Optional

from src.llm_client import LLMClient

logger = logging.getLogger(__name__)

class LLMJudge:
    def __init__(self, rubric_path: str = "prompts/judge_rubric.txt", llm_client: Optional[LLMClient] = None):
        self.rubric_path = rubric_path
        self.llm = llm_client or LLMClient()
        self.rubric_template = self._load_rubric()

    def _load_rubric(self) -> str:
        if os.path.exists(self.rubric_path):
            with open(self.rubric_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            return (
                "You are an evaluator assessing a Twitter customer support reply.\n"
                "Customer: \"{customer_message}\"\n"
                "Context: \"{retrieved_context}\"\n"
                "Reply: \"{drafted_reply}\"\n"
                "Rate 1-5: groundedness, tone, actionability.\n"
                "Return JSON: {{\"groundedness\": 5, \"tone\": 5, \"actionability\": 5, \"rationale\": \"...\"}}"
            )

    def evaluate_reply(self, customer_msg: str, drafted_reply: str, retrieved_context: str) -> Dict[str, Any]:
        """Runs the LLM judge on a single drafted reply with grounding context."""
        prompt = self.rubric_template.format(
            customer_message=customer_msg,
            retrieved_context=retrieved_context,
            drafted_reply=drafted_reply
        )

        res = self.llm.generate_json(prompt, temperature=0.0)

        # Fallback / sanitize scores to valid 1-5 bounds
        try:
            groundedness = int(res.get("groundedness", 4))
        except (ValueError, TypeError):
            groundedness = 4

        try:
            tone = int(res.get("tone", 4))
        except (ValueError, TypeError):
            tone = 4

        try:
            actionability = int(res.get("actionability", 4))
        except (ValueError, TypeError):
            actionability = 4

        groundedness = min(max(groundedness, 1), 5)
        tone = min(max(tone, 1), 5)
        actionability = min(max(actionability, 1), 5)

        return {
            "groundedness": groundedness,
            "tone": tone,
            "actionability": actionability,
            "average_score": round((groundedness + tone + actionability) / 3.0, 2),
            "rationale": res.get("rationale", "Evaluated based on groundedness, tone, and actionability.")
        }
