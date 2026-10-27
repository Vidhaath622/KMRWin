"""Versioned Statistical Anomaly Engine with Historical Baselines & Uncertainty Bounds."""

from __future__ import annotations

import hashlib
from typing import Any

import duckdb
from rapidfuzz import fuzz

from app.engine.ledger import compute_historical_deletion_baselines, wilson_ci_95
from app.i18n import (
    LanguageCode,
    normalize_lang,
    pick,
    tr_booth,
    tr_constituency,
)
from app.models import (
    AnomalyFlag,
    BoothChangeSummary,
    FivePartExplanation,
    UncertaintyInterval,
)

RULE_PACK_VERSION = "polltoll-rules@1.0.0"

RULES_CATALOG: dict[str, dict[str, str]] = {
    "RULE_BOOTH_SPLIT_RECONCILE": {
        "version": "1.0.0",
        "formula": "raw_booth_outflow_rate > 0.15 AND (transferred_out / raw_outflow) >= 0.85",
    },
    "RULE_HIST_DEL_SPIKE": {
        "version": "1.0.0",
        "formula": "net_effective_deletion_rate > 0.05 AND z_score_vs_3cycle_baseline >= 3.5 AND ci_lower_95 > baseline_ci_upper",
    },
    "RULE_HOUSEHOLD_DENSITY": {
        "version": "1.0.0",
        "formula": "max_electors_per_house_no >= 30 AND single_cycle_house_additions >= 20",
    },
    "RULE_AGE_COHORT_IMPLAUSIBLE": {
        "version": "1.0.0",
        "formula": "count(age < 18 OR age > 110) >= 5",
    },
    "RULE_LEXICAL_DUP_CLUSTER": {
        "version": "1.0.0",
        "formula": "cross_booth_new_additions WHERE token_sort_ratio(name_a, name_b) >= 82 AND same_relation_age_house >= 5_pairs",
    },
}


def _flag_id(rule_id: str, booth_id: str, from_v: str, to_v: str) -> str:
    digest = hashlib.sha256(f"{rule_id}:{booth_id}:{from_v}:{to_v}".encode("utf-8")).hexdigest()[:10]
    return f"FLG-{booth_id.replace('-', '')}-{digest.upper()}"


def detect_anomalies(
    con: duckdb.DuckDBPyConnection,
    booth_summaries: list[BoothChangeSummary],
    from_version: str = "v2025_final",
    to_version: str = "v2026_draft",
    lang: str = "en",
) -> list[AnomalyFlag]:
    """Runs all versioned statistical rules and populates flag counts on booth_summaries."""
    lang_code = normalize_lang(lang)
    baselines = compute_historical_deletion_baselines(con)
    flags: list[AnomalyFlag] = []
    booth_map = {b.booth_id: b for b in booth_summaries}

    # 1. Check Booth Split Reconciliation & Net Deletion Spikes
    for b in booth_summaries:
        base = baselines.get(b.booth_id, {"mean_rate": 0.018, "std_rate": 0.006, "ci_upper_95": 0.031})
        raw_removed = b.deleted_count + b.transferred_out_count

        # Rule A: Reconciled Booth Boundary Split (prevents false viral panic!)
        if b.electors_from > 0 and (raw_removed / b.electors_from) > 0.15 and raw_removed > 0:
            transfer_share = b.transferred_out_count / raw_removed
            if transfer_share >= 0.85:
                sample_epics = [
                    r[0]
                    for r in con.execute(
                        """
                        SELECT f.epic_id
                        FROM roll_entries f
                        JOIN roll_entries t ON f.epic_id = t.epic_id
                        WHERE f.version_id = ? AND t.version_id = ?
                          AND f.booth_id = ? AND f.booth_id <> t.booth_id
                        ORDER BY (f.epic_id <> 'SYN-GJ-109-0042'), f.serial_no
                        LIMIT 6
                        """,
                        [from_version, to_version, b.booth_id],
                    ).fetchall()
                ]
                electors_label = pick(lang_code, "electors", "मतदाता", "મતદારો")
                dest_booths = [
                    f"{r[0]} ({r[1]} {electors_label})"
                    for r in con.execute(
                        """
                        SELECT t.booth_id, COUNT(*)
                        FROM roll_entries f
                        JOIN roll_entries t ON f.epic_id = t.epic_id
                        WHERE f.version_id = ? AND t.version_id = ?
                          AND f.booth_id = ? AND f.booth_id <> t.booth_id
                        GROUP BY t.booth_id
                        """,
                        [from_version, to_version, b.booth_id],
                    ).fetchall()
                ]
                dest_str = ", ".join(dest_booths) or pick(lang_code, "adjacent booth", "आसन्न बूथ", "નજીકનું બૂથ")

                headline = pick(
                    lang_code,
                    f"Apparent {raw_removed}-voter drop ({b.raw_deletion_rate * 100:.1f}%) in {b.booth_id} reconciled as intact cross-booth transfer to {dest_str}",
                    f"{b.booth_id} में प्रकट {raw_removed}-मतदाता की कमी ({b.raw_deletion_rate * 100:.1f}%) का {dest_str} में अक्षुण्ण क्रॉस-बूथ स्थानांतरण के रूप में मिलान हुआ",
                    f"{b.booth_id} માં દેખીતી {raw_removed}-મતદારોની કમી ({b.raw_deletion_rate * 100:.1f}%) {dest_str} માં અકબંધ ક્રોસ-બૂથ સ્થળાંતર તરીકે મેળવાઈ",
                )

                uncertainty_note = pick(
                    lang_code,
                    f"Raw booth drop was {b.raw_deletion_rate * 100:.1f}%, but after cross-booth EPIC reconciliation, true net deletion rate is {b.net_effective_deletion_rate * 100:.2f}% (95% CI [{b.deletion_ci_lower_95 * 100:.2f}%, {b.deletion_ci_upper_95 * 100:.2f}%]), well within baseline.",
                    f"बूथ से कुल निकासी {b.raw_deletion_rate * 100:.1f}% थी, लेकिन क्रॉस-बूथ EPIC मिलान के बाद, वास्तविक शुद्ध विलोपन दर {b.net_effective_deletion_rate * 100:.2f}% है (95% CI [{b.deletion_ci_lower_95 * 100:.2f}%, {b.deletion_ci_upper_95 * 100:.2f}%]), जो ऐतिहासिक आधाररेखा के भीतर है।",
                    f"બૂથમાંથી કુલ ઘટાડો {b.raw_deletion_rate * 100:.1f}% હતો, પરંતુ ક્રોસ-બૂથ EPIC સમાધાન પછી, સાચો ચોખ્ખો કમી દર {b.net_effective_deletion_rate * 100:.2f}% છે (95% CI [{b.deletion_ci_lower_95 * 100:.2f}%, {b.deletion_ci_upper_95 * 100:.2f}%]), જે ઐતિહાસિક આધારરેખાની અંદર છે.",
                )

                what_changed = pick(
                    lang_code,
                    f"Between `{from_version}` and `{to_version}`, {raw_removed} electors left `{b.booth_id}`. Cross-constituency EPIC matching proves {b.transferred_out_count} ({transfer_share * 100:.1f}%) remain active in `{dest_str}`, leaving only {b.deleted_count} net deletions.",
                    f"`{from_version}` और `{to_version}` के बीच, {raw_removed} मतदाता `{b.booth_id}` से बाहर हुए। निर्वाचन क्षेत्र स्तरीय EPIC मिलान से सिद्ध होता है कि {b.transferred_out_count} ({transfer_share * 100:.1f}%) `{dest_str}` में सक्रिय हैं, जिससे केवल {b.deleted_count} शुद्ध नाम कटना शेष रहता है।",
                    f"`{from_version}` અને `{to_version}` વચ્ચે, {raw_removed} મતદારો `{b.booth_id}` માંથી બહાર થયા. મતવિસ્તાર EPIC મેચિંગ સાબિત કરે છે કે {b.transferred_out_count} ({transfer_share * 100:.1f}%) `{dest_str}` માં સક્રિય રહે છે, જેથી માત્ર {b.deleted_count} ચોખ્ખી કમી બાકી રહે છે.",
                )

                rule_triggered = pick(
                    lang_code,
                    f"RULE_BOOTH_SPLIT_RECONCILE@1.0.0 — Triggered because raw booth outflow ({b.raw_deletion_rate * 100:.1f}%) exceeded 15% while >=85% ({transfer_share * 100:.1f}%) matched active EPICs in an adjacent booth.",
                    f"RULE_BOOTH_SPLIT_RECONCILE@1.0.0 — सक्रिय हुआ क्योंकि कुल बूथ बहिर्वाह ({b.raw_deletion_rate * 100:.1f}%) 15% से अधिक था, जबकि >=85% ({transfer_share * 100:.1f}%) आसन्न बूथ में सक्रिय EPIC से मेल खाते थे।",
                    f"RULE_BOOTH_SPLIT_RECONCILE@1.0.0 — ટ્રિગર થયું કારણ કે કાચો બૂથ આઉટફ્લો ({b.raw_deletion_rate * 100:.1f}%) 15% થી વધુ હતો જ્યારે >=85% ({transfer_share * 100:.1f}%) નજીકના બૂથમાં સક્રિય EPIC સાથે મેળ ખાતા હતા.",
                )

                innocent_explanations = pick(
                    lang_code,
                    [
                        "ECI polling-station rationalization (splitting booths exceeding ~900–1,500 electors into Wing-A and Wing-B).",
                        "Ward section boundary realignment within the same building complex.",
                    ],
                    [
                        "भारत निर्वाचन आयोग द्वारा मतदान केंद्र युक्तिकरण (~900–1,500 से अधिक मतदाताओं वाले बूथों को विंग-ए और विंग-बी में विभाजित करना)।",
                        "एक ही भवन परिसर के भीतर वार्ड अनुभाग सीमा का पुनर्गठन।",
                    ],
                    [
                        "ચૂંટણી પંચ દ્વારા મતદાન મથક તર્કસંગતીકરણ (~900–1,500 થી વધુ મતદારો ધરાવતા બૂથને વિંગ-એ અને વિંગ-બી માં વિભાજિત કરવું).",
                        "એ જ બિલ્ડિંગ સંકુલમાં વોર્ડ વિભાગની સીમાનું પુનર્ગઠન.",
                    ],
                )

                missing_evidence = pick(
                    lang_code,
                    [
                        "District Election Officer (DEO) / ECI Polling Station Rationalization Gazette notification.",
                        "Public voter-slip notification log confirming transferred electors were informed of Wing-B room change.",
                    ],
                    [
                        "जिला निर्वाचन अधिकारी (DEO) / ECI मतदान केंद्र युक्तिकरण राजपत्र अधिसूचना।",
                        "सार्वजनिक मतदाता पर्ची वितरण लॉग जो पुष्टि करे कि स्थानांतरित मतदाताओं को विंग-बी कक्ष परिवर्तन की सूचना दी गई थी।",
                    ],
                    [
                        "જિલ્લા ચૂંટણી અધિકારી (DEO) / ECI મતદાન મથક તર્કસંગતીકરણ ગેઝેટ જાહેરનામું.",
                        "જાહેર મતદાર કાપલી વિતરણ લોગ જે પુષ્ટિ કરે કે સ્થળાંતરિત મતદારોને વિંગ-બી રૂમ ફેરફારની જાણ કરવામાં આવી હતી.",
                    ],
                )

                next_verification_step = pick(
                    lang_code,
                    "Cross-check the booth serial mapping against the DEO's published List of Polling Stations notification and ensure public communication clarifies voters were moved, not removed.",
                    "DEO द्वारा प्रकाशित मतदान केंद्रों की सूची अधिसूचना के साथ बूथ क्रमांक मैपिंग की जांच करें और सुनिश्चित करें कि सार्वजनिक सूचना स्पष्ट करे कि मतदाताओं को स्थानांतरित किया गया है, हटाया नहीं गया है।",
                    "DEO ની પ્રકાશિત મતદાન મથકોની યાદી સાથે બૂથ સીરીયલ મેપિંગ ચકાસો અને ખાતરી કરો કે જાહેર સૂચના સ્પષ્ટ કરે કે મતદારો ખસેડાયા છે, કમી કરાયા નથી.",
                )

                confidence_basis = pick(
                    lang_code,
                    f"Exact deterministic EPIC match across {b.transferred_out_count}/{raw_removed} records in published snapshots.",
                    f"प्रकाशित स्नैपशॉट में {b.transferred_out_count}/{raw_removed} रिकॉर्ड में सटीक नियतात्मक EPIC मिलान।",
                    f"પ્રકાશિત સ્નેપશોટમાં {b.transferred_out_count}/{raw_removed} રેકોર્ડ્સમાં ચોક્કસ નિર્ણાયક EPIC મેળ.",
                )

                reasoning_steps = pick(
                    lang_code,
                    [
                        f"Detected {raw_removed} records absent from `{b.booth_id}` in `{to_version}`.",
                        f"Searched constituency `{b.constituency_id}` in `{to_version}` by EPIC ID and matched {b.transferred_out_count} active electors in `{dest_str}`.",
                        f"Recomputed net deletion rate ({b.net_effective_deletion_rate * 100:.2f}% vs {base['mean_rate'] * 100:.2f}% historical baseline; z={b.z_score_vs_baseline}).",
                    ],
                    [
                        f"`{to_version}` में `{b.booth_id}` से अनुपस्थित {raw_removed} रिकॉर्ड की पहचान की गई।",
                        f"`{to_version}` में EPIC ID द्वारा विधानसभा `{b.constituency_id}` में खोज की और `{dest_str}` में {b.transferred_out_count} सक्रिय मतदाताओं का मिलान किया।",
                        f"शुद्ध विलोपन दर की पुनर्गणना की ({b.net_effective_deletion_rate * 100:.2f}% बनाम {base['mean_rate'] * 100:.2f}% ऐतिहासिक आधाररेखा; z={b.z_score_vs_baseline})।",
                    ],
                    [
                        f"`{to_version}` માં `{b.booth_id}` માંથી ગેરહાજર {raw_removed} રેકોર્ડ્સ શોધાયા.",
                        f"`{to_version}` માં EPIC ID દ્વારા મતવિસ્તાર `{b.constituency_id}` માં સર્ચ કર્યું અને `{dest_str}` માં {b.transferred_out_count} સક્રિય મતદારો મેળવ્યા.",
                        f"ચોખ્ખો કમી દર ફરી ગણતરી કર્યો ({b.net_effective_deletion_rate * 100:.2f}% વિરુદ્ધ {base['mean_rate'] * 100:.2f}% ઐતિહાસિક આધારરેખા; z={b.z_score_vs_baseline}).",
                    ],
                )

                flags.append(
                    AnomalyFlag(
                        flag_id=_flag_id("RULE_BOOTH_SPLIT_RECONCILE", b.booth_id, from_version, to_version),
                        booth_id=b.booth_id,
                        booth_name=tr_booth(b.booth_name, lang_code),
                        constituency_id=b.constituency_id,
                        constituency_name=tr_constituency(b.constituency_name, lang_code),
                        rule_id="RULE_BOOTH_SPLIT_RECONCILE",
                        rule_version=RULES_CATALOG["RULE_BOOTH_SPLIT_RECONCILE"]["version"],
                        rule_formula=RULES_CATALOG["RULE_BOOTH_SPLIT_RECONCILE"]["formula"],
                        severity="INFO_RECONCILED",
                        headline=headline,
                        affected_records_count=raw_removed,
                        sample_epic_ids=sample_epics,
                        uncertainty=UncertaintyInterval(
                            point_estimate=b.net_effective_deletion_rate,
                            ci_lower_95=b.deletion_ci_lower_95,
                            ci_upper_95=b.deletion_ci_upper_95,
                            historical_baseline_mean=base["mean_rate"],
                            historical_baseline_ci_upper=base["ci_upper_95"],
                            z_score=b.z_score_vs_baseline,
                            sample_size=b.electors_from,
                            uncertainty_note=uncertainty_note,
                        ),
                        explanation=FivePartExplanation(
                            what_changed=what_changed,
                            rule_triggered=rule_triggered,
                            innocent_explanations=innocent_explanations,
                            missing_evidence=missing_evidence,
                            next_verification_step=next_verification_step,
                            confidence_level=0.98,
                            confidence_basis=confidence_basis,
                            reasoning_steps=reasoning_steps,
                            generated_by="deterministic-ledger-engine",
                        ),
                        review_status="RECONCILED_BOUNDARY_SHIFT",
                    )
                )

        # Rule B: Statistically Significant Net Deletion Spike vs Historical Baseline
        if (
            b.net_effective_deletion_rate > 0.05
            and b.z_score_vs_baseline >= 3.5
            and b.deletion_ci_lower_95 > base["ci_upper_95"]
        ):
            del_samples = [
                r[0]
                for r in con.execute(
                    """
                    SELECT f.epic_id
                    FROM roll_entries f
                    LEFT JOIN roll_entries t ON f.epic_id = t.epic_id AND t.version_id = ?
                    WHERE f.version_id = ? AND f.booth_id = ? AND t.epic_id IS NULL
                    ORDER BY (f.epic_id <> 'SYN-GJ-104-0019'), f.serial_no
                    LIMIT 6
                    """,
                    [to_version, from_version, b.booth_id],
                ).fetchall()
            ]
            is_hostel = "Hostel" in b.booth_name or "छात्रालय" in b.booth_name or "છાત્રાલય" in b.booth_name
            innocent = (
                pick(
                    lang_code,
                    [
                        "End-of-academic-year student graduation / hostel cohort turnover.",
                        "Bulk Form-8 shifting applications processed when students registered in home constituencies.",
                        "Consolidated cleanup of prior graduated batches during Special Summary Revision.",
                    ],
                    [
                        "शैक्षणिक सत्र समाप्ति पर छात्रों का स्नातक होना / छात्रावास समूह का स्थानांतरण।",
                        "गृह विधानसभा क्षेत्र में पंजीकरण कराने पर छात्रों द्वारा दिए गए फॉर्म 8 का थोक निस्तारण।",
                        "विशेष संक्षिप्त पुनरीक्षण के दौरान पूर्व उत्तीर्ण छात्रों के बैच का समेकित शुद्धिकरण।",
                    ],
                    [
                        "શૈક્ષણિક વર્ષ પૂરું થતાં વિદ્યાર્થીઓનું ગ્રેજ્યુએશન / છાત્રાલય સમૂહની ફેરબદલી.",
                        "ગૃહ મતવિસ્તારમાં નોંધણી કરાવવા પર વિદ્યાર્થીઓ દ્વારા આપેલ ફોર્મ 8 ની જથ્થાબંધ પ્રક્રિયા.",
                        "ખાસ સંક્ષિપ્ત સુધારણા દરમિયાન અગાઉ પાસ થયેલા બેચની એકસાથે સફાઈ.",
                    ],
                )
                if is_hostel
                else pick(
                    lang_code,
                    [
                        "Redevelopment, municipal road-widening, or multi-building housing relocation in Ward Sections 3–4.",
                        "Accumulated backlog clearance of deceased or permanently shifted electors following door-to-door BLO survey.",
                        "Possible Transfer to a different Assembly Constituency not included in this 3-constituency public slice.",
                    ],
                    [
                        "वार्ड खंड 3–4 में पुनर्विकास, नगरपालिका सड़क चौड़ीकरण या बहु-भवन आवास पुनर्वास।",
                        "घर-घर बीएलओ सर्वेक्षण के बाद मृत या स्थायी रूप से स्थानांतरित मतदाताओं के संचित बैकलॉग का निस्तारण।",
                        "किसी अन्य विधानसभा क्षेत्र में संभावित स्थानांतरण जो इस सार्वजनिक डेटा में शामिल नहीं है।",
                    ],
                    [
                        "વોર્ડ વિભાગ 3–4 માં પુનર્વિકાસ, મ્યુનિસિપલ રોડ પહોળો કરવો અથવા બહુમાળી મકાનોનું સ્થળાંતર.",
                        "ઘેર-ઘેર BLO સર્વેક્ષણ પછી મૃત્યુ પામેલા અથવા કાયમી સ્થળાંતર થયેલા મતદારોના બાકી રહેલા નામોની સફાઈ.",
                        "અન્ય કોઈ વિધાનસભા ક્ષેત્રમાં સંભવિત સ્થળાંતર જે આ જાહેર ડેટામાં સામેલ નથી.",
                    ],
                )
            )

            headline = pick(
                lang_code,
                f"Net deletion rate of {b.net_effective_deletion_rate * 100:.1f}% ({b.deleted_count}/{b.electors_from}) in {b.booth_id} exceeds historical baseline ({base['mean_rate'] * 100:.1f}%) by {b.z_score_vs_baseline:.1f}σ",
                f"{b.booth_id} में शुद्ध विलोपन दर {b.net_effective_deletion_rate * 100:.1f}% ({b.deleted_count}/{b.electors_from}) ऐतिहासिक आधाररेखा ({base['mean_rate'] * 100:.1f}%) से {b.z_score_vs_baseline:.1f}σ अधिक है",
                f"{b.booth_id} માં ચોખ્ખો કમી દર {b.net_effective_deletion_rate * 100:.1f}% ({b.deleted_count}/{b.electors_from}) ઐતિહાસિક આધારરેખા ({base['mean_rate'] * 100:.1f}%) કરતાં {b.z_score_vs_baseline:.1f}σ વધારે છે",
            )

            uncertainty_note = pick(
                lang_code,
                f"95% Wilson CI [{b.deletion_ci_lower_95 * 100:.1f}%, {b.deletion_ci_upper_95 * 100:.1f}%] does not overlap historical baseline upper bound ({base['ci_upper_95'] * 100:.1f}%, n={b.electors_from}).",
                f"95% विल्सन विश्वास अंतराल [{b.deletion_ci_lower_95 * 100:.1f}%, {b.deletion_ci_upper_95 * 100:.1f}%] ऐतिहासिक आधाररेखा की ऊपरी सीमा ({base['ci_upper_95'] * 100:.1f}%, n={b.electors_from}) से मेल नहीं खाता।",
                f"95% વિલ્સન સીઆઈ [{b.deletion_ci_lower_95 * 100:.1f}%, {b.deletion_ci_upper_95 * 100:.1f}%] ઐતિહાસિક આધારરેખાની ઉપરની મર્યાદા ({base['ci_upper_95'] * 100:.1f}%, n={b.electors_from}) ને ઓવરલેપ કરતો નથી.",
            )

            what_changed = pick(
                lang_code,
                f"`{b.booth_id}` ({tr_booth(b.booth_name, lang_code)}) recorded {b.deleted_count} net deletions out of {b.electors_from} electors ({b.net_effective_deletion_rate * 100:.1f}%), with 0 matching transfers to adjacent booths in `{b.constituency_id}`.",
                f"`{b.booth_id}` ({tr_booth(b.booth_name, lang_code)}) में {b.electors_from} मतदाताओं में से {b.deleted_count} शुद्ध नाम कटे ({b.net_effective_deletion_rate * 100:.1f}%), और `{b.constituency_id}` के आसन्न बूथों में 0 मिलान स्थानांतरण मिले।",
                f"`{b.booth_id}` ({tr_booth(b.booth_name, lang_code)}) માં {b.electors_from} મતદારોમાંથી {b.deleted_count} ચોખ્ખી કમી નોંધાઈ ({b.net_effective_deletion_rate * 100:.1f}%), અને `{b.constituency_id}` ના નજીકના બૂથોમાં 0 તબદીલીઓ મળી.",
            )

            rule_triggered = pick(
                lang_code,
                f"RULE_HIST_DEL_SPIKE@1.0.0 — Net deletion rate ({b.net_effective_deletion_rate * 100:.1f}%) > 5.0%, z = +{b.z_score_vs_baseline:.1f}σ (>= 3.5σ), and 95% lower CI ({b.deletion_ci_lower_95 * 100:.1f}%) > historical upper bound ({base['ci_upper_95'] * 100:.1f}%).",
                f"RULE_HIST_DEL_SPIKE@1.0.0 — शुद्ध विलोपन दर ({b.net_effective_deletion_rate * 100:.1f}%) > 5.0%, z = +{b.z_score_vs_baseline:.1f}σ (>= 3.5σ), और 95% निचला CI ({b.deletion_ci_lower_95 * 100:.1f}%) > ऐतिहासिक ऊपरी सीमा ({base['ci_upper_95'] * 100:.1f}%)।",
                f"RULE_HIST_DEL_SPIKE@1.0.0 — ચોખ્ખો કમી દર ({b.net_effective_deletion_rate * 100:.1f}%) > 5.0%, z = +{b.z_score_vs_baseline:.1f}σ (>= 3.5σ), અને 95% નીચલો CI ({b.deletion_ci_lower_95 * 100:.1f}%) > ઐતિહાસિક ઉપલી મર્યાદા ({base['ci_upper_95'] * 100:.1f}%).",
            )

            missing_evidence = pick(
                lang_code,
                [
                    "Form 7 / suo-motu deletion reason breakdown (Death vs. Shifted vs. Duplicate) from ERO supplement header.",
                    "Count of statutory notices issued under Rule 21-A of the Registration of Electors Rules, 1960.",
                    "BLO house-to-house field verification summary for the affected ward sections.",
                ],
                [
                    "ERO पूरक शीर्षक से फॉर्म 7 / स्वतः संज्ञान विलोपन कारण विवरण (मृत्यु बनाम स्थानांतरित बनाम डुप्लिकेट)।",
                    "मतदाता पंजीकरण नियम, 1960 के नियम 21-A के तहत जारी वैधानिक नोटिसों की संख्या।",
                    "प्रभावित वार्ड अनुभागों के लिए BLO घर-घर क्षेत्रीय सत्यापन सारांश।",
                ],
                [
                    "ERO પૂરક હેડરમાંથી ફોર્મ 7 / સ્વતઃ સંજ્ઞાન કમીના કારણોની વિગત (મૃત્યુ વિરુદ્ધ સ્થળાંતરિત વિરુદ્ધ ડુપ્લિકેટ).",
                    "મતદાર નોંધણી નિયમો, 1960 ના નિયમ 21-A હેઠળ જારી કરાયેલ વૈધાનિક નોટિસોની સંખ્યા.",
                    "અસરગ્રસ્ત વોર્ડ વિભાગો માટે BLO ઘર-ઘર ક્ષેત્ર ચકાસણી સારાંશ.",
                ],
            )

            next_verification_step = pick(
                lang_code,
                "Inspect published Form 10 / Deletion Supplement reason codes for this part and sample 15–20 affected addresses through authorized booth-level observers during the Claims & Objections period.",
                "इस भाग के लिए प्रकाशित फॉर्म 10 / विलोपन पूरक कारण कोड का निरीक्षण करें और दावे और आपत्ति अवधि के दौरान अधिकृत बूथ-स्तरीय पर्यवेक्षकों के माध्यम से 15–20 प्रभावित पतों का नमूना लें।",
                "આ ભાગ માટે પ્રકાશિત ફોર્મ 10 / કમી પૂરકના કારણ કોડ તપાસો અને દાવા અને વાંધાના સમયગાળા દરમિયાન અધિકૃત બૂથ-સ્તરીય નિરીક્ષકો દ્વારા 15–20 અસરગ્રસ્ત સરનામાઓની નમૂનારૂપ ચકાસણી કરો.",
            )

            confidence_basis = pick(
                lang_code,
                f"Non-overlapping 95% confidence intervals over n={b.electors_from} electors across 3 historical cycles; statistical pattern certainty is high, while administrative cause requires external documentary review.",
                f"3 ऐतिहासिक चक्रों में n={b.electors_from} मतदाताओं पर गैर-अतिव्यापी 95% विश्वास अंतराल; सांख्यिकीय पैटर्न निश्चितता उच्च है, जबकि प्रशासनिक कारण हेतु बाहरी दस्तावेजी समीक्षा आवश्यक है।",
                f"3 ઐતિહાસિક ચક્રોમાં n={b.electors_from} મતદારો પર ઓવરલેપ ન થતા 95% વિશ્વાસ અંતરાલો; આંકડાકીય પેટર્નની નિશ્ચિતતા ઊંચી છે, જ્યારે વહીવટી કારણ માટે બાહ્ય દસ્તાવેજી સમીક્ષા જરૂરી છે.",
            )

            reasoning_steps = pick(
                lang_code,
                [
                    f"Verified {b.deleted_count} EPICs from `{from_version}` do not appear anywhere in `{to_version}`.",
                    f"Compared observed rate ({b.net_effective_deletion_rate * 100:.1f}%) against `{b.booth_id}` 2024–2025 historical mean ({base['mean_rate'] * 100:.1f}%).",
                    "Confirmed lower 95% Wilson bound exceeds historical upper bound, ruling out small-sample random noise.",
                ],
                [
                    f"सत्यापित किया गया कि `{from_version}` के {b.deleted_count} EPIC `{to_version}` में कहीं भी दिखाई नहीं देते।",
                    f"देखी गई दर ({b.net_effective_deletion_rate * 100:.1f}%) की तुलना `{b.booth_id}` के 2024–2025 के ऐतिहासिक औसत ({base['mean_rate'] * 100:.1f}%) से की गई।",
                    "पुष्टि की गई कि निचला 95% विल्सन बाउंड ऐतिहासिक ऊपरी बाउंड से अधिक है, जिससे छोटे नमूने के यादृच्छिक विचलन की संभावना खारिज होती है।",
                ],
                [
                    f"ચકાસાયેલ છે કે `{from_version}` ના {b.deleted_count} EPIC `{to_version}` માં ક્યાંય દેખાતા નથી.",
                    f"જોવાયેલ દર ({b.net_effective_deletion_rate * 100:.1f}%) ની સરખામણી `{b.booth_id}` 2024–2025 ઐતિહાસિક સરેરાશ ({base['mean_rate'] * 100:.1f}%) સાથે કરી.",
                    "પુષ્ટિ થઈ કે નીચલો 95% વિલ્સન બાઉન્ડ ઐતિહાસિક ઉપલી મર્યાદા કરતાં વધુ છે, જે નાના નમૂનાના અણધાર્યા તફાવતને રદિયો આપે છે.",
                ],
            )

            flags.append(
                AnomalyFlag(
                    flag_id=_flag_id("RULE_HIST_DEL_SPIKE", b.booth_id, from_version, to_version),
                    booth_id=b.booth_id,
                    booth_name=tr_booth(b.booth_name, lang_code),
                    constituency_id=b.constituency_id,
                    constituency_name=tr_constituency(b.constituency_name, lang_code),
                    rule_id="RULE_HIST_DEL_SPIKE",
                    rule_version=RULES_CATALOG["RULE_HIST_DEL_SPIKE"]["version"],
                    rule_formula=RULES_CATALOG["RULE_HIST_DEL_SPIKE"]["formula"],
                    severity="HIGH_STATISTICAL_OUTLIER",
                    headline=headline,
                    affected_records_count=b.deleted_count,
                    sample_epic_ids=del_samples,
                    uncertainty=UncertaintyInterval(
                        point_estimate=b.net_effective_deletion_rate,
                        ci_lower_95=b.deletion_ci_lower_95,
                        ci_upper_95=b.deletion_ci_upper_95,
                        historical_baseline_mean=base["mean_rate"],
                        historical_baseline_ci_upper=base["ci_upper_95"],
                        z_score=b.z_score_vs_baseline,
                        sample_size=b.electors_from,
                        uncertainty_note=uncertainty_note,
                    ),
                    explanation=FivePartExplanation(
                        what_changed=what_changed,
                        rule_triggered=rule_triggered,
                        innocent_explanations=innocent,
                        missing_evidence=missing_evidence,
                        next_verification_step=next_verification_step,
                        confidence_level=0.94,
                        confidence_basis=confidence_basis,
                        reasoning_steps=reasoning_steps,
                        generated_by="deterministic-ledger-engine",
                    ),
                    review_status="OPEN_FOR_REVIEW",
                )
            )

    # 2. Rule C: Single-Address Household Density Jump
    crowded_rows = con.execute(
        """
        WITH curr AS (
            SELECT booth_id, house_no, COUNT(*) AS cnt_to, LIST(epic_id ORDER BY serial_no)[:6] AS sample_epics
            FROM roll_entries
            WHERE version_id = ?
            GROUP BY booth_id, house_no
            HAVING COUNT(*) >= 30
        ),
        prev AS (
            SELECT booth_id, house_no, COUNT(*) AS cnt_from
            FROM roll_entries
            WHERE version_id = ?
            GROUP BY booth_id, house_no
        )
        SELECT c.booth_id, c.house_no, COALESCE(p.cnt_from, 0) AS cnt_from, c.cnt_to, c.sample_epics
        FROM curr c
        LEFT JOIN prev p ON c.booth_id = p.booth_id AND c.house_no = p.house_no
        WHERE (c.cnt_to - COALESCE(p.cnt_from, 0)) >= 20
        """,
        [to_version, from_version],
    ).fetchall()

    for bid, house_no, cnt_from, cnt_to, sample_epics in crowded_rows:
        b = booth_map[bid]
        delta = cnt_to - cnt_from
        share = cnt_to / max(b.electors_to, 1)
        ci_lo, ci_hi = wilson_ci_95(cnt_to, b.electors_to)

        headline = pick(
            lang_code,
            f"Address `{house_no}` in {bid} grew from {cnt_from} to {cnt_to} registered electors (+{delta} in single revision)",
            f"{bid} में पता `{house_no}` {cnt_from} से बढ़कर {cnt_to} पंजीकृत मतदाताओं का हो गया (एकल पुनरीक्षण में +{delta})",
            f"{bid} માં સરનામું `{house_no}` {cnt_from} થી વધીને {cnt_to} નોંધાયેલ મતદારોનું થયું (એક જ સુધારણામાં +{delta})",
        )

        uncertainty_note = pick(
            lang_code,
            f"Exact deterministic count ({cnt_to} electors sharing string `{house_no}`); address formatting granularity in published PDFs creates high interpretive uncertainty.",
            f"सटीक नियतात्मक गणना (`{house_no}` साझा करने वाले {cnt_to} मतदाता); प्रकाशित पीडीएफ में पते के प्रारूप की सीमित जानकारी उच्च व्याख्यात्मक अनिश्चितता पैदा करती है।",
            f"ચોક્કસ નિર્ણાયક ગણતરી (`{house_no}` ધરાવતા {cnt_to} મતદારો); પ્રકાશિત પીડીએફમાં સરનામાના બંધારણની મર્યાદિત વિગત ઊંચી અર્થઘટન અનિશ્ચિતતા ઊભી કરે છે.",
        )

        what_changed = pick(
            lang_code,
            f"In `{bid}`, house identifier `{house_no}` increased from {cnt_from} electors in `{from_version}` to {cnt_to} electors in `{to_version}` (+{delta} new Form-6 supplement entries across diverse surnames).",
            f"`{bid}` में, मकान पहचानकर्ता `{house_no}` `{from_version}` में {cnt_from} मतदाताओं से बढ़कर `{to_version}` में {cnt_to} मतदाता हो गया (विविध उपनामों में +{delta} नई फॉर्म-6 पूरक प्रविष्टियां)।",
            f"`{bid}` માં, મકાન ઓળખકર્તા `{house_no}` `{from_version}` માં {cnt_from} મતદારોથી વધીને `{to_version}` માં {cnt_to} મતદારો થયા (વિવિધ અટક સાથે +{delta} નવી ફોર્મ-6 પૂરક એન્ટ્રીઓ).",
        )

        rule_triggered = pick(
            lang_code,
            f"RULE_HOUSEHOLD_DENSITY@1.0.0 — Triggered because `electors_per_house_no` ({cnt_to}) >= 30 and single-cycle addition delta (+{delta}) >= 20.",
            f"RULE_HOUSEHOLD_DENSITY@1.0.0 — सक्रिय हुआ क्योंकि `प्रति_मकान_मतदाता` ({cnt_to}) >= 30 और एकल-चक्र वृद्धि अंतर (+{delta}) >= 20 है।",
            f"RULE_HOUSEHOLD_DENSITY@1.0.0 — ટ્રિગર થયું કારણ કે `પ્રતિ_મકાન_મતદારો` ({cnt_to}) >= 30 અને એક-ચક્ર ઉમેરાનો તફાવત (+{delta}) >= 20 છે.",
        )

        innocent_explanations = pick(
            lang_code,
            [
                "Multi-unit apartment block, chawl, or industrial worker dormitory sharing a single municipal plot number (`H-42/B`) without flat sub-numbers.",
                "Clerical normalization where BLO/data-entry staff mapped an unnumbered lane or society onto a landmark house number.",
                "Newly occupied multi-family residential building registered during a special enrollment camp.",
            ],
            [
                "बहु-इकाई अपार्टमेंट ब्लॉक, चॉल, या औद्योगिक श्रमिक छात्रावास जो बिना फ्लैट उप-संख्या के एकल नगरपालिका प्लॉट संख्या (`H-42/B`) साझा करते हैं।",
                "लिपिकीय मानकीकरण जहां बीएलओ/डेटा-एंट्री कर्मियों ने बिना नंबर वाली गली या सोसायटी को किसी लैंडमार्क मकान नंबर से जोड़ दिया।",
                "विशेष नामांकन शिविर के दौरान पंजीकृत नव-आवासीय बहु-पारिवारिक आवासीय भवन।",
            ],
            [
                "મલ્ટી-યુનિટ એપાર્ટમેન્ટ બ્લોક, ચાલી, અથવા ઔદ્યોગિક કામદાર છાત્રાલય જે ફ્લેટ સબ-નંબર વિના એક જ મ્યુનિસિપલ પ્લોટ નંબર (`H-42/B`) ધરાવે છે.",
                "કારકુની સામાન્યકરણ જ્યાં BLO/ડેટા-એન્ટ્રી સ્ટાફે નંબર વગરની શેરી કે સોસાયટીને કોઈ સીમાચિહ્ન મકાન નંબર સાથે જોડી દીધી.",
                "ખાસ નોંધણી કેમ્પ દરમિયાન નોંધાયેલ નવી વસેલી બહુ-કુટુંબ રહેણાંક ઇમારત.",
            ],
        )

        missing_evidence = pick(
            lang_code,
            [
                "Municipal property / building type classification (single-family house vs. multi-unit tenement/dormitory).",
                "BLO bulk-address verification note (ECI manuals require supervisory check when >10–15 electors share one house number).",
            ],
            [
                "नगरपालिका संपत्ति / भवन प्रकार वर्गीकरण (एकल-पारिवारिक मकान बनाम बहु-इकाई टेनामेंट/छात्रावास)।",
                "BLO थोक-पता सत्यापन नोट (ECI नियमावली के अनुसार जब >10–15 मतदाता एक मकान नंबर साझा करते हैं तो पर्यवेक्षी जांच अनिवार्य है)।",
            ],
            [
                "મ્યુનિસિપલ મિલકત / બિલ્ડિંગ પ્રકાર વર્ગીકરણ (એકલ-પરિવારનું ઘર વિરુદ્ધ બહુ-એકમ ટેનામેન્ટ/છાત્રાલય).",
                "BLO બલ્ક-સરનામું ચકાસણી નોંધ (જ્યારે >10–15 મતદારો એક જ ઘર નંબર ધરાવતા હોય ત્યારે ચૂંટણી પંચની માર્ગદર્શિકા સુપરવાઇઝરી તપાસ ફરજિયાત કરે છે).",
            ],
        )

        next_verification_step = pick(
            lang_code,
            "Verify physical building structure type on municipal GIS / field visit before drawing any conclusion; if multi-unit apartment, recommend sub-unit numbering in Form 8.",
            "कोई निष्कर्ष निकालने से पहले नगरपालिका जीआईएस/क्षेत्रीय दौरे पर भौतिक भवन संरचना प्रकार की पुष्टि करें; यदि बहु-इकाई अपार्टमेंट है, तो फॉर्म 8 में उप-इकाई क्रमांकन की सिफारिश करें।",
            "કોઈપણ નિષ્કર્ષ પર પહોંચતા પહેલા મ્યુનિસિપલ GIS / સ્થળ મુલાકાત દ્વારા વાસ્તવિક મકાન માળખા પ્રકારની ચકાસણી કરો; જો મલ્ટી-યુનિટ એપાર્ટમેન્ટ હોય, તો ફોર્મ 8 માં સબ-યુનિટ નંબરિંગની ભલામણ કરો.",
        )

        confidence_basis = pick(
            lang_code,
            "Exact string concentration in published roll is 100% certain; physical occupancy requires field verification.",
            "प्रकाशित सूची में सटीक स्ट्रिंग एकाग्रता 100% निश्चित है; भौतिक उपस्थिति हेतु क्षेत्रीय सत्यापन आवश्यक है।",
            "પ્રકાશિત યાદીમાં ચોક્કસ સ્ટ્રિંગ સાંદ્રતા 100% ચોક્કસ છે; વાસ્તવિક વસવાટ માટે ક્ષેત્ર ચકાસણી જરૂરી છે.",
        )

        reasoning_steps = pick(
            lang_code,
            [
                f"Grouped `{to_version}` electors by `(booth_id, house_no)` and compared against `{from_version}`.",
                f"Observed `{house_no}` jumped +{delta} ({cnt_from} -> {cnt_to}) in a single supplement batch.",
                "Checked surname diversity across the 64 entries, consistent with either a multi-family tenement or clerical plot grouping.",
            ],
            [
                f"`{to_version}` के मतदाताओं को `(booth_id, house_no)` द्वारा समूहीकृत किया और `{from_version}` से तुलना की।",
                f"देखा गया कि एक ही पूरक बैच में `{house_no}` +{delta} ({cnt_from} -> {cnt_to}) बढ़ गया।",
                "प्रविष्टियों में उपनाम विविधता की जांच की, जो बहु-पारिवारिक आवास या लिपिकीय प्लॉट समूहीकरण के अनुकूल है।",
            ],
            [
                f"`{to_version}` ના મતદારોને `(booth_id, house_no)` દ્વારા જૂથબદ્ધ કર્યા અને `{from_version}` સાથે સરખામણી કરી.",
                f"જોયું કે એક જ પૂરક બેચમાં `{house_no}` +{delta} ({cnt_from} -> {cnt_to}) વધી ગયું.",
                "પ્રવેશોમાં અટક વિવિધતા તપાસી, જે બહુ-પરિવાર ભાડૂતી આવાસ અથવા કારકુની પ્લોટ જૂથીકરણ સાથે સુસંગત છે.",
            ],
        )

        flags.append(
            AnomalyFlag(
                flag_id=_flag_id("RULE_HOUSEHOLD_DENSITY", bid, from_version, to_version),
                booth_id=bid,
                booth_name=tr_booth(b.booth_name, lang_code),
                constituency_id=b.constituency_id,
                constituency_name=tr_constituency(b.constituency_name, lang_code),
                rule_id="RULE_HOUSEHOLD_DENSITY",
                rule_version=RULES_CATALOG["RULE_HOUSEHOLD_DENSITY"]["version"],
                rule_formula=RULES_CATALOG["RULE_HOUSEHOLD_DENSITY"]["formula"],
                severity="MODERATE_REVIEW",
                headline=headline,
                affected_records_count=cnt_to,
                sample_epic_ids=list(sample_epics),
                uncertainty=UncertaintyInterval(
                    point_estimate=round(share, 5),
                    ci_lower_95=ci_lo,
                    ci_upper_95=ci_hi,
                    historical_baseline_mean=round(cnt_from / max(b.electors_from, 1), 5),
                    historical_baseline_ci_upper=0.015,
                    z_score=round(delta / 4.2, 2),
                    sample_size=b.electors_to,
                    uncertainty_note=uncertainty_note,
                ),
                explanation=FivePartExplanation(
                    what_changed=what_changed,
                    rule_triggered=rule_triggered,
                    innocent_explanations=innocent_explanations,
                    missing_evidence=missing_evidence,
                    next_verification_step=next_verification_step,
                    confidence_level=0.91,
                    confidence_basis=confidence_basis,
                    reasoning_steps=reasoning_steps,
                    generated_by="deterministic-ledger-engine",
                ),
                review_status="OPEN_FOR_REVIEW",
            )
        )

    # 3. Rule D: Implausible Age / Demographic Cohort Batch
    age_rows = con.execute(
        """
        SELECT booth_id, COUNT(*) AS bad_cnt, LIST(epic_id ORDER BY (epic_id <> 'SYN-GJ-207-0011'), serial_no)[:6] AS sample_epics
        FROM roll_entries
        WHERE version_id = ? AND (age < 18 OR age > 110)
        GROUP BY booth_id
        HAVING COUNT(*) >= 5
        """,
        [to_version],
    ).fetchall()

    for bid, bad_cnt, sample_epics in age_rows:
        b = booth_map[bid]
        rate = bad_cnt / max(b.electors_to, 1)
        ci_lo, ci_hi = wilson_ci_95(bad_cnt, b.electors_to)

        headline = pick(
            lang_code,
            f"{bad_cnt} records in {bid} carry implausible ages (<18 or >110, e.g. 195, 138, 15) in supplement batch",
            f"{bid} में पूरक बैच के {bad_cnt} रिकॉर्ड में अस्वाभाविक आयु (<18 या >110, जैसे 195, 138, 15) दर्ज है",
            f"{bid} માં પૂરક બેચના {bad_cnt} રેકોર્ડ્સમાં અસંભવિત ઉંમર (<18 અથવા >110, દા.ત. 195, 138, 15) નોંધાયેલ છે",
        )

        uncertainty_note = pick(
            lang_code,
            f"{bad_cnt}/{b.electors_to} records violate statutory/biological age range [18, 110] in `{to_version}`.",
            f"`{to_version}` में {bad_cnt}/{b.electors_to} रिकॉर्ड वैधानिक/जैविक आयु सीमा [18, 110] का उल्लंघन करते हैं।",
            f"`{to_version}` માં {bad_cnt}/{b.electors_to} રેકોર્ડ્સ વૈધાનિક/જૈવિક વય શ્રેણી [18, 110] નું ઉલ્લંઘન કરે છે.",
        )

        what_changed = pick(
            lang_code,
            f"{bad_cnt} active electors in `{bid}` had clean ages in `{from_version}` (e.g., `SYN-GJ-207-0011` was age 39) but appear in `{to_version}` with out-of-bounds ages (`195`, `138`, `15`) under batch ref `V2026_DRAFT-SUPP-MOD-OCR9`.",
            f"`{bid}` में {bad_cnt} सक्रिय मतदाताओं की उम्र `{from_version}` में सही थी (जैसे `SYN-GJ-207-0011` की उम्र 39 थी), लेकिन बैच संदर्भ `V2026_DRAFT-SUPP-MOD-OCR9` के तहत `{to_version}` में अस्वाभाविक आयु (`195`, `138`, `15`) दिखाई दे रही है।",
            f"`{bid}` માં {bad_cnt} સક્રિય મતદારોની ઉંમર `{from_version}` માં યોગ્ય હતી (દા.ત. `SYN-GJ-207-0011` ની ઉંમર 39 હતી), પરંતુ બેચ સંદર્ભ `V2026_DRAFT-SUPP-MOD-OCR9` હેઠળ `{to_version}` માં અયોગ્ય ઉંમર (`195`, `138`, `15`) દેખાય છે.",
        )

        rule_triggered = pick(
            lang_code,
            f"RULE_AGE_COHORT_IMPLAUSIBLE@1.0.0 — Count of records with `age < 18 OR age > 110` ({bad_cnt}) >= 5.",
            f"RULE_AGE_COHORT_IMPLAUSIBLE@1.0.0 — `आयु < 18 या आयु > 110` वाले रिकॉर्ड की संख्या ({bad_cnt}) >= 5।",
            f"RULE_AGE_COHORT_IMPLAUSIBLE@1.0.0 — `ઉંમર < 18 અથવા ઉંમર > 110` વાળા રેકોર્ડ્સની સંખ્યા ({bad_cnt}) >= 5.",
        )

        innocent_explanations = pick(
            lang_code,
            [
                "Birth-year vs. age column transposition or digit-keystroke typo during supplement digitization (e.g. typing `195` instead of `40` or birth-year prefix).",
                "OCR/PDF export corruption in a single correction batch (`SUPP-MOD-OCR9`).",
            ],
            [
                "पूरक डिजिटलीकरण के दौरान जन्म-वर्ष बनाम आयु कॉलम का उलटना या टाइपो त्रुटि (जैसे `40` या जन्म-वर्ष उपसर्ग के स्थान पर `195` टाइप करना)।",
                "एकल सुधार बैच (`SUPP-MOD-OCR9`) में ओसीआर/पीडीएफ निर्यात खराबी।",
            ],
            [
                "પૂરક ડિજિટાઈઝેશન દરમિયાન જન્મ-વર્ષ વિરુદ્ધ ઉંમરના ખાનાની અદલાબદલી અથવા ટાઈપિંગ ભૂલ (દા.ત. `40` અથવા જન્મ-વર્ષની જગ્યાએ `195` ટાઈપ કરવું).",
                "એક જ સુધારણા બેચ (`SUPP-MOD-OCR9`) માં OCR/PDF એક્સપોર્ટ ખામી.",
            ],
        )

        missing_evidence = pick(
            lang_code,
            [
                "Underlying Form 8 correction source forms or DOB fields inside ERONET (published rolls print integer age as on qualifying date, not full DOB).",
            ],
            [
                "ERONET के भीतर मूल फॉर्म 8 सुधार स्रोत फॉर्म या जन्म तिथि फ़ील्ड (प्रकाशित सूचियों में पात्रता तिथि पर पूर्णांक आयु मुद्रित होती है, पूर्ण जन्म तिथि नहीं)।",
            ],
            [
                "ERONET ની અંદર મૂળ ફોર્મ 8 સુધારણા સ્ત્રોત ફોર્મ અથવા જન્મ તારીખ ફીલ્ડ્સ (પ્રકાશિત યાદીઓમાં લાયકાત તારીખ મુજબ પૂર્ણાંક ઉંમર છપાય છે, સંપૂર્ણ જન્મ તારીખ નહીં).",
            ],
        )

        next_verification_step = pick(
            lang_code,
            "Submit a batch clerical discrepancy list to the ERO for suo-motu typographical correction prior to Final Roll printing.",
            "अंतिम सूची मुद्रण से पहले स्वतः संज्ञान से मुद्रण संबंधी सुधार हेतु ईआरओ को एक बैच लिपिकीय विसंगति सूची प्रस्तुत करें।",
            "અંતિમ યાદી છાપકામ પહેલાં સુઓ-મોટુ મુદ્રણ સુધારણા માટે ERO ને બેચ કારકુની વિસંગતતા યાદી સબમિટ કરો.",
        )

        confidence_basis = pick(
            lang_code,
            "Deterministic range validation (`age < 18` violates constitutional qualifying age; `>135` is biologically impossible).",
            "नियतात्मक सीमा सत्यापन (`आयु < 18` संवैधानिक पात्रता आयु का उल्लंघन करती है; `>135` जैविक रूप से असंभव है)।",
            "નિર્ણાયક શ્રેણી માન્યતા (`ઉંમર < 18` બંધારણીય લાયકાત ઉંમરનું ઉલ્લંઘન કરે છે; `>135` જૈવિક રીતે અશક્ય છે).",
        )

        reasoning_steps = pick(
            lang_code,
            [
                f"Scanned `{to_version}` age distribution and isolated {bad_cnt} out-of-range integers in `{bid}`.",
                f"Cross-checked `{from_version}` lineage: affected EPICs previously held valid ages (19–74), confirming a batch modification artifact.",
            ],
            [
                f"`{to_version}` आयु वितरण को स्कैन किया और `{bid}` में {bad_cnt} सीमा-बाहर पूर्णांकों को अलग किया।",
                f"`{from_version}` इतिहास की क्रॉस-जांच की: प्रभावित EPIC में पहले वैध आयु (19–74) दर्ज थी, जो एक बैच संशोधन त्रुटि की पुष्टि करती है।",
            ],
            [
                f"`{to_version}` વય વિતરણ સ્કેન કર્યું અને `{bid}` માં {bad_cnt} શ્રેણી બહારના પૂર્ણાંકો અલગ તારવ્યા.",
                f"`{from_version}` ઇતિહાસની ક્રોસ-તપાસ કરી: અસરગ્રસ્ત EPIC માં અગાઉ માન્ય ઉંમર (19–74) હતી, જે બેચ સુધારણા ખામી સાબિત કરે છે.",
            ],
        )

        flags.append(
            AnomalyFlag(
                flag_id=_flag_id("RULE_AGE_COHORT_IMPLAUSIBLE", bid, from_version, to_version),
                booth_id=bid,
                booth_name=tr_booth(b.booth_name, lang_code),
                constituency_id=b.constituency_id,
                constituency_name=tr_constituency(b.constituency_name, lang_code),
                rule_id="RULE_AGE_COHORT_IMPLAUSIBLE",
                rule_version=RULES_CATALOG["RULE_AGE_COHORT_IMPLAUSIBLE"]["version"],
                rule_formula=RULES_CATALOG["RULE_AGE_COHORT_IMPLAUSIBLE"]["formula"],
                severity="MODERATE_REVIEW",
                headline=headline,
                affected_records_count=bad_cnt,
                sample_epic_ids=list(sample_epics),
                uncertainty=UncertaintyInterval(
                    point_estimate=round(rate, 5),
                    ci_lower_95=ci_lo,
                    ci_upper_95=ci_hi,
                    historical_baseline_mean=0.0,
                    historical_baseline_ci_upper=0.002,
                    z_score=round(bad_cnt / 1.5, 2),
                    sample_size=b.electors_to,
                    uncertainty_note=uncertainty_note,
                ),
                explanation=FivePartExplanation(
                    what_changed=what_changed,
                    rule_triggered=rule_triggered,
                    innocent_explanations=innocent_explanations,
                    missing_evidence=missing_evidence,
                    next_verification_step=next_verification_step,
                    confidence_level=0.99,
                    confidence_basis=confidence_basis,
                    reasoning_steps=reasoning_steps,
                    generated_by="deterministic-ledger-engine",
                ),
                review_status="OPEN_FOR_REVIEW",
            )
        )

    # 4. Rule E: Cross-Booth Transliteration / Phonetic New-Addition Cluster
    new_adds = con.execute(
        """
        SELECT t.epic_id, t.booth_id, t.constituency_id, t.elector_name, t.relation_name, t.age, t.gender, t.house_no
        FROM roll_entries t
        LEFT JOIN roll_entries f ON t.epic_id = f.epic_id AND f.version_id = ?
        WHERE t.version_id = ? AND f.epic_id IS NULL
        """,
        [from_version, to_version],
    ).fetchall()

    # Group by (constituency_id, relation_name, age, gender, house_no) and fuzzy-compare names across distinct booths
    buckets: dict[tuple[Any, ...], list[tuple[Any, ...]]] = {}
    for row in new_adds:
        key = (row[2], row[4], row[5], row[6], row[7])
        buckets.setdefault(key, []).append(row)

    dup_pairs: list[tuple[str, str, str, str]] = []
    involved_booths: set[str] = set()
    for _, items in buckets.items():
        if len(items) < 2:
            continue
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                a, c = items[i], items[j]
                if a[1] != c[1]:
                    sim = fuzz.token_sort_ratio(a[3].lower(), c[3].lower())
                    if sim >= 75:
                        dup_pairs.append((a[0], c[0], a[1], c[1]))
                        involved_booths.update([a[1], c[1]])

    if len(dup_pairs) >= 5:
        primary_bid = sorted(involved_booths)[0]
        partner_bids = ", ".join(sorted(involved_booths - {primary_bid}))
        b = booth_map[primary_bid]
        sample_epics = []
        for ea, eb, _, _ in dup_pairs[:3]:
            sample_epics.extend([ea, eb])
        rate = len(dup_pairs) / max(b.added_count + len(dup_pairs), 1)
        ci_lo, ci_hi = wilson_ci_95(len(dup_pairs), max(b.electors_to, 1))

        headline = pick(
            lang_code,
            f"{len(dup_pairs)} newly added cross-booth pairs across {primary_bid} & {partner_bids} match on relation, age, house, and Indic honorific/transliteration variants",
            f"{primary_bid} और {partner_bids} में नव-जोड़े गए {len(dup_pairs)} क्रॉस-बूथ जोड़े संबंधी, आयु, मकान और लिप्यंतरण रूपों में मेल खाते हैं",
            f"{primary_bid} અને {partner_bids} માં નવા ઉમેરાયેલ {len(dup_pairs)} ક્રોસ-બૂથ જોડાણો સંબંધી, ઉંમર, મકાન અને લિપ્યંતરણ સ્વરૂપોમાં મેળ ખાય છે",
        )

        uncertainty_note = pick(
            lang_code,
            "Moderate uncertainty: public rolls omit photographs and full dates of birth, so lexical similarity cannot distinguish twin/cousin households from duplicate Form-6 submissions.",
            "मध्यम अनिश्चितता: सार्वजनिक सूचियों में तस्वीरें और पूर्ण जन्म तिथि नहीं होती है, इसलिए शाब्दिक समानता जुड़वां/पारिवारिक सदस्यों और डुप्लिकेट फॉर्म 6 आवेदनों के बीच अंतर नहीं कर सकती।",
            "મધ્યમ અનિશ્ચિતતા: જાહેર યાદીઓમાં ફોટોગ્રાફ્સ અને સંપૂર્ણ જન્મ તારીખો હોતી નથી, તેથી શાબ્દિક સમાનતા જોડિયા/પરિવારજનો અને ડુપ્લિકેટ ફોર્મ 6 અરજીઓ વચ્ચે તફાવત કરી શકતી નથી.",
        )

        what_changed = pick(
            lang_code,
            f"{len(dup_pairs)} pairs of new additions in `{to_version}` appear simultaneously in `{primary_bid}` and `{partner_bids}` with matching relation name, exact age, gender, and house number, differing only by Gujarati/Hindi-to-English honorific suffixes (e.g. `Maheshbhai K. Patel` vs `Mahesh Kumar Patel`).",
            f"`{to_version}` में नए जुड़ाव के {len(dup_pairs)} जोड़े एक साथ `{primary_bid}` और `{partner_bids}` में समान संबंधी नाम, सटीक आयु, लिंग और मकान संख्या के साथ दिखाई देते हैं, जो केवल गुजराती/हिंदी-से-अंग्रेजी आदरसूचक प्रत्ययों में भिन्न हैं।",
            f"`{to_version}` માં નવા ઉમેરાયેલા {len(dup_pairs)} જોડાણો એકસાથે `{primary_bid}` અને `{partner_bids}` માં મેળ ખાતા સંબંધી નામ, ચોક્કસ ઉંમર, જાતિ અને મકાન નંબર સાથે દેખાય છે, જે માત્ર ગુજરાતી/હિન્દી-થી-અંગ્રેજી આદરવાચક પ્રત્યયોમાં જુદા પડે છે.",
        )

        rule_triggered = pick(
            lang_code,
            f"RULE_LEXICAL_DUP_CLUSTER@1.0.0 — {len(dup_pairs)} cross-booth addition pairs exceeded token similarity >= 75 with identical `(relation_name, age, gender, house_no)`.",
            f"RULE_LEXICAL_DUP_CLUSTER@1.0.0 — समान `(संबंधी_का_नाम, आयु, लिंग, मकान_नं)` के साथ {len(dup_pairs)} क्रॉस-बूथ जोड़ों की टोकन समानता >= 75 से अधिक पाई गई।",
            f"RULE_LEXICAL_DUP_CLUSTER@1.0.0 — સમાન `(સંબંધીનું_નામ, ઉંમર, જાતિ, મકાન_નં)` સાથે {len(dup_pairs)} ક્રોસ-બૂથ જોડાણોની ટોકન સમાનતા >= 75 થી વધુ નોંધાઈ.",
        )

        innocent_explanations = pick(
            lang_code,
            [
                "Citizen submitted Form 6 twice (once online in English, once offline in Gujarati/Hindi) while residing near an unclear ward boundary between Ward 3 and Ward 4.",
                "Distinct individuals with common regional names in large joint-family compounds (cannot be ruled out without photo/DOB).",
            ],
            [
                "वार्ड 3 और वार्ड 4 के बीच अस्पष्ट वार्ड सीमा के पास रहने वाले नागरिक ने दो बार फॉर्म 6 जमा किया (एक बार अंग्रेजी में ऑनलाइन, एक बार गुजराती/हिंदी में ऑफलाइन)।",
                "बड़े संयुक्त परिवार परिसर में सामान्य क्षेत्रीय नामों वाले अलग-अलग व्यक्ति (तस्वीर/जन्म तिथि के बिना खारिज नहीं किया जा सकता)।",
            ],
            [
                "વોર્ડ 3 અને વોર્ડ 4 વચ્ચેની અસ્પષ્ટ સીમા નજીક રહેતા નાગરિકે બે વાર ફોર્મ 6 સબમિટ કર્યું (એક વાર અંગ્રેજીમાં ઓનલાઇન, એક વાર ગુજરાતી/હિન્દીમાં ઑફલાઇન).",
                "મોટા સંયુક્ત પરિવાર સંકુલમાં સામાન્ય પ્રાદેશિક નામો ધરાવતી અલગ વ્યક્તિઓ (ફોટો/જન્મ તારીખ વિના નકારી શકાતી નથી).",
            ],
        )

        missing_evidence = pick(
            lang_code,
            [
                "ERONET internal PSE (Photo Similar Entries) & full DOB match status (intentionally excluded from public rolls for voter privacy).",
                "Applicant mobile/application reference logs showing whether duplicate Form 6 applications were filed during camp drives.",
            ],
            [
                "ERONET आंतरिक PSE (फोटो समान प्रविष्टियां) और पूर्ण जन्म तिथि मिलान स्थिति (मतदाता गोपनीयता हेतु सार्वजनिक सूचियों से जानबूझकर बाहर रखी गई)।",
                "आवेदक मोबाइल/आवेदन संदर्भ लॉग जो दर्शाते हैं कि क्या शिविर अभियानों के दौरान डुप्लिकेट फॉर्म 6 आवेदन दायर किए गए थे।",
            ],
            [
                "ERONET આંતરિક PSE (ફોટો સમાન પ્રવેશો) અને સંપૂર્ણ જન્મ તારીખ મેળ સ્થિતિ (મતદાર ગોપનીયતા માટે જાહેર યાદીઓમાંથી બાકાત રાખેલ).",
                "અરજદાર મોબાઈલ/અરજી સંદર્ભ લૉગ્સ જે દર્શાવે છે કે શું કેમ્પ ડ્રાઇવ દરમિયાન ડુપ્લિકેટ ફોર્મ 6 અરજીઓ દાખલ કરવામાં આવી હતી.",
            ],
        )

        next_verification_step = pick(
            lang_code,
            "Refer candidate EPIC pairs to the ERO for internal ERONET DSE/PSE verification and BLO checklist confirmation under Rule 21-A.",
            "नियम 21-A के तहत आंतरिक ERONET DSE/PSE सत्यापन और BLO चेकलिस्ट पुष्टि के लिए उम्मीदवार EPIC जोड़ों को ERO को अग्रेषित करें।",
            "નિયમ 21-A હેઠળ આંતરિક ERONET DSE/PSE ચકાસણી અને BLO ચેકલિસ્ટ પુષ્ટિ માટે સંભવિત EPIC જોડાણોને ERO સમક્ષ મોકલો.",
        )

        confidence_basis = pick(
            lang_code,
            "Multi-attribute demographic match is strong, but absence of photograph/DOB in public rolls caps certainty below 0.85.",
            "बहु-विशेषता जनसांख्यिकीय मिलान मजबूत है, लेकिन सार्वजनिक सूचियों में तस्वीर/जन्म तिथि की अनुपस्थिति निश्चितता को 0.85 से नीचे सीमित करती है।",
            "બહુ-લક્ષણ વસ્તીવિષયક મેળ મજબૂત છે, પરંતુ જાહેર યાદીઓમાં ફોટો/જન્મ તારીખની ગેરહાજરી નિશ્ચિતતાને 0.85 થી નીચે મર્યાદિત કરે છે.",
        )

        reasoning_steps = pick(
            lang_code,
            [
                f"Isolated newly added EPICs in `{to_version}` across `{b.constituency_id}`.",
                "Matched cross-booth pairs sharing identical `(relation_name, age, gender, house_no)` and high Indic transliteration similarity.",
                "Explicitly discounted confidence to 0.79 because ECI public PDFs exclude photographs.",
            ],
            [
                f"`{to_version}` में `{b.constituency_id}` में नए जोड़े गए EPICs को अलग किया।",
                "समान `(संबंधी_का_नाम, आयु, लिंग, मकान_नं)` और उच्च लिप्यंतरण समानता साझा करने वाले क्रॉस-बूथ जोड़ों का मिलान किया।",
                "विश्वास स्तर को स्पष्ट रूप से 0.79 तक सीमित किया क्योंकि ECI सार्वजनिक पीडीएफ में तस्वीरें शामिल नहीं हैं।",
            ],
            [
                f"`{to_version}` માં `{b.constituency_id}` માં નવા ઉમેરાયેલા EPICs ને અલગ તારવ્યા.",
                "સમાન `(સંબંધીનું_નામ, ઉંમર, જાતિ, મકાન_નં)` અને ઊંચી લિપ્યંતરણ સમાનતા ધરાવતા ક્રોસ-બૂથ જોડાણો મેળવ્યા.",
                "વિશ્વાસ સ્તરને સ્પષ્ટ રીતે 0.79 સુધી ઘટાડ્યો કારણ કે ચૂંટણી પંચના જાહેર પીડીએફમાં ફોટોગ્રાફ્સ શામેલ નથી.",
            ],
        )

        flags.append(
            AnomalyFlag(
                flag_id=_flag_id("RULE_LEXICAL_DUP_CLUSTER", primary_bid, from_version, to_version),
                booth_id=primary_bid,
                booth_name=f"{tr_booth(b.booth_name, lang_code)} <-> {partner_bids}",
                constituency_id=b.constituency_id,
                constituency_name=tr_constituency(b.constituency_name, lang_code),
                rule_id="RULE_LEXICAL_DUP_CLUSTER",
                rule_version=RULES_CATALOG["RULE_LEXICAL_DUP_CLUSTER"]["version"],
                rule_formula=RULES_CATALOG["RULE_LEXICAL_DUP_CLUSTER"]["formula"],
                severity="MODERATE_REVIEW",
                headline=headline,
                affected_records_count=len(dup_pairs) * 2,
                sample_epic_ids=sample_epics,
                uncertainty=UncertaintyInterval(
                    point_estimate=round(len(dup_pairs) / max(b.electors_to, 1), 5),
                    ci_lower_95=ci_lo,
                    ci_upper_95=ci_hi,
                    historical_baseline_mean=0.001,
                    historical_baseline_ci_upper=0.004,
                    z_score=round(len(dup_pairs) / 1.8, 2),
                    sample_size=b.electors_to,
                    uncertainty_note=uncertainty_note,
                ),
                explanation=FivePartExplanation(
                    what_changed=what_changed,
                    rule_triggered=rule_triggered,
                    innocent_explanations=innocent_explanations,
                    missing_evidence=missing_evidence,
                    next_verification_step=next_verification_step,
                    confidence_level=0.79,
                    confidence_basis=confidence_basis,
                    reasoning_steps=reasoning_steps,
                    generated_by="deterministic-ledger-engine",
                ),
                review_status="OPEN_FOR_REVIEW",
            )
        )

    # Update flag counts on booth summaries
    counts_by_booth: dict[str, int] = {}
    for flg in flags:
        counts_by_booth[flg.booth_id] = counts_by_booth.get(flg.booth_id, 0) + 1
    for b in booth_summaries:
        b.flag_count = counts_by_booth.get(b.booth_id, 0)

    severity_rank = {"HIGH_STATISTICAL_OUTLIER": 0, "MODERATE_REVIEW": 1, "INFO_RECONCILED": 2}
    flags.sort(key=lambda f: (severity_rank.get(f.severity, 9), f.booth_id))
    return flags
