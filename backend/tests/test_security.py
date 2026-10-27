"""Security guards: reviewer key, read-only public mode, neutral notes, size caps, rate limits.

None of these tests write to the demo database: every request is rejected
before it reaches the audit trail.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.security import reset_rate_limits

client = TestClient(app)

NOTE = {
    "flag_id": "FLG-PS302-TEST",
    "reviewer_role": "Test Reviewer",
    "action": "EVIDENCE_NOTE_ADDED",
    "note": "Requested Form 7 objection records for review.",
}


def test_reviewer_key_required_when_configured(monkeypatch):
    reset_rate_limits()
    monkeypatch.setenv("POLLTOLL_REVIEWER_KEY", "correct-horse")
    missing = client.post("/api/v1/assurance/corrections", json=NOTE)
    assert missing.status_code == 401
    wrong = client.post(
        "/api/v1/assurance/corrections", json=NOTE, headers={"X-PollToll-Reviewer-Key": "nope"}
    )
    assert wrong.status_code == 401
    upload = client.post(
        "/api/v1/ingest/snapshot",
        json={
            "version_id": "v_sec_test",
            "label": "Security test",
            "base_version_id": None,
            "csv_payload": "action,epic_id\nADD,SYN-GJ-101-9999",
        },
    )
    assert upload.status_code == 401


def test_public_hosting_without_key_is_read_only(monkeypatch):
    reset_rate_limits()
    monkeypatch.delenv("POLLTOLL_REVIEWER_KEY", raising=False)
    monkeypatch.setenv("VERCEL", "1")
    res = client.post("/api/v1/assurance/corrections", json=NOTE)
    assert res.status_code == 403
    # Reading stays public
    assert client.get("/api/v1/assurance/corrections").status_code == 200


def test_accusatory_notes_are_rejected(monkeypatch):
    reset_rate_limits()
    monkeypatch.delenv("POLLTOLL_REVIEWER_KEY", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    for text in ["This booth was rigged", "यहाँ धांधली हुई", "અહીં છેતરપિંડી થઈ"]:
        res = client.post("/api/v1/assurance/corrections", json={**NOTE, "note": text})
        assert res.status_code == 422, text


def test_oversized_inputs_are_rejected():
    reset_rate_limits()
    long_claim = client.post(
        "/api/v1/verify/claim-check", json={"claim_text": "x" * 900, "use_llm": False}
    )
    assert long_claim.status_code == 422
    huge = client.post(
        "/api/v1/verify/assistant",
        content=b"{" + b" " * 3_100_000 + b"}",
        headers={"Content-Type": "application/json"},
    )
    assert huge.status_code == 413


def test_write_endpoints_are_rate_limited(monkeypatch):
    reset_rate_limits()
    monkeypatch.delenv("POLLTOLL_REVIEWER_KEY", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    bad = {**NOTE, "note": "rigged rigged rigged"}  # rejected as 422, never stored
    codes = [client.post("/api/v1/assurance/corrections", json=bad).status_code for _ in range(21)]
    assert codes[:20] == [422] * 20
    assert codes[20] == 429
    reset_rate_limits()


def test_cors_only_allows_polltoll_origins():
    ok = client.options(
        "/api/v1/health",
        headers={"Origin": "https://polltoll-omega.vercel.app", "Access-Control-Request-Method": "GET"},
    )
    assert ok.headers.get("access-control-allow-origin") == "https://polltoll-omega.vercel.app"
    evil = client.options(
        "/api/v1/health",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert evil.headers.get("access-control-allow-origin") is None
