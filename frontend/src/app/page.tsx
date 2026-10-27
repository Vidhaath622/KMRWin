"use client";

import React, { useCallback, useEffect, useState } from "react";
import {
  Activity,
  Cpu,
  FileKey2,
  GitCompare,
  Globe2,
  ShieldCheck,
  TerminalSquare,
} from "lucide-react";
import AssuranceCenter from "@/components/AssuranceCenter";
import AuditWorkspace from "@/components/AuditWorkspace";
import InfraConsole from "@/components/InfraConsole";
import VerifyPortal from "@/components/VerifyPortal";
import { fetchAuditDiff, fetchSnapshots } from "@/lib/api";
import { UI_STRINGS } from "@/lib/i18n";
import { BRAND, fmt } from "@/lib/locales/common";
import { PAGE_LOCALE } from "@/lib/locales/page";
import { LanguageCode, LedgerDiffResponse, SnapshotMeta } from "@/lib/types";

type ActivePlane = "audit" | "assurance" | "verify" | "infra";

export default function PollTollControlPlane() {
  const [mounted, setMounted] = useState(false);
  const [plane, setPlane] = useState<ActivePlane>("audit");
  const [language, setLanguage] = useState<LanguageCode>("en");
  const [snapshots, setSnapshots] = useState<SnapshotMeta[]>([]);
  const [fromVersion, setFromVersion] = useState("v2025_final");
  const [toVersion, setToVersion] = useState("v2026_draft");
  const [diffData, setDiffData] = useState<LedgerDiffResponse | null>(null);
  const [loadingDiff, setLoadingDiff] = useState(true);
  const [backendError, setBackendError] = useState<string | null>(null);
  const [preselectedEpic, setPreselectedEpic] = useState<string | null>(null);

  const t = UI_STRINGS[language];
  const pageT = PAGE_LOCALE[language];

  useEffect(() => {
    setMounted(true);
  }, []);

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
      .then((snaps) => {
        setSnapshots(snaps);
      })
      .catch((err) => setBackendError(String(err)));
  }, [language]);

  useEffect(() => {
    void loadDiff(fromVersion, toVersion, language);
  }, [fromVersion, toVersion, language, loadDiff]);

  function handleInspectEpicInVerify(epicId: string) {
    setPreselectedEpic(epicId);
    setPlane("verify");
  }

  function handleSnapshotIngested(newSnap: SnapshotMeta) {
    setSnapshots((prev) => [...prev, newSnap]);
    setFromVersion("v2026_draft");
    setToVersion(newSnap.version_id);
  }

  return (
    <div suppressHydrationWarning className="min-h-screen flex flex-col">
      {/* Infrastructure Telemetry Top Bar */}
      <div className="bg-slate-950 text-slate-300 border-b border-slate-800 px-4 py-2 text-xs font-mono">
        <div className="mx-auto max-w-7xl flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-3">
            <span className="inline-flex items-center gap-1.5 text-emerald-400 font-semibold">
              <Activity className="h-3.5 w-3.5" />
              {pageT.telemetryProtocol}
            </span>
            <span className="text-slate-600">|</span>
            <span>
              {fmt(pageT.telemetryRulePack, { pack: "polltoll-rules@1.0.0" })}
            </span>
            <span className="text-slate-600 hidden sm:inline">|</span>
            <span className="hidden sm:inline">
              {pageT.telemetryAttestation}
            </span>
          </div>
          <div className="text-amber-300/90 truncate">{t.guardrailBanner}</div>
        </div>
      </div>

      {/* Control Plane Header & Navigation */}
      <header className="bg-slate-900 text-white border-b border-slate-800 shadow-sm">
        <div className="mx-auto max-w-7xl px-4 pt-5 pb-0">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 font-mono text-base font-bold text-white shadow-inner">
                PT
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-bold tracking-tight">
                    {BRAND[language]}
                  </h1>
                  <span className="rounded bg-slate-800 px-2 py-0.5 font-mono text-xs text-indigo-300 border border-slate-700">
                    {pageT.brandBadge}
                  </span>
                </div>
                <p className="text-xs text-slate-400">{t.tagline}</p>
              </div>
            </div>

            {/* Multilingual Switcher */}
            <div className="flex items-center gap-2">
              <Globe2 className="h-4 w-4 text-slate-400" />
              <div className="inline-flex rounded-lg border border-slate-700 bg-slate-950 p-0.5 text-xs font-medium">
                {(
                  [
                    { code: "en", label: "English" },
                    { code: "hi", label: "हिन्दी" },
                    { code: "gu", label: "ગુજરાતી" },
                  ] as const
                ).map((l) => (
                  <button
                    key={l.code}
                    onClick={() => setLanguage(l.code)}
                    className={`rounded-md px-3 py-1 transition ${
                      language === l.code
                        ? "bg-indigo-600 text-white font-semibold"
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    {l.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* 4 Infrastructure Planes */}
          <nav className="flex gap-1 overflow-x-auto">
            {[
              {
                id: "audit" as const,
                icon: GitCompare,
                title: pageT.tabAudit,
                sub: pageT.tabAuditSub,
              },
              {
                id: "assurance" as const,
                icon: FileKey2,
                title: pageT.tabAssurance,
                sub: pageT.tabAssuranceSub,
              },
              {
                id: "verify" as const,
                icon: ShieldCheck,
                title: pageT.tabVerify,
                sub: pageT.tabVerifySub,
              },
              {
                id: "infra" as const,
                icon: TerminalSquare,
                title: pageT.tabInfra,
                sub: pageT.tabInfraSub,
              },
            ].map((item) => {
              const Icon = item.icon;
              const active = plane === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setPlane(item.id)}
                  className={`flex items-center gap-2.5 rounded-t-xl px-4 py-3 text-left transition border-t border-x ${
                    active
                      ? "bg-slate-100 text-slate-900 border-slate-200 font-semibold"
                      : "bg-slate-900/50 text-slate-400 border-transparent hover:bg-slate-800/70 hover:text-slate-200"
                  }`}
                >
                  <Icon
                    className={`h-4 w-4 shrink-0 ${
                      active ? "text-indigo-600" : "text-slate-400"
                    }`}
                  />
                  <div>
                    <div className="text-xs font-bold leading-none">
                      {item.title}
                    </div>
                    <div
                      className={`mt-1 text-xs leading-none ${
                        active ? "text-slate-600" : "text-slate-500"
                      }`}
                    >
                      {item.sub}
                    </div>
                  </div>
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Main Plane Content */}
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6">
        {backendError && (
          <div className="mb-6 rounded-xl border border-rose-300 bg-rose-50 p-4 text-xs text-rose-900 font-mono">
            {fmt(pageT.backendErrorWarning, { error: backendError })}
          </div>
        )}

        {plane === "audit" && (
          <AuditWorkspace
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
        )}

        {plane === "assurance" && (
          <AssuranceCenter
            language={language}
            fromVersion={fromVersion}
            toVersion={toVersion}
          />
        )}

        {plane === "verify" && (
          <VerifyPortal
            language={language}
            fromVersion={fromVersion}
            toVersion={toVersion}
            preselectedEpic={preselectedEpic}
          />
        )}

        {plane === "infra" && (
          <InfraConsole
            language={language}
            snapshots={snapshots}
            onSnapshotIngested={handleSnapshotIngested}
          />
        )}
      </main>

      {/* Infrastructure Footer */}
      <footer className="border-t border-slate-200 bg-white px-4 py-4 text-xs text-slate-500">
        <div className="mx-auto max-w-7xl flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2 font-mono">
            <Cpu className="h-3.5 w-3.5 text-indigo-600" />
            <span>{pageT.footerProtocol}</span>
          </div>
          <div>{pageT.footerDisclaimer}</div>
        </div>
      </footer>
    </div>
  );
}
