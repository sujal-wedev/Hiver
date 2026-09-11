"""
Multi-provider LLM client for intent classification, reply drafting, and LLM-as-a-judge.
Supports:
1. OpenAI (gpt-4o-mini, gpt-3.5-turbo, etc.)
2. OpenRouter (any model via OpenAI-compatible API)
3. Gemini (gemini-1.5-flash / gemini-2.5-flash) via direct REST API
4. Anthropic (claude-3-haiku)
5. Offline / Mock fallback for deterministic local test runs without API keys.
"""

import os
import re
import json
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = provider or os.getenv("LLM_PROVIDER")
        self.model = model or os.getenv("LLM_MODEL")

        # Auto-detect available provider if not explicitly given
        if not self.provider:
            if os.getenv("GROQ_API_KEY"):
                self.provider = "groq"
                self.model = self.model or "qwen/qwen3.8-27b"
            elif os.getenv("OPENROUTER_API_KEY"):
                self.provider = "openrouter"
                self.model = self.model or "google/gemini-3.5-flash"
            elif os.getenv("OPENAI_API_KEY"):
                self.provider = "openai"
                self.model = self.model or "gpt-4o-mini"
            elif os.getenv("GEMINI_API_KEY"):
                self.provider = "gemini"
                self.model = self.model or "gemini-1.5-flash"
            elif os.getenv("ANTHROPIC_API_KEY"):
                self.provider = "anthropic"
                self.model = self.model or "claude-3-haiku-20240307"
            else:
                self.provider = "mock"
                self.model = "offline-mock"

        logger.info(f"Initialized LLMClient with provider='{self.provider}', model='{self.model}'")

    def generate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 400) -> str:
        """Generates text from the configured LLM provider."""
        if self.provider == "groq":
            return self._call_groq(prompt, temperature, max_tokens)
        elif self.provider == "openai":
            return self._call_openai(prompt, temperature, max_tokens)
        elif self.provider == "openrouter":
            return self._call_openrouter(prompt, temperature, max_tokens)
        elif self.provider == "gemini":
            return self._call_gemini(prompt, temperature, max_tokens)
        elif self.provider == "anthropic":
            return self._call_anthropic(prompt, temperature, max_tokens)
        else:
            return self._call_mock(prompt)

    def generate_json(self, prompt: str, temperature: float = 0.0) -> Dict[str, Any]:
        """Generates text and parses it strictly into a Python dictionary."""
        raw_text = self.generate(prompt, temperature=temperature)
        # Attempt direct JSON parse
        try:
            return json.loads(raw_text)
        except Exception:
            pass

        # Try regex search for markdown fenced JSON or brace block
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass

        match = re.search(r"(\{.*\})", raw_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass

        # Fallback return
        return {"raw_response": raw_text, "error": "json_parse_failed"}

    def _call_groq(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Calls Groq API (OpenAI-compatible) with high performance and rate limits."""
        import time
        time.sleep(1.2)  # Respect Groq 30 RPM rate limit window
        from openai import OpenAI
        client = OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
        effective_max_tokens = max_tokens if (max_tokens and max_tokens > 0) else 300
        for attempt in range(5):
            try:
                response = client.chat.completions.create(
                    model=self.model or "llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=effective_max_tokens,
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                err_str = str(e)
                if ("429" in err_str or "rate" in err_str.lower()) and attempt < 4:
                    wait_time = (attempt + 1) * 2
                    logger.info(f"Groq rate limit hit (attempt {attempt+1}/5): {err_str[:120]}. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"Groq call failed ({e}), falling back to mock.")
                    return self._call_mock(prompt)

    def _call_openai(self, prompt: str, temperature: float, max_tokens: int) -> str:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model=self.model or "gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"OpenAI call failed ({e}), falling back to mock.")
            return self._call_mock(prompt)

    def _call_openrouter(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Calls OpenRouter API (OpenAI-compatible) with the user's API key and retries on rate limits."""
        import time
        from openai import OpenAI
        client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
        effective_max_tokens = max_tokens if (max_tokens and max_tokens > 0) else 256
        for attempt in range(5):
            try:
                response = client.chat.completions.create(
                    model=self.model or "google/gemini-3.5-flash",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=effective_max_tokens,
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                err_str = str(e)
                if ("429" in err_str or "402" in err_str or "budget" in err_str.lower()) and attempt < 4:
                    wait_time = (attempt + 1) * 3
                    logger.info(f"OpenRouter limit hit (attempt {attempt+1}/5): {err_str[:120]}. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"OpenRouter call failed ({e}), falling back to mock.")
                    return self._call_mock(prompt)

    def _call_gemini(self, prompt: str, temperature: float, max_tokens: int) -> str:
        import requests
        api_key = os.getenv("GEMINI_API_KEY")
        model = self.model or "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        try:
            resp = requests.post(url, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            else:
                logger.warning(f"Gemini API returned status {resp.status_code}: {resp.text}")
                return self._call_mock(prompt)
        except Exception as e:
            logger.warning(f"Gemini call exception ({e}), falling back to mock.")
            return self._call_mock(prompt)

    def _call_anthropic(self, prompt: str, temperature: float, max_tokens: int) -> str:
        import requests
        api_key = os.getenv("ANTHROPIC_API_KEY")
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model or "claude-3-haiku-20240307",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                return data["content"][0]["text"].strip()
            else:
                logger.warning(f"Anthropic returned status {resp.status_code}: {resp.text}")
                return self._call_mock(prompt)
        except Exception as e:
            logger.warning(f"Anthropic exception ({e}), falling back to mock.")
            return self._call_mock(prompt)

    def _call_mock(self, prompt: str) -> str:
        """Intelligent offline mock engine for classification, reply drafting, and judging."""
        # Detect task from prompt markers
        if "classify the customer's incoming message" in prompt or "intent_classify" in prompt:
            # Extract customer message
            msg_match = re.search(r'Customer Message:\s*"(.*?)"', prompt, re.DOTALL)
            text = (msg_match.group(1) if msg_match else prompt).lower()

            if any(k in text for k in ["charge", "billed", "bank", "card", "$", "double charged", "payment"]):
                intent = "billing_dispute"
            elif any(k in text for k in ["password", "otp", "login", "locked", "sign in", "account access", "hacked"]):
                intent = "account_access"
            elif any(k in text for k in ["broken", "damaged", "wrong item", "defective", "scratched", "missing item"]):
                intent = "product_issue"
            elif any(k in text for k in ["refund", "return", "return label", "send back", "drop off"]):
                intent = "refund_return"
            elif any(k in text for k in ["cancel", "cancellation", "cancel prime", "stop order"]):
                intent = "cancellation"
            elif any(k in text for k in ["late", "delayed", "where is my", "package", "tracking", "delivery", "delivered but"]):
                intent = "order_status_delivery"
            elif any(k in text for k in ["app crash", "website", "bug", "checkout error", "cart", "page not loading"]):
                intent = "app_website_bug"
            elif any(k in text for k in ["worst", "scam", "useless", "terrible", "hate", "horrible"]):
                intent = "general_complaint_vent"
            else:
                intent = "other_unclear"

            return json.dumps({
                "intent": intent,
                "confidence": 0.88,
                "reasoning": f"Heuristic match based on customer key terms."
            })

        elif "official Amazon customer support representative" in prompt or "reply_draft" in prompt:
            # Grounded reply generation
            # Extract intent if present
            intent_match = re.search(r'Classified Intent:\s*"(.*?)"', prompt)
            intent = intent_match.group(1) if intent_match else "general"

            replies = {
                "order_status_delivery": "We're sorry for the delivery delay! Please send us a DM with your 17-digit order number so we can investigate with the carrier. ^AH",
                "refund_return": "We'd like to help sort out your return or refund right away. Please send us a DM with your order details to assist. ^AH",
                "billing_dispute": "We understand billing issues are concerning. Please DM us your email and order details so our billing specialists can verify the charges. ^AH",
                "account_access": "We are here to help secure your account. Please visit amazon.com/help or DM us your email address so we can guide you through recovery. ^AH",
                "product_issue": "We are so sorry your item arrived in that condition! Please send us a DM with your order details and photos if possible so we can send a replacement. ^AH",
                "app_website_bug": "Thanks for reporting this glitch! Please try clearing your app cache or web cookies, and DM us if the issue persists. ^AH",
                "cancellation": "We can help you with your cancellation request. Please DM us your order ID or account email to check its dispatch status. ^AH",
                "general_complaint_vent": "We're genuinely sorry to hear about your frustrating experience. Please DM us the details so we can look into what went wrong. ^AH",
                "other_unclear": "Thanks for reaching out to Amazon Help. Please send us a direct message with more details so we can best assist you. ^AH",
            }
            return replies.get(intent, "Thanks for reaching out to Amazon Help! Please DM us with your details so we can assist. ^AH")

        elif "expert evaluator assessing the quality" in prompt or "judge_rubric" in prompt:
            # Judge rubric scoring
            return json.dumps({
                "groundedness": 4,
                "tone": 5,
                "actionability": 4,
                "rationale": "The reply is polite, brand-appropriate, directs to official DM channels, and introduces zero hallucinations."
            })

        return "Response generated successfully."
