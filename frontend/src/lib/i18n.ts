import { LanguageCode } from "./types";

export const UI_STRINGS: Record<
  LanguageCode,
  {
    tagline: string;
    guardrailBanner: string;
    tabAudit: string;
    tabAuditSub: string;
    tabVerify: string;
    tabVerifySub: string;
    tabAssurance: string;
    tabAssuranceSub: string;
    citizenTitle: string;
    citizenSubtitle: string;
    epicPlaceholder: string;
    questionPlaceholder: string;
    askButton: string;
    speakButton: string;
    stopRecording: string;
    listenButton: string;
    claimTitle: string;
    claimSubtitle: string;
    checkClaimBtn: string;
    verifiedCol: string;
    disputedCol: string;
    unprovableCol: string;
  }
> = {
  en: {
    tagline: "Independent Electoral Change-Audit & Public Verification Protocol",
    guardrailBanner:
      "100% Synthetic Roll Dataset • Political Neutrality Enforced • Statistical Flags Require Human Review (Never Proof of Fraud)",
    tabAudit: "PollToll Audit",
    tabAuditSub: "Change Ledger & Baseline Engine",
    tabVerify: "PollToll Verify",
    tabVerifySub: "Citizen Bot & Claim Checker",
    tabAssurance: "PollToll Assurance",
    tabAssuranceSub: "Signed Receipts & ERONET Gap",
    citizenTitle: "Multilingual Citizen Roll-Change Assistant",
    citizenSubtitle:
      "Check how a synthetic EPIC ID changed across 2024–2026 published snapshots in English, Hindi, or Gujarati (Text & Voice).",
    epicPlaceholder: "Synthetic EPIC (e.g. SYN-GJ-109-0042)",
    questionPlaceholder:
      "Ask a question or speak (e.g. 'Is my voter ID SYN-GJ-109-0042 safe?')",
    askButton: "Check & Explain",
    speakButton: "Voice Query",
    stopRecording: "Stop & Transcribe",
    listenButton: "Listen Aloud",
    claimTitle: "Ledger-Grounded Viral Claim Checker",
    claimSubtitle:
      "Evaluates viral allegations strictly against deterministic snapshot math—separating verified counts, disputed framing, and missing non-public evidence.",
    checkClaimBtn: "Audit Viral Claim",
    verifiedCol: "Verified by Published Roll Math",
    disputedCol: "Disputed / Overstated Framing",
    unprovableCol: "Cannot Be Proven from Public Data",
  },
  hi: {
    tagline: "स्वतंत्र मतदाता सूची परिवर्तन-ऑडिट एवं सार्वजनिक सत्यापन प्रोटोकॉल",
    guardrailBanner:
      "100% सिंथेटिक मतदाता डेटासेट • पूर्ण राजनीतिक निष्पक्षता • सांख्यिकीय फ्लैग केवल मानवीय समीक्षा हेतु हैं (धोखाधड़ी का प्रमाण नहीं)",
    tabAudit: "PollToll ऑडिट",
    tabAuditSub: "चेंज लेजर और सांख्यिकीय इंजन",
    tabVerify: "PollToll वेरिफाई",
    tabVerifySub: "नागरिक सहायक और दावा जांच",
    tabAssurance: "PollToll एश्योरेंस",
    tabAssuranceSub: "हस्ताक्षरित रसीद और ERONET विश्लेषण",
    citizenTitle: "बहुभाषी नागरिक मतदाता-सूची सहायक (टेक्स्ट और वॉइस)",
    citizenSubtitle:
      "अंग्रेजी, हिंदी या गुजराती में 2024–2026 के प्रकाशित स्नैपशॉट में अपने सिंथेटिक EPIC नंबर की स्थिति और अगले कदम जानें।",
    epicPlaceholder: "सिंथेटिक EPIC (जैसे SYN-GJ-109-0042)",
    questionPlaceholder:
      "अपना प्रश्न लिखें या बोलें (जैसे 'क्या मेरा नाम SYN-GJ-109-0042 सुरक्षित है?')",
    askButton: "स्थिति जांचें",
    speakButton: "बोलकर पूछें",
    stopRecording: "रुकें और भेजें",
    listenButton: "उत्तर सुनें",
    claimTitle: "वायरल दावा जांचकर्ता (Claim Checker)",
    claimSubtitle:
      "वायरल आरोपों की गणितीय लेजर से निष्पक्ष जांच—सत्यापित आंकड़े, खंडित दावे और अनुपलब्ध साक्ष्य अलग-अलग देखें।",
    checkClaimBtn: "दावे की जांच करें",
    verifiedCol: "प्रकाशित डेटा से सत्यापित तथ्य",
    disputedCol: "खंडित या अतिरंजित व्याख्या",
    unprovableCol: "सार्वजनिक डेटा से असिद्ध (अनुपलब्ध साक्ष्य)",
  },
  gu: {
    tagline: "સ્વતંત્ર મતદાર યાદી ફેરફાર-ઓડિટ અને જાહેર ચકાસણી પ્રોટોકોલ",
    guardrailBanner:
      "100% સિન્થેટિક મતદાર ડેટાસેટ • સંપૂર્ણ રાજકીય નિષ્પક્ષતા • આંકડાકીય ફ્લેગ માત્ર માનવીય સમીક્ષા માટે છે (છેતરપિંડીનો પુરાવો નથી)",
    tabAudit: "PollToll ઓડિટ",
    tabAuditSub: "ચેન્જ લેજર અને આંકડાકીય એન્જિન",
    tabVerify: "PollToll વેરિફાય",
    tabVerifySub: "નાગરિક સહાયક અને દાવા ચકાસણી",
    tabAssurance: "PollToll એશ્યોરન્સ",
    tabAssuranceSub: "ડિજિટલ રસીદ અને ERONET વિશ્લેષણ",
    citizenTitle: "બહુભાષી નાગરિક મતદાર-યાદી સહાયક (ટેક્સ્ટ અને વૉઇસ)",
    citizenSubtitle:
      "અંગ્રેજી, હિન્દી અથવા ગુજરાતીમાં 2024–2026 ની પ્રકાશિત યાદીઓમાં સિન્થેટિક EPIC નંબરની સ્થિતિ અને આગળના પગલાં જાણો.",
    epicPlaceholder: "સિન્થેટિક EPIC (દા.ત. SYN-GJ-109-0042)",
    questionPlaceholder:
      "પ્રશ્ન લખો અથવા બોલો (દા.ત. 'મારું નામ SYN-GJ-109-0042 સુરક્ષિત છે?')",
    askButton: "સ્થિતિ તપાસો",
    speakButton: "બોલીને પૂછો",
    stopRecording: "રોકો અને મોકલો",
    listenButton: "જવાબ સાંભળો",
    claimTitle: "વાયરલ દાવા ચકાસણી (Claim Checker)",
    claimSubtitle:
      "વાયરલ આક્ષેપોની લેજર ગણિત સાથે નિષ્પક્ષ ચકાસણી—ચકાસાયેલ આંકડા, ખંડિત અર્થઘટન અને ખૂટતા પુરાવા અલગ જુઓ.",
    checkClaimBtn: "દાવાની ચકાસણી કરો",
    verifiedCol: "પ્રકાશિત યાદીથી ચકાસાયેલ હકીકત",
    disputedCol: "ખંડિત અથવા અતિશયોક્તિપૂર્ણ અર્થઘટન",
    unprovableCol: "જાહેર ડેટા પરથી સાબિત ન થઈ શકે તેવું",
  },
};

export const PRESET_CLAIMS: Record<LanguageCode, { label: string; claim: string }[]> = {
  en: [
    {
      label: "Booth 109 '340 Vanished Voters' Rumor",
      claim:
        "340 voters were secretly wiped out overnight from Booth PS-109 before the election!",
    },
    {
      label: "Booth 302 Deletion Spike Allegation",
      claim:
        "Booth PS-302 suffered an abnormal deletion spike far above past revision cycles, proving targeted removal.",
    },
    {
      label: "House H-42/B '64 Fake Voters' Post",
      claim:
        "64 voters registered at single address H-42/B in Booth PS-203 proves fake voter roll stuffing!",
    },
  ],
  hi: [
    {
      label: "बूथ 109 से '340 मतदाता गायब' अफवाह",
      claim: "चुनाव से पहले बूथ PS-109 से रातों-रात 340 मतदाताओं के नाम गायब कर दिए गए!",
    },
    {
      label: "बूथ 302 में असामान्य नाम विलोपन दावा",
      claim: "बूथ PS-302 में पिछले वर्षों की तुलना में असामान्य रूप से अधिक नाम काटे गए हैं।",
    },
    {
      label: "मकान H-42/B में '64 फर्जी वोटर' दावा",
      claim: "बूथ PS-203 के एक ही मकान H-42/B में 64 मतदाता दर्ज होना फर्जी वोटिंग का सबूत है!",
    },
  ],
  gu: [
    {
      label: "બૂથ 109 માંથી '340 મતદારો ગાયબ' અફવા",
      claim: "ચૂંટણી પહેલા બૂથ PS-109 માંથી રાતોરાત 340 મતદારોના નામ ગાયબ કરી દેવામાં આવ્યા!",
    },
    {
      label: "બૂથ 302 માં અસામાન્ય નામ કમી અંગેનો દાવો",
      claim: "બૂથ PS-302 માં અગાઉના વર્ષો કરતા ઘણા વધારે નામ કમી થયા છે.",
    },
    {
      label: "મકાન H-42/B માં '64 બોગસ મતદારો' પોસ્ટ",
      claim: "બૂથ PS-203 ના એક જ મકાન H-42/B માં 64 મતદારો નોંધાયા તે બોગસ વોટિંગનો પુરાવો છે!",
    },
  ],
};
