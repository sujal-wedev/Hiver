"""
Milestone 6: Orchestrates Full Evaluation Suite across Trivial, Simple, and Full System.
Evaluates Golden Set (N=170), calculates all metrics, generates confusion matrix,
scores replies with LLM Judge, calibrates against human ratings, and writes results/metrics_summary.json
and results/failure_cases.md.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from src.baselines import TrivialBaseline, SimpleBaseline
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
    os.makedirs(results_dir, exist_ok=True)
    logger.info(f"Loading golden evaluation dataset from {golden_csv}...")
    df = pd.read_csv(golden_csv)
    if limit and limit > 0:
        df = df.iloc[:limit].copy()
    logger.info(f"Loaded {len(df)} golden test rows for evaluation.")

    models = {
        "trivial_baseline": TrivialBaseline(),
        "simple_baseline": SimpleBaseline(),
        "full_system": SupportAgentPipeline()
    }

    judge = LLMJudge()
    all_results = {}
    model_predictions = {}

    y_true_intent = df["primary_intent"].tolist()
    y_true_action = df["ideal_action"].tolist()
    texts = df["text"].tolist()

    for model_name, model in models.items():
        logger.info(f"\n--- Evaluating Model: {model_name} ---")
        preds = []
        for i, text in enumerate(texts):
            if (i + 1) % 20 == 0 or i == 0 or i == len(texts) - 1:
                logger.info(f"[{model_name}] Progress: {i+1}/{len(texts)}")
            pred = model.handle_message(text)
            preds.append(pred)

        model_predictions[model_name] = preds

        y_pred_intent = [p["intent"] for p in preds]
        y_pred_action = [p["decision"] for p in preds]

        # 1. Intent Classification Metrics
        cm_png = os.path.join(results_dir, f"confusion_matrix_{model_name}.png") if model_name != "full_system" else os.path.join(results_dir, "confusion_matrix.png")
        intent_metrics = evaluate_intent_classification(y_true_intent, y_pred_intent, output_png=cm_png)

        # 2. Escalation Decision Metrics
        escalation_metrics = evaluate_escalation_decision(y_true_action, y_pred_action, texts=texts)

        # 3. LLM Judge Scoring on replies (sample up to 40 representative items)
        sample_count = min(40, len(df))
        sample_indices = np.linspace(0, len(df) - 1, sample_count, dtype=int)
        judge_scores = {"groundedness": [], "tone": [], "actionability": []}

        for idx in sample_indices:
            row = df.iloc[idx]
            rep = preds[idx]["reply"]
            ctx = preds[idx].get("retrieved_context", "")
            j_eval = judge.evaluate_reply(row["text"], rep, ctx)
            judge_scores["groundedness"].append(j_eval["groundedness"])
            judge_scores["tone"].append(j_eval["tone"])
            judge_scores["actionability"].append(j_eval["actionability"])

        all_results[model_name] = {
            "intent_accuracy": intent_metrics["accuracy"],
            "intent_macro_f1": intent_metrics["macro_f1"],
            "escalate_precision": escalation_metrics["escalate_precision"],
            "escalate_recall": escalation_metrics["escalate_recall"],
            "escalate_f1": escalation_metrics["escalate_f1"],
            "escalation_accuracy": escalation_metrics["accuracy"],
            "false_negative_count": escalation_metrics["false_negative_count"],
            "false_positive_count": escalation_metrics["false_positive_count"],
            "judge_groundedness_mean": round(float(np.mean(judge_scores["groundedness"])), 2),
            "judge_tone_mean": round(float(np.mean(judge_scores["tone"])), 2),
            "judge_actionability_mean": round(float(np.mean(judge_scores["actionability"])), 2),
            "judge_overall_mean": round(float(np.mean([
                np.mean(judge_scores["groundedness"]),
                np.mean(judge_scores["tone"]),
                np.mean(judge_scores["actionability"])
            ])), 2)
        }

        logger.info(f"{model_name} -> Intent Acc: {intent_metrics['accuracy']:.3f}, Macro-F1: {intent_metrics['macro_f1']:.3f}, Esc F1: {escalation_metrics['escalate_f1']:.3f}, Judge: {all_results[model_name]['judge_overall_mean']:.2f}")

    # 4. Calibrate LLM Judge vs Human Annotator
    logger.info("\n--- Running Judge Calibration vs Human Annotator ---")
    calibration_path = os.path.join(results_dir, "judge_vs_human_agreement.json")
    calibration_summary = calibrate_judge(calibration_path)

    # 5. Extract Top 5 Concrete Failure Cases from Full System
    logger.info("\n--- Generating Diagnostic Failure Analysis ---")
    full_preds = model_predictions["full_system"]
    failure_cases = []

    for idx, (true_intent, pred, true_action, text) in enumerate(zip(y_true_intent, full_preds, y_true_action, texts)):
        pred_intent = pred["intent"]
        pred_action = pred["decision"]
        tweet_id = df.iloc[idx].get("tweet_id", f"TW-{idx+1000}")

        intent_mismatch = (true_intent != pred_intent)
        action_mismatch = (true_action != pred_action)

        if intent_mismatch or action_mismatch:
            err_type = "Intent Misclassification" if intent_mismatch and not action_mismatch else (
                "Escalation Error" if action_mismatch and not intent_mismatch else "Dual Misclassification"
            )
            hypothesis = f"Expected intent '{true_intent}' and action '{true_action}', but predicted intent '{pred_intent}' and action '{pred_action}'."

            failure_cases.append({
                "tweet_id": tweet_id,
                "text": text,
                "true_intent": true_intent,
                "pred_intent": pred_intent,
                "true_action": true_action,
                "pred_action": pred_action,
                "pred_reason": pred["reason"],
                "draft_reply": pred["reply"],
                "error_type": err_type,
                "hypothesis": hypothesis
            })

    # Save Top 5 failure cases to failure_cases.md
    top_failures = failure_cases[:5]
    failures_md_path = os.path.join(results_dir, "failure_cases.md")
    with open(failures_md_path, "w", encoding="utf-8") as f:
        f.write("# Systematic Failure Analysis — AmazonHelp Support Agent\n\n")
        f.write("This document examines 5 real representative failure cases encountered during evaluation on the golden evaluation set (`golden_set/golden_eval_v1.csv`). Each case details the customer input, system prediction vs. ground truth, and root cause diagnosis.\n\n")

        for idx, fc in enumerate(top_failures, 1):
            f.write(f"## Failure Case {idx}: {fc['error_type']}\n")
            f.write(f"- **Tweet ID**: `{fc['tweet_id']}`\n")
            f.write(f"- **Customer Message**: \"{fc['text']}\"\n")
            f.write(f"- **Ground Truth**: Intent = `{fc['true_intent']}`, Ideal Action = `{fc['true_action']}`\n")
            f.write(f"- **System Output**: Intent = `{fc['pred_intent']}`, Decision = `{fc['pred_action']}`\n")
            f.write(f"- **System Escalation Justification**: \"{fc['pred_reason']}\"\n")
            f.write(f"- **Drafted Reply**: \"{fc['draft_reply']}\"\n")
            f.write(f"- **Root Cause Hypothesis**: {fc['hypothesis']}\n\n")
            f.write("---\n\n")

    logger.info(f"Saved {len(top_failures)} failure cases to {failures_md_path}")

    # 6. Save Overall Metrics Summary JSON
    summary_path = os.path.join(results_dir, "metrics_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    logger.info(f"Summary metrics saved to {summary_path}")
    return all_results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run evaluation harness on golden set")
    parser.add_argument("--golden_csv", type=str, default="golden_set/golden_eval_v1.csv")
    parser.add_argument("--results_dir", type=str, default="results")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of rows to evaluate")
    args = parser.parse_args()

    run_evaluation(golden_csv=args.golden_csv, results_dir=args.results_dir, limit=args.limit)
