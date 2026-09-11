"""
Milestone 6: Metrics Calculation for Intent Classification and Escalation Policy.
Computes Accuracy, Macro-F1, Confusion Matrix plot, Escalation Precision/Recall/F1,
and diagnostic False-Negative analysis.
"""

import os
import logging
from typing import Dict, Any, List
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    confusion_matrix,
    classification_report
)
from src.taxonomy import ALL_INTENTS

logger = logging.getLogger(__name__)

def evaluate_intent_classification(
    y_true: List[str],
    y_pred: List[str],
    output_png: str = "results/confusion_matrix.png"
) -> Dict[str, Any]:
    """Computes intent classification accuracy, macro-F1, and generates confusion matrix PNG."""
    acc = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)

    # Confusion matrix
    labels = sorted(list(set(y_true) | set(y_pred)))
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    os.makedirs(os.path.dirname(output_png), exist_ok=True)
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=[l.replace("_", "\n") for l in labels],
        yticklabels=[l.replace("_", " ") for l in labels],
        cbar=False
    )
    plt.title("Intent Classification Confusion Matrix", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Predicted Intent", fontsize=11, labelpad=10)
    plt.ylabel("Ground Truth Intent", fontsize=11, labelpad=10)
    plt.xticks(rotation=45, ha="right", fontsize=9)
    plt.yticks(rotation=0, fontsize=9)
    plt.tight_layout()
    plt.savefig(output_png, dpi=200)
    plt.close()

    cls_report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)

    return {
        "accuracy": round(float(acc), 4),
        "macro_f1": round(float(macro_f1), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "class_report": cls_report
    }

def evaluate_escalation_decision(
    y_true: List[str],
    y_pred: List[str],
    texts: List[str] = None
) -> Dict[str, Any]:
    """
    Computes precision, recall, F1 for the 'escalate' action.
    Analyzes False Negatives (system said 'auto_handle', golden label was 'escalate').
    """
    pos_label = "escalate"
    precision = precision_score(y_true, y_pred, pos_label=pos_label, zero_division=0)
    recall = recall_score(y_true, y_pred, pos_label=pos_label, zero_division=0)
    f1 = f1_score(y_true, y_pred, pos_label=pos_label, zero_division=0)
    acc = accuracy_score(y_true, y_pred)

    # Detailed error breakdown
    false_negatives = []
    false_positives = []
    for i, (yt, yp) in enumerate(zip(y_true, y_pred)):
        text = texts[i] if texts and i < len(texts) else f"Row {i}"
        if yt == "escalate" and yp == "auto_handle":
            false_negatives.append({"index": i, "text": text})
        elif yt == "auto_handle" and yp == "escalate":
            false_positives.append({"index": i, "text": text})

    return {
        "accuracy": round(float(acc), 4),
        "escalate_precision": round(float(precision), 4),
        "escalate_recall": round(float(recall), 4),
        "escalate_f1": round(float(f1), 4),
        "false_negative_count": len(false_negatives),
        "false_positive_count": len(false_positives),
        "false_negatives_sample": false_negatives[:5],
        "false_positives_sample": false_positives[:5],
    }
