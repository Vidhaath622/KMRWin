import { Dict } from "./common";

export const ASSURANCE_LOCALE: Dict<{
  receiptTag: string;
  receiptTitle: string;
  receiptSubtitle: string;
  reIssueBtn: string;
  reIssuingBtn: string;
  tamperBtn: string;
  restoreBtn: string;
  downloadBtn: string;
  printBtn: string;
  verifiedBanner: string;
  tamperBanner: string;
  receiptMeta: string;
  algPrefix: string;
  chk1Canonical: string;
  chk2Sha256: string;
  chk3Ed25519: string;
  chk4HashChain: string;
  passText: string;
  failText: string;
  pubKeyLabel: string;
  payloadDigestLabel: string;
  sigLabel: string;
  chainTitle: string;
  onFlagBy: string;
  prevHash: string;
  eventHash: string;
  gapTag: string;
  gapTitle: string;
  gapSubtitle: string;
  colCapability: string;
  colEronetStatus: string;
  colEpistemicLimit: string;
  colAuditGap: string;
  colPolltollWedge: string;
  prototypeWedgeBadge: string;
}> = {
  en: {
    receiptTag: "Zero-Trust Cryptographic Audit Receipts (Ed25519 + SHA-256)",
    receiptTitle:
      "Client-Side Browser Verification & Append-Only Correction History",
    receiptSubtitle:
      'Outside reviewers verify dataset hashes, rule-pack versions, and reviewer annotations directly via the browser\'s window.crypto.subtle.verify("Ed25519", ...) without trusting PollToll\'s server.',
    reIssueBtn: "Re-Issue Signed Receipt",
    reIssuingBtn: "Signing...",
    tamperBtn: "Simulate 1-Byte Tamper Attack",
    restoreBtn: "Restore Authentic Receipt",
    downloadBtn: "Download .receipt.json",
    printBtn: "Print Audit Report",
    verifiedBanner: "CRYPTOGRAPHICALLY VERIFIED IN BROWSER ({engine})",
    tamperBanner:
      "TAMPER DETECTED — RECEIPT SIGNATURE & DIGEST REJECTED BY BROWSER",
    receiptMeta: "Receipt ID: {id} • Issued: {date}",
    algPrefix: "Alg: {alg}",
    chk1Canonical: "1. Canonical JSON Match",
    chk2Sha256: "2. WebCrypto SHA-256 Digest",
    chk3Ed25519: "3. SubtleCrypto Ed25519 Sig",
    chk4HashChain: "4. Hash-Chained Review Log",
    passText: "PASS",
    failText: "FAIL",
    pubKeyLabel: "Ed25519 Public Key (Hex):",
    payloadDigestLabel: "Signed Payload SHA-256:",
    sigLabel: "Ed25519 Signature (64-Byte Hex):",
    chainTitle:
      "Immutable Hash-Chained Correction & Review History ({count} Events)",
    onFlagBy: "on {flagId} by {role}",
    prevHash: "prev: {hash}...",
    eventHash: "hash: {hash}...",
    gapTag: "Epistemic Validation — Feature-by-Feature ERONET Gap Matrix",
    gapTitle: "Why PollToll Complements Rather Than Rebuilds ECI's ERONET",
    gapSubtitle:
      "Public ECI documentation confirms ERONET's national registration and internal DSE/PSE deduplication capabilities, while cannot-disprove boundaries are disclosed transparently. PollToll targets external change-auditing over published snapshots.",
    colCapability: "Capability",
    colEronetStatus: "Publicly Documented in ERONET / ECI?",
    colEpistemicLimit: "Epistemic Boundary (Internal Unknowns)",
    colAuditGap: "External / Third-Party Audit Gap",
    colPolltollWedge: "PollToll Infrastructure Wedge",
    prototypeWedgeBadge: "Active Prototype Wedge",
  },
  hi: {
    receiptTag: "जीरो-ट्रस्ट क्रिप्टोग्राफिक ऑडिट रसीदें (Ed25519 + SHA-256)",
    receiptTitle: "क्लाइंट-साइड ब्राउज़र सत्यापन एवं केवल-जोड़ने-योग्य समीक्षा इतिहास",
    receiptSubtitle:
      'बाहरी समीक्षक पोलटोल के सर्वर पर भरोसा किए बिना सीधे ब्राउज़र के window.crypto.subtle.verify("Ed25519", ...) के माध्यम से डेटासेट हैश, नियम पैक और समीक्षक टिप्पणियों का सत्यापन करते हैं।',
    reIssueBtn: "हस्ताक्षरित रसीद पुनः जारी करें",
    reIssuingBtn: "हस्ताक्षर जारी है...",
    tamperBtn: "1-बाइट छेड़छाड़ का अनुकरण करें",
    restoreBtn: "प्रामाणिक रसीद बहाल करें",
    downloadBtn: ".receipt.json डाउनलोड करें",
    printBtn: "ऑडिट रिपोर्ट प्रिंट करें",
    verifiedBanner: "ब्राउज़र में क्रिप्टोग्राफिक रूप से सत्यापित ({engine})",
    tamperBanner: "छेड़छाड़ पकड़ी गई — रसीद हस्ताक्षर एवं डाइजेस्ट ब्राउज़र द्वारा अस्वीकृत",
    receiptMeta: "रसीद आईडी: {id} • जारी: {date}",
    algPrefix: "एल्गोरिदम: {alg}",
    chk1Canonical: "1. मानक JSON मिलान",
    chk2Sha256: "2. WebCrypto SHA-256 डाइजेस्ट",
    chk3Ed25519: "3. SubtleCrypto Ed25519 हस्ताक्षर",
    chk4HashChain: "4. हैश-श्रृंखलाबद्ध समीक्षा लॉग",
    passText: "उत्तीर्ण (PASS)",
    failText: "विफल (FAIL)",
    pubKeyLabel: "Ed25519 सार्वजनिक कुंजी (Hex):",
    payloadDigestLabel: "हस्ताक्षरित पेलोड SHA-256:",
    sigLabel: "Ed25519 डिजिटल हस्ताक्षर (64-बाइट Hex):",
    chainTitle:
      "अपरिवर्तनीय हैश-श्रृंखलाबद्ध सुधार एवं समीक्षा इतिहास ({count} घटनाएं)",
    onFlagBy: "{flagId} पर {role} द्वारा",
    prevHash: "पूर्व हैश: {hash}...",
    eventHash: "वर्तमान हैश: {hash}...",
    gapTag: "ज्ञानमीमांसा सत्यापन — ERONET तुलनात्मक विश्लेषण मैट्रिक्स",
    gapTitle: "पोलटोल ECI के ERONET का विकल्प नहीं, बल्कि पूरक क्यों है",
    gapSubtitle:
      "सार्वजनिक ECI दस्तावेज ERONET के राष्ट्रीय पंजीकरण और आंतरिक DSE/PSE मिलान क्षमताओं की पुष्टि करते हैं। पोलटोल केवल प्रकाशित स्नैपशॉट के बाहरी परिवर्तन-ऑडिट पर केंद्रित है।",
    colCapability: "कार्यक्षमता",
    colEronetStatus: "क्या ERONET / ECI में सार्वजनिक रूप से प्रलेखित है?",
    colEpistemicLimit: "ज्ञानमीमांसा सीमा (आंतरिक अज्ञात)",
    colAuditGap: "बाहरी / तृतीय-पक्ष ऑडिट अंतर",
    colPolltollWedge: "पोलटोल इंफ्रास्ट्रक्चर समाधान",
    prototypeWedgeBadge: "सक्रिय प्रोटोटाइप समाधान",
  },
  gu: {
    receiptTag: "ઝીરો-ટ્રસ્ટ ક્રિપ્ટોગ્રાફિક ઓડિટ રસીદો (Ed25519 + SHA-256)",
    receiptTitle: "ક્લાયન્ટ-સાઇડ બ્રાઉઝર ચકાસણી અને માત્ર-ઉમેરાય-તેવો સમીક્ષા ઇતિહાસ",
    receiptSubtitle:
      'બહારના સમીક્ષકો પોલટોલના સર્વર પર વિશ્વાસ કર્યા વિના સીધા બ્રાઉઝરના window.crypto.subtle.verify("Ed25519", ...) દ્વારા ડેટાસેટ હેશ, નિયમ આવૃત્તિઓ અને સમીક્ષક નોંધો ચકાસે છે.',
    reIssueBtn: "સહીવાળી રસીદ ફરીથી મેળવો",
    reIssuingBtn: "સહી થઈ રહી છે...",
    tamperBtn: "1-બાઇટ છેડછાડ સિમ્યુલેટ કરો",
    restoreBtn: "અસલી રસીદ પુનઃસ્થાપિત કરો",
    downloadBtn: ".receipt.json ડાઉનલોડ કરો",
    printBtn: "ઓડિટ રિપોર્ટ પ્રિન્ટ કરો",
    verifiedBanner: "બ્રાઉઝરમાં ક્રિપ્ટોગ્રાફિક રીતે ચકાસાયેલ ({engine})",
    tamperBanner: "છેડછાડ પકડાઈ — રસીદની સહી અને ડાયજેસ્ટ બ્રાઉઝરે નકારી કાઢ્યા",
    receiptMeta: "રસીદ ID: {id} • જારી તારીખ: {date}",
    algPrefix: "એલ્ગોરિધમ: {alg}",
    chk1Canonical: "1. કેનોનિકલ JSON મેળ",
    chk2Sha256: "2. WebCrypto SHA-256 ડાયજેસ્ટ",
    chk3Ed25519: "3. SubtleCrypto Ed25519 સહી",
    chk4HashChain: "4. હેશ-સાંકળિત સમીક્ષા લોગ",
    passText: "સફળ (PASS)",
    failText: "નિષ્ફળ (FAIL)",
    pubKeyLabel: "Ed25519 જાહેર કી (Hex):",
    payloadDigestLabel: "સહી થયેલ પેલોડ SHA-256:",
    sigLabel: "Ed25519 ડિજિટલ સહી (64-બાઈટ Hex):",
    chainTitle:
      "અપરિવર્તનીય હેશ-સાંકળિત સુધારણા અને સમીક્ષા ઇતિહાસ ({count} ઘટનાઓ)",
    onFlagBy: "{flagId} પર {role} દ્વારા",
    prevHash: "અગાઉનો હેશ: {hash}...",
    eventHash: "હાલનો હેશ: {hash}...",
    gapTag: "તુલનાત્મક વિશ્લેષણ — ERONET વિગતવાર મેટ્રિક્સ",
    gapTitle: "પોલટોલ શા માટે ચૂંટણી પંચના ERONET નો વિકલ્પ નથી પણ પૂરક છે",
    gapSubtitle:
      "ચૂંટણી પંચના જાહેર દસ્તાવેજો ERONET ના રાષ્ટ્રીય નોંધણી અને આંતરિક DSE/PSE ક્ષમતાઓની પુષ્ટિ કરે છે. પોલટોલ માત્ર પ્રકાશિત સ્નેપશોટના બાહ્ય ફેરફાર-ઓડિટ પર લક્ષ્ય રાખે છે.",
    colCapability: "ક્ષમતા",
    colEronetStatus: "શું ERONET / ECI માં જાહેરમાં દસ્તાવેજીકૃત છે?",
    colEpistemicLimit: "જ્ઞાનમર્યાદા (આંતરિક અજ્ઞાત બાબતો)",
    colAuditGap: "બાહ્ય / તૃતીય-પક્ષ ઓડિટ તફાવત",
    colPolltollWedge: "પોલટોલ ઈન્ફ્રાસ્ટ્રક્ચર સોલ્યુશન",
    prototypeWedgeBadge: "સક્રિય પ્રોટોટાઇપ સોલ્યુશન",
  },
};
