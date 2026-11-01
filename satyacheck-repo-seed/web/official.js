// web/official.js – Official reporting portals card and advisories (Task F2).
import { getLanguage, t } from "./i18n.js";

// Bundled official resources so rendering does not require network roundtrip
export const OFFICIAL_PORTALS = [
  {
    id: "helpline-1930",
    name_en: "1930 Cyber Fraud Helpline",
    name_hi: "1930 साइबर अपराध हेल्पलाइन",
    url: "tel:1930",
    desc_en: "Immediate freeze on fraudulent bank transactions",
    desc_hi: "धोखाधड़ी वाले लेन-देन तुरंत रुकवाने हेतु कॉल करें",
    action_en: "📞 Call 1930",
    action_hi: "📞 1930 पर कॉल करें",
    for_loss: true,
    is_tel: true,
  },
  {
    id: "cybercrime-portal",
    name_en: "National Cybercrime Portal",
    name_hi: "राष्ट्रीय साइबर अपराध पोर्टल",
    url: "https://cybercrime.gov.in",
    desc_en: "Official complaint & police FIR online",
    desc_hi: "ऑनलाइन औपचारिक साइबर शिकायत या एफआईआर",
    action_en: "File FIR ↗",
    action_hi: "शिकायत दर्ज करें ↗",
    for_loss: true,
    is_tel: false,
  },
  {
    id: "chakshu-portal",
    name_en: "Chakshu (Sanchar Saathi)",
    name_hi: "चक्षु (संचार साथी)",
    url: "https://sancharsaathi.gov.in/sfc/",
    desc_en: "Report suspected spam, fraud calls and SMS",
    desc_hi: "संदिग्ध स्पैम कॉल, एसएमएस व संदेशों की रिपोर्ट करें",
    action_en: "Report Spam ↗",
    action_hi: "स्पैम रिपोर्ट करें ↗",
    for_loss: false,
    is_tel: false,
  },
];


/**
 * Render the "Also tell the authorities" card.
 *
 * @param {Object} options
 * @param {string} [options.verdict=""] - KNOWN_SCAM, SUSPICIOUS, etc.
 * @param {number|null} [options.amountLost=null] - Amount lost in INR
 * @param {boolean} [options.isSuccessScreen=false] - If rendered on report success screen
 * @returns {string} HTML string
 */
export function renderOfficialCard(options = {}) {
  const { verdict = "", amountLost = null, isSuccessScreen = false } = options;
  const lang = getLanguage();
  const isHi = lang === "hi";

  const hasLostMoney = amountLost !== null && Number(amountLost) > 0;
  const isKnownScam = verdict === "KNOWN_SCAM";

  // Reorder portals: put 1930 first if money lost or known scam
  let portals = [...OFFICIAL_PORTALS];
  if (hasLostMoney || isKnownScam) {
    portals.sort((a, b) => (b.id === "helpline-1930" ? 1 : 0) - (a.id === "helpline-1930" ? 1 : 0));
  } else {
    // Chakshu first for suspicious attempts where no money was lost
    portals.sort((a, b) => (b.id === "chakshu-portal" ? 1 : 0) - (a.id === "chakshu-portal" ? 1 : 0));
  }

  const title = isHi ? "अधिकारियों को भी सूचित करें" : "Also tell the authorities";
  const disclaimer = isHi
    ? "हम आपकी रिपोर्ट किसी को नहीं भेजते हैं। कृपया आधिकारिक वेबसाइट पर स्वयं शिकायत दर्ज करें।"
    : "We do not send your report to anyone. Please report on the official site yourself.";

  const portalItems = portals.map((p) => {
    const name = isHi ? p.name_hi : p.name_en;
    const desc = isHi ? p.desc_hi : p.desc_en;
    const action = isHi ? p.action_hi : p.action_en;
    const linkAttr = p.is_tel
      ? `href="${p.url}"`
      : `href="${p.url}" target="_blank" rel="noopener"`;

    return `
      <div class="official-item ${p.id === "helpline-1930" && (hasLostMoney || isKnownScam) ? "official-priority" : ""}">
        <div class="official-meta">
          <div class="official-name">${name}</div>
          <div class="official-desc">${desc}</div>
        </div>
        <a ${linkAttr} class="btn btn-official">
          ${action}
        </a>
      </div>
    `;
  }).join("");

  return `
    <div class="card official-card" id="official-authorities-card">
      <div class="official-header">
        <h4 class="official-title">🏛️ ${title}</h4>
      </div>
      <div class="official-disclaimer">
        ℹ️ ${disclaimer}
      </div>
      <div class="official-list">
        ${portalItems}
      </div>
    </div>
  `;
}

/**
 * Render hand-curated official advisories.
 * Completely hidden if array is empty.
 *
 * @param {Array} advisories
 * @returns {string} HTML string (or empty string if none)
 */
export function renderAdvisoriesCard(advisories = []) {
  if (!Array.isArray(advisories) || advisories.length === 0) {
    return "";
  }

  const lang = getLanguage();
  const isHi = lang === "hi";
  const title = isHi ? "आधिकारिक परामर्श व अलर्ट" : "Official Advisories & Warnings";

  const items = advisories.map((a) => {
    const itemTitle = isHi ? (a.title_hi || a.title_en) : a.title_en;
    return `
      <div class="advisory-item">
        <a href="${a.source_url}" target="_blank" rel="noopener" class="advisory-link">
          ${itemTitle}
        </a>
        <div class="advisory-meta">
          <span>${a.source_name || "Official"}</span> • <span>${a.date || ""}</span>
        </div>
      </div>
    `;
  }).join("");

  return `
    <div class="card advisories-card">
      <h4 class="advisories-title">📢 ${title}</h4>
      <div class="advisories-list">
        ${items}
      </div>
    </div>
  `;
}

