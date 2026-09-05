"""
Lightweight security controls for demo and hackathon deployment.

- Optional API-key auth for intercept endpoint.
- Basic in-memory rate limit per client IP.
"""
from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque

from fastapi import Header, HTTPException, Request, status

_rate_lock = threading.Lock()
_rate_state: dict[str, deque[float]] = defaultdict(deque)


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """
    Enforce API key if CONSENT_GUARD_API_KEY is set.
    If unset, auth is disabled (developer-friendly local mode).
    """
    expected_key = os.environ.get("CONSENT_GUARD_API_KEY")
    if not expected_key:
        return

    if x_api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


def enforce_rate_limit(request: Request) -> None:
    """
    Basic per-IP sliding-window limiter.
    Controlled by env vars:
      - RATE_LIMIT_MAX_REQUESTS (default 60)
      - RATE_LIMIT_WINDOW_SECONDS (default 60)
    """
    max_requests = int(os.environ.get("RATE_LIMIT_MAX_REQUESTS", "60"))
    window_seconds = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60"))
    client_ip = request.client.host if request.client and request.client.host else "unknown"
    now = time.time()
    cutoff = now - window_seconds

    with _rate_lock:
        bucket = _rate_state[client_ip]
        while bucket and bucket[0] < cutoff:
            bucket.popleft()

        if len(bucket) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please retry shortly.",
            )

        bucket.append(now)


def reset_rate_limiter_state() -> None:
    """Test helper to clear in-memory rate limiter state."""
    with _rate_lock:
        _rate_state.clear()
