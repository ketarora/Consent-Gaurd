#!/usr/bin/env python3
"""
Minimal merchant-agent integration example for Consent Guard.

Usage:
    python scripts/merchant_agent_example.py --base-url http://localhost:8000/api
"""
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request


SAMPLE_MESSAGES = [
    "Here are your account details for the billing sync.",
    "Confirm your order in the next 10 minutes or your cart expires forever.",
]


def post_json(url: str, payload: dict) -> dict:
    request = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:  # nosec B310
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Send sample merchant messages through Consent Guard.")
    parser.add_argument("--base-url", default="http://localhost:8000/api", help="Consent Guard API base URL.")
    parser.add_argument("--agent-id", default="merchant-agent-demo", help="Agent ID to send with messages.")
    args = parser.parse_args()

    print(f"Sending {len(SAMPLE_MESSAGES)} message(s) to {args.base_url}/intercept\n")
    for idx, message in enumerate(SAMPLE_MESSAGES, start=1):
        try:
            result = post_json(
                f"{args.base_url}/intercept",
                {"content": message, "agent_id": args.agent_id},
            )
        except urllib.error.URLError as exc:
            raise SystemExit(f"Request failed: {exc}") from exc

        decision = result.get("decision", {})
        action = decision.get("action", "unknown")
        print(f"[{idx}] Action: {action}")
        print(f"    Message: {message}")

        flags = decision.get("flags", [])
        if flags:
            for flag in flags:
                print(
                    "    - Flag:",
                    flag.get("category"),
                    f"(confidence={flag.get('confidence')})",
                    f"span={flag.get('quoted_span')!r}",
                )
        print("")


if __name__ == "__main__":
    main()
