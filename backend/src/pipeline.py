"""
Milestone 4: End-to-End Support Agent Pipeline for AmazonHelp.
Unified entry point:
handle_message(text) -> {intent, confidence, reply, decision, reason, retrieved_context}
"""

import os
import sys
import argparse
import logging
from typing import Dict, Any, Optional

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.classify_intent import LLMIntentClassifier
from src.retrieval import HistoricalRetrievalIndex
from src.draft_reply import ReplyDrafter
from src.escalation_policy import evaluate_escalation_policy
from src.llm_client import LLMClient
from src.data_prep import clean_tweet_text

logger = logging.getLogger(__name__)

class SupportAgentPipeline:
    def __init__(
        self,
        retrieval_index: Optional[HistoricalRetrievalIndex] = None,
        llm_client: Optional[LLMClient] = None
    ):
        self.llm_client = llm_client or LLMClient()
        self.retrieval_index = retrieval_index or HistoricalRetrievalIndex()
        self.intent_classifier = LLMIntentClassifier(llm_client=self.llm_client)
        self.reply_drafter = ReplyDrafter(llm_client=self.llm_client)

    def handle_message(self, text: str, thread_length: int = 1) -> Dict[str, Any]:
        """
        Executes end-to-end processing of an incoming customer message:
        1. Clean text
        2. Classify intent + confidence
        3. Retrieve grounded historical examples
        4. Draft grounded reply with hallucination guards
        5. Evaluate deterministic escalation policy
        """
        cleaned_text, removed_mentions = clean_tweet_text(text)
        if not cleaned_text:
            cleaned_text = text.strip()

        # Step 1: Classify Intent
        classification = self.intent_classifier.classify(cleaned_text)
        intent = classification["intent"]
        confidence = classification["confidence"]

        # Step 2: Retrieve Grounding Context
        retrieved_pairs = self.retrieval_index.retrieve(cleaned_text, intent=intent, k=3)
        context_str = self.retrieval_index.format_for_prompt(retrieved_pairs)

        # Step 3: Draft Grounded Reply
        reply_result = self.reply_drafter.draft_reply(cleaned_text, intent, context_str)
        drafted_reply = reply_result["draft_reply"]

        # Step 4: Deterministic Escalation Policy
        escalation_result = evaluate_escalation_policy(
            text=cleaned_text,
            intent=intent,
            confidence=confidence,
            thread_length=thread_length
        )

        return {
            "intent": intent,
            "confidence": confidence,
            "reply": drafted_reply,
            "decision": escalation_result["decision"],
            "reason": escalation_result["reason"],
            "retrieved_context": context_str,
            "hallucination_detected": reply_result["hallucination_detected"],
            "hallucination_flags": reply_result["hallucination_flags"],
            "model_type": "full_system"
        }

def main():
    parser = argparse.ArgumentParser(description="AmazonHelp AI Support Agent Pipeline")
    parser.add_argument("--message", type=str, help="Single customer message to process")
    parser.add_argument("--interactive", action="store_true", help="Launch interactive CLI prompt")
    args = parser.parse_args()

    agent = SupportAgentPipeline()

    if args.message:
        res = agent.handle_message(args.message)
        print("\n--- Agent Result ---")
        print(f"Customer Message : {args.message}")
        print(f"Intent           : {res['intent']} (Confidence: {res['confidence']:.2f})")
        print(f"Action Decision  : {res['decision'].upper()}")
        print(f"Decision Reason  : {res['reason']}")
        print(f"Drafted Reply    : {res['reply']}")
        print(f"Hallucinations   : {res['hallucination_detected']}")
    elif args.interactive:
        print("\n=== AmazonHelp AI Agent Interactive Terminal (type 'exit' to quit) ===")
        while True:
            try:
                user_input = input("\nCustomer: ").strip()
                if user_input.lower() in ["exit", "quit", "q"]:
                    break
                if not user_input:
                    continue
                res = agent.handle_message(user_input)
                print(f"Intent   : {res['intent']} (conf={res['confidence']:.2f})")
                print(f"Decision : {res['decision'].upper()} -> {res['reason']}")
                print(f"Reply    : {res['reply']}")
            except (KeyboardInterrupt, EOFError):
                break
    else:
        sample = "Where is my package? The tracking has been stuck on carrier facility for 3 days!"
        res = agent.handle_message(sample)
        print(f"Sample test: {sample}\nOutput: {res}")

if __name__ == "__main__":
    main()
