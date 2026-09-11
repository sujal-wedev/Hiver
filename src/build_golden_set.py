"""
Golden Set Builder: Stratified sampling of REAL tweets from processed data.
Produces a CSV with real tweet IDs, real text, pre-populated heuristic intent guesses,
and blank columns for human annotation.

The human annotator must then hand-label each row.
"""

import os
import re
import sys
import io
import pandas as pd
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

np.random.seed(42)

# --- Configuration ---
THREADS_PATH = "data/processed/amazonhelp_threads.parquet"
OUTPUT_PATH = "golden_set/golden_eval_v1.csv"
TARGET_TOTAL = 200  # Aim for 200 (within 150-250 range)
MIN_PER_INTENT = 15  # Minimum stratified samples per intent

# Keyword heuristics for stratified pre-bucketing (NOT the labels — just sampling pools)
INTENT_KEYWORDS = {
    "order_status_delivery": [r"deliver", r"package", r"tracking", r"shipped", r"carrier", r"where is", r"parcel", r"arrived", r"transit", r"late"],
    "refund_return": [r"refund", r"return", r"money back", r"send back", r"drop off", r"label"],
    "billing_dispute": [r"charge", r"billed", r"\$\d+", r"double charged", r"unauthorized", r"credit card", r"overcharged", r"payment"],
    "account_access": [r"password", r"login", r"log in", r"locked", r"sign in", r"otp", r"2fa", r"hacked", r"account.*access"],
    "product_issue": [r"broken", r"damaged", r"wrong item", r"defective", r"scratched", r"missing.*item", r"wrong.*size", r"doa"],
    "app_website_bug": [r"app.*crash", r"website.*error", r"checkout.*fail", r"cart.*error", r"page.*load", r"glitch", r"bug"],
    "cancellation": [r"cancel", r"cancellation", r"stop.*order", r"cancel.*prime", r"unsubscribe"],
    "general_complaint_vent": [r"worst", r"terrible", r"scam", r"pathetic", r"horrible", r"disgusting", r"hate.*amazon", r"worst.*service"],
}

def detect_heuristic_intent(text):
    """Pre-bucket a tweet by keyword for stratified sampling (NOT ground truth)."""
    text_lower = text.lower()
    for intent, patterns in INTENT_KEYWORDS.items():
        for p in patterns:
            if re.search(p, text_lower):
                return intent
    return "other_unclear"


def main():
    print("Loading processed threads...")
    df = pd.read_parquet(THREADS_PATH)
    print(f"Total threads available: {len(df)}")

    # Filter to English-ish (basic heuristic: contains common English words)
    english_words = {"the", "is", "my", "i", "to", "you", "it", "have", "not", "can", "help", "why"}
    def is_likely_english(text):
        words = set(text.lower().split())
        return len(words & english_words) >= 2

    df_eng = df[df["customer_msg"].apply(is_likely_english)].copy()
    print(f"Likely English tweets: {len(df_eng)}")

    # Pre-bucket all tweets
    df_eng["heuristic_intent"] = df_eng["customer_msg"].apply(detect_heuristic_intent)
    print("\nHeuristic pre-bucketing distribution:")
    print(df_eng["heuristic_intent"].value_counts())

    # --- Stage 1: Stratified sampling (minimum per intent) ---
    stratified_samples = []
    for intent in list(INTENT_KEYWORDS.keys()) + ["other_unclear"]:
        pool = df_eng[df_eng["heuristic_intent"] == intent]
        n_sample = min(len(pool), MIN_PER_INTENT + 5)  # Take a few extra per category
        if n_sample > 0:
            sampled = pool.sample(n=n_sample, random_state=42)
            stratified_samples.append(sampled)
            print(f"  Stratified {intent}: sampled {n_sample} from pool of {len(pool)}")

    df_stratified = pd.concat(stratified_samples, ignore_index=True)
    used_ids = set(df_stratified["customer_tweet_id"])
    print(f"\nTotal stratified samples: {len(df_stratified)}")

    # --- Stage 2: Random backfill to reach target ---
    remaining_needed = TARGET_TOTAL - len(df_stratified)
    if remaining_needed > 0:
        remaining_pool = df_eng[~df_eng["customer_tweet_id"].isin(used_ids)]
        backfill = remaining_pool.sample(n=min(remaining_needed, len(remaining_pool)), random_state=42)
        df_golden = pd.concat([df_stratified, backfill], ignore_index=True)
        print(f"Random backfill: {len(backfill)} rows")
    else:
        df_golden = df_stratified.head(TARGET_TOTAL)

    # Shuffle final set
    df_golden = df_golden.sample(frac=1, random_state=42).reset_index(drop=True)
    print(f"\nFinal golden set size: {len(df_golden)}")

    # --- Also pull a few non-English / very short / ambiguous tweets for other_unclear ---
    non_eng_pool = df[~df["customer_tweet_id"].isin(set(df_golden["customer_tweet_id"]))]
    non_eng_pool = non_eng_pool[~non_eng_pool["customer_msg"].apply(is_likely_english)]
    if len(non_eng_pool) > 0:
        non_eng_sample = non_eng_pool.sample(n=min(8, len(non_eng_pool)), random_state=42)
        non_eng_sample["heuristic_intent"] = "other_unclear"
        df_golden = pd.concat([df_golden, non_eng_sample], ignore_index=True)
        print(f"Added {len(non_eng_sample)} non-English/ambiguous tweets for other_unclear coverage")

    print(f"Final golden set size (with non-English): {len(df_golden)}")

    # --- Build output CSV with columns for human annotation ---
    output_rows = []
    for _, row in df_golden.iterrows():
        output_rows.append({
            "tweet_id": row["customer_tweet_id"],
            "text": row["customer_msg"],
            "brand_reply": row.get("brand_reply", ""),
            "heuristic_intent_guess": row["heuristic_intent"],
            "primary_intent": row["heuristic_intent"],  # Pre-fill with heuristic, human must verify
            "secondary_intent": "",
            "ideal_action": "",  # Human must fill
            "escalation_reason": "",
            "ambiguity_flag": False,
            "notes": ""
        })

    df_out = pd.DataFrame(output_rows)

    # Now apply the escalation heuristic to pre-populate ideal_action
    for i, row in df_out.iterrows():
        text_lower = row["text"].lower()
        intent = row["primary_intent"]

        # Escalate-prone intents
        should_escalate = intent in ("billing_dispute", "account_access")

        # Legal/safety keywords
        legal = any(k in text_lower for k in ["lawyer", "bbb", "chargeback", "legal", "court", "police", "fraud", "sue"])
        safety = any(k in text_lower for k in ["shattered", "broken glass", "expired", "injury", "hazard", "stolen", "hacked", "empty box"])
        money = bool(re.search(r"\$\d+", row["text"]))
        repeat = any(k in text_lower for k in ["3rd time", "fourth time", "multiple times", "already called", "promised"])
        frustration = any(k in text_lower for k in ["supervisor", "manager", "unacceptable", "worst customer service", "scam"])

        if should_escalate or legal or safety or money or repeat or frustration:
            df_out.at[i, "ideal_action"] = "escalate"
            reasons = []
            if should_escalate: reasons.append(f"high_risk_intent_{intent}")
            if legal: reasons.append("legal_keyword")
            if safety: reasons.append("safety_keyword")
            if money: reasons.append("monetary_value")
            if repeat: reasons.append("repeat_contact")
            if frustration: reasons.append("high_frustration")
            df_out.at[i, "escalation_reason"] = ",".join(reasons)
        else:
            df_out.at[i, "ideal_action"] = "auto_handle"

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df_out.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print(f"\nSaved golden set to {OUTPUT_PATH}")
    print(f"Rows: {len(df_out)}")

    # Print distribution summary
    print("\n--- Golden Set Distribution ---")
    print("\nIntent distribution:")
    print(df_out["primary_intent"].value_counts())
    print("\nIdeal action distribution:")
    print(df_out["ideal_action"].value_counts())
    print("\nHeuristic pre-fill note: primary_intent and ideal_action are PRE-FILLED with")
    print("heuristic guesses. The human annotator MUST review and correct each row.")


if __name__ == "__main__":
    main()
