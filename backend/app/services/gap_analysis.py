"""Structured ERONET vs. PollToll Feature-by-Feature Gap Analysis service."""

from __future__ import annotations

from app.i18n import LanguageCode, normalize_lang, pick
from app.models import GapAnalysisItem


def get_eronet_gap_matrix(lang: str = "en") -> list[GapAnalysisItem]:
    lang_code: LanguageCode = normalize_lang(lang)

    items = [
        {
            "id": 1,
            "is_prototype_core": False,
            "capability": {
                "en": "National Voter Registration & Form 6 / 7 / 8 Processing",
                "hi": "राष्ट्रीय मतदाता पंजीकरण एवं फॉर्म 6 / 7 / 8 प्रसंस्करण",
                "gu": "રાષ્ટ્રીય મતદાર નોંધણી અને ફોર્મ 6 / 7 / 8 પ્રક્રિયા",
            },
            "eronet_documented_status": {
                "en": "Publicly documented core capability of ERONET / ERONET 2.0 / ECINET and voters.eci.gov.in.",
                "hi": "ERONET / ERONET 2.0 / ECINET और voters.eci.gov.in की सार्वजनिक रूप से प्रलेखित मुख्य क्षमता।",
                "gu": "ERONET / ERONET 2.0 / ECINET અને voters.eci.gov.in ની જાહેરમાં દસ્તાવેજીકૃત મુખ્ય ક્ષમતા.",
            },
            "internal_epistemic_limit": {
                "en": "Confirmed operational at national scale across States/UTs.",
                "hi": "राज्यों/केंद्र शासित प्रदेशों में राष्ट्रीय स्तर पर परिचालन रूप से पुष्ट।",
                "gu": "રાજ્યો/કેન્દ્રશાસિત પ્રદેશોમાં રાષ્ટ્રીય સ્તરે સક્રિય હોવાની પુષ્ટિ થયેલ.",
            },
            "external_audit_gap": {
                "en": "No external gap — rebuilding voter registration workflows is redundant.",
                "hi": "कोई बाहरी कमी नहीं — मतदाता पंजीकरण कार्यप्रवाह का पुनर्निर्माण अनावश्यक है।",
                "gu": "કોઈ બાહ્ય ગેપ નથી — મતદાર નોંધણી વર્કફ્લો ફરીથી બનાવવો બિનજરૂરી છે.",
            },
            "polltoll_wedge": {
                "en": "Out of scope by design; Citizen Assistant only guides citizens to official ECI Form 6/7/8 channels.",
                "hi": "उद्देश्यपूर्वक कार्यक्षेत्र से बाहर; नागरिक सहायक केवल अधिकृत ECI फॉर्म 6/7/8 चैनलों पर मार्गदर्शन करता है।",
                "gu": "ડિઝાઇન મુજબ કાર્યક્ષેત્ર બહાર; નાગરિક સહાયક માત્ર સત્તાવાર ચૂંટણી પંચના ફોર્મ 6/7/8 માધ્યમો પર માર્ગદર્શન આપે છે.",
            },
        },
        {
            "id": 2,
            "is_prototype_core": False,
            "capability": {
                "en": "Photo & Demographic Duplicate Matching (PSE / DSE)",
                "hi": "फोटो एवं जनसांख्यिकीय डुप्लिकेट मिलान (PSE / DSE)",
                "gu": "ફોટો અને વસ્તીવિષયક ડુપ્લિકેટ મેચિંગ (PSE / DSE)",
            },
            "eronet_documented_status": {
                "en": "Built into ERONET Decision Support System with BLO field verification checklists and Rule 18/21-A notices.",
                "hi": "BLO क्षेत्रीय सत्यापन चेकलिस्ट और नियम 18/21-A नोटिस के साथ ERONET निर्णय सहायता प्रणाली में अंतर्निहित।",
                "gu": "BLO ક્ષેત્ર ચકાસણી ચેકલિસ્ટ અને નિયમ 18/21-A નોટિસ સાથે ERONET ડિસિઝન સપોર્ટ સિસ્ટમમાં સમાવિષ્ટ.",
            },
            "internal_epistemic_limit": {
                "en": "Operates on full UNPER database including photographs not released in public PDFs.",
                "hi": "सार्वजनिक पीडीएफ में अप्रकाशित तस्वीरों सहित पूर्ण UNPER डेटाबेस पर संचालित।",
                "gu": "જાહેર પીડીએફમાં અપ્રકાશિત ફોટોગ્રાફ્સ સહિત સંપૂર્ણ UNPER ડેટાબેઝ પર કાર્યરત.",
            },
            "external_audit_gap": {
                "en": "Public searchable PDFs omit voter photos for privacy; competing on photo deduplication is impossible and undesirable.",
                "hi": "गोपनीयता हेतु सार्वजनिक पीडीएफ में तस्वीरें नहीं होतीं; फोटो डी-डुप्लिकेशन में प्रतिस्पर्धा असंभव एवं अवांछनीय है।",
                "gu": "ગોપનીયતા માટે જાહેર પીડીએફમાં ફોટા હોતા નથી; ફોટો ડી-ડુપ્લિકેશનમાં સ્પર્ધા અશક્ય અને અનિચ્છનીય છે.",
            },
            "polltoll_wedge": {
                "en": "Do not compete on PSE; only surface cross-booth supplement transliteration clusters as secondary review cues.",
                "hi": "PSE पर प्रतिस्पर्धा न करें; केवल द्वितीयक समीक्षा संकेत के रूप में क्रॉस-बूथ लिप्यंतरण समूहों को उजागर करें।",
                "gu": "PSE પર સ્પર્ધા ન કરવી; માત્ર ગૌણ સમીક્ષા સંકેત તરીકે ક્રોસ-બૂથ લિપ્યંતરણ ક્લસ્ટર્સ દર્શાવવા.",
            },
        },
        {
            "id": 3,
            "is_prototype_core": True,
            "capability": {
                "en": "Cross-Version Electoral Change Ledger & Booth-Split Reconciliation",
                "hi": "संस्करण-पार मतदाता परिवर्तन लेजर एवं बूथ-विभाजन मिलान",
                "gu": "આવૃત્તિ-આરપાર મતદાર ફેરફાર લેજર અને બૂથ-વિભાજન સમાધાન",
            },
            "eronet_documented_status": {
                "en": "Published externally as thousands of separate per-booth Draft, Supplement, and Final PDFs.",
                "hi": "बाहरी रूप से हजारों अलग-अलग प्रति-बूथ प्रारूप, पूरक और अंतिम पीडीएफ के रूप में प्रकाशित।",
                "gu": "બાહ્ય રીતે હજારો અલગ અલગ પ્રતિ-બૂથ મુસદ્દા, પૂરક અને અંતિમ પીડીએફ તરીકે પ્રકાશિત.",
            },
            "internal_epistemic_limit": {
                "en": "EROs likely retain internal modification histories inside ERONET, which are not externally queryable.",
                "hi": "ERO संभवतः ERONET के अंदर आंतरिक संशोधन इतिहास रखते हैं, जो बाहरी रूप से खोज योग्य नहीं हैं।",
                "gu": "ERO કદાચ ERONET ની અંદર આંતરિક સુધારણા ઇતિહાસ રાખે છે, જે બહારથી શોધી શકાતો નથી.",
            },
            "external_audit_gap": {
                "en": "HIGH GAP: Outside observers see disconnected booth PDFs; e.g. 340 deletions in Booth A and 338 transfers to Booth B trigger false 'mass deletion' panics.",
                "hi": "बड़ा अंतर: बाहरी पर्यवेक्षक असंबद्ध बूथ पीडीएफ देखते हैं; उदा. बूथ A में 340 नाम हटने और बूथ B में 338 स्थानांतरण से झूठी 'सामूहिक विलोपन' की अफवाहें फैलती हैं।",
                "gu": "મોટો તફાવત: બહારના નિરીક્ષકો અસંબંધિત બૂથ પીડીએફ જુએ છે; દા.ત. બૂથ A માંથી 340 કમી અને બૂથ B માં 338 સ્થળાંતરથી ખોટી 'સામૂહિક કમી' ની અફવાઓ ફેલાય છે.",
            },
            "polltoll_wedge": {
                "en": "CORE WEDGE #1: Deterministic Change Ledger reconciling ADDED, DELETED, MODIFIED, and cross-booth BOOTH_TRANSFERRED records with SHA-256 lineage.",
                "hi": "मुख्य मूल्य #1: SHA-256 वंशावली के साथ जोड़े गए, हटाए गए, संशोधित और क्रॉस-बूथ स्थानांतरित रिकॉर्ड का समाधान करने वाला नियतात्मक परिवर्तन लेजर।",
                "gu": "મુખ્ય મૂલ્ય #1: SHA-256 વંશાવળી સાથે ઉમેરાયેલ, કમી થયેલ, સુધારેલ અને ક્રોસ-બૂથ સ્થળાંતરિત રેકોર્ડ્સનું સમાધાન કરતું નિર્ણાયક ચેન્જ લેજર.",
            },
        },
        {
            "id": 4,
            "is_prototype_core": True,
            "capability": {
                "en": "Historical-Baseline Spatio-Temporal Anomaly Testing with Uncertainty Bounds",
                "hi": "अनिश्चितता सीमाओं के साथ ऐतिहासिक आधाररेखा स्थानिक-कालिक विसंगति परीक्षण",
                "gu": "અનિશ્ચિતતા મર્યાદાઓ સાથે ઐતિહાસિક આધારરેખા સ્થાનિક-સાંયોગિક વિસંગતતા પરીક્ષણ",
            },
            "eronet_documented_status": {
                "en": "Not exposed on public portals (which show single-cycle roll PDFs and aggregate elector counts).",
                "hi": "सार्वजनिक पोर्टलों पर प्रदर्शित नहीं (जो केवल एकल-चक्र सूची पीडीएफ और कुल मतदाता संख्या दिखाते हैं)।",
                "gu": "જાહેર પોર્ટલ પર દર્શાવવામાં આવતું નથી (જે માત્ર સિંગલ-સાયકલ પીડીએફ અને કુલ મતદાર ગણતરી બતાવે છે).",
            },
            "internal_epistemic_limit": {
                "en": "Public docs cannot rule out internal CEO/ECI statistical dashboards during Special Summary Revision.",
                "hi": "सार्वजनिक दस्तावेज विशेष संक्षिप्त पुनरीक्षण के दौरान आंतरिक CEO/ECI सांख्यिकीय डैशबोर्ड को खारिज नहीं कर सकते।",
                "gu": "જાહેર દસ્તાવેજો ખાસ સંક્ષિપ્ત સુધારણા દરમિયાન આંતરિક CEO/ECI આંકડાકીય ડેશબોર્ડને નકારી શકતા નથી.",
            },
            "external_audit_gap": {
                "en": "HIGH GAP: Civic groups and reporters cite raw deletion numbers without multi-year baselines or 95% confidence bounds.",
                "hi": "बड़ा अंतर: नागरिक समूह और पत्रकार बहु-वर्षीय आधाररेखा या 95% विश्वास सीमाओं के बिना केवल सकल विलोपन आंकड़ों का हवाला देते हैं।",
                "gu": "મોટો તફાવત: નાગરિક જૂથો અને પત્રકારો બહુ-વર્ષીય આધારરેખા કે 95% વિશ્વાસ મર્યાદાઓ વગર માત્ર કાચા કમી આંકડા ટાંકે છે.",
            },
            "polltoll_wedge": {
                "en": "CORE WEDGE #2: Tests booth rates against 3-cycle historical baselines with explicit 95% Wilson confidence intervals and Z-scores.",
                "hi": "मुख्य मूल्य #2: स्पष्ट 95% विल्सन विश्वास अंतराल और Z-स्कोर के साथ 3-चक्र ऐतिहासिक आधाररेखा के विरुद्ध बूथ दरों का परीक्षण करता है।",
                "gu": "મુખ્ય મૂલ્ય #2: સ્પષ્ટ 95% વિલ્સન કોન્ફિડન્સ ઇન્ટરવલ અને Z-સ્કોર સાથે 3-સાયકલ ઐતિહાસિક આધારરેખા સામે બૂથ દરોનું પરીક્ષણ કરે છે.",
            },
        },
        {
            "id": 5,
            "is_prototype_core": True,
            "capability": {
                "en": "5-Part Evidence-Backed Explanations with Missing-Evidence Disclosure",
                "hi": "अनुपलब्ध-साक्ष्य प्रकटीकरण के साथ 5-भाग साक्ष्य-समर्थित व्याख्याएं",
                "gu": "ખૂટતા-પુરાવા જાહેરાત સાથે 5-ભાગ પુરાવા-સમર્થિત સમજૂતીઓ",
            },
            "eronet_documented_status": {
                "en": "Published supplements list terse reason codes (S/E/Q/M/R) without multi-hypothesis audit context.",
                "hi": "प्रकाशित पूरक बहु-परिकल्पना ऑडिट संदर्भ के बिना केवल संक्षिप्त कारण कोड (S/E/Q/M/R) सूचीबद्ध करते हैं।",
                "gu": "પ્રકાશિત પૂરવણીઓ બહુ-પૂર્વધારણા ઓડિટ સંદર્ભ વિના માત્ર સંક્ષિપ્ત કારણ કોડ (S/E/Q/M/R) દર્શાવે છે.",
            },
            "internal_epistemic_limit": {
                "en": "Internal Decision Matrix stores BLO remarks that remain non-public for privacy.",
                "hi": "आंतरिक निर्णय मैट्रिक्स में BLO टिप्पणियां संग्रहीत होती हैं जो गोपनीयता के कारण गैर-सार्वजनिक रहती हैं।",
                "gu": "આંતરિક નિર્ણય મેટ્રિક્સ BLO શેરાઓ સંગ્રહિત કરે છે જે ગોપનીયતા માટે બિન-જાહેર રહે છે.",
            },
            "external_audit_gap": {
                "en": "HIGH GAP: No neutral tool states what changed, which rule fired, innocent causes, AND which non-public documents are missing.",
                "hi": "बड़ा अंतर: कोई निष्पक्ष उपकरण यह नहीं बताता कि क्या बदला, कौन सा नियम लागू हुआ, निर्दोष कारण क्या हैं, और कौन से गैर-सार्वजनिक दस्तावेज गायब हैं।",
                "gu": "મોટો તફાવત: કોઈ તટસ્થ સાધન સ્પષ્ટ કરતું નથી કે શું બદલાયું, કયો નિયમ લાગુ થયો, નિર્દોષ કારણો કયા છે, અને કયા બિન-જાહેર દસ્તાવેજો ખૂટે છે.",
            },
            "polltoll_wedge": {
                "en": "CORE WEDGE #3: Enforced 5-part schema (What changed, Rule, Innocent causes, Missing evidence, Next verification step).",
                "hi": "मुख्य मूल्य #3: अनिवार्य 5-भाग प्रारूप (क्या बदला, नियम, निर्दोष कारण, अनुपलब्ध साक्ष्य, अगला सत्यापन कदम)।",
                "gu": "મુખ્ય મૂલ્ય #3: ફરજિયાત 5-ભાગનું માળખું (શું બદલાયું, નિયમ, નિર્દોષ કારણો, ખૂટતા પુરાવા, આગળનું ચકાસણી પગલું).",
            },
        },
        {
            "id": 6,
            "is_prototype_core": True,
            "capability": {
                "en": "Tamper-Evident Third-Party Audit Receipts & Append-Only Correction Log",
                "hi": "छेड़छाड़-रोधी तृतीय-पक्ष ऑडिट रसीदें एवं केवल-जोड़ने-योग्य सुधार लॉग",
                "gu": "છેડછાડ-પ્રતિરોધક તૃતીય-પક્ષ ઓડિટ રસીદો અને માત્ર-ઉમેરાય-તેવો સુધારણા લોગ",
            },
            "eronet_documented_status": {
                "en": "Not applicable — ERONET is the authority's internal operational database, not an external attestation protocol.",
                "hi": "लागू नहीं — ERONET प्राधिकरण का आंतरिक परिचालन डेटाबेस है, कोई बाहरी सत्यापन प्रोटोकॉल नहीं।",
                "gu": "લાગુ પડતું નથી — ERONET એ સત્તામંડળનો આંતરિક ઓપરેશનલ ડેટાબેઝ છે, બાહ્ય પ્રમાણીકરણ પ્રોટોકોલ નથી.",
            },
            "internal_epistemic_limit": {
                "en": "Even with strong internal logs, an operational authority cannot act as its own independent external auditor.",
                "hi": "मजबूत आंतरिक लॉग के बावजूद, कोई परिचालन प्राधिकरण अपने स्वयं के स्वतंत्र बाहरी लेखापरीक्षक के रूप में कार्य नहीं कर सकता।",
                "gu": "મજબૂત આંતરિક લૉગ્સ હોવા છતાં, કોઈ ઓપરેશનલ ઓથોરિટી તેના પોતાના સ્વતંત્ર બાહ્ય ઓડિટર તરીકે કાર્ય કરી શકતી નથી.",
            },
            "external_audit_gap": {
                "en": "CRITICAL STARTUP MOAT: Observers, universities, and civic groups lack reproducible signed receipts proving identical neutral tests.",
                "hi": "महत्वपूर्ण अंतर: पर्यवेक्षकों, विश्वविद्यालयों और नागरिक समूहों के पास समान निष्पक्ष परीक्षण साबित करने वाली हस्ताक्षरित रसीदों का अभाव है।",
                "gu": "મહત્વપૂર્ણ તફાવત: નિરીક્ષકો, યુનિવર્સિટીઓ અને નાગરિક જૂથો પાસે સમાન તટસ્થ પરીક્ષણ સાબિત કરતી ડિજિટલ સહીવાળી રસીદોનો અભાવ છે.",
            },
            "polltoll_wedge": {
                "en": "CORE WEDGE #4: Ed25519-signed .polltoll-receipt.json with dataset/rule SHA-256s + hash-chained review log, verifiable in-browser via WebCrypto.",
                "hi": "मुख्य मूल्य #4: डेटासेट/नियम SHA-256 + हैश-श्रृंखलाबद्ध समीक्षा लॉग के साथ Ed25519-हस्ताक्षरित .polltoll-receipt.json, जो WebCrypto द्वारा ब्राउज़र में सत्यापन योग्य है।",
                "gu": "મુખ્ય મૂલ્ય #4: ડેટાસેટ/નિયમ SHA-256 + હેશ-સાંકળિત સમીક્ષા લોગ સાથે Ed25519-હસ્તાક્ષરિત .polltoll-receipt.json, જે WebCrypto દ્વારા બ્રાઉઝરમાં ચકાસી શકાય છે.",
            },
        },
        {
            "id": 7,
            "is_prototype_core": True,
            "capability": {
                "en": "Ledger-Grounded Viral Claim Checker & Multilingual Change Assistant (EN / HI / GU)",
                "hi": "लेजर-आधारित वायरल दावा जांचकर्ता एवं बहुभाषी परिवर्तन सहायक (अंग्रेजी / हिंदी / गुजराती)",
                "gu": "લેજર-આધારિત વાયરલ દાવા ચકાસણી અને બહુભાષી ફેરફાર સહાયક (અંગ્રેજી / હિન્દી / ગુજરાતી)",
            },
            "eronet_documented_status": {
                "en": "Voter Portal supports current EPIC lookup; viral claims are addressed ad-hoc via press releases.",
                "hi": "मतदाता पोर्टल वर्तमान EPIC खोज का समर्थन करता है; वायरल दावों का समाधान प्रेस विज्ञप्तियों के माध्यम से तदर्थ किया जाता है।",
                "gu": "વોટર પોર્ટલ વર્તમાન EPIC શોધને સપોર્ટ કરે છે; વાયરલ દાવાઓનું સમાધાન અખબારી યાદીઓ મારફતે એડ-હોક ધોરણે થાય છે.",
            },
            "internal_epistemic_limit": {
                "en": "Observable directly on public-facing portals.",
                "hi": "सार्वजनिक-उन्मुख पोर्टलों पर सीधे अवलोकनीय।",
                "gu": "જાહેર પોર્ટલ પર સીધું જોઈ શકાય છે.",
            },
            "external_audit_gap": {
                "en": "Citizens and journalists lack instant, non-partisan triage separating Verified numbers, Disputed framing, and Unprovable claims.",
                "hi": "नागरिकों और पत्रकारों के पास सत्यापित आंकड़ों, विवादित व्याख्या और असिद्ध दावों को अलग करने वाली तत्काल, निष्पक्ष व्यवस्था का अभाव है।",
                "gu": "નાગરિકો અને પત્રકારો પાસે ચકાસાયેલ આંકડા, વિવાદિત અર્થઘટન અને અસાબિત દાવાઓને અલગ કરતી ત્વરિત, તટસ્થ વ્યવસ્થાનો અભાવ છે.",
            },
            "polltoll_wedge": {
                "en": "PUBLIC PORTAL (PollToll Verify): Free English, Hindi, and Gujarati voice/text assistant + 3-bucket Claim Checker.",
                "hi": "सार्वजनिक पोर्टल (PollToll वेरिफाई): निःशुल्क अंग्रेजी, हिंदी और गुजराती वॉयस/टेक्स्ट सहायक + 3-स्तंभीय दावा जांचकर्ता।",
                "gu": "જાહેર પોર્ટલ (PollToll વેરિફાય): મફત અંગ્રેજી, હિન્દી અને ગુજરાતી વૉઇસ/ટેક્સ્ટ સહાયક + 3-સ્તંભીય દાવા ચકાસણી.",
            },
        },
    ]

    return [
        GapAnalysisItem(
            id=item["id"],
            capability=item["capability"][lang_code],
            eronet_documented_status=item["eronet_documented_status"][lang_code],
            internal_epistemic_limit=item["internal_epistemic_limit"][lang_code],
            external_audit_gap=item["external_audit_gap"][lang_code],
            polltoll_wedge=item["polltoll_wedge"][lang_code],
            is_prototype_core=item["is_prototype_core"],
        )
        for item in items
    ]
