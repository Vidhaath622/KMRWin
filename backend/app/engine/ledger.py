"""Electoral Change Ledger & Longitudinal Citizen Lookup over DuckDB snapshots."""

from __future__ import annotations

import hashlib
import math
from typing import Any

import duckdb

from app.data.generator import list_snapshots
from app.i18n import (
    LanguageCode,
    normalize_lang,
    pick,
    tr_booth,
    tr_constituency,
    tr_person,
    tr_section,
    tr_snapshot_label,
)
from app.models import (
    BoothChangeSummary,
    CitizenLookupResponse,
    LedgerEntry,
    SnapshotMeta,
)


def wilson_ci_95(successes: int, total: int) -> tuple[float, float]:
    """Computes exact 95% Wilson score confidence interval for a binomial proportion."""
    if total <= 0:
        return (0.0, 0.0)
    z = 1.959963984540054
    phat = successes / total
    denom = 1.0 + (z * z) / total
    center = (phat + (z * z) / (2.0 * total)) / denom
    half = (z * math.sqrt((phat * (1.0 - phat) + (z * z) / (4.0 * total)) / total)) / denom
    return (round(max(0.0, center - half), 5), round(min(1.0, center + half), 5))


def get_snapshot_meta(con: duckdb.DuckDBPyConnection, version_id: str, lang: str = "en") -> SnapshotMeta:
    snaps = {s.version_id: s for s in list_snapshots(con, lang=lang)}
    if version_id not in snaps:
        raise ValueError(f"Unknown snapshot version_id: {version_id}")
    return snaps[version_id]


def compute_historical_deletion_baselines(
    con: duckdb.DuckDBPyConnection,
) -> dict[str, dict[str, float]]:
    """Computes multi-cycle historical deletion rate baselines (v2024_final -> v2025_draft -> v2025_final)."""
    pairs = [("v2024_final", "v2025_draft"), ("v2025_draft", "v2025_final")]
    booth_rates: dict[str, list[float]] = {}
    booth_counts: dict[str, list[int]] = {}

    for v_a, v_b in pairs:
        rows = con.execute(
            """
            WITH prev AS (
                SELECT booth_id, epic_id FROM roll_entries WHERE version_id = ?
            ),
            curr AS (
                SELECT epic_id FROM roll_entries WHERE version_id = ?
            )
            SELECT
                p.booth_id,
                COUNT(*) AS n_prev,
                SUM(CASE WHEN c.epic_id IS NULL THEN 1 ELSE 0 END) AS n_del
            FROM prev p
            LEFT JOIN curr c ON p.epic_id = c.epic_id
            GROUP BY p.booth_id
            """,
            [v_a, v_b],
        ).fetchall()
        for booth_id, n_prev, n_del in rows:
            rate = (n_del / n_prev) if n_prev else 0.0
            booth_rates.setdefault(booth_id, []).append(rate)
            booth_counts.setdefault(booth_id, []).append(n_prev)

    result: dict[str, dict[str, float]] = {}
    for booth_id, rates in booth_rates.items():
        mean_rate = sum(rates) / len(rates)
        avg_n = int(sum(booth_counts[booth_id]) / len(booth_counts[booth_id]))
        # Binomial sampling std dev under historical baseline + empirical dispersion floor
        std = max(math.sqrt(max(mean_rate * (1.0 - mean_rate), 1e-5) / max(avg_n, 1)), 0.0045)
        _, ci_hi = wilson_ci_95(int(round(mean_rate * avg_n)), avg_n)
        result[booth_id] = {
            "mean_rate": round(mean_rate, 5),
            "std_rate": round(std, 5),
            "ci_upper_95": ci_hi,
        }
    return result


def compute_change_ledger(
    con: duckdb.DuckDBPyConnection,
    from_version: str = "v2025_final",
    to_version: str = "v2026_draft",
    sample_limit: int = 120,
    lang: str = "en",
) -> tuple[
    SnapshotMeta,
    SnapshotMeta,
    dict[str, int],
    list[BoothChangeSummary],
    list[LedgerEntry],
]:
    """Computes full row-level Electoral Change Ledger & booth-level statistical summaries."""
    lang_code = normalize_lang(lang)
    s_from = get_snapshot_meta(con, from_version, lang=lang_code)
    s_to = get_snapshot_meta(con, to_version, lang=lang_code)
    baselines = compute_historical_deletion_baselines(con)

    # Full SQL classification across snapshots:
    # - ADDED: in `to`, not in `from`
    # - DELETED: in `from`, not in `to` anywhere in constituency
    # - BOOTH_TRANSFERRED: in `from` AND in `to`, with different `booth_id`
    # - MODIFIED: same `booth_id`, but house_no or elector_name changed, or age changed by != expected (+0/+1/+2)
    diff_rows = con.execute(
        """
        WITH f AS (
            SELECT * FROM roll_entries WHERE version_id = ?
        ),
        t AS (
            SELECT * FROM roll_entries WHERE version_id = ?
        )
        SELECT
            COALESCE(t.epic_id, f.epic_id) AS epic_id,
            COALESCE(t.elector_name, f.elector_name) AS elector_name,
            COALESCE(t.constituency_id, f.constituency_id) AS constituency_id,
            COALESCE(t.constituency_name, f.constituency_name) AS constituency_name,
            f.booth_id AS from_booth_id,
            t.booth_id AS to_booth_id,
            f.serial_no AS from_serial_no,
            t.serial_no AS to_serial_no,
            COALESCE(t.house_no, f.house_no) AS house_no,
            f.house_no AS house_before,
            t.house_no AS house_after,
            f.age AS age_before,
            t.age AS age_after,
            f.elector_name AS name_before,
            t.elector_name AS name_after,
            COALESCE(NULLIF(t.reason_code, ''), NULLIF(f.reason_code, '')) AS reason_code,
            COALESCE(t.supplement_ref, f.supplement_ref) AS supplement_ref,
            CASE
                WHEN f.epic_id IS NULL THEN 'ADDED'
                WHEN t.epic_id IS NULL THEN 'DELETED'
                WHEN f.booth_id <> t.booth_id THEN 'BOOTH_TRANSFERRED'
                WHEN f.house_no <> t.house_no
                     OR f.elector_name <> t.elector_name
                     OR (t.age - f.age) NOT IN (0, 1)
                     OR t.age < 18 OR t.age > 110 THEN 'MODIFIED'
                ELSE 'UNCHANGED'
            END AS change_type
        FROM f
        FULL OUTER JOIN t ON f.epic_id = t.epic_id
        WHERE CASE
            WHEN f.epic_id IS NULL THEN TRUE
            WHEN t.epic_id IS NULL THEN TRUE
            WHEN f.booth_id <> t.booth_id THEN TRUE
            WHEN f.house_no <> t.house_no
                 OR f.elector_name <> t.elector_name
                 OR (t.age - f.age) NOT IN (0, 1)
                 OR t.age < 18 OR t.age > 110 THEN TRUE
            ELSE FALSE
        END
        """,
        [from_version, to_version],
    ).fetchall()

    totals = {
        "electors_from": s_from.total_electors,
        "electors_to": s_to.total_electors,
        "added": 0,
        "deleted": 0,
        "modified": 0,
        "booth_transferred": 0,
    }

    per_booth_stats: dict[str, dict[str, int]] = {}
    sample_entries: list[LedgerEntry] = []

    for r in diff_rows:
        (
            epic_id,
            elector_name,
            cid,
            cname,
            from_bid,
            to_bid,
            from_sno,
            to_sno,
            house_no,
            house_before,
            house_after,
            age_before,
            age_after,
            name_before,
            name_after,
            reason_code,
            supplement_ref,
            ctype,
        ) = r

        if ctype == "ADDED":
            totals["added"] += 1
            per_booth_stats.setdefault(to_bid, _zero_bstat())["added"] += 1
        elif ctype == "DELETED":
            totals["deleted"] += 1
            per_booth_stats.setdefault(from_bid, _zero_bstat())["deleted"] += 1
        elif ctype == "BOOTH_TRANSFERRED":
            totals["booth_transferred"] += 1
            per_booth_stats.setdefault(from_bid, _zero_bstat())["transferred_out"] += 1
            per_booth_stats.setdefault(to_bid, _zero_bstat())["transferred_in"] += 1
        elif ctype == "MODIFIED":
            totals["modified"] += 1
            per_booth_stats.setdefault(to_bid, _zero_bstat())["modified"] += 1

        if len(sample_entries) < sample_limit or epic_id in (
            "SYN-GJ-109-0042",
            "SYN-GJ-104-0019",
            "SYN-GJ-207-0011",
        ):
            mod_fields: dict[str, dict[str, Any]] = {}
            if ctype == "MODIFIED":
                if house_before != house_after:
                    mod_fields["house_no"] = {"before": house_before, "after": house_after}
                if name_before != name_after:
                    mod_fields["elector_name"] = {
                        "before": tr_person(name_before, lang_code),
                        "after": tr_person(name_after, lang_code),
                    }
                if age_before != age_after:
                    mod_fields["age"] = {"before": age_before, "after": age_after}
            elif ctype == "BOOTH_TRANSFERRED":
                mod_fields["booth_id"] = {"before": from_bid, "after": to_bid}

            lid = hashlib.sha256(
                f"{from_version}:{to_version}:{epic_id}:{ctype}".encode("utf-8")
            ).hexdigest()[:14]

            sample_entries.append(
                LedgerEntry(
                    ledger_id=f"LDG-{lid.upper()}",
                    epic_id=epic_id,
                    elector_name=tr_person(elector_name, lang_code),
                    change_type=ctype,
                    constituency_id=cid,
                    constituency_name=tr_constituency(cname, lang_code),
                    from_booth_id=from_bid,
                    to_booth_id=to_bid,
                    from_serial_no=from_sno,
                    to_serial_no=to_sno,
                    house_no=house_no,
                    age_before=age_before,
                    age_after=age_after,
                    reason_code=reason_code,
                    modified_fields=mod_fields,
                    from_snapshot_sha256=s_from.sha256,
                    to_snapshot_sha256=s_to.sha256,
                    supplement_ref=supplement_ref or f"{to_version.upper()}-DIFF",
                )
            )

    # Prioritize hero/interesting entries at top of sample list
    priority_order = {"BOOTH_TRANSFERRED": 0, "DELETED": 1, "MODIFIED": 2, "ADDED": 3}
    sample_entries.sort(
        key=lambda e: (
            e.epic_id not in ("SYN-GJ-109-0042", "SYN-GJ-104-0019", "SYN-GJ-207-0011"),
            priority_order.get(e.change_type, 9),
            e.epic_id,
        )
    )
    sample_entries = sample_entries[:sample_limit]

    # Booth counts
    booth_rows = con.execute(
        """
        SELECT
            b.booth_id,
            b.booth_name,
            b.constituency_id,
            b.constituency_name,
            b.lat,
            b.lon,
            (SELECT COUNT(*) FROM roll_entries r1 WHERE r1.version_id = ? AND r1.booth_id = b.booth_id) AS n_from,
            (SELECT COUNT(*) FROM roll_entries r2 WHERE r2.version_id = ? AND r2.booth_id = b.booth_id) AS n_to
        FROM booths b
        ORDER BY b.booth_id ASC
        """,
        [from_version, to_version],
    ).fetchall()

    booth_summaries: list[BoothChangeSummary] = []
    for bid, bname, cid, cname, lat, lon, n_from, n_to in booth_rows:
        st = per_booth_stats.get(bid, _zero_bstat())
        raw_removed_from_booth = st["deleted"] + st["transferred_out"]
        raw_del_rate = (raw_removed_from_booth / n_from) if n_from else 0.0
        net_del_rate = (st["deleted"] / n_from) if n_from else 0.0
        ci_lo, ci_hi = wilson_ci_95(st["deleted"], n_from)
        base_info = baselines.get(bid, {"mean_rate": 0.018, "std_rate": 0.006})
        z_val = (net_del_rate - base_info["mean_rate"]) / max(base_info["std_rate"], 1e-4)

        booth_summaries.append(
            BoothChangeSummary(
                booth_id=bid,
                booth_name=tr_booth(bname, lang_code),
                constituency_id=cid,
                constituency_name=tr_constituency(cname, lang_code),
                latitude=lat,
                longitude=lon,
                electors_from=n_from,
                electors_to=n_to,
                added_count=st["added"],
                deleted_count=st["deleted"],
                modified_count=st["modified"],
                transferred_in_count=st["transferred_in"],
                transferred_out_count=st["transferred_out"],
                raw_deletion_rate=round(raw_del_rate, 5),
                net_effective_deletion_rate=round(net_del_rate, 5),
                deletion_ci_lower_95=ci_lo,
                deletion_ci_upper_95=ci_hi,
                historical_deletion_baseline=base_info["mean_rate"],
                z_score_vs_baseline=round(z_val, 2),
                flag_count=0,
            )
        )

    return s_from, s_to, totals, booth_summaries, sample_entries


def _zero_bstat() -> dict[str, int]:
    return {
        "added": 0,
        "deleted": 0,
        "modified": 0,
        "transferred_in": 0,
        "transferred_out": 0,
    }


def lookup_citizen_epic(con: duckdb.DuckDBPyConnection, query_epic: str, lang: str = "en") -> CitizenLookupResponse:
    """Traces a synthetic EPIC ID across all 4 published roll snapshots."""
    lang_code = normalize_lang(lang)
    clean_epic = query_epic.strip().upper()
    rows = con.execute(
        """
        SELECT
            r.version_id,
            s.publication_date,
            s.label,
            r.epic_id,
            r.elector_name,
            r.relation_name,
            r.gender,
            r.age,
            r.constituency_id,
            r.constituency_name,
            r.booth_id,
            r.booth_name,
            r.serial_no,
            r.house_no,
            r.section_name,
            r.reason_code,
            r.supplement_ref
        FROM roll_entries r
        JOIN snapshots s ON r.version_id = s.version_id
        WHERE UPPER(r.epic_id) = ?
        ORDER BY s.publication_date ASC
        """,
        [clean_epic],
    ).fetchall()

    if not rows:
        return CitizenLookupResponse(
            found=False,
            epic_id=clean_epic,
            current_status="NOT_FOUND",
            latest_record=None,
            version_history=[],
            plain_language_summary={
                "en": f"No synthetic elector record matching `{clean_epic}` was found across the published roll snapshots.",
                "hi": f"प्रकाशित मतदाता सूची स्नैपशॉट में `{clean_epic}` से मेल खाता कोई सिंथेटिक मतदाता रिकॉर्ड नहीं मिला।",
                "gu": f"પ્રકાશિત મતદાર યાદીના સ્નેપશોટમાં `{clean_epic}` સાથે મેળ ખાતો કોઈ સિન્થેટિક મતદાર રેકોર્ડ મળ્યો નથી.",
            },
            official_next_steps={
                "en": [
                    "Double-check the 10-character EPIC / synthetic test ID spelling.",
                    "Search by constituency and polling station on the official ECI Voter Portal (voters.eci.gov.in).",
                    "If eligible and unregistered, submit Form 6 online or via your Booth Level Officer (BLO).",
                ],
                "hi": [
                    "अपने EPIC नंबर की स्पेलिंग दोबारा जांचें।",
                    "आधिकारिक ECI पोर्टल (voters.eci.gov.in) पर विधानसभा और बूथ द्वारा खोजें।",
                    "यदि आप पात्र हैं और नाम दर्ज नहीं है, तो फॉर्म 6 (Form 6) ऑनलाइन या BLO के माध्यम से जमा करें।",
                ],
                "gu": [
                    "તમારા EPIC નંબરની જોડણી ફરીથી ચકાસો.",
                    "સત્તાવાર ECI પોર્ટલ (voters.eci.gov.in) પર વિધાનસભા અને બૂથ પ્રમાણે શોધો.",
                    "જો તમે પાત્ર છો અને નામ નોંધાયેલ નથી, તો ફોર્મ 6 (Form 6) ઓનલાઇન અથવા BLO મારફતે ભરો.",
                ],
            },
            relevant_eci_forms=["Form 6"],
        )

    history = [
        {
            "version_id": r[0],
            "publication_date": r[1],
            "snapshot_label": tr_snapshot_label(r[2], lang_code),
            "epic_id": r[3],
            "elector_name": tr_person(r[4], lang_code),
            "relation_name": tr_person(r[5], lang_code),
            "gender": r[6],
            "age": r[7],
            "constituency_id": r[8],
            "constituency_name": tr_constituency(r[9], lang_code),
            "booth_id": r[10],
            "booth_name": tr_booth(r[11], lang_code),
            "serial_no": r[12],
            "house_no": r[13],
            "section_name": tr_section(r[14], lang_code),
            "reason_code": r[15],
            "supplement_ref": r[16],
        }
        for r in rows
    ]

    latest = history[-1]
    versions_present = [h["version_id"] for h in history]

    if "v2026_draft" not in versions_present:
        status = "DELETED_IN_DRAFT_SUPPLEMENT"
        prev_booth = latest["booth_id"]
        name = latest["elector_name"]
        summaries = {
            "en": (
                f"Record `{clean_epic}` ({name}) was active in `{latest['version_id']}` at `{prev_booth}`, "
                f"but is absent from `v2026_draft` (Draft Revision Supplement). Because this is a Draft Roll, "
                f"the Claims & Objections window is specifically designed to review or restore eligible entries."
            ),
            "hi": (
                f"रिकॉर्ड `{clean_epic}` ({name}) `{latest['version_id']}` में बूथ `{prev_booth}` पर सक्रिय था, "
                f"लेकिन `v2026_draft` (ड्राफ्ट संशोधन सूची) में मौजूद नहीं है। चूंकि यह ड्राफ्ट रोल है, आप दावे और आपत्तियों (Claims & Objections) की अवधि में इसे जांच और बहाल करवा सकते हैं।"
            ),
            "gu": (
                f"રેકોર્ડ `{clean_epic}` ({name}) `{latest['version_id']}` માં બૂથ `{prev_booth}` પર સક્રિય હતો, "
                f"પરંતુ `v2026_draft` (ડ્રાફ્ટ સુધારણા યાદી) માં હાજર નથી. આ ડ્રાફ્ટ યાદી હોવાથી હક્ક-દાવા અને વાંધા અરજીના સમયગાળામાં તમે નામ ફરીથી નોંધાવી શકો છો."
            ),
        }
        steps = {
            "en": [
                f"Inspect the published Deletion Supplement list at `{prev_booth}` or with the Booth Level Officer (BLO) to check the recorded reason (e.g. shifted residence).",
                "If you still reside at the registered address, contact the Electoral Registration Officer (ERO) / BLO with residence proof during the Claims & Objections window or submit Form 6 for re-inclusion.",
                "If you moved to a new address or city, file Form 8 (Shifting of Residence) on voters.eci.gov.in.",
            ],
            "hi": [
                f"हटाए जाने का दर्ज कारण (जैसे निवास परिवर्तन) देखने के लिए बूथ `{prev_booth}` की डिलीशन सप्लीमेंट सूची या BLO से जांच करें।",
                "यदि आप अभी भी उसी पते पर रहते हैं, तो निवास प्रमाण के साथ BLO/ERO से संपर्क करें या पुनः नाम जुड़वाने हेतु Form 6 भरें।",
                "यदि आप नए पते पर स्थानांतरित हो गए हैं, तो voters.eci.gov.in पर Form 8 (पता परिवर्तन) भरें।",
            ],
            "gu": [
                f"નામ કમી થવાનું નોંધાયેલ કારણ (દા.ત. સ્થળાંતર) જાણવા બૂથ `{prev_booth}` ની ડિલીશન સપ્લીમેન્ટ યાદી અથવા BLO પાસે તપાસ કરો.",
                "જો તમે હજુ પણ તે જ સરનામે રહો છો, તો રહેઠાણના પુરાવા સાથે BLO/ERO નો સંપર્ક કરો અથવા નામ પુનઃ દાખલ કરવા Form 6 ભરો.",
                "જો તમે નવા સરનામે રહેવા ગયા હોવ, તો voters.eci.gov.in પર Form 8 (સરનામું બદલવા) ભરો.",
            ],
        }
        forms = ["Form 6", "Form 8"]
    else:
        prev = history[-2] if len(history) >= 2 else latest
        if prev["booth_id"] != latest["booth_id"]:
            status = "ACTIVE_BOOTH_TRANSFERRED"
            summaries = {
                "en": (
                    f"Good news: `{clean_epic}` ({latest['elector_name']}) is ACTIVE and safe in `v2026_draft`! "
                    f"Your entry was administratively transferred from `{prev['booth_id']}` to adjacent `{latest['booth_id']}` "
                    f"({latest['booth_name']}), Serial #{latest['serial_no']}, due to polling-station rationalization."
                ),
                "hi": (
                    f"अच्छी खबर: `{clean_epic}` ({latest['elector_name']}) `v2026_draft` में पूरी तरह सुरक्षित और सक्रिय (ACTIVE) है! "
                    f"मतदान केंद्र पुनर्गठन के कारण आपका नाम `{prev['booth_id']}` से पास के बूथ `{latest['booth_id']}` "
                    f"({latest['booth_name']}), क्रम संख्या #{latest['serial_no']} में स्थानांतरित हुआ है।"
                ),
                "gu": (
                    f"સારા સમાચાર: `{clean_epic}` ({latest['elector_name']}) `v2026_draft` માં સંપૂર્ણપણે સુરક્ષિત અને સક્રિય (ACTIVE) છે! "
                    f"મતદાન મથકના પુનર્ગઠનને કારણે તમારું નામ `{prev['booth_id']}` થી બાજુના બૂથ `{latest['booth_id']}` "
                    f"({latest['booth_name']}), ક્રમ નંબર #{latest['serial_no']} માં તબદીલ થયું છે."
                ),
            }
            steps = {
                "en": [
                    f"No re-registration needed. Note your updated polling booth `{latest['booth_id']}` and Serial #{latest['serial_no']}.",
                    "Verify your address details on the Voter Information Slip prior to polling day.",
                ],
                "hi": [
                    f"दोबारा पंजीकरण की आवश्यकता नहीं है। अपना नया मतदान केंद्र `{latest['booth_id']}` और क्रम संख्या #{latest['serial_no']} नोट कर लें।",
                    "मतदान से पहले अपनी मतदाता सूचना पर्ची (Voter Slip) जांच लें।",
                ],
                "gu": [
                    f"ફરીથી નોંધણી કરવાની કોઈ જરૂર નથી. તમારું નવું મતદાન મથક `{latest['booth_id']}` અને ક્રમ નંબર #{latest['serial_no']} નોંધી લો.",
                    "મતદાન દિવસ પહેલાં તમારી વોટર ઇન્ફોર્મેશન સ્લિપ ચકાસી લો.",
                ],
            }
            forms = []
        elif latest["age"] < 18 or latest["age"] > 110 or prev["house_no"] != latest["house_no"]:
            status = "ACTIVE_MODIFIED"
            summaries = {
                "en": (
                    f"Record `{clean_epic}` ({latest['elector_name']}) is ACTIVE in `v2026_draft` at `{latest['booth_id']}` "
                    f"(Serial #{latest['serial_no']}), but a field update was logged (Age: {prev['age']} -> {latest['age']}, "
                    f"House: {prev['house_no']} -> {latest['house_no']}). Please review for clerical accuracy."
                ),
                "hi": (
                    f"रिकॉर्ड `{clean_epic}` ({latest['elector_name']}) `v2026_draft` में बूथ `{latest['booth_id']}` पर सक्रिय है, "
                    f"लेकिन विवरण में बदलाव दर्ज हुआ है (आयु: {prev['age']} -> {latest['age']}, मकान: {prev['house_no']} -> {latest['house_no']})। त्रुटि होने पर सुधार कराएं।"
                ),
                "gu": (
                    f"રેકોર્ડ `{clean_epic}` ({latest['elector_name']}) `v2026_draft` માં બૂથ `{latest['booth_id']}` પર સક્રિય છે, "
                    f"પરંતુ વિગતમાં ફેરફાર નોંધાયો છે (ઉંમર: {prev['age']} -> {latest['age']}, મકાન: {prev['house_no']} -> {latest['house_no']}). ભૂલ હોય તો સુધારો કરાવો."
                ),
            }
            steps = {
                "en": [
                    "Your voting status remains active, so your registration is not deleted.",
                    "Submit Form 8 (Correction of Entries in Existing Electoral Roll) on voters.eci.gov.in or via your BLO to fix any clerical age/address typo.",
                ],
                "hi": [
                    "आपका मतदाता नाम सक्रिय है।",
                    "आयु या पते की लिपिकीय त्रुटि सुधारने के लिए voters.eci.gov.in या BLO के माध्यम से Form 8 भरें।",
                ],
                "gu": [
                    "તમારું મતદાર નામ સક્રિય છે.",
                    "ઉંમર કે સરનામાની છાપકામની ભૂલ સુધારવા voters.eci.gov.in અથવા BLO મારફતે Form 8 ભરો.",
                ],
            }
            forms = ["Form 8"]
        else:
            status = "ACTIVE_UNCHANGED"
            summaries = {
                "en": (
                    f"Record `{clean_epic}` ({latest['elector_name']}) is ACTIVE and consistent across `{len(history)}` "
                    f"published snapshots at `{latest['booth_id']}` ({latest['booth_name']}), Serial #{latest['serial_no']}."
                ),
                "hi": (
                    f"रिकॉर्ड `{clean_epic}` ({latest['elector_name']}) सभी `{len(history)}` प्रकाशित सूचियों में बूथ `{latest['booth_id']}` "
                    f"({latest['booth_name']}), क्रम #{latest['serial_no']} पर सुरक्षित और सक्रिय है।"
                ),
                "gu": (
                    f"રેકોર્ડ `{clean_epic}` ({latest['elector_name']}) તમામ `{len(history)}` પ્રકાશિત યાદીઓમાં બૂથ `{latest['booth_id']}` "
                    f"({latest['booth_name']}), ક્રમ #{latest['serial_no']} પર સુરક્ષિત અને સક્રિય છે."
                ),
            }
            steps = {
                "en": ["No action needed. Carry an ECI-approved photo ID along with your EPIC on polling day."],
                "hi": ["किसी कार्रवाई की आवश्यकता नहीं है। मतदान के दिन EPIC या मान्य फोटो पहचान पत्र साथ रखें।"],
                "gu": ["કોઈ કાર્યવાહીની જરૂર નથી. મતદાનના દિવસે EPIC અથવા માન્ય ફોટો ઓળખપત્ર સાથે રાખો."],
            }
            forms = []

    return CitizenLookupResponse(
        found=True,
        epic_id=clean_epic,
        current_status=status,
        latest_record=latest,
        version_history=history,
        plain_language_summary=summaries,
        official_next_steps=steps,
        relevant_eci_forms=forms,
    )
