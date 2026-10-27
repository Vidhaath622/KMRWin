<p align="center"><img src="frontend/public/polltoll-logo.svg" width="128" alt="PollToll logo"></p>

# PollToll — Independent Electoral Change-Audit & Public Verification Infrastructure

**Live demo:** https://polltoll-omega.vercel.app (backend API: https://polltoll-api.vercel.app/api/v1/health)

> **Positioning:** PollToll is **trusted electoral change-audit infrastructure**—not a voter-registration clone of ECI's ERONET and not a partisan accusation website. Instead of managing registrations, PollToll independently tests whether changes across *published* electoral-roll snapshots are **traceable, baseline-calibrated, explainable with explicit uncertainty, and cryptographically reproducible**.

---

## Core Infrastructure Planes

1. **`PollToll Audit` (Institutional Change-Audit Plane)**
   - **Electoral Change Ledger (`DuckDB`)**: Row- and booth-level deterministic diff across snapshots (`v2024_final` → `v2025_draft` → `v2025_final` → `v2026_draft`), classifying every record into `ADDED`, `DELETED`, `MODIFIED`, or cross-booth `BOOTH_TRANSFERRED` (e.g., proving 338 of the 352 entries that left `PS-109` moved intact to `PS-110`; only 14 were removed).
   - **Historical-Baseline Statistical Engine**: Evaluates net booth rates against multi-cycle baselines using **95% Wilson confidence intervals**, Z-scores, and versioned deterministic rules (`polltoll-rules@1.0.0`).
   - **5-Part Evidence Schema**: Every flag discloses *(1) What changed*, *(2) Exact rule & formula triggered*, *(3) Innocent administrative explanations*, *(4) Missing non-public evidence*, and *(5) Next verification step*.
2. **`PollToll Assurance` (Zero-Trust Attestation Plane)**
   - Issues **`Ed25519`-signed `.polltoll-receipt.json` bundles** binding dataset `SHA-256` hashes, rule-pack `SHA-256`, git commit, and an **append-only hash-chained reviewer correction log**.
   - Verifiable **client-side in the browser** via `window.crypto.subtle.verify("Ed25519", ...)` or headlessly via `polltoll_cli.py`.
3. **`PollToll Verify` (Free Public Multilingual Edge — English / हिन्दी / ગુજરાતી)**
   - **Citizen Roll-Change Assistant (Text + Voice Input + TTS Output)** tracing synthetic EPIC IDs across 4 cycles and mapping status to official ECI **Form 6 / Form 7 / Form 8** procedures.
   - **Ledger-Grounded Viral Claim Checker** separating **Verified Roll Math**, **Disputed Framing**, and **Cannot Be Proven from Public Data**.
4. **`PollToll Infra / API & CLI` (Developer & Auditor Pipeline Plane)**
   - Live CSV Snapshot Ingestion Pipeline (`POST /api/v1/ingest/snapshot`) with canonical `SHA-256` content addressing and strict `SYN-*` synthetic-only guardrails.
   - OpenAPI v3.1 contract (`shared/openapi.json`) + headless CLI (`backend/polltoll_cli.py`).

---

## Quickstart

### 1. Start Both Backend (`:8000`) & Control Plane UI (`:3000`)

```bash
./scripts/dev.sh
```

Or run separately:

```bash
# Terminal 1 — FastAPI + DuckDB Audit Engine
cd backend
uv sync --python 3.12
uv run uvicorn app.main:app --reload --port 8000

# Terminal 2 — Next.js 15 Control Plane
cd frontend
npm install
npm run dev
```

### 2. Run Headless Auditor CLI (Offline / CI Reproducibility)

```bash
cd backend
uv run python polltoll_cli.py snapshots
uv run python polltoll_cli.py diff --from v2025_final --to v2026_draft
uv run python polltoll_cli.py sign-receipt --out audit.receipt.json
uv run python polltoll_cli.py verify-receipt audit.receipt.json
```

---

## Antigravity-to-Antigravity Collaboration (`Vidhaath-AGY <-> Yash-AGY`)

Both teammates' Antigravity agents share workspace rules in [`AGENTS.md`](./AGENTS.md) and communicate via [`.agents/skills/peer-bridge/SKILL.md`](./.agents/skills/peer-bridge/SKILL.md) backed by GitHub Issue `#1` on `Vidhaath622/KMRWin`:

```bash
# Read messages from peer Antigravity
python3 .agents/skills/peer-bridge/scripts/peer_bus.py inbox --viewer "Yash-AGY"

# Send update to peer Antigravity
python3 .agents/skills/peer-bridge/scripts/peer_bus.py send \
  --sender "Yash-AGY" --topic "ppt-sync" --status "info" \
  --message "Synced ERONET gap analysis into slides."
```

## Key Architecture & Strategy Docs
- [`docs/ERONET_GAP_ANALYSIS.md`](./docs/ERONET_GAP_ANALYSIS.md) — Cited Feature-by-Feature ERONET Gap Matrix & Epistemic Boundaries (PPT-ready)
- [`docs/WIREFRAME_AND_INFRASTRUCTURE.md`](./docs/WIREFRAME_AND_INFRASTRUCTURE.md) — 5-Stage Infrastructure Dataflow & 4-Plane Control Console Wireframes
