import {
  AuditReceipt,
  CitizenAssistantResponse,
  ClaimCheckResponse,
  CorrectionEvent,
  GapAnalysisItem,
  LanguageCode,
  LedgerDiffResponse,
  SnapshotMeta,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API ${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchSnapshots(): Promise<SnapshotMeta[]> {
  return requestJson<SnapshotMeta[]>("/api/v1/snapshots");
}

export async function fetchAuditDiff(
  fromVersion: string,
  toVersion: string
): Promise<LedgerDiffResponse> {
  return requestJson<LedgerDiffResponse>(
    `/api/v1/audit/diff?from_version=${encodeURIComponent(fromVersion)}&to_version=${encodeURIComponent(toVersion)}&sample_limit=120`
  );
}

export async function appendReviewerCorrection(payload: {
  flag_id: string;
  reviewer_role: string;
  action:
    | "EVIDENCE_NOTE_ADDED"
    | "MARKED_EXPLAINED_ADMIN_SHIFT"
    | "ESCALATED_FOR_FIELD_CHECK";
  note: string;
  evidence_reference?: string;
}): Promise<CorrectionEvent> {
  return requestJson<CorrectionEvent>("/api/v1/assurance/corrections", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function generateSignedReceipt(
  fromVersion: string,
  toVersion: string
): Promise<AuditReceipt> {
  return requestJson<AuditReceipt>(
    `/api/v1/assurance/receipts/generate?from_version=${encodeURIComponent(fromVersion)}&to_version=${encodeURIComponent(toVersion)}`,
    { method: "POST" }
  );
}

export async function queryCitizenAssistant(payload: {
  query: string;
  epic_id?: string;
  language: LanguageCode;
  audio_base64?: string;
  audio_mime_type?: string;
  include_tts?: boolean;
  use_llm?: boolean;
}): Promise<CitizenAssistantResponse> {
  return requestJson<CitizenAssistantResponse>("/api/v1/verify/assistant", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function checkViralClaim(payload: {
  claim_text: string;
  from_version: string;
  to_version: string;
  language: LanguageCode;
  use_llm?: boolean;
}): Promise<ClaimCheckResponse> {
  return requestJson<ClaimCheckResponse>("/api/v1/verify/claim-check", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchQuotaStats(): Promise<{
  configured_key_count: number;
  keys_ready: number;
  keys_in_cooldown: number;
  gemini_key_count?: number;
  gemini_keys_ready?: number;
  groq_key_count?: number;
  groq_keys_ready?: number;
  provider_priority?: string;
  model_cascade: string[];
  groq_model_cascade?: string[];
  cached_entries_in_duckdb: number;
  metrics: {
    live_gemini_calls: number;
    live_groq_calls?: number;
    cache_hits_saved: number;
    deterministic_fastpath_saved: number;
    rate_limit_rotations: number;
  };
  free_tier_protections: string[];
}> {
  return requestJson("/api/v1/infra/quota");
}

export async function fetchGapAnalysis(): Promise<GapAnalysisItem[]> {
  return requestJson<GapAnalysisItem[]>("/api/v1/gap-analysis");
}

export async function ingestSnapshot(payload: {
  version_id: string;
  label: string;
  base_version_id: string | null;
  csv_payload: string;
}): Promise<SnapshotMeta> {
  return requestJson<SnapshotMeta>("/api/v1/ingest/snapshot", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
