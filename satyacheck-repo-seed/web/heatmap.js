// web/heatmap.js – Leaflet Heatmap Layer, Filter Engine & UX Zoom Navigation
// Implements:
// - Pinned Leaflet.heat 0.2.0 integration with gradient: yellow -> orange -> red
// - Fallback 3 concentric translucent circles (r, 0.6r, 0.3r) in severity colour
// - Numbered markers with tap popups & text badges (A few reports / Many / Very many)
// - Faint green dots for areas with no reports (Calm)
// - Bilingual bottom-left legend (CRIT >= 10, HIGH 5-9, MED < 5, Green: no reports)
// - Multi-dimensional filtering: Search, Scam Type, Severity, City
// - Seamless UX: Clicking any locality smoothly flies to it on the map and opens the popup
// - Complete listing of all localities (both active hotspots & calm areas with quick report action)

import { t, getLanguage } from "./i18n.js";

// Specific severity colors
export const SEV_COLORS = {
  CRIT: "#D32F2F", // Red (10 or more)
  HIGH: "#F57C00", // Orange (5-9)
  MED: "#F2B01E",  // Amber (below 5)
  ZERO: "#10b981", // Faint green for areas with no reports
};

// Plain-words naming & actionable safety advice for each scam type
export const SCAM_DETAILS = {
  "digital-arrest": {
    en: "Digital Arrest",
    hi: "डिजिटल अरेस्ट",
    advice_en: "Police or CBI never conduct court trials or make arrests over video calls.",
    advice_hi: "पुलिस या जांच एजेंसियां कभी वीडियो कॉल पर कोर्ट या गिरफ्तारी नहीं करती हैं।",
  },
  "fake-kyc-link": {
    en: "Fake KYC Link",
    hi: "फर्जी केवाईसी लिंक",
    advice_en: "Banks never ask you to update KYC via SMS or WhatsApp links.",
    advice_hi: "बैंक कभी भी एसएमएस या व्हाट्सएप लिंक से केवाईसी अपडेट नहीं मांगते।",
  },
  "upi-refund-qr": {
    en: "UPI Refund QR",
    hi: "यूपीआई रिफंड क्यूआर",
    advice_en: "You never need to enter your UPI PIN or scan a QR code to receive money.",
    advice_hi: "पैसे प्राप्त करने के लिए कभी भी पिन दर्ज करने या क्यूआर स्कैन करने की आवश्यकता नहीं होती।",
  },
  "investment-group": {
    en: "Investment Scam",
    hi: "फर्जी निवेश ग्रुप",
    advice_en: "Beware of WhatsApp or Telegram groups promising guaranteed stock returns.",
    advice_hi: "व्हाट्सएप या टेलीग्राम पर भारी मुनाफे का दावा करने वाले ग्रुपों से सावधान रहें।",
  },
  "courier-customs": {
    en: "Courier / Customs",
    hi: "कूरियर / कस्टम्स",
    advice_en: "Customs officers never demand parcel clearance fees into personal bank accounts.",
    advice_hi: "कस्टम अधिकारी कभी भी व्यक्तिगत बैंक खातों में पार्सल शुल्क नहीं मांगते।",
  },
  "job-offer": {
    en: "Job Offer Scam",
    hi: "फर्जी नौकरी का झांसा",
    advice_en: "Legitimate employers never demand registration fees or paid task deposits.",
    advice_hi: "वास्तविक कंपनियां कभी नौकरी के बदले कोई शुल्क या टास्क डिपॉजिट नहीं मांगतीं।",
  },
  "lottery-prize": {
    en: "Lottery / Prize",
    hi: "लॉटरी / इनाम स्कैम",
    advice_en: "You cannot win a lottery you never entered; never pay fees to claim prizes.",
    advice_hi: "जिस लॉटरी का टिकट नहीं खरीदा वह नहीं जीती जा सकती; इनाम के लिए कोई शुल्क न दें।",
  },
  "loan-app-harassment": {
    en: "Loan App Harassment",
    hi: "लोन ऐप उत्पीड़न",
    advice_en: "Borrow only from RBI-registered lenders; report blackmail to helpline 1930.",
    advice_hi: "केवल आरबीआई-मान्यता प्राप्त ऐप से ही ऋण लें; उत्पीड़न की तुरंत 1930 पर शिकायत करें।",
  },
  "electricity-disconnection": {
    en: "Electricity Threat",
    hi: "बिजली बिल डिस्कनेक्शन",
    advice_en: "Power boards never send disconnection threats from personal 10-digit mobile numbers.",
    advice_hi: "बिजली विभाग व्यक्तिगत मोबाइल नंबरों से कनेक्शन काटने की धमकी नहीं भेजता।",
  },
  "fake-customer-care": {
    en: "Fake Customer Care",
    hi: "फर्जी कस्टमर केयर",
    advice_en: "Always find customer support numbers on official apps or websites, not search ads.",
    advice_hi: "हेल्पलाइन नंबर हमेशा आधिकारिक ऐप या वेबसाइट से ही लें, सर्च विज्ञापनों से नहीं।",
  },
  "otp-call": {
    en: "OTP / PIN Call",
    hi: "ओटीपी / पिन कॉल",
    advice_en: "Never share OTPs, CVV, or passwords with anyone over a call or message.",
    advice_hi: "कॉल या मैसेज पर कभी भी अपना ओटीपी, पासवर्ड या पिन किसी से साझा न करें।",
  },
  "sextortion": {
    en: "Video Call Blackmail",
    hi: "वीडियो कॉल ब्लैकमेल",
    advice_en: "Do not transfer money; preserve evidence and contact cyber helpline 1930 immediately.",
    advice_hi: "पैसे न भेजें; सबूत सुरक्षित रखें और तुरंत साइबर हेल्पलाइन 1930 पर संपर्क करें।",
  },
  "other": {
    en: "Suspicious Activity",
    hi: "संदेहास्पद गतिविधि",
    advice_en: "Never transfer money or share private details with unverified contacts.",
    advice_hi: "अज्ञात संपर्कों को कभी पैसे न भेजें और न ही निजी जानकारी साझा करें।",
  },
};

/**
 * Escape HTML utility
 */
export function escapeHtml(str) {
  if (str == null) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * Return severity metadata with thresholds and bilingual badges
 */
export function getSeverityInfo(count, severity, lang = getLanguage()) {
  const isHi = lang === "hi";
  let sev = severity;
  if (!sev) {
    if (count >= 10) sev = "CRIT";
    else if (count >= 5) sev = "HIGH";
    else sev = "MED";
  }

  if (sev === "CRIT") {
    return {
      severity: "CRIT",
      color: SEV_COLORS.CRIT,
      badge: isHi ? "अत्यधिक रिपोर्टें" : "Very many",
      threshold: isHi ? "10 या अधिक" : "10 or more",
      label: isHi ? "गंभीर गतिविधि" : "Critical Activity",
    };
  }
  if (sev === "HIGH") {
    return {
      severity: "HIGH",
      color: SEV_COLORS.HIGH,
      badge: isHi ? "कई रिपोर्टें" : "Many",
      threshold: isHi ? "5–9" : "5–9",
      label: isHi ? "उच्च गतिविधि" : "High Activity",
    };
  }
  return {
    severity: "MED",
    color: SEV_COLORS.MED,
    badge: isHi ? "कुछ रिपोर्टें" : "A few reports",
    threshold: isHi ? "5 से कम" : "below 5",
    label: isHi ? "मध्यम गतिविधि" : "Moderate Activity",
  };
}

/**
 * Return human-friendly scam name & safety advice
 */
export function getScamInfo(scamType, lang = getLanguage()) {
  const isHi = lang === "hi";
  const key = scamType || "other";
  const detail = SCAM_DETAILS[key];
  if (detail) {
    return {
      name: isHi ? detail.hi : detail.en,
      advice: isHi ? detail.advice_hi : detail.advice_en,
    };
  }
  const readable = key
    .replace(/[-_]/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
  return {
    name: readable,
    advice: isHi
      ? "अज्ञात संपर्कों को कभी पैसे न भेजें और न ही निजी जानकारी साझा करें।"
      : "Never transfer money or share private details with unverified contacts.",
  };
}

/**
 * Build rich tap popup for an active cluster
 */
export function buildClusterPopup(cluster, lang = getLanguage()) {
  const isHi = lang === "hi";
  const sevInfo = getSeverityInfo(cluster.count, cluster.severity, lang);
  const scamInfo = getScamInfo(cluster.top_scam_type, lang);

  const areaName = `${escapeHtml(cluster.locality || "")}, ${escapeHtml(cluster.city || "")}`;
  const pincodeStr = cluster.pincode ? ` (${cluster.pincode})` : "";
  const reportsLabel = isHi ? "स्वतंत्र रिपोर्टें" : "independent reports";
  const scamLabel = isHi ? "शीर्ष स्कैम प्रकार" : "Top scam type";
  const checkLinkText = isHi ? "🔍 नंबर या खाता चेक करें" : "🔍 Check a number";

  return `
    <div class="map-popup-card">
      <div class="popup-header">
        <div class="popup-title">${areaName}${pincodeStr}</div>
        <span class="popup-badge badge-${sevInfo.severity}">
          ${sevInfo.severity} • ${sevInfo.badge}
        </span>
      </div>
      <div class="popup-count-box">
        <span class="popup-count-number">${cluster.count}</span>
        <span class="popup-count-desc">${reportsLabel}</span>
      </div>
      <div class="popup-info-row">
        <span class="popup-label">${scamLabel}:</span>
        <span class="popup-value"><strong>${escapeHtml(scamInfo.name)}</strong></span>
      </div>
      <div class="popup-advice-box">
        <span class="popup-advice-icon">💡</span>
        <span class="popup-advice-text">${escapeHtml(scamInfo.advice)}</span>
      </div>
      <div class="popup-footer">
        <a href="#/check" class="popup-check-link">${checkLinkText}</a>
      </div>
    </div>
  `;
}

/**
 * Build tap popup for areas with no reports in current window
 */
export function buildZeroClusterPopup(area, lang = getLanguage()) {
  const isHi = lang === "hi";
  const areaName = `${escapeHtml(area.locality || "")}, ${escapeHtml(area.city || "")}`;
  const pincodeStr = area.pincode ? ` (${area.pincode})` : "";
  const zeroStatusText = isHi
    ? "इस अवधि में कोई रिपोर्ट दर्ज नहीं हुई (शांत)"
    : "No reports in this period (Calm)";
  const reportLinkText = isHi ? "📢 इस इलाके में रिपोर्ट करें" : "📢 Report a sighting here";

  return `
    <div class="map-popup-card">
      <div class="popup-header">
        <div class="popup-title">${areaName}${pincodeStr}</div>
        <span class="popup-badge badge-ZERO">0</span>
      </div>
      <div class="popup-zero-status">
        <span style="color:#10b981; font-size:1.1rem;">🟢</span>
        <span style="color:#10b981; font-weight:600; font-size:0.88rem;">${zeroStatusText}</span>
      </div>
      <p style="font-size:0.8rem; color:#64748b; margin:6px 0 0;">
        ${isHi ? "अगर आपको इस इलाके में कोई संदिग्ध कॉल या लिंक मिला है, तो रिपोर्ट दर्ज करें।" : "If you encountered suspicious calls or messages in this area, report anonymously."}
      </p>
      <div class="popup-footer" style="margin-top:10px;">
        <a href="#/report" class="popup-check-link popup-report-link" data-pincode="${escapeHtml(area.pincode)}">${reportLinkText}</a>
      </div>
    </div>
  `;
}

// Global reference to bottom-left legend control
let legendControl = null;

/**
 * Render or update bilingual legend in bottom-left corner with config thresholds
 */
export function updateMapLegend(map, lang = getLanguage()) {
  if (!map || !window.L) return;

  if (legendControl) {
    map.removeControl(legendControl);
    legendControl = null;
  }

  legendControl = L.control({ position: "bottomleft" });
  legendControl.onAdd = function () {
    const div = L.DomUtil.create("div", "heatmap-legend");
    const isHi = lang === "hi";

    div.innerHTML = `
      <div class="legend-header">
        <span class="legend-title">${isHi ? "स्कैम गतिविधि स्तर" : "Scam Activity Level"}</span>
      </div>
      <div class="legend-items">
        <div class="legend-row">
          <span class="legend-dot" style="background:${SEV_COLORS.CRIT};"></span>
          <span class="legend-label"><strong>CRIT (10+)</strong>: ${isHi ? "अत्यधिक रिपोर्टें (10 या अधिक)" : "Very many (10 or more)"}</span>
        </div>
        <div class="legend-row">
          <span class="legend-dot" style="background:${SEV_COLORS.HIGH};"></span>
          <span class="legend-label"><strong>HIGH (5–9)</strong>: ${isHi ? "कई रिपोर्टें (5–9)" : "Many (5–9)"}</span>
        </div>
        <div class="legend-row">
          <span class="legend-dot" style="background:${SEV_COLORS.MED};"></span>
          <span class="legend-label"><strong>MED (&lt;5)</strong>: ${isHi ? "कुछ रिपोर्टें (5 से कम)" : "A few reports (below 5)"}</span>
        </div>
        <div class="legend-row">
          <span class="legend-dot legend-dot-green"></span>
          <span class="legend-label">${isHi ? "हरा: इस अवधि में कोई रिपोर्ट नहीं" : "Green: no reports in this period"}</span>
        </div>
      </div>
    `;
    return div;
  };

  legendControl.addTo(map);
}

// Keep track of active map layers & marker references
let activeHeatLayer = null;
let activeGlowLayer = null;
let activeMarkersLayer = null;
let activeDotsLayer = null;
export const activeMarkersMap = new Map(); // pincode -> { marker, lat, lng, type }

/**
 * Smoothly fly to a locality, center the map container into view, and open its popup with pulse
 */
export function flyToLocality(map, lat, lng, pincode) {
  if (!map) return;
  const mapElement = document.getElementById("leaflet-map");
  if (mapElement) {
    mapElement.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  map.flyTo([lat, lng], 14, {
    animate: true,
    duration: 1.1,
    easeLinearity: 0.25,
  });

  const entry = activeMarkersMap.get(pincode);
  if (entry && entry.marker) {
    setTimeout(() => {
      entry.marker.openPopup();
      const el = entry.marker.getElement();
      if (el) {
        el.classList.remove("marker-highlight-pulse");
        void el.offsetWidth; // trigger reflow
        el.classList.add("marker-highlight-pulse");
      }
    }, 450);
  }
}

/**
 * Filter data by user criteria (search, scamType, severity, city)
 */
function applyFilters(clusters, allAreas, filterCriteria = {}) {
  const q = (filterCriteria.search || "").trim().toLowerCase();
  const selectedScam = (filterCriteria.scamType || "").trim();
  const selectedSev = (filterCriteria.severity || "").trim();
  const selectedCity = (filterCriteria.city || "").trim();

  // Filter clusters
  const filteredClusters = clusters.filter((c) => {
    if (selectedCity && selectedCity !== "all" && c.city !== selectedCity) return false;
    if (selectedScam && c.top_scam_type !== selectedScam) return false;
    if (selectedSev) {
      if (selectedSev === "ZERO") return false; // Zero reports only applies to areas without reports
      if (c.severity !== selectedSev) return false;
    }
    if (q) {
      const matchLoc = (c.locality || "").toLowerCase().includes(q);
      const matchCity = (c.city || "").toLowerCase().includes(q);
      const matchPin = (c.pincode || "").toLowerCase().includes(q);
      const matchScam = (c.top_scam_type || "").toLowerCase().includes(q);
      if (!matchLoc && !matchCity && !matchPin && !matchScam) return false;
    }
    return true;
  });

  // Filter all areas
  const filteredAreas = allAreas.filter((a) => {
    if (selectedCity && selectedCity !== "all" && a.city !== selectedCity) return false;
    if (selectedScam) return false; // Areas with 0 reports do not have a scam type
    if (selectedSev && selectedSev !== "ZERO") return false; // If looking for CRIT/HIGH/MED, skip zero areas
    if (q) {
      const matchLoc = (a.locality || "").toLowerCase().includes(q);
      const matchCity = (a.city || "").toLowerCase().includes(q);
      const matchPin = (a.pincode || "").toLowerCase().includes(q);
      if (!matchLoc && !matchCity && !matchPin) return false;
    }
    return true;
  });

  return { filteredClusters, filteredAreas };
}

/**
 * Main map renderer supporting multi-dimensional filters and smooth UX zoom
 */
export function renderHeatmapView(
  map,
  clusters = [],
  allAreas = [],
  lang = getLanguage(),
  filterCriteria = {},
  activeTab = "all"
) {
  const isHi = lang === "hi";

  // Always update the bottom-left legend
  if (map) {
    updateMapLegend(map, lang);
  }

  // Clear previous layers & markers map
  if (map) {
    if (activeHeatLayer) {
      map.removeLayer(activeHeatLayer);
      activeHeatLayer = null;
    }
    if (activeGlowLayer) {
      map.removeLayer(activeGlowLayer);
      activeGlowLayer = null;
    }
    if (activeMarkersLayer) {
      map.removeLayer(activeMarkersLayer);
      activeMarkersLayer = null;
    }
    if (activeDotsLayer) {
      map.removeLayer(activeDotsLayer);
      activeDotsLayer = null;
    }
  }
  activeMarkersMap.clear();

  // Apply filters
  const { filteredClusters, filteredAreas } = applyFilters(clusters, allAreas, filterCriteria);

  const bounds = [];
  const reportedPincodes = new Set();

  const validClusters = filteredClusters.filter(
    (c) => c.lat != null && c.lng != null && typeof c.lat === "number" && typeof c.lng === "number"
  );

  validClusters.forEach((c) => {
    if (c.pincode) reportedPincodes.add(c.pincode);
    bounds.push([c.lat, c.lng]);
  });

  // 1. Heatmap layer or fallback concentric circles
  if (map && validClusters.length > 0) {
    const maxCount = Math.max(...validClusters.map((c) => c.count), 1);
    const heatPoints = validClusters.map((c) => [c.lat, c.lng, c.count / maxCount]);

    let heatPluginLoaded = false;
    if (typeof L !== "undefined" && typeof L.heatLayer === "function") {
      try {
        activeHeatLayer = L.heatLayer(heatPoints, {
          radius: 38,
          blur: 24,
          maxZoom: 14,
          minOpacity: 0.35,
          gradient: {
            0.2: SEV_COLORS.MED,  // yellow / amber #F2B01E
            0.6: SEV_COLORS.HIGH, // orange #F57C00
            1.0: SEV_COLORS.CRIT, // red #D32F2F
          },
        }).addTo(map);
        heatPluginLoaded = true;
      } catch (err) {
        console.warn("Leaflet.heat render error; using concentric circle fallback:", err);
        heatPluginLoaded = false;
      }
    }

    // Fallback: draw 3 concentric translucent circles per cluster (r, 0.6r, 0.3r)
    if (!heatPluginLoaded) {
      activeGlowLayer = L.layerGroup().addTo(map);
      validClusters.forEach((c) => {
        const sevInfo = getSeverityInfo(c.count, c.severity, lang);
        const color = sevInfo.color;
        const r = 600 + Math.min(c.count * 120, 1800);

        L.circle([c.lat, c.lng], {
          radius: r,
          fillColor: color,
          fillOpacity: 0.15,
          stroke: false,
          interactive: false,
        }).addTo(activeGlowLayer);

        L.circle([c.lat, c.lng], {
          radius: r * 0.6,
          fillColor: color,
          fillOpacity: 0.30,
          stroke: false,
          interactive: false,
        }).addTo(activeGlowLayer);

        L.circle([c.lat, c.lng], {
          radius: r * 0.3,
          fillColor: color,
          fillOpacity: 0.55,
          stroke: false,
          interactive: false,
        }).addTo(activeGlowLayer);
      });
    }

    // 2. Numbered markers on clusters
    activeMarkersLayer = L.layerGroup().addTo(map);
    validClusters.forEach((c) => {
      const sevInfo = getSeverityInfo(c.count, c.severity, lang);
      const markerIcon = L.divIcon({
        className: "cluster-numbered-marker-wrapper",
        html: `
          <div class="cluster-num-marker marker-${sevInfo.severity}" 
               role="button"
               tabindex="0"
               aria-label="${c.locality || "Area"}: ${c.count} ${isHi ? "रिपोर्टें" : "reports"}, ${sevInfo.severity} (${sevInfo.badge})">
            <span class="marker-count">${c.count}</span>
          </div>
        `,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
        popupAnchor: [0, -18],
      });

      const marker = L.marker([c.lat, c.lng], { icon: markerIcon }).addTo(activeMarkersLayer);
      marker.bindPopup(buildClusterPopup(c, lang), { maxWidth: 320 });
      activeMarkersMap.set(c.pincode, { marker, lat: c.lat, lng: c.lng, type: "cluster", data: c });
    });
  }

  // 3. Faint green dots for areas with no reports
  if (map && Array.isArray(filteredAreas)) {
    activeDotsLayer = L.layerGroup().addTo(map);
    filteredAreas.forEach((area) => {
      if (area.lat != null && area.lng != null && !reportedPincodes.has(area.pincode)) {
        bounds.push([area.lat, area.lng]);
        const dot = L.circleMarker([area.lat, area.lng], {
          radius: 6,
          color: SEV_COLORS.ZERO,
          fillColor: SEV_COLORS.ZERO,
          fillOpacity: 0.45,
          weight: 1.5,
        }).addTo(activeDotsLayer);

        dot.bindPopup(buildZeroClusterPopup(area, lang), { maxWidth: 280 });
        activeMarkersMap.set(area.pincode, { marker: dot, lat: area.lat, lng: area.lng, type: "zero", data: area });
      }
    });
  }

  // Auto-fit bounds if we have points and not manually zooming
  if (map && bounds.length > 0 && !filterCriteria._skipFit) {
    try {
      map.fitBounds(bounds, { padding: [35, 35], maxZoom: 13 });
    } catch (e) {}
  }

  // 4. Render the cluster list under the map
  renderClustersList(filteredClusters, allAreas, lang, map, activeTab);
}

/**
 * Render the enhanced cluster list under the map with tab navigation & instant zoom on click
 */
export function renderClustersList(
  filteredClusters = [],
  allAreas = [],
  lang = getLanguage(),
  map = null,
  activeTab = "all"
) {
  const isHi = lang === "hi";
  const listContainer = document.getElementById("map-clusters-list");
  if (!listContainer) return;

  const reportedPincodes = new Set(filteredClusters.map((c) => c.pincode));
  const calmAreas = allAreas.filter((a) => !reportedPincodes.has(a.pincode));

  // Update tab counts in DOM
  const elCountAll = document.getElementById("count-all-localities");
  const elCountActive = document.getElementById("count-active-clusters");
  const elCountCalm = document.getElementById("count-calm-areas");
  if (elCountAll) elCountAll.textContent = filteredClusters.length + calmAreas.length;
  if (elCountActive) elCountActive.textContent = filteredClusters.length;
  if (elCountCalm) elCountCalm.textContent = calmAreas.length;

  // Sort active clusters by severity CRIT (3) -> HIGH (2) -> MED (1), then count desc
  const sortedClusters = [...filteredClusters].sort((a, b) => {
    const sevRank = { CRIT: 3, HIGH: 2, MED: 1 };
    const rA = sevRank[a.severity] || (a.count >= 10 ? 3 : a.count >= 5 ? 2 : 1);
    const rB = sevRank[b.severity] || (b.count >= 10 ? 3 : b.count >= 5 ? 2 : 1);
    if (rB !== rA) return rB - rA;
    return (b.count || 0) - (a.count || 0);
  });

  // Prepare items according to active tab
  let itemsToRender = [];
  if (activeTab === "active") {
    itemsToRender = sortedClusters.map((c) => ({ type: "cluster", data: c }));
  } else if (activeTab === "calm") {
    itemsToRender = calmAreas.map((a) => ({ type: "calm", data: a }));
  } else {
    // "all": clusters first, followed by calm areas
    itemsToRender = [
      ...sortedClusters.map((c) => ({ type: "cluster", data: c })),
      ...calmAreas.map((a) => ({ type: "calm", data: a })),
    ];
  }

  if (itemsToRender.length === 0) {
    listContainer.innerHTML = `
      <div class="clusters-empty-state">
        <div style="font-size:2rem; margin-bottom:8px;">🔍</div>
        <p style="color: var(--text-muted); font-size: 0.92rem; font-weight:500;">
          ${isHi ? "कोई मेल खाने वाला इलाका नहीं मिला। कृपया अपने फ़िल्टर समायोजित करें।" : "No matching localities found. Try clearing or adjusting your search filters."}
        </p>
      </div>
    `;
    return;
  }

  const reportsText = isHi ? "स्वतंत्र रिपोर्टें" : "independent reports";
  const topLabel = isHi ? "शीर्ष स्कैम" : "Top Sighting";
  const zoomCue = isHi ? "मैप पर ज़ूम करें ↗" : "Zoom on map ↗";
  const reportHereText = isHi ? "+ यहाँ रिपोर्ट करें" : "+ Report Here";

  listContainer.innerHTML = itemsToRender
    .map((item, index) => {
      if (item.type === "cluster") {
        const c = item.data;
        const sevInfo = getSeverityInfo(c.count, c.severity, lang);
        const scamInfo = getScamInfo(c.top_scam_type, lang);

        return `
          <div class="cluster-item cluster-item-${sevInfo.severity}" 
               data-pincode="${escapeHtml(c.pincode)}" 
               data-lat="${c.lat != null ? c.lat : ""}" 
               data-lng="${c.lng != null ? c.lng : ""}"
               tabindex="0"
               role="button"
               title="${escapeHtml(c.locality)}: ${zoomCue}"
               aria-label="${escapeHtml(c.locality)}, ${escapeHtml(c.city)}: ${c.count} ${reportsText}, ${sevInfo.severity}">
            <div class="cluster-info">
              <div class="cluster-name">
                <span class="cluster-order-num">#${index + 1}</span>
                ${escapeHtml(c.locality || "Area")}, ${escapeHtml(c.city || "")} 
                <span class="cluster-pincode">(${escapeHtml(c.pincode)})</span>
              </div>
              <div class="cluster-meta">
                <span>${topLabel}: <strong>${escapeHtml(scamInfo.name)}</strong></span>
                <span class="meta-separator">•</span>
                <span><strong>${c.count}</strong> ${reportsText}</span>
              </div>
            </div>
            <div class="cluster-badges-group">
              ${(window.satyacheckAlerts || []).some((al) => al.pincode === c.pincode && al.type === "SPIKE") 
                ? '<span class="cluster-badge" style="background:#fee2e2; color:#b91c1c; border:1px solid #fca5a5; font-weight:800;">🚨 SPIKE ALERT</span>' 
                : (window.satyacheckAlerts || []).some((al) => al.pincode === c.pincode && al.type === "NEW_TYPE")
                ? '<span class="cluster-badge" style="background:#ffedd5; color:#c2410c; border:1px solid #fdba74; font-weight:800;">⚠️ NEW PATTERN</span>'
                : ''}
              <span class="cluster-badge cluster-${sevInfo.severity}">${sevInfo.severity}</span>
              <span class="cluster-text-badge text-badge-${sevInfo.severity}">${sevInfo.badge}</span>
              <span class="zoom-cue">${zoomCue}</span>
            </div>
          </div>
        `;
      } else {
        const a = item.data;
        return `
          <div class="cluster-item cluster-item-calm" 
               data-pincode="${escapeHtml(a.pincode)}" 
               data-lat="${a.lat != null ? a.lat : ""}" 
               data-lng="${a.lng != null ? a.lng : ""}"
               tabindex="0"
               role="button"
               title="${escapeHtml(a.locality)}: ${zoomCue}"
               aria-label="${escapeHtml(a.locality)}, ${escapeHtml(a.city)}: 0 reports, Calm">
            <div class="cluster-info">
              <div class="cluster-name">
                <span class="calm-dot">🟢</span>
                ${escapeHtml(a.locality || "Area")}, ${escapeHtml(a.city || "")} 
                <span class="cluster-pincode">(${escapeHtml(a.pincode)})</span>
              </div>
              <div class="cluster-meta">
                <span style="color:#059669; font-weight:500;">
                  ${isHi ? "इस समय सीमा में कोई रिपोर्ट नहीं (शांत इलाका)" : "No reports recorded in this window (Calm)"}
                </span>
              </div>
            </div>
            <div class="cluster-badges-group">
              <span class="cluster-badge badge-ZERO">0 Reports</span>
              <a href="#/report" class="btn-quick-report-calm" data-pincode="${escapeHtml(a.pincode)}">${reportHereText}</a>
              <span class="zoom-cue">${zoomCue}</span>
            </div>
          </div>
        `;
      }
    })
    .join("");

  // Attach click & keyboard listeners to smoothly zoom on map
  listContainer.querySelectorAll(".cluster-item").forEach((card) => {
    const handleZoom = (e) => {
      // If user clicked the quick report link, let default navigation proceed
      if (e.target.closest(".btn-quick-report-calm")) return;

      const lat = parseFloat(card.getAttribute("data-lat"));
      const lng = parseFloat(card.getAttribute("data-lng"));
      const pincode = card.getAttribute("data-pincode");

      // Visual highlight on card
      listContainer.querySelectorAll(".cluster-item").forEach((c) => c.classList.remove("active-selected"));
      card.classList.add("active-selected");

      if (map && !isNaN(lat) && !isNaN(lng)) {
        flyToLocality(map, lat, lng, pincode);
      }
    };

    card.addEventListener("click", handleZoom);
    card.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        handleZoom(e);
      }
    });
  });

  // Attach click listener for "+ Report Here" buttons to pre-select pincode
  listContainer.querySelectorAll(".btn-quick-report-calm").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const pincode = btn.getAttribute("data-pincode");
      if (pincode) {
        setTimeout(() => {
          const pincodeSelect = document.getElementById("report-pincode");
          if (pincodeSelect) {
            pincodeSelect.value = pincode;
          }
        }, 100);
      }
    });
  });
}
