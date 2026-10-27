# PollToll — Shared Antigravity Rules & Architecture (`Vidhaath <-> Yash`)

Welcome! Two developers and two Antigravity agents collaborate in this repository (`Vidhaath622/KMRWin`):
- **Vidhaath + Vidhaath's Antigravity**
- **Yash Gupta + Yash's Antigravity**

## 1. Agent-to-Agent Communication Protocol (MANDATORY)

Whenever the user asks you to talk to, sync with, check updates from, or hand off work to the teammate's Antigravity agent—or before modifying shared contracts in `shared/`—use the **Peer Bridge skill** at `.agents/skills/peer-bridge/SKILL.md`.

Quick commands (run from repo root):
- Check messages from the peer Antigravity agent:
  `python3 .agents/skills/peer-bridge/scripts/peer_bus.py inbox`
- Send a message to the peer Antigravity agent:
  `python3 .agents/skills/peer-bridge/scripts/peer_bus.py send --sender "<Vidhaath-AGY|Yash-AGY>" --topic "<topic>" --message "<text>"`

## 2. Product Thesis & Non-Negotiable Guardrails

**PollToll** is an **independent electoral change-audit platform** over *published* (and in this prototype, **100% synthetic**) electoral-roll snapshots.
We do **not** rebuild or claim superiority over ECI's internal **ERONET** registration/DSE/PSE workflows (see `docs/ERONET_GAP_ANALYSIS.md`). Instead, PollToll provides:
1. **Electoral Change Ledger** (`ADDED`, `DELETED`, `MODIFIED`, `BOOTH_TRANSFERRED`) linked to exact source snapshot SHA-256 + booth/serial coordinates.
2. **Statistical Anomaly Engine** testing spatial/temporal change concentrations against multi-cycle historical baselines with **explicit 95% confidence intervals / uncertainty disclosure**.
3. **5-Part Evidence-Backed Explanations** showing: (a) what changed, (b) exact versioned rule triggered, (c) innocent/alternative administrative explanations, (d) **missing evidence** public data cannot prove, and (e) next verification step.
4. **Independent Audit Receipts** signed with `Ed25519` + `SHA-256` dataset/rule hashes + an **append-only correction history**, verifiable client-side in the browser.
5. **PollToll Verify** public portal: **Claim Checker** (`Verified` / `Disputed` / `Cannot Be Proven from Public Data`) + **Multilingual Citizen Assistant** (Text & Voice in **English**, **Hindi / हिन्दी**, and **Gujarati / ગુજરાતી**).

### Strict Hackathon & Neutrality Rules
- **Synthetic or public aggregate data ONLY.** Never ingest, generate, or store real voter PII. Prefix all synthetic IDs with `SYN-`.
- **Never declare fraud or accuse individuals, political parties, or election authorities.** Flag statistical patterns strictly for authorized human review.
- **Every analytical or AI output MUST expose its reasoning, exact rule/data basis, and confidence/uncertainty level.**
- **Treat claims from all political perspectives identically.**

## 3. Clean Monorepo Boundaries (Zero Merge Conflicts)

- `backend/` — Python FastAPI (`uv`), DuckDB Change Ledger, `SciPy` baseline anomaly engine, `Ed25519` audit receipts, `google-genai` structured explainability + multilingual voice/text assistant.
- `frontend/` — Next.js 15 (App Router, TypeScript, Tailwind CSS, Recharts, WebCrypto `Ed25519` receipt verifier) covering **PollToll Audit**, **PollToll Verify**, and **PollToll Assurance**.
- `shared/openapi.json` — Canonical API contract exported from FastAPI (`backend/scripts/export_openapi.py`). Coordinate via `peer_bus.py` when changing schemas.
- `docs/` — Cited ERONET Feature-by-Feature Gap Analysis (`docs/ERONET_GAP_ANALYSIS.md`) and PPT/methodology briefs.
