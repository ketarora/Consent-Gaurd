#!/usr/bin/env python3
"""
Simple evaluation and dataset hygiene script for Consent Guard.

Usage:
    python eval/run_eval.py --input consent_guard_dataset.json --out eval/results.json --clean
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from allowlist import check_allowlist
from prefilter import run_prefilter


def clean_text(text: str) -> str:
    text = re.sub(r"\bYour your\b", "Your", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def deterministic_predict_flag(message_text: str) -> bool:
    """
    Predict whether a message should be flagged by the deterministic
    false-urgency path: prefilter + allowlist.
    """
    prefilter_flag = run_prefilter(message_text)
    if prefilter_flag is None:
        return False
    checked = check_allowlist(prefilter_flag, message_text)
    return not checked.cleared_by_allowlist


def safe_div(numerator: float, denominator: float) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute dataset stats for Consent Guard.")
    parser.add_argument("--input", required=True, help="Path to source dataset JSON.")
    parser.add_argument("--out", required=True, help="Path to summary output JSON.")
    parser.add_argument("--clean", action="store_true", help="Also write a cleaned dataset file.")
    parser.add_argument(
        "--cleaned-out",
        default="eval/consent_guard_dataset_cleaned.json",
        help="Path to cleaned dataset output when --clean is set.",
    )
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    messages = data.get("messages", [])
    category_counts: Counter[str] = Counter()
    flagged_count = 0
    clean_count = 0
    tp = fp = tn = fn = 0
    urgency_tp = urgency_fp = urgency_tn = urgency_fn = 0

    for message in messages:
        category = message.get("category", "unknown")
        text = message.get("text", "")
        expected_flag = bool(message.get("expected_flag"))
        category_counts[category] += 1
        predicted_flag = deterministic_predict_flag(text)

        if expected_flag:
            flagged_count += 1
        else:
            clean_count += 1

        if expected_flag and predicted_flag:
            tp += 1
        elif not expected_flag and predicted_flag:
            fp += 1
        elif expected_flag and not predicted_flag:
            fn += 1
        else:
            tn += 1

        if category == "false_urgency":
            if expected_flag and predicted_flag:
                urgency_tp += 1
            elif not expected_flag and predicted_flag:
                urgency_fp += 1
            elif expected_flag and not predicted_flag:
                urgency_fn += 1
            else:
                urgency_tn += 1

        if args.clean:
            message["text"] = clean_text(text)

    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    accuracy = safe_div(tp + tn, tp + tn + fp + fn)
    f1 = safe_div(2 * precision * recall, precision + recall)

    urgency_precision = safe_div(urgency_tp, urgency_tp + urgency_fp)
    urgency_recall = safe_div(urgency_tp, urgency_tp + urgency_fn)
    urgency_accuracy = safe_div(
        urgency_tp + urgency_tn, urgency_tp + urgency_tn + urgency_fp + urgency_fn
    )
    urgency_f1 = safe_div(
        2 * urgency_precision * urgency_recall, urgency_precision + urgency_recall
    )

    summary = {
        "total_messages": len(messages),
        "category_counts": dict(sorted(category_counts.items())),
        "flagged_count": flagged_count,
        "clean_count": clean_count,
        "evaluation": {
            "model_scope": "deterministic_prefilter_allowlist_only",
            "note": (
                "These metrics evaluate only the deterministic false-urgency path. "
                "LLM-classified categories are not scored in this script."
            ),
            "overall_confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
            "overall_metrics": {
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "accuracy": accuracy,
            },
            "false_urgency_subset_confusion_matrix": {
                "tp": urgency_tp,
                "fp": urgency_fp,
                "tn": urgency_tn,
                "fn": urgency_fn,
            },
            "false_urgency_subset_metrics": {
                "precision": urgency_precision,
                "recall": urgency_recall,
                "f1": urgency_f1,
                "accuracy": urgency_accuracy,
            },
        },
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
        f.write("\n")

    if args.clean:
        cleaned_path = Path(args.cleaned_out)
        cleaned_path.parent.mkdir(parents=True, exist_ok=True)
        with cleaned_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"Wrote cleaned dataset to {cleaned_path}")

    print(f"Wrote summary to {out_path}")


if __name__ == "__main__":
    main()
