# PollToll — Tech Stack & Hackathon Defense Masterclass
## Comprehensive Engineering Architecture, Mathematical Foundations & Judge Defense Guide

---

## 1. Executive Summary & Institutional Positioning

```
+---------------------------------------------------------------------------------------------------+
|                                      POLLTOLL AUDIT PLATFORM                                      |
+---------------------------------+---------------------------------+-------------------------------+
|  1. PollToll Audit              |  2. PollToll Assurance          |  3. PollToll Verify           |
|  (Institutional OLAP Engine)    |  (Zero-Trust Attestation)       |  (Free Multilingual Edge)     |
|  - DuckDB Change Ledger         |  - Ed25519 Digital Signatures   |  - Form 6/7/8 Guidance        |
|  - 95% Wilson Score CIs         |  - SHA-256 Hash-Chained Log     |  - EN / HI / GU Voice & Text  |
|  - 5-Part Evidence Schema       |  - WebCrypto Browser Verifier   |  - Neutral Claim Checker      |
+---------------------------------+---------------------------------+-------------------------------+
```

### The Problem
During elections, authorities publish periodic electoral-roll PDFs (Draft Roll, Supplement Lists, Final Roll). Because these rolls are distributed as thousands of separate, unlinked files across polling stations:
1. **Routine administrative events look like mass disenfranchisement**: When a booth exceeds capacity (~1,200 electors) and splits into Wing-A and Wing-B, 340 names disappear from Booth A's list and appear in Booth B's list. Partisan actors weaponize the raw drop ("340 voters deleted overnight!"), sparking viral panic.
2. **True statistical anomalies go unnoticed**: Genuine localized anomalies (e.g., a $6\sigma$ net deletion spike with zero transfers, or 64 unrelated electors registered to one house number) get buried under raw PDF clutter.
3. **No independent attestation layer**: Outside observers (journalists, legal teams, civic observers, election watchdogs) have no shared cryptographic receipt proving that two auditors analyzed the exact same dataset with the exact same rules.

### What PollToll Is NOT (The #1 Pitch Trap to Avoid)
- **PollToll does NOT replace or rebuild ECI's ERONET**: ERONET is ECI's internal operational registration engine handling Form 6/7/8 and Photo Similar Entries (PSE) with internal access to voter photographs.
- **PollToll does NOT accuse anyone of fraud**: It is an independent, reproducible change-audit engine over *public snapshots*, separating deterministic roll math from unverified allegations.
- **PollToll contains 0 real voter PII**: All IDs are synthetic (`SYN-GJ-*`).

---

## 2. Tech Stack: Beginning to Advanced

### Layer 1: Core Frameworks & Tooling (Foundational)

| Component | Technology | Why Chosen? | Key Implementation File |
| :--- | :--- | :--- | :--- |
| **Backend Runtime** | Python 3.12 + `uv` | `uv` is 10–100× faster than `pip`/`poetry`. Python provides rich scientific and crypto ecosystems. | [`backend/pyproject.toml`](file:///Users/root1/KRMWin/backend/pyproject.toml) |
| **Backend Web API** | FastAPI 0.115 + Pydantic v2 | Native async execution, automatic OpenAPI 3.1 schema export, strict type validation. | [`backend/app/main.py`](file:///Users/root1/KRMWin/backend/app/main.py) |
| **Frontend Framework**| Next.js 15 (React 19, TypeScript) | Server & Client Components, fast re-renders, App Router architecture. | [`frontend/package.json`](file:///Users/root1/KRMWin/frontend/package.json) |
| **Styling & Icons** | Tailwind CSS + Lucide React | High-density control-room theme, zero CSS bundle bloat. | [`frontend/src/app/globals.css`](file:///Users/root1/KRMWin/frontend/src/app/globals.css) |
| **Data Visualization**| Recharts 2.15 | Client-side responsive charts for booth distributions and uncertainty bars. | [`frontend/src/components/AuditWorkspace.tsx`](file:///Users/root1/KRMWin/frontend/src/components/AuditWorkspace.tsx) |

---

### Layer 2: Columnar Data Engine & Electoral Change Ledger (Intermediate)

#### Why DuckDB instead of PostgreSQL, SQLite, or MongoDB?
1. **Vectorized Columnar Execution**: Traditional row stores (Postgres/SQLite) read entire rows into memory. DuckDB processes millions of columns in vectorized CPU cache chunks (SIMD), executing diffs in milliseconds.
2. **Embedded & Zero-IPC**: No external daemon, socket connections, or network overhead. DuckDB runs directly in the FastAPI process memory space.
3. **Complex Analytical Joins**: Diffs across four snapshot cycles (`v2024_final` $\to$ `v2025_draft` $\to$ `v2025_final` $\to$ `v2026_draft`) run with full SQL expressive power.

#### The SQL Diff Engine (`FULL OUTER JOIN`)
In [`backend/app/engine/ledger.py`](file:///Users/root1/KRMWin/backend/app/engine/ledger.py#L103-L157), PollToll runs a deterministic SQL join across snapshots `f` (from) and `t` (to):

```sql
SELECT
    COALESCE(t.epic_id, f.epic_id) AS epic_id,
    f.booth_id AS from_booth_id,
    t.booth_id AS to_booth_id,
    CASE
        WHEN f.epic_id IS NULL THEN 'ADDED'
        WHEN t.epic_id IS NULL THEN 'DELETED'
        WHEN f.booth_id <> t.booth_id THEN 'BOOTH_TRANSFERRED'
        WHEN f.house_no <> t.house_no
             OR f.elector_name <> t.elector_name
             OR (t.age - f.age) NOT IN (0, 1) THEN 'MODIFIED'
        ELSE 'UNCHANGED'
    END AS change_type
FROM f FULL OUTER JOIN t ON f.epic_id = t.epic_id
```

**Why this matters:** When 340 voters vanish from `PS-109`, a naive script calls them "deletions". PollToll's `BOOTH_TRANSFERRED` classifier proves that **338 of the 340 records moved intact to adjacent booth `PS-110`**, instantly debunking rumors of voter suppression.

---

### Layer 3: Statistical Anomaly Engine & Uncertainty Math (Intermediate to Advanced)

Rather than using arbitrary thresholds (e.g. "flag if deletion > 5%"), PollToll builds multi-cycle empirical baselines and computes **sample-size-adjusted confidence bounds**.

#### 1. 95% Wilson Score Interval for Binomial Proportions
Located in [`backend/app/engine/ledger.py`](file:///Users/root1/KRMWin/backend/app/engine/ledger.py#L20-L29):
$$\hat{p} = \frac{x}{n}, \quad z = 1.95996$$
$$\text{Center} = \frac{\hat{p} + \frac{z^2}{2n}}{1 + \frac{z^2}{n}}, \quad \text{Margin} = \frac{z \sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}$$

* **Why not the standard Normal (Wald) Interval ($\hat{p} \pm z\sqrt{\hat{p}(1-\hat{p})/n}$)?**  
  The Wald interval severely breaks down near 0 or 1 and produces impossible negative rates or zero-width intervals when $x=0$. The Wilson score interval inverts the score test, remaining mathematically sound even for small polling booths ($n \approx 300$).

#### 2. Historical Baseline Z-Score
In [`backend/app/engine/ledger.py`](file:///Users/root1/KRMWin/backend/app/engine/ledger.py#L39-L84):
- Baseline mean ($\mu_{\text{base}}$) is computed per booth across prior revisions (`v2024_final` $\to$ `v2025_draft` $\to$ `v2025_final`).
- Standard deviation includes an empirical dispersion floor ($\sigma = \max(\sqrt{\frac{\mu(1-\mu)}{n}}, 0.0045)$).
- Test statistic:
  $$z = \frac{\text{net\_effective\_deletion\_rate} - \mu_{\text{base}}}{\sigma}$$
- If $z \ge 3.5\sigma$, net deletion $> 5\%$, and the **lower 95% Wilson bound of the current cycle exceeds the upper historical bound**, the engine triggers `RULE_HIST_DEL_SPIKE`.

#### 3. Lexical Clustering via RapidFuzz
Located in [`backend/app/engine/anomaly.py`](file:///Users/root1/KRMWin/backend/app/engine/anomaly.py#L425-L455):
- Identifies cross-booth new additions added in the same supplement sharing identical `(relation_name, age, gender, house_no)`.
- Uses C++-accelerated Levenshtein distance via `rapidfuzz.fuzz.token_sort_ratio(name_a, name_b) >= 75`.
- Flags transliteration variants (e.g., *"Maheshbhai K. Patel"* in Booth 305 vs. *"Mahesh Kumar Patel"* in Booth 306).
- **Epistemic Disclosure**: Sets confidence to 0.79 because public rolls omit photographs, meaning twin or joint-family members cannot be definitively differentiated from duplicate submissions without physical BLO verification.

---

### Layer 4: Zero-Trust Cryptographic Attestation (`Ed25519` + WebCrypto) (Advanced)

```
+---------------------------------------------------------------------------------------+
|                              AUDIT RECEIPT ARCHITECTURE                               |
+---------------------------------------------------------------------------------------+
|  Canonical JSON Payload:                                                              |
|    - Dataset SHA-256 (from_snapshot, to_snapshot)                                     |
|    - Rule Pack Version ("polltoll-rules@1.0.0") & Rules Hash                          |
|    - Git Commit Hash ("dev-local" or 7-char SHA)                                      |
|    - Ledger Totals & Anomaly Flags Summary                                            |
|    - Head Hash of Append-Only Reviewer Correction Log                                  |
+---------------------------------------------------------------------------------------+
                                           |
                                    SHA-256 Digest
                                           |
                     Ed25519 Signature (Private Key, 64 bytes)
                                           |
        +----------------------------------+----------------------------------+
        |                                                                     |
        v                                                                     v
  Backend Headless Verification                         Browser Client-Side Verification
  (Python cryptography library)                        (W3C window.crypto.subtle.verify)
```

#### Why Ed25519 instead of RSA or ECDSA (secp256k1 / P-256)?
1. **High Performance & Constant-Time**: Ed25519 is immune to side-channel timing attacks and verifies in microseconds.
2. **Compact Footprint**: 32-byte public keys and 64-byte signatures—far smaller than 2048-bit RSA keys.
3. **Zero R-S Bias Vulnerabilities**: Unlike ECDSA, Ed25519 has no catastrophic failure risk from weak random number generators.

#### The Client-Side WebCrypto Breakthrough
Inspect [`frontend/src/lib/cryptoVerify.ts`](file:///Users/root1/KRMWin/frontend/src/lib/cryptoVerify.ts#L60-L147):
The browser does not trust the server. When viewing an audit receipt:
1. It re-computes `SHA-256` using `window.crypto.subtle.digest("SHA-256", ...)`.
2. It imports the raw SubjectPublicKeyInfo (SPKI) key into the browser's crypto enclave:
   ```ts
   const pubKey = await window.crypto.subtle.importKey(
     "spki",
     spkiBytes.buffer,
     { name: "Ed25519" },
     false,
     ["verify"]
   );
   ```
3. It validates the cryptographic signature directly:
   ```ts
   const sigOk = await window.crypto.subtle.verify(
     { name: "Ed25519" },
     pubKey,
     sigBytes.buffer,
     msgBytes.buffer
   );
   ```
4. **Interactive Tamper Demo**: In the **Assurance Center**, clicking *"Simulate Tampering"* mutates a single character (`deleted = 999999`). WebCrypto instantly catches the signature mismatch.

#### Append-Only Hash-Chained Reviewer Log
Every review action (e.g., an auditor adding a note to a flag) is stored in DuckDB with:
$$\text{event\_hash}_i = \text{SHA-256}(\text{seq}_i \parallel \text{flag\_id}_i \parallel \text{action}_i \parallel \text{prev\_hash}_{i-1} \parallel \text{timestamp}_i)$$
The head hash is sealed inside the Ed25519 payload. Tampering with any historical review event breaks the hash chain.

---

### Layer 5: AI Explainability & Multilingual Voice Edge (Advanced)

Located in [`backend/app/services/ai_explainer.py`](file:///Users/root1/KRMWin/backend/app/services/ai_explainer.py).

#### The 5-Part Evidence Schema
Every flag generated by the system contains:
1. **What Changed**: Deterministic Delta from the DuckDB Ledger.
2. **Rule Triggered**: Exact versioned formula (e.g., `RULE_HIST_DEL_SPIKE@1.0.0`).
3. **Innocent Administrative Explanations**: e.g., hostel cohort graduation, urban redevelopment, multi-family chawl.
4. **Missing Evidence**: Non-public statutory documents that public rolls cannot prove (e.g., Rule 21-A notice logs, BLO checklists, DEO rationalization orders).
5. **Next Verification Step**: Actionable procedure for an authorized observer under the Registration of Electors Rules, 1960.

#### Free-Tier Quota Shielding (Zero Crash Guarantee)
If a team relies naively on free Gemini API keys during a live hackathon demo, they risk hitting HTTP 429 rate limit errors. PollToll implements a 5-layer shield:
1. **Deterministic-First Fast Path**: Pure EPIC lookups and UI previews run directly on DuckDB in $<5\text{ms}$ with zero LLM calls.
2. **Persistent SHA-256 DuckDB Response Cache**: Cached by `hashlib.sha256(language + query + snapshot_hashes)`. Repeat queries use 0 tokens.
3. **Model Cascade**: Automatically tries `gemini-3.5-flash-lite` $\to$ `gemini-3.1-flash-lite` $\to$ `gemini-3.8-flash`.
4. **Multi-Key Round-Robin with 60s Cooldown**: Automatically rotates between configured keys on HTTP 429/403.
5. **Web Speech API First**: Speech-to-text and text-to-speech run locally in the browser via browser APIs; Gemini audio is reserved as an optional fallback.

---

## 3. The 6 Planted Audit Scenarios in Synthetic Data

All 6 scenarios are deterministically generated by [`backend/app/data/generator.py`](file:///Users/root1/KRMWin/backend/app/data/generator.py):

| Scenario | Booth / Subject | Ground-Truth Phenomenon | How PollToll Resolves It |
| :--- | :--- | :--- | :--- |
| **1. Booth Split** | `PS-109` $\to$ `PS-110` | 340 names leave `PS-109`. | Ledger matches 338 active EPICs in `PS-110`. Classifies viral rumor as **Verified raw drop / Disputed deletion claim / Missing Gazette split order**. |
| **2. Hostel Drop** | `PS-104` | University hostel graduation causes 11.6% deletion drop. | Flags statistical spike, but identifies innocent hypothesis (student batch graduation) and lists Form 8 as next step. |
| **3. True Outlier** | `PS-302` | Localized 9.8% deletion ($z = +6.4\sigma$, 0 transfers). | Flags `HIGH_STATISTICAL_OUTLIER`. Issues signed Ed25519 receipt and names missing Rule 21-A notices. |
| **4. Crowded Address** | `PS-203` | Address `H-42/B` jumps from 6 to 64 electors. | Flags `RULE_HOUSEHOLD_DENSITY`. Explains that industrial tenements share plot numbers in public rolls. |
| **5. Batch OCR Typo**| `PS-207` | Batch modification corrupts ages to 195 or 14. | Flags `RULE_AGE_COHORT_IMPLAUSIBLE` by checking historical lineage (voter was previously 39). |
| **6. Transliteration**| `PS-305` $\leftrightarrow$ `PS-306`| 14 cross-booth pairs with similar names (*"Maheshbhai"* vs *"Mahesh Kumar"*). | `RULE_LEXICAL_DUP_CLUSTER` matches demographic attributes; caps confidence at 0.79 due to missing photos. |

---

## 4. Hackathon Cross-Questioning Defense Guide

---

### Category A: Institutional & Policy Traps

#### Q1: "ECI already has ERONET. Why are you rebuilding voter registration?"
* **Judge's Intent:** Testing whether you understand the Indian election tech landscape or naively built a redundant project.
* **What NOT to Say:** *"Our system is better than ERONET because we use modern AI to detect fake voters."* (Immediate failure).
* **Winning Answer:**
  > "We do **not** rebuild voter registration, and we do **not** compete with ERONET. ERONET is ECI's internal operational database with access to voter photographs and ground Booth Level Officers (BLOs).
  >
  > PollToll solves a distinct institutional problem: **independent, third-party change auditing over *published* roll snapshots**. When ECI publishes thousands of separate booth PDFs during Draft and Final revisions, outside observers, civic watchdogs, and journalists receive disconnected lists. When a polling booth splits, 340 removals in Booth A and 340 additions in Booth B appear as separate lists, triggering viral 'voter deletion' panics.
  >
  > PollToll provides an independent ledger that deterministically links cross-booth transfers, tests statistical changes against historical baselines, and issues Ed25519-signed reproducible audit receipts."

#### Q2: "Are you accusing election officials or political parties of fraud?"
* **Judge's Intent:** Testing your political neutrality, bias, and legal liability awareness.
* **What NOT to Say:** *"We use AI to catch fraudulent deletions by corrupt officials."*
* **Winning Answer:**
  > "Never. PollToll adheres to strict epistemic neutrality. Our engine enforces deterministic rules that separate **verified roll math** from **unverified intent**.
  >
  > For every statistical outlier, our 5-Part Evidence Schema explicitly discloses:
  > 1. Innocent administrative explanations—such as university hostel turnover or slum redevelopment.
  > 2. **Missing evidence** that public rolls cannot prove—such as Rule 21-A statutory notices or BLO field verification logs.
  > 3. The official statutory next step under the Registration of Electors Rules, 1960.
  >
  > We identify where human auditors should look; we never allege fraud or name political entities."

---

### Category B: Data, Privacy & Legality Traps

#### Q3: "Where did you get this voter data? Did you scrape real voters' personal details?"
* **Judge's Intent:** Checking for DPDP Act (Digital Personal Data Protection Act) violations and privacy infringement.
* **What NOT to Say:** *"We scraped published PDFs from the CEO portal."*
* **Winning Answer:**
  > "PollToll operates on **100% synthetic data**. Every single elector record is generated using our deterministic generator script and prefixed with `SYN-`.
  >
  > Zero real voter PII is ingested, stored, or processed in this prototype. Our ingestion pipeline at `POST /api/v1/ingest/snapshot` strictly validates that all incoming records follow the `SYN-*` schema, enforcing data protection by design."

#### Q4: "How do you ingest real rolls if you were to deploy this in production?"
* **Judge's Intent:** Testing if your architecture can scale beyond synthetic CSVs to messy real-world PDFs.
* **Winning Answer:**
  > "ECI publishes machine-readable, searchable PDFs (without photos) during Draft and Final revisions, alongside weekly Forms 9, 10, and 11 claims and objections lists.
  >
  > In production, our ingestion plane uses a PDF extraction pipeline that normalizes booth headers, serial numbers, and EPIC coordinates into canonical CSV records, computes an immutable SHA-256 dataset hash, and registers the snapshot into DuckDB via our content-addressed pipeline."

---

### Category C: Statistical & Algorithmic Traps

#### Q5: "Why did you use Wilson score intervals instead of standard standard deviation or normal approximation?"
* **Judge's Intent:** Testing your mathematical and statistical rigor.
* **What NOT to Say:** *"Our library had Wilson score built-in, so we used it."*
* **Winning Answer:**
  > "Because polling booths have relatively small populations ($n \approx 300\text{ to }1,200$ electors) and deletion proportions are close to zero ($\hat{p} \approx 1\%\text{ to }3\%$).
  >
  > Under these conditions, the standard Wald normal approximation ($\hat{p} \pm z\sqrt{\hat{p}(1-\hat{p})/n}$) suffers from severe coverage probability errors and can produce negative lower bounds. The Wilson score interval inverts the score test, guarantees boundaries within $[0, 1]$, and accurately reflects asymmetric binomial uncertainty at small sample sizes."

#### Q6: "Why is your lexical similarity confidence capped at 0.79?"
* **Judge's Intent:** Testing whether you know the limitations of your own ML/NLP models.
* **Winning Answer:**
  > "In public electoral rolls, photographs and full dates of birth are intentionally redacted for privacy. When two additions appear across neighboring booths sharing identical family names, age, and house numbers, string similarity (using `token_sort_ratio`) cannot differentiate between:
  > 1. A single voter who accidentally registered twice under different transliteration spellings.
  > 2. Real twins or cousins in large joint-family households.
  >
  > To claim 99% confidence on text alone would be intellectually dishonest. We cap confidence at 0.79 and refer the pair to the ERO for internal ERONET DSE/PSE photo matching."

---

### Category D: Cryptography & System Integrity Traps

#### Q7: "Why Ed25519? Why not ECDSA or RSA-4096?"
* **Judge's Intent:** Testing cryptographic knowledge and architectural decision-making.
* **Winning Answer:**
  > "Three reasons:
  > 1. **Zero-Trust Client Verification**: Modern browsers natively support Ed25519 via the W3C Web Cryptography API (`window.crypto.subtle`). Our Next.js client verifies receipts without any external JavaScript cryptography libraries.
  > 2. **Security & Side-Channel Immunity**: Ed25519 is constant-time, eliminating timing-attack vulnerabilities inherent in older RSA implementations. It also avoids ECDSA's vulnerability where a flawed random nonce leaks the private key.
  > 3. **Compact Size**: Ed25519 produces 32-byte public keys and 64-byte signatures, making our `.polltoll-receipt.json` bundles lightweight and easily shareable."

#### Q8: "What prevents someone from tampering with the audit receipt JSON after you sign it?"
* **Judge's Intent:** Testing your understanding of digital signature payload binding.
* **Winning Answer:**
  > "The signature signs the **canonical UTF-8 byte representation** of the JSON payload (`sort_keys=True`, normalized separators).
  >
  > If a malicious actor alters a single digit—for instance, changing `deleted: 340` to `deleted: 999999`—two cryptographic checks fail instantly:
  > 1. The computed SHA-256 digest of the payload will not match the receipt's claimed hash.
  > 2. `crypto.subtle.verify` will reject the Ed25519 signature against the auditor's public key.
  >
  > You can test this live right now in our **Assurance Center** by clicking *'Simulate Tampering'*; WebCrypto rejects the receipt in real time."

---

### Category E: AI & Free-Tier Engineering Traps

#### Q9: "What happens if your Gemini API key hits rate limits (HTTP 429) during our demo?"
* **Judge's Intent:** Checking if your live demo is fragile.
* **Winning Answer:**
  > "Our architecture is quota-shielded with 5 defensive layers:
  > 1. **DuckDB Persistent SHA-256 Response Cache**: Any repeat claim or citizen question returns from DuckDB in $<5\text{ms}$ with zero API calls.
  > 2. **Deterministic Fast Path**: EPIC history tracking runs purely on DuckDB SQL, requiring zero LLM tokens.
  > 3. **Model Cascade**: If `gemini-3.5-flash-lite` encounters capacity limits, the engine cascades to `gemini-3.1-flash-lite` and `gemini-3.8-flash`.
  > 4. **Multi-Key Pool with 60s Cooldown**: The backend rotates across configured API keys and puts rate-limited keys into a 60-second cooldown.
  > 5. **Graceful Deterministic Fallback**: Even if all external AI services are completely offline, our deterministic engine generates full 5-part explanations without crashing."

#### Q10: "LLMs hallucinate. How do you ensure the Citizen Assistant doesn't give incorrect election advice?"
* **Judge's Intent:** Testing GenAI safety and grounding.
* **Winning Answer:**
  > "We use **Strict Grounding with Structured Outputs**:
  > 1. The LLM is never allowed to answer from general memory. We pass the exact DuckDB ledger history as structured JSON context.
  > 2. We enforce a Pydantic schema (`response_format=_GeminiCitizenStructured.model_json_schema()`) which restricts output strictly to official ECI statutory procedures (Forms 6, 7, and 8).
  > 3. Every response undergoes regex-based neutrality sanitization to ensure objective, public-service phrasing."

---

## 5. Quick Reference: System Cheat-Sheet for Pitching

| Feature | Technical Metric | 10-Second Pitch Summary |
| :--- | :--- | :--- |
| **Change Ledger** | DuckDB Full Outer Join | Reconciles thousands of changes deterministically into `ADDED`, `DELETED`, `MODIFIED`, and `BOOTH_TRANSFERRED`. |
| **Booth Split Resolution** | $338/340$ EPIC Transfer Match | Proves that 340 apparent deletions in `PS-109` simply moved to adjacent `PS-110`, stopping viral misinformation. |
| **Statistical Engine** | 95% Wilson CI + Historical $Z$-Score | Flags true statistical spikes ($>3.5\sigma$) while accounting for small-sample binomial uncertainty. |
| **Cryptographic Receipts** | Ed25519 + W3C WebCrypto | Issues signed receipts verified client-side in the browser in under $2\text{ms}$. |
| **Reviewer Trail** | SHA-256 Hash Chaining | Tamper-evident, append-only log recording every human auditor note and status change. |
| **Multilingual Verify** | EN / HI / GU Voice & Text | Empowers citizens and journalists with instant, non-partisan status checks grounded in ECI statutory rules. |
