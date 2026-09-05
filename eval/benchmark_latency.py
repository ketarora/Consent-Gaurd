#!/usr/bin/env python3
"""
Benchmark deterministic path latency (prefilter + allowlist).

Usage:
  python eval/benchmark_latency.py --input consent_guard_dataset.json --out eval/latency_results.json
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from allowlist import check_allowlist
from prefilter import run_prefilter


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    idx = int((len(values) - 1) * pct)
    return values[idx]


def run_once(text: str) -> bool:
    flag = run_prefilter(text)
    if not flag:
        return False
    checked = check_allowlist(flag, text)
    return not checked.cleared_by_allowlist


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark deterministic guard latency.")
    parser.add_argument("--input", required=True, help="Dataset JSON path.")
    parser.add_argument("--out", required=True, help="Output JSON path.")
    parser.add_argument("--iterations", type=int, default=20, help="Passes over dataset.")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    messages = data.get("messages", [])

    timings_ms: list[float] = []
    for _ in range(args.iterations):
        for item in messages:
            text = item.get("text", "")
            start = time.perf_counter()
            run_once(text)
            elapsed_ms = (time.perf_counter() - start) * 1000
            timings_ms.append(elapsed_ms)

    timings_ms.sort()
    output = {
        "dataset_size": len(messages),
        "total_samples": len(timings_ms),
        "iterations": args.iterations,
        "latency_ms": {
            "mean": round(statistics.mean(timings_ms), 4),
            "median": round(statistics.median(timings_ms), 4),
            "p95": round(percentile(timings_ms, 0.95), 4),
            "p99": round(percentile(timings_ms, 0.99), 4),
            "max": round(max(timings_ms), 4) if timings_ms else 0.0,
        },
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Wrote latency benchmark to {out_path}")


if __name__ == "__main__":
    main()
