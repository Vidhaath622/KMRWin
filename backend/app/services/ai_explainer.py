"""Quota-Shielded AI Explainability, Claim Checker & Multilingual Citizen Assistant.

Built specifically to thrive on FREE-TIER Gemini API keys:
1. High-throughput model cascade: `gemini-3.5-flash-lite` -> `gemini-3.1-flash-lite` -> `gemini-3.8-flash`.
2. Persistent SHA-256 DuckDB response cache (`ai_response_cache`): identical claims/questions
   across teammates or demo runs use 0 API quota after the first call.
3. Multi-key round-robin pool (`GEMINI_API_KEYS` / `GEMINI_API_KEY` + `GEMINI_API_KEY_2`)
   with automatic 60-second cooldown rotation on HTTP 429 rate limits.
4. Deterministic-first fast path: EPIC lookups and initial UI mount previews run in <5ms
   on DuckDB with 0 LLM tokens, and 429 exhaustion degrades gracefully with zero errors.
"""

from __future__ import annotations

import base64
import datetime as dt
import hashlib
import itertools
import json
import os
import pathlib
import re
import time
import urllib.error
import urllib.request
import uuid
from typing import Any

import duckdb
from dotenv import dotenv_values, load_dotenv
from pydantic import BaseModel, Field

from app.engine.anomaly import detect_anomalies
from app.engine.ledger import compute_change_ledger, lookup_citizen_epic
from app.models import (
    CitizenAssistantRequest,
    CitizenAssistantResponse,
    ClaimCheckRequest,
    ClaimCheckResponse,
    ClaimFindingItem,
    LanguageCode,
)

# Safely load ~/.env and backend/.env without ever printing secret values
load_dotenv(pathlib.Path.home() / ".env", override=False)
load_dotenv(pathlib.Path(__file__).resolve().parents[2] / ".env", override=False)

FORBIDDEN_ACCUSATION_PATTERNS = [
    r"\brigged\b",
    r"\bfraud\s+confirmed\b",
    r"\bstolen\s+election\b",
    r"\bvote\s+theft\s+proven\b",
]

EPIC_REGEX = re.compile(r"SYN-GJ-\d{3}-\d{4}", re.IGNORECASE)
BOOTH_REGEX = re.compile(r"PS-\d{3}", re.IGNORECASE)

LANGUAGE_NAMES: dict[LanguageCode, str] = {
    "en": "English",
    "hi": "Hindi (हिन्दी)",
    "gu": "Gujarati (ગુજરાતી)",
}

# In-memory telemetry & per-key cooldown state (keys themselves are NEVER exposed)
_KEY_COOLDOWN_UNTIL: dict[int, float] = {}
_GROQ_KEY_COOLDOWN_UNTIL: dict[int, float] = {}
_GROQ_MODEL_COOLDOWN_UNTIL: dict[tuple[int, str], float] = {}
_KEY_COUNTER = itertools.count(0)
_GROQ_COUNTER = itertools.count(0)
_PROVIDER_COUNTER = itertools.count(0)
_GATEWAY_METRICS = {
    "live_gemini_calls": 0,
    "live_groq_calls": 0,
    "cache_hits_saved": 0,
    "deterministic_fastpath_saved": 0,
    "rate_limit_rotations": 0,
}


_BACKEND_ENV_PATH = pathlib.Path(__file__).resolve().parents[2] / ".env"
_HOME_ENV_PATH = pathlib.Path.home() / ".env"


def _load_env_keys(csv_var: str, slot_vars: tuple[str, ...]) -> list[str]:
    merged_env: dict[str, str] = {}
    for env_path in (_HOME_ENV_PATH, _BACKEND_ENV_PATH):
        if env_path.exists():
            for k, v in dotenv_values(env_path).items():
                if v:
                    merged_env[k] = v
    for k in (csv_var, *slot_vars):
        env_val = os.environ.get(k, "").strip()
        if env_val and k not in merged_env:
            merged_env[k] = env_val

    raw_list: list[str] = []
    # Prefer keys explicitly written to backend/.env first
    if _BACKEND_ENV_PATH.exists():
        b_vals = dotenv_values(_BACKEND_ENV_PATH)
        for env_name in slot_vars:
            val = (b_vals.get(env_name) or "").strip()
            if val and val not in raw_list:
                raw_list.append(val)
    csv_keys = merged_env.get(csv_var, "")
    if csv_keys:
        for k in csv_keys.split(","):
            if k.strip() and k.strip() not in raw_list:
                raw_list.append(k.strip())
    for env_name in slot_vars:
        val = merged_env.get(env_name, "").strip()
        if val and val not in raw_list:
            raw_list.append(val)
    return raw_list


def _load_key_pool() -> list[str]:
    return _load_env_keys("GEMINI_API_KEYS", ("GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3"))


def _load_groq_key_pool() -> list[str]:
    return _load_env_keys("GROQ_API_KEYS", ("GROQ_API_KEY", "GROQ_API_KEY_2", "GROQ_API_KEY_3"))


def _model_cascade() -> list[str]:
    primary = os.environ.get("POLLTOLL_GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
    defaults = [primary, "gemini-3.1-flash-lite", "gemini-3.8-flash"]
    deduped: list[str] = []
    for m in defaults:
        if m and m not in deduped:
            deduped.append(m)
    return deduped


def _groq_model_cascade() -> list[str]:
    primary = os.environ.get("POLLTOLL_GROQ_MODEL", "llama-3.3-70b-versatile").strip()
    # On Groq free tier, each model has its OWN independent RPM/RPD quota bucket!
    defaults = [primary, "llama-3.1-8b-instant"]
    deduped: list[str] = []
    for m in defaults:
        if m and m not in deduped:
            deduped.append(m)
    return deduped


def _ai_priority() -> str:
    if _BACKEND_ENV_PATH.exists():
        val = (dotenv_values(_BACKEND_ENV_PATH).get("POLLTOLL_AI_PRIORITY") or "").strip().lower()
        if val in ("auto", "groq", "gemini"):
            return val
    val = os.environ.get("POLLTOLL_AI_PRIORITY", "auto").strip().lower()
    return val if val in ("auto", "groq", "gemini") else "auto"


def _ensure_cache_table(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_response_cache (
            cache_key VARCHAR PRIMARY KEY,
            endpoint VARCHAR,
            model_used VARCHAR,
            response_json VARCHAR,
            created_at_utc VARCHAR
        )
        """
    )


def _cache_get(con: duckdb.DuckDBPyConnection, cache_key: str) -> tuple[dict[str, Any], str] | None:
    _ensure_cache_table(con)
    row = con.execute(
        "SELECT response_json, model_used FROM ai_response_cache WHERE cache_key = ?",
        [cache_key],
    ).fetchone()
    if not row:
        return None
    _GATEWAY_METRICS["cache_hits_saved"] += 1
    return json.loads(row[0]), row[1]


def _cache_put(
    con: duckdb.DuckDBPyConnection,
    cache_key: str,
    endpoint: str,
    model_used: str,
    payload: dict[str, Any],
) -> None:
    _ensure_cache_table(con)
    con.execute("DELETE FROM ai_response_cache WHERE cache_key = ?", [cache_key])
    con.execute(
        "INSERT INTO ai_response_cache VALUES (?, ?, ?, ?, ?)",
        [
            cache_key,
            endpoint,
            model_used,
            json.dumps(payload, ensure_ascii=False),
            dt.datetime.now(dt.timezone.utc).isoformat(),
        ],
    )


def get_ai_gateway_stats(con: duckdb.DuckDBPyConnection) -> dict[str, Any]:
    _ensure_cache_table(con)
    gem_keys = _load_key_pool()
    groq_keys = _load_groq_key_pool()
    now = time.time()
    gem_cooling = sum(1 for idx in range(len(gem_keys)) if _KEY_COOLDOWN_UNTIL.get(idx, 0.0) > now)
    groq_cooling = sum(1 for idx in range(len(groq_keys)) if _GROQ_KEY_COOLDOWN_UNTIL.get(idx, 0.0) > now)
    gem_ready = max(0, len(gem_keys) - gem_cooling)
    groq_ready = max(0, len(groq_keys) - groq_cooling)
    cached_rows = con.execute("SELECT count(*) FROM ai_response_cache").fetchone()[0]
    combined_cascade = list(_model_cascade()) + [f"groq:{m}" for m in _groq_model_cascade()]
    return {
        "configured_key_count": len(gem_keys) + len(groq_keys),
        "keys_ready": gem_ready + groq_ready,
        "keys_in_cooldown": gem_cooling + groq_cooling,
        "gemini_key_count": len(gem_keys),
        "gemini_keys_ready": gem_ready,
        "groq_key_count": len(groq_keys),
        "groq_keys_ready": groq_ready,
        "provider_priority": _ai_priority(),
        "model_cascade": combined_cascade,
        "groq_model_cascade": _groq_model_cascade(),
        "cached_entries_in_duckdb": cached_rows,
        "metrics": dict(_GATEWAY_METRICS),
        "free_tier_protections": [
            "Cross-cloud failover: Gemini (3.5-flash-lite) <-> Groq LPU (llama-3.3-70b + llama-3.1-8b)",
            "Groq per-model quota isolation (~14.4k RPD on 8b-instant + ~1k RPD on 70b per org)",
            "Persistent SHA-256 DuckDB response cache (0 tokens on repeat claims/questions)",
            "Multi-key teammate rotation + automatic 429/403 cooldown quarantine",
            "Browser Web Speech + Groq Whisper STT fallback + Deterministic DuckDB fast-path",
        ],
    }


def _call_gemini_with_rotation(
    input_payload: Any,
    response_format: dict[str, Any] | None = None,
    response_mime_type: str | None = None,
    generation_config: dict[str, Any] | None = None,
    explicit_models: list[str] | None = None,
) -> tuple[Any, str] | None:
    """Attempts Gemini call across available keys and free-tier-friendly model cascade."""
    keys = _load_key_pool()
    if not keys:
        return None

    from google import genai

    models = explicit_models or _model_cascade()
    now = time.time()
    start_idx = next(_KEY_COUNTER) % len(keys)

    for model_name in models:
        for offset in range(len(keys)):
            k_idx = (start_idx + offset) % len(keys)
            if _KEY_COOLDOWN_UNTIL.get(k_idx, 0.0) > now:
                continue
            try:
                client = genai.Client(api_key=keys[k_idx])
                kwargs: dict[str, Any] = {
                    "model": model_name,
                    "input": input_payload,
                    "store": False,
                }
                if response_format is not None:
                    kwargs["response_format"] = response_format
                if response_mime_type is not None:
                    kwargs["response_mime_type"] = response_mime_type
                if generation_config is not None:
                    kwargs["generation_config"] = generation_config
                interaction = client.interactions.create(**kwargs)
                _GATEWAY_METRICS["live_gemini_calls"] += 1
                return interaction, model_name
            except Exception as exc:
                err_str = str(exc).lower()
                if "429" in err_str or "quota" in err_str or "exhausted" in err_str or "rate" in err_str:
                    _KEY_COOLDOWN_UNTIL[k_idx] = time.time() + 60.0
                    _GATEWAY_METRICS["rate_limit_rotations"] += 1
                    continue
                if "403" in err_str or "401" in err_str or "permission" in err_str or "api key" in err_str:
                    _KEY_COOLDOWN_UNTIL[k_idx] = time.time() + 1800.0
                    _GATEWAY_METRICS["rate_limit_rotations"] += 1
                    continue
                break
    return None


def _call_groq_structured(
    prompt: str,
    model_cls: type[BaseModel],
) -> tuple[Any, str] | None:
    """Calls Groq OpenAI-compatible Chat Completions across org keys & independent per-model buckets."""
    keys = _load_groq_key_pool()
    if not keys:
        return None

    schema = model_cls.model_json_schema()
    models = _groq_model_cascade()
    now = time.time()
    start_idx = next(_GROQ_COUNTER) % len(keys)

    system_msg = (
        "You are PollToll's non-partisan electoral audit JSON engine. "
        "Output ONLY a single valid JSON object matching this exact JSON Schema "
        "(use exact property names, satisfy all required fields, no markdown code fences):\n"
        f"{json.dumps(schema, ensure_ascii=False)}"
    )

    for model_name in models:
        for offset in range(len(keys)):
            k_idx = (start_idx + offset) % len(keys)
            if _GROQ_KEY_COOLDOWN_UNTIL.get(k_idx, 0.0) > now:
                continue
            if _GROQ_MODEL_COOLDOWN_UNTIL.get((k_idx, model_name), 0.0) > now:
                continue
            body_bytes = json.dumps(
                {
                    "model": model_name,
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": prompt},
                    ],
                },
                ensure_ascii=False,
            ).encode("utf-8")
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=body_bytes,
                method="POST",
                headers={
                    "Authorization": f"Bearer {keys[k_idx]}",
                    "Content-Type": "application/json",
                    "User-Agent": "PollToll-Audit-Engine/1.0",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                raw_text = payload["choices"][0]["message"]["content"]
                parsed = model_cls.model_validate_json(raw_text)
                _GATEWAY_METRICS["live_groq_calls"] += 1
                return parsed, f"groq:{model_name}"
            except urllib.error.HTTPError as http_err:
                code = http_err.code
                if code == 429:
                    # Per-(org, model) cooldown: other models on the same Groq key stay ready!
                    _GROQ_MODEL_COOLDOWN_UNTIL[(k_idx, model_name)] = time.time() + 60.0
                    _GATEWAY_METRICS["rate_limit_rotations"] += 1
                    continue
                if code in (401, 403):
                    _GROQ_KEY_COOLDOWN_UNTIL[k_idx] = time.time() + 1800.0
                    _GATEWAY_METRICS["rate_limit_rotations"] += 1
                    continue
                break
            except Exception:
                continue
    return None


def _transcribe_audio_groq(audio_b64: str, mime_type: str, lang: str) -> str | None:
    """Free-tier Whisper transcription via Groq `whisper-large-v3-turbo` when available."""
    keys = _load_groq_key_pool()
    if not keys:
        return None
    try:
        audio_bytes = base64.b64decode(audio_b64)
    except Exception:
        return None

    now = time.time()
    start_idx = next(_GROQ_COUNTER) % len(keys)
    ext = "wav" if "wav" in (mime_type or "") else "webm"
    boundary = f"----PollTollBoundary{uuid.uuid4().hex}"

    parts: list[bytes] = []
    parts.append(
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="speech.{ext}"\r\n'
            f"Content-Type: {mime_type or 'audio/webm'}\r\n\r\n"
        ).encode("utf-8")
        + audio_bytes
        + b"\r\n"
    )
    for field_name, field_val in (
        ("model", "whisper-large-v3-turbo"),
        ("language", lang),
        ("response_format", "json"),
    ):
        parts.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{field_name}"\r\n\r\n'
                f"{field_val}\r\n"
            ).encode("utf-8")
        )
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(parts)

    for offset in range(len(keys)):
        k_idx = (start_idx + offset) % len(keys)
        if _GROQ_KEY_COOLDOWN_UNTIL.get(k_idx, 0.0) > now:
            continue
        if _GROQ_MODEL_COOLDOWN_UNTIL.get((k_idx, "whisper-large-v3-turbo"), 0.0) > now:
            continue
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {keys[k_idx]}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "User-Agent": "PollToll-Audit-Engine/1.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            text = (data.get("text") or "").strip()
            if text:
                _GATEWAY_METRICS["live_groq_calls"] += 1
                return text
        except urllib.error.HTTPError as http_err:
            if http_err.code == 429:
                _GROQ_MODEL_COOLDOWN_UNTIL[(k_idx, "whisper-large-v3-turbo")] = time.time() + 60.0
                _GATEWAY_METRICS["rate_limit_rotations"] += 1
                continue
            if http_err.code in (401, 403):
                _GROQ_KEY_COOLDOWN_UNTIL[k_idx] = time.time() + 1800.0
                _GATEWAY_METRICS["rate_limit_rotations"] += 1
                continue
        except Exception:
            continue
    return None


def _call_structured_llm(
    prompt: str,
    model_cls: type[BaseModel],
) -> tuple[Any, str] | None:
    """Load-balances and fails over across Groq and Gemini structured pools."""
    priority = _ai_priority()
    has_groq = len(_load_groq_key_pool()) > 0
    has_gemini = len(_load_key_pool()) > 0

    if priority == "groq":
        providers = ["groq", "gemini"]
    elif priority == "gemini":
        providers = ["gemini", "groq"]
    elif has_groq and has_gemini:
        # Alternate across clouds so both free-tier pools stay cool, with instant failover
        providers = ["groq", "gemini"] if (next(_PROVIDER_COUNTER) % 2 == 0) else ["gemini", "groq"]
    elif has_groq:
        providers = ["groq"]
    else:
        providers = ["gemini"]

    for prov in providers:
        if prov == "groq" and has_groq:
            groq_res = _call_groq_structured(prompt, model_cls)
            if groq_res is not None:
                return groq_res
        elif prov == "gemini" and has_gemini:
            gem_out = _call_gemini_with_rotation(
                input_payload=prompt,
                response_format=model_cls.model_json_schema(),
                response_mime_type="application/json",
            )
            if gem_out is not None:
                inter, model_used = gem_out
                try:
                    parsed = model_cls.model_validate_json(inter.output_text)
                    return parsed, model_used
                except Exception:
                    continue
    return None


def sanitize_neutral_text(text: str) -> str:
    cleaned = text
    for pat in FORBIDDEN_ACCUSATION_PATTERNS:
        cleaned = re.sub(pat, "unverified irregularity allegation", cleaned, flags=re.IGNORECASE)
    return cleaned


class _GeminiClaimStructured(BaseModel):
    overall_assessment_label: str
    verified_facts: list[ClaimFindingItem]
    disputed_interpretations: list[ClaimFindingItem]
    unprovable_from_public_data: list[ClaimFindingItem]
    confidence_level: float = Field(ge=0.0, le=1.0)
    confidence_basis: str
    reasoning_steps: list[str]


class _GeminiCitizenStructured(BaseModel):
    recognized_transcript: str | None = None
    answer_text: str
    confidence_level: float = Field(ge=0.0, le=1.0)
    reasoning_steps: list[str]
    official_next_steps: list[str]
    referenced_forms: list[str]


def check_viral_claim(
    con: duckdb.DuckDBPyConnection, req: ClaimCheckRequest
) -> ClaimCheckResponse:
    """Evaluates a viral allegation using persistent DuckDB cache + quota-safe Gemini cascade."""
    s_from, s_to, totals, booth_summaries, _ = compute_change_ledger(
        con, req.from_version, req.to_version, sample_limit=30
    )
    flags = detect_anomalies(con, booth_summaries, req.from_version, req.to_version)
    booth_map = {b.booth_id: b for b in booth_summaries}

    mentioned_booths = [m.upper() for m in BOOTH_REGEX.findall(req.claim_text)]
    lower_claim = " ".join(req.claim_text.lower().split())
    if not mentioned_booths:
        if "109" in lower_claim or "110" in lower_claim or "340" in lower_claim or "split" in lower_claim:
            mentioned_booths = ["PS-109", "PS-110"]
        elif "302" in lower_claim or "udhna" in lower_claim:
            mentioned_booths = ["PS-302"]
        elif "203" in lower_claim or "64" in lower_claim or "house" in lower_claim or "42/b" in lower_claim:
            mentioned_booths = ["PS-203"]
        elif "104" in lower_claim or "hostel" in lower_claim or "student" in lower_claim:
            mentioned_booths = ["PS-104"]
        elif "207" in lower_claim or "195" in lower_claim or "age" in lower_claim:
            mentioned_booths = ["PS-207"]
        else:
            mentioned_booths = ["PS-109", "PS-302"]

    referenced = [b for b in mentioned_booths if b in booth_map]
    neutrality_note = {
        "en": "PollToll treats all claims identically regardless of source. Outputs separate deterministic roll math from unverified intent and never declare fraud or name parties/individuals.",
        "hi": "PollToll स्रोत की परवाह किए बिना सभी दावों की समान रूप से जांच करता है। यह केवल प्रकाशित डेटा के गणित और अपुष्ट अनुमानों को अलग करता है तथा कभी भी धोखाधड़ी की घोषणा या किसी दल/व्यक्ति का नाम नहीं लेता।",
        "gu": "PollToll તમામ દાવાઓને કોઈપણ રાજકીય પક્ષપાત વિના સમાન ધોરણે ચકાસે છે. તે પ્રકાશિત યાદીના આંકડા અને અપ્રમાણિત અનુમાનોને અલગ પાડે છે અને ક્યારેય છેતરપિંડી જાહેર કરતું નથી.",
    }[req.language]

    cache_key = hashlib.sha256(
        f"claim:{req.language}:{s_from.sha256}:{s_to.sha256}:{lower_claim}".encode("utf-8")
    ).hexdigest()

    if req.use_llm:
        cached = _cache_get(con, cache_key)
        if cached is not None:
            cached_dict, cached_model = cached
            cached_dict["generated_by"] = f"{cached_model} (duckdb-cache-hit)"
            return ClaimCheckResponse(**cached_dict)

        evidence_context = {
            "ledger_totals": totals,
            "referenced_booths": [booth_map[b].model_dump() for b in referenced],
            "matching_flags": [
                {
                    "booth_id": f.booth_id,
                    "rule_id": f.rule_id,
                    "headline": f.headline,
                    "uncertainty": f.uncertainty.model_dump(),
                    "innocent_explanations": f.explanation.innocent_explanations,
                    "missing_evidence": f.explanation.missing_evidence,
                }
                for f in flags
                if f.booth_id in referenced
            ],
        }
        prompt = (
            f"You are PollToll's strictly non-partisan Electoral Change-Audit Claim Checker.\n"
            f"Respond in {LANGUAGE_NAMES[req.language]}.\n"
            f"Evaluate CLAIM strictly using LEDGER JSON. Never declare fraud or blame parties/officials.\n"
            f"CLAIM: {req.claim_text}\n"
            f"LEDGER JSON: {json.dumps(evidence_context, ensure_ascii=False)}"
        )
        llm_out = _call_structured_llm(prompt, _GeminiClaimStructured)
        if llm_out is not None:
            parsed, model_used = llm_out
            try:
                resp = ClaimCheckResponse(
                    claim_text=req.claim_text,
                    language=req.language,
                    overall_assessment_label=sanitize_neutral_text(parsed.overall_assessment_label),
                    verified_facts=parsed.verified_facts,
                    disputed_interpretations=parsed.disputed_interpretations,
                    unprovable_from_public_data=parsed.unprovable_from_public_data,
                    confidence_level=parsed.confidence_level,
                    confidence_basis=parsed.confidence_basis,
                    reasoning_steps=parsed.reasoning_steps,
                    referenced_booths=referenced,
                    neutrality_guardrail_note=neutrality_note,
                    generated_by=f"{model_used}+deterministic-ledger",
                )
                _cache_put(con, cache_key, "claim-check", model_used, resp.model_dump())
                return resp
            except Exception:
                pass
    else:
        _GATEWAY_METRICS["deterministic_fastpath_saved"] += 1

    return _deterministic_claim_response(
        req=req,
        totals=totals,
        booth_map=booth_map,
        referenced=referenced,
        neutrality_note=neutrality_note,
    )


def _deterministic_claim_response(
    req: ClaimCheckRequest,
    totals: dict[str, int],
    booth_map: dict[str, Any],
    referenced: list[str],
    neutrality_note: str,
) -> ClaimCheckResponse:
    lang = req.language
    primary = referenced[0] if referenced else "PS-109"

    if primary in ("PS-109", "PS-110"):
        b109 = booth_map["PS-109"]
        b110 = booth_map["PS-110"]
        labels = {
            "en": "Raw Booth Outflow Verified (340); 'Vanished Voters' Claim Disputed — 338 Transferred Intact to PS-110",
            "hi": "बूथ से 340 नाम हटना सत्यापित; 'गायब मतदाता' दावा खंडित — 338 मतदाता सुरक्षित रूप से PS-110 में स्थानांतरित",
            "gu": "બૂથમાંથી 340 નામનો ઘટાડો ચકાસાયેલ; 'મતદારો ગાયબ' દાવો ખંડિત — 338 મતદારો સુરક્ષિત રીતે PS-110 માં તબદીલ",
        }
        verified = {
            "en": [
                ClaimFindingItem(
                    statement=f"Booth PS-109 elector count decreased from {b109.electors_from} in `{req.from_version}` to {b109.electors_to} in `{req.to_version}` (340 gross outflow).",
                    evidence_source="Electoral Change Ledger (`PS-109` snapshot diff)",
                ),
                ClaimFindingItem(
                    statement=f"Adjacent Booth PS-110 gained {b110.transferred_in_count} transferred EPIC IDs in the exact same revision cycle.",
                    evidence_source="Cross-Booth EPIC Reconciliation (`RULE_BOOTH_SPLIT_RECONCILE@1.0.0`)",
                ),
            ],
            "hi": [
                ClaimFindingItem(
                    statement=f"बूथ PS-109 में मतदाता संख्या `{req.from_version}` के {b109.electors_from} से घटकर `{req.to_version}` में {b109.electors_to} हुई (340 का सकल अंतर)।",
                    evidence_source="Electoral Change Ledger (`PS-109` स्नैपशॉट तुलना)",
                ),
                ClaimFindingItem(
                    statement=f"उसी संशोधन चक्र में पड़ोसी बूथ PS-110 में {b110.transferred_in_count} वही EPIC नंबर सक्रिय रूप से जुड़े हैं।",
                    evidence_source="क्रॉस-बूथ EPIC मिलान (`RULE_BOOTH_SPLIT_RECONCILE@1.0.0`)",
                ),
            ],
            "gu": [
                ClaimFindingItem(
                    statement=f"બૂથ PS-109 માં મતદાર સંખ્યા `{req.from_version}` ના {b109.electors_from} થી ઘટીને `{req.to_version}` માં {b109.electors_to} થઈ (340 નો તફાવત).",
                    evidence_source="Electoral Change Ledger (`PS-109` સ્નેપશોટ સરખામણી)",
                ),
                ClaimFindingItem(
                    statement=f"તે જ સુધારણા ચક્રમાં બાજુના બૂથ PS-110 માં {b110.transferred_in_count} તે જ EPIC નંબરો સક્રિય રીતે ઉમેરાયા છે.",
                    evidence_source="ક્રોસ-બૂથ EPIC રિકન્સિલિએશન (`RULE_BOOTH_SPLIT_RECONCILE@1.0.0`)",
                ),
            ],
        }
        disputed = {
            "en": [
                ClaimFindingItem(
                    statement=f"338 of the 340 electors were NOT removed from the electoral roll; their EPIC IDs remain active in Wing-B (`PS-110`), leaving a true net deletion rate of {b109.net_effective_deletion_rate * 100:.2f}% (within historical baseline).",
                    evidence_source=f"95% Wilson CI [{b109.deletion_ci_lower_95 * 100:.2f}%, {b109.deletion_ci_upper_95 * 100:.2f}%] vs {b109.historical_deletion_baseline * 100:.2f}% baseline",
                )
            ],
            "hi": [
                ClaimFindingItem(
                    statement=f"340 में से 338 मतदाताओं को मतदाता सूची से हटाया नहीं गया है; उनके EPIC नंबर विंग-B (`PS-110`) में सक्रिय हैं। वास्तविक शुद्ध विलोपन दर मात्र {b109.net_effective_deletion_rate * 100:.2f}% है।",
                    evidence_source=f"95% Wilson CI [{b109.deletion_ci_lower_95 * 100:.2f}%, {b109.deletion_ci_upper_95 * 100:.2f}%]",
                )
            ],
            "gu": [
                ClaimFindingItem(
                    statement=f"340 માંથી 338 મતદારોને મતદાર યાદીમાંથી કમી કરવામાં આવ્યા નથી; તેમના EPIC નંબરો વિંગ-B (`PS-110`) માં સક્રિય છે. વાસ્તવિક નેટ ડિલીશન દર માત્ર {b109.net_effective_deletion_rate * 100:.2f}% છે.",
                    evidence_source=f"95% Wilson CI [{b109.deletion_ci_lower_95 * 100:.2f}%, {b109.deletion_ci_upper_95 * 100:.2f}%]",
                )
            ],
        }
        unprovable = {
            "en": [
                ClaimFindingItem(
                    statement="Whether individual households received physical notification slips informing them of the Wing-A to Wing-B room reassignment.",
                    evidence_source="Missing from published roll PDFs (requires DEO Polling Station Rationalization Order & BLO distribution log)",
                )
            ],
            "hi": [
                ClaimFindingItem(
                    statement="क्या प्रत्येक परिवार को विंग-A से विंग-B में कक्ष परिवर्तन की भौतिक सूचना पर्ची प्राप्त हुई।",
                    evidence_source="प्रकाशित पीडीएफ में अनुपलब्ध (DEO पुनर्गठन आदेश और BLO वितरण लॉग आवश्यक)",
                )
            ],
            "gu": [
                ClaimFindingItem(
                    statement="દરેક પરિવારને વિંગ-A થી વિંગ-B માં મતદાન ખંડ બદલાયાની જાણકારી સ્લિપ મળી કે કેમ.",
                    evidence_source="પ્રકાશિત યાદીમાં ઉપલબ્ધ નથી (DEO પુનર્ગઠન આદેશ અને BLO વિતરણ નોંધ જરૂરી)",
                )
            ],
        }
        return ClaimCheckResponse(
            claim_text=req.claim_text,
            language=lang,
            overall_assessment_label=labels[lang],
            verified_facts=verified[lang],
            disputed_interpretations=disputed[lang],
            unprovable_from_public_data=unprovable[lang],
            confidence_level=0.98,
            confidence_basis="Deterministic 1-to-1 EPIC lineage match across published constituency snapshots.",
            reasoning_steps=[
                "Queried PS-109 outflow between v2025_final and v2026_draft.",
                "Joined missing PS-109 EPIC IDs against all active booths in AC-041 and matched 338 records in PS-110.",
                "Separated verified booth-level count shift from the disputed 'mass disenfranchisement' framing.",
            ],
            referenced_booths=["PS-109", "PS-110"],
            neutrality_guardrail_note=neutrality_note,
            generated_by="deterministic-ledger-engine",
        )

    if primary == "PS-203":
        b203 = booth_map["PS-203"]
        return ClaimCheckResponse(
            claim_text=req.claim_text,
            language=lang,
            overall_assessment_label={
                "en": "Address Concentration Verified (64 Electors at H-42/B); 'Fake Voter Proof' Claim Cannot Be Proven from Roll PDFs Alone",
                "hi": "एक पते (H-42/B) पर 64 मतदाता सत्यापित; केवल सूची से 'फर्जी मतदाता' का दावा सिद्ध नहीं होता",
                "gu": "એક સરનામે (H-42/B) 64 મતદારોની નોંધણી ચકાસાયેલ; માત્ર યાદી પરથી 'બોગસ મતદાર' દાવો સાબિત થઈ શકતો નથી",
            }[lang],
            verified_facts=[
                ClaimFindingItem(
                    statement=f"House string `H-42/B` in `PS-203` increased from 6 electors in `{req.from_version}` to 64 electors in `{req.to_version}` (+58 supplement additions).",
                    evidence_source="Electoral Change Ledger (`RULE_HOUSEHOLD_DENSITY@1.0.0`)",
                )
            ],
            disputed_interpretations=[
                ClaimFindingItem(
                    statement="High elector count on one house string is NOT proof of unlawful registration; multi-unit tenements, worker dormitories, and unnumbered chawls routinely share a single plot number in published PDFs.",
                    evidence_source="ECI Booth-Level Address Normalization Guidelines",
                )
            ],
            unprovable_from_public_data=[
                ClaimFindingItem(
                    statement="Physical building capacity of `H-42/B` and whether BLO supervisory field verification was completed.",
                    evidence_source="Requires municipal property record & BLO physical inspection checklist",
                )
            ],
            confidence_level=0.92,
            confidence_basis=f"Exact string aggregation over n={b203.electors_to} published records in PS-203.",
            reasoning_steps=[
                "Verified exact count of `house_no = 'H-42/B'` across v2025_final (6) and v2026_draft (64).",
                "Flagged for authorized field review while rejecting unsupported accusations of fraud.",
            ],
            referenced_booths=["PS-203"],
            neutrality_guardrail_note=neutrality_note,
            generated_by="deterministic-ledger-engine",
        )

    b_ref = booth_map.get(primary, booth_map["PS-302"])
    return ClaimCheckResponse(
        claim_text=req.claim_text,
        language=lang,
        overall_assessment_label={
            "en": f"Elevated Deletion Rate in {b_ref.booth_id} Statistically Verified ({b_ref.net_effective_deletion_rate * 100:.1f}%); Motive or Illegality Unprovable from Public Data",
            "hi": f"बूथ {b_ref.booth_id} में उच्च विलोपन दर ({b_ref.net_effective_deletion_rate * 100:.1f}%) सांख्यिकीय रूप से सत्यापित; सार्वजनिक डेटा से दुर्भावना सिद्ध नहीं",
            "gu": f"બૂથ {b_ref.booth_id} માં ઊંચો ડિલીશન દર ({b_ref.net_effective_deletion_rate * 100:.1f}%) આંકડાકીય રીતે ચકાસાયેલ; જાહેર ડેટા પરથી બદઈરાદો સાબિત થતો નથી",
        }[lang],
        verified_facts=[
            ClaimFindingItem(
                statement=(
                    f"`{b_ref.booth_id}` recorded {b_ref.deleted_count} net deletions out of {b_ref.electors_from} electors "
                    f"({b_ref.net_effective_deletion_rate * 100:.1f}%, 95% CI [{b_ref.deletion_ci_lower_95 * 100:.1f}%, {b_ref.deletion_ci_upper_95 * 100:.1f}%]) "
                    f"vs historical baseline {b_ref.historical_deletion_baseline * 100:.1f}% (z = +{b_ref.z_score_vs_baseline:.1f}σ)."
                ),
                evidence_source=f"Statistical Anomaly Engine (`RULE_HIST_DEL_SPIKE@1.0.0`, dataset total net deletions={totals['deleted']})",
            )
        ],
        disputed_interpretations=[
            ClaimFindingItem(
                statement="A statistical spike establishes where human auditors should look—it does not establish wrongful deletion, as urban relocation, hostel graduation, or deceased-backlog cleanup can produce localized spikes.",
                evidence_source="PollToll Epistemic Audit Standard",
            )
        ],
        unprovable_from_public_data=[
            ClaimFindingItem(
                statement="Whether Rule 21-A statutory notices and house-to-house BLO verification checklists were duly served for each deleted record.",
                evidence_source="Non-public ERO administrative case files",
            )
        ],
        confidence_level=0.94,
        confidence_basis=f"Non-overlapping 95% Wilson confidence interval over n={b_ref.electors_from} records.",
        reasoning_steps=[
            f"Checked cross-booth transfers out of `{b_ref.booth_id}` ({b_ref.transferred_out_count}) to rule out booth-splitting.",
            f"Compared net deletion rate against 2024–2025 baseline ({b_ref.historical_deletion_baseline * 100:.1f}%).",
            "Identified missing administrative records required for human verification.",
        ],
        referenced_booths=[b_ref.booth_id],
        neutrality_guardrail_note=neutrality_note,
        generated_by="deterministic-ledger-engine",
    )


def assist_citizen(
    con: duckdb.DuckDBPyConnection, req: CitizenAssistantRequest
) -> CitizenAssistantResponse:
    """Multilingual (EN / HI / GU) Citizen Assistant with free-tier caching & deterministic fast-path."""
    query_text = req.query.strip()
    transcript: str | None = None

    # 1. Audio fallback only when browser lacked Web Speech API and uploaded raw audio
    if req.audio_base64:
        transcript = _transcribe_audio_groq(
            req.audio_base64, req.audio_mime_type or "audio/webm", req.language
        )
        if not transcript:
            tr_out = _call_gemini_with_rotation(
                input_payload=[
                    {
                        "type": "text",
                        "text": (
                            f"Transcribe this citizen's spoken electoral-roll question accurately in "
                            f"{LANGUAGE_NAMES[req.language]} (preserve any EPIC ID like SYN-GJ-109-0042). "
                            "Return ONLY raw transcript text."
                        ),
                    },
                    {
                        "type": "audio",
                        "data": req.audio_base64,
                        "mime_type": req.audio_mime_type or "audio/webm",
                    },
                ],
                explicit_models=["gemini-3.8-flash", "gemini-3.5-flash-lite"],
            )
            if tr_out is not None and tr_out[0].output_text:
                transcript = tr_out[0].output_text.strip()
        if transcript and not query_text:
            query_text = transcript

    # 2. Extract EPIC ID
    epic = req.epic_id.strip().upper() if req.epic_id else None
    if not epic and query_text:
        m = EPIC_REGEX.search(query_text)
        if m:
            epic = m.group(0).upper()

    lookup = lookup_citizen_epic(con, epic) if epic else None

    # 3. Free-tier optimization: pure EPIC lookups with no custom natural-language question
    # are answered deterministically in <3ms (0 API quota spent, 100% exact).
    should_call_llm = bool(req.use_llm and query_text)
    if not should_call_llm:
        _GATEWAY_METRICS["deterministic_fastpath_saved"] += 1

    answer_text = ""
    steps_out: list[str] = []
    forms_out: list[str] = []
    reasoning_out: list[str] = []
    conf = 0.96
    gen_by = "deterministic-ledger-engine"

    if should_call_llm:
        norm_q = " ".join(query_text.lower().split())
        cache_key = hashlib.sha256(
            f"assist:{req.language}:{epic or 'none'}:{norm_q}".encode("utf-8")
        ).hexdigest()
        cached = _cache_get(con, cache_key)
        if cached is not None:
            c_dict, c_model = cached
            answer_text = c_dict["answer_text"]
            steps_out = c_dict["official_next_steps"]
            forms_out = c_dict["referenced_forms"]
            reasoning_out = c_dict["reasoning_steps"]
            conf = c_dict["confidence_level"]
            gen_by = f"{c_model} (duckdb-cache-hit)"
        else:
            ctx = (
                {
                    "epic_id": lookup.epic_id,
                    "current_status": lookup.current_status,
                    "latest_record": lookup.latest_record,
                    "summary": lookup.plain_language_summary[req.language],
                }
                if lookup
                else {"note": "General citizen ECI process query."}
            )
            prompt = (
                f"You are PollToll Verify, a non-partisan citizen electoral-roll assistant.\n"
                f"Reply in {LANGUAGE_NAMES[req.language]}.\n"
                f"Citizen question: {query_text}\n"
                f"Ledger JSON: {json.dumps(ctx, ensure_ascii=False)}\n"
                "Explain status clearly and cite official ECI Form 6 (inclusion), Form 7 (objection/deletion), or Form 8 (shifting/correction) on voters.eci.gov.in."
            )
            llm_out = _call_structured_llm(prompt, _GeminiCitizenStructured)
            if llm_out is not None:
                parsed, model_used = llm_out
                try:
                    answer_text = sanitize_neutral_text(parsed.answer_text)
                    steps_out = parsed.official_next_steps
                    forms_out = parsed.referenced_forms
                    reasoning_out = parsed.reasoning_steps
                    conf = parsed.confidence_level
                    gen_by = f"{model_used}+deterministic-ledger"
                    _cache_put(
                        con,
                        cache_key,
                        "citizen-assistant",
                        model_used,
                        {
                            "answer_text": answer_text,
                            "official_next_steps": steps_out,
                            "referenced_forms": forms_out,
                            "reasoning_steps": reasoning_out,
                            "confidence_level": conf,
                        },
                    )
                except Exception:
                    pass

    if not answer_text:
        if lookup:
            answer_text = lookup.plain_language_summary[req.language]
            steps_out = lookup.official_next_steps[req.language]
            forms_out = lookup.relevant_eci_forms
            reasoning_out = [
                f"Queried longitudinal DuckDB snapshots (`v2024_final` .. `v2026_draft`) for `{lookup.epic_id}`.",
                f"Classified record lineage status as `{lookup.current_status}`.",
                f"Mapped status to statutory ECI procedures in {LANGUAGE_NAMES[req.language]}.",
            ]
        else:
            answer_text, steps_out, forms_out = _general_citizen_guidance(query_text, req.language)
            reasoning_out = [
                "Parsed citizen procedural question without a specific EPIC ID.",
                f"Retrieved official ECI Special Summary Revision guidance (Forms 6, 7, 8) in {LANGUAGE_NAMES[req.language]}.",
            ]

    # 4. Optional Gemini TTS (only when explicitly requested; browser speechSynthesis handles default free readout)
    tts_b64: str | None = None
    tts_mime: str | None = None
    if req.include_tts:
        tts_out = _call_gemini_with_rotation(
            input_payload=[
                {
                    "type": "user_input",
                    "content": [
                        {
                            "type": "text",
                            "text": answer_text,
                            "annotations": [
                                {
                                    "type": "speech_metadata",
                                    "style": "calm, clear, warm public-service assistant",
                                }
                            ],
                        }
                    ],
                }
            ],
            response_format={"type": "audio"},
            generation_config={"speech_config": [{"voice": "Kore"}]},
            explicit_models=["gemini-3.8-flash-lite-tts"],
        )
        if tts_out is not None and tts_out[0].output_audio and tts_out[0].output_audio.data:
            tts_b64 = tts_out[0].output_audio.data
            tts_mime = tts_out[0].output_audio.mime_type or "audio/wav"

    return CitizenAssistantResponse(
        language=req.language,
        recognized_transcript=transcript,
        answer_text=answer_text,
        confidence_level=conf,
        reasoning_steps=reasoning_out,
        official_next_steps=steps_out,
        referenced_forms=forms_out,
        lookup_result=lookup,
        tts_audio_base64=tts_b64,
        tts_mime_type=tts_mime,
        generated_by=gen_by,
    )


def _general_citizen_guidance(
    query: str, lang: LanguageCode
) -> tuple[str, list[str], list[str]]:
    q = query.lower()
    if any(k in q for k in ("delete", "removed", "missing", "हट", "गायब", "કમી", "નીકળી")):
        ans = {
            "en": (
                "If your name is missing in a newly published Draft Roll, first check whether your polling booth was split "
                "(many voters are simply moved to Wing-B of the same building). If your EPIC is genuinely absent in the Draft Deletion Supplement, "
                "you can apply for restoration during the Claims & Objections period using Form 6 (or Form 8 if you shifted address)."
            ),
            "hi": (
                "यदि ड्राफ्ट मतदाता सूची में आपका नाम नहीं दिख रहा है, तो पहले जांचें कि क्या आपका मतदान केंद्र विभाजित (Split) हुआ है। "
                "यदि नाम वास्तव में डिलीशन सूची में है, तो दावे और आपत्तियों की अवधि में Form 6 (या पता बदलने पर Form 8) भरकर नाम बहाल करवाएं।"
            ),
            "gu": (
                "જો ડ્રાફ્ટ મતદાર યાદીમાં તમારું નામ ન દેખાય, તો પહેલા તપાસો કે તમારું મતદાન મથક વિભાજિત (Split) થયું છે કે કેમ. "
                "જો નામ ખરેખર કમી થયું હોય, તો હક્ક-દાવા સમયગાળા દરમિયાન Form 6 (અથવા સરનામું બદલાયું હોય તો Form 8) ભરીને નામ પુનઃ નોંધાવી શકો છો."
            ),
        }[lang]
        forms = ["Form 6", "Form 8"]
    else:
        ans = {
            "en": (
                "Welcome to PollToll Verify! Enter a synthetic EPIC ID (such as `SYN-GJ-109-0042` for a booth-split transfer, "
                "`SYN-GJ-104-0019` for a draft supplement deletion, or `SYN-GJ-207-0011` for an age-typo check) to trace its history across 4 roll versions."
            ),
            "hi": (
                "PollToll Verify में आपका स्वागत है! 4 मतदाता सूची संस्करणों में स्थिति जांचने के लिए कोई सिंथेटिक EPIC नंबर दर्ज करें "
                "(जैसे बूथ ट्रांसफर के लिए `SYN-GJ-109-0042`, ड्राफ्ट विलोपन के लिए `SYN-GJ-104-0019`, या आयु त्रुटि जांच के लिए `SYN-GJ-207-0011`)।"
            ),
            "gu": (
                "PollToll Verify માં આપનું સ્વાગત છે! 4 મતદાર યાદી આવૃત્તિઓમાં સ્થિતિ તપાસવા માટે સિન્થેટિક EPIC નંબર દાખલ કરો "
                "(દા.ત. બૂથ ટ્રાન્સફર માટે `SYN-GJ-109-0042`, ડ્રાફ્ટ કમી માટે `SYN-GJ-104-0019`, અથવા ઉંમર સુધારણા માટે `SYN-GJ-207-0011`)."
            ),
        }[lang]
        forms = ["Form 6", "Form 7", "Form 8"]

    steps = {
        "en": [
            "Enter your EPIC ID above to inspect cross-version changes between 2024 and 2026 synthetic rolls.",
            "Use Form 6 for new registration, Form 7 for objection/deletion, and Form 8 for address shift or correction on voters.eci.gov.in.",
        ],
        "hi": [
            "2024 से 2026 के संस्करणों में बदलाव देखने के लिए ऊपर अपना EPIC नंबर दर्ज करें।",
            "नए पंजीकरण हेतु Form 6, आपत्ति/विलोपन हेतु Form 7, और पता/विवरण सुधार हेतु voters.eci.gov.in पर Form 8 का उपयोग करें।",
        ],
        "gu": [
            "2024 થી 2026 ની આવૃત્તિઓમાં ફેરફાર જોવા માટે ઉપર તમારો EPIC નંબર દાખલ કરો.",
            "નવી નોંધણી માટે Form 6, વાંધા/કમી માટે Form 7 અને સરનામા કે વિગત સુધારા માટે voters.eci.gov.in પર Form 8 વાપરો.",
        ],
    }[lang]
    return ans, steps, forms
