/**
 * Shared localization primitives used by every PollToll plane.
 *
 * Convention: each component owns a dictionary file in `src/lib/locales/<plane>.ts`
 * shaped as `{ en: {...}, hi: {...}, gu: {...} }` where `hi` and `gu` are typed as
 * `typeof en` so TypeScript fails the build if any key is left untranslated.
 *
 * What is intentionally NOT translated (data coordinates, not words):
 *   numbers, EPIC IDs (SYN-GJ-…), booth IDs (PS-109), constituency IDs (AC-041),
 *   snapshot version IDs (v2025_final), SHA-256 hashes, Ed25519 keys/signatures,
 *   rule IDs / formulas, raw signed JSON payloads, shell/curl/code snippets.
 */
import { LanguageCode } from "../types";

export type Dict<T> = Record<LanguageCode, T>;

/** Picks the dictionary for the active language (falls back to English). */
export function getDict<T>(dict: Dict<T>, lang: LanguageCode): T {
  return dict[lang] ?? dict.en;
}

/** Replaces `{name}` placeholders inside a translated template. */
export function fmt(
  template: string,
  vars: Record<string, string | number>
): string {
  return template.replace(/\{(\w+)\}/g, (_, k: string) =>
    vars[k] !== undefined ? String(vars[k]) : `{${k}}`
  );
}

export const BRAND: Dict<string> = {
  en: "PollToll",
  hi: "पोलटोल",
  gu: "પોલટોલ",
};

export const CHANGE_TYPE_LABELS: Dict<Record<string, string>> = {
  en: {
    ALL: "All",
    ADDED: "Added",
    DELETED: "Deleted",
    MODIFIED: "Modified",
    BOOTH_TRANSFERRED: "Booth Transferred",
  },
  hi: {
    ALL: "सभी",
    ADDED: "जोड़ा गया",
    DELETED: "हटाया गया",
    MODIFIED: "संशोधित",
    BOOTH_TRANSFERRED: "बूथ स्थानांतरित",
  },
  gu: {
    ALL: "બધા",
    ADDED: "ઉમેરાયેલ",
    DELETED: "કમી કરાયેલ",
    MODIFIED: "સુધારેલ",
    BOOTH_TRANSFERRED: "બૂથ સ્થળાંતરિત",
  },
};

export const SEVERITY_LABELS: Dict<Record<string, string>> = {
  en: {
    HIGH_STATISTICAL_OUTLIER: "High Statistical Outlier",
    MODERATE_REVIEW: "Moderate — Field Check",
    INFO_RECONCILED: "Reconciled Booth Split",
  },
  hi: {
    HIGH_STATISTICAL_OUTLIER: "उच्च सांख्यिकीय विचलन",
    MODERATE_REVIEW: "मध्यम — क्षेत्रीय जांच",
    INFO_RECONCILED: "मिलान किया गया बूथ विभाजन",
  },
  gu: {
    HIGH_STATISTICAL_OUTLIER: "ઉચ્ચ આંકડાકીય વિચલન",
    MODERATE_REVIEW: "મધ્યમ — સ્થળ તપાસ",
    INFO_RECONCILED: "મેળવેલ બૂથ વિભાજન",
  },
};

export const REVIEW_STATUS_LABELS: Dict<Record<string, string>> = {
  en: {
    OPEN_FOR_REVIEW: "Open for Review",
    ANNOTATED_BY_REVIEWER: "Annotated by Reviewer",
    RECONCILED_BOUNDARY_SHIFT: "Reconciled Boundary Shift",
  },
  hi: {
    OPEN_FOR_REVIEW: "समीक्षा हेतु खुला",
    ANNOTATED_BY_REVIEWER: "समीक्षक द्वारा टिप्पणी की गई",
    RECONCILED_BOUNDARY_SHIFT: "मिलान की गई सीमा परिवर्तन",
  },
  gu: {
    OPEN_FOR_REVIEW: "સમીક્ષા માટે ખુલ્લું",
    ANNOTATED_BY_REVIEWER: "સમીક્ષક દ્વારા નોંધ કરાયેલ",
    RECONCILED_BOUNDARY_SHIFT: "મેળવેલ સીમા ફેરફાર",
  },
};

export const CORRECTION_ACTION_LABELS: Dict<Record<string, string>> = {
  en: {
    FLAG_LOGGED: "Flag Logged",
    EVIDENCE_NOTE_ADDED: "Evidence Note Added",
    MARKED_EXPLAINED_ADMIN_SHIFT: "Explained by Administrative Order",
    ESCALATED_FOR_FIELD_CHECK: "Escalated for Field Check",
  },
  hi: {
    FLAG_LOGGED: "फ्लैग दर्ज",
    EVIDENCE_NOTE_ADDED: "साक्ष्य टिप्पणी जोड़ी गई",
    MARKED_EXPLAINED_ADMIN_SHIFT: "प्रशासनिक आदेश द्वारा स्पष्ट",
    ESCALATED_FOR_FIELD_CHECK: "क्षेत्रीय जांच हेतु अग्रेषित",
  },
  gu: {
    FLAG_LOGGED: "ફ્લેગ નોંધાયો",
    EVIDENCE_NOTE_ADDED: "પુરાવા નોંધ ઉમેરાઈ",
    MARKED_EXPLAINED_ADMIN_SHIFT: "વહીવટી આદેશ દ્વારા સ્પષ્ટ",
    ESCALATED_FOR_FIELD_CHECK: "સ્થળ તપાસ માટે આગળ મોકલ્યું",
  },
};

export const ROLL_TYPE_LABELS: Dict<Record<string, string>> = {
  en: {
    DRAFT: "Draft",
    FINAL: "Final",
    SUPPLEMENT_CONSOLIDATED: "Supplement (Consolidated)",
  },
  hi: {
    DRAFT: "प्रारूप",
    FINAL: "अंतिम",
    SUPPLEMENT_CONSOLIDATED: "पूरक (समेकित)",
  },
  gu: {
    DRAFT: "મુસદ્દો",
    FINAL: "અંતિમ",
    SUPPLEMENT_CONSOLIDATED: "પૂરક (સંકલિત)",
  },
};

export const CITIZEN_STATUS_LABELS: Dict<Record<string, string>> = {
  en: {
    ACTIVE_UNCHANGED: "Active — Unchanged",
    ACTIVE_MODIFIED: "Active — Modified",
    ACTIVE_BOOTH_TRANSFERRED: "Active — Booth Transferred",
    DELETED_IN_DRAFT_SUPPLEMENT: "Deleted in Draft Supplement",
    NOT_FOUND: "Not Found",
  },
  hi: {
    ACTIVE_UNCHANGED: "सक्रिय — अपरिवर्तित",
    ACTIVE_MODIFIED: "सक्रिय — संशोधित",
    ACTIVE_BOOTH_TRANSFERRED: "सक्रिय — बूथ स्थानांतरित",
    DELETED_IN_DRAFT_SUPPLEMENT: "प्रारूप पूरक में हटाया गया",
    NOT_FOUND: "नहीं मिला",
  },
  gu: {
    ACTIVE_UNCHANGED: "સક્રિય — યથાવત્",
    ACTIVE_MODIFIED: "સક્રિય — સુધારેલ",
    ACTIVE_BOOTH_TRANSFERRED: "સક્રિય — બૂથ સ્થળાંતરિત",
    DELETED_IN_DRAFT_SUPPLEMENT: "મુસદ્દા પૂરકમાં કમી કરાયેલ",
    NOT_FOUND: "મળ્યું નથી",
  },
};

export const REASON_CODE_LABELS: Dict<Record<string, string>> = {
  en: {
    A_FORM6: "Form-6 New Inclusion",
    M_ADDR: "Address Correction",
    M_CORR: "Entry Correction",
    T_BOOTH_SPLIT: "Booth Split Transfer",
  },
  hi: {
    A_FORM6: "फॉर्म-6 नया समावेश",
    M_ADDR: "पता सुधार",
    M_CORR: "प्रविष्टि सुधार",
    T_BOOTH_SPLIT: "बूथ विभाजन स्थानांतरण",
  },
  gu: {
    A_FORM6: "ફોર્મ-6 નવો સમાવેશ",
    M_ADDR: "સરનામા સુધારો",
    M_CORR: "એન્ટ્રી સુધારો",
    T_BOOTH_SPLIT: "બૂથ વિભાજન સ્થળાંતર",
  },
};

/** Labels for roll-record field names (ledger modified_fields keys, citizen history keys). */
export const FIELD_LABELS: Dict<Record<string, string>> = {
  en: {
    version_id: "Version",
    snapshot_label: "Snapshot",
    publication_date: "Publication Date",
    epic_id: "EPIC",
    elector_name: "Elector Name",
    relation_name: "Relative Name",
    gender: "Gender",
    age: "Age",
    house_no: "House No.",
    section_name: "Section",
    booth_id: "Booth",
    booth_name: "Booth Name",
    serial_no: "Serial No.",
    constituency_id: "Constituency",
    constituency_name: "Constituency Name",
    reason_code: "Reason Code",
    supplement_ref: "Supplement Reference",
    status: "Status",
  },
  hi: {
    version_id: "संस्करण",
    snapshot_label: "स्नैपशॉट",
    publication_date: "प्रकाशन तिथि",
    epic_id: "मतदाता पहचान क्र.",
    elector_name: "मतदाता का नाम",
    relation_name: "संबंधी का नाम",
    gender: "लिंग",
    age: "आयु",
    house_no: "मकान क्र.",
    section_name: "खंड",
    booth_id: "बूथ",
    booth_name: "बूथ का नाम",
    serial_no: "क्रमांक",
    constituency_id: "निर्वाचन क्षेत्र",
    constituency_name: "निर्वाचन क्षेत्र का नाम",
    reason_code: "कारण कोड",
    supplement_ref: "पूरक संदर्भ",
    status: "स्थिति",
  },
  gu: {
    version_id: "આવૃત્તિ",
    snapshot_label: "સ્નેપશોટ",
    publication_date: "પ્રકાશન તારીખ",
    epic_id: "મતદાર ઓળખ નં.",
    elector_name: "મતદારનું નામ",
    relation_name: "સંબંધીનું નામ",
    gender: "જાતિ",
    age: "ઉંમર",
    house_no: "મકાન નં.",
    section_name: "વિભાગ",
    booth_id: "બૂથ",
    booth_name: "બૂથનું નામ",
    serial_no: "ક્રમ નં.",
    constituency_id: "મતવિસ્તાર",
    constituency_name: "મતવિસ્તારનું નામ",
    reason_code: "કારણ કોડ",
    supplement_ref: "પૂરક સંદર્ભ",
    status: "સ્થિતિ",
  },
};

export const GENDER_LABELS: Dict<Record<string, string>> = {
  en: { M: "Male", F: "Female", T: "Third Gender" },
  hi: { M: "पुरुष", F: "महिला", T: "तृतीय लिंग" },
  gu: { M: "પુરુષ", F: "સ્ત્રી", T: "તૃતીય જાતિ" },
};

/** Looks up an enum label, falling back to a humanised version of the raw code. */
export function enumLabel(
  map: Dict<Record<string, string>>,
  lang: LanguageCode,
  code: string | null | undefined
): string {
  if (!code) return "";
  return map[lang]?.[code] ?? map.en[code] ?? code.replaceAll("_", " ");
}
