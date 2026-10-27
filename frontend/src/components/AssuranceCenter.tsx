"use client";

import React, { useEffect, useState } from "react";
import {
  CheckCircle2,
  Download,
  FileKey2,
  Fingerprint,
  Link2,
  Printer,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  TableProperties,
} from "lucide-react";
import { fetchGapAnalysis, generateSignedReceipt } from "@/lib/api";
import {
  BrowserVerificationResult,
  verifyReceiptInBrowser,
} from "@/lib/cryptoVerify";
import {
  CORRECTION_ACTION_LABELS,
  fmt,
  getDict,
} from "@/lib/locales/common";
import { ASSURANCE_LOCALE } from "@/lib/locales/assurance";
import { AuditReceipt, GapAnalysisItem, LanguageCode } from "@/lib/types";

interface Props {
  language: LanguageCode;
  fromVersion: string;
  toVersion: string;
}

export default function AssuranceCenter({
  language,
  fromVersion,
  toVersion,
}: Props) {
  const assuranceT = getDict(ASSURANCE_LOCALE, language);
  const actionLabels = getDict(CORRECTION_ACTION_LABELS, language);

  const [originalReceipt, setOriginalReceipt] = useState<AuditReceipt | null>(
    null
  );
  const [activeReceipt, setActiveReceipt] = useState<AuditReceipt | null>(null);
  const [tampered, setTampered] = useState(false);
  const [verification, setVerification] =
    useState<BrowserVerificationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [gapItems, setGapItems] = useState<GapAnalysisItem[]>([]);

  useEffect(() => {
    void fetchGapAnalysis(language)
      .then(setGapItems)
      .catch(() => {});
  }, [language]);

  useEffect(() => {
    void handleIssueReceipt();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fromVersion, toVersion]);

  async function handleIssueReceipt() {
    setLoading(true);
    setTampered(false);
    try {
      const rcpt = await generateSignedReceipt(fromVersion, toVersion);
      setOriginalReceipt(rcpt);
      setActiveReceipt(rcpt);
      const vRes = await verifyReceiptInBrowser(rcpt);
      setVerification(vRes);
    } catch {
      // Handled gracefully without crashing Next.js overlay
    } finally {
      setLoading(false);
    }
  }

  async function handleToggleTamper() {
    if (!originalReceipt) return;
    if (tampered) {
      setTampered(false);
      setActiveReceipt(originalReceipt);
      const vRes = await verifyReceiptInBrowser(originalReceipt);
      setVerification(vRes);
      return;
    }

    // Mutate 1 number inside canonical_payload & payload without possessing private key
    const mutatedPayload = JSON.parse(originalReceipt.canonical_payload);
    if (mutatedPayload.ledger_totals) {
      mutatedPayload.ledger_totals.deleted = 999999;
    }
    const mutatedCanonical = JSON.stringify(mutatedPayload);
    const forged: AuditReceipt = {
      ...originalReceipt,
      payload: mutatedPayload,
      canonical_payload: mutatedCanonical,
    };
    setTampered(true);
    setActiveReceipt(forged);
    const vRes = await verifyReceiptInBrowser(forged);
    setVerification(vRes);
  }

  function handleDownloadReceipt() {
    if (!activeReceipt) return;
    const blob = new Blob([JSON.stringify(activeReceipt, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${activeReceipt.receipt_id.toLowerCase()}.polltoll-receipt.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-8">
      {/* Cryptographic Attestation & WebCrypto Verifier */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-2 text-xs font-mono font-semibold uppercase tracking-wider text-indigo-700">
              <FileKey2 className="h-4 w-4" />
              {assuranceT.receiptTag}
            </div>
            <h2 className="mt-1 text-lg font-bold text-slate-900">
              {assuranceT.receiptTitle}
            </h2>
            <p className="text-sm text-slate-600">
              {assuranceT.receiptSubtitle}
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => void handleIssueReceipt()}
              disabled={loading}
              className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              {loading ? assuranceT.reIssuingBtn : assuranceT.reIssueBtn}
            </button>
            <button
              onClick={() => void handleToggleTamper()}
              disabled={!originalReceipt}
              className={`inline-flex items-center gap-1.5 rounded-lg border px-3.5 py-2 text-xs font-semibold ${
                tampered
                  ? "border-emerald-600 bg-emerald-50 text-emerald-800 hover:bg-emerald-100"
                  : "border-rose-300 bg-rose-50 text-rose-800 hover:bg-rose-100"
              }`}
            >
              <ShieldAlert className="h-3.5 w-3.5" />
              {tampered
                ? assuranceT.restoreBtn
                : assuranceT.tamperBtn}
            </button>
            <button
              onClick={handleDownloadReceipt}
              disabled={!activeReceipt}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-800 hover:bg-slate-50"
            >
              <Download className="h-3.5 w-3.5" />
              {assuranceT.downloadBtn}
            </button>
            <button
              onClick={() => window.print()}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-800 hover:bg-slate-50"
            >
              <Printer className="h-3.5 w-3.5" />
              {assuranceT.printBtn}
            </button>
          </div>
        </div>

        {/* Live WebCrypto Verification Banner */}
        {verification && activeReceipt && (
          <div
            className={`rounded-xl border p-5 ${
              verification.valid
                ? "border-emerald-300 bg-emerald-50/70"
                : "border-rose-400 bg-rose-50"
            }`}
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                {verification.valid ? (
                  <ShieldCheck className="h-6 w-6 text-emerald-700" />
                ) : (
                  <ShieldAlert className="h-6 w-6 text-rose-700" />
                )}
                <div>
                  <div
                    className={`text-sm font-bold ${
                      verification.valid ? "text-emerald-950" : "text-rose-950"
                    }`}
                  >
                    {verification.valid
                      ? fmt(assuranceT.verifiedBanner, { engine: verification.engine })
                      : assuranceT.tamperBanner}
                  </div>
                  <div className="font-mono text-xs text-slate-600">
                    {fmt(assuranceT.receiptMeta, {
                      id: activeReceipt.receipt_id,
                      date: activeReceipt.generated_at_utc,
                    })}
                  </div>
                </div>
              </div>
              <span className="rounded bg-slate-900 px-2.5 py-1 font-mono text-xs text-emerald-300">
                {fmt(assuranceT.algPrefix, { alg: activeReceipt.signature_algorithm })}
              </span>
            </div>

            <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4 text-xs">
              {[
                {
                  label: assuranceT.chk1Canonical,
                  ok: verification.checks.payloadMatchesCanonicalJson,
                },
                {
                  label: assuranceT.chk2Sha256,
                  ok: verification.checks.sha256DigestMatches,
                },
                {
                  label: assuranceT.chk3Ed25519,
                  ok: verification.checks.ed25519SignatureValid,
                },
                {
                  label: assuranceT.chk4HashChain,
                  ok: verification.checks.correctionChainLinksIntact,
                },
              ].map((chk) => (
                <div
                  key={chk.label}
                  className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-3 py-2 font-medium"
                >
                  <span className="text-slate-800">{chk.label}</span>
                  <span
                    className={`font-mono font-bold ${
                      chk.ok ? "text-emerald-700" : "text-rose-700"
                    }`}
                  >
                    {chk.ok ? assuranceT.passText : assuranceT.failText}
                  </span>
                </div>
              ))}
            </div>

            {verification.failures.length > 0 && (
              <ul className="mt-3 list-disc space-y-1 pl-5 text-xs font-medium text-rose-900">
                {verification.failures.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            )}

            <div className="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-3 text-xs font-mono">
              <div className="rounded-lg bg-white p-3 border border-slate-200 truncate">
                <span className="text-slate-500 block">
                  {assuranceT.pubKeyLabel}
                </span>
                <span className="text-slate-900">
                  {activeReceipt.public_key_hex}
                </span>
              </div>
              <div className="rounded-lg bg-white p-3 border border-slate-200 truncate">
                <span className="text-slate-500 block">
                  {assuranceT.payloadDigestLabel}
                </span>
                <span className="text-slate-900">
                  {activeReceipt.payload_sha256}
                </span>
              </div>
              <div className="rounded-lg bg-white p-3 border border-slate-200 truncate">
                <span className="text-slate-500 block">
                  {assuranceT.sigLabel}
                </span>
                <span className="text-slate-900">
                  {activeReceipt.signature_hex}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Append-Only Correction Log Chain */}
        {activeReceipt && (
          <div>
            <h3 className="flex items-center gap-1.5 text-xs font-mono font-bold uppercase tracking-wider text-slate-700">
              <Link2 className="h-4 w-4 text-indigo-600" />
              {fmt(assuranceT.chainTitle, { count: activeReceipt.correction_history.length })}
            </h3>
            <div className="mt-3 space-y-2">
              {activeReceipt.correction_history.map((ev) => (
                <div
                  key={ev.event_id}
                  className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs flex flex-col gap-1 md:flex-row md:items-center md:justify-between"
                >
                  <div>
                    <span className="font-mono font-bold text-indigo-700">
                      {ev.event_id}
                    </span>{" "}
                    •{" "}
                    <span className="font-semibold text-slate-900">
                      {actionLabels[ev.action] || ev.action}
                    </span>{" "}
                    {fmt(assuranceT.onFlagBy, {
                      flagId: ev.flag_id,
                      role: ev.reviewer_role,
                    })}
                    <p className="mt-0.5 text-slate-700">{ev.note}</p>
                  </div>
                  <div className="font-mono text-slate-500 shrink-0 text-right">
                    <div>{fmt(assuranceT.prevHash, { hash: ev.prev_hash.slice(0, 12) })}</div>
                    <div className="text-slate-800 font-semibold">
                      {fmt(assuranceT.eventHash, { hash: ev.event_hash.slice(0, 12) })}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ERONET vs PollToll Feature-by-Feature Gap Analysis Matrix */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono font-semibold uppercase tracking-wider text-indigo-700">
            <TableProperties className="h-4 w-4" />
            {assuranceT.gapTag}
          </div>
          <h3 className="mt-1 text-lg font-bold text-slate-900">
            {assuranceT.gapTitle}
          </h3>
          <p className="text-sm text-slate-600">
            {assuranceT.gapSubtitle}
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
            <thead className="bg-slate-50 font-semibold text-slate-700">
              <tr>
                <th className="px-3 py-2.5">{assuranceT.colCapability}</th>
                <th className="px-3 py-2.5">
                  {assuranceT.colEronetStatus}
                </th>
                <th className="px-3 py-2.5">
                  {assuranceT.colEpistemicLimit}
                </th>
                <th className="px-3 py-2.5">{assuranceT.colAuditGap}</th>
                <th className="px-3 py-2.5">{assuranceT.colPolltollWedge}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {gapItems.map((g) => (
                <tr
                  key={g.id}
                  className={
                    g.is_prototype_core ? "bg-indigo-50/25" : "bg-white"
                  }
                >
                  <td className="px-3 py-3 font-semibold text-slate-900">
                    {g.capability}
                    {g.is_prototype_core && (
                      <span className="mt-1 block w-fit rounded bg-indigo-100 px-1.5 py-0.5 font-mono text-[12px] text-indigo-800">
                        {assuranceT.prototypeWedgeBadge}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-3 text-slate-600">
                    {g.eronet_documented_status}
                  </td>
                  <td className="px-3 py-3 text-slate-600">
                    {g.internal_epistemic_limit}
                  </td>
                  <td className="px-3 py-3 text-slate-800 font-medium">
                    {g.external_audit_gap}
                  </td>
                  <td className="px-3 py-3 text-indigo-950">
                    <span className="inline-flex items-start gap-1">
                      {g.is_prototype_core ? (
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 shrink-0 mt-0.5" />
                      ) : (
                        <Fingerprint className="h-3.5 w-3.5 text-slate-400 shrink-0 mt-0.5" />
                      )}
                      {g.polltoll_wedge}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
