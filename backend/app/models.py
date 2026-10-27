"""Pydantic schemas for PollToll API (Audit, Verify, and Assurance)."""

from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field

LanguageCode = Literal["en", "hi", "gu"]
ChangeType = Literal["ADDED", "DELETED", "MODIFIED", "BOOTH_TRANSFERRED"]
SeverityBand = Literal["INFO_RECONCILED", "MODERATE_REVIEW", "HIGH_STATISTICAL_OUTLIER"]


class SnapshotMeta(BaseModel):
    version_id: str = Field(description="Snapshot identifier, e.g. v2025_final")
    label: str = Field(description="Human-readable publication cycle label")
    publication_date: str
    roll_type: Literal["DRAFT", "FINAL", "SUPPLEMENT_CONSOLIDATED"]
    sha256: str = Field(description="Deterministic SHA-256 content hash of canonical CSV/Parquet")
    total_electors: int
    booth_count: int
    synthetic_notice: str = "100% SYNTHETIC TEST DATASET — NO REAL VOTER DATA"


class UncertaintyInterval(BaseModel):
    point_estimate: float = Field(description="Observed rate or metric (e.g. 0.096 for 9.6%)")
    ci_lower_95: float = Field(description="95% Wilson / Poisson lower bound")
    ci_upper_95: float = Field(description="95% Wilson / Poisson upper bound")
    historical_baseline_mean: float = Field(description="Multi-cycle baseline rate")
    historical_baseline_ci_upper: float
    z_score: float = Field(description="Standardized deviation vs baseline")
    sample_size: int = Field(description="Denominator count in booth/cohort")
    uncertainty_note: str


class FivePartExplanation(BaseModel):
    what_changed: str = Field(description="Exact empirical change recorded in the Electoral Change Ledger")
    rule_triggered: str = Field(description="Exact deterministic rule ID, version, and threshold")
    innocent_explanations: list[str] = Field(
        description="Plausible administrative, demographic, or clerical causes"
    )
    missing_evidence: list[str] = Field(
        description="Documents/records not present in published rolls needed to verify"
    )
    next_verification_step: str = Field(
        description="Concrete non-partisan verification step for an authorized reviewer"
    )
    confidence_level: float = Field(ge=0.0, le=1.0, description="Calibrated statistical confidence in the pattern")
    confidence_basis: str
    reasoning_steps: list[str]
    neutrality_passed: bool = True
    generated_by: Literal["gemini-3.8-flash+deterministic-ledger", "deterministic-ledger-engine"]


class LedgerEntry(BaseModel):
    ledger_id: str
    epic_id: str
    elector_name: str
    change_type: ChangeType
    constituency_id: str
    constituency_name: str
    from_booth_id: str | None = None
    to_booth_id: str | None = None
    from_serial_no: int | None = None
    to_serial_no: int | None = None
    house_no: str
    age_before: int | None = None
    age_after: int | None = None
    reason_code: str | None = None
    modified_fields: dict[str, dict[str, Any]] = Field(default_factory=dict)
    from_snapshot_sha256: str
    to_snapshot_sha256: str
    supplement_ref: str


class BoothChangeSummary(BaseModel):
    booth_id: str
    booth_name: str
    constituency_id: str
    constituency_name: str
    latitude: float
    longitude: float
    electors_from: int
    electors_to: int
    added_count: int
    deleted_count: int
    modified_count: int
    transferred_in_count: int
    transferred_out_count: int
    raw_deletion_rate: float
    net_effective_deletion_rate: float
    deletion_ci_lower_95: float
    deletion_ci_upper_95: float
    historical_deletion_baseline: float
    z_score_vs_baseline: float
    flag_count: int


class AnomalyFlag(BaseModel):
    flag_id: str
    booth_id: str
    booth_name: str
    constituency_id: str
    constituency_name: str
    rule_id: str
    rule_version: str
    rule_formula: str
    severity: SeverityBand
    headline: str
    affected_records_count: int
    sample_epic_ids: list[str]
    uncertainty: UncertaintyInterval
    explanation: FivePartExplanation
    review_status: Literal["OPEN_FOR_REVIEW", "ANNOTATED_BY_REVIEWER", "RECONCILED_BOUNDARY_SHIFT"]


class LedgerDiffResponse(BaseModel):
    from_snapshot: SnapshotMeta
    to_snapshot: SnapshotMeta
    historical_baselines_used: list[str]
    totals: dict[str, int]
    booth_summaries: list[BoothChangeSummary]
    flags: list[AnomalyFlag]
    sample_ledger_entries: list[LedgerEntry]
    neutrality_disclaimer: str


class CorrectionEvent(BaseModel):
    seq: int
    event_id: str
    flag_id: str
    reviewer_role: str
    action: Literal["FLAG_LOGGED", "EVIDENCE_NOTE_ADDED", "MARKED_EXPLAINED_ADMIN_SHIFT", "ESCALATED_FOR_FIELD_CHECK"]
    note: str
    evidence_reference: str | None = None
    timestamp_utc: str
    prev_hash: str
    event_hash: str


class AppendCorrectionRequest(BaseModel):
    flag_id: str = Field(min_length=3, max_length=64)
    reviewer_role: str = Field(default="Independent Civic Auditor", max_length=80)
    action: Literal["EVIDENCE_NOTE_ADDED", "MARKED_EXPLAINED_ADMIN_SHIFT", "ESCALATED_FOR_FIELD_CHECK"]
    note: str = Field(min_length=5, max_length=600)
    evidence_reference: str | None = Field(default=None, max_length=160)


class AuditReceipt(BaseModel):
    receipt_id: str
    schema_version: str = "polltoll-audit-receipt/1.0"
    generated_at_utc: str
    payload: dict[str, Any]
    canonical_payload: str = Field(
        description="Deterministic UTF-8 JSON string signed by Ed25519 for client-side WebCrypto verification"
    )
    payload_sha256: str
    signature_algorithm: str = "Ed25519"
    public_key_hex: str
    public_key_spki_b64: str
    signature_hex: str
    correction_chain_valid: bool
    correction_history: list[CorrectionEvent]


class VerifyReceiptRequest(BaseModel):
    canonical_payload: str
    payload: dict[str, Any]
    payload_sha256: str
    public_key_hex: str
    signature_hex: str
    correction_history: list[CorrectionEvent] = Field(default_factory=list)


class VerifyReceiptResponse(BaseModel):
    valid: bool
    checks: dict[str, bool]
    failure_reasons: list[str]


class ClaimFindingItem(BaseModel):
    statement: str
    evidence_source: str


class ClaimCheckRequest(BaseModel):
    claim_text: str = Field(min_length=6, max_length=800)
    from_version: str = Field(default="v2025_final", max_length=36)
    to_version: str = Field(default="v2026_draft", max_length=36)
    language: LanguageCode = "en"
    use_llm: bool = Field(
        default=True,
        description="Set False on automatic UI mount previews to preserve free-tier Gemini RPM/RPD quota.",
    )


class ClaimCheckResponse(BaseModel):
    claim_text: str
    language: LanguageCode
    overall_assessment_label: str
    verified_facts: list[ClaimFindingItem]
    disputed_interpretations: list[ClaimFindingItem]
    unprovable_from_public_data: list[ClaimFindingItem]
    confidence_level: float = Field(ge=0.0, le=1.0)
    confidence_basis: str
    reasoning_steps: list[str]
    referenced_booths: list[str]
    neutrality_guardrail_note: str
    generated_by: str


class CitizenLookupResponse(BaseModel):
    found: bool
    epic_id: str
    current_status: Literal["ACTIVE_UNCHANGED", "ACTIVE_MODIFIED", "ACTIVE_BOOTH_TRANSFERRED", "DELETED_IN_DRAFT_SUPPLEMENT", "NOT_FOUND"]
    latest_record: dict[str, Any] | None = None
    version_history: list[dict[str, Any]]
    plain_language_summary: dict[LanguageCode, str]
    official_next_steps: dict[LanguageCode, list[str]]
    relevant_eci_forms: list[str]
    # Every output shows its reasoning and confidence (hackathon rule).
    confidence_level: float = Field(default=1.0, ge=0.0, le=1.0)
    confidence_basis: dict[LanguageCode, str] = Field(default_factory=dict)
    reasoning_steps: dict[LanguageCode, list[str]] = Field(default_factory=dict)


class CitizenAssistantRequest(BaseModel):
    query: str = Field(default="", max_length=600)
    epic_id: str | None = Field(default=None, max_length=32)
    language: LanguageCode = "en"
    audio_base64: str | None = Field(
        default=None,
        max_length=2_800_000,  # about 2 MB of audio, i.e. a short voice question
        description="Optional base64 audio from browser mic",
    )
    audio_mime_type: str | None = Field(default=None, max_length=40, description="e.g. audio/webm or audio/wav")
    include_tts: bool = False
    use_llm: bool = Field(
        default=True,
        description="Set False for deterministic EPIC lookups or mount previews to save free-tier API quota.",
    )


class CitizenAssistantResponse(BaseModel):
    language: LanguageCode
    recognized_transcript: str | None = None
    answer_text: str
    confidence_level: float
    reasoning_steps: list[str]
    official_next_steps: list[str]
    referenced_forms: list[str]
    lookup_result: CitizenLookupResponse | None = None
    tts_audio_base64: str | None = None
    tts_mime_type: str | None = None
    generated_by: str


class GapAnalysisItem(BaseModel):
    id: int
    capability: str
    eronet_documented_status: str
    internal_epistemic_limit: str
    external_audit_gap: str
    polltoll_wedge: str
    is_prototype_core: bool
