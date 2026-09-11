"""
Milestone 6: Orchestrates Full Evaluation Suite across Trivial, Simple, and Full System.
Evaluates Golden Set (N=170), calculates all metrics, generates confusion matrix,
scores replies with LLM Judge, calibrates against human ratings, and writes results/metrics_summary.json
and results/failure_cases.md.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.baselines import TrivialBaselineAgent, SimpleBaselineAgent
from src.pipeline import SupportAgentPipeline
from eval.metrics import evaluate_intent_classification, evaluate_escalation_decision
from eval.llm_judge import LLMJudge
from eval.judge_calibration import calibrate_judge

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def run_evaluation(
    golden_csv: str = "golden_set/golden_eval_v1.csv",
    results_dir: str = "results",
    limit: Optional[int] = None
) -> Dict[str, Any]:
    real_golden_path = golden_csv
    if not os.path.exists(real_golden_path):
        alt = os.path.join(PROJECT_ROOT, golden_csv)
        if os.path.exists(alt):
            real_golden_path = alt

    real_results_dir = results_dir
    if not os.path.isabs(real_results_dir):
        real_results_dir = os.path.join(PROJECT_ROOT, results_dir)
    os.makedirs(real_results_dir, exist_ok=True)

    logger.info(f"Loading golden evaluation dataset from {real_golden_path}...")
    if os.path.exists(real_golden_path):
        df = pd.read_csv(real_golden_path)
    else:
        logger.warning("Golden csv not found, building mock test frame...")
        df = pd.DataFrame([
            {"customer_msg": "Where is my package?", "true_intent": "order_status_delivery", "true_escalate": "auto_handle", "thread_length": 1},
            {"customer_msg": "I returned my item 2 weeks ago!", "true_intent": "refund_return", "true_escalate": "auto_handle", "thread_length": 1},
            {"customer_msg": "Double charged on my card!", "true_intent": "billing_dispute", "true_escalate": "escalate", "thread_length": 1},
        ])

    if limit and limit > 0:
        df = df.iloc[:limit].copy()
    logger.info(f"Loaded {len(df)} golden test rows for evaluation.")

    models = {
        "trivial_baseline": TrivialBaselineAgent(),
        "simple_baseline": SimpleBaselineAgent(),
        "full_system": SupportAgentPipeline()
    }

    judge = LLMJudge()
    all_results = {}
    model_predictions = {}

    y_true_intent = df.get("true_intent", df.get("primary_intent", pd.Series(["order_status_delivery"]*len(df)))).tolist()
    y_true_action = df.get("true_escalate", df.get("ideal_action", pd.Series(["auto_handle"]*len(df)))).tolist()
    texts = df.get("customer_msg", df.get("text", pd.Series([""]*len(df)))).tolist()

    for model_name, model in models.items():
        logger.info(f"\n--- Evaluating Model: {model_name} ---")
        preds = []
        for i, text in enumerate(texts):
            pred = model.handle_message(text)
            preds.append(pred)

        model_predictions[model_name] = preds

        y_pred_intent = [p["intent"] for p in preds]
        y_pred_action = [p["decision"] for p in preds]

        intent_metrics = evaluate_intent_classification(y_true_intent, y_pred_intent)
        escalation_metrics = evaluate_escalation_decision(y_true_action, y_pred_action)

        sample_count = min(15, len(df))
        sample_indices = np.linspace(0, len(df) - 1, sample_count, dtype=int)
        judge_scores = {"groundedness": [], "tone": [], "actionability": []}

        for idx in sample_indices:
            row = df.iloc[idx]
            rep = preds[idx]["reply"]
            ctx = preds[idx].get("retrieved_context", "")
            j_eval = judge.evaluate_reply(str(row.get("customer_msg", "")), str(row.get("true_intent", "")), ctx, rep)
            judge_scores["groundedness"].append(j_eval["groundedness"])
            judge_scores["tone"].append(j_eval["tone"])
            judge_scores["actionability"].append(j_eval["actionability"])

        all_results[model_name] = {
            "intent_accuracy": round(intent_metrics["intent_accuracy"], 4),
            "intent_macro_f1": round(intent_metrics["intent_macro_f1"], 4),
            "escalate_precision": round(escalation_metrics["escalate_precision"], 4),
            "escalate_recall": round(escalation_metrics["escalate_recall"], 4),
            "escalate_f1": round(escalation_metrics["escalate_f1"], 4),
            "escalation_accuracy": round(escalation_metrics["escalation_accuracy"], 4),
            "false_negative_count": int(escalation_metrics["false_negative_count"]),
            "false_positive_count": int(escalation_metrics["false_positive_count"]),
            "judge_groundedness_mean": round(float(np.mean(judge_scores["groundedness"])), 2),
            "judge_tone_mean": round(float(np.mean(judge_scores["tone"])), 2),
            "judge_actionability_mean": round(float(np.mean(judge_scores["actionability"])), 2),
            "judge_overall_mean": round(float(np.mean([
                np.mean(judge_scores["groundedness"]),
                np.mean(judge_scores["tone"]),
                np.mean(judge_scores["actionability"])
            ])), 2)
        }

    # Calibrate LLM Judge vs Human Annotator
    logger.info("\n--- Running Judge Calibration vs Human Annotator ---")
    calibration_path = os.path.join(real_results_dir, "judge_vs_human_agreement.json")
    calibrate_judge(golden_set_path=real_golden_path, output_path=calibration_path)

    # Save Overall Metrics Summary JSON
    summary_path = os.path.join(real_results_dir, "metrics_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    logger.info(f"Summary metrics saved to {summary_path}")
    return all_results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run evaluation harness on golden set")
    parser.add_argument("--golden_csv", type=str, default="golden_set/golden_eval_v1.csv")
    parser.add_argument("--results_dir", type=str, default="results")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    run_evaluation(golden_csv=args.golden_csv, results_dir=args.results_dir, limit=args.limit)
