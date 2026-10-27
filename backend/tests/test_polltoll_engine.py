"""Automated test suite for PollToll Change Ledger, Statistical Engine, Neutrality, and Ed25519 Receipts."""

from __future__ import annotations

import json
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_snapshots_are_deterministic_and_synthetic():
    res = client.get("/api/v1/snapshots")
    assert res.status_code == 200
    snaps = res.json()
    assert len(snaps) == 4
    versions = [s["version_id"] for s in snaps]
    assert versions == ["v2024_final", "v2025_draft", "v2025_final", "v2026_draft"]
    assert all(len(s["sha256"]) == 64 for s in snaps)


def test_change_ledger_reconciles_booth_split_and_flags_true_outliers():
    res = client.get("/api/v1/audit/diff?from_version=v2025_final&to_version=v2026_draft")
    assert res.status_code == 200
    body = res.json()

    # 338 electors moved intact from PS-109 -> PS-110
    assert body["totals"]["booth_transferred"] == 338
    booths = {b["booth_id"]: b for b in body["booth_summaries"]}
    assert booths["PS-109"]["transferred_out_count"] == 338
    assert booths["PS-110"]["transferred_in_count"] == 338
    assert booths["PS-109"]["net_effective_deletion_rate"] < 0.03

    rule_ids = {f["rule_id"] for f in body["flags"]}
    assert "RULE_BOOTH_SPLIT_RECONCILE" in rule_ids
    assert "RULE_HIST_DEL_SPIKE" in rule_ids
    assert "RULE_HOUSEHOLD_DENSITY" in rule_ids
    assert "RULE_AGE_COHORT_IMPLAUSIBLE" in rule_ids
    assert "RULE_LEXICAL_DUP_CLUSTER" in rule_ids

    # Every flag must disclose 95% CI, missing evidence, and innocent explanations
    for flg in body["flags"]:
        assert 0.0 <= flg["uncertainty"]["ci_lower_95"] <= flg["uncertainty"]["ci_upper_95"] <= 1.0
        assert len(flg["explanation"]["innocent_explanations"]) >= 1
        assert len(flg["explanation"]["missing_evidence"]) >= 1
        assert flg["explanation"]["neutrality_passed"] is True


def test_multilingual_citizen_lookup_and_claim_checker():
    # Transferred citizen in PS-109 -> PS-110
    c_res = client.get("/api/v1/verify/citizen/SYN-GJ-109-0042")
    assert c_res.status_code == 200
    c_data = c_res.json()
    assert c_data["current_status"] == "ACTIVE_BOOTH_TRANSFERRED"
    assert set(c_data["plain_language_summary"].keys()) == {"en", "hi", "gu"}

    # Gujarati assistant response
    a_res = client.post(
        "/api/v1/verify/assistant",
        json={"query": "મારું નામ SYN-GJ-104-0019 મતદાર યાદીમાં સુરક્ષિત છે?", "language": "gu"},
    )
    assert a_res.status_code == 200
    a_data = a_res.json()
    assert a_data["lookup_result"]["current_status"] == "DELETED_IN_DRAFT_SUPPLEMENT"
    assert "Form 6" in a_data["referenced_forms"]

    # Viral claim check on Booth 109
    cl_res = client.post(
        "/api/v1/verify/claim-check",
        json={"claim_text": "340 voters vanished overnight from Booth PS-109!", "language": "en"},
    )
    assert cl_res.status_code == 200
    cl_data = cl_res.json()
    assert len(cl_data["verified_facts"]) >= 1
    assert len(cl_data["disputed_interpretations"]) >= 1
    assert len(cl_data["unprovable_from_public_data"]) >= 1


def test_ed25519_audit_receipt_and_tamper_detection():
    # Append a reviewer annotation
    ann = client.post(
        "/api/v1/assurance/corrections",
        json={
            "flag_id": "FLG-PS302-TEST",
            "reviewer_role": "University Election Lab Auditor",
            "action": "EVIDENCE_NOTE_ADDED",
            "note": "Requested Form-10 deletion supplement reason breakdown from District Election Office.",
            "evidence_reference": "DEO-REQ-2026-108",
        },
    )
    assert ann.status_code == 200

    rcpt_res = client.post("/api/v1/assurance/receipts/generate")
    assert rcpt_res.status_code == 200
    rcpt = rcpt_res.json()
    assert rcpt["correction_chain_valid"] is True

    # Valid verification passes all 4 cryptographic checks
    ver_ok = client.post(
        "/api/v1/assurance/receipts/verify",
        json={
            "canonical_payload": rcpt["canonical_payload"],
            "payload": rcpt["payload"],
            "payload_sha256": rcpt["payload_sha256"],
            "public_key_hex": rcpt["public_key_hex"],
            "signature_hex": rcpt["signature_hex"],
            "correction_history": rcpt["correction_history"],
        },
    )
    assert ver_ok.status_code == 200
    assert ver_ok.json()["valid"] is True

    # Tampering 1 byte in canonical_payload MUST fail SHA-256 and Ed25519 signature!
    tampered_dict = json.loads(rcpt["canonical_payload"])
    tampered_dict["ledger_totals"]["deleted"] = 999999
    tampered_canonical = json.dumps(tampered_dict, sort_keys=True, separators=(",", ":"))
    ver_bad = client.post(
        "/api/v1/assurance/receipts/verify",
        json={
            "canonical_payload": tampered_canonical,
            "payload": tampered_dict,
            "payload_sha256": rcpt["payload_sha256"],
            "public_key_hex": rcpt["public_key_hex"],
            "signature_hex": rcpt["signature_hex"],
            "correction_history": rcpt["correction_history"],
        },
    )
    assert ver_bad.status_code == 200
    bad_body = ver_bad.json()
    assert bad_body["valid"] is False
    assert bad_body["checks"]["ed25519_signature_valid"] is False


def test_infrastructure_csv_ingestion_and_synthetic_guardrail():
    # Rejects non-SYN real-looking EPIC IDs
    bad_ingest = client.post(
        "/api/v1/ingest/snapshot",
        json={
            "version_id": "v_reject_test",
            "label": "Should Fail",
            "base_version_id": "v2026_draft",
            "csv_payload": "action,epic_id,booth_id,elector_name,relation_name,gender,age,house_no,reason_code\nADD,ABC1234567,PS-101,Test,Rel,M,25,H-1,A_FORM6",
        },
    )
    assert bad_ingest.status_code == 400

    # Accepts valid SYN-* batch and computes deterministic SHA-256
    ok_ingest = client.post(
        "/api/v1/ingest/snapshot",
        json={
            "version_id": "v2026_patch_test",
            "label": "Post-Objection Synthetic Patch",
            "base_version_id": "v2026_draft",
            "csv_payload": "action,epic_id,booth_id,elector_name,relation_name,gender,age,house_no,reason_code\nADD,SYN-GJ-101-9991,PS-101,Devansh Joshi,Kiritbhai Joshi,M,22,H-14,A_FORM6",
        },
    )
    assert ok_ingest.status_code == 200
    assert ok_ingest.headers.get("X-PollToll-Protocol") == "polltoll-audit-infra/0.1"
    meta = ok_ingest.json()
    assert len(meta["sha256"]) == 64
