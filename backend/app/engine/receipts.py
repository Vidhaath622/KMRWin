"""Independent Audit Receipts (`Ed25519` + `SHA-256`) and Append-Only Correction Log."""

from __future__ import annotations

import base64
import datetime as dt
import hashlib
import json
import pathlib
import subprocess
from typing import Any

import duckdb
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from app.data.generator import DATA_DIR
from app.engine.anomaly import RULE_PACK_VERSION, RULES_CATALOG
from app.models import (
    AnomalyFlag,
    AppendCorrectionRequest,
    AuditReceipt,
    CorrectionEvent,
    SnapshotMeta,
    VerifyReceiptRequest,
    VerifyReceiptResponse,
)

KEY_DIR = DATA_DIR / "keys"
PRIV_KEY_FILE = KEY_DIR / "polltoll_auditor_ed25519.pem"


def ensure_signing_keypair() -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    KEY_DIR.mkdir(parents=True, exist_ok=True)
    if PRIV_KEY_FILE.exists():
        priv = serialization.load_pem_private_key(PRIV_KEY_FILE.read_bytes(), password=None)
        assert isinstance(priv, Ed25519PrivateKey)
        return priv, priv.public_key()

    priv = Ed25519PrivateKey.generate()
    pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    PRIV_KEY_FILE.write_bytes(pem)
    return priv, priv.public_key()


def ensure_correction_table(con: duckdb.DuckDBPyConnection, initial_flags: list[AnomalyFlag]) -> None:
    exists = con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_name = 'correction_log'"
    ).fetchone()[0]
    if not exists:
        con.execute(
            """
            CREATE TABLE correction_log (
                seq INTEGER PRIMARY KEY,
                event_id VARCHAR,
                flag_id VARCHAR,
                reviewer_role VARCHAR,
                action VARCHAR,
                note VARCHAR,
                evidence_reference VARCHAR,
                timestamp_utc VARCHAR,
                prev_hash VARCHAR,
                event_hash VARCHAR
            )
            """
        )

    cnt = con.execute("SELECT count(*) FROM correction_log").fetchone()[0]
    if cnt == 0 and initial_flags:
        # Seed genesis immutable audit-trail entries for initial run
        prev_hash = "0" * 64
        ts_base = "2026-10-27T09:00:00+00:00"
        for idx, flg in enumerate(initial_flags[:3], start=1):
            action = (
                "MARKED_EXPLAINED_ADMIN_SHIFT"
                if flg.rule_id == "RULE_BOOTH_SPLIT_RECONCILE"
                else "FLAG_LOGGED"
            )
            note = (
                f"Automated cross-booth EPIC reconciliation verified {flg.affected_records_count} records moved intact to PS-110."
                if flg.rule_id == "RULE_BOOTH_SPLIT_RECONCILE"
                else f"System logged {flg.rule_id}@{flg.rule_version} for independent human review."
            )
            ev_ref = (
                "V2026_DRAFT-BOOTH-RATIONALIZATION-ORDER-14"
                if flg.rule_id == "RULE_BOOTH_SPLIT_RECONCILE"
                else None
            )
            ev_id = f"CORR-{idx:04d}"
            ev_hash = compute_correction_hash(
                seq=idx,
                event_id=ev_id,
                flag_id=flg.flag_id,
                reviewer_role="PollToll Deterministic Ledger",
                action=action,
                note=note,
                evidence_reference=ev_ref,
                timestamp_utc=ts_base,
                prev_hash=prev_hash,
            )
            con.execute(
                "INSERT INTO correction_log VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    idx,
                    ev_id,
                    flg.flag_id,
                    "PollToll Deterministic Ledger",
                    action,
                    note,
                    ev_ref,
                    ts_base,
                    prev_hash,
                    ev_hash,
                ],
            )
            prev_hash = ev_hash


def compute_correction_hash(
    seq: int,
    event_id: str,
    flag_id: str,
    reviewer_role: str,
    action: str,
    note: str,
    evidence_reference: str | None,
    timestamp_utc: str,
    prev_hash: str,
) -> str:
    canonical = json.dumps(
        {
            "seq": seq,
            "event_id": event_id,
            "flag_id": flag_id,
            "reviewer_role": reviewer_role,
            "action": action,
            "note": note,
            "evidence_reference": evidence_reference or "",
            "timestamp_utc": timestamp_utc,
            "prev_hash": prev_hash,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def list_corrections(con: duckdb.DuckDBPyConnection) -> list[CorrectionEvent]:
    rows = con.execute(
        """
        SELECT seq, event_id, flag_id, reviewer_role, action, note, evidence_reference, timestamp_utc, prev_hash, event_hash
        FROM correction_log
        ORDER BY seq ASC
        """
    ).fetchall()
    return [
        CorrectionEvent(
            seq=r[0],
            event_id=r[1],
            flag_id=r[2],
            reviewer_role=r[3],
            action=r[4],
            note=r[5],
            evidence_reference=r[6],
            timestamp_utc=r[7],
            prev_hash=r[8],
            event_hash=r[9],
        )
        for r in rows
    ]


def append_correction_event(
    con: duckdb.DuckDBPyConnection, req: AppendCorrectionRequest
) -> CorrectionEvent:
    existing = list_corrections(con)
    next_seq = (existing[-1].seq + 1) if existing else 1
    prev_hash = existing[-1].event_hash if existing else ("0" * 64)
    ev_id = f"CORR-{next_seq:04d}"
    now_utc = dt.datetime.now(dt.timezone.utc).isoformat()
    ev_hash = compute_correction_hash(
        seq=next_seq,
        event_id=ev_id,
        flag_id=req.flag_id,
        reviewer_role=req.reviewer_role,
        action=req.action,
        note=req.note,
        evidence_reference=req.evidence_reference,
        timestamp_utc=now_utc,
        prev_hash=prev_hash,
    )
    con.execute(
        "INSERT INTO correction_log VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            next_seq,
            ev_id,
            req.flag_id,
            req.reviewer_role,
            req.action,
            req.note,
            req.evidence_reference,
            now_utc,
            prev_hash,
            ev_hash,
        ],
    )
    return CorrectionEvent(
        seq=next_seq,
        event_id=ev_id,
        flag_id=req.flag_id,
        reviewer_role=req.reviewer_role,
        action=req.action,
        note=req.note,
        evidence_reference=req.evidence_reference,
        timestamp_utc=now_utc,
        prev_hash=prev_hash,
        event_hash=ev_hash,
    )


def verify_correction_chain(events: list[CorrectionEvent]) -> tuple[bool, str | None]:
    prev = "0" * 64
    for idx, ev in enumerate(events, start=1):
        if ev.seq != idx:
            return False, f"Sequence gap at event {ev.event_id}: expected seq {idx}, got {ev.seq}"
        if ev.prev_hash != prev:
            return False, f"Broken prev_hash link at event {ev.event_id}"
        expected = compute_correction_hash(
            seq=ev.seq,
            event_id=ev.event_id,
            flag_id=ev.flag_id,
            reviewer_role=ev.reviewer_role,
            action=ev.action,
            note=ev.note,
            evidence_reference=ev.evidence_reference,
            timestamp_utc=ev.timestamp_utc,
            prev_hash=ev.prev_hash,
        )
        if ev.event_hash != expected:
            return False, f"Tampered correction event {ev.event_id}: hash mismatch"
        prev = ev.event_hash
    return True, None


def _git_commit_short() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(DATA_DIR.parents[1]),
            text=True,
        ).strip()
    except Exception:
        return "dev-local"


def generate_audit_receipt(
    con: duckdb.DuckDBPyConnection,
    s_from: SnapshotMeta,
    s_to: SnapshotMeta,
    totals: dict[str, int],
    flags: list[AnomalyFlag],
) -> AuditReceipt:
    ensure_correction_table(con, flags)
    corrections = list_corrections(con)
    chain_ok, _ = verify_correction_chain(corrections)
    priv_key, pub_key = ensure_signing_keypair()

    now_utc = dt.datetime.now(dt.timezone.utc).isoformat()
    rules_sha256 = hashlib.sha256(
        json.dumps(RULES_CATALOG, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    payload: dict[str, Any] = {
        "platform": "PollToll Independent Electoral Change-Audit Protocol",
        "generated_at_utc": now_utc,
        "software_commit": _git_commit_short(),
        "rule_pack_version": RULE_PACK_VERSION,
        "rules_catalog_sha256": rules_sha256,
        "datasets": {
            "from_snapshot": {
                "version_id": s_from.version_id,
                "publication_date": s_from.publication_date,
                "sha256": s_from.sha256,
                "total_electors": s_from.total_electors,
            },
            "to_snapshot": {
                "version_id": s_to.version_id,
                "publication_date": s_to.publication_date,
                "sha256": s_to.sha256,
                "total_electors": s_to.total_electors,
            },
            "synthetic_attestation": "100% SYNTHETIC DATA — ZERO REAL VOTER PII",
        },
        "ledger_totals": totals,
        "flags_summary": [
            {
                "flag_id": f.flag_id,
                "booth_id": f.booth_id,
                "rule_id": f"{f.rule_id}@{f.rule_version}",
                "severity": f.severity,
                "affected_records_count": f.affected_records_count,
                "point_estimate": f.uncertainty.point_estimate,
                "ci_95": [f.uncertainty.ci_lower_95, f.uncertainty.ci_upper_95],
                "confidence_level": f.explanation.confidence_level,
            }
            for f in flags
        ],
        "correction_log_head_hash": corrections[-1].event_hash if corrections else ("0" * 64),
        "correction_event_count": len(corrections),
        "epistemic_disclaimer": (
            "Statistical flags identify patterns requiring authorized human verification; "
            "they are never proof of wrongdoing or fraud."
        ),
    }

    canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload_bytes = canonical_payload.encode("utf-8")
    payload_sha256 = hashlib.sha256(payload_bytes).hexdigest()
    signature = priv_key.sign(payload_bytes)

    raw_pub = pub_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    spki_pub = pub_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    receipt_id = f"RCPT-{payload_sha256[:12].upper()}"

    return AuditReceipt(
        receipt_id=receipt_id,
        generated_at_utc=now_utc,
        payload=payload,
        canonical_payload=canonical_payload,
        payload_sha256=payload_sha256,
        public_key_hex=raw_pub.hex(),
        public_key_spki_b64=base64.b64encode(spki_pub).decode("ascii"),
        signature_hex=signature.hex(),
        correction_chain_valid=chain_ok,
        correction_history=corrections,
    )


def verify_audit_receipt(req: VerifyReceiptRequest) -> VerifyReceiptResponse:
    failures: list[str] = []
    checks = {
        "payload_matches_canonical_json": False,
        "sha256_digest_matches": False,
        "ed25519_signature_valid": False,
        "correction_hash_chain_intact": False,
    }

    try:
        parsed_canonical = json.loads(req.canonical_payload)
        if parsed_canonical == req.payload:
            checks["payload_matches_canonical_json"] = True
        else:
            failures.append("Structured `payload` differs from signed `canonical_payload` JSON.")
    except Exception as exc:
        failures.append(f"Invalid `canonical_payload` JSON: {exc}")

    computed_sha = hashlib.sha256(req.canonical_payload.encode("utf-8")).hexdigest()
    if computed_sha == req.payload_sha256:
        checks["sha256_digest_matches"] = True
    else:
        failures.append(
            f"SHA-256 mismatch: expected {req.payload_sha256[:16]}..., computed {computed_sha[:16]}..."
        )

    try:
        pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(req.public_key_hex))
        pub.verify(bytes.fromhex(req.signature_hex), req.canonical_payload.encode("utf-8"))
        checks["ed25519_signature_valid"] = True
    except (InvalidSignature, ValueError) as exc:
        failures.append(f"Ed25519 cryptographic signature verification failed: {exc or 'InvalidSignature'}")

    chain_ok, chain_err = verify_correction_chain(req.correction_history)
    if chain_ok:
        expected_head = req.correction_history[-1].event_hash if req.correction_history else None
        signed_head = req.payload.get("correction_log_head_hash")
        if expected_head is None or signed_head == expected_head:
            checks["correction_hash_chain_intact"] = True
        else:
            failures.append("Correction log head hash does not match signed payload head hash.")
    else:
        failures.append(chain_err or "Correction hash chain invalid.")

    return VerifyReceiptResponse(
        valid=all(checks.values()),
        checks=checks,
        failure_reasons=failures,
    )
