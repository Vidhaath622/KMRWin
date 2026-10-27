import { Dict } from "./common";

export const VERIFY_LOCALE: Dict<{
  publicServiceBadge: string;
  testEpicsLabel: string;
  epicDemoTags: Record<string, string>;
  voiceTranscriptPrefix: string;
  confidencePrefix: string;
  enginePrefix: string;
  timelineTitle: string;
  serialPrefix: string;
  agePrefix: string;
  housePrefix: string;
  officialStepsTitle: string;
  reasoningTraceTitle: string;
  equalStandardsBadge: string;
  claimPlaceholder: string;
  checkingClaimBtn: string;
  verdictHeader: string;
  confidenceLabel: string;
  boothsLabel: string;
  sourceLabel: string;
  basisLabel: string;
  missingLabel: string;
  micPermissionAlert: string;
  voiceCheckDefaultQuery: string;
}> = {
  en: {
    publicServiceBadge: "Free Public Service • English / हिन्दी / ગુજરાતી",
    testEpicsLabel: "Test Synthetic EPICs:",
    epicDemoTags: {
      "SYN-GJ-109-0042": "Booth Split (PS-109 → PS-110)",
      "SYN-GJ-104-0019": "Draft Hostel Deletion",
      "SYN-GJ-207-0011": "Age Typo (39 → 195)",
      "SYN-GJ-201-0008": "Active & Unchanged",
    },
    voiceTranscriptPrefix: "Voice transcript: “{transcript}”",
    confidencePrefix: "Confidence: {pct}%",
    enginePrefix: "Engine: {engine}",
    timelineTitle: "4-Snapshot Longitudinal Roll History ({epic})",
    serialPrefix: "Serial #{sno}",
    agePrefix: "Age: {age}",
    housePrefix: "House: {house}",
    officialStepsTitle: "Official ECI Next Steps",
    reasoningTraceTitle: "Transparent Reasoning Trace",
    equalStandardsBadge: "Equal Standards Across All Sides • Zero Accusations",
    claimPlaceholder:
      "Paste a viral social media allegation about voter additions, deletions, or booth changes...",
    checkingClaimBtn: "Checking Ledger...",
    verdictHeader: "Ledger Assessment Verdict",
    confidenceLabel: "Confidence:",
    boothsLabel: "Booths:",
    sourceLabel: "Source: {src}",
    basisLabel: "Basis: {basis}",
    missingLabel: "Missing: {missing}",
    micPermissionAlert:
      "Microphone permission unavailable in this browser context; please type your query or use the quick EPIC chips.",
    voiceCheckDefaultQuery: "Voice status check",
  },
  hi: {
    publicServiceBadge: "निःशुल्क जनसेवा • English / हिन्दी / ગુજરાતી",
    testEpicsLabel: "परीक्षण सिंथेटिक EPIC:",
    epicDemoTags: {
      "SYN-GJ-109-0042": "बूथ विभाजन (PS-109 → PS-110)",
      "SYN-GJ-104-0019": "ड्राफ्ट छात्रावास नाम विलोपन",
      "SYN-GJ-207-0011": "आयु टाइपो (39 → 195)",
      "SYN-GJ-201-0008": "सक्रिय एवं अपरिवर्तित",
    },
    voiceTranscriptPrefix: "आवाज़ प्रतिलेख: “{transcript}”",
    confidencePrefix: "विश्वास स्तर: {pct}%",
    enginePrefix: "इंजन: {engine}",
    timelineTitle: "4-स्नैपशॉट क्रमिक मतदाता सूची इतिहास ({epic})",
    serialPrefix: "क्रमांक #{sno}",
    agePrefix: "आयु: {age}",
    housePrefix: "मकान: {house}",
    officialStepsTitle: "आधिकारिक ECI अगले कदम",
    reasoningTraceTitle: "पारदर्शी तर्क शृंखला",
    equalStandardsBadge: "सभी पक्षों के लिए समान मानक • कोई आरोप नहीं",
    claimPlaceholder:
      "मतदाता जोड़ने, हटाने या बूथ परिवर्तन के बारे में कोई वायरल सोशल मीडिया दावा यहां पेस्ट करें...",
    checkingClaimBtn: "लेजर की जांच जारी है...",
    verdictHeader: "लेजर मूल्यांकन निष्कर्ष",
    confidenceLabel: "विश्वास स्तर:",
    boothsLabel: "संबंधित बूथ:",
    sourceLabel: "स्रोत: {src}",
    basisLabel: "आधार: {basis}",
    missingLabel: "अनुपलब्ध: {missing}",
    micPermissionAlert:
      "इस ब्राउज़र में माइक्रोफ़ोन की अनुमति उपलब्ध नहीं है; कृपया अपना प्रश्न लिखें या त्वरित EPIC चिप्स का उपयोग करें।",
    voiceCheckDefaultQuery: "आवाज़ द्वारा स्थिति जांच",
  },
  gu: {
    publicServiceBadge: "મફત જાહેર સેવા • English / हिन्दी / ગુજરાતી",
    testEpicsLabel: "પરીક્ષણ સિન્થેટિક EPIC:",
    epicDemoTags: {
      "SYN-GJ-109-0042": "બૂથ વિભાજન (PS-109 → PS-110)",
      "SYN-GJ-104-0019": "મુસદ્દા છાત્રાલય કમી",
      "SYN-GJ-207-0011": "ઉંમર ટાઈપિંગ ભૂલ (39 → 195)",
      "SYN-GJ-201-0008": "સક્રિય અને યથાવત્",
    },
    voiceTranscriptPrefix: "વૉઇસ ટ્રાન્સક્રિપ્ટ: “{transcript}”",
    confidencePrefix: "વિશ્વાસ સ્તર: {pct}%",
    enginePrefix: "એન્જિન: {engine}",
    timelineTitle: "4-સ્નેપશોટ સતત મતદાર યાદી ઇતિહાસ ({epic})",
    serialPrefix: "ક્રમાંક #{sno}",
    agePrefix: "ઉંમર: {age}",
    housePrefix: "મકાન: {house}",
    officialStepsTitle: "સત્તાવાર ચૂંટણી પંચના આગળના પગલાં",
    reasoningTraceTitle: "પારદર્શક તર્ક પગલાં",
    equalStandardsBadge: "તમામ પક્ષો માટે સમાન ધોરણો • કોઈ આક્ષેપ નહીં",
    claimPlaceholder:
      "મતદાર ઉમેરા, કમી કે બૂથ ફેરફાર અંગેનો વાયરલ સોશિયલ મીડિયા દાવો અહીં પેસ્ટ કરો...",
    checkingClaimBtn: "લેજર ચકાસી રહ્યું છે...",
    verdictHeader: "લેજર મૂલ્યાંકન તારણ",
    confidenceLabel: "વિશ્વાસ સ્તર:",
    boothsLabel: "સંદર્ભિત બૂથ:",
    sourceLabel: "સ્ત્રોત: {src}",
    basisLabel: "આધાર: {basis}",
    missingLabel: "ખૂટતી વિગત: {missing}",
    micPermissionAlert:
      "આ બ્રાઉઝરમાં માઇક્રોફોન પરવાનગી ઉપલબ્ધ નથી; કૃપા કરીને તમારો પ્રશ્ન લખો અથવા ઝડપી EPIC ચિપ્સનો ઉપયોગ કરો.",
    voiceCheckDefaultQuery: "વૉઇસ સ્થિતિ તપાસ",
  },
};
