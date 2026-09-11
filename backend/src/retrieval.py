"""
Milestone 4: Retrieval Index for Grounded Historical AmazonHelp Resolutions.
Embeds historical customer queries and computes cosine similarity to retrieve
top-k historical (customer_msg, brand_reply) pairs for few-shot grounding.
"""

import os
import sys
import logging
from typing import List, Dict, Optional, Any
import numpy as np
import pandas as pd

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

logger = logging.getLogger(__name__)

class HistoricalRetrievalIndex:
    def __init__(
        self,
        threads_path: str = "data/processed/amazonhelp_threads.parquet",
        embeddings_cache: str = "data/processed/retrieval_embeddings.npy",
        model_name: str = "all-MiniLM-L6-v2"
    ):
        self.threads_path = self._resolve_path(threads_path)
        self.embeddings_cache = self._resolve_path(embeddings_cache)
        self.model_name = model_name
        self.model = None
        self.df = None
        self.embeddings = None

        self._initialize_index()

    def _resolve_path(self, rel_path: str) -> str:
        candidates = [
            rel_path,
            os.path.join(PROJECT_ROOT, rel_path),
            os.path.join(BACKEND_DIR, rel_path)
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return os.path.join(PROJECT_ROOT, rel_path)

    def _initialize_index(self):
        """Loads data and precomputes or loads cached embeddings."""
        if not os.path.exists(self.threads_path):
            logger.warning(f"Threads file {self.threads_path} not found. Retrieval will operate in fallback mode.")
            return

        try:
            from sentence_transformers import SentenceTransformer
            self.df = pd.read_parquet(self.threads_path).reset_index(drop=True)
            self.model = SentenceTransformer(self.model_name)

            if os.path.exists(self.embeddings_cache):
                logger.info(f"Loading cached retrieval embeddings from {self.embeddings_cache}...")
                self.embeddings = np.load(self.embeddings_cache)
            else:
                logger.info(f"Computing embeddings for {len(self.df)} historical threads...")
                msgs = self.df["customer_msg"].fillna("").tolist()
                self.embeddings = self.model.encode(msgs, batch_size=64, show_progress_bar=False, normalize_embeddings=True)
                os.makedirs(os.path.dirname(self.embeddings_cache), exist_ok=True)
                np.save(self.embeddings_cache, self.embeddings)
                logger.info("Embeddings cached successfully.")
        except Exception as e:
            logger.warning(f"Failed to initialize sentence transformer embeddings ({e}). Operating in fallback mode.")
            self.df = None
            self.embeddings = None

    def retrieve(self, query: str, intent: Optional[str] = None, k: int = 3) -> List[Dict[str, Any]]:
        """Retrieves top-k historical (customer_msg, brand_reply) pairs by cosine similarity."""
        if self.embeddings is None or self.df is None or len(self.df) == 0:
            return self._default_fallback_examples(intent, k)

        try:
            query_emb = self.model.encode([query], normalize_embeddings=True)[0]
            scores = np.dot(self.embeddings, query_emb)
            top_indices = np.argsort(scores)[::-1][:k]

            results = []
            for idx in top_indices:
                row = self.df.iloc[idx]
                results.append({
                    "similarity": float(scores[idx]),
                    "customer_msg": row["customer_msg"],
                    "brand_reply": row["brand_reply"],
                    "thread_id": row.get("thread_id", "")
                })
            return results
        except Exception as e:
            logger.warning(f"Error during vector retrieval ({e}). Returning fallback examples.")
            return self._default_fallback_examples(intent, k)

    def format_for_prompt(self, retrieved_examples: List[Dict[str, Any]]) -> str:
        """Formats retrieved examples into a readable context block for prompt injection."""
        if not retrieved_examples:
            return "No historical resolution context available."

        formatted_blocks = []
        for i, ex in enumerate(retrieved_examples, 1):
            formatted_blocks.append(
                f"[Example {i}] (Similarity: {ex.get('similarity', 0.0):.2f})\n"
                f"Customer: \"{ex['customer_msg']}\"\n"
                f"AmazonHelp Verified Resolution: \"{ex['brand_reply']}\""
            )
        return "\n\n".join(formatted_blocks)

    def _default_fallback_examples(self, intent: Optional[str], k: int) -> List[Dict[str, Any]]:
        curated_defaults = [
            {
                "similarity": 0.90,
                "customer_msg": "Where is my package? The tracking has not updated in two days.",
                "brand_reply": "We'd like to check this for you! Please reach out to us via direct message with your 17-digit order number so we can investigate. ^AH",
                "thread_id": "historical_sample_1"
            },
            {
                "similarity": 0.88,
                "customer_msg": "I returned my order last week but have not received my refund.",
                "brand_reply": "Refunds usually take 3-5 business days once processed by the carrier. Please DM us your account email so we can verify the return status. ^AH",
                "thread_id": "historical_sample_2"
            },
            {
                "similarity": 0.85,
                "customer_msg": "I was double charged on my card for Prime renewal.",
                "brand_reply": "We're sorry to hear about the billing discrepancy! Please send us a direct message with your account details so we can review the charges with you. ^AH",
                "thread_id": "historical_sample_3"
            }
        ]
        return curated_defaults[:k]
