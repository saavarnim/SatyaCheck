// web/app.js – Vanilla JS ES module application logic per docs/07-frontend.md
import { translations, getLanguage, setLanguage, t } from "./i18n.js";
import {
  renderHeatmapView,
  updateMapLegend,
  renderClustersList,
} from "./heatmap.js";

// ── 25 Seeded Areas (Embedded per docs/07 to avoid extra latency) ───────────
const AREAS = [
  { pincode: "560102", locality: "HSR Layout", city: "Bengaluru", lat: 12.9116, lng: 77.6473 },
  { pincode: "560038", locality: "Indiranagar", city: "Bengaluru", lat: 12.9784, lng: 77.6408 },
  { pincode: "560034", locality: "Koramangala", city: "Bengaluru", lat: 12.9352, lng: 77.6245 },
  { pincode: "560066", locality: "Whitefield", city: "Bengaluru", lat: 12.9698, lng: 77.75 },
  { pincode: "560076", locality: "BTM Layout", city: "Bengaluru", lat: 12.9166, lng: 77.6101 },
  { pincode: "560011", locality: "Jayanagar", city: "Bengaluru", lat: 12.9299, lng: 77.5826 },
  { pincode: "560037", locality: "Marathahalli", city: "Bengaluru", lat: 12.9591, lng: 77.6974 },
  { pincode: "560103", locality: "Bellandur", city: "Bengaluru", lat: 12.926, lng: 77.6762 },
  { pincode: "560100", locality: "Electronic City", city: "Bengaluru", lat: 12.8452, lng: 77.6602 },
  { pincode: "560078", locality: "JP Nagar", city: "Bengaluru", lat: 12.9077, lng: 77.5851 },
  { pincode: "560003", locality: "Malleshwaram", city: "Bengaluru", lat: 13.0035, lng: 77.5709 },
  { pincode: "560010", locality: "Rajajinagar", city: "Bengaluru", lat: 12.9915, lng: 77.552 },
  { pincode: "560024", locality: "Hebbal", city: "Bengaluru", lat: 13.0358, lng: 77.597 },
  { pincode: "560064", locality: "Yelahanka", city: "Bengaluru", lat: 13.1007, lng: 77.5963 },
  { pincode: "560070", locality: "Banashankari", city: "Bengaluru", lat: 12.925, lng: 77.5468 },
  { pincode: "400050", locality: "Bandra West", city: "Mumbai", lat: 19.0596, lng: 72.8295 },
  { pincode: "110016", locality: "Hauz Khas", city: "Delhi", lat: 28.5494, lng: 77.2001 },
  { pincode: "500081", locality: "Madhapur", city: "Hyderabad", lat: 17.4486, lng: 78.3908 },
  { pincode: "600020", locality: "Adyar", city: "Chennai", lat: 13.0012, lng: 80.2565 },
  { pincode: "411014", locality: "Viman Nagar", city: "Pune", lat: 18.5679, lng: 73.9143 },
  { pincode: "700091", locality: "Salt Lake Sector V", city: "Kolkata", lat: 22.579, lng: 88.429 },
  { pincode: "380015", locality: "Satellite", city: "Ahmedabad", lat: 23.026, lng: 72.5085 },
  { pincode: "302017", locality: "Malviya Nagar", city: "Jaipur", lat: 26.857, lng: 75.808 },
  { pincode: "226010", locality: "Gomti Nagar", city: "Lucknow", lat: 26.854, lng: 80.999 },
  { pincode: "682030", locality: "Kakkanad", city: "Kochi", lat: 10.0159, lng: 76.3419 },
];

const SCAM_TYPES = [
  "digital-arrest", "fake-kyc-link", "upi-refund-qr",
  "investment-group", "courier-customs", "job-offer",
  "lottery-prize", "loan-app-harassment", "electricity-disconnection",
  "fake-customer-care", "otp-call", "sextortion", "other",
];

// ── Pseudonymous Device UUID (docs/07) ──────────────────────────────────────
function getDeviceUuid() {
  try {
    let id = localStorage.getItem("satyacheck_device_id");
    if (!id) {
      id = "dev_" + Math.random().toString(36).substring(2, 10) + Date.now().toString(36);
      localStorage.setItem("satyacheck_device_id", id);
    }
    return id;
  } catch (e) {
    return "dev_ephemeral_" + Math.random().toString(36).substring(2, 10);
  }
}

const DEVICE_ID = getDeviceUuid();

// ── Licence Polling State ───────────────────────────────────────────────────
let isLicenceExpired = false;
let licencePollInterval = null;

function showLicenceExpired() {
  isLicenceExpired = true;
  document.getElementById("licence-expired-overlay").classList.add("active");
  if (!licencePollInterval) {
    licencePollInterval = setInterval(pollLicenceStatus, 30000);
  }
}

function hideLicenceExpired() {
  isLicenceExpired = false;
  document.getElementById("licence-expired-overlay").classList.remove("active");
  if (licencePollInterval) {
    clearInterval(licencePollInterval);
    licencePollInterval = null;
  }
}

async function pollLicenceStatus() {
  try {
    const res = await fetch("/health");
    if (res.ok) {
      // test lookup route to confirm licence is valid
      const testRes = await fetch("/lookup?type=phone&value=1930");
      if (testRes.status !== 403) {
        hideLicenceExpired();
      }
    }
  } catch (e) {}
}

// ── Safe API Fetcher ────────────────────────────────────────────────────────
async function apiFetch(url, options = {}) {
  const headers = options.headers || {};
  headers["X-Device-Id"] = DEVICE_ID;
  options.headers = headers;

  const res = await fetch(url, options);
  if (res.status === 403) {
    try {
      const data = await res.clone().json();
      if (data && data.error === "LICENSE_EXPIRED") {
        showLicenceExpired();
      }
    } catch (e) {}
  }
  return res;
}

// ── Type Auto-Detection ─────────────────────────────────────────────────────
function detectIdentifierType(val) {
  const s = val.trim();
  if (!s) return "phone";
  if (s.includes("@")) return "upi";
  if (/^(https?:\/\/|[a-z0-9-]+\.[a-z]{2,})/i.test(s)) return "url";
  if (/^[A-Za-z]{3,6}$/.test(s)) return "sender_id";
  return "phone";
}

// ── DOM Translation Render ──────────────────────────────────────────────────
function renderTranslations() {
  const lang = getLanguage();
  document.documentElement.lang = lang;
  document.getElementById("txt-curr-lang").textContent = lang === "en" ? "हिन्दी" : "English";

  // Elements with data-i18n
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    el.textContent = t(key);
  });

  // Elements with data-i18n-ph (placeholder)
  document.querySelectorAll("[data-i18n-ph]").forEach((el) => {
    const key = el.getAttribute("data-i18n-ph");
    el.setAttribute("placeholder", t(key));
  });

  renderScamAdviceDirectory();

  // If map clusters were loaded, re-render map legend and cluster list with new language
  if (lastLoadedClusters && lastLoadedClusters.length > 0) {
    renderFilteredMap();
  }
}

function renderScamAdviceDirectory() {
  const container = document.getElementById("scam-advice-directory");
  if (!container) return;

  container.innerHTML = SCAM_TYPES.map((type) => {
    const typeLabelKey = "scam_" + type.replaceAll("-", "_");
    const adviceKey = "advice_" + type.replaceAll("-", "_");
    return `
      <div class="card" style="margin-bottom: 12px; padding: 14px;">
        <h4 style="font-size: 0.95rem; font-weight: 700; color: var(--primary); margin-bottom: 4px;">
          ${t(typeLabelKey)}
        </h4>
        <p style="font-size: 0.88rem; color: #334155; line-height: 1.5;">
          ${t(adviceKey)}
        </p>
      </div>
    `;
  }).join("");
}

// ── Routing ─────────────────────────────────────────────────────────────────
const ROUTES = ["check", "report", "map", "alerts", "about"];

function navigateTo(route) {
  if (!ROUTES.includes(route)) route = "check";
  window.location.hash = `#/${route}`;

  // Update view visibility
  ROUTES.forEach((r) => {
    const sec = document.getElementById(`view-${r}`);
    if (sec) sec.classList.toggle("active", r === route);
  });

  // Update navigation link highlights
  document.querySelectorAll(".desktop-nav a, .bottom-nav-item").forEach((el) => {
    const href = el.getAttribute("href") || "";
    const active = href.includes(route);
    el.classList.toggle("active", active);
  });

  window.scrollTo(0, 0);

  // Trigger view data loaders
  if (route === "map") loadMapData();
  if (route === "alerts") loadAlertsData();
}

window.addEventListener("hashchange", () => {
  const hash = window.location.hash.replace("#/", "");
  navigateTo(hash);
});

// ── Check View Logic ────────────────────────────────────────────────────────
let checkSelectedType = "auto";

function setupCheckView() {
  const input = document.getElementById("input-check-value");
  const chips = document.querySelectorAll("#check-type-chips .chip");
  const form = document.getElementById("form-check");
  const btn = document.getElementById("btn-submit-check");

  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      chips.forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      checkSelectedType = chip.getAttribute("data-type");
    });
  });

  input.addEventListener("input", () => {
    if (checkSelectedType === "auto") {
      const detected = detectIdentifierType(input.value);
      chips.forEach((c) => {
        if (c.getAttribute("data-type") === detected) {
          c.classList.add("active");
        } else if (c.getAttribute("data-type") !== "auto") {
          c.classList.remove("active");
        }
      });
    }
  });

  let isChecking = false;

  async function executeCheck() {
    if (isChecking) return;
    const val = input.value.trim();
    if (!val) return;

    let type = checkSelectedType;
    if (type === "auto") type = detectIdentifierType(val);

    isChecking = true;
    btn.disabled = true;
    btn.innerHTML = `⏳ <span style="margin-left: 6px;">${t("checkingBtn")}</span>`;

    try {
      const res = await apiFetch(`/lookup?type=${type}&value=${encodeURIComponent(val)}`);
      const data = await res.json();
      renderLookupResult(data, type, val);
    } catch (e) {
      alert("Network error checking identifier.");
    } finally {
      isChecking = false;
      btn.disabled = false;
      btn.innerHTML = `🔍 <span data-i18n="checkButton" style="margin-left: 6px;">${t("checkButton")}</span>`;
    }
  }

  form.addEventListener("submit", (e) => {
    if (e && e.preventDefault) e.preventDefault();
    executeCheck();
  });

  if (btn) {
    btn.addEventListener("click", (e) => {
      if (e && e.preventDefault) e.preventDefault();
      executeCheck();
    });
  }
}

function renderLookupResult(data, type, rawValue) {
  const container = document.getElementById("check-result-container");
  container.style.display = "block";

  if (data.error) {
    let help = "Please enter a valid phone number, UPI ID, link or SMS sender.";
    if (type === "phone") {
      help = "Please enter a valid 10-digit Indian phone number starting with 6-9 (e.g. +91 98765 43210) or toll-free (1800/1860).";
    } else if (type === "upi") {
      help = "Please enter a valid UPI ID (e.g. username@okhdfcbank).";
    } else if (type === "url") {
      help = "Please enter a valid web link with domain (e.g. secure-kyc.in).";
    } else if (type === "sender_id") {
      help = "SMS Sender ID must be 3 to 6 uppercase letters (e.g. HDFCBK).";
    }
    container.innerHTML = `
      <div class="advice-box" style="border-left: 4px solid var(--verdict-known); margin-top: 20px;">
        <h4 style="color: var(--verdict-known); margin-bottom: 6px;">Invalid Format for ${type.toUpperCase()}</h4>
        <p style="font-size: 0.95rem; color: var(--text-main);">${help}</p>
      </div>
    `;
    return;
  }

  const verdict = data.verdict || "NO_REPORTS";
  const displayVal = data.display_value || rawValue;
  const reports = data.report_count || 0;
  const distinct = data.distinct_reporters || 0;

  // Explanation line
  let explanation = "";
  if (verdict === "VERIFIED_BUSINESS") {
    explanation = t("verifiedDesc");
  } else if (verdict === "NO_REPORTS") {
    explanation = t("noReportsDesc");
  } else if (distinct > 1) {
    explanation = t("reportedByCount", { count: distinct, reports: reports });
  } else {
    explanation = t("reportedBySingular", { reports: reports });
  }

  // Recommended action text
  const whatToDo = t(`whatToDo_${verdict}`) || t("whatToDo_NO_REPORTS");

  // Dispute banner if active challenge
  const challengedBanner = data.challenged
    ? `<div style="background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 10px; margin-bottom: 12px; font-size: 0.85rem; color: #b45309;">
         ⚖️ ${t("challengedNotice")}
       </div>`
    : "";

  container.innerHTML = `
    <div class="card result-card verdict-${verdict}">
      <div class="verdict-badge badge-${verdict}">
        ${t(`verdict_${verdict}`)}
      </div>
      <div class="display-value-box">${escapeHtml(displayVal)}</div>
      ${challengedBanner}
      <p class="explanation-text">${explanation}</p>

      <div class="advice-box">
        <h4>💡 ${t("whatToDoTitle")}</h4>
        <p>${whatToDo}</p>
      </div>

      <div style="margin-top: 14px; font-size: 0.85rem;">
        <a href="#/about" style="color: var(--primary); text-decoration: underline;">
          ${t("disputeLink")}
        </a>
      </div>

      <!-- Expandable Technical Details -->
      <button type="button" class="tech-details-toggle" id="btn-toggle-tech">
        <span>${t("techDetailsTitle")}</span>
        <span id="tech-toggle-icon">▼</span>
      </button>

      <div class="tech-details-content" id="tech-details-box">
        <table class="tech-table">
          <tr><td>${t("detailIdentifier")}</td><td>${escapeHtml(type)}: ${escapeHtml(displayVal)}</td></tr>
          <tr><td>${t("detailVerdict")}</td><td>${escapeHtml(verdict)}</td></tr>
          <tr><td>${t("detailDistinctReporters")}</td><td>${distinct}</td></tr>
          <tr><td>${t("detailTotalReports")}</td><td>${reports}</td></tr>
          <tr><td>${t("detailFirstSeen")}</td><td>${data.first_seen ? data.first_seen.split("T")[0] : t("noneText")}</td></tr>
          <tr><td>${t("detailLastSeen")}</td><td>${data.last_seen ? data.last_seen.split("T")[0] : t("noneText")}</td></tr>
          <tr><td>${t("detailScamType")}</td><td>${escapeHtml(data.scam_type || "other")}</td></tr>
          <tr><td>${t("detailChallenged")}</td><td>${data.challenged ? "True (Under Review)" : "False"}</td></tr>
        </table>
      </div>
    </div>
  `;

  document.getElementById("btn-toggle-tech").addEventListener("click", () => {
    const box = document.getElementById("tech-details-box");
    const icon = document.getElementById("tech-toggle-icon");
    const isOpen = box.classList.toggle("open");
    icon.textContent = isOpen ? "▲" : "▼";
  });
}

// ── Report Flow Logic ───────────────────────────────────────────────────────
let reportSelectedChannel = "phone call";
let reportSelectedScamType = "digital-arrest";
let reportSelectedTime = "now";

function setupReportView() {
  // Populate area dropdown
  const areaSelect = document.getElementById("report-pincode");
  AREAS.forEach((a) => {
    const opt = document.createElement("option");
    opt.value = a.pincode;
    opt.textContent = `${a.locality}, ${a.city} (${a.pincode})`;
    areaSelect.appendChild(opt);
  });

  // Channel grid selector
  document.querySelectorAll("#grid-channels .select-card").forEach((card) => {
    card.addEventListener("click", () => {
      document.querySelectorAll("#grid-channels .select-card").forEach((c) => c.classList.remove("active"));
      card.classList.add("active");
      reportSelectedChannel = card.getAttribute("data-val");
    });
  });

  // Scam type grid selector
  document.querySelectorAll("#grid-scam-types .select-card").forEach((card) => {
    card.addEventListener("click", () => {
      document.querySelectorAll("#grid-scam-types .select-card").forEach((c) => c.classList.remove("active"));
      card.classList.add("active");
      reportSelectedScamType = card.getAttribute("data-val");
    });
  });

  // Time chips
  document.querySelectorAll("#report-time-chips .chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      document.querySelectorAll("#report-time-chips .chip").forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      reportSelectedTime = chip.getAttribute("data-time");
    });
  });

  // Identifier type & input
  const idInput = document.getElementById("report-identifier-value");
  const idTypeSelect = document.getElementById("report-identifier-type");
  let reportTypeManuallySelected = false;

  idTypeSelect.addEventListener("change", () => {
    reportTypeManuallySelected = true;
  });

  idInput.addEventListener("input", () => {
    if (!reportTypeManuallySelected) {
      const detected = detectIdentifierType(idInput.value);
      idTypeSelect.value = detected;
    }
  });

  function validateReportIdentifier(type, val) {
    if (!val) return "Identifier value cannot be empty.";
    if (type === "phone") {
      const digits = val.replace(/\D/g, "");
      if (/^(1800|1860)\d{4,7}$/.test(digits) || /^19\d{2}$/.test(digits)) return null;
      let d = digits;
      if (d.length === 12 && d.startsWith("91")) d = d.substring(2);
      else if (d.length === 11 && d.startsWith("0")) d = d.substring(1);
      if (d.length !== 10) return "Phone number must be exactly 10 digits (e.g. +91 98765 43210).";
      if (!"23456789".includes(d[0])) return "Phone number must start with digits 2 to 9.";
      if (new Set(d).size === 1) return "Phone number cannot be all repeated digits.";
      if (d === "1234567890" || d === "0123456789") return "Sequential numbers like 1234567890 are not accepted.";
      return null;
    }
    if (type === "upi") {
      const clean = val.toLowerCase().replace(/\s/g, "");
      if (!/^[a-z0-9._-]{2,64}@[a-z][a-z0-9]{1,32}$/.test(clean)) {
        return "Please enter a valid UPI ID with bank handle (e.g. name@okaxis).";
      }
      return null;
    }
    if (type === "url") {
      if (!/[a-z0-9-]+\.[a-z]{2,}/i.test(val)) {
        return "Please enter a valid website link or domain (e.g. secure-kyc.in).";
      }
      return null;
    }
    if (type === "sender_id") {
      const clean = val.trim().replace(/^.*-/, "");
      if (!/^[A-Za-z]{3,6}$/.test(clean)) {
        return "SMS Sender ID must be 3 to 6 letters (e.g. HDFCBK or VM-SBIINB).";
      }
      return null;
    }
    return null;
  }

  // Evidence checkbox
  const screenshotCheck = document.getElementById("report-has-screenshot");

  // Form submit
  const form = document.getElementById("form-report");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const idType = idTypeSelect.value;
    const idVal = idInput.value.trim();
    const pincode = areaSelect.value;
    const note = document.getElementById("report-note").value.trim();
    const amountVal = document.getElementById("report-amount").value;
    const hasScreenshot = Boolean(screenshotCheck && screenshotCheck.checked);

    if (!idVal || !pincode) {
      alert("Please enter the identifier and select your area.");
      return;
    }

    const formatError = validateReportIdentifier(idType, idVal);
    if (formatError) {
      alert(formatError);
      idInput.focus();
      return;
    }

    // Occurred at ISO timestamp based on selected time chip
    let occurredAt = null;
    if (reportSelectedTime === "today") {
      const d = new Date();
      d.setHours(d.getHours() - 3);
      occurredAt = d.toISOString();
    } else if (reportSelectedTime === "yesterday") {
      const d = new Date();
      d.setDate(d.getDate() - 1);
      occurredAt = d.toISOString();
    }

    const reportUid = "REP-" + Math.random().toString(36).substring(2, 10).toUpperCase();
    const payload = {
      report_id: reportUid,
      identifier_type: idType,
      identifier_value: idVal,
      channel: reportSelectedChannel,
      scam_type: reportSelectedScamType,
      pincode: pincode,
      occurred_at: occurredAt,
      note: note,
      has_screenshot: hasScreenshot,
      amount_lost_inr: amountVal ? parseFloat(amountVal) : null,
      reporter_id: DEVICE_ID,
    };

    const submitBtn = document.getElementById("btn-submit-report");
    submitBtn.disabled = true;
    submitBtn.textContent = t("submittingBtn");

    try {
      const res = await apiFetch("/reports", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.status === 201) {
        const data = await res.json();
        form.style.display = "none";
        const successBox = document.getElementById("report-success-container");
        successBox.style.display = "block";
        const reportIdEl = document.getElementById("res-report-id");
        if (reportIdEl) {
          reportIdEl.textContent = data.report_id || payload.report_id;
        }
        const caseIdEl = document.getElementById("res-case-id");
        if (caseIdEl) {
          caseIdEl.textContent = data.case_id || "RECORDED";
        }
      } else {
        const err = await res.json().catch(() => ({}));
        let msg = "Submission failed. Please check your inputs.";
        if (err.error === "INVALID_REQUEST") {
          msg = "Invalid format for " + idType.toUpperCase() + ". Please check your inputs and area.";
        } else if (err.error === "SLOW_DOWN") {
          msg = "Rate limit reached. Please wait a moment before reporting again.";
        }
        alert(msg);
      }
    } catch (e) {
      alert("Network error submitting report.");
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = t("submitReportBtn");
    }
  });

  // Report another button
  document.getElementById("btn-report-another").addEventListener("click", () => {
    form.reset();
    reportTypeManuallySelected = false;
    const reportIdEl = document.getElementById("res-report-id");
    if (reportIdEl) reportIdEl.textContent = "";
    const caseIdEl = document.getElementById("res-case-id");
    if (caseIdEl) caseIdEl.textContent = "";

    // Reset default grid and chip selections
    reportSelectedChannel = "phone call";
    document.querySelectorAll("#grid-channels .select-card").forEach((c, idx) => {
      c.classList.toggle("active", idx === 0);
    });
    reportSelectedScamType = "digital-arrest";
    document.querySelectorAll("#grid-scam-types .select-card").forEach((c, idx) => {
      c.classList.toggle("active", idx === 0);
    });
    reportSelectedTime = "now";
    document.querySelectorAll("#report-time-chips .chip").forEach((c, idx) => {
      c.classList.toggle("active", idx === 0);
    });

    form.style.display = "block";
    document.getElementById("report-success-container").style.display = "none";
  });
}

// ── Map View Logic ──────────────────────────────────────────────────────────
let leafletMap = null;
let lastLoadedClusters = [];
let currentMapDays = 7;
let currentMapFilterCriteria = {
  search: "",
  scamType: "",
  severity: "",
  city: "all",
};
let currentMapListingTab = "all";

function renderFilteredMap() {
  if (window.L && leafletMap) {
    renderHeatmapView(
      leafletMap,
      lastLoadedClusters,
      AREAS,
      getLanguage(),
      currentMapFilterCriteria,
      currentMapListingTab
    );
  } else {
    renderClustersList(
      lastLoadedClusters,
      AREAS,
      getLanguage(),
      null,
      currentMapListingTab
    );
  }
}

function setupMapView() {
  // Time window chips (24 hours, 3 days, 7 days)
  const chipsContainer = document.getElementById("map-time-chips");
  if (chipsContainer) {
    chipsContainer.addEventListener("click", (e) => {
      const chip = e.target.closest(".chip");
      if (!chip) return;
      const days = parseInt(chip.getAttribute("data-days"), 10);
      if (isNaN(days) || days > 7) return; // Never offer more than 7

      chipsContainer.querySelectorAll(".chip").forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      currentMapDays = days;
      loadMapData();
    });
  }

  // Radius select
  const radiusSelect = document.getElementById("map-filter-radius");
  if (radiusSelect) {
    radiusSelect.addEventListener("change", loadMapData);
  }

  // Live search input
  const searchInput = document.getElementById("map-search-input");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      currentMapFilterCriteria.search = e.target.value;
      renderFilteredMap();
    });
  }

  // Scam type filter
  const scamSelect = document.getElementById("map-filter-scam-type");
  if (scamSelect) {
    scamSelect.addEventListener("change", (e) => {
      currentMapFilterCriteria.scamType = e.target.value;
      renderFilteredMap();
    });
  }

  // Severity filter
  const sevSelect = document.getElementById("map-filter-severity");
  if (sevSelect) {
    sevSelect.addEventListener("change", (e) => {
      currentMapFilterCriteria.severity = e.target.value;
      renderFilteredMap();
    });
  }

  // City quick jump chips
  const cityChipsContainer = document.getElementById("map-city-chips");
  if (cityChipsContainer) {
    cityChipsContainer.addEventListener("click", (e) => {
      const chip = e.target.closest(".chip");
      if (!chip) return;
      const city = chip.getAttribute("data-city") || "all";

      cityChipsContainer.querySelectorAll(".chip").forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");
      currentMapFilterCriteria.city = city;

      if (city !== "all" && leafletMap) {
        const cityArea = AREAS.find((a) => a.city === city);
        if (cityArea && cityArea.lat != null && cityArea.lng != null) {
          leafletMap.flyTo([cityArea.lat, cityArea.lng], 12, {
            animate: true,
            duration: 1.1,
            easeLinearity: 0.25,
          });
        }
      }
      renderFilteredMap();
    });
  }

  // Reset / Fit All view button
  const fitAllBtn = document.getElementById("btn-map-fit-all");
  if (fitAllBtn) {
    fitAllBtn.addEventListener("click", () => {
      currentMapFilterCriteria = { search: "", scamType: "", severity: "", city: "all" };
      if (searchInput) searchInput.value = "";
      if (scamSelect) scamSelect.value = "";
      if (sevSelect) sevSelect.value = "";
      if (cityChipsContainer) {
        cityChipsContainer.querySelectorAll(".chip").forEach((c, idx) => c.classList.toggle("active", idx === 0));
      }

      renderFilteredMap();

      if (leafletMap) {
        const bounds = AREAS.map((a) => [a.lat, a.lng]);
        leafletMap.fitBounds(bounds, { padding: [35, 35], maxZoom: 12 });
      }
    });
  }

  // Listing filter tabs (All Localities | Active Hotspots | Calm Areas)
  const tabFilterContainer = document.getElementById("cluster-tab-filters");
  if (tabFilterContainer) {
    tabFilterContainer.addEventListener("click", (e) => {
      const tabBtn = e.target.closest(".tab-btn");
      if (!tabBtn) return;
      tabFilterContainer.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      tabBtn.classList.add("active");
      currentMapListingTab = tabBtn.getAttribute("data-tab") || "all";
      renderFilteredMap();
    });
  }
}

async function loadMapData() {
  const mapContainer = document.getElementById("leaflet-map");
  const blockedNotice = document.getElementById("map-blocked-message");

  // Check if map library is blocked
  if (!window.L) {
    if (mapContainer) mapContainer.style.display = "none";
    if (blockedNotice) blockedNotice.style.display = "flex";
  } else {
    if (mapContainer) mapContainer.style.display = "block";
    if (blockedNotice) blockedNotice.style.display = "none";

    if (!leafletMap) {
      leafletMap = L.map("leaflet-map").setView([12.9716, 77.5946], 11);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18,
        attribution: "© OpenStreetMap contributors",
      }).addTo(leafletMap);
    }

    setTimeout(() => leafletMap.invalidateSize(), 150);
  }

  const radius = document.getElementById("map-filter-radius")?.value || "";
  let url = `/map?days=${currentMapDays}`;
  if (radius) url += `&radius_km=${radius}`;

  const listContainer = document.getElementById("map-clusters-list");
  if (listContainer) {
    listContainer.innerHTML = `<p style="color: var(--text-muted); font-size: 0.88rem;">${t("loadingText") || "Loading map data..."}</p>`;
  }

  try {
    const res = await apiFetch(url);
    const data = await res.json();
    lastLoadedClusters = data.clusters || [];
    renderFilteredMap();
  } catch (e) {
    if (listContainer) {
      listContainer.innerHTML = `<p style="color: #b91c1c; font-size: 0.88rem;">Error loading map clusters.</p>`;
    }
  }
}

// ── Alerts View Logic ───────────────────────────────────────────────────────
async function loadAlertsData() {
  const container = document.getElementById("alerts-list-container");
  container.innerHTML = `<p style="color: var(--text-muted); font-size: 0.88rem;">Loading alerts...</p>`;

  try {
    const res = await apiFetch("/alerts");
    const data = await res.json();
    const alerts = data.alerts || [];

    if (alerts.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 24px; color: var(--text-muted);">
          <div style="font-size: 2rem; margin-bottom: 8px;">🛡️</div>
          <p>${t("noAlertsActive")}</p>
        </div>
      `;
      return;
    }

    container.innerHTML = alerts.map((a) => {
      const isSpike = a.type === "SPIKE";
      const tagClass = isSpike ? "tag-SPIKE" : "tag-NEW_TYPE";
      const title = isSpike ? t("alertSpikeTitle") : t("alertNewTypeTitle");
      const desc = isSpike
        ? t("alertSpikeDesc", { count: a.count, baseline: a.baseline_per_day })
        : t("alertNewTypeDesc", { type: a.scam_type });

      // Find locality name for pincode
      const area = AREAS.find((ar) => ar.pincode === a.pincode);
      const locText = area ? `${area.locality}, ${area.city}` : a.pincode;

      return `
        <div class="card alert-card alert-${a.type}">
          <span class="alert-tag ${tagClass}">${a.type}</span>
          <h4 style="font-size: 1rem; font-weight: 700; margin-bottom: 4px;">
            ${title} • ${escapeHtml(locText)}
          </h4>
          <p style="font-size: 0.88rem; color: #475569; margin-bottom: 8px;">${desc}</p>
          <div style="font-size: 0.78rem; color: var(--text-muted);">
            Monitored window: ${escapeHtml(a.window)}
          </div>
        </div>
      `;
    }).join("");
  } catch (e) {
    container.innerHTML = "<p>Error loading alerts.</p>";
  }
}

// ── About & Dispute Flow Logic ──────────────────────────────────────────────
function setupAboutView() {
  const form = document.getElementById("form-dispute");
  const feedback = document.getElementById("dispute-feedback");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const idType = document.getElementById("dispute-identifier-type").value;
    const idVal = document.getElementById("dispute-identifier-value").value.trim();
    const name = document.getElementById("dispute-name").value.trim();
    const email = document.getElementById("dispute-email").value.trim();
    const proof = document.getElementById("dispute-proof").value.trim();

    const btn = document.getElementById("btn-submit-dispute");
    btn.disabled = true;

    try {
      const res = await apiFetch("/challenges", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          identifier_type: idType,
          identifier_value: idVal,
          claimant_name: name,
          contact_email: email,
          proof_note: proof,
        }),
      });

      if (res.status === 201) {
        const data = await res.json();
        feedback.style.display = "block";
        feedback.style.background = "#ecfdf5";
        feedback.style.color = "#065f46";
        feedback.textContent = t("disputeSuccess", { id: data.challenge_id });
        form.reset();
      } else if (res.status === 409) {
        feedback.style.display = "block";
        feedback.style.background = "#fef2f2";
        feedback.style.color = "#991b1b";
        feedback.textContent = "A recently rejected dispute is in cooldown. Please retry later.";
      } else {
        feedback.style.display = "block";
        feedback.style.background = "#fef2f2";
        feedback.style.color = "#991b1b";
        feedback.textContent = "Dispute submission failed. Please verify your details.";
      }
    } catch (e) {
      alert("Network error submitting dispute.");
    } finally {
      btn.disabled = false;
    }
  });
}

// ── Utility: Escape HTML ────────────────────────────────────────────────────
function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ── Initialisation ──────────────────────────────────────────────────────────
window.addEventListener("DOMContentLoaded", () => {
  // Language toggle button listener
  document.getElementById("btn-lang-toggle").addEventListener("click", () => {
    const nextLang = getLanguage() === "en" ? "hi" : "en";
    setLanguage(nextLang);
    renderTranslations();
  });

  renderTranslations();
  setupCheckView();
  setupReportView();
  setupMapView();
  setupAboutView();

  // Route according to initial hash
  const initialHash = window.location.hash.replace("#/", "");
  navigateTo(initialHash || "check");
});
