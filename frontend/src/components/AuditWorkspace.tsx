"use client";

import React, { useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowRightLeft,
  CheckCircle2,
  FileSearch,
  GitCompare,
  HelpCircle,
  Layers,
  MessageSquarePlus,
  Scale,
  ShieldCheck,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { appendReviewerCorrection } from "@/lib/api";
import {
  AnomalyFlag,
  ChangeType,
  LedgerDiffResponse,
  SnapshotMeta,
} from "@/lib/types";

interface Props {
  snapshots: SnapshotMeta[];
  fromVersion: string;
  toVersion: string;
  onChangeVersions: (fromV: string, toV: string) => void;
  diffData: LedgerDiffResponse | null;
  loading: boolean;
  onInspectEpicInVerify: (epicId: string) => void;
  onRefreshDiff: () => void;
}

export default function AuditWorkspace({
  snapshots,
  fromVersion,
  toVersion,
  onChangeVersions,
  diffData,
  loading,
  onInspectEpicInVerify,
  onRefreshDiff,
}: Props) {
  const [selectedFlagId, setSelectedFlagId] = useState<string | null>(null);
  const [ledgerFilter, setLedgerFilter] = useState<"ALL" | ChangeType>("ALL");
  const [reviewerRole, setReviewerRole] = useState(
    "Independent Civic Observer"
  );
  const [reviewAction, setReviewAction] = useState<
    | "EVIDENCE_NOTE_ADDED"
    | "MARKED_EXPLAINED_ADMIN_SHIFT"
    | "ESCALATED_FOR_FIELD_CHECK"
  >("EVIDENCE_NOTE_ADDED");
  const [reviewNote, setReviewNote] = useState("");
  const [reviewRef, setReviewRef] = useState("");
  const [savingNote, setSavingNote] = useState(false);
  const [noteSavedBanner, setNoteSavedBanner] = useState<string | null>(null);

  const selectedFlag: AnomalyFlag | null = useMemo(() => {
    if (!diffData || diffData.flags.length === 0) return null;
    return (
      diffData.flags.find((f) => f.flag_id === selectedFlagId) ||
      diffData.flags[0]
    );
  }, [diffData, selectedFlagId]);

  const chartData = useMemo(() => {
    if (!diffData) return [];
    return diffData.booth_summaries.map((b) => ({
      booth: b.booth_id,
      rawDropPct: Number((b.raw_deletion_rate * 100).toFixed(2)),
      netDeletionPct: Number((b.net_effective_deletion_rate * 100).toFixed(2)),
      baselinePct: Number((b.historical_deletion_baseline * 100).toFixed(2)),
      ci95UpperPct: Number((b.deletion_ci_upper_95 * 100).toFixed(2)),
      added: b.added_count,
      deleted: b.deleted_count,
      transferredOut: b.transferred_out_count,
      modified: b.modified_count,
    }));
  }, [diffData]);

  const filteredEntries = useMemo(() => {
    if (!diffData) return [];
    if (ledgerFilter === "ALL") return diffData.sample_ledger_entries;
    return diffData.sample_ledger_entries.filter(
      (e) => e.change_type === ledgerFilter
    );
  }, [diffData, ledgerFilter]);

  async function handleAddAnnotation(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedFlag || reviewNote.trim().length < 5) return;
    setSavingNote(true);
    setNoteSavedBanner(null);
    try {
      const ev = await appendReviewerCorrection({
        flag_id: selectedFlag.flag_id,
        reviewer_role: reviewerRole,
        action: reviewAction,
        note: reviewNote.trim(),
        evidence_reference: reviewRef.trim() || undefined,
      });
      setReviewNote("");
      setReviewRef("");
      setNoteSavedBanner(
        `Appended immutable event ${ev.event_id} (SHA-256: ${ev.event_hash.slice(
          0,
          14
        )}...)`
      );
      onRefreshDiff();
    } catch (err) {
      setNoteSavedBanner(`Failed to log note: ${String(err)}`);
    } finally {
      setSavingNote(false);
    }
  }

  const severityBadge = (sev: AnomalyFlag["severity"]) => {
    if (sev === "HIGH_STATISTICAL_OUTLIER") {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-900 border border-amber-300">
          <AlertTriangle className="h-3 w-3" /> High Statistical Outlier
        </span>
      );
    }
    if (sev === "MODERATE_REVIEW") {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-sky-100 px-2.5 py-0.5 text-xs font-semibold text-sky-900 border border-sky-300">
          <FileSearch className="h-3 w-3" /> Moderate — Field Check
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-900 border border-emerald-300">
        <CheckCircle2 className="h-3 w-3" /> Reconciled Booth Split
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Snapshot Comparison Bar */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-indigo-700">
              <GitCompare className="h-4 w-4" />
              Electoral Change Ledger — Deterministic Snapshot Diff
            </div>
            <p className="mt-1 text-sm text-slate-600">
              Compares published roll versions row-by-row, reconciles cross-booth
              transfers, and tests net rates against 2024–2025 historical
              baselines.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500">
                Reference Roll (From)
              </label>
              <select
                value={fromVersion}
                onChange={(e) => onChangeVersions(e.target.value, toVersion)}
                className="mt-1 rounded-lg border border-slate-300 bg-slate-50 px-3 py-1.5 text-sm font-medium text-slate-900"
              >
                {snapshots.map((s) => (
                  <option
                    key={s.version_id}
                    value={s.version_id}
                    disabled={s.version_id === toVersion}
                  >
                    {s.version_id} ({s.publication_date})
                  </option>
                ))}
              </select>
            </div>
            <ArrowRightLeft className="mt-4 h-4 w-4 text-slate-400" />
            <div>
              <label className="block text-xs font-medium text-slate-500">
                Target Roll (To)
              </label>
              <select
                value={toVersion}
                onChange={(e) => onChangeVersions(fromVersion, e.target.value)}
                className="mt-1 rounded-lg border border-slate-300 bg-slate-50 px-3 py-1.5 text-sm font-medium text-slate-900"
              >
                {snapshots.map((s) => (
                  <option
                    key={s.version_id}
                    value={s.version_id}
                    disabled={s.version_id === fromVersion}
                  >
                    {s.version_id} ({s.publication_date})
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {diffData && (
          <div className="mt-4 grid grid-cols-1 gap-2 rounded-lg bg-slate-50 p-3 text-xs font-mono text-slate-600 md:grid-cols-2 border border-slate-200/80">
            <div className="truncate">
              <span className="font-semibold text-slate-800">
                {diffData.from_snapshot.version_id} SHA-256:
              </span>{" "}
              {diffData.from_snapshot.sha256}
            </div>
            <div className="truncate">
              <span className="font-semibold text-slate-800">
                {diffData.to_snapshot.version_id} SHA-256:
              </span>{" "}
              {diffData.to_snapshot.sha256}
            </div>
          </div>
        )}
      </div>

      {loading && !diffData ? (
        <div className="rounded-xl border border-slate-200 bg-white p-12 text-center text-sm text-slate-500">
          Computing deterministic DuckDB Electoral Change Ledger & 95% Wilson
          uncertainty bounds...
        </div>
      ) : diffData ? (
        <>
          {/* KPI Strip */}
          <div className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="text-xs font-medium text-slate-500">
                Reference Electors
              </div>
              <div className="mt-1 text-2xl font-bold text-slate-900">
                {diffData.totals.electors_from.toLocaleString()}
              </div>
              <div className="mt-1 text-xs text-slate-500">
                → {diffData.totals.electors_to.toLocaleString()} in target
              </div>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="text-xs font-medium text-slate-500">
                Additions (+)
              </div>
              <div className="mt-1 text-2xl font-bold text-indigo-700">
                +{diffData.totals.added.toLocaleString()}
              </div>
              <div className="mt-1 text-xs text-slate-500">
                Form-6 & supplement inclusions
              </div>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="text-xs font-medium text-slate-500">
                True Net Deletions (-)
              </div>
              <div className="mt-1 text-2xl font-bold text-amber-700">
                -{diffData.totals.deleted.toLocaleString()}
              </div>
              <div className="mt-1 text-xs text-slate-500">
                Absent across entire roll
              </div>
            </div>
            <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-4 shadow-sm">
              <div className="text-xs font-semibold text-emerald-800">
                Reconciled Booth Splits
              </div>
              <div className="mt-1 text-2xl font-bold text-emerald-700">
                {diffData.totals.booth_transferred.toLocaleString()}
              </div>
              <div className="mt-1 text-xs text-emerald-800/80">
                Active EPICs moved PS-109 → PS-110
              </div>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="text-xs font-medium text-slate-500">
                Field Modifications (Δ)
              </div>
              <div className="mt-1 text-2xl font-bold text-slate-800">
                {diffData.totals.modified.toLocaleString()}
              </div>
              <div className="mt-1 text-xs text-slate-500">
                Address, spelling, or age edits
              </div>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="text-xs font-medium text-slate-500">
                Triggered Audit Rules
              </div>
              <div className="mt-1 text-2xl font-bold text-slate-900">
                {diffData.flags.length}
              </div>
              <div className="mt-1 text-xs text-slate-500">
                With 95% CIs & missing-evidence list
              </div>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-900">
                Raw Booth Outflow vs. Reconciled Net Deletion Rate & Historical
                Baseline (%)
              </h3>
              <p className="mt-0.5 text-xs text-slate-500">
                Notice PS-109: 36.2% raw drop collapses to 0.21% net deletion
                once 338 transfers to PS-110 are reconciled—whereas PS-104 &
                PS-302 exceed historical baselines even at 95% confidence bounds.
              </p>
              <div className="mt-4 h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="booth" tick={{ fontSize: 11 }} />
                    <YAxis unit="%" tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar
                      dataKey="rawDropPct"
                      name="Raw Outflow %"
                      fill="#cbd5e1"
                      radius={[3, 3, 0, 0]}
                    />
                    <Bar
                      dataKey="netDeletionPct"
                      name="True Net Deletion %"
                      fill="#d97706"
                      radius={[3, 3, 0, 0]}
                    />
                    <Bar
                      dataKey="baselinePct"
                      name="2024–25 Historical Baseline %"
                      fill="#4f46e5"
                      radius={[3, 3, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-900">
                Booth-Wise Electoral Change Ledger Breakdown (Record Counts)
              </h3>
              <p className="mt-0.5 text-xs text-slate-500">
                Traceable decomposition into Additions, Cross-Booth Transfers,
                Modifications, and Net Deletions.
              </p>
              <div className="mt-4 h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="booth" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar
                      dataKey="added"
                      stackId="a"
                      name="Added"
                      fill="#4f46e5"
                    />
                    <Bar
                      dataKey="transferredOut"
                      stackId="a"
                      name="Transferred (Split)"
                      fill="#10b981"
                    />
                    <Bar
                      dataKey="modified"
                      stackId="a"
                      name="Modified"
                      fill="#0ea5e9"
                    />
                    <Bar
                      dataKey="deleted"
                      stackId="a"
                      name="Net Deleted"
                      fill="#f59e0b"
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Master-Detail Anomaly Flags & 5-Part Evidence Inspector */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
            <div className="lg:col-span-5 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-700">
                  Statistical & Ledger Review Queue ({diffData.flags.length})
                </h3>
                <span className="text-xs text-slate-500">
                  Select flag to inspect 5-part brief
                </span>
              </div>
              {diffData.flags.map((flg) => {
                const active = selectedFlag?.flag_id === flg.flag_id;
                return (
                  <button
                    key={flg.flag_id}
                    onClick={() => setSelectedFlagId(flg.flag_id)}
                    className={`w-full text-left rounded-xl border p-4 transition-all ${
                      active
                        ? "border-indigo-600 bg-indigo-50/40 ring-1 ring-indigo-600 shadow-sm"
                        : "border-slate-200 bg-white hover:border-slate-300"
                    }`}
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      {severityBadge(flg.severity)}
                      <span className="font-mono text-xs text-slate-500">
                        {flg.booth_id} • {flg.rule_id}@{flg.rule_version}
                      </span>
                    </div>
                    <div className="mt-2 text-sm font-semibold text-slate-900">
                      {flg.headline}
                    </div>
                    <div className="mt-2 flex items-center justify-between text-xs text-slate-600">
                      <span>
                        Affected:{" "}
                        <strong>{flg.affected_records_count}</strong> records
                      </span>
                      <span>
                        Confidence:{" "}
                        <strong>
                          {(flg.explanation.confidence_level * 100).toFixed(0)}%
                        </strong>{" "}
                        • Status:{" "}
                        <span className="font-medium text-indigo-700">
                          {flg.review_status.replaceAll("_", " ")}
                        </span>
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* 5-Part Evidence Inspector */}
            <div className="lg:col-span-7">
              {selectedFlag && (
                <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-5">
                  <div className="border-b border-slate-200 pb-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      {severityBadge(selectedFlag.severity)}
                      <span className="font-mono text-xs text-slate-500">
                        Flag ID: {selectedFlag.flag_id}
                      </span>
                    </div>
                    <h3 className="mt-2 text-lg font-bold text-slate-900">
                      {selectedFlag.headline}
                    </h3>
                    <p className="mt-1 text-xs text-slate-500">
                      {selectedFlag.constituency_id} —{" "}
                      {selectedFlag.constituency_name} • {selectedFlag.booth_name}
                    </p>
                  </div>

                  {/* Uncertainty Box */}
                  <div className="rounded-lg border border-indigo-200 bg-indigo-50/50 p-4">
                    <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-indigo-900">
                      <span className="flex items-center gap-1.5">
                        <Scale className="h-4 w-4" /> Statistical Baseline &
                        Uncertainty Disclosure
                      </span>
                      <span>
                        Sample Size n ={" "}
                        {selectedFlag.uncertainty.sample_size.toLocaleString()}
                      </span>
                    </div>
                    <div className="mt-2 grid grid-cols-2 gap-3 sm:grid-cols-4 text-xs">
                      <div className="rounded bg-white p-2 border border-indigo-100">
                        <div className="text-slate-500">Observed Metric</div>
                        <div className="font-mono text-sm font-bold text-slate-900">
                          {(
                            selectedFlag.uncertainty.point_estimate * 100
                          ).toFixed(2)}
                          %
                        </div>
                      </div>
                      <div className="rounded bg-white p-2 border border-indigo-100">
                        <div className="text-slate-500">95% Wilson CI</div>
                        <div className="font-mono text-sm font-bold text-slate-900">
                          [
                          {(
                            selectedFlag.uncertainty.ci_lower_95 * 100
                          ).toFixed(1)}
                          %,{" "}
                          {(
                            selectedFlag.uncertainty.ci_upper_95 * 100
                          ).toFixed(1)}
                          %]
                        </div>
                      </div>
                      <div className="rounded bg-white p-2 border border-indigo-100">
                        <div className="text-slate-500">2024–25 Baseline</div>
                        <div className="font-mono text-sm font-bold text-slate-900">
                          {(
                            selectedFlag.uncertainty.historical_baseline_mean *
                            100
                          ).toFixed(2)}
                          %
                        </div>
                      </div>
                      <div className="rounded bg-white p-2 border border-indigo-100">
                        <div className="text-slate-500">Z-Score Deviation</div>
                        <div className="font-mono text-sm font-bold text-indigo-700">
                          {selectedFlag.uncertainty.z_score >= 0 ? "+" : ""}
                          {selectedFlag.uncertainty.z_score}σ
                        </div>
                      </div>
                    </div>
                    <p className="mt-2 text-xs text-indigo-950/80">
                      {selectedFlag.uncertainty.uncertainty_note}
                    </p>
                  </div>

                  {/* 5-Part Structured Brief */}
                  <div className="space-y-4 text-sm">
                    <div>
                      <h4 className="font-semibold text-slate-900">
                        1. What Changed (Ledger Evidence)
                      </h4>
                      <p className="mt-1 text-slate-700">
                        {selectedFlag.explanation.what_changed}
                      </p>
                      <div className="mt-2 flex flex-wrap items-center gap-1.5">
                        <span className="text-xs text-slate-500">
                          Trace sample EPICs:
                        </span>
                        {selectedFlag.sample_epic_ids.map((ep) => (
                          <button
                            key={ep}
                            onClick={() => onInspectEpicInVerify(ep)}
                            className="rounded bg-slate-100 px-2 py-0.5 font-mono text-xs text-indigo-700 hover:bg-indigo-100"
                            title="Inspect longitudinal citizen record"
                          >
                            {ep} ↗
                          </button>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold text-slate-900">
                        2. Exact Deterministic Rule Triggered
                      </h4>
                      <p className="mt-1 text-slate-700">
                        {selectedFlag.explanation.rule_triggered}
                      </p>
                      <code className="mt-1 block rounded bg-slate-900 px-3 py-1.5 text-xs text-emerald-300 font-mono">
                        {selectedFlag.rule_formula}
                      </code>
                    </div>

                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                      <div className="rounded-lg border border-emerald-200 bg-emerald-50/40 p-3.5">
                        <h4 className="font-semibold text-emerald-950 flex items-center gap-1.5 text-xs uppercase tracking-wide">
                          <ShieldCheck className="h-4 w-4 text-emerald-700" />
                          3. Innocent / Administrative Explanations
                        </h4>
                        <ul className="mt-2 list-disc space-y-1.5 pl-4 text-xs text-slate-700">
                          {selectedFlag.explanation.innocent_explanations.map(
                            (it, i) => (
                              <li key={i}>{it}</li>
                            )
                          )}
                        </ul>
                      </div>

                      <div className="rounded-lg border border-sky-200 bg-sky-50/40 p-3.5">
                        <h4 className="font-semibold text-sky-950 flex items-center gap-1.5 text-xs uppercase tracking-wide">
                          <HelpCircle className="h-4 w-4 text-sky-700" />
                          4. Missing Evidence (Not in Public PDFs)
                        </h4>
                        <ul className="mt-2 list-disc space-y-1.5 pl-4 text-xs text-slate-700">
                          {selectedFlag.explanation.missing_evidence.map(
                            (it, i) => (
                              <li key={i}>{it}</li>
                            )
                          )}
                        </ul>
                      </div>
                    </div>

                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3.5">
                      <h4 className="font-semibold text-slate-900 text-xs uppercase tracking-wide">
                        5. Next Non-Partisan Verification Step
                      </h4>
                      <p className="mt-1 text-xs text-slate-700">
                        {selectedFlag.explanation.next_verification_step}
                      </p>
                      <div className="mt-2 border-t border-slate-200 pt-2 text-xs text-slate-500">
                        <strong>Confidence Calibration (
                        {(selectedFlag.explanation.confidence_level * 100).toFixed(
                          0
                        )}
                        %):</strong>{" "}
                        {selectedFlag.explanation.confidence_basis}
                      </div>
                    </div>
                  </div>

                  {/* Append-Only Reviewer Correction Form */}
                  <form
                    onSubmit={handleAddAnnotation}
                    className="rounded-lg border border-slate-200 bg-slate-50/70 p-4 space-y-3"
                  >
                    <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-800">
                      <MessageSquarePlus className="h-4 w-4 text-indigo-600" />
                      Append Reviewer Finding to Hash-Chained Audit Log
                    </div>
                    <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                      <input
                        type="text"
                        value={reviewerRole}
                        onChange={(e) => setReviewerRole(e.target.value)}
                        placeholder="Reviewer role / org"
                        className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs"
                      />
                      <select
                        value={reviewAction}
                        onChange={(e) =>
                          setReviewAction(
                            e.target.value as typeof reviewAction
                          )
                        }
                        className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs"
                      >
                        <option value="EVIDENCE_NOTE_ADDED">
                          Attach Documentary Note
                        </option>
                        <option value="MARKED_EXPLAINED_ADMIN_SHIFT">
                          Mark Explained by Admin Order
                        </option>
                        <option value="ESCALATED_FOR_FIELD_CHECK">
                          Request Authorized BLO/ERO Check
                        </option>
                      </select>
                    </div>
                    <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                      <input
                        type="text"
                        value={reviewNote}
                        onChange={(e) => setReviewNote(e.target.value)}
                        placeholder="Enter factual verification note (min 5 chars, never overwrites original flag)..."
                        className="sm:col-span-2 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs"
                      />
                      <input
                        type="text"
                        value={reviewRef}
                        onChange={(e) => setReviewRef(e.target.value)}
                        placeholder="Doc ref (e.g. Gazette #14)"
                        className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-mono"
                      />
                    </div>
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[11px] text-slate-500">
                        Appends SHA-256 hash-linked entry included in signed
                        PollToll Assurance receipts.
                      </span>
                      <button
                        type="submit"
                        disabled={savingNote || reviewNote.trim().length < 5}
                        className="rounded-lg bg-indigo-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
                      >
                        {savingNote ? "Logging..." : "Append to Ledger"}
                      </button>
                    </div>
                    {noteSavedBanner && (
                      <div className="rounded bg-emerald-100 px-3 py-1.5 text-xs font-mono text-emerald-900">
                        {noteSavedBanner}
                      </div>
                    )}
                  </form>
                </div>
              )}
            </div>
          </div>

          {/* Traceable Electoral Change Ledger Sample Table */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                  <Layers className="h-4 w-4 text-indigo-600" />
                  Source-Linked Electoral Change Ledger Records
                </h3>
                <p className="text-xs text-slate-500">
                  Every row links to exact Reference & Target snapshot SHA-256s,
                  polling station part, serial number, and supplement batch.
                </p>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {(
                  [
                    "ALL",
                    "BOOTH_TRANSFERRED",
                    "DELETED",
                    "MODIFIED",
                    "ADDED",
                  ] as const
                ).map((t) => (
                  <button
                    key={t}
                    onClick={() => setLedgerFilter(t)}
                    className={`rounded-lg px-2.5 py-1 text-xs font-medium ${
                      ledgerFilter === t
                        ? "bg-slate-900 text-white"
                        : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                    }`}
                  >
                    {t.replace("_", " ")}
                  </button>
                ))}
              </div>
            </div>

            <div className="mt-4 overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
                <thead className="bg-slate-50 font-semibold text-slate-600">
                  <tr>
                    <th className="px-3 py-2">Ledger ID</th>
                    <th className="px-3 py-2">Synthetic EPIC</th>
                    <th className="px-3 py-2">Elector (Synth)</th>
                    <th className="px-3 py-2">Change Classification</th>
                    <th className="px-3 py-2">Booth / Serial Lineage</th>
                    <th className="px-3 py-2">Field Delta</th>
                    <th className="px-3 py-2">Supplement Source Ref</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {filteredEntries.slice(0, 25).map((row) => (
                    <tr key={row.ledger_id} className="hover:bg-slate-50">
                      <td className="px-3 py-2 font-mono text-slate-500">
                        {row.ledger_id}
                      </td>
                      <td className="px-3 py-2">
                        <button
                          onClick={() => onInspectEpicInVerify(row.epic_id)}
                          className="font-mono font-semibold text-indigo-700 hover:underline"
                        >
                          {row.epic_id}
                        </button>
                      </td>
                      <td className="px-3 py-2 text-slate-800">
                        {row.elector_name}
                      </td>
                      <td className="px-3 py-2">
                        <span
                          className={`inline-block rounded px-2 py-0.5 font-semibold ${
                            row.change_type === "BOOTH_TRANSFERRED"
                              ? "bg-emerald-100 text-emerald-900"
                              : row.change_type === "DELETED"
                              ? "bg-amber-100 text-amber-900"
                              : row.change_type === "MODIFIED"
                              ? "bg-sky-100 text-sky-900"
                              : "bg-indigo-100 text-indigo-900"
                          }`}
                        >
                          {row.change_type}
                        </span>
                      </td>
                      <td className="px-3 py-2 font-mono text-slate-600">
                        {row.from_booth_id
                          ? `${row.from_booth_id}#${row.from_serial_no}`
                          : "—"}{" "}
                        →{" "}
                        {row.to_booth_id
                          ? `${row.to_booth_id}#${row.to_serial_no}`
                          : "—"}
                      </td>
                      <td className="px-3 py-2 font-mono text-slate-600">
                        {Object.keys(row.modified_fields).length > 0
                          ? JSON.stringify(row.modified_fields)
                          : row.age_before && row.age_after
                          ? `age ${row.age_before}→${row.age_after}`
                          : row.house_no}
                      </td>
                      <td className="px-3 py-2 font-mono text-slate-500">
                        {row.supplement_ref}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : null}
    </div>
  );
}
