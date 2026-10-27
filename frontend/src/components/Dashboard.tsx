"use client";

import React, { useRef, useState } from "react";
import { ArrowRight, FileUp, Loader2 } from "lucide-react";
import { ingestSnapshot, readableApiError } from "@/lib/api";
import { fmt, getDict } from "@/lib/locales/common";
import { SHELL_LOCALE } from "@/lib/locales/shell";
import { LanguageCode, LedgerDiffResponse, Section, SnapshotMeta } from "@/lib/types";

interface Props {
  language: LanguageCode;
  snapshots: SnapshotMeta[];
  fromVersion: string;
  toVersion: string;
  onChangeVersions: (fromV: string, toV: string) => void;
  onSnapshotIngested: (snap: SnapshotMeta) => void;
  diffData: LedgerDiffResponse | null;
  loading: boolean;
  onNavigate: (s: Section) => void;
}

const n = (v: number) => v.toLocaleString("en-IN");

export default function Dashboard({
  language,
  snapshots,
  fromVersion,
  toVersion,
  onChangeVersions,
  onSnapshotIngested,
  diffData,
  loading,
  onNavigate,
}: Props) {
  const s = getDict(SHELL_LOCALE, language);
  const t = diffData?.totals;
  const balances = t ? t.electors_from - t.deleted + t.added === t.electors_to : false;

  const highFlags =
    diffData?.flags.filter((f) => f.severity === "HIGH_STATISTICAL_OUTLIER").length ?? 0;
  const changes = t ? t.added + t.deleted + t.modified + t.booth_transferred : 0;

  const steps: { label: string; sub: string; target: Section }[] = [
    { label: s.stepUpload, sub: s.stepUploadSub, target: "dashboard" },
    { label: s.stepCompare, sub: s.stepCompareSub, target: "comparison" },
    { label: s.stepFlags, sub: s.stepFlagsSub, target: "flags" },
    { label: s.stepReview, sub: s.stepReviewSub, target: "review" },
    { label: s.stepReport, sub: s.stepReportSub, target: "report" },
  ];

  return (
    <div className="space-y-8">
      {/* Roll arithmetic: the one thing a judge should remember */}
      <section className="overflow-hidden rounded-[28px] bg-white shadow-sheet">
        <div className="relative px-6 py-8 sm:px-10 sm:py-10">
          {!t ? (
            <div className="flex h-36 items-center gap-3 text-slate-500">
              {loading && <Loader2 className="h-5 w-5 animate-spin" />}
              {s.loading}
            </div>
          ) : (
            <>
              <div className="settle flex flex-wrap items-end gap-x-6 gap-y-6 sm:gap-x-8">
                <Term value={n(t.electors_from)} label={s.eqOld} tone="text-ink-950" />
                <Op>−</Op>
                <Term value={n(t.deleted)} label={s.eqRemoved} tone="text-removed" />
                <Op>+</Op>
                <Term value={n(t.added)} label={s.eqAdded} tone="text-added" />
                <Op>{balances ? "=" : "→"}</Op>
                <Term value={n(t.electors_to)} label={s.eqNew} tone="text-ink-950" emphasis />
              </div>
              <p className="mt-7 max-w-[70ch] border-t border-dashed border-ink-950/10 pt-5 text-[15px] leading-relaxed text-slate-600">
                {fmt(s.movedLine, { moved: "\u0000", modified: "\u0001" })
                  .split(/(\u0000|\u0001)/)
                  .map((part, i) =>
                    part === "\u0000" ? (
                      <span key={i} className="rounded-md bg-moved-soft px-1.5 py-0.5 font-bold text-moved">
                        {n(t.booth_transferred)}
                      </span>
                    ) : part === "\u0001" ? (
                      <span key={i} className="rounded-md bg-corrected-soft px-1.5 py-0.5 font-bold text-corrected">
                        {n(t.modified)}
                      </span>
                    ) : (
                      <React.Fragment key={i}>{part}</React.Fragment>
                    )
                  )}
              </p>
            </>
          )}
        </div>
      </section>

      {/* Load the two rolls */}
      <section className="rounded-[24px] border border-ink-950/[0.07] bg-white/60 p-5 sm:p-7">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-ink-950">{s.uploadTitle}</h2>
            <p className="mt-1 max-w-[64ch] text-sm text-slate-600">{s.uploadLede}</p>
          </div>
        </div>

        <div className="mt-5 grid grid-cols-1 items-stretch gap-4 md:grid-cols-[1fr_auto_1fr]">
          <RollSlot
            title={s.oldRoll}
            language={language}
            snapshots={snapshots}
            value={fromVersion}
            disabledValue={toVersion}
            onPick={(v) => onChangeVersions(v, toVersion)}
            baseForDelta={null}
            onIngested={(snap) => {
              onSnapshotIngested(snap);
              onChangeVersions(snap.version_id, toVersion);
            }}
            slot="old"
          />
          <div className="hidden items-center justify-center md:flex">
            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-ink-950 text-white">
              <ArrowRight className="h-4 w-4" />
            </span>
          </div>
          <RollSlot
            title={s.newRoll}
            language={language}
            snapshots={snapshots}
            value={toVersion}
            disabledValue={fromVersion}
            onPick={(v) => onChangeVersions(fromVersion, v)}
            baseForDelta={fromVersion}
            onIngested={(snap) => {
              onSnapshotIngested(snap);
              onChangeVersions(fromVersion, snap.version_id);
            }}
            slot="new"
          />
        </div>

        <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs text-slate-500">{s.csvHint}</p>
          <button
            onClick={() => onNavigate("comparison")}
            disabled={fromVersion === toVersion}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-ink-600 px-5 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-ink-700 disabled:opacity-40"
          >
            {s.compareBtn}
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </section>

      {/* How an audit runs: a real sequence, so it is numbered */}
      <section>
        <h2 className="mb-3 text-lg font-bold tracking-tight text-ink-950">{s.stepsTitle}</h2>
        <ol className="grid grid-cols-1 gap-px overflow-hidden rounded-[20px] bg-ink-950/[0.08] sm:grid-cols-5">
          {steps.map((st, i) => (
            <li key={st.label} className="bg-white">
              <button
                onClick={() => onNavigate(st.target)}
                className="group flex h-full w-full flex-col p-4 text-left transition-colors hover:bg-ink-50"
              >
                <span className="text-sm font-bold text-ink-500 tabular">{i + 1}</span>
                <span className="mt-2 font-semibold text-ink-950">{st.label}</span>
                <span className="mt-0.5 text-[13px] leading-snug text-slate-500">{st.sub}</span>
              </button>
            </li>
          ))}
        </ol>
      </section>

      {/* Numbers that matter */}
      {diffData && t && (
        <section className="grid grid-cols-2 gap-x-6 gap-y-5 rounded-[20px] bg-ink-950 px-6 py-6 text-white sm:grid-cols-3 lg:grid-cols-6 sm:px-8">
          <Stat value={n(t.electors_to)} label={s.statRecords} />
          <Stat value={n(diffData.booth_summaries.length)} label={s.statBooths} />
          <Stat value={n(changes)} label={s.statChanges} />
          <Stat value={n(diffData.flags.length)} label={s.statFlags} />
          <Stat value={n(highFlags)} label={s.statHigh} accent />
          <Stat value="100%" label={s.statHuman} />
        </section>
      )}

      {/* Booth by booth */}
      {diffData && (
        <section className="overflow-hidden rounded-[24px] bg-white shadow-sheet">
          <div className="flex items-center justify-between px-6 pb-3 pt-5">
            <h2 className="text-lg font-bold tracking-tight text-ink-950">{s.boothTitle}</h2>
            <button
              onClick={() => onNavigate("flags")}
              className="text-sm font-semibold text-ink-600 hover:text-ink-800"
            >
              {s.viewFlags}
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-sm">
              <thead>
                <tr className="border-y border-ink-950/[0.06] bg-canvas/60 text-left text-xs text-slate-500">
                  <th className="px-6 py-2.5 font-medium">{s.boothCol}</th>
                  <th className="px-3 py-2.5 text-right font-medium">{s.boothBefore}</th>
                  <th className="px-3 py-2.5 text-right font-medium">{s.boothAfter}</th>
                  <th className="px-3 py-2.5 text-right font-medium">{s.boothAdded}</th>
                  <th className="px-3 py-2.5 text-right font-medium">{s.boothRemoved}</th>
                  <th className="px-3 py-2.5 text-right font-medium">{s.boothMoved}</th>
                  <th className="px-6 py-2.5 font-medium">{s.boothNet}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-950/[0.05]">
                {diffData.booth_summaries.map((b) => {
                  const net = b.net_effective_deletion_rate * 100;
                  const base = b.historical_deletion_baseline * 100;
                  const scale = 15; // % at full width
                  const over = net > b.deletion_ci_upper_95 * 100 || b.z_score_vs_baseline >= 3;
                  return (
                    <tr key={b.booth_id} className="tabular">
                      <td className="px-6 py-3">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-ink-950">{b.booth_id}</span>
                          {b.flag_count > 0 && (
                            <span
                              title={s.boothFlagged}
                              className="h-2 w-2 rounded-full bg-ink-500"
                            />
                          )}
                        </div>
                        <div className="max-w-[220px] truncate text-xs text-slate-500">{b.booth_name}</div>
                      </td>
                      <td className="px-3 py-3 text-right text-slate-600">{n(b.electors_from)}</td>
                      <td className="px-3 py-3 text-right font-semibold text-ink-950">{n(b.electors_to)}</td>
                      <td className="px-3 py-3 text-right font-semibold text-added">
                        {b.added_count ? `+${n(b.added_count)}` : "—"}
                      </td>
                      <td className="px-3 py-3 text-right font-semibold text-removed">
                        {b.deleted_count ? `−${n(b.deleted_count)}` : "—"}
                      </td>
                      <td className="px-3 py-3 text-right font-semibold text-moved">
                        {b.transferred_out_count ? n(b.transferred_out_count) : "—"}
                      </td>
                      <td className="px-6 py-3">
                        <div className="flex items-center gap-3">
                          <div className="relative h-2 w-36 rounded-full bg-ink-950/[0.06]">
                            <div
                              className={`absolute inset-y-0 left-0 rounded-full ${over ? "bg-removed" : "bg-ink-300"}`}
                              style={{ width: `${Math.min(100, (net / scale) * 100)}%` }}
                            />
                            <div
                              title="Historical baseline"
                              className="absolute -top-1 h-4 w-[2px] rounded bg-ink-950"
                              style={{ left: `${Math.min(100, (base / scale) * 100)}%` }}
                            />
                          </div>
                          <span className={`w-14 text-right text-xs font-semibold ${over ? "text-removed" : "text-slate-600"}`}>
                            {net.toFixed(1)}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}

function Term({
  value,
  label,
  tone,
  emphasis = false,
}: {
  value: string;
  label: string;
  tone: string;
  emphasis?: boolean;
}) {
  return (
    <div className="min-w-0">
      <div
        className={`tabular font-black leading-none tracking-[-0.035em] ${tone} ${
          emphasis ? "text-[56px] sm:text-[72px]" : "text-[44px] sm:text-[60px]"
        }`}
      >
        {value}
      </div>
      <div className="mt-2 text-sm font-medium text-slate-500">{label}</div>
    </div>
  );
}

function Op({ children }: { children: React.ReactNode }) {
  return (
    <div aria-hidden className="pb-9 text-[36px] font-light leading-none text-ink-950/25 sm:text-[48px]">
      {children}
    </div>
  );
}

function Stat({ value, label, accent = false }: { value: string; label: string; accent?: boolean }) {
  return (
    <div>
      <div className={`text-[28px] font-extrabold leading-none tracking-tight tabular ${accent ? "text-ink-300" : "text-white"}`}>
        {value}
      </div>
      <div className="mt-1.5 text-[13px] leading-snug text-ink-200/70">{label}</div>
    </div>
  );
}

function RollSlot({
  title,
  language,
  snapshots,
  value,
  disabledValue,
  onPick,
  baseForDelta,
  onIngested,
  slot,
}: {
  title: string;
  language: LanguageCode;
  snapshots: SnapshotMeta[];
  value: string;
  disabledValue: string;
  onPick: (v: string) => void;
  baseForDelta: string | null;
  onIngested: (snap: SnapshotMeta) => void;
  slot: "old" | "new";
}) {
  const s = getDict(SHELL_LOCALE, language);
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [dragging, setDragging] = useState(false);
  const current = snapshots.find((x) => x.version_id === value);

  async function handleFile(file: File) {
    setBusy(true);
    setMsg(null);
    try {
      const csv = await file.text();
      // A CSV with DELETE/MODIFY rows is a supplement applied onto the old roll;
      // otherwise it is treated as a complete roll on its own.
      const isDelta = /(^|\n)\s*(DELETE|MODIFY)\s*,/i.test(csv);
      const stem = file.name.replace(/\.[^.]+$/, "").replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 18);
      const versionId = `${slot}_${stem || "roll"}_${Date.now().toString(36)}`.slice(0, 36);
      const label = file.name.length >= 4 ? file.name.slice(0, 120) : `${file.name} upload`;
      const snap = await ingestSnapshot({
        version_id: versionId,
        label,
        base_version_id: isDelta ? baseForDelta : null,
        csv_payload: csv,
      });
      onIngested(snap);
      setMsg({ ok: true, text: fmt(s.uploadedAs, { id: snap.version_id }) });
    } catch (err) {
      const detail = readableApiError(err);
      setMsg({ ok: false, text: fmt(s.uploadFailed, { error: detail }) });
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div className="flex flex-col rounded-[20px] bg-white p-5 shadow-sheet">
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="text-base font-bold text-ink-950">{title}</h3>
        {current && (
          <span className="flex gap-3 text-xs text-slate-500 tabular">
            <span>{current.total_electors.toLocaleString("en-IN")}</span>
            <span>{current.publication_date}</span>
          </span>
        )}
      </div>

      <label className="mt-3 block">
        <span className="mb-1 block text-xs font-medium text-slate-500">{s.pickVersion}</span>
        <select
          value={value}
          onChange={(e) => onPick(e.target.value)}
          className="w-full rounded-xl border border-ink-950/10 bg-canvas/50 px-3 py-2.5 text-sm font-semibold text-ink-950"
        >
          {snapshots.map((x) => (
            <option key={x.version_id} value={x.version_id} disabled={x.version_id === disabledValue}>
              {x.label || x.version_id}
            </option>
          ))}
        </select>
      </label>

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          const f = e.dataTransfer.files?.[0];
          if (f) void handleFile(f);
        }}
        disabled={busy}
        className={`mt-3 flex flex-1 items-center justify-center gap-2.5 rounded-xl border-2 border-dashed px-4 py-5 text-sm font-semibold transition-colors ${
          dragging
            ? "border-ink-500 bg-ink-50 text-ink-700"
            : "border-ink-950/10 text-slate-600 hover:border-ink-300 hover:bg-ink-50/60 hover:text-ink-700"
        }`}
      >
        {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileUp className="h-4 w-4" />}
        {busy ? s.uploading : s.uploadCsv}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept=".csv,text/csv"
        className="sr-only"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) void handleFile(f);
        }}
      />
      {msg && (
        <p className={`mt-2 text-xs ${msg.ok ? "text-added" : "text-removed"}`}>{msg.text}</p>
      )}
    </div>
  );
}
