"""Structured ERONET vs. PollToll Feature-by-Feature Gap Analysis service."""

from __future__ import annotations

from app.models import GapAnalysisItem


def get_eronet_gap_matrix() -> list[GapAnalysisItem]:
    return [
        GapAnalysisItem(
            id=1,
            capability="National Voter Registration & Form 6 / 7 / 8 Processing",
            eronet_documented_status="Publicly documented core capability of ERONET / ERONET 2.0 / ECINET and voters.eci.gov.in.",
            internal_epistemic_limit="Confirmed operational at national scale across States/UTs.",
            external_audit_gap="No external gap — rebuilding voter registration workflows is redundant.",
            polltoll_wedge="Out of scope by design; Citizen Assistant only guides citizens to official ECI Form 6/7/8 channels.",
            is_prototype_core=False,
        ),
        GapAnalysisItem(
            id=2,
            capability="Photo & Demographic Duplicate Matching (PSE / DSE)",
            eronet_documented_status="Built into ERONET Decision Support System with BLO field verification checklists and Rule 18/21-A notices.",
            internal_epistemic_limit="Operates on full UNPER database including photographs not released in public PDFs.",
            external_audit_gap="Public searchable PDFs omit voter photos for privacy; competing on photo deduplication is impossible and undesirable.",
            polltoll_wedge="Do not compete on PSE; only surface cross-booth supplement transliteration clusters as secondary review cues.",
            is_prototype_core=False,
        ),
        GapAnalysisItem(
            id=3,
            capability="Cross-Version Electoral Change Ledger & Booth-Split Reconciliation",
            eronet_documented_status="Published externally as thousands of separate per-booth Draft, Supplement, and Final PDFs.",
            internal_epistemic_limit="EROs likely retain internal modification histories inside ERONET, which are not externally queryable.",
            external_audit_gap="HIGH GAP: Outside observers see disconnected booth PDFs; e.g. 340 deletions in Booth A and 338 transfers to Booth B trigger false 'mass deletion' panics.",
            polltoll_wedge="CORE WEDGE #1: Deterministic Change Ledger reconciling ADDED, DELETED, MODIFIED, and cross-booth BOOTH_TRANSFERRED records with SHA-256 lineage.",
            is_prototype_core=True,
        ),
        GapAnalysisItem(
            id=4,
            capability="Historical-Baseline Spatio-Temporal Anomaly Testing with Uncertainty Bounds",
            eronet_documented_status="Not exposed on public portals (which show single-cycle roll PDFs and aggregate elector counts).",
            internal_epistemic_limit="Public docs cannot rule out internal CEO/ECI statistical dashboards during Special Summary Revision.",
            external_audit_gap="HIGH GAP: Civic groups and reporters cite raw deletion numbers without multi-year baselines or 95% confidence bounds.",
            polltoll_wedge="CORE WEDGE #2: Tests booth rates against 3-cycle historical baselines with explicit 95% Wilson confidence intervals and Z-scores.",
            is_prototype_core=True,
        ),
        GapAnalysisItem(
            id=5,
            capability="5-Part Evidence-Backed Explanations with Missing-Evidence Disclosure",
            eronet_documented_status="Published supplements list terse reason codes (S/E/Q/M/R) without multi-hypothesis audit context.",
            internal_epistemic_limit="Internal Decision Matrix stores BLO remarks that remain non-public for privacy.",
            external_audit_gap="HIGH GAP: No neutral tool states what changed, which rule fired, innocent causes, AND which non-public documents are missing.",
            polltoll_wedge="CORE WEDGE #3: Enforced 5-part schema (What changed, Rule, Innocent causes, Missing evidence, Next verification step).",
            is_prototype_core=True,
        ),
        GapAnalysisItem(
            id=6,
            capability="Tamper-Evident Third-Party Audit Receipts & Append-Only Correction Log",
            eronet_documented_status="Not applicable — ERONET is the authority's internal operational database, not an external attestation protocol.",
            internal_epistemic_limit="Even with strong internal logs, an operational authority cannot act as its own independent external auditor.",
            external_audit_gap="CRITICAL STARTUP MOAT: Observers, universities, and civic groups lack reproducible signed receipts proving identical neutral tests.",
            polltoll_wedge="CORE WEDGE #4: Ed25519-signed .polltoll-receipt.json with dataset/rule SHA-256s + hash-chained review log, verifiable in-browser via WebCrypto.",
            is_prototype_core=True,
        ),
        GapAnalysisItem(
            id=7,
            capability="Ledger-Grounded Viral Claim Checker & Multilingual Change Assistant (EN / HI / GU)",
            eronet_documented_status="Voter Portal supports current EPIC lookup; viral claims are addressed ad-hoc via press releases.",
            internal_epistemic_limit="Observable directly on public-facing portals.",
            external_audit_gap="Citizens and journalists lack instant, non-partisan triage separating Verified numbers, Disputed framing, and Unprovable claims.",
            polltoll_wedge="PUBLIC PORTAL (PollToll Verify): Free English, Hindi, and Gujarati voice/text assistant + 3-bucket Claim Checker.",
            is_prototype_core=True,
        ),
    ]
