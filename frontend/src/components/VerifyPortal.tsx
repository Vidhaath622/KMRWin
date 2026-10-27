"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  CheckCircle2,
  HelpCircle,
  Mic,
  MicOff,
  Search,
  ShieldAlert,
  Volume2,
  XCircle,
} from "lucide-react";
import { checkViralClaim, queryCitizenAssistant } from "@/lib/api";
import { PRESET_CLAIMS, UI_STRINGS } from "@/lib/i18n";
import {
  CITIZEN_STATUS_LABELS,
  fmt,
  getDict,
} from "@/lib/locales/common";
import { VERIFY_LOCALE } from "@/lib/locales/verify";
import {
  CitizenAssistantResponse,
  ClaimCheckResponse,
  LanguageCode,
} from "@/lib/types";

interface Props {
  language: LanguageCode;
  fromVersion: string;
  toVersion: string;
  preselectedEpic: string | null;
}

export default function VerifyPortal({
  language,
  fromVersion,
  toVersion,
  preselectedEpic,
}: Props) {
  const t = UI_STRINGS[language];
  const verifyT = getDict(VERIFY_LOCALE, language);
  const citizenStatusLabels = getDict(CITIZEN_STATUS_LABELS, language);

  const [epicInput, setEpicInput] = useState(
    preselectedEpic || "SYN-GJ-109-0042"
  );
  const [questionInput, setQuestionInput] = useState("");
  const [assistantRes, setAssistantRes] =
    useState<CitizenAssistantResponse | null>(null);
  const [loadingAssistant, setLoadingAssistant] = useState(false);
  const [recording, setRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const [claimInput, setClaimInput] = useState(
    PRESET_CLAIMS[language][0].claim
  );
  const [claimRes, setClaimRes] = useState<ClaimCheckResponse | null>(null);
  const [loadingClaim, setLoadingClaim] = useState(false);

  const demoEpics = [
    {
      epic: "SYN-GJ-109-0042",
      tag: verifyT.epicDemoTags["SYN-GJ-109-0042"] || "Booth Split",
    },
    {
      epic: "SYN-GJ-104-0019",
      tag: verifyT.epicDemoTags["SYN-GJ-104-0019"] || "Draft Hostel Deletion",
    },
    {
      epic: "SYN-GJ-207-0011",
      tag: verifyT.epicDemoTags["SYN-GJ-207-0011"] || "Age Typo",
    },
    {
      epic: "SYN-GJ-201-0008",
      tag: verifyT.epicDemoTags["SYN-GJ-201-0008"] || "Active & Unchanged",
    },
  ];

  useEffect(() => {
    setClaimInput(PRESET_CLAIMS[language][0].claim);
  }, [language]);

  useEffect(() => {
    if (preselectedEpic) {
      setEpicInput(preselectedEpic);
      void runAssistantLookup(preselectedEpic, "", undefined, undefined, false);
    } else {
      void runAssistantLookup("SYN-GJ-109-0042", "", undefined, undefined, false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [preselectedEpic, language]);

  useEffect(() => {
    void runClaimCheck(PRESET_CLAIMS[language][0].claim, false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [language, fromVersion, toVersion]);

  async function runAssistantLookup(
    epic: string,
    q: string,
    audioB64?: string,
    audioMime?: string,
    useLlm = true
  ) {
    setLoadingAssistant(true);
    try {
      const res = await queryCitizenAssistant({
        epic_id: epic.trim() || undefined,
        query: q,
        language,
        audio_base64: audioB64,
        audio_mime_type: audioMime,
        include_tts: false,
        use_llm: useLlm,
      });
      setAssistantRes(res);
      if (res.tts_audio_base64) {
        playBase64Audio(res.tts_audio_base64, res.tts_mime_type || "audio/wav");
      }
    } catch {
      // Prevent unhandled promise rejection overlay on transient reload
    } finally {
      setLoadingAssistant(false);
    }
  }

  async function runClaimCheck(textToAudit: string, useLlm = true) {
    if (textToAudit.trim().length < 6) return;
    setLoadingClaim(true);
    try {
      const res = await checkViralClaim({
        claim_text: textToAudit.trim(),
        from_version: fromVersion,
        to_version: toVersion,
        language,
        use_llm: useLlm,
      });
      setClaimRes(res);
    } catch {
      // Prevent unhandled promise rejection overlay on transient reload
    } finally {
      setLoadingClaim(false);
    }
  }

  function playBase64Audio(b64: string, mime: string) {
    const audio = new Audio(`data:${mime};base64,${b64}`);
    void audio.play();
  }

  function handleSpeakAloud() {
    if (!assistantRes) return;
    if (assistantRes.tts_audio_base64) {
      playBase64Audio(
        assistantRes.tts_audio_base64,
        assistantRes.tts_mime_type || "audio/wav"
      );
      return;
    }
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(assistantRes.answer_text);
      utter.lang =
        language === "hi" ? "hi-IN" : language === "gu" ? "gu-IN" : "en-IN";
      window.speechSynthesis.speak(utter);
    }
  }

  async function toggleVoiceRecording() {
    if (recording) {
      mediaRecorderRef.current?.stop();
      setRecording(false);
      return;
    }

    // Zero-quota fast path: Browser Web Speech API (0 Gemini audio tokens consumed!)
    const win = window as unknown as Record<string, unknown>;
    const SpeechRecCtor = (win.SpeechRecognition || win.webkitSpeechRecognition) as
      | (new () => {
          lang: string;
          interimResults: boolean;
          onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
          onerror: (() => void) | null;
          onend: (() => void) | null;
          start: () => void;
        })
      | undefined;

    if (SpeechRecCtor) {
      const rec = new SpeechRecCtor();
      rec.lang =
        language === "hi" ? "hi-IN" : language === "gu" ? "gu-IN" : "en-IN";
      rec.interimResults = false;
      setRecording(true);
      rec.onresult = (event) => {
        const spoken = event.results?.[0]?.[0]?.transcript || "";
        if (spoken) {
          setQuestionInput(spoken);
          void runAssistantLookup(epicInput, spoken, undefined, undefined, true);
        }
      };
      rec.onerror = () => setRecording(false);
      rec.onend = () => setRecording(false);
      rec.start();
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      audioChunksRef.current = [];
      mr.ondataavailable = (ev) => {
        if (ev.data.size > 0) audioChunksRef.current.push(ev.data);
      };
      mr.onstop = async () => {
        stream.getTracks().forEach((tr) => tr.stop());
        const blob = new Blob(audioChunksRef.current, {
          type: mr.mimeType || "audio/webm",
        });
        const reader = new FileReader();
        reader.onloadend = () => {
          const dataUrl = String(reader.result || "");
          const b64 = dataUrl.includes(",") ? dataUrl.split(",")[1] : "";
          void runAssistantLookup(
            epicInput,
            questionInput || verifyT.voiceCheckDefaultQuery,
            b64,
            blob.type || "audio/webm"
          );
        };
        reader.readAsDataURL(blob);
      };
      mediaRecorderRef.current = mr;
      mr.start();
      setRecording(true);
    } catch {
      alert(verifyT.micPermissionAlert);
    }
  }

  return (
    <div className="space-y-8">
      {/* Citizen Assistant Section */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div>
            <span className="inline-block rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-semibold text-indigo-700 border border-indigo-200">
              {verifyT.publicServiceBadge}
            </span>
            <h2 className="mt-2 text-lg font-bold text-slate-900">
              {t.citizenTitle}
            </h2>
            <p className="text-sm text-slate-600">{t.citizenSubtitle}</p>
          </div>
        </div>

        {/* Quick synthetic EPIC demo pills */}
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium text-slate-500">
            {verifyT.testEpicsLabel}
          </span>
          {demoEpics.map((d) => (
            <button
              key={d.epic}
              onClick={() => {
                setEpicInput(d.epic);
                void runAssistantLookup(d.epic, questionInput);
              }}
              className={`rounded-full border px-3 py-1 text-xs font-medium transition ${
                epicInput === d.epic
                  ? "border-indigo-600 bg-indigo-600 text-white"
                  : "border-slate-300 bg-slate-50 text-slate-700 hover:bg-slate-100"
              }`}
            >
              <span className="font-mono">{d.epic}</span> — {d.tag}
            </button>
          ))}
        </div>

        {/* Inputs */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void runAssistantLookup(epicInput, questionInput);
          }}
          className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-12"
        >
          <input
            type="text"
            value={epicInput}
            onChange={(e) => setEpicInput(e.target.value)}
            placeholder={t.epicPlaceholder}
            className="md:col-span-3 rounded-lg border border-slate-300 px-3 py-2 text-sm font-mono"
          />
          <input
            type="text"
            value={questionInput}
            onChange={(e) => setQuestionInput(e.target.value)}
            placeholder={t.questionPlaceholder}
            className="md:col-span-5 rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
          <div className="md:col-span-4 flex gap-2">
            <button
              type="submit"
              disabled={loadingAssistant}
              className="flex-1 inline-flex items-center justify-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              <Search className="h-4 w-4" />
              {loadingAssistant ? "..." : t.askButton}
            </button>
            <button
              type="button"
              onClick={() => void toggleVoiceRecording()}
              className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-2 text-sm font-medium ${
                recording
                  ? "border-rose-500 bg-rose-50 text-rose-700 animate-pulse"
                  : "border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
              }`}
            >
              {recording ? (
                <>
                  <MicOff className="h-4 w-4" /> {t.stopRecording}
                </>
              ) : (
                <>
                  <Mic className="h-4 w-4" /> {t.speakButton}
                </>
              )}
            </button>
          </div>
        </form>

        {/* Assistant Output */}
        {assistantRes && (
          <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50/70 p-5 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                {assistantRes.lookup_result && (
                  <span
                    className={`rounded-full px-3 py-0.5 text-xs font-semibold ${
                      assistantRes.lookup_result.current_status.startsWith(
                        "ACTIVE"
                      )
                        ? "bg-emerald-100 text-emerald-900 border border-emerald-300"
                        : "bg-amber-100 text-amber-900 border border-amber-300"
                    }`}
                  >
                    {citizenStatusLabels[assistantRes.lookup_result.current_status] ||
                      assistantRes.lookup_result.current_status.replaceAll("_", " ")}
                  </span>
                )}
                <span className="text-xs text-slate-500">
                  {fmt(verifyT.confidencePrefix, {
                    pct: (assistantRes.confidence_level * 100).toFixed(0),
                  })}{" "}
                  • {fmt(verifyT.enginePrefix, { engine: assistantRes.generated_by })}
                </span>
              </div>
              <button
                type="button"
                onClick={handleSpeakAloud}
                className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-200 bg-white px-3 py-1 text-xs font-semibold text-indigo-700 hover:bg-indigo-50"
              >
                <Volume2 className="h-3.5 w-3.5" /> {t.listenButton}
              </button>
            </div>

            {assistantRes.recognized_transcript && (
              <div className="text-xs italic text-slate-600">
                {fmt(verifyT.voiceTranscriptPrefix, {
                  transcript: assistantRes.recognized_transcript,
                })}
              </div>
            )}

            <p className="text-base font-medium leading-relaxed text-slate-900">
              {assistantRes.answer_text}
            </p>

            {/* 4-Cycle Longitudinal Lineage Timeline */}
            {assistantRes.lookup_result &&
              assistantRes.lookup_result.version_history.length > 0 && (
                <div>
                  <div className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-2">
                    {fmt(verifyT.timelineTitle, {
                      epic: assistantRes.lookup_result.epic_id,
                    })}
                  </div>
                  <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
                    {assistantRes.lookup_result.version_history.map((vh) => (
                      <div
                        key={String(vh.version_id)}
                        className="rounded-lg border border-slate-200 bg-white p-3 text-xs"
                      >
                        <div className="font-mono font-bold text-indigo-700">
                          {String(vh.version_id)}
                        </div>
                        <div className="mt-1 font-semibold text-slate-900">
                          {String(vh.booth_id)} •{" "}
                          {fmt(verifyT.serialPrefix, { sno: String(vh.serial_no) })}
                        </div>
                        <div className="text-slate-600 truncate">
                          {String(vh.booth_name)}
                        </div>
                        <div className="mt-1 text-slate-500 font-mono">
                          {fmt(verifyT.agePrefix, { age: String(vh.age) })} •{" "}
                          {fmt(verifyT.housePrefix, { house: String(vh.house_no) })}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            {/* Official Next Steps & Forms */}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="rounded-lg border border-slate-200 bg-white p-3.5">
                <div className="text-xs font-semibold uppercase tracking-wide text-slate-700">
                  {verifyT.officialStepsTitle}
                </div>
                <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-slate-700">
                  {assistantRes.official_next_steps.map((st, idx) => (
                    <li key={idx}>{st}</li>
                  ))}
                </ul>
                {assistantRes.referenced_forms.length > 0 && (
                  <div className="mt-2 flex gap-1.5">
                    {assistantRes.referenced_forms.map((f) => (
                      <span
                        key={f}
                        className="rounded bg-indigo-50 px-2 py-0.5 text-xs font-semibold text-indigo-800 border border-indigo-200"
                      >
                        ECI {f}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <div className="rounded-lg border border-slate-200 bg-white p-3.5">
                <div className="text-xs font-semibold uppercase tracking-wide text-slate-700">
                  {verifyT.reasoningTraceTitle}
                </div>
                <ol className="mt-2 list-decimal space-y-1 pl-4 text-xs text-slate-600">
                  {assistantRes.reasoning_steps.map((r, idx) => (
                    <li key={idx}>{r}</li>
                  ))}
                </ol>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Viral Claim Checker Section */}
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-5">
        <div>
          <span className="inline-block rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-800 border border-amber-200">
            {verifyT.equalStandardsBadge}
          </span>
          <h2 className="mt-2 text-lg font-bold text-slate-900">
            {t.claimTitle}
          </h2>
          <p className="text-sm text-slate-600">{t.claimSubtitle}</p>
        </div>

        {/* Preset Viral Claims */}
        <div className="flex flex-wrap gap-2">
          {PRESET_CLAIMS[language].map((p, i) => (
            <button
              key={i}
              onClick={() => {
                setClaimInput(p.claim);
                void runClaimCheck(p.claim);
              }}
              className="rounded-lg border border-slate-300 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-800 hover:bg-slate-100"
            >
              {p.label}
            </button>
          ))}
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            void runClaimCheck(claimInput);
          }}
          className="flex flex-col gap-3 sm:flex-row"
        >
          <input
            type="text"
            value={claimInput}
            onChange={(e) => setClaimInput(e.target.value)}
            className="flex-1 rounded-lg border border-slate-300 px-3.5 py-2 text-sm"
            placeholder={verifyT.claimPlaceholder}
          />
          <button
            type="submit"
            disabled={loadingClaim}
            className="rounded-lg bg-slate-900 px-5 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50"
          >
            {loadingClaim ? verifyT.checkingClaimBtn : t.checkClaimBtn}
          </button>
        </form>

        {claimRes && (
          <div className="space-y-4 rounded-xl border border-slate-200 bg-slate-50 p-5">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 pb-3">
              <div>
                <div className="text-xs font-semibold uppercase tracking-wide text-indigo-700">
                  {verifyT.verdictHeader}
                </div>
                <div className="mt-0.5 text-base font-bold text-slate-900">
                  {claimRes.overall_assessment_label}
                </div>
              </div>
              <div className="text-right text-xs text-slate-600">
                <div>
                  {verifyT.confidenceLabel}{" "}
                  <strong>
                    {(claimRes.confidence_level * 100).toFixed(0)}%
                  </strong>
                </div>
                <div className="font-mono">
                  {verifyT.boothsLabel} {claimRes.referenced_booths.join(", ")}
                </div>
              </div>
            </div>

            {/* 3 Epistemic Buckets */}
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
              <div className="rounded-xl border border-emerald-200 bg-white p-4">
                <h4 className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-emerald-800">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  {t.verifiedCol}
                </h4>
                <div className="mt-3 space-y-2.5">
                  {claimRes.verified_facts.map((item, idx) => (
                    <div key={idx} className="text-xs">
                      <p className="font-medium text-slate-800">
                        {item.statement}
                      </p>
                      <span className="mt-0.5 block font-mono text-[11px] text-emerald-700">
                        {fmt(verifyT.sourceLabel, { src: item.evidence_source })}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-xl border border-amber-200 bg-white p-4">
                <h4 className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-amber-800">
                  <XCircle className="h-4 w-4 text-amber-600" />
                  {t.disputedCol}
                </h4>
                <div className="mt-3 space-y-2.5">
                  {claimRes.disputed_interpretations.map((item, idx) => (
                    <div key={idx} className="text-xs">
                      <p className="font-medium text-slate-800">
                        {item.statement}
                      </p>
                      <span className="mt-0.5 block font-mono text-[11px] text-amber-700">
                        {fmt(verifyT.basisLabel, { basis: item.evidence_source })}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-xl border border-sky-200 bg-white p-4">
                <h4 className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-sky-900">
                  <HelpCircle className="h-4 w-4 text-sky-600" />
                  {t.unprovableCol}
                </h4>
                <div className="mt-3 space-y-2.5">
                  {claimRes.unprovable_from_public_data.map((item, idx) => (
                    <div key={idx} className="text-xs">
                      <p className="font-medium text-slate-800">
                        {item.statement}
                      </p>
                      <span className="mt-0.5 block font-mono text-[11px] text-sky-700">
                        {fmt(verifyT.missingLabel, { missing: item.evidence_source })}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-2 rounded-lg border border-slate-200 bg-white p-3 text-xs text-slate-600 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-1.5">
                <ShieldAlert className="h-4 w-4 text-indigo-600 shrink-0" />
                <span>{claimRes.neutrality_guardrail_note}</span>
              </div>
              <span className="font-mono text-[11px] text-slate-400 shrink-0">
                {claimRes.confidence_basis}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
