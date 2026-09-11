"""
Evaluation metrics calculation module for Intent Classification and Escalation Policy.
"""

from typing import Dict, Any, List
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

def evaluate_intent_classification(y_true: List[str], y_pred: List[str]) -> Dict[str, float]:
    """Calculates Accuracy and Macro F1 score for Intent Classification."""
    acc = accuracy_score(y_true, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    return {
        "intent_accuracy": float(acc),
        "intent_macro_f1": float(f1)
    }

def evaluate_escalation_decision(y_true: List[str], y_pred: List[str]) -> Dict[str, Any]:
    """
    Calculates Precision, Recall, F1 score, and False Negatives / False Positives
    for escalation decision ('escalate' vs 'auto_handle').
    """
    # Binary mapping: escalate=1, auto_handle=0
    y_true_binary = [1 if y == "escalate" else 0 for y in y_true]
    y_pred_binary = [1 if y == "escalate" else 0 for y in y_pred]

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true_binary, y_pred_binary, average="binary", pos_label=1, zero_division=0
    )
    acc = accuracy_score(y_true_binary, y_pred_binary)

    # Count False Negatives (True Escalate, Model Auto-Handle - CRITICAL SAFETY RISK)
    fn_count = sum(1 for t, p in zip(y_true_binary, y_pred_binary) if t == 1 and p == 0)
    # Count False Positives (True Auto-Handle, Model Escalate - COSTLY AGENT FATIGUE)
    fp_count = sum(1 for t, p in zip(y_true_binary, y_pred_binary) if t == 0 and p == 1)

    return {
        "escalate_precision": float(precision),
        "escalate_recall": float(recall),
        "escalate_f1": float(f1),
        "escalation_accuracy": float(acc),
        "false_negative_count": int(fn_count),
        "false_positive_count": int(fp_count)
    }
