import { Dict } from "./common";

export const AUDIT_LOCALE: Dict<{
  diffTitle: string;
  diffSubtitle: string;
  refRollLabel: string;
  targetRollLabel: string;
  loadingLedger: string;
  kpiRefElectors: string;
  kpiInTarget: string;
  kpiAdditions: string;
  kpiAdditionsSub: string;
  kpiDeletions: string;
  kpiDeletionsSub: string;
  kpiSplits: string;
  kpiSplitsSub: string;
  kpiModifications: string;
  kpiModificationsSub: string;
  kpiRules: string;
  kpiRulesSub: string;
  chart1Title: string;
  chart1Sub: string;
  chart1Raw: string;
  chart1Net: string;
  chart1Baseline: string;
  chart2Title: string;
  chart2Sub: string;
  chart2Added: string;
  chart2Transferred: string;
  chart2Modified: string;
  chart2Deleted: string;
  queueTitle: string;
  queueSub: string;
  affectedRecords: string;
  confidence: string;
  statusLabel: string;
  flagIdPrefix: string;
  uncertaintyHeader: string;
  sampleSize: string;
  observedMetric: string;
  wilsonCI: string;
  baselineHistorical: string;
  zScoreDeviation: string;
  sec1Title: string;
  traceSampleEpics: string;
  inspectCitizenTooltip: string;
  sec2Title: string;
  sec3Title: string;
  sec4Title: string;
  sec5Title: string;
  confidenceCalibration: string;
  formTitle: string;
  formRolePlaceholder: string;
  formActionEvidence: string;
  formActionExplained: string;
  formActionEscalate: string;
  formNotePlaceholder: string;
  formRefPlaceholder: string;
  formNotice: string;
  formSubmitBtn: string;
  formSubmittingBtn: string;
  formSuccessAppended: string;
  formErrorFailed: string;
  tableTitle: string;
  tableSub: string;
  colLedgerId: string;
  colEpic: string;
  colElector: string;
  colClassification: string;
  colLineage: string;
  colDelta: string;
  colSupplementRef: string;
  ageDeltaText: string;
}> = {
  en: {
    diffTitle: "Electoral Change Ledger — Deterministic Snapshot Diff",
    diffSubtitle:
      "Compares published roll versions row-by-row, reconciles cross-booth transfers, and tests net rates against 2024–2025 historical baselines.",
    refRollLabel: "Reference Roll (From)",
    targetRollLabel: "Target Roll (To)",
    loadingLedger:
      "Computing deterministic DuckDB Electoral Change Ledger & 95% Wilson uncertainty bounds...",
    kpiRefElectors: "Reference Electors",
    kpiInTarget: "→ {count} in target",
    kpiAdditions: "Additions (+)",
    kpiAdditionsSub: "Form-6 & supplement inclusions",
    kpiDeletions: "True Net Deletions (-)",
    kpiDeletionsSub: "Absent across entire roll",
    kpiSplits: "Reconciled Booth Splits",
    kpiSplitsSub: "Active EPICs moved PS-109 → PS-110",
    kpiModifications: "Field Modifications (Δ)",
    kpiModificationsSub: "Address, spelling, or age edits",
    kpiRules: "Triggered Audit Rules",
    kpiRulesSub: "With 95% CIs & missing-evidence list",
    chart1Title:
      "Raw Booth Outflow vs. Reconciled Net Deletion Rate & Historical Baseline (%)",
    chart1Sub:
      "Notice PS-109: 36.2% raw drop collapses to 0.21% net deletion once 338 transfers to PS-110 are reconciled—whereas PS-104 & PS-302 exceed historical baselines even at 95% confidence bounds.",
    chart1Raw: "Raw Outflow %",
    chart1Net: "True Net Deletion %",
    chart1Baseline: "2024–25 Historical Baseline %",
    chart2Title: "Booth-Wise Electoral Change Ledger Breakdown (Record Counts)",
    chart2Sub:
      "Traceable decomposition into Additions, Cross-Booth Transfers, Modifications, and Net Deletions.",
    chart2Added: "Added",
    chart2Transferred: "Transferred (Split)",
    chart2Modified: "Modified",
    chart2Deleted: "Net Deleted",
    queueTitle: "Statistical & Ledger Review Queue ({count})",
    queueSub: "Select flag to inspect 5-part brief",
    affectedRecords: "Affected: {count} records",
    confidence: "Confidence: {pct}%",
    statusLabel: "Status: ",
    flagIdPrefix: "Flag ID: ",
    uncertaintyHeader: "Statistical Baseline & Uncertainty Disclosure",
    sampleSize: "Sample Size n = {n}",
    observedMetric: "Observed Metric",
    wilsonCI: "95% Wilson CI",
    baselineHistorical: "2024–25 Baseline",
    zScoreDeviation: "Z-Score Deviation",
    sec1Title: "1. What Changed (Ledger Evidence)",
    traceSampleEpics: "Trace sample EPICs:",
    inspectCitizenTooltip: "Inspect longitudinal citizen record",
    sec2Title: "2. Exact Deterministic Rule Triggered",
    sec3Title: "3. Innocent / Administrative Explanations",
    sec4Title: "4. Missing Evidence (Not in Public PDFs)",
    sec5Title: "5. Next Non-Partisan Verification Step",
    confidenceCalibration: "Confidence Calibration ({pct}%):",
    formTitle: "Append Reviewer Finding to Hash-Chained Audit Log",
    formRolePlaceholder: "Reviewer role / org",
    formActionEvidence: "Attach Documentary Note",
    formActionExplained: "Mark Explained by Admin Order",
    formActionEscalate: "Request Authorized BLO/ERO Check",
    formNotePlaceholder:
      "Enter factual verification note (min 5 chars, never overwrites original flag)...",
    formRefPlaceholder: "Doc ref (e.g. Gazette #14)",
    formNotice:
      "Appends SHA-256 hash-linked entry included in signed PollToll Assurance receipts.",
    formSubmitBtn: "Append to Ledger",
    formSubmittingBtn: "Logging...",
    formSuccessAppended: "Appended immutable event {id} (SHA-256: {hash}...)",
    formErrorFailed: "Failed to log note: {error}",
    tableTitle: "Source-Linked Electoral Change Ledger Records",
    tableSub:
      "Every row links to exact Reference & Target snapshot SHA-256s, polling station part, serial number, and supplement batch.",
    colLedgerId: "Ledger ID",
    colEpic: "Synthetic EPIC",
    colElector: "Elector (Synth)",
    colClassification: "Change Classification",
    colLineage: "Booth / Serial Lineage",
    colDelta: "Field Delta",
    colSupplementRef: "Supplement Source Ref",
    ageDeltaText: "age {before}→{after}",
  },
  hi: {
    diffTitle: "मतदाता परिवर्तन लेजर — नियतात्मक स्नैपशॉट अंतर",
    diffSubtitle:
      "प्रकाशित मतदाता सूची के संस्करणों की पंक्ति-दर-पंक्ति तुलना, बूथ स्थानांतरण का मिलान और 2024–2025 की ऐतिहासिक आधाररेखा के विरुद्ध शुद्ध दरों का परीक्षण।",
    refRollLabel: "संदर्भ सूची (प्रारंभिक)",
    targetRollLabel: "लक्षित सूची (अंतिम)",
    loadingLedger:
      "नियतात्मक DuckDB मतदाता परिवर्तन लेजर एवं 95% विल्सन अनिश्चितता सीमाओं की गणना जारी है...",
    kpiRefElectors: "संदर्भ मतदाता",
    kpiInTarget: "→ लक्ष्य सूची में {count}",
    kpiAdditions: "नए जुड़ाव (+)",
    kpiAdditionsSub: "फॉर्म-6 एवं पूरक समावेश",
    kpiDeletions: "वास्तविक शुद्ध विलोपन (-)",
    kpiDeletionsSub: "पूरी सूची से अनुपस्थित",
    kpiSplits: "समाधानित बूथ विभाजन",
    kpiSplitsSub: "सक्रिय EPIC PS-109 से PS-110 में स्थानांतरित",
    kpiModifications: "फ़ील्ड संशोधन (Δ)",
    kpiModificationsSub: "पता, वर्तनी या आयु सुधार",
    kpiRules: "सक्रिय ऑडिट नियम",
    kpiRulesSub: "95% विश्वास अंतराल और साक्ष्य सूची सहित",
    chart1Title:
      "सकल बूथ बहिर्वाह बनाम समाधानित शुद्ध विलोपन दर एवं ऐतिहासिक आधाररेखा (%)",
    chart1Sub:
      "ध्यान दें PS-109: 36.2% का सकल बहाव PS-110 में 338 स्थानांतरणों के मिलान के बाद मात्र 0.21% शुद्ध विलोपन रह जाता है—जबकि PS-104 और PS-302 आधाररेखा से काफी ऊपर हैं।",
    chart1Raw: "सकल बहिर्वाह %",
    chart1Net: "वास्तविक शुद्ध विलोपन %",
    chart1Baseline: "2024–25 ऐतिहासिक आधाररेखा %",
    chart2Title: "बूथ-वार मतदाता परिवर्तन लेजर विवरण (रिकॉर्ड संख्या)",
    chart2Sub:
      "नए जुड़ाव, क्रॉस-बूथ स्थानांतरण, संशोधन और शुद्ध विलोपन में सत्यापन योग्य विभाजन।",
    chart2Added: "जोड़ा गया",
    chart2Transferred: "स्थानांतरित (विभाजित)",
    chart2Modified: "संशोधित",
    chart2Deleted: "शुद्ध विलोपित",
    queueTitle: "सांख्यिकीय एवं लेजर समीक्षा कतार ({count})",
    queueSub: "5-भाग का विवरण देखने के लिए फ्लैग चुनें",
    affectedRecords: "प्रभावित: {count} रिकॉर्ड",
    confidence: "विश्वास स्तर: {pct}%",
    statusLabel: "स्थिति: ",
    flagIdPrefix: "फ्लैग आईडी: ",
    uncertaintyHeader: "सांख्यिकीय आधाररेखा एवं अनिश्चितता प्रकटीकरण",
    sampleSize: "नमूना आकार n = {n}",
    observedMetric: "देखा गया मान",
    wilsonCI: "95% विल्सन विश्वास अंतराल",
    baselineHistorical: "2024–25 आधाररेखा",
    zScoreDeviation: "Z-स्कोर विचलन",
    sec1Title: "1. क्या बदला (लेजर साक्ष्य)",
    traceSampleEpics: "नमूना EPIC देखें:",
    inspectCitizenTooltip: "नागरिक का पूर्ण स्नैपशॉट इतिहास देखें",
    sec2Title: "2. सक्रिय हुआ सटीक नियतात्मक नियम",
    sec3Title: "3. निर्दोष / प्रशासनिक व्याख्याएं",
    sec4Title: "4. अनुपलब्ध साक्ष्य (सार्वजनिक पीडीएफ में नहीं)",
    sec5Title: "5. अगला गैर-पक्षपातपूर्ण सत्यापन कदम",
    confidenceCalibration: "विश्वास अंशांकन ({pct}%):",
    formTitle: "हैश-श्रृंखलाबद्ध ऑडिट लॉग में समीक्षक टिप्पणी जोड़ें",
    formRolePlaceholder: "समीक्षक भूमिका / संस्था",
    formActionEvidence: "दस्तावेजी टिप्पणी संलग्न करें",
    formActionExplained: "प्रशासनिक आदेश द्वारा स्पष्ट चिह्नित करें",
    formActionEscalate: "अधिकृत BLO/ERO जांच का अनुरोध करें",
    formNotePlaceholder:
      "तथ्यात्मक सत्यापन टिप्पणी दर्ज करें (न्यूनतम 5 अक्षर, मूल फ्लैग कभी नहीं मिटेगा)...",
    formRefPlaceholder: "दस्तावेज़ संदर्भ (उदा. राजपत्र #14)",
    formNotice:
      "SHA-256 हैश-लिंक्ड प्रविष्टि जोड़ता है जो हस्ताक्षरित पोलटोल एश्योरेंस रसीद में शामिल होती है।",
    formSubmitBtn: "लेजर में जोड़ें",
    formSubmittingBtn: "दर्ज किया जा रहा है...",
    formSuccessAppended: "अपरिवर्तनीय घटना {id} जोड़ी गई (SHA-256: {hash}...)",
    formErrorFailed: "टिप्पणी दर्ज करने में विफल: {error}",
    tableTitle: "स्रोत-संबद्ध मतदाता परिवर्तन लेजर रिकॉर्ड",
    tableSub:
      "प्रत्येक पंक्ति सटीक संदर्भ और लक्ष्य स्नैपशॉट SHA-256, मतदान केंद्र भाग, क्रमांक और पूरक बैच से जुड़ी है।",
    colLedgerId: "लेजर आईडी",
    colEpic: "सिंथेटिक EPIC",
    colElector: "मतदाता (सिंथेटिक)",
    colClassification: "परिवर्तन वर्गीकरण",
    colLineage: "बूथ / क्रमांक वंशावली",
    colDelta: "फ़ील्ड अंतर",
    colSupplementRef: "पूरक स्रोत संदर्भ",
    ageDeltaText: "आयु {before}→{after}",
  },
  gu: {
    diffTitle: "મતદાર ફેરફાર લેજર — નિર્ણાયક સ્નેપશોટ તફાવત",
    diffSubtitle:
      "પ્રકાશિત મતદાર યાદી આવૃત્તિઓની ક્રમબદ્ધ સરખામણી, બૂથ સ્થળાંતરનું સમાધાન અને 2024–2025 ઐતિહાસિક આધારરેખા સામે ચોખ્ખા દરોનું પરીક્ષણ.",
    refRollLabel: "સંદર્ભ યાદી (પ્રારંભિક)",
    targetRollLabel: "લક્ષ્ય યાદી (અંતિમ)",
    loadingLedger:
      "નિર્ણાયક DuckDB મતદાર ફેરફાર લેજર અને 95% વિલ્સન અનિશ્ચિતતા મર્યાદાઓની ગણતરી ચાલુ છે...",
    kpiRefElectors: "સંદર્ભ મતદારો",
    kpiInTarget: "→ લક્ષ્ય યાદીમાં {count}",
    kpiAdditions: "નવા ઉમેરા (+)",
    kpiAdditionsSub: "ફોર્મ-6 અને પૂરક સમાવેશ",
    kpiDeletions: "વાસ્તવિક ચોખ્ખી કમી (-)",
    kpiDeletionsSub: "સમગ્ર યાદીમાંથી ગેરહાજર",
    kpiSplits: "મેળવેલ બૂથ વિભાજન",
    kpiSplitsSub: "સક્રિય EPIC PS-109 થી PS-110 માં સ્થળાંતરિત",
    kpiModifications: "વિગત સુધારણા (Δ)",
    kpiModificationsSub: "સરનામું, જોડણી અથવા ઉંમર સુધારો",
    kpiRules: "સક્રિય ઓડિટ નિયમો",
    kpiRulesSub: "95% વિશ્વાસ મર્યાદા અને પુરાવા યાદી સાથે",
    chart1Title:
      "કુલ બૂથ ઘટાડો વિરુદ્ધ સમાધાન થયેલ ચોખ્ખો કમી દર અને ઐતિહાસિક આધારરેખા (%)",
    chart1Sub:
      "ધ્યાન આપો PS-109: PS-110 માં 338 સ્થળાંતરો મેળવ્યા પછી 36.2% નો ઘટાડો ઘટીને માત્ર 0.21% ચોખ્ખી કમી રહે છે—જ્યારે PS-104 અને PS-302 આધારરેખા કરતાં ઘણા વધારે છે.",
    chart1Raw: "કુલ ઘટાડો %",
    chart1Net: "વાસ્તવિક ચોખ્ખી કમી %",
    chart1Baseline: "2024–25 ઐતિહાસિક આધારરેખા %",
    chart2Title: "બૂથ-વાર મતદાર ફેરફાર લેજર વિગતો (રેકોર્ડ સંખ્યા)",
    chart2Sub:
      "નવા ઉમેરા, ક્રોસ-બૂથ સ્થળાંતર, સુધારણા અને ચોખ્ખી કમીમાં ચકાસણી યોગ્ય વિભાજન.",
    chart2Added: "ઉમેરાયેલ",
    chart2Transferred: "સ્થળાંતરિત (વિભાજિત)",
    chart2Modified: "સુધારેલ",
    chart2Deleted: "ચોખ્ખી કમી",
    queueTitle: "આંકડાકીય અને લેજર સમીક્ષા કતાર ({count})",
    queueSub: "5-ભાગની વિગત તપાસવા ફ્લેગ પસંદ કરો",
    affectedRecords: "અસરગ્રસ્ત: {count} રેકોર્ડ્સ",
    confidence: "વિશ્વાસ સ્તર: {pct}%",
    statusLabel: "સ્થિતિ: ",
    flagIdPrefix: "ફ્લેગ ID: ",
    uncertaintyHeader: "આંકડાકીય આધારરેખા અને અનિશ્ચિતતા જાહેરાત",
    sampleSize: "નમૂના કદ n = {n}",
    observedMetric: "જોવાયેલ મૂલ્ય",
    wilsonCI: "95% વિલ્સન કોન્ફિડન્સ ઇન્ટરવલ",
    baselineHistorical: "2024–25 આધારરેખા",
    zScoreDeviation: "Z-સ્કોર વિચલન",
    sec1Title: "1. શું બદલાયું (લેજર પુરાવા)",
    traceSampleEpics: "નમૂનારૂપ EPIC તપાસો:",
    inspectCitizenTooltip: "નાગરિકનો સંપૂર્ણ ઇતિહાસ જુઓ",
    sec2Title: "2. લાગુ થયેલ ચોક્કસ નિર્ણાયક નિયમ",
    sec3Title: "3. નિર્દોષ / વહીવટી સમજૂતીઓ",
    sec4Title: "4. ખૂટતા પુરાવા (જાહેર પીડીએફમાં નથી)",
    sec5Title: "5. આગળનું તટસ્થ ચકાસણી પગલું",
    confidenceCalibration: "વિશ્વાસ માપાંકન ({pct}%):",
    formTitle: "હેશ-સાંકળિત ઓડિટ લોગમાં સમીક્ષક તારણ ઉમેરો",
    formRolePlaceholder: "સમીક્ષકની ભૂમિકા / સંસ્થા",
    formActionEvidence: "દસ્તાવેજી નોંધ જોડો",
    formActionExplained: "વહીવટી આદેશ દ્વારા સ્પષ્ટ ચિહ્નિત કરો",
    formActionEscalate: "અધિકૃત BLO/ERO તપાસની વિનંતી કરો",
    formNotePlaceholder:
      "હકીકતલક્ષી ચકાસણી નોંધ દાખલ કરો (ઓછામાં ઓછા 5 અક્ષર, મૂળ ફ્લેગ ક્યારેય લખાશે નહીં)...",
    formRefPlaceholder: "દસ્તાવેજ સંદર્ભ (દા.ત. ગેઝેટ #14)",
    formNotice:
      "SHA-256 હેશ-લિંક્ડ એન્ટ્રી ઉમેરે છે જે હસ્તાક્ષરિત પોલટોલ એશ્યોરન્સ રસીદમાં સામેલ થાય છે.",
    formSubmitBtn: "લેજરમાં ઉમેરો",
    formSubmittingBtn: "નોંધાઈ રહ્યું છે...",
    formSuccessAppended: "અપરિવર્તનીય ઘટના {id} ઉમેરાઈ (SHA-256: {hash}...)",
    formErrorFailed: "નોંધ કરવામાં નિષ્ફળ: {error}",
    tableTitle: "સ્ત્રોત-સંકળાયેલ મતદાર ફેરફાર લેજર રેકોર્ડ્સ",
    tableSub:
      "દરેક હરોળ સંદર્ભ અને લક્ષ્ય સ્નેપશોટ SHA-256, મતદાન મથક ભાગ, ક્રમ નંબર અને પૂરક બેચ સાથે ચોક્કસ રીતે જોડાયેલ છે.",
    colLedgerId: "લેજર ID",
    colEpic: "સિન્થેટિક EPIC",
    colElector: "મતદાર (સિન્થેટિક)",
    colClassification: "ફેરફાર વર્ગીકરણ",
    colLineage: "બૂથ / ક્રમ વંશાવળી",
    colDelta: "વિગત તફાવત",
    colSupplementRef: "પૂરક સ્ત્રોત સંદર્ભ",
    ageDeltaText: "ઉંમર {before}→{after}",
  },
};
