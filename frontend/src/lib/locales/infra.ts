import { Dict } from "./common";

export const INFRA_LOCALE: Dict<{
  quotaShieldTitle: string;
  keyPoolLabel: string;
  cacheHitsLabel: string;
  fastpathLabel: string;
  liveCallsLabel: string;
  card1Tag: string;
  card1Title: string;
  card1Desc: string;
  card2Tag: string;
  card2Title: string;
  card2Desc: string;
  card3Tag: string;
  card3Title: string;
  card3Desc: string;
  pipelineTag: string;
  pipelineTitle: string;
  pipelineSubtitle: string;
  idLabel: string;
  baseLabel: string;
  rowsSuffix: string;
  pubLabel: string;
  defaultPubLabel: string;
  csvLabel: string;
  guardrailText: string;
  ingestBtn: string;
  ingestingBtn: string;
  successTitle: string;
  successSha: string;
  successDetails: string;
  cliTitle: string;
  apiTitle: string;
}> = {
  en: {
    quotaShieldTitle:
      "Multi-Cloud Free-Tier Quota Shield (Gemini + Groq LPU + DuckDB Cache)",
    keyPoolLabel: "Key Pool (Gemini / Groq Ready)",
    cacheHitsLabel: "DuckDB Cache Hits Saved",
    fastpathLabel: "Deterministic Fast-Path Saves",
    liveCallsLabel: "Live Calls (Gemini / Groq)",
    card1Tag: "Content-Addressed Store",
    card1Title: "Immutable DuckDB Snapshot Registry",
    card1Desc:
      "Every ingested roll publication is canonically sorted by (booth_id, serial_no, epic_id) and hashed with SHA-256 before indexing.",
    card2Tag: "Air-Gapped / CI Auditor CLI",
    card2Title: "Headless Reproducible Execution",
    card2Desc:
      "Election observers and university labs run polltoll_cli.py locally to reproduce diffs and verify .polltoll-receipt.json bundles without trusting our hosted cloud.",
    card3Tag: "OpenAPI v3.1 Contract-First",
    card3Title: "REST API & Embeddable Civic Endpoints",
    card3Desc:
      "Newsrooms and civic bots integrate /api/v1/audit/diff, /api/v1/verify/claim-check, and /api/v1/assurance/receipts directly into external workflows.",
    pipelineTag: "Live Ingestion Pipeline — POST /api/v1/ingest/snapshot",
    pipelineTitle: "Ingest & Content-Hash a New Synthetic Roll Snapshot",
    pipelineSubtitle:
      "Simulate publishing a post-objection supplement (for example, fixing the age typo on SYN-GJ-207-0011 and resolving a duplicate). PollToll computes the canonical SHA-256 and immediately makes the snapshot available in PollToll Audit.",
    idLabel: "New Snapshot ID (Immutable)",
    baseLabel: "Base Snapshot to Patch",
    rowsSuffix: "rows",
    pubLabel: "Publication Label",
    defaultPubLabel: "2026 SSR Final Release Candidate (Post-Claims Patch)",
    csvLabel:
      "Canonical Supplement CSV Payload (Strictly SYN-* Synthetic IDs Enforced)",
    guardrailText:
      "Guardrail: Non-synthetic EPICs (not prefixed with SYN-) are rejected at ingestion time.",
    ingestBtn: "Ingest Snapshot & Compute SHA-256",
    ingestingBtn: "Hashing & Indexing...",
    successTitle:
      "Snapshot `{id}` Registered & Switched to Active Audit Target!",
    successSha: "Canonical SHA-256: {sha}",
    successDetails:
      "Total Electors: {total} across {booths} booths. Open the PollToll Audit tab to inspect the updated diff!",
    cliTitle: "Headless Auditor CLI (`backend/polltoll_cli.py`)",
    apiTitle: "Programmatic REST API (`shared/openapi.json`)",
  },
  hi: {
    quotaShieldTitle:
      "मल्टी-क्लाउड फ्री-टियर कोटा शील्ड (Gemini + Groq LPU + DuckDB कैश)",
    keyPoolLabel: "कुंजी पूल (Gemini / Groq सक्रिय)",
    cacheHitsLabel: "DuckDB कैश हिट्स द्वारा सुरक्षित",
    fastpathLabel: "नियतात्मक फ़ास्ट-पाथ बचत",
    liveCallsLabel: "लाइव कॉल (Gemini / Groq)",
    card1Tag: "कंटेंट-एड्रेस्ड स्टोर",
    card1Title: "अपरिवर्तनीय DuckDB स्नैपशॉट रजिस्ट्री",
    card1Desc:
      "प्रत्येक इनजेस्ट की गई मतदाता सूची को (booth_id, serial_no, epic_id) द्वारा मानक रूप से क्रमबद्ध किया जाता है और इंडेक्सिंग से पहले SHA-256 द्वारा हैश किया जाता है।",
    card2Tag: "एयर-गैप्ड / CI ऑडिटर CLI",
    card2Title: "हेडलेस पुनरुत्पादक निष्पादन",
    card2Desc:
      "चुनाव पर्यवेक्षक और विश्वविद्यालय प्रयोगशालाएं हमारे होस्टेड क्लाउड पर भरोसा किए बिना स्थानीय रूप से अंतर की जांच और .polltoll-receipt.json के सत्यापन हेतु polltoll_cli.py चलाती हैं।",
    card3Tag: "OpenAPI v3.1 अनुबंध-प्रथम",
    card3Title: "REST API और अंतर्निहित नागरिक एंडपॉइंट",
    card3Desc:
      "समाचार कक्ष और नागरिक बॉट सीधे बाहरी कार्यप्रवाह में /api/v1/audit/diff, /api/v1/verify/claim-check और /api/v1/assurance/receipts को एकीकृत करते हैं।",
    pipelineTag: "लाइव इनजेशन पाइपलाइन — POST /api/v1/ingest/snapshot",
    pipelineTitle: "नया सिंथेटिक मतदाता स्नैपशॉट इनजेस्ट और कंटेंट-हैश करें",
    pipelineSubtitle:
      "दावे-आपत्ति के बाद का पूरक प्रकाशित करने का अनुकरण करें (उदाहरण के लिए, SYN-GJ-207-0011 पर आयु टाइपो को ठीक करना और डुप्लिकेट का समाधान करना)। पोलटोल मानक SHA-256 की गणना करता है और तुरंत स्नैपशॉट को पोलटोल ऑडिट में उपलब्ध कराता है।",
    idLabel: "नया स्नैपशॉट आईडी (अपरिवर्तनीय)",
    baseLabel: "पैच हेतु आधार स्नैपशॉट",
    rowsSuffix: "पंक्तियाँ",
    pubLabel: "प्रकाशन लेबल",
    defaultPubLabel: "2026 SSR अंतिम रिलीज उम्मीदवार (दावा-पश्चात पैच)",
    csvLabel:
      "मानक पूरक CSV पेलोड (केवल SYN-* सिंथेटिक आईडी अनिवार्य)",
    guardrailText:
      "सुरक्षा नियम: गैर-सिंथेटिक EPIC (जो SYN- से शुरू नहीं होते) इनजेशन के समय खारिज कर दिए जाते हैं।",
    ingestBtn: "स्नैपशॉट इनजेस्ट करें और SHA-256 की गणना करें",
    ingestingBtn: "हैशिंग एवं इंडेक्सिंग जारी है...",
    successTitle:
      "स्नैपशॉट `{id}` पंजीकृत हुआ और सक्रिय ऑडिट लक्ष्य में बदला गया!",
    successSha: "मानक SHA-256: {sha}",
    successDetails:
      "कुल मतदाता: {booths} बूथों में {total}। अद्यतन अंतर देखने के लिए पोलटोल ऑडिट टैब खोलें!",
    cliTitle: "हेडलेस ऑडिटर CLI (`backend/polltoll_cli.py`)",
    apiTitle: "प्रोग्रामैटिक REST API (`shared/openapi.json`)",
  },
  gu: {
    quotaShieldTitle:
      "મલ્ટી-ક્લાઉડ ફ્રી-ટાયર ક્વોટા શીલ્ડ (Gemini + Groq LPU + DuckDB કેશ)",
    keyPoolLabel: "કી પૂલ (Gemini / Groq સક્રિય)",
    cacheHitsLabel: "DuckDB કેશ હિટ્સ બચાવ્યા",
    fastpathLabel: "નિર્ણાયક ફાસ્ટ-પાથ બચત",
    liveCallsLabel: "લાઇવ કોલ્સ (Gemini / Groq)",
    card1Tag: "કન્ટેન્ટ-એડ્રેસ્ડ સ્ટોર",
    card1Title: "અપરિવર્તનીય DuckDB સ્નેપશોટ રજિસ્ટ્રી",
    card1Desc:
      "દરેક દાખલ થયેલ યાદી પ્રકાશનને (booth_id, serial_no, epic_id) દ્વારા કેનોનિકલ રીતે સૉર્ટ કરવામાં આવે છે અને અનુક્રમણિકા પહેલાં SHA-256 સાથે હેશ કરવામાં આવે છે.",
    card2Tag: "એર-ગેપ્ડ / CI ઓડિટર CLI",
    card2Title: "હેડલેસ પુનઃઉત્પાદનક્ષમ અમલીકરણ",
    card2Desc:
      "ચૂંટણી નિરીક્ષકો અને યુનિવર્સિટી લેબ્સ અમારા ક્લાઉડ પર આધાર રાખ્યા વિના સ્થાનિક રીતે તફાવતો ચકાસવા અને .polltoll-receipt.json માન્ય કરવા polltoll_cli.py ચલાવે છે.",
    card3Tag: "OpenAPI v3.1 કોન્ટ્રાક્ટ-પ્રથમ",
    card3Title: "REST API અને નાગરિક એન્ડપોઇન્ટ્સ",
    card3Desc:
      "સમાચાર ગૃહો અને નાગરિક બૉટો સીધા બાહ્ય વર્કફ્લોમાં /api/v1/audit/diff, /api/v1/verify/claim-check અને /api/v1/assurance/receipts ને જોડે છે.",
    pipelineTag: "લાઇવ ઇન્જેશન પાઇપલાઇન — POST /api/v1/ingest/snapshot",
    pipelineTitle: "નવો સિન્થેટિક રોલ સ્નેપશોટ ઇન્જેસ્ટ અને કન્ટેન્ટ-હેશ કરો",
    pipelineSubtitle:
      "વાંધા-અરજી પછીની પૂરવણી પ્રકાશિત કરવાનું સિમ્યુલેટ કરો (દાખલા તરીકે, SYN-GJ-207-0011 પર ઉંમરની ટાઇપિંગ ભૂલ સુધારવી અને ડુપ્લિકેટ ઉકેલવું). પોલટોલ કેનોનિકલ SHA-256 ની ગણતરી કરે છે અને તરત જ સ્નેપશોટને પોલટોલ ઓડિટમાં ઉપલબ્ધ બનાવે છે.",
    idLabel: "નવો સ્નેપશોટ ID (અપરિવર્તનીય)",
    baseLabel: "સુધારવા માટે આધાર સ્નેપશોટ",
    rowsSuffix: "હરોળો",
    pubLabel: "પ્રકાશન લેબલ",
    defaultPubLabel: "2026 SSR અંતિમ રીલીઝ ઉમેદવાર (દાવા પછીનો પેચ)",
    csvLabel:
      "કેનોનિકલ પૂરક CSV પેલોડ (માત્ર SYN-* સિન્થેટિક ID ફરજિયાત)",
    guardrailText:
      "સુરક્ષા નિયમ: બિન-સિન્થેટિક EPIC (જે SYN- થી શરૂ થતા નથી) ઇન્જેશન વખતે નકારી કાઢવામાં આવે છે.",
    ingestBtn: "સ્નેપશોટ ઇન્જેસ્ટ કરો અને SHA-256 ગણો",
    ingestingBtn: "હેશિંગ અને ઇન્ડેક્સિંગ થઈ રહ્યું છે...",
    successTitle:
      "સ્નેપશોટ `{id}` રજીસ્ટર થયો અને સક્રિય ઓડિટ ટાર્ગેટ પર સ્વિચ થયો!",
    successSha: "કેનોનિકલ SHA-256: {sha}",
    successDetails:
      "કુલ મતદારો: {booths} બૂથમાં {total}। અપડેટ કરેલ તફાવત તપાસવા પોલટોલ ઓડિટ ટેબ ખોલો!",
    cliTitle: "હેડલેસ ઓડિટર CLI (`backend/polltoll_cli.py`)",
    apiTitle: "પ્રોગ્રામેટિક REST API (`shared/openapi.json`)",
  },
};
