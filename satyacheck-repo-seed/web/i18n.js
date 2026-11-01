// web/i18n.js – Bilingual dictionary (English & Hindi) for SatyaCheck
// Every string comes from here per docs/07-frontend.md.
// Note: Hindi translations provided; // TODO native speaker review

export const translations = {
  en: {
    appTitle: "SatyaCheck",
    appTagline: "Community Scam Map & Verification",
    navCheck: "Check",
    navReport: "Report",
    navMap: "Map",
    navAlerts: "Alerts",
    navAbout: "About",

    // Check View
    checkHeading: "Check Before You Trust",
    checkSubheading: "Instant community-verified check for unknown phone numbers, UPI IDs, links, or SMS headers.",
    checkPlaceholder: "Paste a number, UPI ID, link or SMS sender...",
    checkButton: "Check Now",
    checkingBtn: "Checking...",
    reportCTA: "Report a Scam",
    recentAlertsPreview: "Recent Area Alerts",
    emergencyHelpline: "Lost money? Call national cyber helpline 1930 or visit cybercrime.gov.in immediately.",
    nationalCybercrimePortal: "cybercrime.gov.in",

    // Type Chips
    typeAuto: "Auto-detect",
    typePhone: "Phone",
    typeUpi: "UPI ID",
    typeUrl: "Link / URL",
    typeSender: "SMS Sender",

    // Verdicts
    verdict_KNOWN_SCAM: "Known Scam",
    verdict_SUSPICIOUS: "Suspicious",
    verdict_NO_REPORTS: "No Reports",
    verdict_VERIFIED_BUSINESS: "Verified Business",

    // Explanations
    reportedByCount: "Reported by {count} independent people ({reports} total sightings)",
    reportedBySingular: "Reported by 1 person ({reports} total sightings)",
    noReportsDesc: "No one has reported this yet. That is not proof it is safe.",
    verifiedDesc: "Official verified identifier belonging to a registered organisation or government service.",
    challengedNotice: "The owner has disputed this. It is under review.",
    disputeLink: "This is my number / organisation",

    // What to do
    whatToDoTitle: "Recommended Action",
    whatToDo_KNOWN_SCAM: "Do not respond, do not click any links, and never send money or approve requests from this identifier. Block immediately.",
    whatToDo_SUSPICIOUS: "Exercise extreme caution. Verify identity independently through official public channels before sharing any information.",
    whatToDo_NO_REPORTS: "Stay alert. Always confirm identities directly via official contacts. Never share passwords, OTPs, or UPI PINs.",
    whatToDo_VERIFIED_BUSINESS: "Recognised verified identity. Still beware of spoofing or callers demanding unexpected transactions.",

    // Tech details
    techDetailsTitle: "Technical Verification Details",
    detailIdentifier: "Identifier",
    detailVerdict: "Verdict",
    detailDistinctReporters: "Independent Cohorts",
    detailTotalReports: "Total Sightings",
    detailFirstSeen: "First Sighted",
    detailLastSeen: "Most Recent Sighting",
    detailScamType: "Predominant Scam Type",
    detailEvidence: "Recent Sightings",
    detailChallenged: "Dispute Status",
    noneText: "None",

    // Report View
    reportHeading: "Report a Scam Sighting",
    reportSubheading: "Help protect your community. Takes under 60 seconds. No login required.",
    step1Channel: "1. How did they contact you?",
    step2Type: "2. What type of scam was it?",
    step3Identifier: "3. Identifier details",
    step4Area: "4. Your general area (pincode)",
    step5Time: "5. When did this happen?",
    step6Note: "6. Brief note (Optional)",
    notePrivacyWarning: "Privacy rule: Do NOT include your name, phone number, or bank details.",
    step7Loss: "Did you lose money? (Optional)",
    amountLostLabel: "Amount lost (₹ INR)",
    hasScreenshotLabel: "I have a screenshot / evidence saved",
    hasScreenshotHint: "Keep it safe on your device for cyber helpline 1930 reporting. For your privacy, SatyaCheck never collects images.",
    submitReportBtn: "Submit Anonymous Report",
    submittingBtn: "Submitting...",

    // Channels
    channel_call: "Phone Call",
    channel_sms: "SMS or WhatsApp",
    channel_qr: "QR Code",
    channel_web: "Fake Website",
    channel_upi: "UPI Request",
    channel_other: "Something Else",

    // Scam Types
    scam_digital_arrest: "Digital Arrest",
    scam_fake_kyc: "Fake KYC Link",
    scam_upi_refund: "UPI Refund QR",
    scam_investment: "Investment Group",
    scam_courier: "Courier / Customs",
    scam_job_offer: "Job Offer",
    scam_lottery: "Lottery / Prize",
    scam_loan_app: "Loan App Harassment",
    scam_electricity: "Electricity Disconnection",
    scam_customer_care: "Fake Customer Care",
    scam_otp_call: "OTP / PIN Call",
    scam_sextortion: "Sextortion / Video Call",
    scam_other: "Other Scam",

    // Time options
    timeJustNow: "Just now",
    timeToday: "Earlier today",
    timeYesterday: "Yesterday",

    // Success Screen
    reportSuccessTitle: "Report Received",
    reportSuccessMessage: "Thank you for alerting your community. Your report has been anonymously verified and added to the sightings graph.",
    reportRefLabel: "Report Submission ID",
    reportRefSub: "Unique tracking reference generated for this report submission",
    caseRefLabel: "Community Cluster Case ID",
    caseRefSub: "Cryptographic cluster grouping all reports for this specific number or account",
    attachScreenshotTitle: "Attach Screenshot (Optional)",
    reportAnonNote: "Your report is anonymous. Only salted cryptographic tokens and pincode-level location are stored.",
    notPoliceComplaint: "Important: SatyaCheck is a community intelligence map, NOT a police FIR or formal complaint.",

    // Map View
    mapHeading: "Community Scam Activity Map",
    mapSubheading: "Aggregated independent sightings by locality over recent days.",
    mapFilterDays: "Time Window:",
    mapFilterRadius: "Radius:",
    timeChip24h: "24 hours",
    timeChip3d: "3 days",
    timeChip7d: "7 days",
    badgeFew: "A few reports",
    badgeMany: "Many",
    badgeVeryMany: "Very many",
    badgeNoReports: "No reports",
    legendTitle: "Scam Activity Level",
    legendCrit: "CRIT (10 or more): Very many",
    legendHigh: "HIGH (5–9): Many",
    legendMed: "MED (below 5): A few reports",
    legendGreen: "Green: no reports in this period",
    popupReports: "independent reports",
    popupTopScam: "Top scam type",
    popupAdvice: "Safety advice",
    popupCheckLink: "Check a number",
    mapBlockedTitle: "Map view unavailable",
    mapBlockedMsg: "Interactive map blocked by browser/network. Viewing cluster reports list below.",
    noReportsInPeriod: "No reports in this period",
    searchMapPlaceholder: "Search locality, city, or pincode...",
    btnFitAll: "Reset View",
    tabAllLocalities: "All Localities",
    tabActiveHotspots: "Active Hotspots",
    tabCalmAreas: "Calm Areas",
    days7: "Last 7 days",
    days14: "Last 14 days",
    days30: "Last 30 days",
    radiusAll: "All Areas",
    radius2km: "2 km",
    radius5km: "5 km",
    radius10km: "10 km",
    mapClustersList: "Active Locality Clusters",
    severityCrit: "Critical Activity",
    severityHigh: "High Activity",
    severityMed: "Moderate Activity",

    // Alerts View
    alertsHeading: "Emerging Threat Alerts",
    alertsSubheading: "Real-time anomaly detection for local spikes and newly emerging scam tactics.",
    noAlertsActive: "No active anomaly alerts in your area right now.",
    alertSpikeTitle: "Sudden Spike in Scam Sightings",
    alertSpikeDesc: "{count} independent reports in the last 24h (prior daily baseline: {baseline}/day).",
    alertNewTypeTitle: "New Scam Pattern Emerged",
    alertNewTypeDesc: "The scam type '{type}' was newly sighted in this locality in the last 24h.",

    // About View
    aboutHeading: "About SatyaCheck",
    trustHeader: "How Our Trust Engine Works",
    trust1: "A single report is a sighting, never an automatic verdict.",
    trust2: "Coordinated bot accounts on the same network or with copy-pasted notes are merged into a single cohort.",
    trust3: "An identifier reaches Known Scam only when multiple independent people on distinct networks corroborate it.",
    trust4: "Numbers are masked until enough independent sightings exist, preventing harassment.",
    trust5: "Legitimate businesses and helplines can verify their identity or dispute incorrect reports.",

    privacyHeader: "Our Privacy Architecture",
    privacy1: "We never ask for your name, phone number, or exact GPS coordinates.",
    privacy2: "Your device and network are pseudonymised using HMAC-SHA256 salted tokens.",
    privacy3: "Notes are automatically scrubbed for personal details and strictly capped at 300 characters.",
    privacy4: "No screenshots are ever uploaded to our servers.",

    adviceHeader: "Scam Prevention Knowledgebase",
    disputeHeader: "Business Dispute & Verification Form",
    disputeSubheading: "If your business or organisation number is reported incorrectly, file an official dispute below.",
    disputeName: "Claimant / Organisation Name",
    disputeEmail: "Official Contact Email",
    disputeProof: "Proof or Justification",
    submitDisputeBtn: "Submit Dispute Challenge",
    disputeSuccess: "Dispute submitted successfully. Challenge ID: {id}. Your identifier is now marked under review.",

    // Scam advice items (docs/07)
    advice_digital_arrest: "No police or government agency ever arrests citizens over a WhatsApp/Skype video call. Hang up immediately. Call 1930 or visit cybercrime.gov.in if money was lost.",
    advice_fake_kyc_link: "Banks and telecom operators never send SMS links to complete KYC or update SIM cards. Call 1930 or visit cybercrime.gov.in if money was lost.",
    advice_upi_refund_qr: "Scanning any QR code or entering your UPI PIN always sends money from your account; it never receives money. Call 1930 or visit cybercrime.gov.in if money was lost.",
    advice_investment_group: "Telegram and WhatsApp groups promising guaranteed high returns or insider trading are traps. Call 1930 or visit cybercrime.gov.in if money was lost.",
    advice_courier_customs: "Legitimate parcel companies do not call asking for police clearance or customs tax via personal UPI. Call 1930 or visit cybercrime.gov.in if money was lost.",
    advice_job_offer: "Genuine employers never demand security deposits, training charges, or review task fees. Call 1930 or visit cybercrime.gov.in if money was lost.",
    advice_lottery_prize: "You cannot win a lottery or car contest that you never purchased a ticket for. Call 1930 or visit cybercrime.gov.in if money was lost.",
    advice_loan_app_harassment: "Never grant contact list or gallery permissions to unofficial APK loan apps. Call 1930 or visit cybercrime.gov.in if money was lost.",
    advice_electricity_disconnection: "Power companies never threaten immediate disconnection via random personal mobile numbers. Check only on the official electricity portal. Call 1930 or visit cybercrime.gov.in if money was lost.",
    advice_fake_customer_care: "Never use Google search phone numbers for bank or airline customer service. Use only the official app or website. Call 1930 or visit cybercrime.gov.in if money was lost.",
    advice_otp_call: "Never share an OTP, PIN, or banking password over a phone call, regardless of who claims to be speaking. Call 1930 or visit cybercrime.gov.in if money was lost.",
    advice_sextortion: "Do not send money or panic. Block the caller, save screenshot evidence, and report immediately to cybercrime.gov.in. Call 1930 or visit cybercrime.gov.in if money was lost.",
    advice_other: "When in doubt, stop and verify through known official numbers. Call 1930 or visit cybercrime.gov.in if money was lost.",

    // Licence expired
    licenceExpiredTitle: "Licence Expired",
    licenceExpiredMsg: "The SatyaCheck evaluation licence has expired. Please contact your system provider to renew.",
    licencePollingMsg: "Checking system status every 30 seconds...",
  },

  hi: {
    appTitle: "सत्यचेक (SatyaCheck)",
    appTagline: "सामुदायिक स्कैम मैप और सत्यापन",
    navCheck: "जांचें",
    navReport: "रिपोर्ट करें",
    navMap: "नक्शा",
    navAlerts: "अलर्ट",
    navAbout: "जानकारी",

    // Check View
    checkHeading: "भरोसा करने से पहले जांचें",
    checkSubheading: "अज्ञात फोन नंबर, यूपीआई आईडी, लिंक या एसएमएस हेडर की सामुदायिक सत्यापन जांच।",
    checkPlaceholder: "नंबर, यूपीआई आईडी, लिंक या एसएमएस प्रेषक यहां पेस्ट करें...",
    checkButton: "अभी जांचें",
    checkingBtn: "जांच जारी है...",
    reportCTA: "स्कैम की रिपोर्ट करें",
    recentAlertsPreview: "क्षेत्रीय ताजा अलर्ट",
    emergencyHelpline: "पैसे गंवाए हैं? तुरंत राष्ट्रीय साइबर हेल्पलाइन 1930 पर कॉल करें या cybercrime.gov.in पर जाएं।",
    nationalCybercrimePortal: "cybercrime.gov.in",

    // Type Chips
    typeAuto: "स्वतः पहचान",
    typePhone: "फोन",
    typeUpi: "यूपीआई आईडी",
    typeUrl: "वेब लिंक",
    typeSender: "एसएमएस प्रेषक",

    // Verdicts
    verdict_KNOWN_SCAM: "ज्ञात स्कैम",
    verdict_SUSPICIOUS: "संदिग्ध",
    verdict_NO_REPORTS: "कोई रिपोर्ट नहीं",
    verdict_VERIFIED_BUSINESS: "सत्यापित व्यवसाय",

    // Explanations
    reportedByCount: "{count} स्वतंत्र नागरिकों द्वारा रिपोर्ट किया गया (कुल {reports} बार देखा गया)",
    reportedBySingular: "1 नागरिक द्वारा रिपोर्ट किया गया (कुल {reports} बार देखा गया)",
    noReportsDesc: "इसे अभी तक किसी ने रिपोर्ट नहीं किया है। इसका मतलब यह सुरक्षित होने का प्रमाण नहीं है।",
    verifiedDesc: "पंजीकृत संगठन या सरकारी सेवा से जुड़ा आधिकारिक सत्यापित पहचानकर्ता।",
    challengedNotice: "मालिक ने इस पर आपत्ति दर्ज की है। यह वर्तमान में समीक्षाधीन है।",
    disputeLink: "यह मेरा नंबर / संगठन है",

    // What to do
    whatToDoTitle: "सलाह",
    whatToDo_KNOWN_SCAM: "कोई उत्तर न दें, किसी लिंक पर क्लिक न करें, और कोई पैसा न भेजें। तुरंत ब्लॉक करें।",
    whatToDo_SUSPICIOUS: "अत्यधिक सावधानी बरतें। कोई भी जानकारी साझा करने से पहले आधिकारिक माध्यमों से पुष्टि करें।",
    whatToDo_NO_REPORTS: "सतर्क रहें। कभी भी अपना पासवर्ड, ओटीपी या यूपीआई पिन किसी के साथ साझा न करें।",
    whatToDo_VERIFIED_BUSINESS: "सत्यापित पहचान। फिर भी अचानक असामान्य पैसे मांगने वाले कॉलों से सावधान रहें।",

    // Tech details
    techDetailsTitle: "तकनीकी सत्यापन विवरण",
    detailIdentifier: "पहचानकर्ता",
    detailVerdict: "निष्कर्ष",
    detailDistinctReporters: "स्वतंत्र समूह (कोहोर्ट)",
    detailTotalReports: "कुल रिपोर्ट",
    detailFirstSeen: "पहली बार देखा गया",
    detailLastSeen: "हाल में देखा गया",
    detailScamType: "प्रमुख स्कैम प्रकार",
    detailEvidence: "हालिया साक्ष्य",
    detailChallenged: "विवाद स्थिति",
    noneText: "कोई नहीं",

    // Report View
    reportHeading: "स्कैम की रिपोर्ट दर्ज करें",
    reportSubheading: "अपने समुदाय की सुरक्षा करें। 60 सेकंड से कम समय। किसी लॉगिन की आवश्यकता नहीं।",
    step1Channel: "1. आपसे संपर्क कैसे किया गया?",
    step2Type: "2. यह किस प्रकार का स्कैम था?",
    step3Identifier: "3. पहचानकर्ता विवरण",
    step4Area: "4. आपका सामान्य क्षेत्र (पिनकोड)",
    step5Time: "5. यह कब हुआ?",
    step6Note: "6. संक्षिप्त विवरण (वैकल्पिक)",
    notePrivacyWarning: "गोपनीयता नियम: कृपया अपना नाम, फोन नंबर या बैंक विवरण न लिखें।",
    step7Loss: "क्या पैसों का नुकसान हुआ? (वैकल्पिक)",
    amountLostLabel: "खोई गई राशि (₹ INR)",
    hasScreenshotLabel: "मेरे पास स्क्रीनशॉट / साक्ष्य सुरक्षित है",
    hasScreenshotHint: "इसे हेल्पलाइन 1930 या पुलिस रिपोर्टिंग के लिए सुरक्षित रखें। गोपनीयता हेतु, सत्यचेक कभी इमेज एकत्र नहीं करता।",
    submitReportBtn: "गुमनाम रिपोर्ट जमा करें",
    submittingBtn: "जमा हो रहा है...",

    // Channels
    channel_call: "फोन कॉल",
    channel_sms: "एसएमएस या व्हाट्सएप",
    channel_qr: "क्यूआर कोड",
    channel_web: "फर्जी वेबसाइट",
    channel_upi: "यूपीआई अनुरोध",
    channel_other: "कुछ अन्य",

    // Scam Types
    scam_digital_arrest: "डिजिटल अरेस्ट",
    scam_fake_kyc: "फर्जी केवाईसी लिंक",
    scam_upi_refund: "यूपीआई रिफंड क्यूआर",
    scam_investment: "निवेश ग्रुप",
    scam_courier: "कूरियर / कस्टम्स",
    scam_job_offer: "नौकरी का प्रस्ताव",
    scam_lottery: "लॉटरी / इनाम",
    scam_loan_app: "लोन ऐप उत्पीड़न",
    scam_electricity: "बिजली बिल डिस्कनेक्शन",
    scam_customer_care: "फर्जी कस्टमर केयर",
    scam_otp_call: "ओटीपी / पिन कॉल",
    scam_sextortion: "सेक्सटॉर्शन / वीडियो कॉल",
    scam_other: "अन्य स्कैम",

    // Time options
    timeJustNow: "अभी-अभी",
    timeToday: "आज पहले",
    timeYesterday: "कल",

    // Success Screen
    reportSuccessTitle: "रिपोर्ट प्राप्त हुई",
    reportSuccessMessage: "समुदाय को सतर्क करने के लिए धन्यवाद। आपकी रिपोर्ट गुमनाम रूप से सत्यापित कर ली गई है।",
    reportRefLabel: "रिपोर्ट सबमिशन आईडी",
    reportRefSub: "इस विशिष्ट रिपोर्ट सबमिशन के लिए उत्पन्न अद्वितीय संदर्भ",
    caseRefLabel: "सामुदायिक क्लस्टर केस आईडी",
    caseRefSub: "इस विशिष्ट नंबर या खाते की सभी रिपोर्टों का क्रिप्टोग्राफिक समूह",
    attachScreenshotTitle: "स्क्रीनशॉट संलग्न करें (वैकल्पिक)",
    reportAnonNote: "आपकी रिपोर्ट पूर्णतः गोपनीय है। केवल सुरक्षित क्रिप्टोग्राफिक टोकन और पिनकोड स्तर का स्थान संग्रहीत किया जाता है।",
    notPoliceComplaint: "महत्वपूर्ण: सत्यचेक एक सामुदायिक खुफिया प्लेटफॉर्म है, यह पुलिस एफआईआर या औपचारिक शिकायत नहीं है।",

    // Map View
    mapHeading: "सामुदायिक स्कैम गतिविधि मैप",
    mapSubheading: "हाल के दिनों में इलाकों के आधार पर एकत्रित स्वतंत्र रिपोर्टें।",
    mapFilterDays: "समय सीमा:",
    mapFilterRadius: "त्रिज्या:",
    timeChip24h: "24 घंटे",
    timeChip3d: "3 दिन",
    timeChip7d: "7 दिन",
    badgeFew: "कुछ रिपोर्टें",
    badgeMany: "कई रिपोर्टें",
    badgeVeryMany: "अत्यधिक रिपोर्टें",
    badgeNoReports: "कोई रिपोर्ट नहीं",
    legendTitle: "स्कैम गतिविधि स्तर",
    legendCrit: "CRIT (10 या अधिक): अत्यधिक रिपोर्टें",
    legendHigh: "HIGH (5–9): कई रिपोर्टें",
    legendMed: "MED (5 से कम): कुछ रिपोर्टें",
    legendGreen: "हरा: इस अवधि में कोई रिपोर्ट नहीं",
    popupReports: "स्वतंत्र रिपोर्टें",
    popupTopScam: "शीर्ष स्कैम प्रकार",
    popupAdvice: "सुरक्षा सलाह",
    popupCheckLink: "नंबर चेक करें",
    mapBlockedTitle: "मैप दृश्य अनुपलब्ध है",
    mapBlockedMsg: "इंटरैक्टिव मैप लोड नहीं हो सका। नीचे इलाकों की रिपोर्ट सूची देखें।",
    noReportsInPeriod: "इस अवधि में कोई रिपोर्ट नहीं",
    searchMapPlaceholder: "इलाका, शहर या पिनकोड खोजें...",
    btnFitAll: "पूरा मैप देखें",
    tabAllLocalities: "सभी इलाके",
    tabActiveHotspots: "सक्रिय हॉटस्पॉट",
    tabCalmAreas: "शांत इलाके",
    days7: "पिछले 7 दिन",
    days14: "पिछले 14 दिन",
    days30: "पिछले 30 दिन",
    radiusAll: "सभी क्षेत्र",
    radius2km: "2 किमी",
    radius5km: "5 किमी",
    radius10km: "10 किमी",
    mapClustersList: "सक्रिय इलाके",
    severityCrit: "गंभीर गतिविधि",
    severityHigh: "उच्च गतिविधि",
    severityMed: "मध्यम गतिविधि",

    // Alerts View
    alertsHeading: "ताजा उभरती चेतावनियां (Alerts)",
    alertsSubheading: "स्थानीय अचानक वृद्धि और नए स्कैम तरीकों का रीयल-टाइम पता लगाना।",
    noAlertsActive: "इस समय आपके क्षेत्र में कोई असामान्य अलर्ट सक्रिय नहीं है।",
    alertSpikeTitle: "स्कैम रिपोर्टों में अचानक वृद्धि",
    alertSpikeDesc: "पिछले 24 घंटों में {count} स्वतंत्र रिपोर्टें मिलीं (दैनिक सामान्य आधार: {baseline}/दिन)।",
    alertNewTypeTitle: "नया स्कैम तरीका सामने आया",
    alertNewTypeDesc: "पिछले 24 घंटों में इस क्षेत्र में '{type}' प्रकार का स्कैम पहली बार देखा गया।",

    // About View
    aboutHeading: "सत्यचेक के बारे में",
    trustHeader: "हमारा ट्रस्ट इंजन कैसे काम करता है",
    trust1: "एक रिपोर्ट केवल एक सूचना है, कोई अंतिम फैसला नहीं।",
    trust2: "समान नेटवर्क या कॉपी-पेस्ट विवरण वाले खातों को एक ही समूह (कोहोर्ट) माना जाता है।",
    trust3: "कोई पहचानकर्ता केवल तभी 'ज्ञात स्कैम' बनता है जब अलग-अलग नेटवर्कों से स्वतंत्र लोग इसकी पुष्टि करते हैं।",
    trust4: "पर्याप्त स्वतंत्र साक्ष्य मिलने तक नंबर छिपा कर रखे जाते हैं ताकि किसी का उत्पीड़न न हो।",
    trust5: "वैध व्यवसाय और हेल्पलाइन अपनी पहचान सत्यापित करा सकते हैं या गलत रिपोर्ट पर आपत्ति जता सकते हैं।",

    privacyHeader: "हमारी गोपनीयता वास्तुकला",
    privacy1: "हम कभी आपका नाम, फोन नंबर या सटीक जीपीएस स्थान नहीं मांगते।",
    privacy2: "आपकी डिवाइस और नेटवर्क को केवल HMAC-SHA256 टोकन के रूप में बदला जाता है।",
    privacy3: "व्यक्तिगत जानकारी को हटाने के लिए विवरणों को स्वचालित रूप से साफ किया जाता है और 300 अक्षरों तक सीमित रखा जाता है।",
    privacy4: "हमारे सर्वर पर कभी कोई स्क्रीनशॉट अपलोड नहीं किया जाता।",

    adviceHeader: "स्कैम रोकथाम ज्ञानकोष",
    disputeHeader: "व्यापारिक विवाद एवं सत्यापन फॉर्म",
    disputeSubheading: "यदि आपके व्यावसायिक नंबर की गलत रिपोर्ट की गई है, तो नीचे आधिकारिक आपत्ति दर्ज करें।",
    disputeName: "दावेदार / संगठन का नाम",
    disputeEmail: "आधिकारिक संपर्क ईमेल",
    disputeProof: "प्रमाण या स्पष्टीकरण",
    submitDisputeBtn: "विवाद चुनौती जमा करें",
    disputeSuccess: "विवाद सफलतापूर्वक दर्ज हुआ। चुनौती आईडी: {id}। आपका पहचानकर्ता अब समीक्षाधीन है।",

    // Scam advice items (docs/07)
    advice_digital_arrest: "कोई भी सरकारी एजेंसी वीडियो कॉल पर कभी किसी को गिरफ्तार नहीं करती। तुरंत कॉल काटें। पैसे गंवाए हैं तो 1930 पर कॉल करें या cybercrime.gov.in पर जाएं।",
    advice_fake_kyc_link: "बैंक या टेलीकॉम ऑपरेटर कभी सिम या केवाईसी अपडेट के लिए लिंक नहीं भेजते। पैसे गंवाए हैं तो 1930 पर कॉल करें या cybercrime.gov.in पर जाएं।",
    advice_upi_refund_qr: "क्यूआर कोड स्कैन करने या यूपीआई पिन डालने से हमेशा पैसे कटते हैं, कभी प्राप्त नहीं होते। पैसे गंवाए हैं तो 1930 पर कॉल करें या cybercrime.gov.in पर जाएं।",
    advice_investment_group: "गारंटीड मुनाफे का वादा करने वाले टेलीग्राम या व्हाट्सएप ग्रुप धोखाधड़ी हैं। पैसे गंवाए हैं तो 1930 पर कॉल करें या cybercrime.gov.in पर जाएं।",
    advice_courier_customs: "कूरियर कंपनियां कभी व्यक्तिगत यूपीआई पर पुलिस क्लीयरेंस टैक्स नहीं मांगतीं। पैसे गंवाए हैं तो 1930 पर कॉल करें या cybercrime.gov.in पर जाएं।",
    advice_job_offer: "सच्चे नियोक्ता कभी काम देने के लिए सुरक्षा जमा राशि या टास्क शुल्क नहीं मांगते। पैसे गंवाए हैं तो 1930 पर कॉल करें या cybercrime.gov.in पर जाएं।",
    advice_lottery_prize: "जिस लॉटरी या प्रतियोगिता का टिकट आपने कभी खरीदा ही नहीं, उसे आप कभी जीत नहीं सकते। पैसे गंवाए हैं तो 1930 पर कॉल करें या cybercrime.gov.in पर जाएं।",
    advice_loan_app_harassment: "अनाधिकृत लोन ऐप्स को कभी भी अपनी कॉन्टैक्ट लिस्ट या गैलरी की अनुमति न दें। पैसे गंवाए हैं तो 1930 पर कॉल करें या cybercrime.gov.in पर जाएं।",
    advice_electricity_disconnection: "बिजली विभाग व्यक्तिगत नंबरों से तुरंत बिजली काटने की धमकी नहीं देता। केवल आधिकारिक पोर्टल पर जांचें। पैसे गंवाए हैं तो 1930 पर कॉल करें या cybercrime.gov.in पर जाएं।",
    advice_fake_customer_care: "गूगल सर्च पर मिले अज्ञात कस्टमर केयर नंबरों पर भरोसा न करें। केवल बैंक की आधिकारिक ऐप या वेबसाइट से नंबर लें। पैसे गंवाए हैं तो 1930 पर कॉल करें या cybercrime.gov.in पर जाएं।",
    advice_otp_call: "फोन पर किसी के साथ भी अपना ओटीपी, पासवर्ड या यूपीआई पिन कभी साझा न करें। पैसे गंवाए हैं तो 1930 पर कॉल करें या cybercrime.gov.in पर जाएं।",
    advice_sextortion: "घबराएं नहीं और कोई पैसा न दें। नंबर ब्लॉक करें, स्क्रीनशॉट साक्ष्य रखें और cybercrime.gov.in पर तुरंत रिपोर्ट करें। पैसे गंवाए हैं तो 1930 पर कॉल करें।",
    advice_other: "संदेह होने पर रुकें और आधिकारिक नंबरों से जांच करें। पैसे गंवाए हैं तो 1930 पर कॉल करें या cybercrime.gov.in पर जाएं।",

    // Licence expired
    licenceExpiredTitle: "लाइसेंस समाप्त हो गया है",
    licenceExpiredMsg: "सत्यचेक मूल्यांकन लाइसेंस की अवधि समाप्त हो चुकी है। कृपया नवीनीकरण के लिए अपने सेवा प्रदाता से संपर्क करें।",
    licencePollingMsg: "हर 30 सेकंड में सिस्टम स्थिति की जांच की जा रही है...",
  },
};

let currentLang = "en";

export function setLanguage(lang) {
  if (translations[lang]) {
    currentLang = lang;
    try {
      localStorage.setItem("satyacheck_lang", lang);
    } catch (e) {
      // storage blocked, fallback in-memory
    }
  }
}

export function getLanguage() {
  try {
    const saved = localStorage.getItem("satyacheck_lang");
    if (saved && translations[saved]) return saved;
  } catch (e) {}
  return currentLang;
}

export function t(key, params = {}) {
  const dict = translations[currentLang] || translations["en"];
  let str = dict[key] || translations["en"][key] || key;
  for (const [k, v] of Object.entries(params)) {
    str = str.replaceAll(`{${k}}`, v);
  }
  return str;
}
