"use client";

import React, { useEffect, useState } from "react";
import {
  CheckCircle2,
  Code2,
  DatabaseZap,
  Gauge,
  Server,
  Terminal,
  UploadCloud,
} from "lucide-react";
import { fetchQuotaStats, ingestSnapshot } from "@/lib/api";
import { fmt, getDict } from "@/lib/locales/common";
import { INFRA_LOCALE } from "@/lib/locales/infra";
import { LanguageCode, SnapshotMeta } from "@/lib/types";

interface Props {
  language: LanguageCode;
  snapshots: SnapshotMeta[];
  onSnapshotIngested: (newSnap: SnapshotMeta) => void;
}

const DEFAULT_CSV = `action,epic_id,booth_id,elector_name,relation_name,gender,age,house_no,reason_code
ADD,SYN-GJ-101-9901,PS-101,Devansh K. Joshi,Kiritbhai Joshi,M,22,H-14/A,A_FORM6
ADD,SYN-GJ-101-9902,PS-101,Meenaben R. Joshi,Kiritbhai Joshi,F,48,H-14/A,A_FORM6
MODIFY,SYN-GJ-207-0011,PS-207,Kavita R. Shah,Karsanbhai Shah,F,40,H-71,M_FORM8_AGE_FIX
DELETE,SYN-GJ-305-8800,PS-305,Maheshbhai K. Patel,Karsanbhai Patel,M,38,H-18,D_DUP_RESOLVED`;

export default function InfraConsole({
  language,
  snapshots,
  onSnapshotIngested,
}: Props) {
  const infraT = getDict(INFRA_LOCALE, language);

  const [versionId, setVersionId] = useState("v2026_final_rc1");
  const [label, setLabel] = useState(infraT.defaultPubLabel);
  const [baseVersion, setBaseVersion] = useState("v2026_draft");
  const [csvPayload, setCsvPayload] = useState(DEFAULT_CSV);
  const [ingesting, setIngesting] = useState(false);
  const [ingestedMeta, setIngestedMeta] = useState<SnapshotMeta | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [quota, setQuota] = useState<Awaited<
    ReturnType<typeof fetchQuotaStats>
  > | null>(null);

  useEffect(() => {
    setLabel(infraT.defaultPubLabel);
  }, [infraT.defaultPubLabel]);

  useEffect(() => {
    void fetchQuotaStats()
      .then(setQuota)
      .catch(() => {});
  }, []);

  async function handleIngest(e: React.FormEvent) {
    e.preventDefault();
    setIngesting(true);
    setErrorMsg(null);
    setIngestedMeta(null);
    try {
      const snap = await ingestSnapshot({
        version_id: versionId.trim(),
        label: label.trim(),
        base_version_id: baseVersion || null,
        csv_payload: csvPayload,
      });
      setIngestedMeta(snap);
      onSnapshotIngested(snap);
    } catch (err) {
      setErrorMsg(String(err));
    } finally {
      setIngesting(false);
    }
  }

  return (
    <div className="space-y-8">
      {/* Infrastructure Overview Strip */}
      {quota && (
        <div className="rounded-xl border border-indigo-200 bg-indigo-50/40 p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase text-indigo-800">
              <Gauge className="h-4 w-4" /> {infraT.quotaShieldTitle}
            </div>
            <span className="rounded bg-slate-900 px-2.5 py-0.5 font-mono text-xs text-emerald-300">
              Cascade: {quota.model_cascade.join(" → ")}
            </span>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4 text-xs">
            <div className="rounded-lg border border-indigo-100 bg-white p-3">
              <div className="text-slate-500">
                {infraT.keyPoolLabel}
              </div>
              <div className="mt-0.5 font-mono text-base font-bold text-slate-900">
                {quota.gemini_keys_ready ?? quota.keys_ready}/
                {quota.gemini_key_count ?? quota.configured_key_count} Gem •{" "}
                {quota.groq_keys_ready ?? 0}/{quota.groq_key_count ?? 0} Groq
              </div>
            </div>
            <div className="rounded-lg border border-indigo-100 bg-white p-3">
              <div className="text-slate-500">{infraT.cacheHitsLabel}</div>
              <div className="mt-0.5 font-mono text-base font-bold text-emerald-700">
                {quota.metrics.cache_hits_saved} ({quota.cached_entries_in_duckdb}{" "}
                stored)
              </div>
            </div>
            <div className="rounded-lg border border-indigo-100 bg-white p-3">
              <div className="text-slate-500">{infraT.fastpathLabel}</div>
              <div className="mt-0.5 font-mono text-base font-bold text-indigo-700">
                {quota.metrics.deterministic_fastpath_saved}
              </div>
            </div>
            <div className="rounded-lg border border-indigo-100 bg-white p-3">
              <div className="text-slate-500">{infraT.liveCallsLabel}</div>
              <div className="mt-0.5 font-mono text-base font-bold text-slate-900">
                {quota.metrics.live_gemini_calls} /{" "}
                {quota.metrics.live_groq_calls ?? 0}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase text-indigo-700">
            <DatabaseZap className="h-4 w-4" /> {infraT.card1Tag}
          </div>
          <div className="mt-2 text-sm font-semibold text-slate-900">
            {infraT.card1Title}
          </div>
          <p className="mt-1 text-xs text-slate-600">
            {infraT.card1Desc}
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase text-indigo-700">
            <Terminal className="h-4 w-4" /> {infraT.card2Tag}
          </div>
          <div className="mt-2 text-sm font-semibold text-slate-900">
            {infraT.card2Title}
          </div>
          <p className="mt-1 text-xs text-slate-600">
            {infraT.card2Desc}
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase text-indigo-700">
            <Server className="h-4 w-4" /> {infraT.card3Tag}
          </div>
          <div className="mt-2 text-sm font-semibold text-slate-900">
            {infraT.card3Title}
          </div>
          <p className="mt-1 text-xs text-slate-600">
            {infraT.card3Desc}
          </p>
        </div>
      </div>

      {/* Live Snapshot Ingestion Pipeline */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-indigo-700">
            <UploadCloud className="h-4 w-4" />
            {infraT.pipelineTag}
          </div>
          <h2 className="mt-1 text-lg font-bold text-slate-900">
            {infraT.pipelineTitle}
          </h2>
          <p className="text-sm text-slate-600">
            {infraT.pipelineSubtitle}
          </p>
        </div>

        <form onSubmit={handleIngest} className="space-y-4">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700">
                {infraT.idLabel}
              </label>
              <input
                type="text"
                value={versionId}
                onChange={(e) => setVersionId(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-xs font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700">
                {infraT.baseLabel}
              </label>
              <select
                value={baseVersion}
                onChange={(e) => setBaseVersion(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 text-xs font-mono"
              >
                {snapshots.map((s) => (
                  <option key={s.version_id} value={s.version_id}>
                    {s.label || s.version_id} ({s.total_electors.toLocaleString()} {infraT.rowsSuffix})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700">
                {infraT.pubLabel}
              </label>
              <input
                type="text"
                value={label}
                onChange={(e) => setLabel(e.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-xs"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700">
              {infraT.csvLabel}
            </label>
            <textarea
              rows={5}
              value={csvPayload}
              onChange={(e) => setCsvPayload(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-300 bg-slate-950 p-3 font-mono text-xs text-emerald-300"
            />
          </div>

          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-500">
              {infraT.guardrailText}
            </span>
            <button
              type="submit"
              disabled={ingesting}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {ingesting
                ? infraT.ingestingBtn
                : infraT.ingestBtn}
            </button>
          </div>
        </form>

        {ingestedMeta && (
          <div className="rounded-xl border border-emerald-300 bg-emerald-50 p-4 text-xs space-y-1">
            <div className="flex items-center gap-1.5 font-bold text-emerald-950">
              <CheckCircle2 className="h-4 w-4 text-emerald-700" />
              {fmt(infraT.successTitle, { id: ingestedMeta.version_id })}
            </div>
            <div className="font-mono text-emerald-900">
              {fmt(infraT.successSha, { sha: ingestedMeta.sha256 })}
            </div>
            <div className="text-emerald-800">
              {fmt(infraT.successDetails, {
                total: ingestedMeta.total_electors.toLocaleString(),
                booths: ingestedMeta.booth_count,
              })}
            </div>
          </div>
        )}

        {errorMsg && (
          <div className="rounded-xl border border-rose-300 bg-rose-50 p-3 text-xs font-mono text-rose-900">
            {errorMsg}
          </div>
        )}
      </div>

      {/* Headless CLI & Programmatic REST SDK Snippets */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-3">
          <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase text-slate-700">
            <Terminal className="h-4 w-4 text-indigo-600" />
            {infraT.cliTitle}
          </div>
          <pre className="overflow-x-auto rounded-lg bg-slate-950 p-4 font-mono text-xs text-slate-200 leading-relaxed">
{`# 1. List content-addressed snapshots & SHA-256 digests
cd backend && uv run python polltoll_cli.py snapshots

# 2. Run deterministic Electoral Change Ledger & Wilson 95% CIs
uv run python polltoll_cli.py diff --from v2025_final --to v2026_draft

# 3. Issue tamper-evident Ed25519 Audit Receipt bundle
uv run python polltoll_cli.py sign-receipt --out audit.receipt.json

# 4. Offline cryptographic verification (exit code 2 on tamper)
uv run python polltoll_cli.py verify-receipt audit.receipt.json`}
          </pre>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-3">
          <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase text-slate-700">
            <Code2 className="h-4 w-4 text-indigo-600" />
            {infraT.apiTitle}
          </div>
          <pre className="overflow-x-auto rounded-lg bg-slate-950 p-4 font-mono text-xs text-slate-200 leading-relaxed">
{`# Query Electoral Change Ledger + Versioned Rules
curl -s "http://127.0.0.1:8000/api/v1/audit/diff?from_version=v2025_final&to_version=v2026_draft" | jq .totals

# Audit a viral social-media allegation in Gujarati
curl -s -X POST "http://127.0.0.1:8000/api/v1/verify/claim-check" \\
  -H "Content-Type: application/json" \\
  -d '{"claim_text":"બૂથ PS-109 માંથી 340 મતદારો ગાયબ!","language":"gu"}'

# Inspect response protocol telemetry headers
curl -I "http://127.0.0.1:8000/api/v1/health"`}
          </pre>
        </div>
      </div>
    </div>
  );
}
