// web/explain.js – Plain-language explanation card component (Task F1).
import { t, getLanguage } from "./i18n.js";

/**
 * Render the "What does this mean?" card.
 *
 * @param {Object} explain - Structured explain payload from GET /lookup
 * @param {string} [scamType="other"] - Primary scam type
 * @returns {string} HTML string
 */
export function renderExplainCard(explain, scamType = "other") {
  if (!explain) return "";

  const level = explain.level || "low";
  const confText = t(`explain_conf_${level}`);
  const headline = t(explain.headline_key);
  const notMeaning = t(explain.not_meaning_key);

  const cleanScam = (scamType || "other").replace(/-/g, "_").toLowerCase();
  const howScamWorks = t(`how_scam_${cleanScam}`) || t("how_scam_other");

  // 3-step confidence bar: low, medium, high
  const levels = ["low", "medium", "high"];
  const currentIdx = Math.max(0, levels.indexOf(level));

  const barHtml = `
    <div class="explain-conf-wrapper">
      <div class="explain-conf-header">
        <span class="explain-conf-title">${t("explain_confidence_label")}</span>
        <span class="explain-conf-badge conf-${level}">${confText}</span>
      </div>
      <div class="explain-conf-bar" role="progressbar" aria-valuenow="${currentIdx + 1}" aria-valuemin="1" aria-valuemax="3" aria-label="${t("explain_confidence_label")} ${confText}">
        <div class="conf-seg ${currentIdx >= 0 ? "active" : ""} conf-seg-low"></div>
        <div class="conf-seg ${currentIdx >= 1 ? "active" : ""} conf-seg-medium"></div>
        <div class="conf-seg ${currentIdx >= 2 ? "active" : ""} conf-seg-high"></div>
      </div>
    </div>
  `;

  // Why points
  const whyItems = (explain.why || [])
    .map((item) => `<li>${t(item.key, { n: item.n })}</li>`)
    .join("");

  // Do actions
  const doItems = (explain.do || [])
    .map((actionKey) => `<li>${t(actionKey)}</li>`)
    .join("");

  // Speech support
  const hasSpeech = typeof window !== "undefined" && "speechSynthesis" in window;
  const listenBtnHtml = hasSpeech
    ? `<button type="button" class="btn btn-listen" id="btn-explain-listen" aria-label="Listen to explanation">
         ${t("explain_listen_btn")}
       </button>`
    : "";

  return `
    <div class="card explain-card" id="explain-card">
      <div class="explain-card-top">
        <h3 class="explain-card-title">${t("explain_card_title")}</h3>
        ${listenBtnHtml}
      </div>

      <!-- Part 1: Meaning -->
      <div class="explain-part">
        <h4 class="explain-part-heading">${t("explain_part_meaning")}</h4>
        <p class="explain-headline">${headline}</p>
        ${barHtml}
        <div class="explain-not-meaning">
          <strong>${t("explain_not_meaning_prefix")}</strong> ${notMeaning}
        </div>
      </div>

      <!-- Part 2: Why we say this -->
      <div class="explain-part">
        <h4 class="explain-part-heading">${t("explain_part_why")}</h4>
        <ul class="explain-list">
          ${whyItems}
        </ul>
        <div class="explain-how-works">
          <div class="explain-how-works-title">💡 ${t("explain_how_scam_works_title")}</div>
          <p class="explain-how-works-body">${howScamWorks}</p>
        </div>
      </div>

      <!-- Part 3: What to do now -->
      <div class="explain-part">
        <h4 class="explain-part-heading">${t("explain_part_do")}</h4>
        <ul class="explain-list explain-do-list">
          ${doItems}
        </ul>
      </div>
    </div>
  `;
}

/**
 * Wire up the SpeechSynthesis "Listen" / "Stop" button.
 *
 * @param {Object} explain
 * @param {string} [scamType="other"]
 */
export function setupExplainSpeech(explain, scamType = "other") {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
  const btn = document.getElementById("btn-explain-listen");
  if (!btn || !explain) return;

  btn.onclick = () => {
    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
      btn.textContent = t("explain_listen_btn");
      return;
    }

    const lang = getLanguage();
    const cleanScam = (scamType || "other").replace(/-/g, "_").toLowerCase();
    const howScamWorks = (t(`how_scam_${cleanScam}`) || t("how_scam_other")).replace(/<br\s*\/?>/gi, " ");

    const speechParts = [
      t("explain_card_title"),
      t("explain_part_meaning"),
      t(explain.headline_key),
      t("explain_confidence_label") + " " + t(`explain_conf_${explain.level || "low"}`),
      t("explain_not_meaning_prefix") + " " + t(explain.not_meaning_key),
      t("explain_part_why"),
      ...(explain.why || []).map((w) => t(w.key, { n: w.n })),
      t("explain_how_scam_works_title") + " " + howScamWorks,
      t("explain_part_do"),
      ...(explain.do || []).map((d) => t(d)),
    ];

    const utterance = new SpeechSynthesisUtterance(speechParts.join(". "));
    utterance.lang = lang === "hi" ? "hi-IN" : "en-IN";
    utterance.rate = 0.95;

    utterance.onend = () => {
      btn.textContent = t("explain_listen_btn");
    };
    utterance.onerror = () => {
      btn.textContent = t("explain_listen_btn");
    };

    btn.textContent = t("explain_stop_btn");
    window.speechSynthesis.speak(utterance);
  };
}
