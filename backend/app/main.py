"""PollToll FastAPI Application Entrypoint."""

from __future__ import annotations

import os
import threading
from contextlib import asynccontextmanager
from typing import Any

import duckdb
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.data.generator import ensure_synthetic_database, list_snapshots
from app.engine.anomaly import RULE_PACK_VERSION, RULES_CATALOG, detect_anomalies
from app.engine.ingest import IngestSnapshotRequest, ingest_csv_snapshot
from app.engine.ledger import compute_change_ledger, lookup_citizen_epic
from app.i18n import normalize_lang, pick
from app.engine.receipts import (
    append_correction_event,
    ensure_correction_table,
    generate_audit_receipt,
    list_corrections,
    verify_audit_receipt,
)
from app.models import (
    AppendCorrectionRequest,
    AuditReceipt,
    CitizenAssistantRequest,
    CitizenAssistantResponse,
    CitizenLookupResponse,
    ClaimCheckRequest,
    ClaimCheckResponse,
    CorrectionEvent,
    GapAnalysisItem,
    LedgerDiffResponse,
    SnapshotMeta,
    VerifyReceiptRequest,
    VerifyReceiptResponse,
)
from app.services.ai_explainer import (
    assist_citizen,
    check_viral_claim,
    get_ai_gateway_stats,
)
from app.services.gap_analysis import get_eronet_gap_matrix
from app.security import (
    MAX_BODY_BYTES,
    REVIEWER_HEADER,
    allowed_origins,
    assert_neutral_note,
    rate_limit,
    require_reviewer,
)

_db_conn: duckdb.DuckDBPyConnection | None = None
_db_init_lock = threading.Lock()


def get_db() -> duckdb.DuckDBPyConnection:
    """Returns a thread-safe per-caller DuckDB cursor so concurrent FastAPI worker threads never collide."""
    global _db_conn
    if _db_conn is None:
        with _db_init_lock:
            if _db_conn is None:
                _db_conn = ensure_synthetic_database()
    return _db_conn.cursor()


@asynccontextmanager
async def lifespan(_: FastAPI):
    con = get_db()
    _, _, _, b_sum, _ = compute_change_ledger(con, "v2025_final", "v2026_draft")
    flags = detect_anomalies(con, b_sum, "v2025_final", "v2026_draft")
    ensure_correction_table(con, flags)
    yield


app = FastAPI(
    title="PollToll API — Independent Electoral Change-Audit Platform",
    version="0.1.0",
    description=(
        "Deterministic Electoral Change Ledger, Historical-Baseline Statistical Anomaly Engine, "
        "5-Part Evidence Explanations, Multilingual Citizen Verify Assistant (EN/HI/GU), "
        "and Client-Verifiable Ed25519 Audit Receipts over 100% synthetic roll snapshots."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", REVIEWER_HEADER],
)


@app.middleware("http")
async def add_protocol_headers(request: Request, call_next) -> Response:
    # Reject oversized bodies before they are parsed (CSV uploads and voice clips are capped).
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > MAX_BODY_BYTES:
        return JSONResponse(status_code=413, content={"detail": "Request body is too large."})
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = response.headers.get("Cache-Control", "no-store")
    response.headers["X-PollToll-Protocol"] = "polltoll-audit-infra/0.1"
    response.headers["X-PollToll-Rule-Pack"] = RULE_PACK_VERSION
    response.headers["X-PollToll-Synthetic-Only"] = "true"
    return response


@app.post(
    "/api/v1/ingest/snapshot",
    response_model=SnapshotMeta,
    dependencies=[Depends(rate_limit("write")), Depends(require_reviewer)],
)
def api_ingest_snapshot(req: IngestSnapshotRequest) -> SnapshotMeta:
    try:
        return ingest_csv_snapshot(get_db(), req)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/v1/health")
def health() -> dict[str, Any]:
    con = get_db()
    snaps = list_snapshots(con)
    gw = get_ai_gateway_stats(con)
    return {
        "status": "ok",
        "platform": "PollToll",
        "rule_pack_version": RULE_PACK_VERSION,
        "gemini_live_enabled": gw["configured_key_count"] > 0,
        "gemini_key_pool_size": gw["configured_key_count"],
        "supported_languages": ["en", "hi", "gu"],
        "synthetic_data_only": True,
        "snapshot_count": len(snaps),
    }


@app.get("/api/v1/infra/quota")
def api_infra_quota() -> dict[str, Any]:
    return get_ai_gateway_stats(get_db())


@app.get("/api/v1/snapshots", response_model=list[SnapshotMeta])
def api_snapshots(lang: str = Query(default="en")) -> list[SnapshotMeta]:
    return list_snapshots(get_db(), lang=lang)


@app.get("/api/v1/rules")
def api_rules() -> dict[str, Any]:
    return {
        "rule_pack_version": RULE_PACK_VERSION,
        "rules": RULES_CATALOG,
    }


@app.get("/api/v1/gap-analysis", response_model=list[GapAnalysisItem])
def api_gap_analysis(lang: str = Query(default="en")) -> list[GapAnalysisItem]:
    return get_eronet_gap_matrix(lang=lang)


@app.get("/api/v1/audit/diff", response_model=LedgerDiffResponse)
def api_audit_diff(
    from_version: str = Query(default="v2025_final"),
    to_version: str = Query(default="v2026_draft"),
    sample_limit: int = Query(default=100, ge=10, le=500),
    lang: str = Query(default="en"),
) -> LedgerDiffResponse:
    if from_version == to_version:
        raise HTTPException(status_code=400, detail="from_version and to_version must be distinct snapshots.")
    con = get_db()
    lang_code = normalize_lang(lang)
    try:
        s_from, s_to, totals, booth_summaries, sample_entries = compute_change_ledger(
            con, from_version=from_version, to_version=to_version, sample_limit=sample_limit, lang=lang_code
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    flags = detect_anomalies(con, booth_summaries, from_version=from_version, to_version=to_version, lang=lang_code)
    ensure_correction_table(con, flags)

    # Reflect latest reviewer annotation status on flags
    annotated_flag_ids = {
        c.flag_id for c in list_corrections(con) if c.action != "FLAG_LOGGED"
    }
    for f in flags:
        if f.flag_id in annotated_flag_ids and f.review_status == "OPEN_FOR_REVIEW":
            f.review_status = "ANNOTATED_BY_REVIEWER"

    baselines_used = pick(
        lang_code,
        ["v2024_final -> v2025_draft", "v2025_draft -> v2025_final"],
        ["2024 अंतिम -> 2025 प्रारूप", "2025 प्रारूप -> 2025 अंतिम"],
        ["2024 અંતિમ -> 2025 મુસદ્દો", "2025 મુસદ્દો -> 2025 અંતિમ"],
    )
    disclaimer = pick(
        lang_code,
        "100% Synthetic Electoral Roll Data. Statistical flags highlight unusual change patterns for authorized human review and never establish fraud or wrongdoing.",
        "100% सिंथेटिक मतदाता डेटासेट। सांख्यिकीय फ्लैग केवल अधिकृत मानवीय समीक्षा के लिए असामान्य परिवर्तन पैटर्न को रेखांकित करते हैं और कभी भी धोखाधड़ी या गड़बड़ी साबित नहीं करते हैं।",
        "100% સિન્થેટિક મતદાર ડેટાસેટ. આંકડાકીય ફ્લેગ માત્ર અધિકૃત માનવીય સમીક્ષા માટે અસામાન્ય ફેરફારની પેટર્ન દર્શાવે છે અને ક્યારેય છેતરપિંડી કે ગેરરીતિ સાબિત કરતા નથી.",
    )

    return LedgerDiffResponse(
        from_snapshot=s_from,
        to_snapshot=s_to,
        historical_baselines_used=baselines_used,
        totals=totals,
        booth_summaries=booth_summaries,
        flags=flags,
        sample_ledger_entries=sample_entries,
        neutrality_disclaimer=disclaimer,
    )


@app.get("/api/v1/assurance/corrections", response_model=list[CorrectionEvent])
def api_list_corrections() -> list[CorrectionEvent]:
    return list_corrections(get_db())


@app.post(
    "/api/v1/assurance/corrections",
    response_model=CorrectionEvent,
    dependencies=[Depends(rate_limit("write")), Depends(require_reviewer)],
)
def api_append_correction(req: AppendCorrectionRequest) -> CorrectionEvent:
    assert_neutral_note(req.note, req.evidence_reference, req.reviewer_role)
    return append_correction_event(get_db(), req)


@app.post(
    "/api/v1/assurance/receipts/generate",
    response_model=AuditReceipt,
    dependencies=[Depends(rate_limit("receipt"))],
)
def api_generate_receipt(
    from_version: str = Query(default="v2025_final"),
    to_version: str = Query(default="v2026_draft"),
) -> AuditReceipt:
    con = get_db()
    s_from, s_to, totals, booth_summaries, _ = compute_change_ledger(
        con, from_version=from_version, to_version=to_version, sample_limit=20
    )
    flags = detect_anomalies(con, booth_summaries, from_version=from_version, to_version=to_version)
    return generate_audit_receipt(con, s_from, s_to, totals, flags)


@app.post("/api/v1/assurance/receipts/verify", response_model=VerifyReceiptResponse)
def api_verify_receipt(req: VerifyReceiptRequest) -> VerifyReceiptResponse:
    return verify_audit_receipt(req)


@app.get("/api/v1/verify/citizen/{epic_id}", response_model=CitizenLookupResponse)
def api_citizen_lookup(epic_id: str, lang: str = Query(default="en")) -> CitizenLookupResponse:
    return lookup_citizen_epic(get_db(), epic_id, lang=lang)


@app.post(
    "/api/v1/verify/assistant",
    response_model=CitizenAssistantResponse,
    dependencies=[Depends(rate_limit("ai"))],
)
def api_citizen_assistant(req: CitizenAssistantRequest) -> CitizenAssistantResponse:
    return assist_citizen(get_db(), req)


@app.post(
    "/api/v1/verify/claim-check",
    response_model=ClaimCheckResponse,
    dependencies=[Depends(rate_limit("ai"))],
)
def api_claim_check(req: ClaimCheckRequest) -> ClaimCheckResponse:
    return check_viral_claim(get_db(), req)
