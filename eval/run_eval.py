#!/usr/bin/env python3
"""
Simple evaluation and dataset hygiene script for Consent Guard.

Usage:
    python eval/run_eval.py --input consent_guard_dataset.json --out eval/results.json --clean

This script:
 - loads the dataset
 - computes per-category counts and flagged/clean counts
 - optionally applies a small cleaning pass (fix "Your your" -> "Your")
 - writes cleaned dataset and a summary JSON
"""
import argparse
import json
import re
from collections import Counter


def clean_text(s: str) -> str:
    s = re.sub(r"\bYour your\b", "Your", s)
    s = re.sub(r"\s+\|\s+", " | ", s)
    s = re.sub(r"\s+\", s)
    return s


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    messages = data.get("messages", [])
    total = len(messages)
    category_counts = Counter()
    flagged = 0
    clean = 0

    for m in messages:
        cat = m.get("category", "unknown")
        category_counts[cat] += 1
        if m.get("expected_flag"):
            flagged += 1
        else:
            clean += 1
        if args.clean:
            text = m.get("text", "")
            text = text.replace("Your your", "Your")
            # normalize multiple spaces
            text = re.sub(r"\s+", " ", text).strip()
            m["text"] = text

    summary = {
        "total_messages": total,
        "category_counts": dict(category_counts),
        "flagged_count": flagged,
        "clean_count": clean,
    }

    if args.clean:
        cleaned_path = "eval/consent_guard_dataset_cleaned.json"
        with open(cleaned_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        summary["cleaned_dataset"] = cleaned_path

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("Wrote summary to", args.out)


if __name__ == "__main__":
    main()
