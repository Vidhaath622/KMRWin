"""Programmatic Snapshot Ingestion Pipeline (CSV -> Canonical Sort -> SHA-256 -> DuckDB)."""

from __future__ import annotations

import csv
import datetime as dt
import io
from typing import Any

import duckdb
from pydantic import BaseModel, Field

from app.data.generator import BOOTHS, _canonical_sha256
from app.models import SnapshotMeta


class IngestSnapshotRequest(BaseModel):
    version_id: str = Field(
        pattern=r"^[a-zA-Z0-9_\-]{3,36}$",
        description="Unique snapshot identifier, e.g. v2026_final_patch1",
    )
    label: str = Field(min_length=4, max_length=120)
    publication_date: str = Field(default_factory=lambda: dt.date.today().isoformat())
    roll_type: str = Field(default="SUPPLEMENT_CONSOLIDATED")
    base_version_id: str | None = Field(
        default="v2026_draft",
        max_length=36,
        description="Optional existing snapshot to apply CSV delta rows onto (or null for standalone full CSV)",
    )
    csv_payload: str = Field(
        min_length=15,
        max_length=2_000_000,
        description="CSV with columns: action(ADD|DELETE|MODIFY),epic_id,booth_id,elector_name,relation_name,gender,age,house_no,reason_code",
    )


def ingest_csv_snapshot(
    con: duckdb.DuckDBPyConnection, req: IngestSnapshotRequest
) -> SnapshotMeta:
    """Ingests a full CSV or applies a deterministic supplement CSV patch onto a base snapshot."""
    existing = con.execute(
        "SELECT count(*) FROM snapshots WHERE version_id = ?", [req.version_id]
    ).fetchone()[0]
    if existing:
        raise ValueError(f"Snapshot `{req.version_id}` already exists (snapshots are immutable).")

    booth_lookup = {b["booth_id"]: b for b in BOOTHS}
    records_by_epic: dict[str, dict[str, Any]] = {}

    if req.base_version_id:
        base_rows = con.execute(
            """
            SELECT epic_id, constituency_id, constituency_name, booth_id, booth_name,
                   serial_no, elector_name, relation_name, gender, age, house_no,
                   section_name, reason_code, supplement_ref
            FROM roll_entries
            WHERE version_id = ?
            """,
            [req.base_version_id],
        ).fetchall()
        if not base_rows:
            raise ValueError(f"Base snapshot `{req.base_version_id}` not found.")
        for r in base_rows:
            records_by_epic[r[0]] = {
                "version_id": req.version_id,
                "epic_id": r[0],
                "constituency_id": r[1],
                "constituency_name": r[2],
                "booth_id": r[3],
                "booth_name": r[4],
                "serial_no": r[5],
                "elector_name": r[6],
                "relation_name": r[7],
                "gender": r[8],
                "age": int(r[9]),
                "house_no": r[10],
                "section_name": r[11],
                "reason_code": r[12] or "",
                "supplement_ref": r[13] or f"{req.version_id.upper()}-BASE",
            }

    reader = csv.DictReader(io.StringIO(req.csv_payload.strip()))
    applied = 0
    for raw in reader:
        action = (raw.get("action") or "ADD").strip().upper()
        epic = (raw.get("epic_id") or "").strip().upper()
        if not epic.startswith("SYN-"):
            raise ValueError(
                f"Guardrail rejection on `{epic}`: PollToll ingestion requires `SYN-` synthetic IDs only."
            )
        if action == "DELETE":
            records_by_epic.pop(epic, None)
            applied += 1
            continue

        bid = (raw.get("booth_id") or "PS-101").strip().upper()
        bmeta = booth_lookup.get(bid, BOOTHS[0])
        records_by_epic[epic] = {
            "version_id": req.version_id,
            "epic_id": epic,
            "constituency_id": bmeta["constituency_id"],
            "constituency_name": bmeta["constituency_name"],
            "booth_id": bmeta["booth_id"],
            "booth_name": bmeta["booth_name"],
            "serial_no": 0,
            "elector_name": (raw.get("elector_name") or "Synthetic Elector").strip(),
            "relation_name": (raw.get("relation_name") or "Synthetic Relation").strip(),
            "gender": (raw.get("gender") or "M").strip().upper()[:1],
            "age": int(raw.get("age") or 30),
            "house_no": (raw.get("house_no") or "H-10").strip(),
            "section_name": "Ingested Supplement Batch",
            "reason_code": (raw.get("reason_code") or f"INGEST_{action}").strip(),
            "supplement_ref": f"{req.version_id.upper()}-CSV-INGEST",
        }
        applied += 1

    if applied == 0:
        raise ValueError("CSV payload contained 0 actionable rows.")

    # Re-sequence serial numbers deterministically per booth
    by_booth: dict[str, list[dict[str, Any]]] = {}
    for item in records_by_epic.values():
        by_booth.setdefault(item["booth_id"], []).append(item)

    final_rows: list[dict[str, Any]] = []
    for bid in sorted(by_booth.keys()):
        b_list = sorted(by_booth[bid], key=lambda x: (x["serial_no"] or 999999, x["epic_id"]))
        for idx, item in enumerate(b_list, start=1):
            item["serial_no"] = idx
            final_rows.append(item)

    sha = _canonical_sha256(final_rows)
    roll_type = (
        req.roll_type
        if req.roll_type in ("DRAFT", "FINAL", "SUPPLEMENT_CONSOLIDATED")
        else "SUPPLEMENT_CONSOLIDATED"
    )
    booth_cnt = len({r["booth_id"] for r in final_rows})

    con.execute(
        "INSERT INTO snapshots VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            req.version_id,
            req.label,
            req.publication_date,
            roll_type,
            sha,
            len(final_rows),
            booth_cnt,
        ],
    )
    con.executemany(
        "INSERT INTO roll_entries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                r["version_id"],
                r["epic_id"],
                r["constituency_id"],
                r["constituency_name"],
                r["booth_id"],
                r["booth_name"],
                r["serial_no"],
                r["elector_name"],
                r["relation_name"],
                r["gender"],
                r["age"],
                r["house_no"],
                r["section_name"],
                r["reason_code"],
                r["supplement_ref"],
            )
            for r in final_rows
        ],
    )

    return SnapshotMeta(
        version_id=req.version_id,
        label=req.label,
        publication_date=req.publication_date,
        roll_type=roll_type,  # type: ignore[arg-type]
        sha256=sha,
        total_electors=len(final_rows),
        booth_count=booth_cnt,
    )
