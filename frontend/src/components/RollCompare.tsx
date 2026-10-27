"use client";

import React, { useEffect, useMemo, useState } from "react";
import { ArrowRight, Loader2, Minus, PenLine, Plus } from "lucide-react";
import { fetchAuditDiff } from "@/lib/api";
import { CHANGE_TYPE_LABELS, FIELD_LABELS, fmt, getDict } from "@/lib/locales/common";
import { SHELL_LOCALE } from "@/lib/locales/shell";
import { ChangeType, LanguageCode, LedgerDiffResponse, LedgerEntry } from "@/lib/types";

interface Props {
  language: LanguageCode;
  fromVersion: string;
  toVersion: string;
  diffData: LedgerDiffResponse | null;
  loading: boolean;
  onTraceEpic: (epicId: string) => void;
}

const TONE: Record<
  ChangeType,
  { text: string; soft: string; dot: string; Icon: typeof Plus }
> = {
  ADDED: { text: "text-added", soft: "bg-added-soft", dot: "bg-added", Icon: Plus },
  DELETED: { text: "text-removed", soft: "bg-removed-soft", dot: "bg-removed", Icon: Minus },
  BOOTH_TRANSFERRED: { text: "text-moved", soft: "bg-moved-soft", dot: "bg-moved", Icon: ArrowRight },
  MODIFIED: { text: "text-corrected", soft: "bg-corrected-soft", dot: "bg-corrected", Icon: PenLine },
};

type ShellStrings = (typeof SHELL_LOCALE)["en"];

const ORDER: ChangeType[] = ["BOOTH_TRANSFERRED", "DELETED", "ADDED", "MODIFIED"];
const PAGE = 30;

export default function RollCompare({
  language,
  fromVersion,
  toVersion,
  diffData,
  loading,
  onTraceEpic,
}: Props) {
  const s = getDict(SHELL_LOCALE, language);
  const changeLabels = getDict(CHANGE_TYPE_LABELS, language);
  const fieldLabels = getDict(FIELD_LABELS, language);

  // The page-wide diff carries a 120-entry sample; the side-by-side view asks
  // the same endpoint for a deeper sample so every change type is represented.
  const [deep, setDeep] = useState<LedgerEntry[] | null>(null);
  useEffect(() => {
    let live = true;
    setDeep(null);
    fetchAuditDiff(fromVersion, toVersion, language, 500)
      .then((d) => live && setDeep(d.sample_ledger_entries))
      .catch(() => live && setDeep(null));
    return () => {
      live = false;
    };
  }, [fromVersion, toVersion, language]);

  const entries = useMemo(
    () => deep ?? diffData?.sample_ledger_entries ?? [],
    [deep, diffData]
  );

  // Booths that appear in the changed entries, busiest first
  const booths = useMemo(() => {
    const counts = new Map<string, number>();
    for (const e of entries) {
      const ids = new Set([e.from_booth_id, e.to_booth_id].filter(Boolean) as string[]);
      ids.forEach((id) => counts.set(id, (counts.get(id) ?? 0) + 1));
    }
    return [...counts.entries()].sort((a, b) => b[1] - a[1]);
  }, [entries]);

  const [booth, setBooth] = useState<string>("ALL");
  const [type, setType] = useState<"ALL" | ChangeType>("ALL");
  const [shown, setShown] = useState(PAGE);

  // Open on the busiest booth (in the demo data, the PS-109 split)
  useEffect(() => {
    setBooth(booths[0]?.[0] ?? "ALL");
    setShown(PAGE);
  }, [entries]); // eslint-disable-line react-hooks/exhaustive-deps

  const inBooth = useMemo(
    () =>
      booth === "ALL"
        ? entries
        : entries.filter((e) => e.from_booth_id === booth || e.to_booth_id === booth),
    [entries, booth]
  );
  const rows = useMemo(
    () =>
      [...(type === "ALL" ? inBooth : inBooth.filter((e) => e.change_type === type))].sort(
        (a, b) => ORDER.indexOf(a.change_type) - ORDER.indexOf(b.change_type)
      ),
    [inBooth, type]
  );
  const typeCounts = useMemo(() => {
    const c: Record<string, number> = {};
    inBooth.forEach((e) => (c[e.change_type] = (c[e.change_type] ?? 0) + 1));
    return c;
  }, [inBooth]);

  const summary =
    booth === "ALL" ? null : diffData?.booth_summaries.find((b) => b.booth_id === booth);

  if (!diffData) {
    return (
      <div className="flex h-64 items-center justify-center gap-3 rounded-[24px] bg-white text-slate-500 shadow-sheet">
        {loading && <Loader2 className="h-5 w-5 animate-spin" />}
        {s.loading}
      </div>
    );
  }

  return (
    <section>
      {/* Filters */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="mb-1.5 text-xs font-medium text-slate-500">{s.sheetBooth}</div>
          <div className="flex flex-wrap gap-1.5">
            {[["ALL", entries.length] as [string, number], ...booths].map(([id, count]) => (
              <button
                key={id}
                onClick={() => {
                  setBooth(id);
                  setShown(PAGE);
                }}
                aria-pressed={booth === id}
                className={`rounded-full px-3 py-1.5 text-sm font-semibold transition-colors ${
                  booth === id
                    ? "bg-ink-950 text-white"
                    : "bg-white text-slate-700 shadow-sm hover:bg-ink-50"
                }`}
              >
                {id === "ALL" ? s.sheetAllBooths : id}
                <span className={`ml-1.5 text-xs tabular ${booth === id ? "text-ink-200" : "text-slate-400"}`}>
                  {count}
                </span>
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {ORDER.map((ct) => {
            const tone = TONE[ct];
            const active = type === ct;
            return (
              <button
                key={ct}
                onClick={() => setType(active ? "ALL" : ct)}
                aria-pressed={active}
                className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-semibold transition-colors ${
                  active ? `${tone.soft} ${tone.text} ring-1 ring-current` : "bg-white text-slate-700 shadow-sm hover:bg-ink-50"
                }`}
              >
                <span className={`h-2 w-2 rounded-full ${tone.dot}`} />
                {changeLabels[ct] || ct}
                <span className="text-xs text-slate-400 tabular">{typeCounts[ct] ?? 0}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* The two roll pages */}
      <div className="relative mt-5">
        <div aria-hidden className="pointer-events-none absolute inset-0 hidden md:grid md:grid-cols-[1fr_56px_1fr]">
          <div className="roll-sheet rounded-[20px] shadow-sheet" />
          <div />
          <div className="roll-sheet rounded-[20px] shadow-sheet" />
        </div>

        <div className="relative grid grid-cols-1 md:grid-cols-[1fr_56px_1fr]">
          <SheetHead
            title={s.oldRoll}
            label={diffData.from_snapshot.label || diffData.from_snapshot.version_id}
            date={diffData.from_snapshot.publication_date}
            sha={diffData.from_snapshot.sha256}
            total={summary ? summary.electors_from : diffData.totals.electors_from}
            printed={s.printedRoll}
            booth={booth === "ALL" ? s.sheetAllBooths : `${s.sheetBooth} ${booth}`}
          />
          <div className="hidden md:block" />
          <SheetHead
            title={s.newRoll}
            label={diffData.to_snapshot.label || diffData.to_snapshot.version_id}
            date={diffData.to_snapshot.publication_date}
            sha={diffData.to_snapshot.sha256}
            total={summary ? summary.electors_to : diffData.totals.electors_to}
            printed={s.printedRoll}
            booth={booth === "ALL" ? s.sheetAllBooths : `${s.sheetBooth} ${booth}`}
            delta={
              summary
                ? summary.electors_to - summary.electors_from
                : diffData.totals.electors_to - diffData.totals.electors_from
            }
          />

          {rows.length === 0 && (
            <div className="col-span-full px-6 py-12 text-center text-sm text-slate-500">{s.sheetEmpty}</div>
          )}

          {rows.slice(0, shown).map((e) => (
            <Row
              key={e.ledger_id}
              e={e}
              s={s}
              changeLabel={changeLabels[e.change_type] || e.change_type}
              fieldLabels={fieldLabels}
              onTrace={onTraceEpic}
            />
          ))}

          <div className="col-span-full flex flex-col items-center gap-3 px-6 pb-6 pt-4 text-center">
            {rows.length > shown && (
              <button
                onClick={() => setShown((v) => v + PAGE)}
                className="rounded-full bg-ink-950 px-4 py-2 text-sm font-semibold text-white hover:bg-ink-800"
              >
                {fmt(s.sheetShowing, { n: `+${Math.min(PAGE, rows.length - shown)}` })}
              </button>
            )}
            <p className="max-w-[70ch] text-xs text-slate-500">{s.sheetSample}</p>
          </div>
        </div>
      </div>
    </section>
  );
}

function SheetHead({
  title,
  label,
  date,
  sha,
  total,
  printed,
  booth,
  delta,
}: {
  title: string;
  label: string;
  date: string;
  sha: string;
  total: number;
  printed: string;
  booth: string;
  delta?: number;
}) {
  return (
    <div className="mt-4 rounded-t-[20px] bg-white px-5 pb-4 pt-5 shadow-sheet md:mt-0 md:bg-transparent md:shadow-none">
      <div className="flex items-start justify-between gap-3 border-b-2 border-ink-950 pb-3">
        <div className="min-w-0">
          <div className="text-xs font-medium text-slate-500">{printed}</div>
          <div className="truncate text-lg font-extrabold leading-tight text-ink-950">{title}</div>
          <div className="truncate text-sm text-slate-600">
            {label} <span className="text-slate-400">{date}</span>
          </div>
        </div>
        <div className="shrink-0 text-right">
          <div className="text-xs text-slate-500">{booth}</div>
          <div className="text-2xl font-black leading-tight tracking-tight text-ink-950 tabular">
            {total.toLocaleString("en-IN")}
          </div>
          {delta !== undefined && delta !== 0 && (
            <div className={`text-xs font-bold tabular ${delta > 0 ? "text-added" : "text-removed"}`}>
              {delta > 0 ? "+" : "−"}
              {Math.abs(delta).toLocaleString("en-IN")}
            </div>
          )}
        </div>
      </div>
      <div className="mt-2 truncate font-mono text-[11px] text-slate-400" title={sha}>
        sha256 {sha.slice(0, 24)}…
      </div>
    </div>
  );
}

function Row({
  e,
  s,
  changeLabel,
  fieldLabels,
  onTrace,
}: {
  e: LedgerEntry;
  s: ShellStrings;
  changeLabel: string;
  fieldLabels: Record<string, string>;
  onTrace: (epic: string) => void;
}) {
  const tone = TONE[e.change_type];
  const Icon = tone.Icon;
  // Booth/serial moves are already shown by the booth tag; list only real corrections.
  const fields = Object.entries(e.modified_fields ?? {}).filter(
    ([k]) => !/booth|serial/i.test(k)
  );
  const ageChanged = e.change_type === "MODIFIED" && "age" in (e.modified_fields ?? {});

  const leftEmpty = e.change_type === "ADDED";
  const rightEmpty = e.change_type === "DELETED";

  return (
    <>
      {/* Old roll */}
      <div className="px-3 py-1.5 md:pl-5 md:pr-2">
        {leftEmpty ? (
          <Placeholder text={s.sheetNotInOld} />
        ) : (
          <Entry
            e={e}
            s={s}
            booth={e.from_booth_id}
            serial={e.from_serial_no}
            age={e.age_before}
            struck={e.change_type === "DELETED"}
            highlight={e.change_type === "DELETED" ? "removed" : undefined}
            changes={fields.filter(([k]) => k !== "age").map(([k, v]) => [fieldLabels[k] || k, String(v.before)])}
            ageMarked={ageChanged}
            onTrace={onTrace}
          />
        )}
      </div>

      {/* Change marker */}
      <div className="flex items-center justify-center py-1.5" title={changeLabel}>
        <span className={`flex h-8 w-8 items-center justify-center rounded-full ${tone.soft} ${tone.text}`}>
          <Icon className="h-4 w-4" strokeWidth={2.5} />
          <span className="sr-only">{changeLabel}</span>
        </span>
      </div>

      {/* New roll */}
      <div className="px-3 py-1.5 md:pl-2 md:pr-5">
        {rightEmpty ? (
          <Placeholder text={s.sheetRemoved} tone="removed" />
        ) : (
          <Entry
            e={e}
            s={s}
            booth={e.to_booth_id}
            serial={e.to_serial_no}
            age={e.age_after}
            highlight={
              e.change_type === "ADDED"
                ? "added"
                : e.change_type === "BOOTH_TRANSFERRED"
                ? "moved"
                : e.change_type === "MODIFIED"
                ? "corrected"
                : undefined
            }
            boothMarked={e.change_type === "BOOTH_TRANSFERRED"}
            changes={fields.filter(([k]) => k !== "age").map(([k, v]) => [fieldLabels[k] || k, String(v.after)])}
            ageMarked={ageChanged}
            onTrace={onTrace}
          />
        )}
      </div>
    </>
  );
}

const HL = {
  added: "border-added/30 bg-added-soft/60",
  removed: "border-removed/25 bg-removed-soft/50",
  moved: "border-moved/25 bg-moved-soft/50",
  corrected: "border-corrected/30 bg-corrected-soft/60",
} as const;

function Entry({
  e,
  s,
  booth,
  serial,
  age,
  struck = false,
  highlight,
  boothMarked = false,
  changes,
  ageMarked,
  onTrace,
}: {
  e: LedgerEntry;
  s: ShellStrings;
  booth: string | null;
  serial: number | null;
  age: number | null;
  struck?: boolean;
  highlight?: keyof typeof HL;
  boothMarked?: boolean;
  changes: [string, string][];
  ageMarked: boolean;
  onTrace: (epic: string) => void;
}) {
  return (
    <div
      className={`grid h-full grid-cols-[52px_1fr] gap-3 rounded-xl border px-3 py-2.5 ${
        highlight ? HL[highlight] : "border-ink-950/[0.07] bg-white"
      }`}
    >
      <div className="border-r border-ink-950/10 pr-2 text-center">
        <div className="text-[10px] text-slate-400">{s.sheetSerial}</div>
        <div className="text-base font-bold leading-tight text-ink-950 tabular">{serial ?? "—"}</div>
        <div
          className={`mt-0.5 text-[11px] font-semibold ${
            boothMarked ? "rounded bg-moved px-1 text-white" : "text-slate-500"
          }`}
        >
          {booth ?? "—"}
        </div>
      </div>
      <div className="min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div
            className={`truncate font-semibold text-ink-950 ${
              struck ? "line-through decoration-removed decoration-2" : ""
            }`}
          >
            {e.elector_name}
          </div>
          <button
            onClick={() => onTrace(e.epic_id)}
            title={s.sheetTrace}
            className="shrink-0 font-mono text-[11px] text-ink-600 hover:text-ink-800 hover:underline"
          >
            {e.epic_id}
          </button>
        </div>
        <div className="mt-0.5 flex flex-wrap gap-x-3 text-xs text-slate-600">
          <span>
            {s.sheetHouse} {e.house_no}
          </span>
          {age != null && (
            <span className={ageMarked ? "font-bold text-corrected" : ""}>
              {s.sheetAge} {age}
            </span>
          )}
          {changes.map(([k, v]) => (
              <span key={k} className="font-semibold text-corrected">
                {k}: {v}
              </span>
            ))}
        </div>
      </div>
    </div>
  );
}

function Placeholder({ text, tone }: { text: string; tone?: "removed" }) {
  return (
    <div
      className={`flex h-full min-h-[62px] items-center justify-center rounded-xl border border-dashed px-3 text-xs font-medium ${
        tone === "removed"
          ? "border-removed/30 text-removed/80"
          : "border-ink-950/15 text-slate-400"
      }`}
    >
      {text}
    </div>
  );
}
