"use client";

import React, { useEffect, useMemo, useState } from "react";
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
import {
  appendReviewerCorrection,
  getReviewerKey,
  readableApiError,
  setReviewerKey,
} from "@/lib/api";
import { SHELL_LOCALE } from "@/lib/locales/shell";
import {
  CHANGE_TYPE_LABELS,
  fmt,
  getDict,
  REVIEW_STATUS_LABELS,
  SEVERITY_LABELS,
} from "@/lib/locales/common";
import { AUDIT_LOCALE } from "@/lib/locales/audit";
import {
  AnomalyFlag,
  ChangeType,
  LanguageCode,
  LedgerDiffResponse,
  SnapshotMeta,
} from "@/lib/types";
import { ticks } from "@/lib/ticks";

interface Props {
  language: LanguageCode;
  snapshots: SnapshotMeta[];
  fromVersion: string;
  toVersion: string;
  onChangeVersions: (fromV: string, toV: string) => void;
  diffData: LedgerDiffResponse | null;
  loading: boolean;
  onInspectEpicInVerify: (epicId: string) => void;
  onRefreshDiff: () => void;
  /** Which part of the workspace the sidebar section shows. */
  section?: "comparison" | "flags" | "review";
  selectedFlagId?: string | null;
  onSelectFlag?: (id: string) => void;
  onOpenReview?: (id: string) => void;
  openReviewLabel?: string;
}

export default function AuditWorkspace({
  language,
  snapshots,
  fromVersion,
  toVersion,
  onChangeVersions,
  diffData,
  loading,
  onInspectEpicInVerify,
  onRefreshDiff,
  section = "flags",
  selectedFlagId: controlledFlagId,
  onSelectFlag,
  onOpenReview,
  openReviewLabel,
}: Props) {
  const showCompare = section === "comparison";
  const showInspector = section === "flags";
  const showReview = section === "review";
  const auditT = getDict(AUDIT_LOCALE, language);
  const changeLabels = getDict(CHANGE_TYPE_LABELS, language);
  const sevLabels = getDict(SEVERITY_LABELS, language);
  const revStatusLabels = getDict(REVIEW_STATUS_LABELS, language);

  const [localFlagId, setLocalFlagId] = useState<string | null>(null);
  const selectedFlagId = controlledFlagId !== undefined ? controlledFlagId : localFlagId;
  const setSelectedFlagId = (id: string) => {
    setLocalFlagId(id);
    onSelectFlag?.(id);
  };
  const [ledgerFilter, setLedgerFilter] = useState<"ALL" | ChangeType>("ALL");
  const [reviewerRole, setReviewerRole] = useState(
    language === "hi"
      ? "स्वतंत्र नागरिक पर्यवेक्षक"
      : language === "gu"
      ? "સ્વતંત્ર નાગરિક નિરીક્ષક"
      : "Independent Civic Observer"
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
  const [noteError, setNoteError] = useState(false);
  const [reviewerKey, setReviewerKeyState] = useState("");
  const shellT = getDict(SHELL_LOCALE, language);
  useEffect(() => {
    setReviewerKeyState(getReviewerKey());
  }, []);

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
    setNoteError(false);
    setReviewerKey(reviewerKey.trim());
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
        fmt(auditT.formSuccessAppended, {
          id: ev.event_id,
          hash: ev.event_hash.slice(0, 14),
        })
      );
      onRefreshDiff();
    } catch (err) {
      setNoteError(true);
      setNoteSavedBanner(
        fmt(auditT.formErrorFailed, { error: readableApiError(err) })
      );
    } finally {
      setSavingNote(false);
    }
  }

  const severityBadge = (sev: AnomalyFlag["severity"]) => {
    const text = sevLabels[sev] || sev;
    if (sev === "HIGH_STATISTICAL_OUTLIER") {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-900 border border-amber-300">
          <AlertTriangle className="h-3 w-3" /> {text}
        </span>
      );
    }
    if (sev === "MODERATE_REVIEW") {
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-sky-100 px-2.5 py-0.5 text-xs font-semibold text-sky-900 border border-sky-300">
          <FileSearch className="h-3 w-3" /> {text}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-900 border border-emerald-300">
        <CheckCircle2 className="h-3 w-3" /> {text}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Snapshot Comparison Bar (roll pickers now live in the page header) */}
      {showCompare && (
      <div className="rounded-[20px] bg-white p-5 shadow-sheet">
        <div className="hidden flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2 text-xs font-semiboldr text-ink-700">
              <GitCompare className="h-4 w-4" />
              {auditT.diffTitle}
            </div>
            <p className="mt-1 text-sm text-slate-600">
              {auditT.diffSubtitle}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-500">
                {auditT.refRollLabel}
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
                    {s.label || s.version_id} ({s.publication_date})
                  </option>
                ))}
              </select>
            </div>
            <ArrowRightLeft className="mt-4 h-4 w-4 text-slate-400" />
            <div>
              <label className="block text-xs font-medium text-slate-500">
                {auditT.targetRollLabel}
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
                    {s.label || s.version_id} ({s.publication_date})
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
                {diffData.from_snapshot.label || diffData.from_snapshot.version_id} SHA-256:
              </span>{" "}
              {diffData.from_snapshot.sha256}
            </div>
            <div className="truncate">
              <span className="font-semibold text-slate-800">
                {diffData.to_snapshot.label || diffData.to_snapshot.version_id} SHA-256:
              </span>{" "}
              {diffData.to_snapshot.sha256}
            </div>
          </div>
        )}
      </div>
      )}

      {loading && !diffData ? (
        <div className="rounded-[20px] bg-white p-12 shadow-sheet text-center text-sm text-slate-500">
          {auditT.loadingLedger}
        </div>
      ) : diffData ? (
        <>
          {/* KPI Strip (shown on the Dashboard instead) */}
          <div className="hidden">
            <div className="rounded-[20px] bg-white p-4 shadow-sheet">
              <div className="text-xs font-medium text-slate-500">
                {auditT.kpiRefElectors}
              </div>
              <div className="mt-1 text-2xl font-bold text-slate-900">
                {diffData.totals.electors_from.toLocaleString()}
              </div>
              <div className="mt-1 text-xs text-slate-500">
                {fmt(auditT.kpiInTarget, { count: diffData.totals.electors_to.toLocaleString() })}
              </div>
            </div>
            <div className="rounded-[20px] bg-white p-4 shadow-sheet">
              <div className="text-xs font-medium text-slate-500">
                {auditT.kpiAdditions}
              </div>
              <div className="mt-1 text-2xl font-bold text-ink-700">
                +{diffData.totals.added.toLocaleString()}
              </div>
              <div className="mt-1 text-xs text-slate-500">
                {auditT.kpiAdditionsSub}
              </div>
            </div>
            <div className="rounded-[20px] bg-white p-4 shadow-sheet">
              <div className="text-xs font-medium text-slate-500">
                {auditT.kpiDeletions}
              </div>
              <div className="mt-1 text-2xl font-bold text-amber-700">
                -{diffData.totals.deleted.toLocaleString()}
              </div>
              <div className="mt-1 text-xs text-slate-500">
                {auditT.kpiDeletionsSub}
              </div>
            </div>
            <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-4 shadow-sm">
              <div className="text-xs font-semibold text-emerald-800">
                {auditT.kpiSplits}
              </div>
              <div className="mt-1 text-2xl font-bold text-emerald-700">
                {diffData.totals.booth_transferred.toLocaleString()}
              </div>
              <div className="mt-1 text-xs text-emerald-800/80">
                {auditT.kpiSplitsSub}
              </div>
            </div>
            <div className="rounded-[20px] bg-white p-4 shadow-sheet">
              <div className="text-xs font-medium text-slate-500">
                {auditT.kpiModifications}
              </div>
              <div className="mt-1 text-2xl font-bold text-slate-800">
                {diffData.totals.modified.toLocaleString()}
              </div>
              <div className="mt-1 text-xs text-slate-500">
                {auditT.kpiModificationsSub}
              </div>
            </div>
            <div className="rounded-[20px] bg-white p-4 shadow-sheet">
              <div className="text-xs font-medium text-slate-500">
                {auditT.kpiRules}
              </div>
              <div className="mt-1 text-2xl font-bold text-slate-900">
                {diffData.flags.length}
              </div>
              <div className="mt-1 text-xs text-slate-500">
                {auditT.kpiRulesSub}
              </div>
            </div>
          </div>

          {/* Charts Row */}
          {showCompare && (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="rounded-[20px] bg-white p-5 shadow-sheet">
              <h3 className="text-sm font-semibold text-slate-900">
                {auditT.chart1Title}
              </h3>
              <p className="mt-0.5 text-xs text-slate-500">
                {auditT.chart1Sub}
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
                      name={auditT.chart1Raw}
                      fill="#cbd5e1"
                      radius={[3, 3, 0, 0]}
                    />
                    <Bar
                      dataKey="netDeletionPct"
                      name={auditT.chart1Net}
                      fill="#B3261E"
                      radius={[3, 3, 0, 0]}
                    />
                    <Bar
                      dataKey="baselinePct"
                      name={auditT.chart1Baseline}
                      fill="#1A1442"
                      radius={[3, 3, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-[20px] bg-white p-5 shadow-sheet">
              <h3 className="text-sm font-semibold text-slate-900">
                {auditT.chart2Title}
              </h3>
              <p className="mt-0.5 text-xs text-slate-500">
                {auditT.chart2Sub}
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
                      name={auditT.chart2Added}
                      fill="#0E7A4F"
                    />
                    <Bar
                      dataKey="transferredOut"
                      stackId="a"
                      name={auditT.chart2Transferred}
                      fill="#0B6A87"
                    />
                    <Bar
                      dataKey="modified"
                      stackId="a"
                      name={auditT.chart2Modified}
                      fill="#9A6200"
                    />
                    <Bar
                      dataKey="deleted"
                      stackId="a"
                      name={auditT.chart2Deleted}
                      fill="#B3261E"
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          )}

          {/* Master-Detail Anomaly Flags & 5-Part Evidence Inspector */}
          {(showInspector || showReview) && (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
            <div className="lg:col-span-5 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semiboldr text-slate-700">
                  {fmt(auditT.queueTitle, { count: diffData.flags.length })}
                </h3>
                <span className="text-xs text-slate-500">
                  {auditT.queueSub}
                </span>
              </div>
              {diffData.flags.map((flg) => {
                const active = selectedFlag?.flag_id === flg.flag_id;
                const statusText = revStatusLabels[flg.review_status] || flg.review_status.replaceAll("_", " ");
                return (
                  <button
                    key={flg.flag_id}
                    onClick={() => setSelectedFlagId(flg.flag_id)}
                    className={`w-full text-left rounded-xl border p-4 transition-all ${
                      active
                        ? "border-ink-600 bg-ink-50/40 ring-1 ring-ink-600 shadow-sm"
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
                      {ticks(flg.headline)}
                    </div>
                    <div className="mt-2 flex items-center justify-between text-xs text-slate-600">
                      <span>
                        {fmt(auditT.affectedRecords, { count: flg.affected_records_count })}
                      </span>
                      <span>
                        {fmt(auditT.confidence, { pct: (flg.explanation.confidence_level * 100).toFixed(0) })}
                        {" "}• {auditT.statusLabel}
                        <span className="font-medium text-ink-700">
                          {statusText}
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
                <div className="rounded-[20px] bg-white p-6 shadow-sheet space-y-5">
                  <div className="border-b border-slate-200 pb-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      {severityBadge(selectedFlag.severity)}
                      <span className="font-mono text-xs text-slate-500">
                        {auditT.flagIdPrefix}{selectedFlag.flag_id}
                      </span>
                    </div>
                    <h3 className="mt-2 text-lg font-bold text-slate-900">
                      {ticks(selectedFlag.headline)}
                    </h3>
                    <p className="mt-1 text-xs text-slate-500">
                      {selectedFlag.constituency_id} —{" "}
                      {selectedFlag.constituency_name} • {selectedFlag.booth_name}
                    </p>
                  </div>

                  {showInspector && (<>
                  {/* Uncertainty Box */}
                  <div className="rounded-lg border border-ink-200 bg-ink-50/50 p-4">
                    <div className="flex items-center justify-between text-xs font-semiboldr text-ink-900">
                      <span className="flex items-center gap-1.5">
                        <Scale className="h-4 w-4" /> {auditT.uncertaintyHeader}
                      </span>
                      <span>
                        {fmt(auditT.sampleSize, { n: selectedFlag.uncertainty.sample_size.toLocaleString() })}
                      </span>
                    </div>
                    <div className="mt-2 grid grid-cols-2 gap-3 sm:grid-cols-4 text-xs">
                      <div className="rounded bg-white p-2 border border-ink-100">
                        <div className="text-slate-500">{auditT.observedMetric}</div>
                        <div className="font-mono text-sm font-bold text-slate-900">
                          {(
                            selectedFlag.uncertainty.point_estimate * 100
                          ).toFixed(2)}
                          %
                        </div>
                      </div>
                      <div className="rounded bg-white p-2 border border-ink-100">
                        <div className="text-slate-500">{auditT.wilsonCI}</div>
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
                      <div className="rounded bg-white p-2 border border-ink-100">
                        <div className="text-slate-500">{auditT.baselineHistorical}</div>
                        <div className="font-mono text-sm font-bold text-slate-900">
                          {(
                            selectedFlag.uncertainty.historical_baseline_mean *
                            100
                          ).toFixed(2)}
                          %
                        </div>
                      </div>
                      <div className="rounded bg-white p-2 border border-ink-100">
                        <div className="text-slate-500">{auditT.zScoreDeviation}</div>
                        <div className="font-mono text-sm font-bold text-ink-700">
                          {selectedFlag.uncertainty.z_score >= 0 ? "+" : ""}
                          {selectedFlag.uncertainty.z_score}σ
                        </div>
                      </div>
                    </div>
                    <p className="mt-2 text-xs text-ink-950/80">
                      {ticks(selectedFlag.uncertainty.uncertainty_note)}
                    </p>
                  </div>

                  {/* 5-Part Structured Brief */}
                  <div className="space-y-4 text-sm">
                    <div>
                      <h4 className="font-semibold text-slate-900">
                        {auditT.sec1Title}
                      </h4>
                      <p className="mt-1 text-slate-700">
                        {ticks(selectedFlag.explanation.what_changed)}
                      </p>
                      <div className="mt-2 flex flex-wrap items-center gap-1.5">
                        <span className="text-xs text-slate-500">
                          {auditT.traceSampleEpics}
                        </span>
                        {selectedFlag.sample_epic_ids.map((ep) => (
                          <button
                            key={ep}
                            onClick={() => onInspectEpicInVerify(ep)}
                            className="rounded bg-slate-100 px-2 py-0.5 font-mono text-xs text-ink-700 hover:bg-ink-100"
                            title={auditT.inspectCitizenTooltip}
                          >
                            {ep} ↗
                          </button>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold text-slate-900">
                        {auditT.sec2Title}
                      </h4>
                      <p className="mt-1 text-slate-700">
                        {ticks(selectedFlag.explanation.rule_triggered)}
                      </p>
                      <code className="mt-1 block rounded bg-slate-900 px-3 py-1.5 text-xs text-emerald-300 font-mono">
                        {selectedFlag.rule_formula}
                      </code>
                    </div>

                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                      <div className="rounded-lg border border-emerald-200 bg-emerald-50/40 p-3.5">
                        <h4 className="font-semibold text-emerald-950 flex items-center gap-1.5 text-xs">
                          <ShieldCheck className="h-4 w-4 text-emerald-700" />
                          {auditT.sec3Title}
                        </h4>
                        <ul className="mt-2 list-disc space-y-1.5 pl-4 text-xs text-slate-700">
                          {selectedFlag.explanation.innocent_explanations.map(
                            (it, i) => (
                              <li key={i}>{ticks(it)}</li>
                            )
                          )}
                        </ul>
                      </div>

                      <div className="rounded-lg border border-sky-200 bg-sky-50/40 p-3.5">
                        <h4 className="font-semibold text-sky-950 flex items-center gap-1.5 text-xs">
                          <HelpCircle className="h-4 w-4 text-sky-700" />
                          {auditT.sec4Title}
                        </h4>
                        <ul className="mt-2 list-disc space-y-1.5 pl-4 text-xs text-slate-700">
                          {selectedFlag.explanation.missing_evidence.map(
                            (it, i) => (
                              <li key={i}>{ticks(it)}</li>
                            )
                          )}
                        </ul>
                      </div>
                    </div>

                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3.5">
                      <h4 className="font-semibold text-slate-900 text-xs">
                        {auditT.sec5Title}
                      </h4>
                      <p className="mt-1 text-xs text-slate-700">
                        {ticks(selectedFlag.explanation.next_verification_step)}
                      </p>
                      <div className="mt-2 border-t border-slate-200 pt-2 text-xs text-slate-500">
                        <strong>
                          {fmt(auditT.confidenceCalibration, {
                            pct: (selectedFlag.explanation.confidence_level * 100).toFixed(0),
                          })}
                        </strong>{" "}
                        {ticks(selectedFlag.explanation.confidence_basis)}
                      </div>
                    </div>
                  </div>

                  {onOpenReview && (
                    <button
                      type="button"
                      onClick={() => onOpenReview(selectedFlag.flag_id)}
                      className="inline-flex items-center gap-2 rounded-xl bg-ink-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-ink-700"
                    >
                      <MessageSquarePlus className="h-4 w-4" />
                      {openReviewLabel || auditT.formTitle}
                    </button>
                  )}
                  </>)}

                  {showReview && (<>
                  <div className="space-y-3 text-sm">
                    <p className="text-slate-700">{ticks(selectedFlag.explanation.what_changed)}</p>
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3.5">
                      <h4 className="text-xs font-semibold text-slate-900">{auditT.sec5Title}</h4>
                      <p className="mt-1 text-xs text-slate-700">{ticks(selectedFlag.explanation.next_verification_step)}</p>
                    </div>
                  </div>
                  {/* Append-Only Reviewer Correction Form */}
                  <form
                    onSubmit={handleAddAnnotation}
                    className="rounded-lg border border-slate-200 bg-slate-50/70 p-4 space-y-3"
                  >
                    <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800">
                      <MessageSquarePlus className="h-4 w-4 text-ink-600" />
                      {auditT.formTitle}
                    </div>
                    <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                      <input
                        type="text"
                        value={reviewerRole}
                        onChange={(e) => setReviewerRole(e.target.value)}
                        placeholder={auditT.formRolePlaceholder}
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
                          {auditT.formActionEvidence}
                        </option>
                        <option value="MARKED_EXPLAINED_ADMIN_SHIFT">
                          {auditT.formActionExplained}
                        </option>
                        <option value="ESCALATED_FOR_FIELD_CHECK">
                          {auditT.formActionEscalate}
                        </option>
                      </select>
                    </div>
                    <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                      <input
                        type="text"
                        value={reviewNote}
                        onChange={(e) => setReviewNote(e.target.value)}
                        placeholder={auditT.formNotePlaceholder}
                        className="sm:col-span-2 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs"
                      />
                      <input
                        type="text"
                        value={reviewRef}
                        onChange={(e) => setReviewRef(e.target.value)}
                        placeholder={auditT.formRefPlaceholder}
                        className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-mono"
                      />
                    </div>
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[11px] text-slate-500">
                        {auditT.formNotice}
                      </span>
                      <button
                        type="submit"
                        disabled={savingNote || reviewNote.trim().length < 5}
                        className="rounded-lg bg-ink-600 px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-ink-700 disabled:opacity-50"
                      >
                        {savingNote ? auditT.formSubmittingBtn : auditT.formSubmitBtn}
                      </button>
                    </div>
                    <label className="block">
                      <span className="mb-1 block text-[11px] font-medium text-slate-600">
                        {shellT.reviewerKeyLabel}
                      </span>
                      <input
                        type="password"
                        autoComplete="off"
                        value={reviewerKey}
                        onChange={(e) => setReviewerKeyState(e.target.value)}
                        placeholder={shellT.reviewerKeyPlaceholder}
                        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs"
                      />
                      <span className="mt-1 block text-[11px] text-slate-500">{shellT.reviewerKeyHint}</span>
                    </label>
                    {noteSavedBanner && (
                      <div
                        role={noteError ? "alert" : "status"}
                        className={`rounded px-3 py-1.5 text-xs ${
                          noteError ? "bg-removed-soft text-removed" : "bg-emerald-100 font-mono text-emerald-900"
                        }`}
                      >
                        {noteSavedBanner}
                      </div>
                    )}
                  </form>
                  </>)}
                </div>
              )}
            </div>
          </div>
          )}

          {/* Traceable Electoral Change Ledger Sample Table */}
          {showCompare && (
          <div className="rounded-[20px] bg-white p-5 shadow-sheet">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                  <Layers className="h-4 w-4 text-ink-600" />
                  {auditT.tableTitle}
                </h3>
                <p className="text-xs text-slate-500">
                  {auditT.tableSub}
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
                    {changeLabels[t] || t.replace("_", " ")}
                  </button>
                ))}
              </div>
            </div>

            <div className="mt-4 overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
                <thead className="bg-slate-50 font-semibold text-slate-600">
                  <tr>
                    <th className="px-3 py-2">{auditT.colLedgerId}</th>
                    <th className="px-3 py-2">{auditT.colEpic}</th>
                    <th className="px-3 py-2">{auditT.colElector}</th>
                    <th className="px-3 py-2">{auditT.colClassification}</th>
                    <th className="px-3 py-2">{auditT.colLineage}</th>
                    <th className="px-3 py-2">{auditT.colDelta}</th>
                    <th className="px-3 py-2">{auditT.colSupplementRef}</th>
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
                          className="font-mono font-semibold text-ink-700 hover:underline"
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
                              : "bg-ink-100 text-ink-900"
                          }`}
                        >
                          {changeLabels[row.change_type] || row.change_type}
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
                          ? fmt(auditT.ageDeltaText, { before: row.age_before, after: row.age_after })
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
          )}
        </>
      ) : null}
    </div>
  );
}
