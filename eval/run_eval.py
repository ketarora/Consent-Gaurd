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


def clean_text(text: str) -> str:
    text = re.sub(r"\bYour your\b", "Your", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


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

    for message in messages:
        category = message.get("category", "unknown")
        category_counts[category] += 1
        if bool(message.get("expected_flag")):
            flagged_count += 1
        else:
            clean_count += 1

        if args.clean:
            message["text"] = clean_text(message.get("text", ""))

    summary = {
        "total_messages": len(messages),
        "category_counts": dict(sorted(category_counts.items())),
        "flagged_count": flagged_count,
        "clean_count": clean_count,
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
