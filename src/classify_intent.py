"""
Milestone 4: Intent Classification Modules.
Implements:
1. LLMIntentClassifier: Zero/few-shot LLM classifier using prompts/intent_classify.txt
2. ClassicalIntentClassifier: TF-IDF + Logistic Regression benchmark classifier
"""

import os
import re
import json
import logging
from typing import Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from src.taxonomy import Intent, ALL_INTENTS, get_taxonomy_prompt_string
from src.llm_client import LLMClient

logger = logging.getLogger(__name__)

class LLMIntentClassifier:
    def __init__(self, prompt_template_path: str = "prompts/intent_classify.txt", llm_client: Optional[LLMClient] = None):
        self.prompt_template_path = prompt_template_path
        self.llm = llm_client or LLMClient()
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        if os.path.exists(self.prompt_template_path):
            with open(self.prompt_template_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            return (
                "You are a customer-support triage agent for AmazonHelp.\n"
                "Classify the customer message into one of:\n{taxonomy_definitions}\n\n"
                "Message: \"{customer_message}\"\n\n"
                "Return JSON: {{\"intent\": \"...\", \"confidence\": 0.9, \"reasoning\": \"...\"}}"
            )

    def classify(self, message: str) -> Dict[str, Any]:
        """Classifies a customer message using the LLM prompt template."""
        tax_defs = get_taxonomy_prompt_string()
        prompt = self.prompt_template.format(
            taxonomy_definitions=tax_defs,
            customer_message=message
        )

        result = self.llm.generate_json(prompt, temperature=0.0)
        predicted_intent = result.get("intent", "").strip().lower()

        # Validate against official taxonomy
        if predicted_intent not in ALL_INTENTS:
            # Check for partial or alias match
            matched = False
            for valid_intent in ALL_INTENTS:
                if valid_intent in predicted_intent or predicted_intent in valid_intent:
                    predicted_intent = valid_intent
                    matched = True
                    break
            if not matched:
                predicted_intent = Intent.OTHER_UNCLEAR.value

        confidence = float(result.get("confidence", 0.85))
        reasoning = result.get("reasoning", "Classified based on semantic match with taxonomy.")

        return {
            "intent": predicted_intent,
            "confidence": min(max(confidence, 0.0), 1.0),
            "reasoning": reasoning
        }

class ClassicalIntentClassifier:
    """TF-IDF + Logistic Regression classifier for benchmarking."""
    def __init__(self):
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=2500, stop_words="english")
        self.classifier = LogisticRegression(max_iter=1000, class_weight="balanced")
        self.is_trained = False

    def train(self, texts: list[str], labels: list[str]):
        X = self.vectorizer.fit_transform(texts)
        self.classifier.fit(X, labels)
        self.is_trained = True

    def classify(self, message: str) -> Dict[str, Any]:
        if not self.is_trained:
            return {"intent": Intent.ORDER_STATUS_DELIVERY.value, "confidence": 0.5, "reasoning": "Untrained classical model"}
        X = self.vectorizer.transform([message])
        probs = self.classifier.predict_proba(X)[0]
        best_idx = np.argmax(probs)
        best_intent = self.classifier.classes_[best_idx]
        return {
            "intent": best_intent,
            "confidence": float(probs[best_idx]),
            "reasoning": "Classical TF-IDF Logistic Regression prediction"
        }
