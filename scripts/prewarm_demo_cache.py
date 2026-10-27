#!/usr/bin/env python3
"""Pre-warms PollToll's persistent DuckDB AI cache before a live hackathon stage demo.

Run while the FastAPI backend is running on http://127.0.0.1:8000:
    python3 scripts/prewarm_demo_cache.py
"""

from __future__ import annotations

import json
import time
import urllib.request

BASE_URL = "http://127.0.0.1:8000"

PRESET_CLAIMS = [
    ("en", "340 voters were secretly wiped out overnight from Booth PS-109 before the election!"),
    ("en", "Booth PS-302 suffered an abnormal deletion spike far above past revision cycles, proving targeted removal."),
    ("en", "64 voters registered at single address H-42/B in Booth PS-203 proves fake voter roll stuffing!"),
    ("hi", "चुनाव से पहले बूथ PS-109 से रातों-रात 340 मतदाताओं के नाम गायब कर दिए गए!"),
    ("hi", "बूथ PS-302 में पिछले वर्षों की तुलना में असामान्य रूप से अधिक नाम काटे गए हैं।"),
    ("gu", "ચૂંટણી પહેલા બૂથ PS-109 માંથી રાતોરાત 340 મતદારોના નામ ગાયબ કરી દેવામાં આવ્યા!"),
    ("gu", "બૂથ PS-302 માં અગાઉના વર્ષો કરતા ઘણા વધારે નામ કમી થયા છે."),
]

CITIZEN_QUESTIONS = [
    ("en", "SYN-GJ-109-0042", "Why did my booth change and is my registration safe?"),
    ("hi", "SYN-GJ-104-0019", "मेरा नाम ड्राफ्ट सूची से क्यों हटा और मैं इसे वापस कैसे जुड़वाऊं?"),
    ("gu", "SYN-GJ-109-0042", "મારું નામ SYN-GJ-109-0042 સુરક્ષિત છે કે નહીં?"),
]


def post_json(path: str, payload: dict) -> dict:
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    print("Pre-warming PollToll DuckDB AI cache on", BASE_URL)
    for lang, claim in PRESET_CLAIMS:
        t0 = time.perf_counter()
        res = post_json(
            "/api/v1/verify/claim-check",
            {
                "claim_text": claim,
                "language": lang,
                "from_version": "v2025_final",
                "to_version": "v2026_draft",
                "use_llm": True,
            },
        )
        ms = (time.perf_counter() - t0) * 1000
        print(f"  [claim:{lang}] {ms:6.1f} ms -> {res.get('generated_by')}")

    for lang, epic, q in CITIZEN_QUESTIONS:
        t0 = time.perf_counter()
        res = post_json(
            "/api/v1/verify/assistant",
            {
                "epic_id": epic,
                "query": q,
                "language": lang,
                "use_llm": True,
                "include_tts": False,
            },
        )
        ms = (time.perf_counter() - t0) * 1000
        print(f"  [assist:{lang}] {ms:6.1f} ms -> {res.get('generated_by')}")

    with urllib.request.urlopen(f"{BASE_URL}/api/v1/infra/quota", timeout=10) as resp:
        quota = json.loads(resp.read().decode("utf-8"))
    print("\nCache ready! Stored entries in DuckDB:", quota.get("cached_entries_in_duckdb"))


if __name__ == "__main__":
    main()
