"""Shared localization helpers for PollToll (English / Hindi / Gujarati).

All user-facing text produced by the backend should flow through these helpers so the
frontend can render every word in the citizen's chosen language. Machine identifiers
(EPIC IDs like ``SYN-GJ-109-0042``, booth IDs like ``PS-109``, snapshot version IDs,
SHA-256 hashes, rule IDs and formulas) are intentionally left untouched — they are
data coordinates, not words.

Signed audit receipts and the hash-chained correction log MUST stay in canonical English
(``lang="en"``) so their SHA-256 / Ed25519 signatures remain stable and verifiable.
"""

from __future__ import annotations

from typing import Literal, TypeVar

LanguageCode = Literal["en", "hi", "gu"]
SUPPORTED_LANGUAGES: tuple[LanguageCode, ...] = ("en", "hi", "gu")

T = TypeVar("T")


def normalize_lang(lang: str | None) -> LanguageCode:
    """Coerces an arbitrary query value into a supported language code (default ``en``)."""
    if lang in SUPPORTED_LANGUAGES:
        return lang  # type: ignore[return-value]
    return "en"


def pick(lang: str, en: T, hi: T, gu: T) -> T:
    """Returns the variant matching ``lang``; falls back to English."""
    if lang == "hi":
        return hi
    if lang == "gu":
        return gu
    return en


# ---------------------------------------------------------------------------
# Brand
# ---------------------------------------------------------------------------
BRAND: dict[LanguageCode, str] = {"en": "PollToll", "hi": "पोलटोल", "gu": "પોલટોલ"}


# ---------------------------------------------------------------------------
# Synthetic booth / constituency / section names
# ---------------------------------------------------------------------------
BOOTH_NAMES: dict[str, dict[str, str]] = {
    "Municipal School No. 4, Navrangpura (Synth)": {
        "hi": "नगरपालिका विद्यालय क्र. 4, नवरंगपुरा (सिंथेटिक)",
        "gu": "મ્યુનિસિપલ શાળા નં. 4, નવરંગપુરા (સિન્થેટિક)",
    },
    "University Hostel Block-C Hall (Synth)": {
        "hi": "विश्वविद्यालय छात्रावास ब्लॉक-सी हॉल (सिंथेटिक)",
        "gu": "યુનિવર્સિટી છાત્રાલય બ્લોક-સી હોલ (સિન્થેટિક)",
    },
    "Chandkheda Civic Centre Wing-A (Synth)": {
        "hi": "चांदखेड़ा नागरिक केंद्र विंग-ए (सिंथेटिक)",
        "gu": "ચાંદખેડા નાગરિક કેન્દ્ર વિંગ-એ (સિન્થેટિક)",
    },
    "Chandkheda Civic Centre Wing-B [New Split Booth] (Synth)": {
        "hi": "चांदखेड़ा नागरिक केंद्र विंग-बी [नया विभाजित बूथ] (सिंथेटिक)",
        "gu": "ચાંદખેડા નાગરિક કેન્દ્ર વિંગ-બી [નવું વિભાજિત બૂથ] (સિન્થેટિક)",
    },
    "Paldi Community Library Room-1 (Synth)": {
        "hi": "पालडी सामुदायिक पुस्तकालय कक्ष-1 (सिंथेटिक)",
        "gu": "પાલડી સામુદાયિક પુસ્તકાલય ખંડ-1 (સિન્થેટિક)",
    },
    "Vasna Industrial Estate Primary School (Synth)": {
        "hi": "वासणा औद्योगिक क्षेत्र प्राथमिक विद्यालय (सिंथेटिक)",
        "gu": "વાસણા ઔદ્યોગિક વસાહત પ્રાથમિક શાળા (સિન્થેટિક)",
    },
    "Ambawadi Polytechnic Annex (Synth)": {
        "hi": "आंबावाडी पॉलिटेक्निक उपभवन (सिंथेटिक)",
        "gu": "આંબાવાડી પોલિટેકનિક ઉપભવન (સિન્થેટિક)",
    },
    "Madalpur Ward Office Hall-2 (Synth)": {
        "hi": "मादलपुर वार्ड कार्यालय हॉल-2 (सिंथेटिक)",
        "gu": "માદલપુર વોર્ડ કચેરી હોલ-2 (સિન્થેટિક)",
    },
    "Adajan Riverfront High School (Synth)": {
        "hi": "अडाजण रिवरफ्रंट उच्च विद्यालय (सिंथेटिक)",
        "gu": "અડાજણ રિવરફ્રન્ટ હાઈસ્કૂલ (સિન્થેટિક)",
    },
    "Udhna Sector-7 Nagar Shala (Synth)": {
        "hi": "उधना सेक्टर-7 नगर शाला (सिंथेटिक)",
        "gu": "ઉધના સેક્ટર-7 નગર શાળા (સિન્થેટિક)",
    },
    "Varachha Ward-3 Krushi Bhavan (Synth)": {
        "hi": "वराछा वार्ड-3 कृषि भवन (सिंथेटिक)",
        "gu": "વરાછા વોર્ડ-3 કૃષિ ભવન (સિન્થેટિક)",
    },
    "Varachha Ward-4 Sarvajanik Hall (Synth)": {
        "hi": "वराछा वार्ड-4 सार्वजनिक हॉल (सिंथेटिक)",
        "gu": "વરાછા વોર્ડ-4 સાર્વજનિક હોલ (સિન્થેટિક)",
    },
}

CONSTITUENCY_NAMES: dict[str, dict[str, str]] = {
    "Sabarmati North (Synthetic)": {
        "hi": "साबरमती उत्तर (सिंथेटिक)",
        "gu": "સાબરમતી ઉત્તર (સિન્થેટિક)",
    },
    "Ellisbridge Central (Synthetic)": {
        "hi": "एलिसब्रिज मध्य (सिंथेटिक)",
        "gu": "એલિસબ્રિજ મધ્ય (સિન્થેટિક)",
    },
    "Tapi East Corridor (Synthetic)": {
        "hi": "तापी पूर्व कॉरिडोर (सिंथेटिक)",
        "gu": "તાપી પૂર્વ કોરિડોર (સિન્થેટિક)",
    },
}

SNAPSHOT_LABELS: dict[str, dict[str, str]] = {
    "2024 Final Electoral Roll (Historical Baseline 1)": {
        "hi": "2024 अंतिम मतदाता सूची (ऐतिहासिक आधाररेखा 1)",
        "gu": "2024 અંતિમ મતદાર યાદી (ઐતિહાસિક આધારરેખા 1)",
    },
    "2025 SSR Draft Roll (Historical Baseline 2)": {
        "hi": "2025 विशेष संक्षिप्त पुनरीक्षण प्रारूप सूची (ऐतिहासिक आधाररेखा 2)",
        "gu": "2025 ખાસ સંક્ષિપ્ત સુધારણા મુસદ્દા યાદી (ઐતિહાસિક આધારરેખા 2)",
    },
    "2025 SSR Final Published Roll (Reference Snapshot)": {
        "hi": "2025 विशेष संक्षिप्त पुनरीक्षण अंतिम प्रकाशित सूची (संदर्भ स्नैपशॉट)",
        "gu": "2025 ખાસ સંક્ષિપ્ત સુધારણા અંતિમ પ્રકાશિત યાદી (સંદર્ભ સ્નેપશોટ)",
    },
    "2026 Special Summary Revision Draft + Supplement-1": {
        "hi": "2026 विशेष संक्षिप्त पुनरीक्षण प्रारूप + पूरक-1",
        "gu": "2026 ખાસ સંક્ષિપ્ત સુધારણા મુસદ્દો + પૂરક-1",
    },
}

SECTION_NAMES: dict[str, dict[str, str]] = {
    "Industrial Dormitory Lane": {"hi": "औद्योगिक आवास गली", "gu": "ઔદ્યોગિક આવાસ ગલી"},
}


def tr_booth(name: str | None, lang: str) -> str:
    if not name or lang == "en":
        return name or ""
    # Composite names such as "Wing-A (Synth) <-> PS-306" — translate each known piece.
    if name in BOOTH_NAMES:
        return BOOTH_NAMES[name][lang]
    out = name
    for en_name, tr in BOOTH_NAMES.items():
        if en_name in out:
            out = out.replace(en_name, tr[lang])
    return out


def tr_constituency(name: str | None, lang: str) -> str:
    if not name or lang == "en":
        return name or ""
    return CONSTITUENCY_NAMES.get(name, {}).get(lang, name)


def tr_snapshot_label(label: str | None, lang: str) -> str:
    if not label or lang == "en":
        return label or ""
    return SNAPSHOT_LABELS.get(label, {}).get(lang, label)


def tr_section(name: str | None, lang: str) -> str:
    if not name or lang == "en":
        return name or ""
    if name in SECTION_NAMES:
        return SECTION_NAMES[name][lang]
    if name.startswith("Ward Section "):
        n = name.removeprefix("Ward Section ")
        return pick(lang, name, f"वार्ड खंड {n}", f"વોર્ડ વિભાગ {n}")
    return name


# ---------------------------------------------------------------------------
# Synthetic person names (token-level transliteration)
# ---------------------------------------------------------------------------
_NAME_TOKENS: dict[str, tuple[str, str]] = {
    # token: (hindi, gujarati)
    "Aaravbhai": ("आरवभाई", "આરવભાઈ"),
    "Rameshbhai": ("रमेशभाई", "રમેશભાઈ"),
    "Maheshbhai": ("महेशभाई", "મહેશભાઈ"),
    "Kiran": ("किरण", "કિરણ"),
    "Suresh": ("सुरेश", "સુરેશ"),
    "Devansh": ("देवांश", "દેવાંશ"),
    "Pratik": ("प्रतीक", "પ્રતીક"),
    "Harshil": ("हर्षिल", "હર્ષિલ"),
    "Nilesh": ("नीलेश", "નીલેશ"),
    "Jignesh": ("जिग्नेश", "જીગ્નેશ"),
    "Rajesh": ("राजेश", "રાજેશ"),
    "Vivek": ("विवेक", "વિવેક"),
    "Sanjay": ("संजय", "સંજય"),
    "Irfan": ("इरफ़ान", "ઈરફાન"),
    "Chirag": ("चिराग", "ચિરાગ"),
    "Diya": ("दिया", "દિયા"),
    "Kavita": ("कविता", "કવિતા"),
    "Ushaben": ("उषाबेन", "ઉષાબેન"),
    "Aben": ("उषाबेन", "ઉષાબેન"),
    "Nirali": ("निराली", "નિરાલી"),
    "Meenaben": ("मीनाबेन", "મીનાબેન"),
    "Pooja": ("पूजा", "પૂજા"),
    "Bhavna": ("भावना", "ભાવના"),
    "Kinjal": ("किंजल", "કિંજલ"),
    "Ritu": ("रितु", "રિતુ"),
    "Hetal": ("हेतल", "હેતલ"),
    "Seema": ("सीमा", "સીમા"),
    "Anjali": ("अंजलि", "અંજલિ"),
    "Farida": ("फ़रीदा", "ફરીદા"),
    "Rekhaben": ("रेखाबेन", "રેખાબેન"),
    "Priya": ("प्रिया", "પ્રિયા"),
    "Patel": ("पटेल", "પટેલ"),
    "Shah": ("शाह", "શાહ"),
    "Mehta": ("मेहता", "મહેતા"),
    "Parmar": ("परमार", "પરમાર"),
    "Desai": ("देसाई", "દેસાઈ"),
    "Joshi": ("जोशी", "જોશી"),
    "Solanki": ("सोलंकी", "સોલંકી"),
    "Trivedi": ("त्रिवेदी", "ત્રિવેદી"),
    "Chauhan": ("चौहान", "ચૌહાણ"),
    "Rathod": ("राठौड़", "રાઠોડ"),
    "Panchal": ("पांचाल", "પંચાલ"),
    "Vaghela": ("वाघेला", "વાઘેલા"),
    "Bhatt": ("भट्ट", "ભટ્ટ"),
    "Shaikh": ("शेख", "શેખ"),
    "Karsanbhai": ("करसनभाई", "કરસનભાઈ"),
    "Mahesh": ("महेश", "મહેશ"),
    "Kumar": ("कुमार", "કુમાર"),
    "Niraliben": ("निरालीबेन", "નિરાલીબેન"),
    "Sureshbhai": ("सुरेशभाई", "સુરેશભાઈ"),
    "Jigneshkumar": ("जिग्नेशकुमार", "જીગ્નેશકુમાર"),
    "Dahyabhai": ("दह्याभाई", "દહ્યાભાઈ"),
    "Kinjalben": ("किंजलबेन", "કિંજલબેન"),
    "Rajeshbhai": ("राजेशभाई", "રાજેશભાઈ"),
    "Harshilkumar": ("हर्षिलकुमार", "હર્ષિલકુમાર"),
    "Mukeshbhai": ("मुकेशभाई", "મુકેશભાઈ"),
    "Hetalben": ("हेतलबेन", "હેતલબેન"),
    "Pravin": ("प्रवीण", "પ્રવીણ"),
    "Pravinbhai": ("प्रवीणभाई", "પ્રવીણભાઈ"),
    "Chiragbhai": ("चिरागभाई", "ચિરાગભાઈ"),
    "Vinodbhai": ("विनोदभाई", "વિનોદભાઈ"),
}

_INITIALS: dict[str, tuple[str, str]] = {
    "A": ("ए", "એ"),
    "B": ("बी", "બી"),
    "C": ("सी", "સી"),
    "D": ("डी", "ડી"),
    "H": ("एच", "એચ"),
    "K": ("के", "કે"),
    "M": ("एम", "એમ"),
    "N": ("एन", "એન"),
    "P": ("पी", "પી"),
    "R": ("आर", "આર"),
    "S": ("एस", "એસ"),
    "V": ("वी", "વી"),
}


def _tr_name_token(tok: str, lang: str) -> str:
    idx = 0 if lang == "hi" else 1
    core = tok.rstrip(".,")
    suffix = tok[len(core):]
    key = core[:1].upper() + core[1:].lower() if core else core
    if key in _NAME_TOKENS:
        return _NAME_TOKENS[key][idx] + suffix
    if len(core) == 1 and core.upper() in _INITIALS:
        return _INITIALS[core.upper()][idx] + suffix
    return tok


def tr_person(name: str | None, lang: str) -> str:
    """Transliterates a synthetic elector / relative name token-by-token."""
    if not name or lang == "en":
        return name or ""
    return " ".join(_tr_name_token(t, lang) for t in name.split(" "))


def tr_gender(code: str | None, lang: str) -> str:
    if not code:
        return ""
    labels = {
        "M": ("Male", "पुरुष", "પુરુષ"),
        "F": ("Female", "महिला", "સ્ત્રી"),
        "T": ("Third Gender", "तृतीय लिंग", "તૃતીય જાતિ"),
    }
    if code not in labels:
        return code
    en, hi, gu = labels[code]
    return pick(lang, en, hi, gu)
