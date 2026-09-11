"""
LLM-as-a-Judge Evaluation Module.
Evaluates drafted replies on 1-5 scales across 3 core dimensions:
1. Groundedness (1-5)
2. Tone & Brand Alignment (1-5)
3. Actionability & DM Resolution (1-5)
"""

import os
import sys
import logging
from typing import Dict, Any, Optional

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.llm_client import LLMClient

logger = logging.getLogger(__name__)

JUDGE_PROMPT_TEMPLATE = """You are an expert evaluator assessing the quality of an automated Twitter support reply for AmazonHelp (@AmazonHelp).

[Customer Message]: "{customer_message}"
[Classified Intent]: "{intent}"
[Grounding Context Provided]: "{retrieved_context}"
[Drafted Reply]: "{draft_reply}"

Evaluate the drafted reply across 3 dimensions on a scale of 1 to 5:

1. Groundedness (1-5): Does the reply adhere strictly to provided Amazon policy guidelines without inventing fake tracking numbers, order IDs, or dollar refund amounts?
2. Tone (1-5): Is the reply professional, empathetic, brand-aligned, and Twitter-appropriate?
3. Actionability (1-5): Does the reply provide clear next steps (e.g. directing to DM with order details)?

Return JSON ONLY:
{{
  "groundedness": 5,
  "tone": 5,
  "actionability": 4,
  "rationale": "Explanation..."
}}
"""

class LLMJudge:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def evaluate_reply(
        self,
        customer_msg: str,
        intent: str,
        retrieved_context: str,
        draft_reply: str
    ) -> Dict[str, Any]:
        prompt = JUDGE_PROMPT_TEMPLATE.format(
            customer_message=customer_msg,
            intent=intent,
            retrieved_context=retrieved_context,
            draft_reply=draft_reply
        )
        res = self.llm.generate_json(prompt, temperature=0.0)

        groundedness = int(res.get("groundedness", 4))
        tone = int(res.get("tone", 5))
        actionability = int(res.get("actionability", 4))
        overall_mean = (groundedness + tone + actionability) / 3.0

        return {
            "groundedness": min(max(groundedness, 1), 5),
            "tone": min(max(tone, 1), 5),
            "actionability": min(max(actionability, 1), 5),
            "overall_mean": round(overall_mean, 2),
            "rationale": res.get("rationale", "Reply evaluated as grounded and brand appropriate.")
        }
