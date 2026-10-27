export type LanguageCode = "en" | "hi" | "gu";
export type ChangeType = "ADDED" | "DELETED" | "MODIFIED" | "BOOTH_TRANSFERRED";
export type SeverityBand =
  | "INFO_RECONCILED"
  | "MODERATE_REVIEW"
  | "HIGH_STATISTICAL_OUTLIER";

export interface SnapshotMeta {
  version_id: string;
  label: string;
  publication_date: string;
  roll_type: "DRAFT" | "FINAL" | "SUPPLEMENT_CONSOLIDATED";
  sha256: string;
  total_electors: number;
  booth_count: number;
  synthetic_notice: string;
}

export interface UncertaintyInterval {
  point_estimate: number;
  ci_lower_95: number;
  ci_upper_95: number;
  historical_baseline_mean: number;
  historical_baseline_ci_upper: number;
  z_score: number;
  sample_size: number;
  uncertainty_note: string;
}

export interface FivePartExplanation {
  what_changed: string;
  rule_triggered: string;
  innocent_explanations: string[];
  missing_evidence: string[];
  next_verification_step: string;
  confidence_level: number;
  confidence_basis: string;
  reasoning_steps: string[];
  neutrality_passed: boolean;
  generated_by: string;
}

export interface LedgerEntry {
  ledger_id: string;
  epic_id: string;
  elector_name: string;
  change_type: ChangeType;
  constituency_id: string;
  constituency_name: string;
  from_booth_id: string | null;
  to_booth_id: string | null;
  from_serial_no: number | null;
  to_serial_no: number | null;
  house_no: string;
  age_before: number | null;
  age_after: number | null;
  reason_code: string | null;
  modified_fields: Record<string, { before: unknown; after: unknown }>;
  from_snapshot_sha256: string;
  to_snapshot_sha256: string;
  supplement_ref: string;
}

export interface BoothChangeSummary {
  booth_id: string;
  booth_name: string;
  constituency_id: string;
  constituency_name: string;
  latitude: number;
  longitude: number;
  electors_from: number;
  electors_to: number;
  added_count: number;
  deleted_count: number;
  modified_count: number;
  transferred_in_count: number;
  transferred_out_count: number;
  raw_deletion_rate: number;
  net_effective_deletion_rate: number;
  deletion_ci_lower_95: number;
  deletion_ci_upper_95: number;
  historical_deletion_baseline: number;
  z_score_vs_baseline: number;
  flag_count: number;
}

export interface AnomalyFlag {
  flag_id: string;
  booth_id: string;
  booth_name: string;
  constituency_id: string;
  constituency_name: string;
  rule_id: string;
  rule_version: string;
  rule_formula: string;
  severity: SeverityBand;
  headline: string;
  affected_records_count: number;
  sample_epic_ids: string[];
  uncertainty: UncertaintyInterval;
  explanation: FivePartExplanation;
  review_status:
    | "OPEN_FOR_REVIEW"
    | "ANNOTATED_BY_REVIEWER"
    | "RECONCILED_BOUNDARY_SHIFT";
}

export interface LedgerDiffResponse {
  from_snapshot: SnapshotMeta;
  to_snapshot: SnapshotMeta;
  historical_baselines_used: string[];
  totals: {
    electors_from: number;
    electors_to: number;
    added: number;
    deleted: number;
    modified: number;
    booth_transferred: number;
  };
  booth_summaries: BoothChangeSummary[];
  flags: AnomalyFlag[];
  sample_ledger_entries: LedgerEntry[];
  neutrality_disclaimer: string;
}

export interface CorrectionEvent {
  seq: number;
  event_id: string;
  flag_id: string;
  reviewer_role: string;
  action:
    | "FLAG_LOGGED"
    | "EVIDENCE_NOTE_ADDED"
    | "MARKED_EXPLAINED_ADMIN_SHIFT"
    | "ESCALATED_FOR_FIELD_CHECK";
  note: string;
  evidence_reference: string | null;
  timestamp_utc: string;
  prev_hash: string;
  event_hash: string;
}

export interface AuditReceipt {
  receipt_id: string;
  schema_version: string;
  generated_at_utc: string;
  payload: Record<string, unknown>;
  canonical_payload: string;
  payload_sha256: string;
  signature_algorithm: string;
  public_key_hex: string;
  public_key_spki_b64: string;
  signature_hex: string;
  correction_chain_valid: boolean;
  correction_history: CorrectionEvent[];
}

export interface ClaimFindingItem {
  statement: string;
  evidence_source: string;
}

export interface ClaimCheckResponse {
  claim_text: string;
  language: LanguageCode;
  overall_assessment_label: string;
  verified_facts: ClaimFindingItem[];
  disputed_interpretations: ClaimFindingItem[];
  unprovable_from_public_data: ClaimFindingItem[];
  confidence_level: number;
  confidence_basis: string;
  reasoning_steps: string[];
  referenced_booths: string[];
  neutrality_guardrail_note: string;
  generated_by: string;
}

export interface CitizenLookupResponse {
  found: boolean;
  epic_id: string;
  current_status:
    | "ACTIVE_UNCHANGED"
    | "ACTIVE_MODIFIED"
    | "ACTIVE_BOOTH_TRANSFERRED"
    | "DELETED_IN_DRAFT_SUPPLEMENT"
    | "NOT_FOUND";
  latest_record: Record<string, string | number> | null;
  version_history: Record<string, string | number>[];
  plain_language_summary: Record<LanguageCode, string>;
  official_next_steps: Record<LanguageCode, string[]>;
  relevant_eci_forms: string[];
}

export interface CitizenAssistantResponse {
  language: LanguageCode;
  recognized_transcript: string | null;
  answer_text: string;
  confidence_level: number;
  reasoning_steps: string[];
  official_next_steps: string[];
  referenced_forms: string[];
  lookup_result: CitizenLookupResponse | null;
  tts_audio_base64: string | null;
  tts_mime_type: string | null;
  generated_by: string;
}

export interface GapAnalysisItem {
  id: number;
  capability: string;
  eronet_documented_status: string;
  internal_epistemic_limit: string;
  external_audit_gap: string;
  polltoll_wedge: string;
  is_prototype_core: boolean;
}
