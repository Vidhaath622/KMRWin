import { Dict } from "./common";

export const PAGE_LOCALE: Dict<{
  telemetryProtocol: string;
  telemetryRulePack: string;
  telemetryAttestation: string;
  brandBadge: string;
  tabAudit: string;
  tabAuditSub: string;
  tabAssurance: string;
  tabAssuranceSub: string;
  tabVerify: string;
  tabVerifySub: string;
  tabInfra: string;
  tabInfraSub: string;
  backendErrorWarning: string;
  footerProtocol: string;
  footerDisclaimer: string;
}> = {
  en: {
    telemetryProtocol: "PROTOCOL: ONLINE",
    telemetryRulePack: "RULE_PACK: {pack}",
    telemetryAttestation: "ATTESTATION: Ed25519 + SHA-256",
    brandBadge: "Audit Infrastructure v0.1",
    tabAudit: "PollToll Audit",
    tabAuditSub: "Change Ledger & Baseline Engine",
    tabAssurance: "PollToll Assurance",
    tabAssuranceSub: "Signed Receipts & ERONET Gap",
    tabVerify: "PollToll Verify",
    tabVerifySub: "Citizen Bot & Claim Checker",
    tabInfra: "Infra / API & CLI",
    tabInfraSub: "Snapshot Ingestion & SDKs",
    backendErrorWarning:
      "Backend connection warning ({error}). Ensure FastAPI is running on http://127.0.0.1:8000.",
    footerProtocol:
      "PollToll Independent Electoral Change-Audit Protocol • DuckDB + Wilson 95% CIs + Ed25519 + Gemini 3.8",
    footerDisclaimer:
      "Synthetic Testbed Only (`SYN-GJ-*`) • Built for Independent Observers, Universities & Civic Auditors",
  },
  hi: {
    telemetryProtocol: "प्रोटोकॉल: ऑनलाइन",
    telemetryRulePack: "नियम पैक: {pack}",
    telemetryAttestation: "सत्यापन: Ed25519 + SHA-256",
    brandBadge: "ऑडिट इंफ्रास्ट्रक्चर v0.1",
    tabAudit: "पोलटोल ऑडिट",
    tabAuditSub: "चेंज लेजर और सांख्यिकीय इंजन",
    tabAssurance: "पोलटोल एश्योरेंस",
    tabAssuranceSub: "हस्ताक्षरित रसीद और ERONET विश्लेषण",
    tabVerify: "पोलटोल वेरिफाई",
    tabVerifySub: "नागरिक सहायक और दावा जांच",
    tabInfra: "इंफ्रा / API और CLI",
    tabInfraSub: "स्नैपशॉट इनजेशन और SDK",
    backendErrorWarning:
      "बैकएंड कनेक्शन चेतावनी ({error})। सुनिश्चित करें कि FastAPI http://127.0.0.1:8000 पर चल रहा है।",
    footerProtocol:
      "पोलटोल स्वतंत्र मतदाता सूची परिवर्तन-ऑडिट प्रोटोकॉल • DuckDB + Wilson 95% CIs + Ed25519 + Gemini 3.8",
    footerDisclaimer:
      "केवल सिंथेटिक परीक्षण डेटासेट (`SYN-GJ-*`) • स्वतंत्र पर्यवेक्षकों, विश्वविद्यालयों और नागरिक लेखापरीक्षकों के लिए निर्मित",
  },
  gu: {
    telemetryProtocol: "પ્રોટોકોલ: ઑનલાઇન",
    telemetryRulePack: "નિયમ પેક: {pack}",
    telemetryAttestation: "પ્રમાણીકરણ: Ed25519 + SHA-256",
    brandBadge: "ઓડિટ ઈન્ફ્રાસ્ટ્રક્ચર v0.1",
    tabAudit: "પોલટોલ ઓડિટ",
    tabAuditSub: "ચેન્જ લેજર અને આંકડાકીય એન્જિન",
    tabAssurance: "પોલટોલ એશ્યોરન્સ",
    tabAssuranceSub: "ડિજિટલ રસીદ અને ERONET વિશ્લેષણ",
    tabVerify: "પોલટોલ વેરિફાય",
    tabVerifySub: "નાગરિક સહાયક અને દાવા ચકાસણી",
    tabInfra: "ઇન્ફ્રા / API અને CLI",
    tabInfraSub: "સ્નેપશોટ ઇન્જેશન અને SDK",
    backendErrorWarning:
      "બેકએન્ડ કનેક્શન ચેતવણી ({error})। ખાતરી કરો કે FastAPI http://127.0.0.1:8000 પર ચાલી રહ્યું છે.",
    footerProtocol:
      "પોલટોલ સ્વતંત્ર મતદાર યાદી ફેરફાર-ઓડિટ પ્રોટોકોલ • DuckDB + Wilson 95% CIs + Ed25519 + Gemini 3.8",
    footerDisclaimer:
      "માત્ર સિન્થેટિક ટેસ્ટ ડેટાસેટ (`SYN-GJ-*`) • સ્વતંત્ર નિરીક્ષકો, યુનિવર્સિટીઓ અને નાગરિક ઓડિટર્સ માટે નિર્મિત",
  },
};
