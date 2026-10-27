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

// Default to same-origin `/api/v1/*` proxied via Next.js rewrites (immune to browser extensions, CORS, and localhost/127.0.0.1 splits)
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "";

function xhrFallback<T>(url: string, init?: RequestInit): Promise<T> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open(init?.method || "GET", url, true);
    if (init?.body) {
      xhr.setRequestHeader("Content-Type", "application/json");
    }
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText) as T);
        } catch (err) {
          reject(err);
        }
      } else {
        reject(new Error(`API ${xhr.status}: ${xhr.responseText}`));
      }
    };
    xhr.onerror = () => reject(new Error("Network request failed"));
    xhr.send(typeof init?.body === "string" ? init.body : null);
  });
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const headers: Record<string, string> = {
    Accept: "application/json",
  };
  if (init?.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  try {
    const res = await fetch(url, {
      ...init,
      headers: {
        ...headers,
        ...((init?.headers as Record<string, string>) || {}),
      },
      cache: "no-store",
    });
    if (!res.ok) {
      const detail = await res.text();
      throw new Error(`API ${res.status}: ${detail}`);
    }
    return res.json() as Promise<T>;
  } catch (err) {
    // Bypass broken browser extension `window.fetch` interceptors (e.g. Urban VPN `requests.js`)
    if (typeof XMLHttpRequest !== "undefined" && err instanceof TypeError) {
      return xhrFallback<T>(url, init);
    }
    throw err;
  }
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
    { method: "POST", body: "{}" }
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
