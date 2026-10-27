#!/usr/bin/env python3
"""PollToll Headless Infrastructure CLI (`polltoll_cli.py`).

Enables independent auditors, universities, newsrooms, and CI pipelines to run
deterministic Electoral Change Ledger diffs, issue Ed25519 audit receipts, and
cryptographically verify receipts offline without trusting any hosted web server.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

BACKEND_ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.data.generator import ensure_synthetic_database, list_snapshots  # noqa: E402
from app.engine.anomaly import detect_anomalies  # noqa: E402
from app.engine.ledger import compute_change_ledger  # noqa: E402
from app.engine.receipts import generate_audit_receipt, verify_audit_receipt  # noqa: E402
from app.models import CorrectionEvent, VerifyReceiptRequest  # noqa: E402
from app.services.gap_analysis import get_eronet_gap_matrix  # noqa: E402


def cmd_snapshots(_: argparse.Namespace) -> None:
    con = ensure_synthetic_database()
    snaps = [s.model_dump() for s in list_snapshots(con)]
    print(json.dumps(snaps, indent=2))


def cmd_diff(args: argparse.Namespace) -> None:
    con = ensure_synthetic_database()
    s_from, s_to, totals, booths, _ = compute_change_ledger(
        con, from_version=args.from_version, to_version=args.to_version, sample_limit=20
    )
    flags = detect_anomalies(con, booths, from_version=args.from_version, to_version=args.to_version)
    output = {
        "from_snapshot": s_from.model_dump(),
        "to_snapshot": s_to.model_dump(),
        "totals": totals,
        "flags": [
            {
                "flag_id": f.flag_id,
                "booth_id": f.booth_id,
                "rule": f"{f.rule_id}@{f.rule_version}",
                "severity": f.severity,
                "headline": f.headline,
                "ci_95": [f.uncertainty.ci_lower_95, f.uncertainty.ci_upper_95],
                "z_score": f.uncertainty.z_score,
            }
            for f in flags
        ],
    }
    print(json.dumps(output, indent=2))


def cmd_sign_receipt(args: argparse.Namespace) -> None:
    con = ensure_synthetic_database()
    s_from, s_to, totals, booths, _ = compute_change_ledger(
        con, from_version=args.from_version, to_version=args.to_version, sample_limit=20
    )
    flags = detect_anomalies(con, booths, from_version=args.from_version, to_version=args.to_version)
    receipt = generate_audit_receipt(con, s_from, s_to, totals, flags)
    out_path = pathlib.Path(args.out)
    out_path.write_text(receipt.model_dump_json(indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "signed",
                "receipt_id": receipt.receipt_id,
                "payload_sha256": receipt.payload_sha256,
                "public_key_hex": receipt.public_key_hex,
                "output_file": str(out_path),
            },
            indent=2,
        )
    )


def cmd_verify_receipt(args: argparse.Namespace) -> None:
    raw = json.loads(pathlib.Path(args.receipt_file).read_text(encoding="utf-8"))
    req = VerifyReceiptRequest(
        canonical_payload=raw["canonical_payload"],
        payload=raw["payload"],
        payload_sha256=raw["payload_sha256"],
        public_key_hex=raw["public_key_hex"],
        signature_hex=raw["signature_hex"],
        correction_history=[CorrectionEvent(**c) for c in raw.get("correction_history", [])],
    )
    res = verify_audit_receipt(req)
    print(res.model_dump_json(indent=2))
    if not res.valid:
        sys.exit(2)


def cmd_gap(_: argparse.Namespace) -> None:
    print(json.dumps([g.model_dump() for g in get_eronet_gap_matrix()], indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="PollToll Independent Electoral Change-Audit CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_snaps = sub.add_parser("snapshots", help="List content-addressed roll snapshots & SHA-256 hashes")
    p_snaps.set_defaults(func=cmd_snapshots)

    p_diff = sub.add_parser("diff", help="Run Electoral Change Ledger & Statistical Anomaly Engine")
    p_diff.add_argument("--from", dest="from_version", default="v2025_final")
    p_diff.add_argument("--to", dest="to_version", default="v2026_draft")
    p_diff.set_defaults(func=cmd_diff)

    p_sign = sub.add_parser("sign-receipt", help="Generate & sign an Ed25519 Audit Receipt JSON")
    p_sign.add_argument("--from", dest="from_version", default="v2025_final")
    p_sign.add_argument("--to", dest="to_version", default="v2026_draft")
    p_sign.add_argument("--out", default="polltoll.receipt.json")
    p_sign.set_defaults(func=cmd_sign_receipt)

    p_ver = sub.add_parser("verify-receipt", help="Verify an Ed25519 Audit Receipt & Hash Chain offline")
    p_ver.add_argument("receipt_file")
    p_ver.set_defaults(func=cmd_verify_receipt)

    p_gap = sub.add_parser("gap-matrix", help="Print ERONET vs PollToll epistemic gap matrix")
    p_gap.set_defaults(func=cmd_gap)

    ns = parser.parse_args()
    ns.func(ns)


if __name__ == "__main__":
    main()
