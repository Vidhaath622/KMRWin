"""Request guards for the public PollToll API.

- Reviewer key: endpoints that write to the audit trail (reviewer notes, roll uploads)
  require the `X-PollToll-Reviewer-Key` header when POLLTOLL_REVIEWER_KEY is set.
  On Vercel without a key configured, writes are switched off (public read-only demo).
  Locally without a key, writes stay open so the stage demo works offline.
- Rate limits: a small per-IP sliding window on expensive and write endpoints.
- Neutral-language check for reviewer notes (the log is signed into audit receipts).
- Allowed CORS origins.
"""

from __future__ import annotations

import hmac
import os
import re
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

REVIEWER_HEADER = "X-PollToll-Reviewer-Key"
MAX_BODY_BYTES = 3_000_000

_DEFAULT_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://polltoll-omega.vercel.app",
]


def allowed_origins() -> list[str]:
    raw = os.environ.get("POLLTOLL_ALLOWED_ORIGINS", "").strip()
    if raw:
        return [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]
    return _DEFAULT_ORIGINS


def require_reviewer(request: Request) -> None:
    """Gate for endpoints that change the audit trail."""
    expected = os.environ.get("POLLTOLL_REVIEWER_KEY", "").strip()
    if not expected:
        if os.environ.get("VERCEL"):
            raise HTTPException(
                status_code=403,
                detail=(
                    "Reviewing and roll uploads are switched off on this public site. "
                    "The site owner can enable them by setting POLLTOLL_REVIEWER_KEY."
                ),
            )
        return  # local development and offline stage demo
    supplied = request.headers.get(REVIEWER_HEADER, "")
    if not supplied or not hmac.compare_digest(supplied.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(
            status_code=401,
            detail="A valid reviewer key is required to change the audit trail. Enter it on the Review page.",
        )


# --- Rate limiting -----------------------------------------------------------

# bucket -> (max requests, window seconds)
RATE_LIMITS: dict[str, tuple[int, int]] = {
    "write": (20, 60),
    "ai": (60, 60),
    "receipt": (30, 60),
}

_hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_hits_lock = threading.Lock()


def client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    real = request.headers.get("x-real-ip", "")
    if real:
        return real.strip()
    return request.client.host if request.client else "unknown"


def rate_limit(bucket: str):
    """FastAPI dependency factory: `Depends(rate_limit("ai"))`."""

    def _check(request: Request) -> None:
        if os.environ.get("POLLTOLL_RATE_LIMIT", "1") == "0":
            return
        limit, window = RATE_LIMITS[bucket]
        key = (bucket, client_ip(request))
        now = time.monotonic()
        with _hits_lock:
            q = _hits[key]
            while q and now - q[0] > window:
                q.popleft()
            if len(q) >= limit:
                retry = max(1, int(window - (now - q[0])))
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many requests. Try again in {retry} seconds.",
                    headers={"Retry-After": str(retry)},
                )
            q.append(now)
            if len(_hits) > 50_000:  # keep memory bounded on long-lived servers
                _hits.clear()

    return _check


def reset_rate_limits() -> None:
    with _hits_lock:
        _hits.clear()


# --- Neutral language for reviewer notes --------------------------------------

_ACCUSATORY = re.compile(
    r"\b(rigg(ed|ing)|fraud(ulent)?|stolen|steal(ing)?|theft|cheat(ed|ing)?|scam|"
    r"corrupt(ion)?|criminal|conspira(cy|cies)|bribe(d|ry)?)\b"
    r"|धांधली|धोखाधड़ी|चोरी|घोटाला|भ्रष्ट"
    r"|ધાંધલી|છેતરપિંડી|ચોરી|કૌભાંડ|ભ્રષ્ટ",
    re.IGNORECASE,
)


def assert_neutral_note(*texts: str | None) -> None:
    for text in texts:
        if text and _ACCUSATORY.search(text):
            raise HTTPException(
                status_code=422,
                detail=(
                    "Notes must stay neutral: describe the evidence you checked, "
                    "not wrongdoing. Accusatory words are not accepted in the audit log."
                ),
            )
