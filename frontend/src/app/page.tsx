"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  ClipboardCheck,
  Columns2,
  FileSignature,
  Flag,
  LayoutDashboard,
  UserSearch,
} from "lucide-react";
import AssuranceCenter from "@/components/AssuranceCenter";
import AuditWorkspace from "@/components/AuditWorkspace";
import Dashboard from "@/components/Dashboard";
import RollCompare from "@/components/RollCompare";
import VerifyPortal from "@/components/VerifyPortal";
import { fetchAuditDiff, fetchSnapshots } from "@/lib/api";
import { BRAND, fmt, getDict } from "@/lib/locales/common";
import { SHELL_LOCALE } from "@/lib/locales/shell";
import { LanguageCode, LedgerDiffResponse, Section, SnapshotMeta } from "@/lib/types";

const LANGS = [
  { code: "en", label: "EN", name: "English" },
  { code: "hi", label: "हि", name: "हिन्दी" },
  { code: "gu", label: "ગુ", name: "ગુજરાતી" },
] as const;

/** The ink mark on a voter's fingernail: PollToll's logo. */
function InkMark({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 28 32" aria-hidden className={className}>
      <path
        d="M4 13c0-6 4.5-10 10-10s10 4 10 10v12a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4V13Z"
        fill="#F4F2FD"
      />
      <path
        d="M14 8v19"
        stroke="#7056D9"
        strokeWidth="4.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

export default function PollTollControlPlane() {
  const [section, setSection] = useState<Section>("dashboard");
  const [language, setLanguage] = useState<LanguageCode>("en");
  const [snapshots, setSnapshots] = useState<SnapshotMeta[]>([]);
  const [fromVersion, setFromVersion] = useState("v2025_final");
  const [toVersion, setToVersion] = useState("v2026_draft");
  const [diffData, setDiffData] = useState<LedgerDiffResponse | null>(null);
  const [loadingDiff, setLoadingDiff] = useState(true);
  const [backendError, setBackendError] = useState<string | null>(null);
  const [preselectedEpic, setPreselectedEpic] = useState<string | null>(null);
  const [selectedFlagId, setSelectedFlagId] = useState<string | null>(null);

  const s = getDict(SHELL_LOCALE, language);

  const loadDiff = useCallback(
    async (fromV: string, toV: string, lang: LanguageCode) => {
      setLoadingDiff(true);
      setBackendError(null);
      try {
        const data = await fetchAuditDiff(fromV, toV, lang);
        setDiffData(data);
      } catch (err) {
        setBackendError(String(err));
      } finally {
        setLoadingDiff(false);
      }
    },
    []
  );

  useEffect(() => {
    void fetchSnapshots(language)
      .then((snaps) => setSnapshots(snaps))
      .catch((err) => setBackendError(String(err)));
  }, [language]);

  useEffect(() => {
    void loadDiff(fromVersion, toVersion, language);
  }, [fromVersion, toVersion, language, loadDiff]);

  function go(next: Section) {
    setSection(next);
    if (typeof window !== "undefined") window.scrollTo({ top: 0 });
  }

  function handleInspectEpicInVerify(epicId: string) {
    setPreselectedEpic(epicId);
    go("citizen");
  }

  function handleSnapshotIngested(newSnap: SnapshotMeta) {
    setSnapshots((prev) =>
      prev.some((p) => p.version_id === newSnap.version_id)
        ? prev
        : [...prev, newSnap]
    );
  }

  const openFlags =
    diffData?.flags.filter((f) => f.review_status === "OPEN_FOR_REVIEW")
      .length ?? 0;

  const nav: {
    id: Section;
    label: string;
    icon: typeof Flag;
    count?: number;
  }[] = [
    { id: "dashboard", label: s.navDashboard, icon: LayoutDashboard },
    { id: "comparison", label: s.navComparison, icon: Columns2 },
    { id: "flags", label: s.navFlags, icon: Flag, count: diffData?.flags.length },
    { id: "review", label: s.navReview, icon: ClipboardCheck, count: openFlags || undefined },
    { id: "report", label: s.navReport, icon: FileSignature },
  ];

  const heading: Record<Section, { title: string; lede: string }> = {
    dashboard: { title: s.dashTitle, lede: s.dashLede },
    comparison: { title: s.compTitle, lede: s.compLede },
    flags: { title: s.flagsTitle, lede: s.flagsLede },
    review: { title: s.reviewTitle, lede: s.reviewLede },
    report: { title: s.reportTitle, lede: s.reportLede },
    citizen: { title: s.citizenTitle, lede: s.citizenLede },
  };

  const label = (id: string) =>
    snapshots.find((x) => x.version_id === id)?.label || id;

  const navButton = (item: (typeof nav)[number] | { id: Section; label: string; icon: typeof Flag; count?: number }) => {
    const Icon = item.icon;
    const active = section === item.id;
    return (
      <button
        key={item.id}
        onClick={() => go(item.id)}
        aria-current={active ? "page" : undefined}
        className={`group relative flex shrink-0 items-center gap-3 rounded-xl px-3 py-2.5 text-left text-[15px] transition-colors lg:w-full ${
          active
            ? "bg-white/[0.09] text-white"
            : "text-ink-200/80 hover:bg-white/[0.05] hover:text-white"
        }`}
      >
        {active && (
          <span
            aria-hidden
            className="absolute left-0 top-1/2 hidden h-6 w-[5px] -translate-y-1/2 rounded-full bg-ink-400 lg:block"
          />
        )}
        <Icon
          className={`h-[18px] w-[18px] shrink-0 ${
            active ? "text-ink-300" : "text-ink-300/60 group-hover:text-ink-300"
          }`}
          strokeWidth={2}
        />
        <span className="font-medium">{item.label}</span>
        {item.count !== undefined && item.count > 0 && (
          <span
            className={`ml-auto rounded-full px-2 py-0.5 text-xs font-semibold tabular ${
              active ? "bg-ink-400 text-ink-950" : "bg-white/10 text-ink-100"
            }`}
          >
            {item.count}
          </span>
        )}
      </button>
    );
  };

  return (
    <div suppressHydrationWarning className="min-h-screen lg:flex">
      {/* Sidebar */}
      <aside className="z-20 bg-ink-950 text-white lg:sticky lg:top-0 lg:flex lg:h-screen lg:w-[264px] lg:shrink-0 lg:flex-col">
        <div className="flex items-center gap-3 px-5 pb-3 pt-5 lg:pb-6 lg:pt-7">
          <InkMark className="h-8 w-7" />
          <div>
            <div className="text-xl font-extrabold tracking-tight">
              {BRAND[language]}
            </div>
            <div className="text-xs text-ink-200/70">
              {s.brandSub}
            </div>
          </div>
        </div>

        {/* The pair of rolls being audited */}
        <div className="mx-4 mb-4 hidden rounded-2xl border border-white/10 bg-white/[0.04] p-3.5 text-sm lg:block">
          <div className="text-xs text-ink-200/60">{s.oldRoll}</div>
          <div className="truncate font-semibold text-white">
            {label(fromVersion)}
          </div>
          <div className="my-2 h-px bg-white/10" />
          <div className="text-xs text-ink-200/60">{s.newRoll}</div>
          <div className="truncate font-semibold text-white">
            {label(toVersion)}
          </div>
        </div>

        <nav className="flex gap-1 overflow-x-auto px-3 pb-3 lg:flex-1 lg:flex-col lg:overflow-visible lg:pb-0">
          {nav.map(navButton)}
          <div className="mx-3 my-3 hidden h-px bg-white/10 lg:block" />
          <div className="hidden px-3 pb-1 text-xs text-ink-200/50 lg:block">
            {s.navPublicGroup}
          </div>
          {navButton({ id: "citizen", label: s.navCitizen, icon: UserSearch })}
        </nav>

        <div className="hidden space-y-4 px-5 pb-6 lg:block">
          <div>
            <div className="mb-1.5 text-xs text-ink-200/60">{s.language}</div>
            <div className="grid grid-cols-3 gap-1 rounded-xl bg-white/[0.06] p-1">
              {LANGS.map((l) => (
                <button
                  key={l.code}
                  onClick={() => setLanguage(l.code)}
                  title={l.name}
                  aria-pressed={language === l.code}
                  className={`rounded-lg py-1.5 text-sm font-semibold transition-colors ${
                    language === l.code
                      ? "bg-white text-ink-950"
                      : "text-ink-200/80 hover:text-white"
                  }`}
                >
                  {l.label}
                </button>
              ))}
            </div>
          </div>
          <p className="text-xs leading-relaxed text-ink-200/60">
            {s.sidebarNote}
          </p>
        </div>
      </aside>

      {/* Main */}
      <div className="min-w-0 flex-1">
        <header className="border-b border-ink-950/[0.07] bg-canvas/90 px-5 py-6 backdrop-blur sm:px-8 lg:px-10 lg:py-8">
          <div className="mx-auto flex max-w-[1240px] flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
            <div className="max-w-[600px]">
              <h1 className="text-[28px] font-extrabold leading-[1.1] tracking-tight text-ink-950 sm:text-[34px]">
                {heading[section].title}
              </h1>
              <p className="mt-2.5 max-w-[62ch] text-[15px] leading-relaxed text-slate-600">
                {heading[section].lede}
              </p>
            </div>

            <div className="flex shrink-0 flex-wrap items-end gap-2 xl:flex-nowrap">
              <label className="block w-full sm:w-auto">
                <span className="mb-1 block text-xs font-medium text-slate-500">
                  {s.oldRoll}
                </span>
                <select
                  value={fromVersion}
                  onChange={(e) => setFromVersion(e.target.value)}
                  className="w-full rounded-xl sm:w-44 border border-ink-950/10 bg-white px-3 py-2 text-sm font-semibold text-ink-950 shadow-sm"
                >
                  {snapshots.map((x) => (
                    <option key={x.version_id} value={x.version_id} disabled={x.version_id === toVersion}>
                      {x.label || x.version_id}
                    </option>
                  ))}
                </select>
              </label>
              <span aria-hidden className="hidden pb-2.5 text-slate-400 sm:inline">
                →
              </span>
              <label className="block w-full sm:w-auto">
                <span className="mb-1 block text-xs font-medium text-slate-500">
                  {s.newRoll}
                </span>
                <select
                  value={toVersion}
                  onChange={(e) => setToVersion(e.target.value)}
                  className="w-full rounded-xl sm:w-44 border border-ink-950/10 bg-white px-3 py-2 text-sm font-semibold text-ink-950 shadow-sm"
                >
                  {snapshots.map((x) => (
                    <option key={x.version_id} value={x.version_id} disabled={x.version_id === fromVersion}>
                      {x.label || x.version_id}
                    </option>
                  ))}
                </select>
              </label>
              {/* Language on small screens (sidebar hides it) */}
              <div className="flex gap-1 rounded-xl bg-white p-1 shadow-sm lg:hidden">
                {LANGS.map((l) => (
                  <button
                    key={l.code}
                    onClick={() => setLanguage(l.code)}
                    aria-pressed={language === l.code}
                    className={`rounded-lg px-2.5 py-1 text-sm font-semibold ${
                      language === l.code ? "bg-ink-950 text-white" : "text-slate-600"
                    }`}
                  >
                    {l.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-[1240px] px-5 py-8 sm:px-8 lg:px-10">
          {backendError && (
            <div className="mb-6 rounded-2xl border border-removed/30 bg-removed-soft px-4 py-3 text-sm text-removed">
              {fmt(s.backendDown, { error: backendError })}
            </div>
          )}

          {section === "dashboard" && (
            <Dashboard
              language={language}
              snapshots={snapshots}
              fromVersion={fromVersion}
              toVersion={toVersion}
              onChangeVersions={(fv, tv) => {
                setFromVersion(fv);
                setToVersion(tv);
              }}
              onSnapshotIngested={handleSnapshotIngested}
              diffData={diffData}
              loading={loadingDiff}
              onNavigate={go}
            />
          )}

          {section === "comparison" && (
            <div className="space-y-8">
              <RollCompare
                language={language}
                fromVersion={fromVersion}
                toVersion={toVersion}
                diffData={diffData}
                loading={loadingDiff}
                onTraceEpic={handleInspectEpicInVerify}
              />
              <AuditWorkspace
                section="comparison"
                language={language}
                snapshots={snapshots}
                fromVersion={fromVersion}
                toVersion={toVersion}
                onChangeVersions={(fv, tv) => {
                  setFromVersion(fv);
                  setToVersion(tv);
                }}
                diffData={diffData}
                loading={loadingDiff}
                onInspectEpicInVerify={handleInspectEpicInVerify}
                onRefreshDiff={() => void loadDiff(fromVersion, toVersion, language)}
              />
            </div>
          )}

          {(section === "flags" || section === "review") && (
            <AuditWorkspace
              section={section}
              language={language}
              snapshots={snapshots}
              fromVersion={fromVersion}
              toVersion={toVersion}
              onChangeVersions={(fv, tv) => {
                setFromVersion(fv);
                setToVersion(tv);
              }}
              diffData={diffData}
              loading={loadingDiff}
              onInspectEpicInVerify={handleInspectEpicInVerify}
              onRefreshDiff={() => void loadDiff(fromVersion, toVersion, language)}
              selectedFlagId={selectedFlagId}
              onSelectFlag={setSelectedFlagId}
              onOpenReview={(id) => {
                setSelectedFlagId(id);
                go("review");
              }}
              openReviewLabel={s.openReview}
            />
          )}

          {section === "report" && (
            <AssuranceCenter
              language={language}
              fromVersion={fromVersion}
              toVersion={toVersion}
            />
          )}

          {section === "citizen" && (
            <VerifyPortal
              language={language}
              fromVersion={fromVersion}
              toVersion={toVersion}
              preselectedEpic={preselectedEpic}
            />
          )}
        </main>
      </div>
    </div>
  );
}
