"""
Milestone 3: Stratified Sampling & Labeling Tool for Golden Evaluation Set.
Allows stratified sampling across intent candidates with keyword pre-bucketing,
random natural-frequency backfilling, interactive CLI labeling, and self-consistency kappa checks.
"""

import os
import re
import argparse
import logging
import pandas as pd
import numpy as np
from sklearn.metrics import cohen_kappa_score
from src.taxonomy import Intent, ALL_INTENTS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

INTENT_KEYWORD_HEURISTICS = {
    Intent.ORDER_STATUS_DELIVERY.value: [
        r"where.*(?:package|order|delivery|item)", r"tracking", r"carrier", r"delayed",
        r"delivered but", r"still haven't received", r"late delivery", r"eta"
    ],
    Intent.REFUND_RETURN.value: [
        r"refund", r"return", r"send.*back", r"drop.*off", r"return label",
        r"return window", r"money back"
    ],
    Intent.BILLING_DISPUTE.value: [
        r"double.*charge", r"charged", r"bank", r"credit card", r"\$\d+",
        r"unauthorized", r"prime.*fee", r"overcharged", r"billing"
    ],
    Intent.ACCOUNT_ACCESS.value: [
        r"locked out", r"password", r"otp", r"2fa", r"login", r"log in",
        r"sign in", r"hacked", r"suspended", r"verification code"
    ],
    Intent.PRODUCT_ISSUE.value: [
        r"damaged", r"broken", r"wrong item", r"defective", r"scratched",
        r"missing part", r"shattered", r"expired"
    ],
    Intent.APP_WEBSITE_BUG.value: [
        r"website", r"app crash", r"cart error", r"checkout error", r"glitch",
        r"server error", r"bug", r"page.*load"
    ],
    Intent.CANCELLATION.value: [
        r"cancel.*order", r"cancellation", r"cancel.*prime", r"stop.*order",
        r"cancel.*membership"
    ],
    Intent.GENERAL_COMPLAINT_VENT.value: [
        r"worst", r"terrible", r"pathetic", r"scam", r"unacceptable",
        r"ridiculous", r"horrible customer service", r"disgusted"
    ]
}

def stratify_and_sample(
    threads_path: str = "data/processed/amazonhelp_threads.parquet",
    output_path: str = "golden_set/unlabeled_sample.csv",
    target_per_intent: int = 18,
    random_backfill: int = 60,
    seed: int = 42
):
    """Draws a stratified sample with natural random backfill."""
    df = pd.read_parquet(threads_path)
    np.random.seed(seed)
    selected_indices = set()
    stratified_rows = []

    # Stratified draw using keyword heuristics
    for intent, patterns in INTENT_KEYWORD_HEURISTICS.items():
        combined_pat = "|".join(patterns)
        matches = df[df["customer_msg"].str.contains(combined_pat, case=False, regex=True, na=False)]
        available = matches[~matches.index.isin(selected_indices)]

        n_draw = min(len(available), target_per_intent)
        if n_draw > 0:
            sample = available.sample(n=n_draw, random_state=seed)
            for idx, row in sample.iterrows():
                selected_indices.add(idx)
                stratified_rows.append({
                    "tweet_id": row["customer_tweet_id"],
                    "text": row["customer_msg"],
                    "sample_source": f"stratified_{intent}"
                })

    # Natural frequency backfill
    remaining = df[~df.index.isin(selected_indices)]
    backfill_sample = remaining.sample(n=min(len(remaining), random_backfill), random_state=seed)
    for idx, row in backfill_sample.iterrows():
        selected_indices.add(idx)
        stratified_rows.append({
            "tweet_id": row["customer_tweet_id"],
            "text": row["customer_msg"],
            "sample_source": "random_backfill"
        })

    sampled_df = pd.DataFrame(stratified_rows)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    sampled_df.to_csv(output_path, index=False)
    logger.info(f"Sampled {len(sampled_df)} tweets ({len(stratified_rows) - len(backfill_sample)} stratified, {len(backfill_sample)} random) saved to {output_path}")

def compute_self_consistency(original_csv: str, relabeled_csv: str):
    """Computes Cohen's kappa between initial labeling and blind re-labeling."""
    df_orig = pd.read_csv(original_csv)
    df_relab = pd.read_csv(relabeled_csv)

    merged = pd.merge(df_orig, df_relab, on="tweet_id", suffixes=("_orig", "_relab"))
    kappa_intent = cohen_kappa_score(merged["primary_intent_orig"], merged["primary_intent_relab"])
    kappa_action = cohen_kappa_score(merged["ideal_action_orig"], merged["ideal_action_relab"])
    exact_intent = (merged["primary_intent_orig"] == merged["primary_intent_relab"]).mean()
    exact_action = (merged["ideal_action_orig"] == merged["ideal_action_relab"]).mean()

    print(f"\n--- Inter-Annotator / Self-Consistency Check (N={len(merged)}) ---")
    print(f"Primary Intent Cohen's Kappa : {kappa_intent:.3f} (Exact Agreement: {exact_intent:.1%})")
    print(f"Ideal Action Cohen's Kappa   : {kappa_action:.3f} (Exact Agreement: {exact_action:.1%})")
    return {
        "n_samples": len(merged),
        "kappa_intent": round(float(kappa_intent), 3),
        "exact_intent": round(float(exact_intent), 3),
        "kappa_action": round(float(kappa_action), 3),
        "exact_action": round(float(exact_action), 3),
    }

def main():
    parser = argparse.ArgumentParser(description="Stratified sampling and labeling tools")
    parser.add_argument("--sample", action="store_true", help="Run stratified sampling")
    parser.add_argument("--threads", type=str, default="data/processed/amazonhelp_threads.parquet")
    parser.add_argument("--out", type=str, default="golden_set/unlabeled_sample.csv")
    parser.add_argument("--check-kappa", action="store_true", help="Compute self-consistency Cohen's Kappa")
    parser.add_argument("--orig", type=str, default="golden_set/golden_eval_v1.csv")
    parser.add_argument("--relab", type=str, default="golden_set/golden_eval_relabel_10pct.csv")
    args = parser.parse_args()

    if args.sample:
        stratify_and_sample(args.threads, args.out)
    elif args.check_kappa:
        compute_self_consistency(args.orig, args.relab)

if __name__ == "__main__":
    main()
